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

from .scaffold import (Lock, as_str, digest, read_lock, render_template,
                       write_lock)


@dataclass
class Migration:
    id: str
    description: str
    applies: Callable[[Path, Path], bool]
    apply: Callable[[Path, Path], str]


def _bootstrap_applies(repo_root: Path, factory_dir: Path) -> bool:
    lock = read_lock(repo_root)
    return lock is None or not lock.base


def _bootstrap_apply(repo_root: Path, factory_dir: Path) -> str:
    """Give a pre-lock repo a template base + lock so it can be upgraded.

    Repos scaffolded before ``psf upgrade`` existed have no base to merge against;
    reconstruct it from the current defaults, honoring the repo's own mode and
    feedback settings so the base matches what it actually installed.
    """
    yml = factory_dir / "factory.yml"
    mode, fb_mode, upstream = "hitl", "hint", "marcusjhang/personal-software-factory"
    if yml.exists():
        import yaml

        raw = yaml.safe_load(yml.read_text()) or {}
        mode = as_str(raw.get("mode"), mode)
        fb = raw.get("feedback", {}) or {}
        fb_mode = as_str(fb.get("mode"), fb_mode)
        upstream = as_str(fb.get("upstream"), upstream)
    files = render_template(upstream, fb_mode, mode)
    write_lock(repo_root, Lock(revision="bootstrap", template_digest=digest(files),
                               base=files, migrations=[m.id for m in MIGRATIONS]).stamp())
    return "pinned current template as the upgrade base"


MIGRATIONS: list[Migration] = [
    Migration(
        id="2026-09-bootstrap-lock",
        description="Create psf.lock.json with a template base for repos scaffolded before upgrades existed.",
        applies=_bootstrap_applies,
        apply=_bootstrap_apply,
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
