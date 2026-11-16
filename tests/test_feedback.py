import json

from psf.events import EventLog
from psf.feedback import build_envelope, export, ingest, report
from psf.state import Workflow


def _factory(tmp_path):
    root = tmp_path / "factory"
    (root / "agents").mkdir(parents=True)
    (root / "factory.yml").write_text(
        "schemaVersion: psf/v1\nname: t\nagents:\n"
        + "".join(f"  {r}: {{prompt: agents/{r}.md}}\n"
                  for r in ("triage", "spec", "implement", "verify", "review"))
        + "limits:\n  max_attempts: 2\n"
    )
    for r in ("triage", "spec", "implement", "verify", "review"):
        (root / "agents" / f"{r}.md").write_text("p")
    return root


def test_envelope_excludes_goal_text(tmp_path):
    root = _factory(tmp_path)
    log = EventLog(tmp_path / "e.db")
    Workflow(log).create("SECRETPROJECT internal goal wording")
    log.close()
    env = build_envelope(root, tmp_path / "e.db")
    assert "SECRETPROJECT" not in json.dumps(env)
    assert env["metrics"]["work_items"] == 1
    assert env["schema"] == "psf.feedback/v1"


def test_export_ingest_report_roundtrip(tmp_path):
    root = _factory(tmp_path)
    EventLog(tmp_path / "e.db").close()
    p = export(root, tmp_path / "e.db", out=tmp_path / "env.json")
    assert p.exists()
    n = ingest(tmp_path / "inbox", p)
    assert n == 1
    r = report(tmp_path / "inbox")
    assert r["envelopes"] == 1
    assert "totals" in r and "suggestions" in r


def test_export_reports_failure_nonzero(tmp_path, monkeypatch):
    from psf import cli, feedback
    from psf.events import EventLog

    root = tmp_path / "factory"
    (root / "agents").mkdir(parents=True)
    (root / "factory.yml").write_text(
        "schemaVersion: psf/v1\nname: t\nrunner: mock\nagents:\n"
        + "".join(f"  {r}: {{ prompt: agents/{r}.md }}\n"
                  for r in ("triage", "spec", "implement", "verify", "review"))
        + "gates: {}\nlimits:\n  max_attempts: 2\n")
    for r in ("triage", "spec", "implement", "verify", "review"):
        (root / "agents" / f"{r}.md").write_text("p")
    ledger = tmp_path / "e.db"
    EventLog(ledger).close()

    monkeypatch.setattr(feedback, "publish_issue", lambda repo, env: (None, "label missing"))
    rc = cli.main(["--factory", str(root), "--ledger", str(ledger),
                   "feedback", "export", "--github", "owner/repo"])
    assert rc == 1  # filing failed -> non-zero, never silent success

    monkeypatch.setattr(feedback, "publish_issue", lambda repo, env: ("https://github.com/o/r/issues/2", None))
    rc = cli.main(["--factory", str(root), "--ledger", str(ledger),
                   "feedback", "export", "--github", "owner/repo"])
    assert rc == 0


def test_ingest_issues_neutralizes_path_traversal(tmp_path, monkeypatch):
    """A malicious envelope_id in an issue body must not escape the inbox."""
    from psf import feedback, github

    wf = tmp_path / "factory"
    (wf / "agents").mkdir(parents=True)
    (wf / "factory.yml").write_text("schemaVersion: psf/v1\nname: t\n")
    env = {"schema": "psf.feedback/v1", "envelope_id": "../../PWNED",
           "metrics": {"work_items": 1}, "failures": {"verify_failures": 0}}
    body = "```json\n" + json.dumps(env) + "\n```"
    monkeypatch.setattr(github, "list_issues",
                        lambda *a, **k: [{"number": 1, "body": body}])
    inbox = tmp_path / "inbox"
    n = feedback.ingest_issues(inbox, repo="acme/app")
    assert n == 1
    assert not (tmp_path / "PWNED").exists()
    assert not (tmp_path.parent / "PWNED").exists()
    files = list(inbox.glob("*.json"))
    assert len(files) == 1 and ".." not in files[0].name


# --- 0.2.1: weekly local export + report dedupe ------------------------------

def _cli_factory(tmp_path, fb_mode):
    root = _factory(tmp_path)
    (root / "factory.yml").write_text((root / "factory.yml").read_text()
                                      + f"feedback:\n  upstream: owner/repo\n  mode: \"{fb_mode}\"\n")
    return root


def _args(root, ledger, *rest):
    return ["--factory", str(root), "--ledger", str(ledger), "feedback", "export", *rest]


def test_local_export_works_when_feedback_off(tmp_path, monkeypatch):
    from psf import cli
    monkeypatch.chdir(tmp_path)
    root = _cli_factory(tmp_path, "off")
    log = EventLog(tmp_path / "e.db"); Workflow(log).create("g"); log.close()
    assert cli.main(_args(root, tmp_path / "e.db")) == 0
    assert not list((tmp_path / ".psf/feedback").glob("FB-*.json"))      # off: nothing
    assert cli.main(_args(root, tmp_path / "e.db", "--local")) == 0
    assert len(list((tmp_path / ".psf/feedback").glob("FB-*.json"))) == 1


def test_local_never_publishes_even_in_auto_mode(tmp_path, monkeypatch):
    from psf import cli, feedback
    monkeypatch.chdir(tmp_path)
    root = _cli_factory(tmp_path, "auto")
    EventLog(tmp_path / "e.db").close()
    called = []
    monkeypatch.setattr(feedback, "publish_issue", lambda repo, env: called.append(repo) or ("u", None))
    assert cli.main(_args(root, tmp_path / "e.db", "--local")) == 0
    assert called == []
    env = json.loads(next((tmp_path / ".psf/feedback").glob("FB-*.json")).read_text())
    assert env["repo"] is None
    assert cli.main(_args(root, tmp_path / "e.db", "--local", "--github", "o/r")) == 2


def test_if_changed_skips_empty_and_unchanged(tmp_path, monkeypatch):
    from psf import cli
    monkeypatch.chdir(tmp_path)
    root = _cli_factory(tmp_path, "hint")
    ledger = tmp_path / "e.db"
    EventLog(ledger).close()
    fb = tmp_path / ".psf/feedback"
    run = lambda: cli.main(_args(root, ledger, "--local", "--if-changed"))
    assert run() == 0 and not list(fb.glob("FB-*.json"))                # no work, no export
    log = EventLog(ledger); Workflow(log).create("g"); log.close()
    assert run() == 0 and len(list(fb.glob("FB-*.json"))) == 1          # new work
    assert run() == 0 and len(list(fb.glob("FB-*.json"))) == 1          # unchanged: skipped
    log = EventLog(ledger); Workflow(log).create("g2"); log.close()
    assert run() == 0 and len(list(fb.glob("FB-*.json"))) == 2          # more work


def test_report_keeps_newest_envelope_per_source(tmp_path):
    from psf.feedback import report
    inbox = tmp_path / "inbox"; inbox.mkdir()
    def env(eid, src, at, items):
        e = {"schema": "psf.feedback/v1", "envelope_id": eid, "generated_at": at,
             "metrics": {"work_items": items}, "failures": {}}
        if src:
            e["source"] = src
        (inbox / f"{eid}.json").write_text(json.dumps(e))
    env("FB-a1", "src-a", "2026-11-01T00:00:00Z", 5)
    env("FB-a2", "src-a", "2026-11-08T00:00:00Z", 7)   # cumulative: supersedes a1
    env("FB-b1", "src-b", "2026-11-08T00:00:00Z", 3)
    env("FB-old", None, "2026-10-01T00:00:00Z", 2)     # legacy, ungroupable: kept
    r = report(inbox)
    assert r["envelopes"] == 3 and r["superseded"] == 1
    assert r["totals"]["work_items"] == 7 + 3 + 2


def test_source_id_is_random_stable_and_per_ledger(tmp_path, monkeypatch):
    from psf.feedback import source_id
    a = source_id(tmp_path / ".psf/factory.db")
    monkeypatch.chdir(tmp_path)                      # cwd no longer matters
    assert source_id(tmp_path / ".psf/factory.db") == a
    assert a.startswith("src-") and str(tmp_path) not in a
    assert (tmp_path / ".psf/source-id").read_text().strip() == a
    assert source_id(tmp_path / "other/.psf/factory.db") != a


def test_report_tolerates_malformed_source(tmp_path):
    from psf.feedback import report
    inbox = tmp_path / "inbox"; inbox.mkdir()
    (inbox / "FB-x.json").write_text(json.dumps({"schema": "psf.feedback/v1", "source": ["x"],
                                                  "metrics": {"work_items": 1}}))
    (inbox / "FB-y.json").write_text(json.dumps({"schema": "psf.feedback/v1", "source": {"a": 1},
                                                  "metrics": {"work_items": 2}}))
    r = report(inbox)
    assert r["envelopes"] == 2 and r["totals"]["work_items"] == 3


def test_if_changed_requires_local_default_output(tmp_path, monkeypatch):
    from psf import cli
    monkeypatch.chdir(tmp_path)
    root = _cli_factory(tmp_path, "hint")
    EventLog(tmp_path / "e.db").close()
    assert cli.main(_args(root, tmp_path / "e.db", "--if-changed")) == 2
    assert cli.main(_args(root, tmp_path / "e.db", "--local", "--if-changed", "--out", "x.json")) == 2
