from psf.e2e import run_e2e


def test_e2e_suite():
    rep = run_e2e()
    assert rep["total"] == 8 and rep["failed"] == 0, rep["issues"]
