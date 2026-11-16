# Changelog

What changed in psf and why. Newest first. Consumer projects get template changes with `psf upgrade`.

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
