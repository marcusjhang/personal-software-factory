# Personal Software Factory — Technical Specification

**Version:** psf/v1 (draft)
**Status:** specification. Describes the intended contract; nothing here is
claimed as implemented.
**Audience:** implementers of PSF and authors of factory definitions.

---

## 1. Overview and principles

PSF is a single-binary/single-package CLI plus a small deterministic controller.
It turns a goal into a reviewable change by running agents through a fixed,
gated lifecycle, recording every transition in an append-only ledger.

**Principles (normative):**

1. **Controller decides.** Only the controller writes lifecycle state. Agents
   return typed results; they never mutate state directly.
2. **Prompt is not authority.** Every gate is a compiled predicate evaluated by
   the controller.
3. **Digest binding.** Specs, approvals, artifacts, and events are bound by
   `sha256` content digests over canonical JSON.
4. **Separation of duties.** Implement and verify use distinct roles and
   distinct identities.
5. **Append-only history.** The ledger is hash-chained; projections are derived.
6. **Bounded work.** Every attempt is bounded by retries, time, and cost.
7. **Local-first.** No network egress except the user's configured runner and
   optional git/CI adapters.
8. **Fail closed.** Unknown keys, versions, or guard inputs are rejected.

## 2. Glossary

| Term | Definition |
|---|---|
| **Factory** | Versioned, repo-native config (`factory/factory.yml`) declaring roles, runner, gates, limits. |
| **Runner** | Adapter that executes one role and returns a typed result. |
| **Work item** | One goal's lifecycle record. |
| **Attempt** | One execution of a role for a work item. |
| **Spec** | Typed description of the intended change + acceptance criteria. |
| **Approval** | Human decision bound to a subject digest. |
| **Artifact** | Digest-addressed output (spec, patch, evidence, review). |
| **Ledger** | Append-only, hash-chained event store. |
| **Gate** | Compiled predicate that must hold for a transition. |

## 3. System architecture

```
┌───────────────────────────── CLI (psf) ─────────────────────────────┐
│ init · validate · run · status · log · bench · serve(opt)           │
└───────────────┬─────────────────────────────────────────────────────┘
                │
┌───────────────▼───────────── CONTROL PLANE ─────────────────────────┐
│ FactoryCompiler   Controller/Workflow   GateEvaluator               │
│ Scheduler         LeaseManager (v0.3)    EffectLedger (v0.3)        │
│ Reconciler (v0.3) RunnerRegistry         BudgetMeter                │
└──────┬──────────────────────┬───────────────────────┬───────────────┘
       │                      │                       │
┌──────▼───────┐      ┌───────▼────────┐      ┌───────▼──────────────┐
│ Ledger (SQLite)│     │ Execution plane│      │ Adapters             │
│ events        │      │ Foreman        │      │ git / worktree       │
│ projections   │      │ triage·spec·   │      │ GitHub (PR)          │
│ (append-only) │      │ implement·     │      │ CI (checks)          │
│               │      │ verify·review  │      │ runners (mock/subproc)│
└───────────────┘      └────────────────┘      └──────────────────────┘
```

**Process model (v0.x):** one local process; `psf run` executes the loop
synchronously, checkpointing to the ledger so an interrupted run resumes. A
daemon mode is a later milestone.

## 4. Factory format (`factory/factory.yml`)

### 4.1 Top-level schema

| Key | Type | Required | Meaning |
|---|---|---|---|
| `schemaVersion` | string | yes | Must equal `psf/v1`. |
| `name` | string | yes | Factory identity. |
| `description` | string | no | Human summary. |
| `runner` | enum | no | `mock` \| `subprocess`. Default `mock`. |
| `runnerOptions` | mapping | no | Runner-specific (e.g. `command`, `timeout`). |
| `agents` | mapping | yes | Role → agent spec. |
| `gates` | mapping | no | Gate policy (e.g. `spec_approval: true`). |
| `limits` | mapping | no | `max_attempts`, `max_minutes`, `max_cost`. |

Unknown top-level keys are rejected.

### 4.2 Agent spec

| Key | Type | Required | Meaning |
|---|---|---|---|
| `prompt` | path | yes* | Markdown prompt, relative to `factory/`. |
| `command` | string[] | no | Overrides runner command for this role. |
| `model` | string | no | Model id passed to the runner. |
| `description` | string | no | Human summary. |

*Required for `subprocess`; the `mock` runner ignores prompts.

Required roles: `triage`, `spec`, `implement`, `verify`, `review`.
The **foreman** is the controller's coordinator and is configured by the
controller, not declared as a worker agent (a factory MAY declare a `foreman`
prompt to shape coordination style).

### 4.3 Compile checks (must all pass)

1. `schemaVersion` supported; required keys present; no unknown keys.
2. Every required role present; no duplicate role keys.
3. Every `prompt` path resolves to an existing file.
4. `limits.max_attempts >= 1`; budgets non-negative.
5. Gate policy values are booleans.
6. Workflow is well-formed: exactly one initial state; every state reachable;
   no non-terminal sink; every gate predicate references known fields.

Compilation yields a `factory_digest` (canonical digest over the resolved
factory, including prompt file contents).

## 5. Work-item lifecycle

### 5.1 States

```
INTAKE TRIAGE SPEC SPEC_REVIEW READY BUILD VERIFY REVIEW HANDOFF DONE
side states: BLOCKED  CANCELLED  REJECTED
```

Terminal states: `DONE`, `CANCELLED`, `REJECTED`.

### 5.2 Transition table (closed)

| From | Allowed to |
|---|---|
| INTAKE | TRIAGE, CANCELLED |
| TRIAGE | SPEC, REJECTED, BLOCKED, CANCELLED |
| SPEC | SPEC_REVIEW, BLOCKED, CANCELLED |
| SPEC_REVIEW | READY, SPEC, BLOCKED, CANCELLED |
| READY | BUILD, BLOCKED, CANCELLED |
| BUILD | VERIFY, BLOCKED, CANCELLED |
| VERIFY | REVIEW, BUILD, BLOCKED, CANCELLED |
| REVIEW | HANDOFF, BUILD, BLOCKED, CANCELLED |
| HANDOFF | DONE, BLOCKED |
| BLOCKED | (the saved prior state only) |

No other pair is legal. `BLOCKED` records the state it came from and unblocking
must return exactly there; it never skips a gate.

### 5.3 Guards

| Target | Guard |
|---|---|
| READY | `spec_digest` set **and** an approval exists whose `subject_digest == spec_digest`. |
| BUILD (from VERIFY/REVIEW) | `attempts < limits.max_attempts`. |
| HANDOFF (from REVIEW) | review decision == `approve`. |
| DONE (from HANDOFF) | human marks handed off (v0.x: explicit owner action). |

A guard failure raises `GateError`; no event is written; state is unchanged.

## 6. Data model

### 6.1 SQLite (v0.1–v0.2)

```sql
CREATE TABLE events (
  seq       INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id  TEXT NOT NULL UNIQUE,
  ts        TEXT NOT NULL,          -- RFC3339 UTC
  type      TEXT NOT NULL,
  work_id   TEXT,
  actor     TEXT NOT NULL,
  payload   TEXT NOT NULL,          -- canonical JSON
  prev_hash TEXT NOT NULL,
  hash      TEXT NOT NULL           -- sha256(prev_hash || canonical(body))
);

CREATE TABLE work_items (            -- projection, rebuildable from events
  id            TEXT PRIMARY KEY,
  goal          TEXT NOT NULL,
  state         TEXT NOT NULL,
  spec_digest   TEXT,
  approval_digest TEXT,
  artifact_digest TEXT,
  attempts      INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);

CREATE TABLE attempts (              -- v0.3
  attempt_id TEXT PRIMARY KEY,
  work_id    TEXT NOT NULL,
  role       TEXT NOT NULL,
  attempt    INTEGER NOT NULL,
  status     TEXT NOT NULL,
  runner     TEXT,
  model      TEXT,
  started_at TEXT, finished_at TEXT,
  usage      TEXT
);

CREATE TABLE leases (                -- v0.3
  lease_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, attempt_id TEXT,
  owner TEXT NOT NULL, fence INTEGER NOT NULL, issued_at TEXT, expires_at TEXT,
  heartbeat_at TEXT, revoked INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE effects (               -- v0.3
  effect_id TEXT PRIMARY KEY, work_id TEXT, kind TEXT NOT NULL,
  idem_key TEXT NOT NULL UNIQUE, status TEXT NOT NULL, -- INTENT|CONFIRMED|UNKNOWN|COMPENSATED
  request_digest TEXT, receipt TEXT, created_at TEXT, settled_at TEXT
);
```

`work_items` and any other projection are **derived**; on load the controller
folds the event stream. If they disagree, the event stream wins and the
projection is rebuilt.

### 6.2 Event types

| Type | Payload |
|---|---|
| `WorkCreated` | `{goal}` |
| `SpecProduced` | `{spec, digest}` |
| `ApprovalRecorded` | `{subject_digest, approver}` |
| `StateChanged` | `{from, to, reason}` |
| `BuildCompleted` | `{artifact_digest, summary}` |
| `VerifyCompleted` | `{passed, findings[]}` |
| `ReviewCompleted` | `{decision, notes}` |
| `AttemptStarted` | `{attempt_id, role, runner, model}` (v0.3) |
| `AttemptFinished` | `{attempt_id, status, usage}` (v0.3) |
| `EffectIntent` / `EffectSettled` | effect lifecycle (v0.3) |
| `CancellationRequested` / `Compensated` | cancellation saga (v0.3) |
| `Reconciled` | `{observed, drift}` (v0.3) |

## 7. Ledger and canonicalization

- **Canonical JSON:** UTF-8, sorted keys, no insignificant whitespace, non-ASCII
  preserved. (A future RFC 8785 implementation may replace this; it must pass
  the same byte-stability tests.)
- **Digest:** `sha256:<hex>` over canonical bytes.
- **Hash chain:** `hash = sha256(prev_hash || canonical(event_body))` where
  `event_body` excludes `hash`. `prev_hash` of the first event is
  `sha256:genesis`.
- **Integrity:** `verify_chain()` recomputes every link and fails closed on the
  first mismatch. A torn tail (last record truncated) is quarantined; interior
  corruption blocks writes and allows read-only export.

## 8. Controller algorithm

```
run(goal):
  work = create(goal)                      # INTAKE
  work = transition(work, TRIAGE)

  triage = agent("triage").run(task)
  if triage.decision == reject: transition(work, REJECTED); return
  work = transition(work, SPEC)

  spec = agent("spec").run(task)
  work = record_spec(work, spec)           # -> SPEC_REVIEW (digest bound)
  if gates.spec_approval:
      approval = await_human_approval(work) # exact spec digest
      if not approval: return (WAITING)
      work = approve_spec(work, approval)   # -> READY (guard checked)

  work = transition(work, BUILD)
  while True:
      build = agent("implement").run(task, attempt=work.attempts)
      work = record_build(work, build.artifact_digest)     # -> VERIFY
      verify = agent("verify").run(task, spec=work.spec)   # independent identity
      work = record_verification(work, verify.passed, verify.findings)
      if work.state == REVIEW: break                       # passed
      if work.state != BUILD: return                       # budget exhausted/blocked

  review = agent("review").run(task, artifacts=...)
  work = record_review(work, review.decision)              # -> HANDOFF or BUILD
  if work.state == HANDOFF:
      handoff(work)                                        # diff / draft PR
```

Notes:

- `await_human_approval` never fabricates a decision; no approval means the run
  is left in `SPEC_REVIEW` (a durable wait).
- Every agent call is wrapped by the budget meter and, in v0.3, by a lease.
- Failure classes: `transient` (retry with backoff, same effect key),
  `correctable` (feed findings back to implement), `terminal` (block/cancel),
  `policy` (never auto-retry).

## 9. Runner protocol

### 9.1 Task (stdin)

```jsonc
{
  "role": "implement",
  "goal": "add CSV export to the metrics page",
  "context": { "spec": {...}, "artifacts": [...], "command": ["..."] },
  "workspace": "/repo/.psf/work/W-ab12cd34",
  "attempt": 0,
  "feedback": ["verification: column order mismatch"]
}
```

### 9.2 Result (stdout, last JSON line)

```jsonc
{
  "ok": true,
  "output": { "artifact_digest": "sha256:...", "patch": "...", "summary": "..." },
  "summary": "implemented CSV export",
  "usage": { "tokens": 12000, "cost_usd": 0.18, "seconds": 240 }
}
```

Non-zero exit or unparseable output is a `transient`/`terminal` failure as
classified by the controller. `usage` feeds the budget meter.

### 9.3 Built-in runners

- **mock** — deterministic, offline. Used by tests and the internal benchmark.
- **subprocess** — runs `command` with the task on stdin. This is the
  bring-your-own-harness hook.

A runner MUST NOT require network unless the user configures it, and MUST NOT
merge, push, or mutate the lifecycle.

## 10. Workspace isolation

- Default: a throwaway temp directory (safe for machines with no repo).
- With a git repo: `git worktree add -b psf/<work-id> .psf/worktrees/<work-id> <base>`
  so parallel work never collides.
- The implementer's writes are contained to the workspace. Handoff converts the
  workspace diff into a patch or draft PR.
- Cleanup removes the worktree and branch after handoff (or on cancellation),
  gated by a cleanup receipt.

## 11. Adapters

| Adapter | v | Responsibility |
|---|---|---|
| Git/worktree | v0.2 | isolation, diff, branch, cleanup |
| GitHub | v0.2 | draft PR creation, issue intake, check reads |
| CI | v0.3 | run checks, read results, required-check identity |
| Reconciler | v0.3 | compare desired vs observed remote state; preserve unknown objects |

Adapters are read/write-safe: writes are effects with idempotency keys and
receipts; reads are observations with provenance, never authorization.

## 12. CLI specification

| Command | Purpose | Exit codes |
|---|---|---|
| `psf init [--force]` | Scaffold `factory/` and `.psf/`. | 0 ok, 2 exists |
| `psf validate [path]` | Compile-check the factory. | 0 valid, 1 invalid |
| `psf run "<goal>" [--yes] [--mock]` | Run one goal through the factory. | 0 done, 3 waiting-approval, 4 failed, 5 policy |
| `psf status [work-id]` | Show work items and current state. | 0 |
| `psf log [work-id] [--json]` | Print the ledger (hash-verified). | 0 |
| `psf approve <work-id> [--digest D]` | Record a spec/merge approval. | 0, 3 mismatch |
| `psf cancel <work-id>` | Request cancellation. | 0 |
| `psf bench [suite]` | Run the internal benchmark harness. | 0 pass, 1 regression |

Global: `--repo PATH`, `--json`, `--verbose`, `--no-color`. All commands derive
identity from the local user and never trust an in-payload actor id.

**`psf status` output (example):**

```
W-ab12cd34  REVIEW    add CSV export to the metrics page   attempts 2/2
             spec sha256:9f2c…  verify pass  review pending
```

## 13. Configuration and precedence

1. Built-in defaults.
2. `factory/factory.yml` (committed, reviewed).
3. `.psf/config.local.yml` (gitignored, machine-specific: runner command, paths).
4. CLI flags (one invocation only).

Lower layers may tighten limits; they may not disable mandatory gates
(`spec_approval`, independent verification) or weaken security.

## 14. Failure, retry, cancellation, reconciliation

- **Retry:** bounded by `max_attempts`, exponential backoff + jitter, same
  idempotency key for effects. Policy/budget failures never auto-retry.
- **Cancellation:** stop new dispatch → revoke leases → attempt compensation →
  require cleanup receipts → `CANCELLED`. Irreversible effects escalate to a
  human rather than claiming rollback.
- **Unknown effects:** if an external call's result is unknown, quarantine and
  observe before any retry. Never blindly replay.
- **Reconciliation:** compare canonical state to observed remote state; classify
  drift; apply only allowlisted changes; preserve unknown objects; fail closed on
  destructive or ambiguous drift.

## 15. Security and trust boundaries

| Boundary | Treatment |
|---|---|
| Goal text, repo code, issue bodies, logs, model output | Untrusted data. May contain prompt injection. |
| Agent → controller | Typed result only; never authorization. |
| Controller → workspace | Bounded capability; no standing credentials. |
| Controller → external write | Effect with idempotency + receipt; least privilege. |
| Human approval | Bound to exact subject digest; rechecked at use; expiry/revocation. |

Requirements: no secrets in logs; least-privilege tokens; worktree containment;
path-traversal/symlink defenses in artifact handling; identity separation for
implement vs. verify; refuse to promote without a matching approval.

## 16. Observability and metrics

Every run emits structured records and derives:

- attempts per success, retry exhaustion, time-to-handoff;
- verification pass-after-repair, review escape, rollback recovery;
- human interventions, review minutes, questions per item;
- cost per accepted change, tokens, seconds.

`psf status`/`psf log --json` expose these without leaking secrets.

## 17. Testing and benchmark harness

**Unit/contract:** schema validation, digest stability, ledger chain, state
machine (all legal/illegal edges), guard failures, retry exhaustion, cancellation.

**Property/model:** generate the transition graph from the table; assert
reachability, no non-terminal sink, and that no legal path builds without a
current approval.

**Fault/security:** crash before/after each step; duplicate/out-of-order input;
torn ledger tail; prompt-injection fixtures; gate-bypass attempts; identity
separation; secret non-exposure.

**Benchmark harness:** a suite of tasks each with a goal, a start SHA, and a
checker. Run:
- **Baseline:** one strong agent + checker (no gates).
- **Factory:** full loop with independent verification.

Report pass rate, cost, retries, and interventions at equal budget. External
adapters (SWE-bench-style) plug in behind the same interface, with frozen
evaluators and full-SHA starts.

## 18. Packaging and distribution

- Pure-Python package, no compiled deps beyond PyYAML; `psf` console script.
- `uvx` / `pipx` / `pip` installs; a Docker image; a `curl | sh` installer.
- State and factory live in the user's repo; nothing is sent to a server.
- Optional: a single-file build (zipapp) for fully offline use.

## 19. Versioning and compatibility

- `psf/v1` is the factory schema version; the compiler refuses unknown versions.
- The event envelope carries `schema_version`; readers preserve unknown fields
  (forward compatibility) but writers validate strictly.
- Factory upgrades are PRs with a change summary and a rollback pin.

## 20. PostgreSQL migration path

When durability beyond a single machine is needed (v1.0), the store moves to
PostgreSQL: restricted non-owner roles, append-only event/audit tables,
database-time leases, compare-and-append CAS, and a transactional outbox. Before
any external write token is enabled, a two-session admission/renew/reclaim race
must prove a single winner with stale-fence rejection. SQLite is retired from
the writer path at that point.

## 21. Non-goals (technical)

- No autonomous merge/deploy; no self-approval; no writing protected config.
- No multi-tenant isolation in v1.0 local mode.
- No universal workflow language or dynamic plugin execution.
- No exactly-once claim for external effects without provider support.
