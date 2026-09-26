# Handoff and continuity

What travels with a repo, what doesn't, and how to resume or hand off in-flight work.

## What lives where

| artifact | location | tracked in git? | meaning |
|---|---|---|---|
| factory definition | `factory/`, `psf.lock.json` | **yes** | the process: prompts, gates, pinned template revision |
| ledger + work items | `.psf/factory.db` | no (`.psf/` is gitignored) | the *history*: every event, work item, verification |
| durability state | `.psf/durability.db` | no | leases, outbox, idempotency keys |
| isolated workspaces | `.psf/worktrees/<work-id>` | no | per-item git worktrees |
| handoff branches | `psf/<work-id>` | **yes** (pushed on `--github`) | the actual change, as a branch/draft PR |

So a fresh clone gets the **process** but not the **run history**. That is deliberate:
the ledger is local state, like a database, not source.

## Handing off in-flight work

A work item is only "in flight" in its *ledger* and its *workspace/branch*. To hand
one off:

1. **Land the change as code.** Use `psf run --git --github` so the work item becomes a
   draft PR on branch `psf/<work-id>`. That branch is the durable artifact a teammate
   can pick up — it needs no ledger.
2. **Share the ledger only if resume-in-place matters.** If the next agent must
   continue the *exact* work item, ship `.psf/factory.db` out-of-band (it is not in
   git). Otherwise the taking-over agent starts a fresh ledger and re-runs the goal —
   the process is identical, the history is just new.
3. **Never rely on `.psf/` across clones.** `git worktree` metadata and leases are
   machine-local; a clone that is missing `.psf/` is a clean start, not a corrupt one.

## Inspecting state

```bash
psf status                      # work items and their states
psf status <work-id> --json     # one item, with spec/verification/review
psf log <work-id>               # the event ledger for that item
psf metrics                     # outcome signals
```

## Why not ship `.psf/` by default

The ledger is append-only and single-writer. Shipping it in git would invite merge
conflicts on a hash-chained file and leak local runs into shared history. The
reproducible, reviewable unit is the **diff** (branch/PR); the ledger is the local
audit trail that produced it.
