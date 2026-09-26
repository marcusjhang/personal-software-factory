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


## Round 2 — consumer feedback (`live-translate-diarize-poc`, work item W-7fef699d)

A real run reported: **every gate green, artifact could not run** (`review_escape`).
8 high-severity runtime/lifecycle defects reached handoff because the gate suite was
entirely static. Dispositions (P1 = high):

| id | sev | finding (consumer) | disposition |
|---|---|---|---|
| R2-1 | high | `verify_command` was a keyless shape-only check that never connected to the integration. | **mitigated**: baseline-vacuity check (`command_is_vacuous`) + reachability advisory (`verify_reachability`); deterministic connection still must be configured (documented). |
| R2-2 | high | Acceptance criteria were prose satisfiable by plausible code; no run evidence required. | **partial**: spec prompt already requires behavioral/testable criteria; reachability advisory added. Full "evidence per criterion" (R2) is planned, not built. |
| R2-3 | high | Defects only visible on a **second run** / restart (audio context, persisted setup, timer/error, broken Retry). | **mitigated**: `gates.verify_command` accepts a **list** (run N checks, e.g. lifecycle/second-run); `H11` proves a second-run state leak is caught. |
| R2-4 | high | Dead logic: a state machine exercised only by the self-check, never called by the server. | **mitigated**: `dead_logic_under_test()` advisory appended to verification findings; `H9`. |
| R2-5 | high | `psf feedback export --github` **fails silently** when the `factory-feedback` label is missing. | **fixed**: creates the label first, verifies the issue URL, exits non-zero on failure; test + `H` coverage. |
| R2-6 | medium | Review approved code that could not start. | **mitigated**: a failing `verify_command` now blocks (`H4`); review stays advisory. |
| R2-7 | medium | A gate relying on bare `assert` is a no-op under `python -O`. | **fixed detector**: `failure_masked_by_optimize()` + `H10`. |
| R2-8 | medium | Spec assumed an API behaviour (a completion event) that never fires. | **planned**: label spec assumptions vs observations (R7) — not built. |

**Open P1 after round 2: mitigations landed; remaining are advisory by design (R2/R7/R8
need richer runtime evidence, planned). No unmitigated high-severity gate gap.**
