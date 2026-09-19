from psf.classifier import MockClassifier, build_classifier
from psf.supervisor import SupervisorState, decide, evidence_bundle, supervise_step
from psf.supveval import run_supervisor_eval


def test_supervisor_eval_suite():
    rep = run_supervisor_eval()
    assert rep["total"] == 16
    assert rep["failed"] == 0, rep["issues"]


def test_classifier_providers():
    assert isinstance(build_classifier({}), MockClassifier)
    assert isinstance(build_classifier({"provider": "mock"}), MockClassifier)
    try:
        build_classifier({"provider": "nope"})
        assert False
    except ValueError:
        pass


def test_finish_requires_verification():
    from psf.classifier import Answer
    yes = {k: Answer("noul", 1.0) for k in ("needs_human", "worker_stuck", "work_off_track", "meaningful_progress")}
    yes["needs_human"] = Answer("noul", 0.0)
    assert decide(yes, SupervisorState(verified=False)).action != "FINISH"
    assert decide(yes, SupervisorState(verified=True)).action == "FINISH"


def test_evidence_redacts_and_bounds():
    ev = evidence_bundle(goal="g", status="s", diff="TOKEN" + "z" * 40000, redact=("TOKEN",))
    assert "TOKEN" not in ev["diff"] and len(ev["diff"]) <= 20000
