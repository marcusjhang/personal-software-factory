"""`psf upgrade` — reconcile a repo's factory with a newer template.

The model is Copier's: keep a *pristine base* (``psf.lock.json``'s ``base``) of
what was installed, then three-way merge it against the repo's current files
(ours) and a newer template (theirs). Local edits survive; real clashes surface
as conflict markers; added/removed template files follow the usual three-way
rules. A failed post-merge verification rolls the files back.

Structural changes that text cannot express are applied afterward as migrations
(``psf.migrations``). Nothing is written under ``--pretend``/``--check``, and the
lock's applied revision/digest only advances after a successful merge.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .migrations import legacy_base, rebase_pending, run_migrations
from .scaffold import (Lock, as_str, digest, lock_path, read_lock, read_template,
                       render_template, write_lock)


@dataclass
class Change:
    path: str
    action: str          # added | updated | merged | conflict | deleted | kept
    diff: str = ""
    conflict: bool = False


@dataclass
class UpgradeReport:
    revision: str = ""
    base_digest: str = ""
    target_digest: str = ""
    changes: list[Change] = field(default_factory=list)
    migrations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    drifted: bool = False
    applied: bool = False
    conflict: bool = False

    def to_dict(self) -> dict:
        return {"revision": self.revision, "base_digest": self.base_digest,
                "target_digest": self.target_digest, "drifted": self.drifted,
                "applied": self.applied, "conflict": self.conflict,
                "migrations": self.migrations, "notes": self.notes,
                "changes": [{"path": c.path, "action": c.action,
                             "conflict": c.conflict} for c in self.changes]}


def _merge(ours: str, base: str, theirs: str, label: str) -> tuple[str, bool]:
    """Three-way text merge via `git merge-file`; returns (text, conflicted)."""
    if ours == theirs:
        return ours, False
    if ours == base:
        return theirs, False
    if theirs == base:
        return ours, False
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "ours").write_text(ours)
        (d / "base").write_text(base)
        (d / "theirs").write_text(theirs)
        p = subprocess.run(["git", "merge-file", "-p", "-L", f"{label} (yours)",
                            "-L", label, "-L", f"{label} (upstream)",
                            str(d / "ours"), str(d / "base"), str(d / "theirs")],
                           capture_output=True, text=True)
        return p.stdout, p.returncode != 0


def _unified(ours: str | None, theirs: str | None, label: str) -> str:
    if ours is None or theirs is None:
        return ""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "a").write_text(ours)
        (d / "b").write_text(theirs)
        p = subprocess.run(["git", "diff", "--no-index", "--", "a", "b"],
                           capture_output=True, text=True, cwd=d)
        return p.stdout.replace(str(d / "a"), f"a/{label}").replace(str(d / "b"), f"b/{label}")


def plan(ours: dict[str, str], base: dict[str, str], theirs: dict[str, str]) -> list[tuple[Change, str | None]]:
    """Compute the merge. Returns [(change, new_text|None)]; None means delete."""
    out: list[tuple[Change, str | None]] = []
    for rel in sorted(set(ours) | set(base) | set(theirs)):
        o, b, t = ours.get(rel), base.get(rel), theirs.get(rel)
        if o is None and b is None:                       # new upstream file
            out.append((Change(rel, "added", _unified(None, t, rel)), t))
        elif o is None and b is not None:                 # locally deleted -> respect
            out.append((Change(rel, "kept", "", False), None))
        elif b is None and t is None:                     # only local -> keep
            out.append((Change(rel, "kept"), None))
        elif t is None and b is not None:                 # upstream removed it
            if o == b:
                out.append((Change(rel, "deleted"), None))
            else:
                out.append((Change(rel, "kept"), None))
        else:
            merged, conflict = _merge(o, b or "", t, rel)
            if merged == o:
                out.append((Change(rel, "kept"), None))
            elif merged == t:
                out.append((Change(rel, "updated", _unified(o, t, rel)), t))
            else:
                out.append((Change(rel, "merged", _unified(o, merged, rel), conflict), merged))
    return out


def _consumer_settings(factory_dir: Path) -> tuple[str, str, str]:
    """Read the repo's own mode/feedback so the target matches its choices."""
    yml = factory_dir / "factory.yml"
    mode, fb_mode, upstream = "hitl", "hint", "marcusjhang/personal-software-factory"
    if yml.exists():
        try:
            import yaml

            raw = yaml.safe_load(yml.read_text()) or {}
            mode = as_str(raw.get("mode"), mode)
            fb = raw.get("feedback", {}) or {}
            fb_mode = as_str(fb.get("mode"), fb_mode)
            upstream = as_str(fb.get("upstream"), upstream)
        except Exception:  # noqa: BLE001 - a broken yml is caught by validate later
            pass
    return upstream, fb_mode, mode


def template_from(path: str | Path) -> tuple[dict[str, str], str]:
    """Load a target template from a dir (template root, or a repo's factory/).

    A template must be complete: a partial directory would make absent files look
    like upstream deletions and silently delete the consumer's files.
    """
    p = Path(path)
    if (p / "factory.yml").exists():
        files = read_template(p)
    elif (p / "factory" / "factory.yml").exists():
        files = read_template(p / "factory")
    else:
        raise FileNotFoundError(f"no factory.yml (or factory/factory.yml) under {p}")
    required = set(render_template("owner/repo", "off", "hitl"))
    missing = sorted(required - set(files))
    if missing:
        raise ValueError(f"incomplete template under {p}: missing {missing}")
    return files, digest(files)


def run_upgrade(repo_root: str | Path, factory_dir: str | Path, *, source: str | Path | None = None,
                revision: str | None = None, pretend: bool = False, check: bool = False,
                force: bool = False, verify: bool = True, resolved: bool = False) -> UpgradeReport:
    repo_root, factory_dir = Path(repo_root), Path(factory_dir)
    if resolved:
        return _mark_resolved(repo_root, factory_dir, source=source, revision=revision,
                              dry_run=check or pretend)
    if source is not None:
        theirs, target_digest = template_from(source)
        revision = revision or f"local:{Path(source)}"
    else:
        upstream, fb_mode, mode = _consumer_settings(factory_dir)
        theirs = render_template(upstream, fb_mode, mode)
        target_digest = digest(theirs)
        revision = revision or "current"

    ours = read_template(factory_dir)
    lock_before = _snapshot_lock(repo_root)   # a rollback restores the lock too (R-378237e8 F2)
    lock = read_lock(repo_root)
    base = dict(lock.base) if lock else {}
    rep = UpgradeReport(revision=revision, base_digest=digest(base) if base else "",
                        target_digest=target_digest)

    if not base and (check or pretend):
        rep.drifted = True
        rep.notes.append("no template base pinned (run `psf upgrade` to bootstrap it)")
        return rep

    applied = list(lock.migrations) if lock else []
    if not base:                       # pre-lock repo: bootstrap the base first
        applied, rep.notes = run_migrations(repo_root, factory_dir, applied)
        lock = read_lock(repo_root)
        base = dict(lock.base) if lock else {}
        rep.base_digest = digest(base) if base else ""
    elif rebase_pending(repo_root, factory_dir, applied):
        # Lock pinned by the old bootstrap (current template as base): re-pin to
        # the 0.1.0 template first, or files added since 0.1.0 never arrive.
        if check or pretend:
            base = legacy_base(factory_dir)
            rep.notes.append("bootstrap base is stale: the next `psf upgrade` re-pins it to the 0.1.0 template")
        else:
            applied, notes = run_migrations(repo_root, factory_dir, applied)
            rep.notes += notes
            lock = read_lock(repo_root)
            base = dict(lock.base) if lock else {}
        rep.base_digest = digest(base) if base else ""

    merged = plan(ours, base, theirs)
    rep.changes = [c for c, _ in merged]
    rep.drifted = any(c.action in ("added", "updated", "merged", "deleted", "conflict")
                      for c in rep.changes)
    rep.conflict = any(c.conflict for c in rep.changes)

    if check or pretend:
        return rep

    if rep.conflict and not force:
        # Never write conflict markers unless asked, whether or not verification runs
        # (review R-f6501094 F3: --no-verify used to leave markers in place).
        _restore_lock(repo_root, lock_before)
        conflicted = ", ".join(c.path for c in rep.changes if c.conflict)
        rep.notes.append(f"rolled back: merge conflicts in {conflicted}; nothing was written")
        rep.notes.append("to resolve: `psf upgrade --force` (writes the conflict markers), edit the marked files, "
                         "`psf validate`, then `psf upgrade --resolved`")
        return rep

    for change, text in merged:
        if change.action == "kept":
            continue                       # no upstream change; leave local file alone
        target = factory_dir / change.path
        if change.action == "deleted":
            if target.exists():
                target.unlink()
            continue
        if text is None:                   # defensive: only a deletion may be None
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    if base:                               # structural migrations (post-merge)
        applied, extra = run_migrations(repo_root, factory_dir, applied)
        rep.notes += extra
    rep.migrations = applied

    if verify and not force:
        err = _verify(factory_dir)
        if err:
            _restore(factory_dir, ours, {c.path for c, _ in merged})
            _restore_lock(repo_root, lock_before)
            rep.migrations = list(read_lock(repo_root).migrations) if lock_before else []
            rep.notes.append(f"rolled back: verification failed — {err}")
            return rep

    # Advance the base to the target for everything that merged; a file still in
    # conflict keeps its old base so `--resolved` can move it after a human fixes it.
    # (Keeping the old base for *every* file after a forced merge left newly added
    # files out of the base, so a later deletion brought them back: R-f6501094 F1.)
    new_base = dict(theirs)
    for c in rep.changes:
        if c.conflict:
            if c.path in base:
                new_base[c.path] = base[c.path]
            else:
                new_base.pop(c.path, None)
    write_lock(repo_root, Lock(revision=revision, template_digest=target_digest, migrations=applied,
                               base=new_base,
                               conflicts=sorted(c.path for c in rep.changes if c.conflict)).stamp())
    rep.applied = True
    return rep


def _mark_resolved(repo_root: Path, factory_dir: Path, *, source: str | Path | None,
                   revision: str | None, dry_run: bool = False) -> UpgradeReport:
    """After `psf upgrade --force` left conflicts and a human resolved them by hand,
    advance the base of exactly those files (recorded in the lock as `conflicts`)
    to the target template, so `--check` stops reporting the same conflict forever.

    Only a forced merge writes the clean upstream hunks next to the markers, so only
    its conflicts can be marked resolved: marking a file whose merge was never
    written would bury upstream changes for good (review R-aaf05b23 F1). Every other
    file keeps its base, so pending upstream changes still arrive and deliberate
    deletions stay deleted (R-378237e8 F4/F5); a conflict resolved by deleting the
    file stays deleted too (R-aaf05b23 F3). Refuses with no pinned base, no forced
    conflict pending, a different target than the forced merge, remaining markers,
    or a factory that does not verify. Nothing is written under `--check`/`--pretend`.
    """
    if source is not None:
        theirs, target_digest = template_from(source)
        revision = revision or f"local:{Path(source)}"
    else:
        theirs = render_template(*_consumer_settings(factory_dir))
        target_digest = digest(theirs)
        revision = revision or "current"
    lock = read_lock(repo_root)
    rep = UpgradeReport(revision=revision, base_digest=digest(lock.base) if lock and lock.base else "",
                        target_digest=target_digest)
    if not lock or not lock.base:
        rep.notes.append("not marked resolved: no upgrade base pinned yet; run `psf upgrade` first")
        return rep
    if not lock.conflicts:
        rep.notes.append("not marked resolved: no forced conflict is pending; run `psf upgrade` "
                         "(and `psf upgrade --force` if it reports a conflict)")
        return rep
    if lock.template_digest != target_digest:
        rep.notes.append("not marked resolved: the target differs from the one the conflicts came from; "
                         "use the same template (or `--from`) as the forced upgrade")
        return rep
    err = _verify(factory_dir)
    if err:
        rep.notes.append(f"not marked resolved: {err}")
        return rep
    ours = read_template(factory_dir)
    new_base = dict(lock.base)
    for rel in lock.conflicts:
        if rel in theirs:
            new_base[rel] = theirs[rel]
        else:
            new_base.pop(rel, None)
    rep.changes = [Change(rel, "resolved") for rel in lock.conflicts]
    remaining = [c for c, _ in plan(ours, new_base, theirs) if c.action != "kept"]
    rep.drifted = bool(remaining)
    if dry_run:
        rep.notes.append(f"would mark resolved: {', '.join(lock.conflicts)}")
        return rep
    write_lock(repo_root, Lock(revision=lock.revision, template_digest=lock.template_digest,
                               migrations=list(lock.migrations), base=new_base).stamp())
    rep.applied = True
    rep.notes.append(f"marked resolved: {', '.join(lock.conflicts)}; local files left as they are")
    if remaining:
        rep.notes.append("upstream changes still pending; run `psf upgrade` to apply them: "
                         + ", ".join(c.path for c in remaining))
    return rep


def _snapshot_lock(repo_root: Path) -> str | None:
    p = lock_path(repo_root)
    return p.read_text() if p.exists() else None


def _restore_lock(repo_root: Path, before: str | None) -> None:
    """Put the lock back exactly as it was before this upgrade (or remove it)."""
    p = lock_path(repo_root)
    if before is None:
        if p.exists():
            p.unlink()
    else:
        p.write_text(before)


def _restore(factory_dir: Path, before: dict[str, str], touched: set[str]) -> None:
    """Undo a merge: put back the original files and remove anything we added."""
    for rel in set(before) | touched:
        p = factory_dir / rel
        if rel in before:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(before[rel])
        elif p.exists():
            p.unlink()


def _verify(factory_dir: Path) -> str | None:
    from .audit import run_audit

    for f in factory_dir.rglob("*"):
        if f.is_file() and f.suffix in (".yml", ".yaml", ".md"):
            text = f.read_text(errors="replace")
            if "\n<<<<<<< " in "\n" + text or "\n>>>>>>> " in "\n" + text:
                return f"unresolved conflict markers in {f.relative_to(factory_dir)}"
    try:
        rep = run_audit(factory_dir, factory_dir.parent / ".psf" / "factory.db", include_bench=False)
    except Exception as e:                 # e.g. YAML that no longer parses: roll back, never crash
        first = (str(e).strip().splitlines() or [""])[0]
        return f"factory no longer loads: {type(e).__name__}: {first}"
    if not rep.healthy:
        return "; ".join(f"{c.name}: {c.detail}" for c in rep.failures)
    return None
