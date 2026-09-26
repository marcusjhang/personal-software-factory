"""End-to-end tests — one per stage boundary, driven through the real CLI.

Distinct from the unit/eval suites: these invoke ``psf ...`` (in-process) in a
throwaway git repo and assert the *observable* outcome (final state, ledger, and
artifacts), covering every point of the development process:
init -> triage/spec -> approval gate -> build -> verify -> review -> handoff,
plus modes, cancel/unblock, improvement, feedback, governance, and health.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import tempfile
from pathlib import Path

from .evalkit import EvalResult
from .events import EventLog
from .state import Workflow


def _run_cli(argv: list[str]) -> int:
    from . import cli

    with contextlib.redirect_stdout(io.StringIO()):
        try:
            return cli.main(argv)
        except SystemExit as e:  # argparse errors
            return int(e.code or 1)


def _repo(tmp: Path, name: str) -> Path:
    d = tmp / name
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=d, check=False)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=d, check=False)
    subprocess.run(["git", "config", "user.name", "t"], cwd=d, check=False)
    (d / "README.md").write_text("# proj\n")
    subprocess.run(["git", "add", "-A"], cwd=d, check=False)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=d, check=False)
    return d


def _in(d: Path):
    class _Cd:
        def __enter__(self):
            self.old = os.getcwd()
            os.chdir(d)
        def __exit__(self, *exc):
            os.chdir(self.old)
    return _Cd()


def _states(d: Path) -> tuple[list[str], bool]:
    log = EventLog(d / ".psf" / "factory.db")
    wf = Workflow(log)
    states = [wf.fold(w).state for w in log.work_ids()]
    ok, _ = log.verify_chain()
    log.close()
    return states, ok


def eval_X1(tmp: Path) -> EvalResult:
    """init -> full loop (mock) -> handoff + DONE, ledger intact, real diff."""
    d = _repo(tmp, "x1")
    with _in(d):
        assert _run_cli(["init", "--feedback", "off", "--mode", "yolo"]) == 0
        rc = _run_cli(["run", "--git", "--no-ask", "add a health endpoint"])
    states, chain = _states(d)
    log = EventLog(d / ".psf" / "factory.db")
    events = [e.type for e in log.all()]
    w = log.work_ids()[0]
    diff = ""
    for e in log.for_work(w):
        if e.type == "HandoffProduced":
            diff = e.payload.get("diff", "")
    log.close()
    ok = rc == 0 and states == ["DONE"] and chain and "HandoffProduced" in events and "artifact.txt" in diff
    return EvalResult("X1", "init -> build -> verify -> review -> handoff", "pass" if ok else "fail",
                      {"state": states, "chain": chain, "diff": diff[:60]})


def eval_X2(tmp: Path) -> EvalResult:
    """Approval gate: HITL without approval waits in SPEC_REVIEW, then approves to READY."""
    d = _repo(tmp, "x2")
    with _in(d):
        assert _run_cli(["init", "--feedback", "off", "--mode", "hitl"]) == 0
        rc = _run_cli(["run", "--no-approve", "--no-ask", "needs my approval"])
    states, _ = _states(d)
    log = EventLog(d / ".psf" / "factory.db")
    wf = Workflow(log)
    wid = log.work_ids()[0]
    approved = wf.approve_spec(wf.fold(wid), approver="owner")
    log.close()
    ok = rc == 3 and states == ["SPEC_REVIEW"] and approved.state == "READY"
    return EvalResult("X2", "spec-review wait -> approval -> READY", "pass" if ok else "fail",
                      {"state": states, "after_approval": approved.state})


def eval_X3(tmp: Path) -> EvalResult:
    """YOLO mode auto-approves and completes without a human."""
    d = _repo(tmp, "x3")
    with _in(d):
        assert _run_cli(["init", "--feedback", "off", "--mode", "yolo"]) == 0
        rc = _run_cli(["run", "--git", "--no-ask", "autonomous feature"])
    states, _ = _states(d)
    ok = rc == 0 and states == ["DONE"]
    return EvalResult("X3", "YOLO end-to-end", "pass" if ok else "fail", {"state": states})


def eval_X4(tmp: Path) -> EvalResult:
    """Cancel and unblock through the CLI."""
    d = _repo(tmp, "x4")
    with _in(d):
        _run_cli(["init", "--feedback", "off", "--mode", "hitl"])
        _run_cli(["run", "--no-approve", "--no-ask", "to cancel"])
        wid = EventLog(d / ".psf" / "factory.db").work_ids()[0]
        rc_cancel = _run_cli(["cancel", wid, "--reason", "no longer needed"])
        # create + block + unblock
        from .events import EventLog as EL
        from .state import Workflow as WF
        log = EL(d / ".psf" / "factory.db")
        w = WF(log).create("block me")
        w = WF(log).transition(w, "TRIAGE")
        w = WF(log).transition(w, "SPEC")
        w = WF(log).transition(w, "BLOCKED", reason="wait")
        log.close()
        rc_unblock = _run_cli(["unblock", w.id])
    states, _ = _states(d)
    log = EventLog(d / ".psf" / "factory.db")
    wf = Workflow(log)
    final = {wf.fold(x).id: wf.fold(x).state for x in log.work_ids()}
    log.close()
    ok = rc_cancel == 0 and rc_unblock == 0 and final.get(wid) == "CANCELLED" and final.get(w.id) == "SPEC"
    return EvalResult("X4", "cancel + unblock via CLI", "pass" if ok else "fail", {"final": final})


def eval_X5(tmp: Path) -> EvalResult:
    """Feedback export produces a privacy-filtered envelope; chain intact."""
    d = _repo(tmp, "x5")
    with _in(d):
        _run_cli(["init", "--feedback", "hint", "--mode", "yolo"])
        _run_cli(["run", "--no-ask", "secret project goal wording"])
        rc = _run_cli(["feedback", "export"])
    envs = sorted((d / ".psf" / "feedback").glob("FB-*.json"))
    text = envs[0].read_text() if envs else ""
    ok = rc == 0 and envs and "secret project goal wording" not in text and "work_items" in text
    return EvalResult("X5", "feedback export (privacy-filtered)", "pass" if ok else "fail",
                      {"envelopes": len(envs)})


def eval_X6(tmp: Path) -> EvalResult:
    """Eval governance end-to-end: add -> approve -> rotate -> status."""
    d = _repo(tmp, "x6")
    with _in(d):
        _run_cli(["init", "--feedback", "off"])
        a = _run_cli(["evals", "add", "--case-id", "cX", "--goal", "add a thing",
                      "--source", "issue#1", "--owner", "me"])
        b = _run_cli(["evals", "approve", "--case-id", "cX", "--approver", "reviewer", "--author", "me"])
        c = _run_cli(["evals", "rotate", "--n", "1", "--approver", "reviewer", "--author", "me"])
        s = _run_cli(["evals", "status"])
    ok = 0 == a == b == c == s
    return EvalResult("X6", "eval governance CLI", "pass" if ok else "fail", {"rc": [a, b, c, s]})


def eval_X7(tmp: Path) -> EvalResult:
    """Self-improvement end-to-end through the CLI: promote then rollback."""
    d = _repo(tmp, "x7")
    yml = None
    with _in(d):
        _run_cli(["init", "--feedback", "off", "--mode", "hitl"])
        rc_promote = _run_cli(["improve", "--promote"])
        yml = (d / "factory" / "factory.yml").read_text()
        rc_rollback = _run_cli(["improve", "--rollback"])
        yml_after = (d / "factory" / "factory.yml").read_text()
    ok = rc_promote == 0 and rc_rollback == 0 and "max_attempts: 3" in yml and yml_after != yml
    return EvalResult("X7", "improve promote -> rollback", "pass" if ok else "fail",
                      {"promoted": "max_attempts: 3" in yml})


def eval_X8(tmp: Path) -> EvalResult:
    """Health check runs end-to-end on a fresh repo and is green."""
    d = _repo(tmp, "x8")
    with _in(d):
        _run_cli(["init", "--feedback", "off"])
        rc = _run_cli(["audit"])
    ok = rc == 0
    return EvalResult("X8", "psf audit (health) on fresh repo", "pass" if ok else "fail", {"rc": rc})


def eval_X9(tmp: Path) -> EvalResult:
    """Feedback transfer, offline: consumer export -> ingest -> report.

    Proves a consumer's usage signal reaches the main repo's inbox and is
    aggregated, and that the envelope carries counts/digests only (no goals,
    paths, or source).
    """
    from .feedback import ingest, report

    consumer = _repo(tmp, "x9c")
    main = _repo(tmp, "x9m")
    goal = "SENTINEL_GOAL_add_gizmo"
    with _in(consumer):
        _run_cli(["init", "--feedback", "hint", "--mode", "yolo"])
        _run_cli(["run", "--no-ask", "--mode", "yolo", goal])
        rc = _run_cli(["feedback", "export", "--out", str(consumer / "export.json")])
        env_text = (consumer / "export.json").read_text()
    n = ingest(main / ".psf" / "feedback" / "inbox", consumer / "export.json")
    rep = report(main / ".psf" / "feedback" / "inbox")
    leaked = goal in env_text
    ok = (rc == 0 and n == 1 and rep["envelopes"] == 1
          and rep["totals"]["work_items"] >= 1 and not leaked)
    return EvalResult("X9", "feedback: consumer export -> ingest -> report",
                      "pass" if ok else "fail",
                      {"ingested": n, "envelopes": rep["envelopes"],
                       "work_items": rep["totals"]["work_items"], "leaked_goal": leaked})


def eval_X10(tmp: Path) -> EvalResult:
    """Feedback intake from GitHub issues (deterministic, no network).

    A `factory-feedback` issue body carries the envelope in a ```json fence;
    `ingest_issues` extracts it into the inbox and it shows up in the report.
    """
    from . import github
    from .feedback import build_envelope, ingest_issues, report

    main = _repo(tmp, "x10m")
    with _in(main):
        _run_cli(["init", "--feedback", "off"])
    env = build_envelope(main / "factory", main / ".psf" / "factory.db", repo="acme/app")
    env["metrics"]["work_items"] = 5
    env["metrics"]["blocked"] = 2
    body = ("Automated feedback envelope\n\n```json\n"
            + __import__("json").dumps(env, indent=2) + "\n```\n")
    issue = {"number": 7, "title": "feedback", "body": body,
             "labels": [{"name": "factory-feedback"}]}
    old = github.list_issues
    github.list_issues = lambda *a, **k: [issue]
    try:
        n = ingest_issues(main / ".psf" / "feedback" / "inbox", repo="acme/app")
    finally:
        github.list_issues = old
    rep = report(main / ".psf" / "feedback" / "inbox")
    ok = n == 1 and rep["envelopes"] == 1 and rep["totals"]["blocked"] == 2
    return EvalResult("X10", "feedback: ingest factory-feedback issues",
                      "pass" if ok else "fail",
                      {"ingested": n, "blocked": rep["totals"]["blocked"]})


def eval_X11(tmp: Path) -> EvalResult:
    """Feedback transfer, live: file a real issue and read it back.

    Gated on PSF_FEEDBACK_LIVE_REPO to avoid touching a repo in normal runs;
    on success the transient issue is closed again.
    """
    repo = os.environ.get("PSF_FEEDBACK_LIVE_REPO")
    if not repo:
        return EvalResult("X11", "feedback: live GitHub round-trip", "pass",
                          {"skipped": "set PSF_FEEDBACK_LIVE_REPO=owner/repo"})
    from .feedback import build_envelope, ingest_issues, publish_issue, report

    main = _repo(tmp, "x11m")
    with _in(main):
        _run_cli(["init", "--feedback", "off"])
    env = build_envelope(main / "factory", main / ".psf" / "factory.db", repo=repo)
    url, err = publish_issue(repo, env)
    if not url:
        return EvalResult("X11", "feedback: live GitHub round-trip", "fail", {"error": err})
    try:
        n = ingest_issues(main / ".psf" / "feedback" / "inbox", repo=repo)
        rep = report(main / ".psf" / "feedback" / "inbox")
    finally:
        num = url.rstrip("/").split("/")[-1]
        subprocess.run(["gh", "issue", "close", num, "-R", repo, "-c", "e2e"],
                       capture_output=True, check=False)
    ok = n >= 1 and rep["envelopes"] >= 1
    return EvalResult("X11", "feedback: live GitHub round-trip", "pass" if ok else "fail",
                      {"url": url, "ingested": n})


def run_e2e() -> dict:
    evals = []
    with tempfile.TemporaryDirectory(prefix="psf-e2e-") as d:
        tmp = Path(d)
        for fn in (eval_X1, eval_X2, eval_X3, eval_X4, eval_X5, eval_X6, eval_X7,
                   eval_X8, eval_X9, eval_X10, eval_X11):
            try:
                evals.append(fn(tmp))
            except Exception as e:  # noqa: BLE001
                evals.append(EvalResult(fn.__name__, fn.__name__, "fail", {"error": repr(e)}))
    passed = sum(1 for e in evals if e.status == "pass")
    issues = [{"id": e.id, "name": e.name, "detail": e.detail} for e in evals if e.status != "pass"]
    return {"passed": passed, "failed": len(evals) - passed, "total": len(evals),
            "evals": [{"id": e.id, "name": e.name, "status": e.status, "detail": e.detail} for e in evals],
            "issues": issues}
