import sqlite3
from pathlib import Path

import pytest

from psf.agents import AgentResult, AgentTask, MockRunner
from psf.bench import BenchTask, ScriptedRunner, run_benchmark
from psf.canonical import digest
from psf.events import EventLog
from psf.foreman import Foreman
from psf.schema import Factory, validate
from psf.state import GateError, Workflow


def make_factory(tmp_path: Path, *, spec_approval=False, max_attempts=2) -> Factory:
    (tmp_path / "agents").mkdir(exist_ok=True)
    for role in ("triage", "spec", "implement", "verify", "review"):
        (tmp_path / "agents" / f"{role}.md").write_text("prompt")
    return Factory(
        name="t", schema_version="psf/v1", path=tmp_path / "factory.yml",
        runner="mock", gates={"spec_approval": spec_approval}, limits={"max_attempts": max_attempts},
    )


def test_digest_is_stable():
    assert digest({"b": 1, "a": 2}) == digest({"a": 2, "b": 1})
    assert digest({"a": 1}) != digest({"a": 2})


def test_ledger_chain_and_tamper(tmp_path):
    log = EventLog(tmp_path / "e.db")
    log.append("A", {"x": 1}, work_id="W1")
    log.append("B", {"y": 2}, work_id="W1")
    ok, msg = log.verify_chain()
    assert ok, msg
    # tamper directly
    log.conn.execute("UPDATE events SET payload='{\"x\":999}' WHERE seq=1")
    log.conn.commit()
    ok, _ = log.verify_chain()
    assert not ok


def test_schema_validation(tmp_path):
    good = {
        "schemaVersion": "psf/v1", "name": "x",
        "agents": {r: {"prompt": f"agents/{r}.md"} for r in ("triage", "spec", "implement", "verify", "review")},
    }
    (tmp_path / "agents").mkdir()
    for r in ("triage", "spec", "implement", "verify", "review"):
        (tmp_path / "agents" / f"{r}.md").write_text("p")
    assert validate(good, base_dir=tmp_path) == []
    bad = dict(good)
    bad["agents"] = {"triage": {"prompt": "agents/triage.md"}}
    errors = validate(bad, base_dir=tmp_path)
    assert any("missing required agent role" in e for e in errors)


def test_illegal_transition_and_ready_gate(tmp_path):
    wf = Workflow(EventLog(tmp_path / "e.db"))
    w = wf.create("do a thing")
    with pytest.raises(GateError):
        wf.transition(w, "READY")  # INTAKE -> READY is illegal
    w = wf.transition(w, "TRIAGE")
    w = wf.transition(w, "SPEC")
    w = wf.record_spec(w, {"title": "t"}, actor="spec")
    with pytest.raises(GateError):
        wf.transition(w, "READY")  # no approval yet
    w = wf.approve_spec(w, approver="owner")
    assert w.state == "READY"


def test_approval_must_match_spec(tmp_path):
    wf = Workflow(EventLog(tmp_path / "e.db"))
    w = wf.create("g")
    w = wf.transition(w, "TRIAGE"); w = wf.transition(w, "SPEC")
    w = wf.record_spec(w, {"title": "one"}, actor="spec")
    # forge an approval for a different digest
    wf.log.append("ApprovalRecorded", {"subject_digest": "sha256:deadbeef", "approver": "owner"}, work_id=w.id)
    w = wf.fold(w.id)
    with pytest.raises(GateError):
        wf.transition(w, "READY")


def test_foreman_end_to_end(tmp_path):
    factory = make_factory(tmp_path)
    log = EventLog(tmp_path / "e.db")
    result = Foreman(factory, Workflow(log)).run("add a health endpoint")
    assert result.work.state == "DONE"
    assert result.verify_passed
    ok, _ = log.verify_chain()
    assert ok


def test_foreman_retries_then_blocks(tmp_path):
    factory = make_factory(tmp_path, max_attempts=2)
    tasks = [BenchTask("t", "never solves", solves_on_attempt=99)]
    log = EventLog(tmp_path / "e.db")
    result = Foreman(factory, Workflow(log), ScriptedRunner(tasks)).run("never solves")
    assert result.work.state == "BLOCKED"
    assert result.work.attempts == 2


def test_benchmark_factory_beats_or_equals_baseline():
    report = run_benchmark()
    assert report.factory_pass >= report.baseline_pass
    assert report.factory_pass == report.total


def _git(cwd, *a):
    import subprocess
    subprocess.run(["git", *a], cwd=str(cwd), check=True, capture_output=True, text=True)


def test_workspace_git_isolation(tmp_path):
    from psf.workspace import Workspace

    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("hi")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "init")

    ws = Workspace.create("W-test", repo=repo, use_git=True)
    assert ws.path.exists() and not ws.is_temp
    (ws.path / "b.txt").write_text("change")
    assert "b.txt" in ws.diff()
    ws.cleanup()
    assert not ws.path.exists()
