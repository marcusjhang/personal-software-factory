from psf.selfeval import run_self_eval


def test_self_eval_runs_and_reports():
    rep = run_self_eval()
    assert rep["total"] == 26
    assert rep["passed"] + rep["failed"] == rep["total"]
    assert isinstance(rep["issues"], list)
    ids = {e["id"] for e in rep["evals"]}
    assert ids == {"E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "E10", "E11",
                   "E12", "E13", "E14", "E15", "E16", "E17", "E18", "E19", "E20", "E21",
                   "E22", "E23", "E24", "E25", "E26"}
