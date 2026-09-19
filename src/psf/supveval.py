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


def eval_S9(tmp: Path) -> EvalResult:
    """Integrated: an escalation from the supervisor blocks the item (needs human)."""
    from .agents import AgentResult, MockRunner
    from .events import EventLog
    from .foreman import Foreman
    from .schema import Factory
    from .state import Workflow

    class Failing(MockRunner):
        def run(self, task):
            if task.role == "verify":
                return AgentResult(False, {"passed": False, "findings": ["nope"]})
            return super().run(task)

    f = Factory(name="s9", schema_version="psf/v1", path=tmp / "factory.yml", mode="yolo",
                gates={"spec_approval": True, "verify_quorum": 1}, limits={"max_attempts": 3},
                classifier={"provider": "mock", "supervisor": {"enabled": True}})
    log = EventLog(tmp / "s9.db")
    clf = MockClassifier({"needs_human": 0.95})
    res = Foreman(f, Workflow(log), Failing(), classifier=clf).run("g", finish=False)
    types = [e.type for e in log.for_work(res.work.id)]
    log.close()
    ok = res.work.state == "BLOCKED" and "Escalated" in types and "HandoffProduced" not in types
    return EvalResult("S9", "integrated escalation blocks", "pass" if ok else "fail",
                      {"state": res.work.state, "events": [t for t in types if t.startswith(("Supervisor", "Worker", "Escalat"))]})


def eval_S10(tmp: Path) -> EvalResult:
    """Integrated: a STEER delivers guidance into the next implement attempt."""
    from .agents import AgentResult, MockRunner
    from .events import EventLog
    from .foreman import Foreman
    from .schema import Factory
    from .state import Workflow

    seen: list[list[str]] = []

    class Failing(MockRunner):
        def run(self, task):
            if task.role == "implement":
                seen.append(list(task.feedback or []))
            if task.role == "verify":
                return AgentResult(False, {"passed": False, "findings": ["nope"]})
            return super().run(task)

    f = Factory(name="s10", schema_version="psf/v1", path=tmp / "factory.yml", mode="yolo",
                gates={"spec_approval": True, "verify_quorum": 1}, limits={"max_attempts": 3},
                classifier={"provider": "mock", "supervisor": {"enabled": True, "max_steers": 1, "max_retries": 0}})
    log = EventLog(tmp / "s10.db")
    clf = MockClassifier({"worker_stuck": 0.95})
    Foreman(f, Workflow(log), Failing(), classifier=clf).run("g", finish=False)
    log.close()
    steered = any(any("supervisor: steer" in fb for fb in attempt) for attempt in seen)
    return EvalResult("S10", "steer reaches the next attempt", "pass" if steered else "fail",
                      {"attempts": len(seen), "steered": steered})


def eval_S11(tmp: Path) -> EvalResult:
    """Disabled by default: no supervisor events when not enabled."""
    from .agents import AgentResult, MockRunner
    from .events import EventLog
    from .foreman import Foreman
    from .schema import Factory
    from .state import Workflow

    class Failing(MockRunner):
        def run(self, task):
            if task.role == "verify":
                return AgentResult(False, {"passed": False, "findings": ["nope"]})
            return super().run(task)

    f = Factory(name="s11", schema_version="psf/v1", path=tmp / "factory.yml", mode="yolo",
                gates={"spec_approval": True, "verify_quorum": 1}, limits={"max_attempts": 2},
                classifier={"provider": "mock", "supervisor": {"enabled": False}})
    log = EventLog(tmp / "s11.db")
    res = Foreman(f, Workflow(log), Failing()).run("g", finish=False)
    types = [e.type for e in log.for_work(res.work.id)]
    log.close()
    ok = res.work.state == "BLOCKED" and not any(t.startswith("Supervisor") or t.startswith("Worker") or t == "Escalated" for t in types)
    return EvalResult("S11", "supervisor off by default", "pass" if ok else "fail",
                      {"state": res.work.state, "supervisor_events": [t for t in types if t.startswith("Supervisor")]})


def eval_S12(tmp: Path) -> EvalResult:
    """The supervisor can never FINISH a failing item, whatever it predicts."""
    from .agents import AgentResult, MockRunner
    from .events import EventLog
    from .foreman import Foreman
    from .schema import Factory
    from .state import Workflow

    class Failing(MockRunner):
        def run(self, task):
            if task.role == "verify":
                return AgentResult(False, {"passed": False, "findings": ["nope"]})
            return super().run(task)

    f = Factory(name="s12", schema_version="psf/v1", path=tmp / "factory.yml", mode="yolo",
                gates={"spec_approval": True, "verify_quorum": 1}, limits={"max_attempts": 2},
                classifier={"provider": "mock", "supervisor": {"enabled": True}})
    log = EventLog(tmp / "s12.db")
    clf = MockClassifier({"worker_stuck": 0.0, "work_off_track": 0.0, "needs_human": 0.0,
                          "meaningful_progress": 1.0})  # says all-good, but verify fails
    res = Foreman(f, Workflow(log), Failing(), classifier=clf).run("g", finish=False)
    types = [e.type for e in log.for_work(res.work.id)]
    log.close()
    ok = res.work.state == "BLOCKED" and "HandoffProduced" not in types
    return EvalResult("S12", "classifier cannot finish unverified work", "pass" if ok else "fail",
                      {"state": res.work.state})


def eval_C1(tmp: Path) -> EvalResult:
    """Calibration: the threshold sweep recovers a separable signal."""
    from .calibrate import sweep
    records = [{"score": 0.9, "label": 1}, {"score": 0.85, "label": 1},
               {"score": 0.2, "label": 0}, {"score": 0.1, "label": 0}]
    r = sweep(records)
    ok = r["accuracy"] == 1.0 and 0.2 < r["best_threshold"] <= 0.85
    return EvalResult("C1", "threshold sweep recovers signal", "pass" if ok else "fail", r)


def eval_C2(tmp: Path) -> EvalResult:
    """Calibration: reliability reports low ECE for a calibrated set."""
    from .calibrate import reliability
    records = [{"score": 0.9, "label": 1}, {"score": 0.8, "label": 1}] * 5 + \
              [{"score": 0.1, "label": 0}, {"score": 0.2, "label": 0}] * 5
    r = reliability(records, bins=5)
    ok = r["ece"] <= 0.25
    return EvalResult("C2", "reliability ECE computed", "pass" if ok else "fail", {"ece": r["ece"]})


def eval_S13(tmp: Path) -> EvalResult:
    """Performance/cost: at most one assessment per retry; calls bounded by attempts."""
    from .agents import AgentResult, MockRunner
    from .events import EventLog
    from .foreman import Foreman
    from .schema import Factory
    from .state import Workflow

    class Failing(MockRunner):
        def run(self, task):
            if task.role == "verify":
                return AgentResult(False, {"passed": False, "findings": ["nope"]})
            return super().run(task)

    f = Factory(name="s13", schema_version="psf/v1", path=tmp / "factory.yml", mode="yolo",
                gates={"spec_approval": True, "verify_quorum": 1}, limits={"max_attempts": 4},
                classifier={"provider": "mock", "supervisor": {"enabled": True, "max_steers": 1, "max_retries": 1}})
    log = EventLog(tmp / "s13.db")
    clf = CountingClassifier(MockClassifier({"worker_stuck": 0.9}))
    res = Foreman(f, Workflow(log), Failing(), classifier=clf).run("g", finish=False)
    assessed = sum(1 for e in log.for_work(res.work.id) if e.type == "SupervisorAssessed")
    log.close()
    # one assessment per retry, bounded by (max_attempts - 1) = 3 here
    ok = clf.calls() == assessed <= 3
    return EvalResult("S13", "cost bounded by retries", "pass" if ok else "fail",
                      {"calls": clf.calls(), "assessed": assessed, "attempts": res.work.attempts})


def eval_C3(tmp: Path) -> EvalResult:
    """Calibration records can be derived from the ledger."""
    from .agents import AgentResult, MockRunner
    from .calibrate import records_from_ledger, sweep
    from .events import EventLog
    from .foreman import Foreman
    from .schema import Factory
    from .state import Workflow

    class Failing(MockRunner):
        def run(self, task):
            if task.role == "verify":
                return AgentResult(False, {"passed": False, "findings": ["nope"]})
            return super().run(task)

    f = Factory(name="c3", schema_version="psf/v1", path=tmp / "factory.yml", mode="yolo",
                gates={"spec_approval": True, "verify_quorum": 1}, limits={"max_attempts": 2},
                classifier={"provider": "mock", "supervisor": {"enabled": True}})
    log = EventLog(tmp / "c3.db")
    Foreman(f, Workflow(log), Failing(), classifier=MockClassifier({"worker_stuck": 0.9})).run("g", finish=False)
    recs = records_from_ledger(log)
    log.close()
    ok = len(recs) >= 1 and sweep(recs)["n"] == len(recs)
    return EvalResult("C3", "records from ledger", "pass" if ok else "fail",
                      {"records": recs, "sweep": sweep(recs)} if recs else {"records": []})


def run_supervisor_eval() -> dict:
    evals = []
    with tempfile.TemporaryDirectory(prefix="psf-sup-") as d:
        tmp = Path(d)
        for fn in (eval_S1, eval_S2, eval_S3, eval_S4, eval_S5, eval_S6, eval_S7, eval_S8,
                   eval_S9, eval_S10, eval_S11, eval_S12, eval_S13, eval_C1, eval_C2, eval_C3):
            try:
                evals.append(fn(tmp))
            except Exception as e:  # noqa: BLE001
                evals.append(EvalResult(fn.__name__, fn.__name__, "fail", {"error": repr(e)}))
    passed = sum(1 for e in evals if e.status == "pass")
    issues = [{"id": e.id, "name": e.name, "detail": e.detail} for e in evals if e.status != "pass"]
    return {"passed": passed, "failed": len(evals) - passed, "total": len(evals),
            "evals": [{"id": e.id, "name": e.name, "status": e.status, "detail": e.detail} for e in evals],
            "issues": issues}
