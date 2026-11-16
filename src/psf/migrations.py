"""Ordered, idempotent migrations for a consumer's factory.

A three-way merge handles *textual* change, but some upstream changes are
structural (a key renamed, a required field added, a file relocated) and cannot
be merged. Those ship as migrations here: each declares a predicate for when it
applies and an action that is safe to run more than once. Applied ids are
recorded in ``psf.lock.json`` so they run at most once.

Adding a migration: append to MIGRATIONS with a new id; never edit a shipped one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .scaffold import Lock, as_str, digest, read_lock, write_lock
from .template_history import render_0_1_0


@dataclass
class Migration:
    id: str
    description: str
    applies: Callable[[Path, Path], bool]
    apply: Callable[[Path, Path], str]


def _bootstrap_applies(repo_root: Path, factory_dir: Path) -> bool:
    lock = read_lock(repo_root)
    return lock is None or not lock.base


def _settings(factory_dir: Path) -> tuple[str, str, str]:
    """The repo's own mode / feedback mode / upstream, so a base matches what it installed."""
    yml = factory_dir / "factory.yml"
    mode, fb_mode, upstream = "hitl", "hint", "marcusjhang/personal-software-factory"
    if yml.exists():
        import yaml

        try:
            raw = yaml.safe_load(yml.read_text()) or {}
        except yaml.YAMLError:
            raw = {}
        if isinstance(raw, dict):
            mode = as_str(raw.get("mode"), mode)
            fb = raw.get("feedback", {}) or {}
            if isinstance(fb, dict):
                fb_mode = as_str(fb.get("mode"), fb_mode)
                upstream = as_str(fb.get("upstream"), upstream)
    return upstream, fb_mode, mode


def _legacy_base(factory_dir: Path) -> dict[str, str]:
    """The 0.1.0 template: the newest template a pre-lock repo can have come from.

    Using the *current* template here (the old behavior) made every file and line
    added upstream since 0.1.0 look like a local deletion, so upgrades silently
    never delivered them (e.g. agents/code-review.md, gates.code_review).
    """
    return render_0_1_0(*_settings(factory_dir))


def _bootstrap_apply(repo_root: Path, factory_dir: Path) -> str:
    """Give a pre-lock repo a template base + lock so it can be upgraded."""
    files = _legacy_base(factory_dir)
    write_lock(repo_root, Lock(revision="bootstrap-0.1.0", template_digest=digest(files),
                               base=files, migrations=[m.id for m in MIGRATIONS]).stamp())
    return "pinned the 0.1.0 template as the upgrade base"


REBASE_ID = "2026-11-rebase-bootstrap-base"


def legacy_base(factory_dir: Path) -> dict[str, str]:
    return _legacy_base(factory_dir)


def rebase_pending(repo_root: Path, factory_dir: Path, applied: list[str]) -> bool:
    """True when this lock was pinned by the old bootstrap and must be re-based
    *before* merging (a post-merge migration would be overwritten by the new base)."""
    return REBASE_ID not in applied and _rebase_applies(repo_root, factory_dir)


def _rebase_applies(repo_root: Path, factory_dir: Path) -> bool:
    """Only locks pinned by the old bootstrap that show the actual symptom: a
    template file the stale base claims was installed is absent from the factory.
    Repos whose owners already restored the files are left alone."""
    lock = read_lock(repo_root)
    if not (lock and lock.base and "2026-09-bootstrap-lock" in (lock.migrations or [])):
        return False
    legacy = _legacy_base(factory_dir)
    return any(rel not in legacy and not (factory_dir / rel).exists() for rel in lock.base)


def _rebase_apply(repo_root: Path, factory_dir: Path) -> str:
    """Repair locks pinned by the old bootstrap (current template as base).

    Those repos never received files/lines added after 0.1.0. Re-pin the base to
    the 0.1.0 template so the next merge adds them; local edits still merge.
    """
    lock = read_lock(repo_root)
    files = _legacy_base(factory_dir)
    write_lock(repo_root, Lock(revision="bootstrap-0.1.0", template_digest=digest(files), base=files,
                               migrations=list(lock.migrations or [])).stamp())
    return "re-pinned the bootstrap base to the 0.1.0 template (missing template files will now be added)"


MIGRATIONS: list[Migration] = [
    Migration(
        id="2026-09-bootstrap-lock",
        description="Create psf.lock.json with a template base for repos scaffolded before upgrades existed.",
        applies=_bootstrap_applies,
        apply=_bootstrap_apply,
    ),
    Migration(
        id=REBASE_ID,
        description="Re-pin locks created by the old bootstrap to the 0.1.0 template so missed template files arrive.",
        applies=_rebase_applies,
        apply=_rebase_apply,
    ),
]


def run_migrations(repo_root: Path, factory_dir: Path, applied: list[str]) -> tuple[list[str], list[str]]:
    """Run every pending migration in order; return (applied_ids, notes)."""
    notes: list[str] = []
    done = list(applied)
    for m in MIGRATIONS:
        if m.id in done:
            continue
        if not m.applies(repo_root, factory_dir):
            continue
        notes.append(f"{m.id}: {m.apply(repo_root, factory_dir)}")
        done.append(m.id)
    return done, notes
