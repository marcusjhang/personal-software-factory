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
