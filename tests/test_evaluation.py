import json

from psf.evaluation import candidate_touches_protected, manifest_digest, run_eval


def _eval_dir(tmp_path):
    d = tmp_path / "eval"
    d.mkdir()
    (d / "tasks.json").write_text(json.dumps({"tasks": [
        {"id": "a", "goal": "g1", "solves_on_attempt": 1},
        {"id": "b", "goal": "g2", "solves_on_attempt": 2},
        {"id": "c", "goal": "g3", "solves_on_attempt": 3},
        {"id": "d", "goal": "g4", "solves_on_attempt": 3},
    ]}))
    (d / "thresholds.json").write_text(json.dumps({"metric": "pass_rate", "epsilon": 0.0, "n_min": 3}))
    return d


def test_eval_promotes_when_candidate_improves(tmp_path):
    ev = run_eval(_eval_dir(tmp_path), baseline_attempts=2, candidate_attempts=3)
    assert ev.decision == "PROMOTE"
    assert ev.n_scored == 4
    assert ev.candidate_rate > ev.baseline_rate
    assert ev.ci_low >= 0


def test_eval_rejects_when_candidate_worse(tmp_path):
    ev = run_eval(_eval_dir(tmp_path), baseline_attempts=3, candidate_attempts=1)
    assert ev.decision == "REJECT"
    assert any("non-inferiority" in r or "ci_low" in r for r in ev.reasons)


def test_protected_paths_and_manifest_change(tmp_path):
    d = _eval_dir(tmp_path)
    assert candidate_touches_protected(["eval/tasks.json"])
    assert candidate_touches_protected(["eval/judge/prompt.md"])
    assert not candidate_touches_protected(["src/psf/cli.py", "factory/factory.yml"])
    before = manifest_digest(d)
    (d / "tasks.json").write_text(json.dumps({"tasks": [{"id": "z", "goal": "x", "solves_on_attempt": 1}]}))
    assert manifest_digest(d) != before
