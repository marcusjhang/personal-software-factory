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

---

## 2026-09-18 — M2 landed, and the factory built itself

**Built M2 from research, not vibes.** Leases carry a monotonic epoch used as a
fencing token; renew/release are epoch-conditional so a zombie worker cannot
write. Effects are recorded as an intent before sending, and a failure between
send and settle lands in `UNKNOWN`, which is reconciled by observing the target
— never blind-retried. Idempotency keys reject same-key/different-bytes. Retry
classes (transient/correctable/terminal/policy) drive capped exponential backoff
with full jitter. Eight tests pin the classic races.

**GitHub assumed.** We cut the host-agnostic abstraction. Intake is issues,
handoff is a draft PR, identity is `gh`/GitHub App. The adapter is written; it
only runs when the operator passes `--github`, because it is the one place PSF
performs an external write.

**Dogfood — it built itself.** We ran the factory on its own repository, in a
git worktree, with a subprocess agent: goal → triage → spec → approval → build →
independent verify → review → handoff. Result: work item `W-7df7e359`, branch
`psf/W-7df7e359` with a real diff, 46 ledger events, chain verified, `DONE`.
Then we removed the demo worktree.

**Discovery — dogfooding is still shallow.** The "agent" was a script that
writes a marker file. That proves the *process* (isolation, gates, ledger,
handoff) but not that the factory can implement a real feature unaided. Closing
that gap is exactly what the runner adapter is for: point `command` at a real
harness. Recorded as a goal revision: **the factory must eventually make a
non-trivial change to its own source through its own loop**, not just a marker.

**Next.** M3 (protected evaluation gate) and M4 (outcome metrics), then
packaging (`uvx`/`pipx`/Docker) so it is genuinely plug-and-play.

---

## 2026-09-18 — M3/M4, packaging, and the factory changed its own code

**Protected evaluation (M3).** A candidate must not be able to edit the thing
that judges it. We pinned `eval/` (task set, thresholds, manifest) by digest and
made promotion a **non-inferiority** gate: promote only when the lower
confidence bound on the delta is at least `-epsilon`, with a minimum sample and
complete telemetry. A test immediately caught a real bug — the eval was reading
the one-shot baseline column instead of the retry-budget run — which is exactly
the kind of mistake a protected eval exists to prevent.

**Outcomes (M4) + packaging.** `psf outcome` records accepted change, review
escape, cost, and human minutes; `psf metrics` aggregates them. `Dockerfile`,
`install.sh`, and `.dockerignore` make it installable; `uvx`/`pipx` work off the
`psf` console script.

**The deep self-build — done.** We pointed the runner at a real harness
(Claude Code, `claude -p` in `acceptEdits` mode) and asked the factory to change
its own source: add a `doctor` alias for the `audit` subcommand. The implement
agent produced a correct edit to `src/psf/cli.py`. Then the **independent
verifier blocked it** — the spec required an acceptance test and none was added.

**Discovery that mattered.** The verifier's block was right, and it exposed a
product bug: the implement agent was **never given the spec**, so it could not
possibly satisfy acceptance criteria it never saw. Fixed: the foreman now passes
the spec and acceptance criteria to implement. This is precisely the failure the
factory is meant to catch — and it caught it in its own code, while building
itself.

**Human gate.** The owner reviewed the diff, added the missing test, and adopted
the factory's edit. The work item stayed `BLOCKED`; nothing was auto-merged.

**Where we are.** Self-improving (human-gated): yes — propose, protected eval,
shadow, canary, human promote, rollback. Plug-and-play: yes — one command
installs it, `psf init` scaffolds a repo. Dogfooding: yes — it edits its own
source through its own loop.

**Remaining.** Make `improve`'s candidate space richer than one config field;
formalize a `psf self-build`; add a CI workflow; and keep the diary honest about
what is proven (local, small-sample) versus claimed.


