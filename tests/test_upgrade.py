from pathlib import Path

from psf.migrations import run_migrations
from psf.scaffold import Lock, digest, read_lock, render_template, write_lock
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


# --- bootstrap base (consumer feedback 2026-11-16: missed template files) ----

def _legacy_repo(tmp_path: Path) -> tuple[Path, Path]:
    """A repo scaffolded by psf 0.1.0 before locks existed."""
    from psf.template_history import render_0_1_0
    factory = tmp_path / "factory"
    for rel, text in render_0_1_0("marcusjhang/personal-software-factory", "off", "hitl").items():
        (factory / rel).parent.mkdir(parents=True, exist_ok=True)
        (factory / rel).write_text(text)
    (tmp_path / ".psf").mkdir()
    return tmp_path, factory


def test_prelock_upgrade_adds_files_and_lines_added_since_0_1_0(tmp_path: Path):
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    rep = run_upgrade(root, factory)
    assert rep.applied and not rep.conflict
    assert (factory / "agents/code-review.md").exists()
    assert "code_review" in (factory / "factory.yml").read_text()
    assert "psf review start" in (factory / "AGENTS.md").read_text()
    assert run_upgrade(root, factory, check=True).drifted is False


def test_prelock_upgrade_keeps_local_edits(tmp_path: Path):
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    (factory / "agents/implement.md").write_text("my own implement prompt\n")
    run_upgrade(root, factory)
    assert (factory / "agents/implement.md").read_text() == "my own implement prompt\n"
    assert (factory / "agents/code-review.md").exists()


def test_old_bootstrap_lock_is_repaired_on_next_upgrade(tmp_path: Path):
    """Simulate a lock written by the old bootstrap (current template as base)."""
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    current = render_template("marcusjhang/personal-software-factory", "off", "hitl")
    write_lock(root, Lock(revision="current", template_digest=digest(current), base=current,
                          migrations=["2026-09-bootstrap-lock"]).stamp())
    chk = run_upgrade(root, factory, check=True)            # the bug: used to say "up to date"
    assert chk.drifted and not (factory / "agents/code-review.md").exists()
    rep = run_upgrade(root, factory)
    assert rep.applied and not rep.conflict
    assert (factory / "agents/code-review.md").exists()
    assert "code_review" in (factory / "factory.yml").read_text()
    assert "2026-11-rebase-bootstrap-base" in rep.migrations
    assert run_upgrade(root, factory, check=True).drifted is False


def test_rebase_does_not_touch_normal_locks(tmp_path: Path):
    from psf.migrations import rebase_pending
    root, factory = _legacy_repo(tmp_path)
    current = render_template("marcusjhang/personal-software-factory", "off", "hitl")
    write_lock(root, Lock(revision="v0.2.1", template_digest=digest(current), base=current,
                          migrations=["2026-09-bootstrap-lock", "2026-11-rebase-bootstrap-base"]).stamp())
    assert not rebase_pending(root, factory, ["2026-09-bootstrap-lock", "2026-11-rebase-bootstrap-base"])
    write_lock(root, Lock(revision="psf 0.1.0", template_digest="x", base={"factory.yml": "a"}, migrations=[]).stamp())
    assert not rebase_pending(root, factory, [])


# --- conflicts: insert-only merges, rollback instead of crash, --resolved ------

def test_side_by_side_insertions_are_a_conflict_not_a_guess():
    """Both sides inserting at the same spot is left to a human (no silent resolution)."""
    from psf.upgrade import _merge
    base = "gates:\n  verify_quorum: 2\nlimits:\n  max_attempts: 2\n"
    ours = "gates:\n  verify_quorum: 2\n  code_review: false\nlimits:\n  max_attempts: 2\n"
    theirs = "gates:\n  verify_quorum: 2\n  code_review: true\nlimits:\n  max_attempts: 2\n"
    _, conflict = _merge(ours, base, theirs, "factory.yml")
    assert conflict


def test_merge_real_conflict_still_conflicts():
    from psf.upgrade import _merge
    base = "limits:\n  max_attempts: 2\n"
    text, conflict = _merge("limits:\n  max_attempts: 5\n", base, "limits:\n  max_attempts: 3\n", "factory.yml")
    assert conflict and "<<<<<<<" in text


def test_conflicted_yaml_rolls_back_instead_of_crashing(tmp_path: Path):
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    run_upgrade(root, factory)                                   # pin a lock
    before = (factory / "factory.yml").read_text()
    edited = before.replace("max_attempts: 2", "max_attempts: 7")
    (factory / "factory.yml").write_text(edited)
    lock = read_lock(root)
    base = dict(lock.base)
    base["factory.yml"] = base["factory.yml"].replace("max_attempts: 2", "max_attempts: 1")
    theirs_src = tmp_path / "tpl"
    for rel, text in render_template("marcusjhang/personal-software-factory", "off", "hitl").items():
        (theirs_src / rel).parent.mkdir(parents=True, exist_ok=True)
        (theirs_src / rel).write_text(text.replace("max_attempts: 2", "max_attempts: 3"))
    write_lock(root, Lock(revision="x", template_digest=digest(base), base=base,
                          migrations=list(lock.migrations)).stamp())
    rep = run_upgrade(root, factory, source=theirs_src)          # must not raise
    assert not rep.applied
    assert any("rolled back" in n for n in rep.notes)
    assert (factory / "factory.yml").read_text() == edited       # restored, no markers
    assert any("psf upgrade --resolved" in n for n in rep.notes)    # tells the user how


def test_resolved_advances_base_only_when_clean(tmp_path: Path):
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    run_upgrade(root, factory)
    (factory / "factory.yml").write_text((factory / "factory.yml").read_text()
                                         + "<<<<<<< factory.yml (yours)\nx\n=======\ny\n>>>>>>> factory.yml (upstream)\n")
    rep = run_upgrade(root, factory, resolved=True)
    assert not rep.applied and any("conflict markers" in n for n in rep.notes)
    good = render_template("marcusjhang/personal-software-factory", "off", "hitl")["factory.yml"]
    (factory / "factory.yml").write_text(good.replace("max_attempts: 2", "max_attempts: 4"))
    rep = run_upgrade(root, factory, resolved=True)
    assert rep.applied
    assert run_upgrade(root, factory, check=True).drifted is False   # no phantom CONFLICT
    assert "max_attempts: 4" in (factory / "factory.yml").read_text()


def test_resolved_refuses_without_a_pinned_base(tmp_path: Path):
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    rep = run_upgrade(root, factory, resolved=True)
    assert not rep.applied and any("run `psf upgrade` first" in n for n in rep.notes)
    assert not (root / "psf.lock.json").exists()
    rep = run_upgrade(root, factory)                       # normal path still delivers
    assert (factory / "agents/code-review.md").exists()


def test_resolved_leaves_missing_template_files_addable(tmp_path: Path):
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    run_upgrade(root, factory)
    (factory / "agents/code-review.md").unlink()           # e.g. a rolled-back merge never wrote it
    rep = run_upgrade(root, factory, resolved=True)
    assert rep.applied and any("agents/code-review.md" in n for n in rep.notes)
    run_upgrade(root, factory)
    assert (factory / "agents/code-review.md").exists()
