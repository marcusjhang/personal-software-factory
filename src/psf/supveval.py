"""Supervisor / classifier eval suite (S1..S8).

Offline and deterministic (MockClassifier). Proves the advisory-only contract,
bounded intervention, uncertainty handling, fail-closed behaviour, privacy
bounds, and the one-call cost model.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .classifier import CountingClassifier, ErrorClassifier, MockClassifier, Noul
from .evalkit import EvalResult
from .supervisor import DEFAULT_THRESHOLDS, SupervisorState, decide, evidence_bundle, supervise_step


def _answers(signals: dict) -> dict:
    return MockClassifier(signals).ask({}, {"needs_human": Noul("x"), "work_off_track": Noul("x"),
                                            "worker_stuck": Noul("x"), "meaningful_progress": Noul("x")})


def eval_S1(tmp: Path) -> EvalResult:
    """Advisory-only: the classifier can never FINISH; only the verifier can."""
    all_yes = _answers({"needs_human": 0.0, "work_off_track": 1.0, "worker_stuck": 1.0,
                        "meaningful_progress": 1.0})
    unverified = SupervisorState(verified=False)
    d1 = decide(all_yes, unverified)
    verified = SupervisorState(verified=True)
    d2 = decide(all_yes, verified)
    ok = d1.action != "FINISH" and d2.action == "FINISH"
    return EvalResult("S1", "advisory-only (no self-finish)", "pass" if ok else "fail",
                      {"unverified_action": d1.action, "verified_action": d2.action})


def eval_S2(tmp: Path) -> EvalResult:
    """Determinism: same evidence + state -> same decision."""
    clf = MockClassifier({"worker_stuck": 0.9})
    ev = evidence_bundle(goal="g", status="running", diff="+ x")
    a = supervise_step(clf, ev, SupervisorState())
    b = supervise_step(clf, ev, SupervisorState())
    ok = (a.action, a.reason) == (b.action, b.reason)
    return EvalResult("S2", "deterministic decisions", "pass" if ok else "fail",
                      {"a": a.action, "b": b.action})


def eval_S3(tmp: Path) -> EvalResult:
    """Stuck detection: stop a stuck worker, continue a progressing one."""
    stuck = decide(_answers({"worker_stuck": 0.95}), SupervisorState())
    ok_progress = decide(_answers({"worker_stuck": 0.10, "meaningful_progress": 0.9}),
                         SupervisorState())
    ok = stuck.action in ("STEER", "STOP", "RETRY") and ok_progress.action == "CONTINUE"
    return EvalResult("S3", "stuck vs progressing", "pass" if ok else "fail",
                      {"stuck_action": stuck.action, "progress_action": ok_progress.action})


def eval_S4(tmp: Path) -> EvalResult:
    """Bounded, no oscillation: at most max_steers steers, then stop/retry."""
    st = SupervisorState(max_steers=1, max_retries=1)
    seq = []
    for _ in range(6):
        d = decide(_answers({"worker_stuck": 0.95}), st)
        seq.append(d.action)
        if d.action == "STEER":
            st.steers += 1
            st.last_action = "STEER"
        elif d.action == "RETRY":
            st.retries += 1
            st.last_action = "RETRY"
        elif d.action == "STOP":
            break
    steers = seq.count("STEER")
    no_osc = "STEER" not in seq[seq.index("STOP"):] if "STOP" in seq else True
    ok = steers <= 1 and "STOP" in seq and no_osc
    return EvalResult("S4", "bounded / no oscillation", "pass" if ok else "fail",
                      {"sequence": seq, "steers": steers})


def eval_S5(tmp: Path) -> EvalResult:
    """Uncertainty below threshold does nothing (no guessing)."""
    d = decide(_answers({"worker_stuck": 0.5, "work_off_track": 0.5}), SupervisorState())
    ok = d.action == "CONTINUE"
    return EvalResult("S5", "uncertainty -> no action", "pass" if ok else "fail",
                      {"action": d.action, "threshold": DEFAULT_THRESHOLDS["stuck"]})


def eval_S6(tmp: Path) -> EvalResult:
    """Fail closed: a classifier error means no intervention."""
    d = supervise_step(ErrorClassifier(), {"goal": "g"}, SupervisorState())
    ok = d.action == "CONTINUE" and d.reason.startswith("fail_closed")
    return EvalResult("S6", "fail-closed on classifier error", "pass" if ok else "fail",
                      {"action": d.action, "reason": d.reason})


def eval_S7(tmp: Path) -> EvalResult:
    """Privacy: evidence is bounded and secrets are redacted."""
    ev = evidence_bundle(goal="g", status="run", diff="SECRET" + "x" * 50000,
                         output_tail="SECRET" + "y" * 50000, redact=("SECRET",))
    ok = "SECRET" not in ev["diff"] and len(ev["diff"]) <= 20000 and len(ev["output_tail"]) <= 12000
    return EvalResult("S7", "bounded + redacted evidence", "pass" if ok else "fail",
                      {"diff_len": len(ev["diff"]), "tail_len": len(ev["output_tail"]),
                       "secret_present": "SECRET" in ev["diff"]})


def eval_S8(tmp: Path) -> EvalResult:
    """Cost: one batched classifier call per assessment."""
    clf = CountingClassifier(MockClassifier({"worker_stuck": 0.9}))
    supervise_step(clf, {"goal": "g"}, SupervisorState())
    ok = clf.calls() == 1
    return EvalResult("S8", "one call per assessment", "pass" if ok else "fail",
                      {"calls": clf.calls()})


def run_supervisor_eval() -> dict:
    evals = []
    with tempfile.TemporaryDirectory(prefix="psf-sup-") as d:
        tmp = Path(d)
        for fn in (eval_S1, eval_S2, eval_S3, eval_S4, eval_S5, eval_S6, eval_S7, eval_S8):
            try:
                evals.append(fn(tmp))
            except Exception as e:  # noqa: BLE001
                evals.append(EvalResult(fn.__name__, fn.__name__, "fail", {"error": repr(e)}))
    passed = sum(1 for e in evals if e.status == "pass")
    issues = [{"id": e.id, "name": e.name, "detail": e.detail} for e in evals if e.status != "pass"]
    return {"passed": passed, "failed": len(evals) - passed, "total": len(evals),
            "evals": [{"id": e.id, "name": e.name, "status": e.status, "detail": e.detail} for e in evals],
            "issues": issues}
