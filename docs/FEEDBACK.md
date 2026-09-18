# Consumer Feedback Loop

How usage of this factory on **other projects** flows back to improve this repo.

## The loop

```
  CONSUMER REPO (any project using psf)              MAIN REPO (personal-software-factory)
  ┌───────────────────────────────┐                 ┌────────────────────────────────────┐
  │ psf run / psf outcome         │                 │ psf feedback ingest <issue/export>  │
  │      │                        │                 │      │                             │
  │      ▼                        │                 │      ▼                             │
  │ .psf/factory.db (ledger)      │                 │ .psf/feedback/inbox/*.json         │
  │      │                        │                 │      │                             │
  │      ▼                        │   issue         │      ▼                             │
  │ psf feedback export ──────────┼───────────────▶ │ psf feedback report                │
  │   (counts + digests only)     │  (GitHub,       │      │  suggestions                │
  │   --github <main-repo>        │   labelled      │      ▼                             │
  └───────────────────────────────┘   factory-      │ psf improve  ──▶ protected eval    │
                                      feedback)     │      │           shadow/canary    │
                                                    │      ▼                             │
                                                    │ human promote ──▶ new release      │
                                                    └────────────────────────────────────┘
                                                                  │
                                     consumer upgrades pinned release ◀┘
```

## What an envelope contains (and does not)

An envelope is **counts, digests, and versions** — never your content:

```json
{
  "schema": "psf.feedback/v1",
  "envelope_id": "FB-1a2b3c4d",
  "psf_version": "0.1.0",
  "factory_digest": "sha256:...",
  "eval_manifest_digest": "sha256:...",
  "repo": "you/your-project",
  "metrics": { "work_items": 42, "states": {"DONE": 39, "BLOCKED": 3},
               "attempts": 61, "retries": 19, "blocked": 3,
               "outcomes": {"accepted": 39, "review_escape": 1,
                            "cost_usd": 7.4, "human_minutes": 55} },
  "failures": { "verify_failures": 12 },
  "note": "counts, digests, and versions only; no source, prompts, or secrets"
}
```

**Never included:** goal text, file contents, file paths, prompts, diffs, secrets,
tokens, customer data. Export is explicit; nothing is sent automatically.

## Commands

In a consuming repo:

```bash
psf feedback export                       # writes .psf/feedback/FB-xxxx.json
psf feedback export --github you/personal-software-factory   # files an issue there
```

In the main repo:

```bash
gh issue list --label factory-feedback    # or: psf feedback ingest <file-or-dir>
psf feedback ingest ./incoming/           # collect envelopes into .psf/feedback/inbox
psf feedback report                       # aggregate + suggestions
psf improve                               # turn signals into a gated change
```

## How signals become improvements

- `report` aggregates blocked/retries/verify-failures/cost across consumers.
- Recurring **verify failures** are the best candidates to promote into
  **protected evaluation cases** (`eval/tasks.json`) — they are exactly the
  cases the factory is currently failing.
- Recurring **blocks/retries** feed `psf improve` (e.g. raise the retry budget),
  which still must pass the protected eval, the self-audit, and a human promote.
- Consumer envelopes are **evidence, not authority**: they cannot promote a
  change, edit the eval, or alter policy.

## Privacy and trust

- Opt-in at every step. `export` is local by default; `--github` publishes.
- `repo` is optional; omit it to stay anonymous.
- Envelopes are additive and signed by digest in the main repo's ledger
  (`FeedbackReceived`), so they are auditable but never authoritative.
