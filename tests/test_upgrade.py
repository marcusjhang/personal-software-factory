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


def test_resolved_refuses_without_a_pinned_base(tmp_path: Path):
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    rep = run_upgrade(root, factory, resolved=True)
    assert not rep.applied and any("run `psf upgrade` first" in n for n in rep.notes)
    assert not (root / "psf.lock.json").exists()
    rep = run_upgrade(root, factory)                       # normal path still delivers
    assert (factory / "agents/code-review.md").exists()


UP = "marcusjhang/personal-software-factory"


def _target(tmp_path: Path, edit=lambda rel, t: t, drop=()) -> Path:
    """A complete template dir derived from the current template."""
    src = tmp_path / "tpl"
    for rel, text in render_template(UP, "off", "hitl").items():
        if rel in drop:
            continue
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text(edit(rel, text))
    return src


def _conflicted_repo(tmp_path: Path, extra=lambda rel, t: t) -> tuple[Path, Path, Path]:
    """Repo at the current template, local max_attempts 7, target max_attempts 3 (+ extra edits)."""
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    assert run_upgrade(root, factory).applied
    yml = factory / "factory.yml"
    yml.write_text(yml.read_text().replace("max_attempts: 2", "max_attempts: 7"))
    src = _target(tmp_path, lambda rel, t: extra(rel, t.replace("max_attempts: 2", "max_attempts: 3")))
    return root, factory, src


def test_resolved_advances_only_conflicted_files(tmp_path: Path):
    from psf.upgrade import run_upgrade
    root, factory, src = _conflicted_repo(tmp_path)
    rep = run_upgrade(root, factory, source=src)
    assert not rep.applied and rep.conflict                  # rolled back
    yml = factory / "factory.yml"
    yml.write_text(yml.read_text() + "<<<<<<< factory.yml (yours)\nx\n=======\ny\n>>>>>>> factory.yml (upstream)\n")
    rep = run_upgrade(root, factory, source=src, resolved=True)
    assert not rep.applied and any("conflict markers" in n for n in rep.notes)
    yml.write_text(yml.read_text().split("<<<<<<<")[0])   # human keeps max_attempts 7
    rep = run_upgrade(root, factory, source=src, resolved=True)
    assert rep.applied and [c.path for c in rep.changes] == ["factory.yml"]
    assert run_upgrade(root, factory, source=src, check=True).drifted is False   # no phantom CONFLICT
    assert "max_attempts: 7" in yml.read_text()


def test_resolved_honours_check_and_pretend(tmp_path: Path):
    """R-378237e8 F3: --resolved with --check/--pretend writes nothing."""
    from psf.scaffold import lock_path
    from psf.upgrade import run_upgrade
    root, factory, src = _conflicted_repo(tmp_path)
    before = lock_path(root).read_text()
    for kw in ({"check": True}, {"pretend": True}):
        rep = run_upgrade(root, factory, source=src, resolved=True, **kw)
        assert not rep.applied and any("would mark resolved" in n for n in rep.notes)
        assert lock_path(root).read_text() == before


def test_resolved_keeps_deliberate_deletions(tmp_path: Path):
    """R-378237e8 F4: a file the user deleted is not re-added after --resolved."""
    from psf.upgrade import run_upgrade
    root, factory, src = _conflicted_repo(tmp_path)
    (factory / "agents/code-review.md").unlink()           # deliberate local deletion
    assert run_upgrade(root, factory, source=src, resolved=True).applied
    rep = run_upgrade(root, factory, source=src)
    assert rep.applied and not (factory / "agents/code-review.md").exists()


def test_resolved_requires_a_pending_conflict(tmp_path: Path):
    """R-378237e8 F5: --resolved with nothing in conflict refuses and suppresses nothing."""
    from psf.scaffold import lock_path
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    run_upgrade(root, factory)
    src = _target(tmp_path, lambda rel, t: t + "upstream line\n" if rel == "agents/spec.md" else t)
    before = lock_path(root).read_text()
    rep = run_upgrade(root, factory, source=src, resolved=True)
    assert not rep.applied and any("no upgrade conflict is pending" in n for n in rep.notes)
    assert lock_path(root).read_text() == before
    assert run_upgrade(root, factory, source=src).applied
    assert "upstream line" in (factory / "agents/spec.md").read_text()


def test_resolved_does_not_suppress_other_upstream_changes(tmp_path: Path):
    """R-378237e8 F5: only the conflicted file's base moves; other upstream edits still arrive."""
    from psf.upgrade import run_upgrade
    root, factory, src = _conflicted_repo(
        tmp_path, lambda rel, t: t + "upstream line\n" if rel == "agents/spec.md" else t)
    rep = run_upgrade(root, factory, source=src, resolved=True)
    assert rep.applied and rep.drifted and any("agents/spec.md" in n for n in rep.notes)
    rep = run_upgrade(root, factory, source=src)
    assert rep.applied and not rep.conflict
    assert "upstream line" in (factory / "agents/spec.md").read_text()
    assert "max_attempts: 7" in (factory / "factory.yml").read_text()


def test_rollback_restores_a_rebased_lock(tmp_path: Path):
    """R-378237e8 F2: the rebase writes the lock before merging; a rollback must undo it."""
    from psf.scaffold import lock_path
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    current = render_template(UP, "off", "hitl")
    write_lock(root, Lock(revision="current", template_digest=digest(current), base=current,
                          migrations=["2026-09-bootstrap-lock"]).stamp())
    yml = factory / "factory.yml"
    yml.write_text(yml.read_text().replace("max_attempts: 2", "max_attempts: 7"))
    before = lock_path(root).read_text()
    src = _target(tmp_path, lambda rel, t: t.replace("max_attempts: 2", "max_attempts: 3"))
    rep = run_upgrade(root, factory, source=src)
    assert not rep.applied and any("rolled back" in n for n in rep.notes)
    assert lock_path(root).read_text() == before
    assert not (factory / "agents/code-review.md").exists()


def test_rollback_removes_a_bootstrap_lock(tmp_path: Path):
    """R-378237e8 F2: a pre-lock repo whose first upgrade rolls back is left without a lock."""
    from psf.scaffold import lock_path
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    yml = factory / "factory.yml"
    yml.write_text(yml.read_text().replace("max_attempts: 2", "max_attempts: 7"))
    src = _target(tmp_path, lambda rel, t: t.replace("max_attempts: 2", "max_attempts: 3"))
    rep = run_upgrade(root, factory, source=src)
    assert not rep.applied and not lock_path(root).exists()


def test_rebase_records_its_own_id(tmp_path: Path):
    """R-378237e8 F1: the lock written by the rebase includes the rebase id, so it never re-runs
    (and re-adds a file the user later deletes) after a forced or resolved upgrade."""
    from psf.migrations import REBASE_ID, rebase_pending
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    current = render_template(UP, "off", "hitl")
    write_lock(root, Lock(revision="current", template_digest=digest(current), base=current,
                          migrations=["2026-09-bootstrap-lock"]).stamp())
    yml = factory / "factory.yml"
    yml.write_text(yml.read_text().replace("max_attempts: 2", "max_attempts: 7"))
    src = _target(tmp_path, lambda rel, t: t.replace("max_attempts: 2", "max_attempts: 3"))
    rep = run_upgrade(root, factory, source=src, force=True)     # writes markers, base not advanced
    assert rep.conflict and REBASE_ID in read_lock(root).migrations
    (factory / "agents/code-review.md").unlink()                 # deliberate deletion afterwards
    assert not rebase_pending(root, factory, list(read_lock(root).migrations))


def test_bootstrap_records_every_migration_id(tmp_path: Path):
    """R-378237e8 F1: after a pre-lock bootstrap, deleting a post-0.1.0 file must not trigger
    the rebase on the next upgrade (which would bring the file back)."""
    from psf.migrations import MIGRATIONS
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    assert run_upgrade(root, factory).applied
    assert {m.id for m in MIGRATIONS} <= set(read_lock(root).migrations)
    (factory / "agents/code-review.md").unlink()
    rep = run_upgrade(root, factory)
    assert not (factory / "agents/code-review.md").exists()
    assert run_upgrade(root, factory, check=True).drifted is False


# --- independent review R-f6501094 ---------------------------------------------

def test_force_then_resolved_keeps_a_later_deletion(tmp_path: Path):
    """R-f6501094 F1: files added by a forced, conflicted upgrade enter the base."""
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    yml = factory / "factory.yml"
    yml.write_text(yml.read_text().replace("max_attempts: 2", "max_attempts: 7"))
    src = _target(tmp_path, lambda rel, t: t.replace("max_attempts: 2", "max_attempts: 3"))
    rep = run_upgrade(root, factory, source=src, force=True)
    assert rep.conflict and (factory / "agents/code-review.md").exists()
    yml.write_text(render_template(UP, "off", "hitl")["factory.yml"].replace("max_attempts: 2", "max_attempts: 7"))
    assert run_upgrade(root, factory, source=src, resolved=True).applied
    lock = read_lock(root)
    assert "agents/code-review.md" in lock.base and digest(lock.base) == lock.template_digest
    (factory / "agents/code-review.md").unlink()
    assert run_upgrade(root, factory, source=src, check=True).drifted is False
    run_upgrade(root, factory, source=src)
    assert not (factory / "agents/code-review.md").exists()


def test_rebase_runs_when_owner_restored_the_files_by_hand(tmp_path: Path):
    """R-f6501094 F2: restoring missing files must not leave missing lines suppressed."""
    from psf.upgrade import run_upgrade
    root, factory = _legacy_repo(tmp_path)
    current = render_template(UP, "off", "hitl")
    write_lock(root, Lock(revision="current", template_digest=digest(current), base=current,
                          migrations=["2026-09-bootstrap-lock"]).stamp())
    for rel, text in current.items():                     # owner copied the missing files in
        if not (factory / rel).exists():
            (factory / rel).parent.mkdir(parents=True, exist_ok=True)
            (factory / rel).write_text(text)
    assert "code_review" not in (factory / "factory.yml").read_text()
    assert run_upgrade(root, factory, check=True).drifted
    rep = run_upgrade(root, factory)
    assert rep.applied and "code_review" in (factory / "factory.yml").read_text()


def test_conflict_without_verify_writes_nothing(tmp_path: Path):
    """R-f6501094 F3: --no-verify must not leave conflict markers behind."""
    from psf.scaffold import lock_path
    from psf.upgrade import run_upgrade
    root, factory, src = _conflicted_repo(tmp_path)
    before_yml, before_lock = (factory / "factory.yml").read_text(), lock_path(root).read_text()
    rep = run_upgrade(root, factory, source=src, verify=False)
    assert not rep.applied and any("rolled back" in n for n in rep.notes)
    assert (factory / "factory.yml").read_text() == before_yml
    assert lock_path(root).read_text() == before_lock
