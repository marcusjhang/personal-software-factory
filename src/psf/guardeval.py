"""Guardrail evals (H1..H6).

Proof that each guardrail actually fires — including *mutation* checks that inject
a violation and assert the guard detects it (so the evals are demonstrated to be
sensitive, not merely asserted).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .agents import MockRunner
from .audit import run_audit
from .evalkit import EvalResult, make_factory
from .events import EventLog
from .foreman import Foreman
from .schema import Factory, load as load_factory
from .state import Workflow


def _mk(tmp: Path, name: str, *, gates=None, limits=None) -> tuple[Factory, EventLog]:
    root = tmp / name
    make_factory(root, max_attempts=2)
    factory = load_factory(root)
    if gates:
        factory.gates.update(gates)
    if limits:
        factory.limits.update(limits)
    return factory, EventLog(tmp / f"{name}.db")


def eval_H1(tmp: Path) -> EvalResult:
    """An illegal transition injected into the ledger is caught by audit (mutation)."""
    _, log = _mk(tmp, "h1")
    log.append("WorkCreated", {"goal": "g", "max_attempts": 2}, work_id="W1")
    log.append("StateChanged", {"from": "INTAKE", "to": "BUILD", "reason": "forged"}, work_id="W1")
    checks = {c.name: c.status for c in run_audit(tmp / "h1", tmp / "h1.db", include_bench=False).checks}
    ok = checks.get("state.illegal_transitions") == "fail"
    log.close()
    return EvalResult("H1", "illegal transition detected by audit", "pass" if ok else "fail", checks)


def eval_H2(tmp: Path) -> EvalResult:
    """A READY state without a digest-bound approval is caught by audit (mutation)."""
    _, log = _mk(tmp, "h2")
    for e in (("WorkCreated", {"goal": "g", "max_attempts": 2}),
              ("StateChanged", {"from": "INTAKE", "to": "TRIAGE", "reason": ""}),
              ("StateChanged", {"from": "TRIAGE", "to": "SPEC", "reason": ""}),
              ("SpecProduced", {"spec": {"title": "t"}, "digest": "sha256:x"}),
              ("StateChanged", {"from": "SPEC", "to": "READY", "reason": "forged"})):
        log.append(e[0], e[1], work_id="W1")
    checks = {c.name: c.status for c in run_audit(tmp / "h2", tmp / "h2.db", include_bench=False).checks}
    ok = checks.get("state.digest_bound_approval") == "fail"
    log.close()
    return EvalResult("H2", "unapproved READY detected by audit", "pass" if ok else "fail", checks)


def eval_H3(tmp: Path) -> EvalResult:
    """Ledger tampering breaks the hash chain (mutation)."""
    _, log = _mk(tmp, "h3")
    log.append("WorkCreated", {"goal": "g", "max_attempts": 2}, work_id="W1")
    log.conn.execute("UPDATE events SET payload='{\"goal\":\"hacked\"}' WHERE seq=1")
    log.conn.commit()
    ok, _ = log.verify_chain()
    log.close()
    return EvalResult("H3", "ledger tamper detected", "pass" if not ok else "fail", {})


def eval_H4(tmp: Path) -> EvalResult:
    """A failing deterministic verify_command blocks the work item."""
    factory, log = _mk(tmp, "h4", gates={"spec_approval": True, "verify_quorum": 1,
                                         "verify_command": "false"})
    res = Foreman(factory, Workflow(log), MockRunner()).run("g", finish=False)
    ok = res.work.state == "BLOCKED"
    log.close()
    return EvalResult("H4", "deterministic verify gate blocks", "pass" if ok else "fail",
                      {"state": res.work.state})


def eval_H5(tmp: Path) -> EvalResult:
    """A wall-clock budget overrun blocks the work item."""
    factory, log = _mk(tmp, "h5", gates={"spec_approval": False, "verify_quorum": 1},
                       limits={"max_minutes": 1e-9})
    res = Foreman(factory, Workflow(log), MockRunner()).run("g", finish=False)
    ok = res.work.state == "BLOCKED"
    log.close()
    return EvalResult("H5", "max_minutes budget blocks", "pass" if ok else "fail",
                      {"state": res.work.state})


def eval_H6(tmp: Path) -> EvalResult:
    """Cancel is reachable; BLOCKED unblocks only to its saved prior state."""
    _, log = _mk(tmp, "h6")
    wf = Workflow(log)
    w = wf.create("g")
    w = wf.transition(w, "TRIAGE")
    w = wf.transition(w, "SPEC")
    blocked = wf.transition(w, "BLOCKED", reason="wait")
    back = wf.transition(blocked, "SPEC", reason="unblock")
    cancelled = wf.transition(back, "CANCELLED", reason="stop")
    wrong = False
    try:
        wf.transition(blocked, "TRIAGE", reason="skip gate")  # not the saved state
    except Exception:  # noqa: BLE001
        wrong = True
    ok = blocked.state == "BLOCKED" and back.state == "SPEC" and cancelled.state == "CANCELLED" and wrong
    log.close()
    return EvalResult("H6", "cancel + unblock-to-saved-state", "pass" if ok else "fail",
                      {"blocked": blocked.state, "back": back.state})


def run_guardrail_eval() -> dict:
    evals = []
    with tempfile.TemporaryDirectory(prefix="psf-guard-") as d:
        tmp = Path(d)
        for fn in (eval_H1, eval_H2, eval_H3, eval_H4, eval_H5, eval_H6):
            try:
                evals.append(fn(tmp))
            except Exception as e:  # noqa: BLE001
                evals.append(EvalResult(fn.__name__, fn.__name__, "fail", {"error": repr(e)}))
    passed = sum(1 for e in evals if e.status == "pass")
    issues = [{"id": e.id, "name": e.name, "detail": e.detail} for e in evals if e.status != "pass"]
    return {"passed": passed, "failed": len(evals) - passed, "total": len(evals),
            "evals": [{"id": e.id, "name": e.name, "status": e.status, "detail": e.detail} for e in evals],
            "issues": issues}
