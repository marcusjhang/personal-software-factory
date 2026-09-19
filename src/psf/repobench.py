"""Multi-repo capability evaluation.

Builds a matrix of real git repositories across **sizes** (tiny -> large) and
**domains** (cli, api, etl, lib, script), each with a task and a deterministic
checker (run the project's tests). Runs the factory against each and records
resolve rate, attempts, and per-repo outcomes.

Two modes:

- ``process`` (deterministic): a reference solver applies the known-correct
  change, so we exercise the factory's plumbing (worktree, gates, verify,
  handoff, ledger) across many repo shapes at scale.
- ``real``: a real harness (Claude) implements the task; the project's tests
  grade it. Slower and small-n, but measures actual capability.

Also a per-repo eval-growth loop: each repo grows its own protected eval set from
its outcome, under the governance rules (provenance + separate approval).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .events import EventLog
from .evalkit import make_eval_dir
from .foreman import Foreman
from .schema import Factory
from .state import Workflow

SIZES = {"tiny": 1, "small": 5, "medium": 20, "large": 60}
DOMAINS = ("cli", "api", "etl", "lib", "script")
EXISTING = {"cli": "parse", "api": "route", "etl": "extract", "lib": "encode", "script": "step"}


def build_repo(dest: Path, size: str, domain: str) -> Path:
    """Create a real git repo with starter code + tests for the given shape."""
    dest = Path(dest)
    (dest / "app").mkdir(parents=True, exist_ok=True)
    (dest / "tests").mkdir(parents=True, exist_ok=True)
    (dest / "app" / "__init__.py").write_text("")
    n = SIZES[size]
    verb = EXISTING[domain]
    for i in range(n):
        (dest / "app" / f"mod{i}.py").write_text(
            f"def {verb}_{i}():\n    return {i}\n")
    checks = "\n".join(f"    assert app.mod{i}.{verb}_{i}() == {i}" for i in range(n))
    imports = "\n".join(f"import app.mod{i}" for i in range(n))
    (dest / "tests" / "test_base.py").write_text(
        "import app\n" + imports + "\n\n\ndef test_base():\n"
        + (checks or "    assert True") + "\n")
    (dest / "pytest.ini").write_text("[pytest]\npythonpath = .\n")
    _git(dest, "init")
    _git(dest, "config", "user.email", "t@t")
    _git(dest, "config", "user.name", "t")
    _git(dest, "add", "-A")
    _git(dest, "commit", "-m", "init")
    return dest


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True)


def checker(workspace: Path) -> bool:
    """Deterministic grader: the project's tests pass."""
    p = subprocess.run(["python3", "-m", "pytest", "-q"], cwd=str(workspace),
                       capture_output=True, text=True)
    return p.returncode == 0


def task_goal(size: str, domain: str) -> str:
    return (f"In the '{domain}' project, add app/feature.py exposing feature() -> '{domain}', "
            f"and tests/test_feature.py that asserts it. Keep all existing tests passing.")


def solution(domain: str) -> dict[str, str]:
    return {
        "app/feature.py": f"def feature():\n    return \"{domain}\"\n",
        "tests/test_feature.py": ("from app.feature import feature\n\n\n"
                                  f"def test_feature():\n    assert feature() == \"{domain}\"\n"),
    }


class RepoProcessRunner:
    """Deterministic reference solver: applies the known-correct change."""

    def __init__(self, domain: str):
        self.domain = domain

    def run(self, task):
        from .agents import AgentResult
        ws = task.workspace
        if task.role == "implement":
            for rel, body in solution(self.domain).items():
                fp = ws / rel
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(body)
            return AgentResult(True, {"artifact_digest": "ref"})
        if task.role == "verify":
            passed = checker(ws)
            return AgentResult(passed, {"passed": passed, "findings": [] if passed else ["tests fail"]})
        if task.role == "triage":
            return AgentResult(True, {"decision": "spec"})
        if task.role == "spec":
            return AgentResult(True, {"title": task.goal, "body": "x", "acceptance": ["tests pass"]})
        return AgentResult(True, {"decision": "approve"})


class RepoRealRunner:
    """Real harness: Claude implements; the project's tests verify."""

    def __init__(self, claude_script: str | Path, timeout: int = 900):
        self.script = str(claude_script)
        self.timeout = timeout

    def run(self, task):
        from .agents import AgentResult, AgentTask
        from .agents import SubprocessRunner
        if task.role == "implement":
            sub = SubprocessRunner(default_command=["python3", self.script], timeout=self.timeout)
            res = sub.run(task)
            return res
        if task.role == "verify":
            passed = checker(task.workspace)
            return AgentResult(passed, {"passed": passed, "findings": [] if passed else ["tests fail"]})
        sub = SubprocessRunner(default_command=["python3", self.script], timeout=self.timeout)
        return sub.run(task)


def _factory() -> Factory:
    return Factory(name="repobench", schema_version="psf/v1", path=Path("factory.yml"),
                   runner="mock", mode="yolo",
                   gates={"spec_approval": True, "verify_quorum": 1},
                   limits={"max_attempts": 2})


@dataclass
class MatrixResult:
    repos: list[dict] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.repos)

    @property
    def resolved(self) -> int:
        return sum(1 for r in self.repos if r["resolved"])

    def by_size(self) -> dict:
        out: dict[str, dict] = {}
        for r in self.repos:
            s = out.setdefault(r["size"], {"total": 0, "resolved": 0})
            s["total"] += 1
            s["resolved"] += int(r["resolved"])
        return out

    def to_dict(self) -> dict:
        return {"total": self.total, "resolved": self.resolved,
                "resolve_rate": self.resolved / self.total if self.total else 0.0,
                "by_size": self.by_size(), "repos": self.repos}


def run_matrix(*, sizes: list[str] | None = None, domains: list[str] | None = None,
               mode: str = "process", root: str | Path | None = None,
               claude_script: str | Path | None = None) -> dict:
    sizes = sizes or list(SIZES)
    domains = domains or list(DOMAINS)
    tmp_root = Path(root) if root else Path(tempfile.mkdtemp(prefix="psf-repobench-"))
    tmp_root.mkdir(parents=True, exist_ok=True)
    result = MatrixResult()
    for size in sizes:
        for domain in domains:
            repo = build_repo(tmp_root / f"{size}-{domain}", size, domain)
            log = EventLog(repo / ".psf" / "factory.db")
            runner = (RepoProcessRunner(domain) if mode == "process"
                      else RepoRealRunner(claude_script or "scripts/psf_agent_claude.py"))
            res = None
            error = None
            try:
                res = Foreman(_factory(), Workflow(log), runner).run(
                    task_goal(size, domain), repo=repo, use_git=True, finish=False)
            except Exception as e:  # noqa: BLE001 - a repo failing is a data point
                error = repr(e)
            log.close()
            if res is not None:
                resolved = res.verify_passed and res.work.state in ("REVIEW", "HANDOFF", "DONE")
                findings = res.findings or []
                state, attempts = res.work.state, res.work.attempts
            else:
                resolved, findings, state, attempts = False, [], "ERROR", 0
            result.repos.append({
                "repo": f"{size}-{domain}", "size": size, "domain": domain, "mode": mode,
                "state": state, "attempts": attempts, "verify_passed": bool(res and res.verify_passed),
                "resolved": resolved, "error": error, "findings": findings[:3],
            })
            # clean the worktree for this run to bound disk use
            subprocess.run(["git", "worktree", "prune"], cwd=str(repo),
                           capture_output=True, text=True)
    return result.to_dict()


def grow_evals_per_repo(eval_dir: str | Path, *, domain: str, size: str, source: str,
                        approver: str = "owner", author: str = "system") -> dict:
    """Per-repo eval growth: add a case for this repo's task, then approve it."""
    from .evalgov import add_candidate, approve_candidate, integrity, status

    d = Path(eval_dir)
    if not (d / "tasks.json").exists():
        make_eval_dir(d.parent, tasks=[{"id": "seed", "goal": "keep tests green",
                                        "solves_on_attempt": 1}])
    cid = f"{size}-{domain}"
    try:
        add_candidate(d, case_id=cid, goal=task_goal(size, domain), solves_on_attempt=2,
                      source=source, owner=author)
        approve_candidate(d, cid, approver=approver, author=author)
    except ValueError:
        pass  # already present
    return {"status": status(d), "integrity": integrity(d)}
