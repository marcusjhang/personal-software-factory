# Personal Software Factory — Plan

**Status:** finalised product plan (specification). No implementation is claimed.
**Companion:** [docs/TECH-SPEC.md](./docs/TECH-SPEC.md) defines the implementation contract.

---

## 1. One-sentence promise

**Open one repository, run `psf init` once, say what you want in plain language,
and receive a reviewable change that a foreman agent drove through a durable,
gated, independently-verified build process — using whatever coding model you
choose.**

## 2. Problem

Modern coding agents can edit code, but they do not run a reliable software
process. The failure modes are consistent and well documented:

- **Amnesia.** Decisions, constraints, and the reason for a change are lost
  between sessions and across agents.
- **Skipped verification.** The agent that wrote the code also declares it done.
- **Blind retries and phantom completion.** Failures are retried without
  classifying them; "the run completed" is mistaken for "the work is merged."
- **No authority boundary.** Prompt instructions ("never merge") are treated as
  guarantees when they are only suggestions.
- **No audit trail.** You cannot reconstruct what happened, what was approved,
  or which model/version produced which artifact.

The fix is not a better model. It is a **deterministic process shell** around the
model: durable state, enforced gates, independent verification, and a ledger.

## 3. Target user and jobs

**Primary:** a solo developer or small team (1–10) who already uses a coding
agent and wants it to run a disciplined loop on their own repository without
adopting a heavy platform.

**Jobs to be done:**

1. "Turn a sentence into a scoped, reviewable change."
2. "Never let work proceed past a gate I did not approve."
3. "Show me exactly what happened and why."
4. "Use my model / my subscription / my machine."
5. "Install it in five minutes and keep state in my repo."

## 4. Product model

### 4.1 Visible concepts (keep it small)

| Concept | Meaning |
|---|---|
| **Goal** | One sentence describing the desired outcome. |
| **Team** | The roles the foreman assigned for this goal (usually 1 executor + 1 verifier). |
| **Route** | The chosen path through the factory (direct vs. spec-first vs. research). |
| **Gates** | The points where a human must decide (spec approval, merge). |
| **Artifacts** | The spec, patch, verification evidence, review, and handoff. |
| **Budget** | Bounded time/tokens/attempts for the goal. |
| **Stop** | The conditions that halt work (budget, failure, policy, cancellation). |

### 4.2 The loop

```
INTAKE → TRIAGE → SPEC → SPEC_REVIEW → READY → BUILD → VERIFY → REVIEW → HANDOFF → DONE
                    ▲                            │        │         │
                    │                            │        │         │
                    └──────── retry (bounded) ◄──┴────────┴─────────┘
```

- **SPEC_REVIEW** requires a human approval bound to the exact spec digest.
- **VERIFY** is performed by an independent role/identity from **BUILD**.
- **HANDOFF** produces a diff or draft PR; a human merges. The factory never
  merges or deploys.

### 4.3 What the user experiences

1. `psf run "add CSV export to the metrics page"`
2. The foreman triages, asks at most a couple of high-value questions, and
   produces a compact **Team Card**: goal, spec summary, plan, gates, budget.
3. The user approves the spec (or requests changes).
4. The factory builds in an isolated workspace, verifies independently, and
   reviews.
5. The user receives a diff / draft PR plus evidence: spec, verification result,
   review notes, and the ledger of every transition.

## 5. Scope

### In scope for v1.0

- Repo-native factory-as-code (`factory/`), compile-checked.
- One durable local ledger (SQLite for the first milestones; PostgreSQL later).
- The full loop above with enforced gates and bounded retries.
- Model-agnostic runner protocol with a mock runner and one real adapter.
- Git workspace isolation (worktrees) and draft-PR handoff.
- Independent verification and a benchmark harness.
- One-command install and `psf init` in any repository.

### Out of scope (non-goals)

- Autonomous merge/deploy/production change.
- Multi-tenant SaaS, fleet scheduling, or a hosted control plane.
- A universal workflow language or plugin marketplace.
- Training or fine-tuning models.
- Replacing Git, GitHub, CI, or branch protection.
- Claiming unattended production readiness or ROI.

## 6. Factory-as-code

The factory is versioned configuration in the repository — the authored
authority. Full format in [docs/TECH-SPEC.md §4](./docs/TECH-SPEC.md).

```yaml
# factory/factory.yml
schemaVersion: psf/v1
name: default
runner: subprocess
runnerOptions:
  command: ["psf-agent", "--model", "claude"]   # bring your own harness
agents:
  triage:    { prompt: agents/triage.md }
  spec:      { prompt: agents/spec.md }
  implement: { prompt: agents/implement.md }
  verify:    { prompt: agents/verify.md }
  review:    { prompt: agents/review.md }
gates:
  spec_approval: true          # human approval required before build
limits:
  max_attempts: 2
  max_minutes: 45
```

The compiler rejects missing roles, dangling prompt files, unknown keys, and
non-conforming values. Configuration is not runtime state: run history lives in
the ledger.

## 7. Architecture (overview)

Three planes, one ledger.

```
        factory-as-code (Git)                 human (CLI / GitHub)
                │ compile()                          │ decisions
                ▼                                    ▼
   ┌──────────────────── CONTROL PLANE (deterministic) ────────────────────┐
   │ policy + DoR gates · scheduler · approvals · fenced leases            │
   │ effect ledger + outbox · reconciler · budgets · retry/cancel           │
   └──────┬────────────────────────────────────────────┬───────────────────┘
          │ signed context + capability grant           │ observed state
          ▼                                             ▼
   EXECUTION PLANE (disposable)                  Git / GitHub / CI (projection)
   foreman · triage · spec · implement · verify · review
   (isolated worktrees, no standing authority)
```

- **Control plane** is deterministic code, not an LLM. It is the only writer of
  lifecycle state.
- **Execution plane** is disposable workers that receive a bounded task and
  return typed artifacts. They cannot approve, merge, or write state directly.
- **Ledger** is append-only and hash-chained; projections are rebuildable.
- **External systems** (GitHub, CI) are observed and reconciled, never trusted
  as the canonical record.

## 8. Agent roles

| Role | Responsibility | Cannot |
|---|---|---|
| **Foreman** | Route a goal, coordinate roles, enforce budget, summarize. | Bypass gates; approve; merge. |
| **Triage** | Scope, classify risk, decide spec-first vs. direct, reject non-goals. | Write code. |
| **Spec** | Produce a typed spec + acceptance criteria. | Approve its own spec. |
| **Implement** | Make the change in an isolated workspace. | Verify or review its own work. |
| **Verify** | Reproduce and check the change against the frozen spec (independent identity). | Edit the change. |
| **Review** | Assess quality, risk, and fit; approve or return. | Edit the change. |

Separation of duties is a hard rule: the verifier identity differs from the
implementer identity, and neither can approve the spec or merge.

## 9. Human gates and authority

Authority is enforced by the controller and by the hosting system, never by
prompt text.

- **Spec approval** is bound to the canonical digest of the spec. Any material
  change invalidates it and returns work to SPEC.
- **Merge** is owned by the human and the repository's protections (branch
  rules, CODEOWNERS, required checks). "Handoff" is not "merged".
- **Destructive/irreversible actions** require explicit approval and a
  documented rollback or are refused.
- **Cancellation** stops new dispatch, revokes leases, and reaches a terminal
  state only after cleanup receipts exist.

## 10. Runners and compatibility (bring your own model)

The factory talks to models through a small runner protocol:

```jsonc
// task (stdin)
{ "role": "implement", "goal": "...", "context": {...}, "workspace": "/path", "attempt": 0, "feedback": [] }
// result (stdout)
{ "ok": true, "output": { "patch": "...", "summary": "..." }, "summary": "...", "usage": {...} }
```

Two runners ship first: `mock` (deterministic, for tests/benchmarks) and
`subprocess` (any command that speaks the protocol). Model choice, credentials,
and cost stay with the user.

## 11. Distribution

Anyone can download and run the factory:

- `uvx personal-software-factory` — zero-install.
- `pipx install personal-software-factory` — isolated install.
- `docker run -v "$PWD:/repo" ...` — containerized.
- `curl -fsSL .../install.sh | sh` — scripted install.

Repository layout after `psf init`:

```
factory/        factory-as-code (committed)
.psf/           local ledger + workspaces (gitignored)
```

## 12. Evaluation and benchmarks

"How do we know it works?" is answered at two levels.

**Orchestration correctness (internal suite):**

- State-space tests: every legal and illegal transition, guards, retry
  exhaustion, cancellation, and terminal reachability.
- Ledger tests: hash-chain integrity, replay equivalence, torn-tail detection.
- Security tests: prompt-injection in inputs, gate-bypass attempts, identity
  separation, and secret non-exposure.
- A benchmark harness comparing **factory (adaptive team + independent verify)**
  against **one strong agent + checker** at equal budget.

**Real-world quality (external harness):**

- Adapter to run a task suite (e.g., SWE-bench-style) with full-SHA starts,
  repeated trials, and a frozen evaluator.
- Reported with denominators and limits; scores are bounded evidence, not truth.

**Metrics:** accepted-change rate, escaped-defect severity, human review time,
total cost per accepted change, retries, interventions, and rollback success.

## 13. Roadmap

Each milestone is independently useful and gated by its acceptance criteria.

| Milestone | Deliverable | Acceptance criteria |
|---|---|---|
| **v0.1 Walking skeleton** | Factory-as-code + compiler, ledger, state machine, mock runner, `psf init/run/status/validate`. | Full loop runs end to end on the mock runner; illegal transitions and unbound approvals are refused; ledger chain verifies. |
| **v0.2 Real agent** | `subprocess` runner + one real adapter; git worktree isolation; draft-PR handoff. | A real goal produces a reviewable draft PR; verification runs independently. |
| **v0.3 Durability** | Leases/fencing, effect ledger + outbox, retries, cancellation, reconciliation. | Crash/duplicate/fence/fault tests pass; no blind retry of an ambiguous effect. |
| **v0.4 Evaluation** | Scorers, protected offline eval, benchmark harness + baseline comparison. | Factory beats one-agent+checker on the internal suite at equal budget, or the gap is documented. |
| **v0.5 Subfactories** | Maintenance (signal→fix) and deep-research factories; budgets/cleanup. | A signal produces a gated fix; a research run produces cited structured output. |
| **v1.0 Governed improvement** | Failure clustering → proposal → offline → shadow → bounded canary → **human** promote/rollback; PostgreSQL mutation foundation. | No protected-path bypass; auto-rollback drill passes; upgrade/rollback of the factory itself is tested. |

## 14. Success metrics

- Median time from goal to reviewable change.
- Share of changes that pass independent verification first time.
- Human interventions per accepted change (target: decreasing).
- Escaped defects per accepted change.
- Cost per accepted change and per model/harness.
- Install-to-first-change time for a new user (target: < 10 minutes).

## 15. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Agents are unreliable. | Verification is independent; retries bounded; handoff is human-gated. |
| Prompt instructions treated as policy. | Gates compiled and enforced in code; repo protections back merge. |
| State loss / corruption. | Append-only hash-chained ledger; replay; later PostgreSQL + outbox. |
| Ambiguous external effects. | Intent-before-effect, receipts, `UNKNOWN` quarantine, reconcile-never-blind-retry. |
| Benchmark overclaiming. | Frozen evaluators, full-SHA starts, denominators, published limits. |
| Scope creep into a platform. | Non-goals are explicit; local-first; one repo at a time. |

## 16. Open questions

1. Default handoff: draft PR vs. local diff for users without GitHub?
2. How much of the spec should the human edit vs. approve verbatim?
3. Cost/attempt budgeting defaults across different harnesses.
4. Whether the first real adapter targets Claude Code, Codex, or both.
5. When (if ever) to add a shared service beyond local, single-repo use.

## 17. Relationship to prior research

This plan is a focused productisation of earlier, broader "agent operating
system" research: keep the hard-won safety invariants (enforced gates,
independent verification, durable ledger, human-owned promotion) and drop the
enterprise control-plane weight for a downloadable, personal, repo-native tool.
Warp Factories are used as a UX and format reference, not as the control plane.
