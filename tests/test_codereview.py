"""OCR delegate code-review loop: file selection, stop rule, cap, fail-closed."""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from psf import codereview as cr
from psf.cli import main
from psf.scaffold import render_template
from psf.schema import validate

FAKE_OCR = textwrap.dedent('''\
    #!{python}
    import json, os, sys
    args = sys.argv[1:]
    log = os.environ.get("FAKE_OCR_LOG")
    if log:
        open(log, "a").write(json.dumps(args) + "\\n")
    if os.environ.get("FAKE_OCR_FAIL"):
        print("boom", file=sys.stderr); sys.exit(3)
    assert args[0] == "delegate", args
    if args[1] == "preview":
        files = [p for p in os.environ.get("FAKE_OCR_FILES", "").split(",") if p]
        mode = "range" if "--from" in args else "workspace"
        print(json.dumps({{"schema_version": "1", "mode": mode, "reviewable_files":
            [{{"path": p, "status": "deleted" if p.startswith("gone") else "modified"}} for p in files]}}))
    elif args[1] == "rule":
        paths = [a for a in args[2:] if not a.startswith("--") and a not in ("json", "never")]
        print(json.dumps({{"schema_version": "1", "groups": [
            {{"group_id": 1, "source": "system", "pattern": "**/*.py", "rule": "be correct", "files": paths}}]}}))
''')


@pytest.fixture
def repo(tmp_path, monkeypatch):
    fake = tmp_path / "bin" / "ocr"
    fake.parent.mkdir()
    fake.write_text(FAKE_OCR.format(python=sys.executable))
    fake.chmod(0o755)
    monkeypatch.setenv("PSF_OCR", str(fake))
    monkeypatch.setenv("FAKE_OCR_LOG", str(tmp_path / "ocr.log"))
    root = tmp_path / "proj"
    root.mkdir()
    monkeypatch.chdir(root)
    return root


def _git(root: Path, *files: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    for f in files:
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        (root / f).write_text("x\n")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)


def _f(sev, verified=True, i="F"):
    return {"id": i, "severity": sev, "file": "a.py", "summary": "s", "verified": verified}


# --- selection --------------------------------------------------------------

def test_diff_mode_uses_ocr_preview_and_drops_deleted(repo, monkeypatch):
    monkeypatch.setenv("FAKE_OCR_FILES", "a.py,b.py,gone.py")
    state = cr.start(repo, base="main")
    assert state["mode"] == "range"
    assert state["files"] == ["a.py", "b.py"]
    assert state["rule_groups"][0]["files"] == ["a.py", "b.py"]
    calls = [json.loads(line) for line in (repo.parent / "ocr.log").read_text().splitlines()]
    assert calls[0][:4] == ["delegate", "preview", "--from", "main"]
    assert calls[1][:2] == ["delegate", "rule"]


def test_full_mode_lists_tracked_code_only(repo):
    _git(repo, "src/app.py", "web/x.ts", "Dockerfile", "README.md", "data.json", "docs/a.md")
    state = cr.start(repo, full=True)
    assert state["mode"] == "full"
    assert state["files"] == ["Dockerfile", "src/app.py", "web/x.ts"]


def test_rules_batched_and_merged(repo, monkeypatch):
    groups = cr.resolve_rules(repo, [f"f{i}.py" for i in range(5)], batch=2)
    assert len(groups) == 1 and groups[0]["files"] == [f"f{i}.py" for i in range(5)]


def test_nothing_to_review_is_done(repo, monkeypatch):
    monkeypatch.setenv("FAKE_OCR_FILES", "")
    state = cr.start(repo)
    assert state["result"] == cr.DONE
    with pytest.raises(cr.ReviewError):
        cr.record(repo, [])


# --- fail closed ------------------------------------------------------------

def test_missing_ocr_fails_closed(repo, monkeypatch):
    monkeypatch.setenv("PSF_OCR", str(repo / "nope"))
    monkeypatch.setenv("PATH", "/nonexistent")
    with pytest.raises(cr.ReviewError, match="ocr CLI not found"):
        cr.start(repo)
    assert not (repo / ".psf/review").exists()


def test_ocr_error_fails_closed(repo, monkeypatch):
    monkeypatch.setenv("FAKE_OCR_FAIL", "1")
    with pytest.raises(cr.ReviewError, match="rc=3"):
        cr.start(repo)


# --- the loop ---------------------------------------------------------------

def test_loop_converges_when_highs_fall_to_threshold(repo, monkeypatch):
    monkeypatch.setenv("FAKE_OCR_FILES", "a.py")
    cr.start(repo)
    r1 = cr.record(repo, [_f("high", i="H1"), _f("critical", i="H2"), _f("high", i="H3")])
    assert (r1["verified_highs"], r1["decision"]) == (3, cr.CONTINUE)
    r2 = cr.record(repo, {"findings": [_f("high"), _f("high"), _f("medium"), _f("low")]})
    assert (r2["verified_highs"], r2["decision"]) == (2, cr.DONE)
    assert cr.load(repo)["result"] == cr.DONE
    with pytest.raises(cr.ReviewError, match="already finished"):
        cr.record(repo, [])


def test_loop_stops_at_cap_without_converging(repo, monkeypatch):
    monkeypatch.setenv("FAKE_OCR_FILES", "a.py")
    cr.start(repo, settings=cr.Settings(max_highs=2, max_rounds=3))
    highs = [_f("high", i=f"H{i}") for i in range(3)]
    assert cr.record(repo, highs)["decision"] == cr.CONTINUE
    assert cr.record(repo, highs)["decision"] == cr.CONTINUE
    assert cr.record(repo, highs)["decision"] == cr.STOP
    assert cr.load(repo)["result"] == cr.STOP


def test_unverified_and_taste_findings_never_block(repo, monkeypatch):
    monkeypatch.setenv("FAKE_OCR_FILES", "a.py")
    cr.start(repo, settings=cr.Settings(max_highs=0, max_rounds=5))
    noise = [_f("high", verified=False)] * 4 + [_f(s) for s in ("medium", "low", "taste", "style", "info")]
    assert cr.record(repo, noise)["decision"] == cr.DONE


@pytest.mark.parametrize("bad", [
    [{"severity": "huge", "verified": True}],
    [{"severity": "high"}],
    [{"severity": "high", "verified": "yes"}],
    {"nope": []},
    ["x"],
])
def test_bad_findings_rejected(repo, monkeypatch, bad):
    monkeypatch.setenv("FAKE_OCR_FILES", "a.py")
    cr.start(repo)
    with pytest.raises(cr.ReviewError):
        cr.record(repo, bad)
    assert cr.load(repo)["rounds"] == []


def test_session_id_cannot_escape_review_dir(repo):
    with pytest.raises(cr.ReviewError, match="bad session"):
        cr.load(repo, "../../etc/passwd")


# --- CLI + config -----------------------------------------------------------

def test_cli_exit_codes_and_factory_settings(repo, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_OCR_FILES", "a.py")
    fac = repo / "factory"
    for rel, text in render_template("o/r", "off", "hitl").items():
        (fac / rel).parent.mkdir(parents=True, exist_ok=True)
        (fac / rel).write_text(text.replace("max_highs: 2", "max_highs: 1"))
    assert main(["review", "start"]) == 0
    assert cr.load(repo)["max_highs"] == 1
    fj = repo / "f.json"
    fj.write_text(json.dumps([_f("high"), _f("high")]))
    assert main(["review", "record", str(fj)]) == 10
    fj.write_text(json.dumps([_f("high")]))
    assert main(["review", "record", str(fj)]) == 0
    assert main(["review", "status"]) == 0
    assert "| 2 | 1 | 1 | DONE |" in capsys.readouterr().out
    assert main(["review", "record", str(fj)]) == 2


def test_cli_missing_ocr_returns_error(repo, monkeypatch):
    monkeypatch.setenv("PSF_OCR", str(repo / "nope"))
    monkeypatch.setenv("PATH", "/nonexistent")
    assert main(["review", "start"]) == 2


def test_template_ships_loop_and_validates(tmp_path):
    files = render_template("o/r", "off", "hitl")
    assert "agents/code-review.md" in files and "psf review start --full" in files["AGENTS.md"]
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text)
    import yaml
    raw = yaml.safe_load(files["factory.yml"])
    assert validate(raw, base_dir=tmp_path) == []
    raw["gates"]["code_review"] = {"max_highs": -1, "max_rounds": True, "x": 1}
    errs = validate(raw, base_dir=tmp_path)
    assert any("max_highs" in e for e in errs) and any("max_rounds" in e for e in errs)
    assert any("unknown keys" in e for e in errs)


def test_corrupt_session_is_a_review_error(repo, monkeypatch):
    monkeypatch.setenv("FAKE_OCR_FILES", "a.py")
    state = cr.start(repo)
    (repo / ".psf/review" / f"{state['session']}.json").write_text("{not json")
    with pytest.raises(cr.ReviewError, match="unreadable"):
        cr.load(repo)
    assert main(["review", "status"]) == 2
