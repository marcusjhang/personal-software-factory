# Diary

Running narrative: what we tried, what we learned, and how the goal changed.
Goals here are **not stagnant** — they are revised when discovery warrants it.
The north star is fixed: **a plug-and-play, self-improving software factory**.
Everything else (architecture, milestones, scope) is negotiable.

---

## 2026-09-18 — From plan to product

**Entry.** The repo started as a plan-only "repository agent operating system".
We wiped it and renamed it `personal-software-factory`. Decision: stop writing
more plan, start writing the smallest thing that actually runs the loop.

**Discovery.** The plan was enterprise-heavy (multi-tenant, canary rings, RLS).
That is not a product one person downloads. Goal revised: keep the *safety
invariants* (enforced gates, digest-bound approvals, independent verification,
durable ledger) and drop the control-plane weight. First useful thing: one
person, one repo, one command.

**Decision — M0 shape.** A deterministic controller that is the only writer of
lifecycle state, an append-only hash-chained ledger, factory-as-code, and a
foreman that delegates to specialist agents. Model-agnostic runner so the user
brings their own model.

**Discovery — the improvement loop caught a real bug.** When we first ran
`psf improve`, the candidate (`max_attempts 2→3`) had *no effect*: offline
40%→40%. Root cause: `max_attempts` was set on an in-memory object but never
persisted to the ledger, so every projection fold reset it to the default 2.
Fix: persist it in the `WorkCreated` event and restore it on fold. Lesson:
projections must be derivable from events alone — anything not in the ledger
does not exist. This is exactly the class of bug the factory is meant to catch
in other people's work; it caught ours.

**Decision — self-audit as a first-class mechanism.** `psf audit` became part of
the product, not a dev script. It checks the ledger chain, factory compile,
state-integrity, digest-bound approvals, and benchmark non-regression. It gates
promotion: a candidate cannot be promoted unless the audit is green.

**Decision — research before build.** M2 (durability) was designed from primary
sources (Postgres locking docs, Kleppmann on fencing tokens, transactional
outbox, Temporal retry/cancellation, Stripe idempotency). Key takeaways adopted:
DB-time leases with monotonic epochs; effect intent written in the same
transaction as state; `UNKNOWN` is a first-class outbox state and is reconciled
before any retry; cancellation is an intent and is terminal only at quiescence.

**Goal revision — assume GitHub.** Everyone using this factory has GitHub. So we
stop abstracting the host. Intake = GitHub issues; handoff = draft PR; CI =
GitHub checks; identity = GitHub App / `gh` auth. The host-agnostic adapter
layer is cut from v1. This simplifies M1 (real handoff) and the identity model.

**Discovery — dogfooding is the test.** The factory should change its own repo
through its own mechanism, not via hand-edits. Every milestone ends by running
the factory on this repository (in a git worktree) and reviewing the produced
diff/PR.

**Next.** M1 (GitHub draft-PR handoff), M2 (leases/fencing/outbox), then
M3 evaluation gates, M4 outcome metrics, and packaging so `uvx <pkg>` gives
anyone their own factory.
