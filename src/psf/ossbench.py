"""Real OSS-repo evaluation (large, mature codebases).

Two task kinds:

- **localization** — find the file that defines a symbol (ground truth computed
  from the repo with `git grep`), and write its path to ``ANSWER.txt``. Scores
  navigation on huge repos without needing a build.
- **change** — add a small, self-contained module + hermetic test at the repo
  root and make ``pytest`` pass. Exercises a real repo/worktree end to end.

Grading is deterministic (path match / pytest), so the real harness only has to
implement; verification runs locally.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .agents import AgentResult, AgentTask, SubprocessRunner
from .events import EventLog
from .foreman import Foreman
from .schema import Factory
from .state import Workflow

SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".rb", ".go", ".rs", ".java", ".rs"}
_IDENT = re.compile(r"\b(?:export\s+)?(?:async\s+)?(?:function|const|def|class)\s+([A-Za-z_][A-Za-z0-9_]{5,})")


def repo_stats(repo: Path) -> dict:
    files = subprocess.run(["git", "ls-files"], cwd=str(repo), capture_output=True, text=True).stdout.split()
    by_ext: dict[str, int] = {}
    for f in files:
        by_ext[Path(f).suffix] = by_ext.get(Path(f).suffix, 0) + 1
    return {"files": len(files), "top_ext": sorted(by_ext.items(), key=lambda kv: -kv[1])[:5]}


def find_unique_symbol(repo: Path, *, max_files: int = 20000) -> tuple[str, str] | None:
    """Return (symbol, file) for an identifier that appears in exactly one source file."""
    files = subprocess.run(["git", "ls-files"], cwd=str(repo), capture_output=True, text=True).stdout.split()
    occ: dict[str, set[str]] = {}
    for f in files[:max_files]:
        if Path(f).suffix not in SOURCE_EXTS:
            continue
        p = repo / f
        try:
            if p.stat().st_size > 200_000:
                continue
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for m in _IDENT.finditer(text):
            occ.setdefault(m.group(1), set()).add(f)
    for sym in sorted(occ):
        fs = occ[sym]
        if len(fs) == 1:
            return sym, next(iter(fs))
    return None


class OSSRunner:
    """Claude implements; a deterministic local checker verifies."""

    def __init__(self, checker, claude_script: str | Path, timeout: int = 900):
        self.checker = checker
        self.sub = SubprocessRunner(default_command=["python3", str(claude_script)], timeout=timeout)

    def run(self, task: AgentTask) -> AgentResult:
        if task.role == "verify":
            passed, findings = self.checker(task.workspace)
            return AgentResult(passed, {"passed": passed, "findings": findings})
        return self.sub.run(task)


def _factory() -> Factory:
    return Factory(name="ossbench", schema_version="psf/v1", path=Path("factory.yml"),
                   runner="subprocess", mode="yolo",
                   gates={"spec_approval": True, "verify_quorum": 1},
                   limits={"max_attempts": 2})


def localization_goal(symbol: str) -> str:
    return (f"In this repository, find the single file that defines `{symbol}`. "
            "Write only its repository-relative path (one line, no quotes, no explanation) "
            "to a new file named ANSWER.txt at the repository root.")


def make_localization_checker(expected_file: str):
    def check(ws: Path):
        ans = ws / "ANSWER.txt"
        if not ans.exists():
            return False, ["ANSWER.txt not written"]
        got = ans.read_text().strip().strip("`\"'").lstrip("./").strip()
        ok = got == expected_file or got.endswith(expected_file)
        return ok, [] if ok else [f"expected {expected_file}, got {got!r}"]
    return check


CHANGE_GOAL = ("Create a module `psf_probe.py` at the repository root with a function "
               "`probe()` that returns the string 'ok', and a test file `test_psf_probe.py` "
               "at the root that imports psf_probe and asserts probe() == 'ok'. "
               "Make `python -m pytest test_psf_probe.py -q` pass.")


def change_checker(ws: Path):
    p = subprocess.run(["python3", "-m", "pytest", "test_psf_probe.py", "-q"],
                       cwd=str(ws), capture_output=True, text=True)
    return p.returncode == 0, [] if p.returncode == 0 else [p.stdout.strip()[-200:]]


def run_oss_task(repo: Path, *, kind: str, claude_script: str | Path) -> dict:
    repo = Path(repo)
    symbol = expected = None
    if kind == "localization":
        found = find_unique_symbol(repo)
        if not found:
            return {"repo": repo.name, "kind": kind, "resolved": False, "error": "no unique symbol"}
        symbol, expected = found
        goal = localization_goal(symbol)
        checker = make_localization_checker(expected)
    else:
        goal = CHANGE_GOAL
        checker = change_checker
    log = EventLog(repo / ".psf-oss.db")
    result = {"repo": repo.name, "kind": kind, "symbol": symbol, "expected": expected,
              "stats": repo_stats(repo)}
    try:
        res = Foreman(_factory(), Workflow(log), OSSRunner(checker, claude_script)).run(
            goal, repo=repo, use_git=True, finish=False)
        result.update(state=res.work.state, attempts=res.work.attempts,
                      resolved=bool(res.verify_passed and res.work.state in ("REVIEW", "HANDOFF", "DONE")))
    except Exception as e:  # noqa: BLE001
        result.update(resolved=False, error=repr(e))
    log.close()
    subprocess.run(["git", "worktree", "prune"], cwd=str(repo), capture_output=True, text=True)
    return result
