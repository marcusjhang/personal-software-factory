# Updating the factory (`psf upgrade`)

Your `factory/` is repo-native config — `psf` upgrades don't rewrite it behind
your back. Updates are an explicit, reviewable **three-way merge**, the same idea
`copier update` uses.

## The pieces

| file | role |
|---|---|
| `factory/` | your live factory — prompts, `factory.yml`, `AGENTS.md`. Edit freely. |
| `psf.lock.json` | the pin: applied `revision`, `template_digest`, applied migrations, and `base` (a pristine snapshot of the template as you installed it = the merge base). Tracked, so CI sees it. |

`psf init` writes the factory plus the lock. The lock's `base` is what makes an
update a well-defined diff instead of a guess.

## The flow

```bash
psf upgrade --check                 # CI: exit 1 if an update would change anything
psf upgrade --pretend               # show the plan (added/updated/merged/conflict); write nothing
psf upgrade                         # merge + apply; keeps your local edits
psf upgrade --from ./pinned-template --to v0.2   # merge from a specific template (tag/tarball)
```

Merge rules (per file): if you didn't touch it → take upstream; if upstream didn't
touch it → keep yours; if you both changed it → three-way merge, with conflict
markers if the same lines clash; a file you deleted stays deleted; a new upstream
file arrives.

Applying only succeeds if `psf validate` and `psf audit` pass (skip with
`--no-verify`, override with `--force`). The base and lock advance **only after a
conflict-free, verified apply** — so `psf audit` warns if a merge was left
unresolved.

## Migrations

Not everything is text-mergeable (a renamed key, a required field). Those ship as
ordered, idempotent migrations in `src/psf/migrations.py` and run after the merge;
applied ids are recorded in the lock. Repos scaffolded before this feature existed
are upgraded by the `2026-09-bootstrap-lock` migration, which snapshots their
current template as the base.

## Two channels (don't confuse them)

- **The tool** (`psf` itself) updates like any dependency: `pipx upgrade
  personal-software-factory`, `uv tool upgrade`, or
  `pipx install --force git+https://github.com/<upstream>`.
- **Your `factory/`** updates by `psf upgrade` — a merge you review and commit in
  *your* git.

`psf audit` reports `factory.revision` so you can see what you're pinned to and
whether the base is self-consistent.
