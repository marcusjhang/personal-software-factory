from psf.selfeval import run_self_eval


def test_self_eval_runs_and_reports():
    rep = run_self_eval()
    assert rep["total"] == 8
    assert rep["passed"] + rep["failed"] == rep["total"]
    assert isinstance(rep["issues"], list)
    ids = {e["id"] for e in rep["evals"]}
    assert ids == {"E2", "E5", "E6", "E7", "E10", "E15", "E16", "E19"}
