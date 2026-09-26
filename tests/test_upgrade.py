from pathlib import Path

from psf.migrations import run_migrations
from psf.scaffold import Lock, digest, render_template, write_lock
from psf.upgrade import plan


def _ours_base_theirs(o, b, t, rel="f"):
    return {rel: x for x in (o,) if x is not None}, \
           {rel: x for x in (b,) if x is not None}, \
           {rel: x for x in (t,) if x is not None}


def test_plan_keeps_when_unchanged():
    o, b, t = _ours_base_theirs("same\n", "same\n", "same\n")
    (change, text), = plan(o, b, t)
    assert change.action == "kept" and text is None


def test_plan_applies_upstream_when_local_untouched():
    o, b, t = _ours_base_theirs("old\n", "old\n", "new\n")
    (change, text), = plan(o, b, t)
    assert change.action == "updated" and text == "new\n"


def test_plan_keeps_local_when_upstream_untouched():
    o, b, t = _ours_base_theirs("local\n", "old\n", "old\n")
    (change, text), = plan(o, b, t)
    assert change.action == "kept" and text is None


def test_plan_conflicts_on_both_edited():
    o, b, t = _ours_base_theirs("mine\n", "base\n", "theirs\n")
    (change, text), = plan(o, b, t)
    assert change.action == "merged" and change.conflict and "<<<<<<<" in text


def test_plan_adds_and_deletes():
    ours, base, theirs = {"a": "x\n"}, {"a": "x\n"}, {"a": "x\n", "b": "y\n"}
    changes = {c.path: c.action for c, _ in plan(ours, base, theirs)}
    assert changes["b"] == "added"
    ours2, base2, theirs2 = {}, {"gone": "x\n"}, {}
    (c, _), = plan(ours2, base2, theirs2)
    assert c.action == "kept"          # locally deleted -> respected


def test_digest_is_order_independent():
    assert digest({"a": "1", "b": "2"}) == digest({"b": "2", "a": "1"})


def test_bootstrap_migration_creates_lock(tmp_path: Path):
    factory = tmp_path / "factory"
    factory.mkdir()
    (factory / "factory.yml").write_text("mode: yolo\nfeedback: {mode: off}\n")
    (factory / "agents").mkdir()
    (tmp_path / ".psf").mkdir()
    applied, notes = run_migrations(tmp_path, factory, [])
    assert "2026-09-bootstrap-lock" in applied
    assert (tmp_path / "psf.lock.json").exists()
    # idempotent: running again applies nothing
    applied2, _ = run_migrations(tmp_path, factory, applied)
    assert applied2 == applied


def test_lock_roundtrip(tmp_path: Path):
    files = render_template("x/y", "off", "hitl")
    write_lock(tmp_path, Lock(revision="r1", template_digest=digest(files), base=files).stamp())
    from psf.scaffold import read_lock

    lock = read_lock(tmp_path)
    assert lock and lock.revision == "r1" and lock.applied_at
