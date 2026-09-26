"""Live end-to-end: run the full 5-role loop through a real harness.

Unlike ``e2e`` (mock runner), this drives a real coding agent (opencode/DeepSeek,
Claude, Codex) on a tiny scratch repo, graded by a **deterministic**
``verify_command`` (pytest), so "verified" is not just the LLM's opinion.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import tempfile
from pathlib import Path

FAILING_TEST = """import greet


def test_greet():
    assert greet.greet("World") == "Hello, World!"
"""


def _repo(tmp: Path) -> Path:
    d = tmp / "live"
    (d / "tests").mkdir(parents=True)
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=d, check=False)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=d, check=False)
    subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=False)
    (d / "README.md").write_text("# scratch\n")
    (d / "pytest.ini").write_text("[pytest]\npythonpath = .\n")
    # a failing test at baseline so the verify gate actually bites
    (d / "tests" / "test_greet.py").write_text(FAILING_TEST)
    subprocess.run(["git", "add", "-A"], cwd=d, check=False)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=d, check=False)
    return d


def _grade(d: Path) -> tuple[bool, str]:
    """Grade the worktree: pytest passes and greetings are correct."""
    wts = sorted((d / ".psf" / "worktrees").glob("*"))
    if not wts:
        return False, "no worktree"
    p = subprocess.run(["python3", "-m", "pytest", "-q"], cwd=str(wts[0]),
                       capture_output=True, text=True)
    return p.returncode == 0, (p.stdout or p.stderr)[-200:]


def run_live(harness: str, *, model: str | None = None, github_repo: str | None = None,
             timeout: int = 1800) -> dict:
    from . import cli

    goal = ("Add a Python module greet.py with a function greet(name) that returns "
            "the string Hello, <name>!, then make the existing test suite pass.")
    tmp = Path(tempfile.mkdtemp(prefix="psf-live-"))
    d = _repo(tmp)
    result = {"harness": harness, "model": model, "repo": str(d)}
    old = os.getcwd()
    try:
        os.chdir(d)
        with contextlib.redirect_stdout(io.StringIO()):
            cli.main(["init", "--feedback", "off", "--mode", "yolo"])
        # pin a deterministic verify gate so verification runs the tests
        import yaml
        yml = d / "factory" / "factory.yml"
        raw = yaml.safe_load(yml.read_text())
        raw.setdefault("gates", {})["verify_command"] = "python3 -m pytest -q"
        raw["gates"]["verify_quorum"] = 1
        yml.write_text(yaml.safe_dump(raw, sort_keys=False))
        env_cmd = ["--harness", harness] + (["--model", model] if model else [])
        attempts = []
        for _ in range(2):  # one bounded retry for a false triage rejection
            with contextlib.redirect_stdout(io.StringIO()):
                rc = cli.main(["run", "--git", "--no-ask", *env_cmd, goal]
                              + (["--github"] if github_repo else []))
            states = _states_of(d)
            attempts.append(states)
            if states == ["DONE"] or states == ["HANDOFF"]:
                break
        passed, detail = _grade(d)
        result.update(rc=rc, pytest_passed=passed, detail=detail, attempts=attempts,
                      states=_states_of(d))
        result["events"] = _events_of(d)
    except Exception as e:  # noqa: BLE001
        result.update(error=repr(e))
    finally:
        os.chdir(old)
    result["resolved"] = bool(result.get("pytest_passed") and
                              any(s in ("DONE", "HANDOFF") for s in (result.get("states") or [])))
    return result


def _states_of(d: Path) -> list[str]:
    from .events import EventLog
    from .state import Workflow
    log = EventLog(d / ".psf" / "factory.db")
    wf = Workflow(log)
    states = [wf.fold(w).state for w in log.work_ids()]
    log.close()
    return states


def _events_of(d: Path) -> list[str]:
    from .events import EventLog
    log = EventLog(d / ".psf" / "factory.db")
    types = [e.type for e in log.all()]
    log.close()
    return types


def run_live_suite(harnesses: list[tuple[str, str | None]]) -> dict:
    results = [run_live(h, model=m) for h, m in harnesses]
    return {"total": len(results), "resolved": sum(1 for r in results if r.get("resolved")),
            "results": results}
