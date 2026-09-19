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


def make_factory(tmp_path: Path, *, spec_approval=False, max_attempts=2, verify_quorum=1) -> Factory:
    (tmp_path / "agents").mkdir(exist_ok=True)
    for role in ("triage", "spec", "implement", "verify", "review"):
        (tmp_path / "agents" / f"{role}.md").write_text("prompt")
    return Factory(
        name="t", schema_version="psf/v1", path=tmp_path / "factory.yml",
        runner="mock", gates={"spec_approval": spec_approval, "verify_quorum": verify_quorum},
        limits={"max_attempts": max_attempts},
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


class CountingVerifyRunner(MockRunner):
    """Mock runner that counts verify calls and fails the chosen (1-based) ones."""

    def __init__(self, fail_on: set[int] = frozenset()):
        self.fail_on = set(fail_on)
        self.verify_calls = 0

    def run(self, task: AgentTask) -> AgentResult:
        if task.role != "verify":
            return super().run(task)
        self.verify_calls += 1
        if self.verify_calls in self.fail_on:
            return AgentResult(False, {"passed": False, "findings": [f"verify #{self.verify_calls} failed"]})
        return super().run(task)


def test_verify_quorum(tmp_path):
    (tmp_path / "agents").mkdir()
    for r in ("triage", "spec", "implement", "verify", "review"):
        (tmp_path / "agents" / f"{r}.md").write_text("p")
    base = {"schemaVersion": "psf/v1", "name": "x",
            "agents": {r: {"prompt": f"agents/{r}.md"} for r in
                       ("triage", "spec", "implement", "verify", "review")}}
    # schema: only the integers 1 and 2 are accepted
    for ok in (1, 2):
        assert validate({**base, "gates": {"verify_quorum": ok}}, base_dir=tmp_path) == []
    for bad in (0, 3, "2", 2.0, True):
        errs = validate({**base, "gates": {"verify_quorum": bad}}, base_dir=tmp_path)
        assert any("gates.verify_quorum" in e for e in errs), bad
    # model: default is 1
    assert make_factory(tmp_path).verify_quorum == 1
    assert Factory(name="t", schema_version="psf/v1", path=tmp_path / "f.yml").verify_quorum == 1

    # foreman: quorum 2 runs the verifier twice per build and needs both to pass
    factory = make_factory(tmp_path, verify_quorum=2, max_attempts=2)
    runner = CountingVerifyRunner()
    result = Foreman(factory, Workflow(EventLog(tmp_path / "ok.db")), runner).run("g")
    assert result.work.state == "DONE" and result.work.attempts == 1
    assert runner.verify_calls == 2

    # one failing verification out of two blocks REVIEW and triggers a retry
    runner = CountingVerifyRunner(fail_on={2})
    result = Foreman(factory, Workflow(EventLog(tmp_path / "retry.db")), runner).run("g")
    assert result.work.state == "DONE" and result.work.attempts == 2
    assert runner.verify_calls == 4
    assert "VERIFY->BUILD" in result.work.transitions

    # quorum 1 is unchanged: a single verification per build
    runner = CountingVerifyRunner()
    Foreman(make_factory(tmp_path, verify_quorum=1), Workflow(EventLog(tmp_path / "one.db")), runner).run("g")
    assert runner.verify_calls == 1


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


def test_schema_accepts_and_validates_feedback(tmp_path):
    from psf.schema import validate

    (tmp_path / "agents").mkdir()
    for r in ("triage", "spec", "implement", "verify", "review"):
        (tmp_path / "agents" / f"{r}.md").write_text("p")
    base = {"schemaVersion": "psf/v1", "name": "x",
            "agents": {r: {"prompt": f"agents/{r}.md"} for r in
                       ("triage", "spec", "implement", "verify", "review")}}
    assert validate({**base, "feedback": {"upstream": "o/r", "publish": False}}, base_dir=tmp_path) == []
    errs = validate({**base, "feedback": {"upstream": 5}}, base_dir=tmp_path)
    assert any("feedback.upstream" in e for e in errs)


def test_init_writes_agents_md(tmp_path, monkeypatch):
    from psf import cli

    monkeypatch.chdir(tmp_path)
    rc = cli.main(["init"])
    assert rc == 0
    assert (tmp_path / "factory" / "AGENTS.md").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert "psf feedback export" in (tmp_path / "AGENTS.md").read_text()


def test_mode_toggle(tmp_path, monkeypatch, capsys):
    import yaml

    from psf import cli

    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--feedback", "off", "--mode", "hitl"]) == 0

    def mode():
        return yaml.safe_load((tmp_path / "factory" / "factory.yml").read_text())["mode"]

    assert mode() == "hitl"
    assert cli.main(["mode", "yolo"]) == 0
    assert mode() == "yolo"
    assert cli.main(["mode"]) == 0
    assert "yolo" in capsys.readouterr().out
    # a run in yolo mode proceeds without human approval
    assert cli.main(["run", "--mode", "yolo", "--no-ask", "autonomous smoke"]) == 0


def test_feedback_consent_choose_and_opt_out(tmp_path, monkeypatch, capsys):
    import yaml

    from psf import cli

    monkeypatch.chdir(tmp_path)

    def mode_now():
        return yaml.safe_load((tmp_path / "factory" / "factory.yml").read_text())["feedback"]["mode"]

    assert cli.main(["init", "--feedback", "off"]) == 0
    assert mode_now() == "off"
    # exporting while opted out sends nothing
    cli.main(["--factory", "factory", "--ledger", ".psf/factory.db", "feedback", "export"])
    assert "feedback is OFF" in capsys.readouterr().out
    # opt in (auto), then back out anytime
    assert cli.main(["feedback", "opt-in", "--auto"]) == 0
    assert mode_now() == "auto"
    assert cli.main(["feedback", "status"]) == 0
    assert "mode=auto" in capsys.readouterr().out
    assert cli.main(["feedback", "opt-out"]) == 0
    assert mode_now() == "off"


def test_foreman_lease_prevents_concurrent_run(tmp_path):
    from psf.durability import Durability

    root = _factory_dir(tmp_path)
    log = EventLog(tmp_path / "e.db")
    d = Durability(tmp_path / "dur.db")
    d.claim("W-x", "other-worker", ttl=60)  # someone else holds it
    with pytest.raises(GateError):
        Foreman(load_factory(root), Workflow(log), durability=d).run("goal", work_id="W-x")


def test_foreman_releases_lease_after_run(tmp_path):
    from psf.durability import Durability

    root = _factory_dir(tmp_path)
    log = EventLog(tmp_path / "e.db")
    d = Durability(tmp_path / "dur.db")
    result = Foreman(load_factory(root), Workflow(log), durability=d).run("goal")
    assert d.lease(result.work.id) is None


def test_improve_refuses_protected_field(tmp_path):
    from psf.improve import run_improvement

    root = _factory_dir(tmp_path)
    ledger = tmp_path / "e.db"
    EventLog(ledger).close()
    with pytest.raises(ValueError):
        run_improvement(root, ledger, promote=True, field="gates.spec_approval", candidate=False)


def test_improve_multi_candidate_picks_smallest_sufficient(tmp_path):
    from psf.improve import run_improvement

    root = _factory_dir(tmp_path)  # max_attempts: 2
    ledger = tmp_path / "e.db"
    EventLog(ledger).close()
    r = run_improvement(root, ledger, promote=True)
    assert r.promoted
    assert r.proposal.candidate == 3  # smallest candidate that clears the eval
    assert "max_attempts: 3" in (root / "factory.yml").read_text()


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


def test_review_revise_loops_back_to_build(tmp_path):
    from psf.agents import AgentResult

    class ReviseOnce(MockRunner):
        def __init__(self):
            self.reviews = 0

        def run(self, task):
            if task.role == "review":
                self.reviews += 1
                return AgentResult(True, {"decision": "revise" if self.reviews == 1 else "approve"})
            return super().run(task)

    f = make_factory(tmp_path, max_attempts=3)
    res = Foreman(f, Workflow(EventLog(tmp_path / "r1.db")), ReviseOnce()).run("g")
    assert res.work.state == "DONE"


def test_always_revise_terminates_blocked(tmp_path):
    from psf.agents import AgentResult

    class AlwaysRevise(MockRunner):
        def run(self, task):
            if task.role == "review":
                return AgentResult(True, {"decision": "revise", "notes": "still wrong: x", "blocking": True})
            return super().run(task)

    f = make_factory(tmp_path, max_attempts=2)
    res = Foreman(f, Workflow(EventLog(tmp_path / "r2.db")), AlwaysRevise()).run("g", finish=False)
    assert res.work.state == "BLOCKED"


def test_empty_revise_is_not_a_blocker(tmp_path):
    from psf.agents import AgentResult

    class EmptyRevise(MockRunner):
        def run(self, task):
            if task.role == "review":
                return AgentResult(True, {"decision": "revise", "notes": ""})
            return super().run(task)

    f = make_factory(tmp_path, max_attempts=2)
    res = Foreman(f, Workflow(EventLog(tmp_path / "r3.db")), EmptyRevise()).run("g")
    assert res.work.state == "DONE"


def test_init_scaffolds_eval(tmp_path, monkeypatch):
    from psf import cli

    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--feedback", "off", "--mode", "hitl"]) == 0
    assert (tmp_path / "eval" / "tasks.json").exists()
    assert (tmp_path / "eval" / "holdout.json").exists()


def test_fresh_repo_evals_do_not_crash(tmp_path, monkeypatch):
    from psf import cli

    monkeypatch.chdir(tmp_path)
    cli.main(["init", "--feedback", "off", "--mode", "hitl"])
    rc = cli.main(["eval-self"])
    assert rc == 0  # all self-evals pass on a brand-new repo


def test_harness_pin(tmp_path, monkeypatch, capsys):
    import yaml
    from psf import cli

    monkeypatch.chdir(tmp_path)
    cli.main(["init", "--feedback", "off", "--mode", "hitl"])
    assert cli.main(["harness", "opencode", "--model", "deepseek/deepseek-v4-pro", "--permissions", "safe"]) == 0
    raw = yaml.safe_load((tmp_path / "factory" / "factory.yml").read_text())
    assert raw["runner"] == "subprocess"
    cmd = raw["runnerOptions"]["command"]
    assert "psf.adapters.opencode" in " ".join(cmd) and "deepseek/deepseek-v4-pro" in cmd
    assert raw["runnerOptions"]["permissions"] == "safe"
    assert cli.main(["harness"]) == 0
    assert "opencode" in capsys.readouterr().out


def test_cancel_and_unblock_commands(tmp_path, monkeypatch, capsys):
    from psf import cli

    monkeypatch.chdir(tmp_path)
    cli.main(["init", "--feedback", "off", "--mode", "hitl"])
    # create a work item sitting in SPEC_REVIEW (no-approve), then cancel it
    cli.main(["run", "--no-approve", "--no-ask", "hold"])
    wid = cli.main.__self__ if False else None
    import psf.cli as c
    _, log, wf = c._load(type("A", (), {"factory": "factory", "ledger": ".psf/factory.db"})())
    ids = log.work_ids()
    assert ids
    rc = cli.main(["cancel", ids[0], "--reason", "no longer needed"])
    assert rc == 0
    assert wf.fold(ids[0]).state == "CANCELLED"
    # unblock path: create + block + unblock
    w = wf.create("blocked one")
    w = wf.transition(w, "TRIAGE")
    w = wf.transition(w, "SPEC")
    w = wf.transition(w, "BLOCKED", reason="wait")
    rc = cli.main(["unblock", w.id])
    assert rc == 0 and wf.fold(w.id).state == "SPEC"


def test_guardrail_eval_suite():
    from psf.guardeval import run_guardrail_eval
    rep = run_guardrail_eval()
    assert rep["total"] == 6 and rep["failed"] == 0, rep["issues"]
