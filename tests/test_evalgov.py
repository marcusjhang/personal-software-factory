import pytest

from psf.evalgov import (add_candidate, approve_candidate, integrity, retire_case,
                         rotate_holdout, run_governance_eval, status, _temp_eval)


def test_governance_eval_suite():
    rep = run_governance_eval()
    assert rep["total"] == 8
    assert rep["passed"] + rep["failed"] == rep["total"]
    assert rep["failed"] == 0, rep["issues"]


def test_governance_lifecycle_end_to_end(tmp_path):
    d = _temp_eval(tmp_path)
    add_candidate(d, case_id="c1", goal="add z", solves_on_attempt=2, source="F1", owner="o")
    assert status(d)["candidate"] == 1
    # provenance and self-approval are enforced
    with pytest.raises(ValueError):
        add_candidate(d, case_id="c2", goal="add w", solves_on_attempt=1, source="", owner="o")
    with pytest.raises(ValueError):
        approve_candidate(d, "c1", approver="o", author="o")
    approve_candidate(d, "c1", approver="bob", author="o")
    assert status(d)["optimization"] == 2
    rotate_holdout(d, n=1, approver="bob", author="o")
    assert integrity(d) == []
    retire_case(d, "h1", reason="superseded", approver="bob", author="o")
    assert status(d)["retired"] >= 1
    with pytest.raises(ValueError):
        retire_case(d, "e1", reason="", approver="bob", author="o")
