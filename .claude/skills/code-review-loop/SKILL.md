---
name: code-review-loop
description: >
  Run the OCR delegate-mode code-review loop on a feature, branch or whole repo:
  `psf review start`, review the listed files against the resolved OCR rules,
  verify each high/critical finding, fix them, re-review, and stop when at most
  2 verified highs remain (cap 5 rounds). Use at the end of every feature, for a
  one-off full-repo review ("review the whole codebase"), or when another skill
  says "run the OCR loop".
license: MIT
compatibility: >
  Requires the `ocr` CLI (open-code-review, delegate mode, no LLM key):
  `npm install -g @alibaba-group/open-code-review`, or set PSF_OCR to its path.
---

# Code review loop

`psf review` does the mechanics (file selection, rule resolution, round ledger,
stop rule). You do the review. Follow `factory/agents/code-review.md`; in short:

```bash
psf review start                    # uncommitted changes (workspace mode)
psf review start --base main        # a branch: main..HEAD
psf review start --full             # every tracked code file, once per project
# read .psf/review/<session>.json: files + rule groups; review each file against its group
psf review record findings.json     # exit 0 DONE · 10 CONTINUE (fix highs, re-review) · 11 STOP (did not converge)
psf review status                   # round table; paste into docs/CODE-REVIEW-ROUNDS.md
```

`findings.json` is a list of `{id, severity, file, summary, verified, disposition}`.
`severity` is one of critical, high, medium, low, info, taste or style. Only **verified** high or critical
findings count. Medium and lower, taste and style never block.

Rules:
- Verify a high finding before counting it: reproduce it, or name the line and the input that breaks.
- On CONTINUE, fix every verified high/critical finding, add a regression test for behavioral bugs, run the
  project's tests, and review the changed files again in the next round.
- On STOP, report the remaining highs. Never call the code clean without the round that shows it.
- The stop rule comes from `gates.code_review` in `factory/factory.yml` (default `max_highs: 2`, `max_rounds: 5`).
  The CLI flags `--max-highs` and `--max-rounds` override it for one session.

Afterwards, file psf feedback (OCR false positives, gates that blocked for no reason, anything slow or missing)
the way your workspace documents it.
