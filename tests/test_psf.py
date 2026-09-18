import sqlite3
from pathlib import Path

import pytest

from psf.agents import AgentResult, AgentTask, MockRunner
from psf.bench import BenchTask, ScriptedRunner, run_benchmark
from psf.canonical import digest
from psf.events import EventLog
from psf.foreman import Foreman
from psf.schema import Factory, load as load_factory, validate
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


def _factory_dir(tmp_path):
    root = tmp_path / "factory"
    (root / "agents").mkdir(parents=True)
    (root / "factory.yml").write_text(
        "schemaVersion: psf/v1\nname: t\nrunner: mock\n"
        "agents:\n" + "".join(f"  {r}: {{ prompt: agents/{r}.md }}\n"
                              for r in ("triage", "spec", "implement", "verify", "review")) +
        "gates:\n  spec_approval: true\nlimits:\n  max_attempts: 2\n"
    )
    for r in ("triage", "spec", "implement", "verify", "review"):
        (root / "agents" / f"{r}.md").write_text("p")
    return root


def test_audit_healthy(tmp_path):
    from psf.audit import run_audit

    root = _factory_dir(tmp_path)
    log = EventLog(tmp_path / "e.db")
    Foreman(load_factory(root), Workflow(log)).run("do a thing")
    log.close()
    report = run_audit(root, tmp_path / "e.db")
    assert report.healthy, [c for c in report.checks if c.status == "fail"]


def test_audit_detects_tamper(tmp_path):
    from psf.audit import run_audit

    root = _factory_dir(tmp_path)
    log = EventLog(tmp_path / "e.db")
    log.append("WorkCreated", {"goal": "g", "max_attempts": 2}, work_id="W1")
    log.conn.execute("UPDATE events SET payload='{\"goal\":\"hacked\"}' WHERE seq=1")
    log.conn.commit()
    log.close()
    report = run_audit(root, tmp_path / "e.db", include_bench=False)
    assert not report.healthy


def test_improve_promotes_and_rolls_back(tmp_path):
    from psf.improve import run_improvement

    root = _factory_dir(tmp_path)
    ledger = tmp_path / "e.db"
    EventLog(ledger).close()
    result = run_improvement(root, ledger, promote=True)
    assert result.promoted
    yml = (root / "factory.yml").read_text()
    assert "max_attempts: 3" in yml
    back = run_improvement(root, ledger, rollback=True)
    assert back.rolled_back
    assert "max_attempts: 2" in (root / "factory.yml").read_text()


def test_doctor_alias_matches_audit(tmp_path):
    from psf.cli import main

    root = _factory_dir(tmp_path)
    ledger = str(tmp_path / "e.db")
    rc_audit = main(["--factory", str(root), "--ledger", ledger, "audit", "--fast"])
    rc_doctor = main(["--factory", str(root), "--ledger", ledger, "doctor", "--fast"])
    assert rc_audit == 0 and rc_doctor == rc_audit


def test_metrics_json(tmp_path, capsys):
    import json

    from psf.cli import main

    root = _factory_dir(tmp_path)
    ledger = tmp_path / "e.db"
    log = EventLog(ledger)
    work = Foreman(load_factory(root), Workflow(log)).run("do a thing").work
    log.append("OutcomeRecorded", {"accepted": True, "review_escape": False,
                                   "cost_usd": 1.5, "human_minutes": 3},
               work_id=work.id, actor="owner")
    log.close()

    rc = main(["--factory", str(root), "--ledger", str(ledger), "metrics", "--json"])
    assert rc == 0
    m = json.loads(capsys.readouterr().out)
    assert m["work_items"] == 1
    assert m["states"] == {"DONE": 1}
    assert m["attempts"] == 1 and m["retries"] == 0 and m["blocked"] == 0
    assert m["outcomes"] == {"accepted": 1, "review_escape": 0, "cost_usd": 1.5, "human_minutes": 3.0}
    assert m["chain"]["ok"] is True
    assert m["events"] > 0


def test_status_json(tmp_path, capsys):
    import json

    from psf.cli import main

    root = _factory_dir(tmp_path)
    ledger = tmp_path / "e.db"
    base = ["--factory", str(root), "--ledger", str(ledger)]

    # empty ledger still emits valid JSON
    assert main(base + ["status", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []

    log = EventLog(ledger)
    work = Foreman(load_factory(root), Workflow(log)).run("do a thing").work
    log.close()

    rc = main(base + ["status", "--json"])
    assert rc == 0
    items = json.loads(capsys.readouterr().out)
    assert len(items) == 1
    item = items[0]
    assert item["id"] == work.id
    assert item["goal"] == "do a thing"
    assert item["state"] == "DONE"
    assert item["attempts"] == 1 and item["max_attempts"] == 2
    assert item["spec_digest"] == work.spec_digest

    # filtering by work id returns just that item
    assert main(base + ["status", work.id, "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == items
