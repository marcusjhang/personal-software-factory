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

## Round 3: the loop becomes `psf review` (2026-11-16)

The stop rule changes from 0 open P1 to **≤2 verified high/critical** with a **cap of 5 rounds** (STOP is reported).
The mechanics are now code (`src/psf/codereview.py`, `psf review`). The judgment is in the skill
`code-review-loop` and the template prompt `agents/code-review.md`. The loop ran on its own diff:

### Review R-c2a231eb (workspace, 4 files) → DONE

| round | findings | verified high+ | decision |
|---|---|---|---|
| 1 | 2 | 0 | DONE |

| id | sev | finding | disposition |
|---|---|---|---|
| M1 | medium | a corrupt session JSON was reported as "cannot read findings" | fixed, with test `test_corrupt_session_is_a_review_error` |
| L1 | low | a `--base` value starting with `-` reaches ocr unchecked (local CLI input only) | accepted |

### Pre-merge review R-ac65af1a (range main..eafba22, 6 files) → DONE (independent reviewer)

| round | findings | verified high+ | decision |
|---|---|---|---|
| 1 | 2 | 0 | DONE |

| id | sev | finding | disposition |
|---|---|---|---|
| CR1 | medium | an invalid `factory.yml` silently fell back to the default stop rule in `psf review start` | fixed: an invalid factory now errors (exit 5); a missing factory still uses the defaults. Tests added |
| CR2 | low | a truncated session file raised KeyError | fixed: `load()` checks the required keys. Test added |

### Pre-merge review R-a9d61a89 (0.2.1, range d194835..665dcf5, 5 files) → DONE (independent reviewer)

Round 1: 7 findings, 0 verified high+. F1 (medium: a non-string `source` crashed `report`) fixed. F2 (medium: `--if-changed` with
publishing could skip an unpublished envelope) fixed: `--if-changed` now requires `--local`. F3 and F4 (low: the source id depended on cwd and was a
guessable path hash) fixed: random id in `.psf/source-id`. F6 (low) fixed. F7 (style) fixed. F5 (low: a spoofed envelope can hide another
repo's signals) accepted, because feedback is evidence and never authority.

### Pre-merge review for 0.2.2 (upgrade fixes), independent reviewers

| session | range | round result | notes |
|---|---|---|---|
| R-0a2fd23c | 5efc4b7..4d58e47 | 6 findings, **3 verified high → CONTINUE** | R1–R3 (high) and R4 (medium) all came from a new insert-only auto-merge that could silently lose or override user config (separator mis-parse, duplicate YAML keys, blank-line base, unchecked git rc). **Resolver removed**: conflicts stay with a human. R5 (medium, `--resolved` could re-create the skip bug) fixed. R6 (low, CRLF, pre-existing) accepted |
| R-378237e8 | 5efc4b7..de30810 | 2 findings, 0 verified high → DONE | S1 (medium) fixed: the rollback note says how to resolve. S2 (low, read-only probe of the lock's own keys) accepted |
| (self) | de30810..final | 0 findings → DONE | message-only change for S1 |

**Correction (not merged):** R-378237e8 was recorded as DONE from the reviewer's interim result. Its final result was
F1 (high: a deleted file comes back because the migration ids recorded after bootstrap are incomplete), F2 (high: the rebase
writes the lock before merging and a rollback doesn't restore it, so a repo can be stuck in a permanent conflict), F3 (medium:
`--resolved` writes the lock under `--check`/`--pretend`), F4 (medium: `--resolved` re-adds files the user deliberately deleted), F5 (medium:
`--resolved` without a pending conflict suppresses upstream changes), and F6 (info: the frozen 0.1.0 template is byte-identical).
**0.2.2 is held on branch `fix/bootstrap-base-0.1` and not merged.** Every fix round has turned up new problems in the
rebase and `--resolved` design. Next: restore the lock on rollback (F2), persist all migration ids (F1), make
`--resolved` honour check/pretend, keep deliberate deletions, and require a pending conflict (F3–F5). Then run a fresh
independent review.

### 0.2.2 finished (weekly pass, 2026-11-21), independent reviewers

The held R-378237e8 findings were fixed first: a rollback restores the lock (F2), every migration id is recorded after
bootstrap (F1), and `--resolved` honours check/pretend, needs a pending conflict and keeps deliberate deletions (F3–F5).
8 regression tests. Then three fresh independent review rounds on `main..HEAD`:

| session | head | result | notes |
|---|---|---|---|
| R-f6501094 | 5312698 | 7 findings, 2 verified high → DONE (fixed anyway) | F1 high: a forced merge kept the old base for every file, so added files came back after deletion → clean files now take the target base. F2 high: the rebase skipped repos whose owners restored files by hand, so lines stayed suppressed → every old-bootstrap lock is rebased. F3 medium: `--no-verify` left markers → a conflict without `--force` writes nothing. F4/F5 low fixed. F6 (read_lock on null fields, pre-existing) and F7 accepted (F7 fixed in the next round) |
| R-aaf05b23 | f6bf3ee | 5 findings, 1 verified high → DONE (fixed anyway) | F1 high: `--resolved` after a rolled-back merge buried that file's clean upstream hunks → `--force` records `conflicts` in the lock and `--resolved` acts only on them (and refuses a different target). F2 medium: refused `--resolved` exited 0 → exit 1. F3 medium: a conflict resolved by deletion came back → stays deleted. F4 accepted, F5 fixed |
| R-2ec9cf53 | 5da626c | 3 findings, 0 verified high → DONE | F1 medium: a target change between `--force` and `--resolved` needs a second resolution. F2 low: `--force` twice nests markers. F3 low: `--resolved --check` refusal exits 0. All accepted and ledgered |
