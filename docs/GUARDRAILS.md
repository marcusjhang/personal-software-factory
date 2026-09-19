# Guardrails — matrix and proof

Every guardrail the factory enforces, the mechanism that enforces it, and the
eval/test that **proves** it. Guardrail + adapter suites run as part of
`psf audit` (so they are exercised on every health check), and `psf improve`
refuses to promote unless the audit is green.

## Enforcement matrix

| # | Guardrail | Mechanism (code) | Proof |
|---|---|---|---|
| 1 | Only the controller writes lifecycle state | `state.Workflow`; agents return typed results | `E6`, `H1` |
| 2 | Closed transition table; illegal transitions refused | `state.TRANSITIONS` + `_check_guard` | `H1`, `test_illegal_transition_and_ready_gate` |
| 3 | `READY` requires a digest-bound approval | `_check_guard` compares `approval_digest == spec_digest` | `H2`, `E6` |
| 4 | Independent verification, quorum (default 2) | `foreman` verify loop `factory.verify_quorum` | `E2`, process eval (defects 18→2) |
| 5 | Deterministic project check | `gates.verify_command` run in the worktree | `H4` |
| 6 | Bounded retries | `limits.max_attempts`; exhaustion → `BLOCKED` | `test_foreman_retries_then_blocks` |
| 7 | Wall-clock / cost budget | `limits.max_minutes` enforced in the build loop | `H5` |
| 8 | Cancel and unblock | `psf cancel` / `psf unblock`; unblock only to saved state | `H6` |
| 9 | Review cannot veto verified work silently | advisory unless `blocking: true` + notes | `E27`, `F10` fix |
| 10 | Append-only, tamper-evident ledger | hash chain + `verify_chain` | `H3`, `E7` |
| 11 | Protected evaluation (candidate can't edit) | digest-pinned `eval/` + `candidate_touches_protected` | `E7`, `G3` |
| 12 | Goodhart guard (holdout non-inferiority) | `evaluation.run_eval` holdout gate | `E3`, `E4` |
| 13 | Promotion needs green audit + protected eval | `improve.run_improvement` | `E5`, `E2`, `E10` |
| 14 | Reversible change | `psf improve --rollback` | `E10` |
| 15 | Eval governance (custody) | provenance, separate approval, no-leak, rotation, retire, expiry, isolation | `G1`–`G8` |
| 16 | Classifier is advisory only | `supervisor.decide`; FINISH requires `verified` | `S1`, `S12` |
| 17 | Fail-closed on classifier error | `supervisor.supervise_step` | `S6` |
| 18 | Bounded interventions / no oscillation | `SupervisorState` caps + policy | `S4`, `S13` |
| 19 | Normalized permissions across harnesses | `adapters.common.command(permissions=…)` | `A5` |
| 20 | Harness capability manifest | `adapters.common.capabilities` | `A6` |
| 21 | Feedback privacy | counts/digests only, opt-in, revocable | `E8`, `E14` |
| 22 | Runtime errors fail closed, don't abort the run | `SubprocessRunner` catches missing-binary/timeout/OSError | `test` + code review H1 |
| 23 | Single-writer ledger | documented: SQLite append is not serialized (single-process by design; PostgreSQL planned) | reviewed/accepted (M3) |

## How they are *used* (not just present)

- **`psf audit`** runs `guardrails.suite` (H1–H6) and `adapters.suite` (A1–A8)
  every time, plus the benchmark and ledger checks.
- **`psf improve`** refuses to promote unless `psf audit` is green and the
  protected eval passes; rollback is one command.
- **Adapters** apply the normalized permission profile and advertise capabilities.
- **`AGENTS.md`** (and CLAUDE.md/Copilot/Cursor/Gemini) tell agents to run the loop
  and `psf audit` before finishing.

## Suites

| suite | command | count |
|---|---|---|
| self-improvement | `psf eval-self` | 27 (E1–E27) |
| eval governance | `psf eval-gov` | 8 (G1–G8) |
| supervisor/classifier | `psf eval-supervisor` | 16 (S1–S13, C1–C3) |
| harness adapters | `psf eval-adapters` | 8 (A1–A8) |
| guardrails | `psf eval-guardrails` | 6 (H1–H6) |
| process | `psf eval-suite` | stochastic |
| multi-repo | `psf eval-repos` | 20 repos |
| unit tests | `pytest` | 62 |
