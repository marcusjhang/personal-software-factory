# Logbook

Append-only record of what was actually done, newest last. One line per action
with its commit when committed. See `docs/DIARY.md` for the narrative and
reasoning; see `PLAN.md` / `docs/TECH-SPEC.md` for the intended design.

## 2026-09

- 09-18 — Repo renamed `agent-project-management` → `personal-software-factory`; history wiped to a clean root; plan + tech spec committed (`82e2a32`).
- 09-18 — Built M0 walking skeleton: canonical digest, hash-chained ledger, factory-as-code schema/compiler, closed-transition state machine with gates, mock + subprocess runners, foreman, worktree isolation, benchmark, CLI. `08b02d9`.
- 09-18 — Added `psf audit` (self health check) and governed improvement loop (`psf improve`: propose → offline eval → shadow → canary → human promote → rollback). Fixed a real bug the loop exposed: `max_attempts` was not persisted in the ledger. `2246612`.
- 09-18 — Added `psf metrics`; wired the audit as a promotion gate (health must be green to promote). `9431981`.
- 09-18 — Ran a research pass (Postgres locking, Kleppmann fencing, outbox, Temporal, Stripe idempotency, AWS jitter) to design M2.
- 09-18 — Wrote `LOGBOOK.md` and `docs/DIARY.md`; began M2 durability (leases/fencing, outbox, idempotency, retry classification).
- 09-18 — Implemented M2 durability from a research pass (Postgres locking, Kleppmann fencing, outbox, Temporal, Stripe, AWS jitter): atomic lease claim with monotonic epoch, fenced renew/release, transactional outbox, `UNKNOWN` reconciled-not-retried, idempotency same-key/different-bytes rejection, retry classification + full-jitter backoff. 8 durability tests. `a1abe0f`.
- 09-18 — Adopted **GitHub as the assumed host**; added `src/psf/github.py` (issue intake, push + draft-PR handoff) and `psf run --runner/--command/--github`.
- 09-18 — **Dogfooded a self-build**: ran the factory on this repository in a git worktree via the subprocess agent; produced branch `psf/W-7df7e359` with a real diff, 46 ledger events, chain verified, `DONE`. Demo worktree cleaned up after review.

