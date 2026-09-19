# Code Review — rounds

Iterative OpenCodeReview (OCR) passes over the factory. Method: OCR **delegation
mode** (`ocr delegate preview` / `ocr delegate rule`, no LLM key required) selects
the reviewable files and resolves the rules; the agent performs the review and the
fixes. P1 = OCR severity **critical** or **high**. Stop rule: a full pass reports
**≤2 open P1**.

## Round 0 — baseline review (pre-OCR-loop)

Full pass over the added code (`82e2a32..HEAD`). Findings and dispositions are in
[CODE-REVIEW.md](./CODE-REVIEW.md): **H1, H2** (high) and **M1, M2, M4, M5**
(medium) fixed; **M3, L4–L6** accepted/documented. Fixes re-verified by the whole
battery.

## Round 1 — OCR loop

```
ocr delegate preview --from 82e2a32 --to HEAD --format json
→ 76 reviewable files (40 code: src/psf/**, scripts/**, pyproject, Dockerfile, install.sh)
ocr delegate rule <code files>  → 2 rule groups (correctness/security/perf/maintainability; typo/idiom)
```

**Coverage:** 40/40 code files reviewed (in depth: state, events, durability,
audit, schema, agents, workspace, adapters/common, evaluation, improve, foreman,
classifier, supervisor, feedback, github, bench, canonical, calibrate, evalkit, cli;
pattern-scanned: eval suites, repobench/ossbench, scripts).

**Open P1 after round 1: 0** — the high-severity issues (H1 runner abort, H2
worktree re-run crash) were already fixed in round 0 and do not reproduce. New
findings this round were all **low/medium** and were fixed as part of the
"evals/guardrails sufficient" work:

| id | sev | finding | disposition |
|---|---|---|---|
| R1-1 | low | CLI help strings stale (`eval-self` said E2/E5…, `eval-adapters` said A1–A4, `eval-supervisor` said S1–S8) | fixed |
| R1-2 | low | `AGENTS.md` told agents to set the legacy `feedback.publish: true` | fixed → `feedback.mode: auto` |
| R1-3 | medium | adapters' `verify` was LLM-judged only (no deterministic check) | fixed → `gates.verify_command` (H4) |
| R1-4 | medium | no `psf cancel` / `psf unblock` despite state support | fixed → commands + H6 |
| R1-5 | medium | `limits.max_minutes` unenforced | fixed → enforced (H5) |
| R1-6 | medium | evals not mutation-tested (sensitivity asserted, not shown) | fixed → H1/H2/H3 inject violations and assert detection |
| R1-7 | low | ledger append single-writer not documented | documented (M3 / GUARDRAILS #23) |

**Stop rule met:** 0 open P1 (≤ 2). Loop terminated after one round.

## Result

- Open P1: **0**.
- Regression: full battery green after every fix (see [GUARDRAILS.md](./GUARDRAILS.md)).
