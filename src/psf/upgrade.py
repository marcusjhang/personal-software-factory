"""`psf upgrade` — reconcile a repo's factory with a newer template.

The model is Copier's: keep a *pristine base* (``.psf/template``) of what was
installed, then three-way merge it against the repo's current files (ours) and a
newer template (theirs). Local edits survive; real clashes surface as conflict
markers; added/removed template files are handled by the usual three-way rules.

Structural changes that text cannot express are applied afterward as migrations
(``psf.migrations``). Nothing is written under ``--pretend``/``--check``, and the
lock's applied revision/digest only advances after a successful merge.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .migrations import run_migrations
from .scaffold import (Lock, as_str, digest, read_lock, read_template,
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
    """Load a target template from a dir (template root, or a repo's factory/)."""
    p = Path(path)
    if (p / "factory.yml").exists():
        files = read_template(p)
    elif (p / "factory" / "factory.yml").exists():
        files = read_template(p / "factory")
    else:
        raise FileNotFoundError(f"no factory.yml (or factory/factory.yml) under {p}")
    return files, digest(files)


def run_upgrade(repo_root: str | Path, factory_dir: str | Path, *, source: str | Path | None = None,
                revision: str | None = None, pretend: bool = False, check: bool = False,
                force: bool = False, verify: bool = True) -> UpgradeReport:
    repo_root, factory_dir = Path(repo_root), Path(factory_dir)
    if source is not None:
        theirs, target_digest = template_from(source)
        revision = revision or f"local:{Path(source)}"
    else:
        upstream, fb_mode, mode = _consumer_settings(factory_dir)
        theirs = render_template(upstream, fb_mode, mode)
        target_digest = digest(theirs)
        revision = revision or "current"

    ours = read_template(factory_dir)
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

    merged = plan(ours, base, theirs)
    rep.changes = [c for c, _ in merged]
    rep.drifted = any(c.action in ("added", "updated", "merged", "deleted", "conflict")
                      for c in rep.changes)
    rep.conflict = any(c.conflict for c in rep.changes)

    if check or pretend:
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
            rep.notes.append(f"NOT applied: verification failed — {err}")
            return rep

    # Advance the base only when the merge is conflict-free; otherwise keep the
    # old base so the upgrade can be retried after the conflict is resolved.
    new_base = base if rep.conflict else theirs
    write_lock(repo_root, Lock(revision=revision, template_digest=target_digest,
                               migrations=applied, base=new_base).stamp())
    rep.applied = True
    return rep


def _verify(factory_dir: Path) -> str | None:
    from .audit import run_audit

    rep = run_audit(factory_dir, factory_dir.parent / ".psf" / "factory.db", include_bench=False)
    if not rep.healthy:
        return "; ".join(f"{c.name}: {c.detail}" for c in rep.failures)
    return None
