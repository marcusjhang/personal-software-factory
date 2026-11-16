# Changelog

What changed in psf and why. Newest first. Consumer projects get template changes with `psf upgrade`.

## 0.2.2 — 2026-11-16

Verified and merged by sidework.productivity under Marcus's standing permission. Evidence is in the PR.

### Fixed
- **`psf upgrade` silently skipped new template files and lines in repos created before the lock existed.** Bootstrap
  pinned the *current* template as the merge base, so everything added since 0.1.0 (`agents/code-review.md`,
  `gates.code_review`) looked like a local deletion and never arrived, while `psf validate` still passed. Bootstrap
  now pins a frozen copy of the 0.1.0 template (`src/psf/template_history.py`). A one-time migration
  (`2026-11-rebase-bootstrap-base`) repairs locks the old bootstrap wrote, but only where a template file is actually missing,
  so the next `psf upgrade` adds the missing files. If the repo also changed `factory.yml`, that surfaces as a conflict to
  resolve by hand (see docs/UPGRADE.md). Why: consumer feedback (experiments). It was confirmed in 5 repos.
- **A conflicted upgrade no longer crashes.** The post-merge check now catches unresolved markers and a factory that no
  longer parses, then rolls back instead of throwing a YAML traceback. Why: consumer feedback (asian-bounty).
### Added
- `psf upgrade --resolved`: after resolving conflicts by hand, it advances the base so `--check` stops reporting the same
  conflict forever. It refuses with no pinned base, while markers remain, or when the factory doesn't verify. Template files
  still missing locally stay addable. Why: consumer feedback (asian-bounty).

## 0.2.1 — 2026-11-16

Verified and merged by sidework.productivity under Marcus's standing permission. Evidence is in the PR.

### Added
- `psf feedback export --local`: always writes a local file and never publishes, even when `feedback.mode` is `auto`
  or `off`. Why: consumers export weekly as a local file only. `auto` mode silently filed a GitHub issue, and `off`
  mode silently wrote nothing (consumer feedback).
- `psf feedback export --if-changed`: skips when there is no new work since the newest local export, and skips an
  empty first export. Why: export only in weeks that had work, with no empty exports.
- Envelopes carry `source`, a random per-repo id kept in `.psf/source-id`. It is stable from any folder and is not derived from the path. Why: dedupe.
- `--if-changed` requires `--local` and the default output, so an unpublished or custom-named export can't hide new work.

### Fixed
- `psf feedback report` double-counted, because exports are cumulative and report summed every envelope from the
  same repo. It now keeps the newest envelope per `source` and reports `superseded`. A malformed `source` from an issue no longer crashes `report`.

### Changed
- The template AGENTS feedback step is now `psf feedback export --local --if-changed`; `--github` is used only when the
  maintainer asks.

## 0.2.0 — 2026-11-16

Verified and merged by sidework.productivity under Marcus's standing permission (16 Nov 2026). Evidence is in the PR.
Upgrade: reinstall psf (`install.sh`, or `uv tool install --force git+https://github.com/marcusjhang/personal-software-factory@v0.2.0`), then run `psf upgrade` in your repo.

### Added
- **`psf review`: the OCR delegate code-review loop.** Why: psf gated on correctness only; nothing caught
  duplication, dead code, weak error handling or complexity. `psf review start [--base REF | --full]` selects files
  (the diff through `ocr delegate preview`, or every tracked code file) and resolves rules (`ocr delegate rule`).
  `psf review record` scores a round and returns DONE, CONTINUE or STOP: stop at ≤2 verified high/critical findings,
  with a cap of 5 rounds. Without `ocr` it fails closed.
- **Template:** `gates.code_review` (stop rule), `agents/code-review.md` (reviewer procedure), and a
  "Code review loop" step in `AGENTS.md`. Existing projects get them with `psf upgrade`.
- **Skill `code-review-loop`.** The feedback-ingestion skill reuses it, so there is one loop and no copied steps.
