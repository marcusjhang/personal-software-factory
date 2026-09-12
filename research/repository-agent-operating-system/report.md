# ⚠️ SUPERSEDED LEGACY SYNTHESIS — NOT CURRENT DECISION EVIDENCE

> **NON-AUTHORITATIVE STATUS:** The entire document below is retained only as historical synthesis. Every categorical claim, confidence label, cutoff/date statement, and source-to-claim association in it is an **unreviewed legacy candidate association**, not verified truth, verified current behavior, or semantic support. Legacy `2026-09-13` metadata has no established UTC meaning. The controlling scope cutoff and evidence semantics are [`PLAN.md` §4](../../PLAN.md#4-evidence-and-method), [`evidence-cutoff.md`](evidence-cutoff.md), and the schema-3 graph in [`material-claims.json`](material-claims.json). A pre-implementation immutable re-fetch from one run plus human semantic review is required before any candidate edge can become decision evidence.

# Repository-native agent project-management operating system

## Decision

Build a **thin, deterministic control plane around untrusted planning and implementation agents**. Do not deploy a general autonomous agent with GitHub credentials. The minimum end-to-end architecture is:

1. **Webhook ingress:** a GitHub App verifies `X-Hub-Signature-256`, stores the raw delivery under `(installation_id, delivery_id)`, queues it, and returns promptly. GitHub recommends validation, asynchronous handling, and a response within 10 seconds; failed deliveries need explicit recovery ([webhook best practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks), [failed deliveries](https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries)).
2. **Durable control database:** PostgreSQL holds `inbox`, append-only `events`, `work_items`, `commands`, `leases`, `attempts`, `approvals`, `evidence`, `outbox`, effect receipts, and GitHub projections. A transactional controller is the only authority that accepts lifecycle transitions. It assigns monotonic aggregate versions and lease fencing tokens.
3. **GitHub reconciler:** Git contains desired schemas and policy. The reconciler inventories GitHub, plans a diff, applies bounded idempotent operations, reads back, and records drift. GitHub Project item state remains remote actual state. Project GraphQL calls address remote node IDs, and adding an item and changing its field are separate operations ([Projects API guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)).
4. **Read-only planner:** it proposes a revisioned specification, acceptance oracles, risk tier, dependency DAG, capability request, and rollback. It has no READY, policy, lease, merge, or deploy authority.
5. **Admission and bootstrap service:** it selects one dependency-satisfied `READY` item in a database transaction, issues a fenced lease, and returns a signed, content-addressed Run Context Bundle for an exact base SHA.
6. **Ephemeral implementation worker:** it receives a short-lived task-branch capability. It cannot approve, merge, deploy, edit governance, or change its own evaluator.
7. **Independent clean verifier:** under a separate identity, it checks out the exact candidate SHA in a clean environment, runs fixed checks, and emits a content-addressed evidence bundle.
8. **Publisher, reviewer, merger, and deployer:** separate principals open/update the PR, review the exact head, enable auto-merge or merge queue only after policy passes, and release an exact attested artifact. GitHub rulesets, CODEOWNERS, merge queue, and protected environments are last-mile enforcement, not the primary workflow ledger ([rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), [merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue), [environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)).
9. **Evidence and telemetry plane:** immutable object storage retains manifests, attestations, decisions, and compact audit evidence. OpenTelemetry carries correlation, not authorization ([OTel signals](https://opentelemetry.io/docs/concepts/signals/)).
10. **Improvement plane:** postmortems and telemetry can create eval cases and change proposals. A separate curator, evaluator, policy owner, and promoter control offline, shadow, canary, promotion, and rollback. The proposer cannot see or edit hidden outcomes, lower gates, approve itself, or promote its own change.

The authority model is explicit:

| Concern | Authority | Non-authoritative inputs/projections |
|---|---|---|
| Desired schema, workflow, risk and capability policy | Protected default-branch Git revision | Agent prose; issue text; generated summaries |
| Live workflow state, leases, approvals, commands and effects | Transactional controller ledger | Labels, assignees, Project Status, comments |
| Issue/PR/check/deployment facts | GitHub API observations identified by IDs and exact SHAs | Webhook arrival alone; cached node IDs |
| Product intent and exceptional risk acceptance | Named humans under revision-bound policy | Planner or implementer recommendation |
| Code correctness evidence | Independent verifier plus required human/domain review by tier | Self-authored tests; AI review alone |
| Merge/release actuation | Separate merge/deploy principals after deterministic policy | Author token; Project status |
| Improvement promotion | Independent evaluation, human approval, protected environment | The proposing agent or one benchmark score |

**Decision:** implement the architecture in stages, beginning read-only. Permit no automatic production changes initially. Consider auto-merge only for a closed, reversible R1 profile after local evidence. Keep R2/R3 human-gated and R4 human-led. The source set supports the component mechanisms and the safety boundary. It does **not** establish end-to-end unattended production readiness, safe universal thresholds, or a general productivity gain.

## Scope and versions

- **Objective:** a repository-native operating system for issue intake, planning, readiness, safe claim and bootstrap, implementation, verification, review, merge, cleanup, observability intake, and governed improvement.
- **Research cutoff:** **2026-09-13**, as requested in the outline. Many GitHub pages are living, versionless documentation. Before rollout, probe the target tenant, plan, live GraphQL schema, App permissions, ruleset and environment availability.
- **Evidence set:** all 10 JSON results passed the bundled validator with 20/20 required fields. Primary sources were preferred. Independent studies and incident reports were used to constrain safety and efficacy claims.
- **Boundary:** single-organization GitHub repositories and organization Project v2 are the assumed first target. The design is portable at its manifest/event layer, but the adapter details are GitHub-specific.
- **Method limit:** this is a design synthesis. No controller was deployed and no target-repository benchmark was run. Numeric rollout gates below are **proposed local decision thresholds**, not externally proven constants.

## Key findings

1. **“Status as code” must be split into desired and actual state.** Git can own issue forms, label definitions, Project field/status schema, transition policy, capabilities, and migrations. Project fields/items are organization- or user-scoped remote resources addressed through GraphQL. Current issue status cannot truthfully be reconstructed from a YAML file. Use `desired / last-applied / observed` reconciliation, explicit field ownership, and a separate transition ledger ([Projects API](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects), [OpenGitOps principles](https://github.com/open-gitops/documents/blob/main/PRINCIPLES.md)).
2. **READY is a signed decision over an exact revision, not a label.** GitHub forms can require fields, but they cannot prove semantic completeness and remain documented as public preview ([issue-form schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema)). READY must bind the spec, plan DAG, acceptance oracle, base SHA, risk, policy, capability profile, approvers, and expiry. Any material change invalidates it.
3. **A fresh agent needs a controller-issued bootstrap bundle.** `AGENTS.md`, Copilot instructions, and `CLAUDE.md` differ in precedence, loading, and size. They orient a model but do not enforce authority ([Codex `AGENTS.md`](https://developers.openai.com/codex/guides/agents-md), [Copilot instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot), [Claude memory](https://docs.anthropic.com/en/docs/claude-code/memory)). The bundle must state exact objective, state, hashes, lease, budgets, allowed actions, architecture, commands, and trust classes.
4. **GitHub visibility is not a concurrency primitive.** An assignee or Project field is mutable presentation state. GitHub Actions concurrency has arbitrary ordering and retains only one running and one pending member per group, so it is unsuitable for fair durable admission ([Actions concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)). Use a database claim, TTL, heartbeat, and fencing token checked at every effect boundary.
5. **Verification must be independent and SHA-bound.** A clean verifier must not reuse the author environment, credentials, or caches. Required results, approval, and evidence bind to the current PR head. Merge queue must test `merge_group` rather than rely only on the earlier PR head ([`merge_group` event](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group)).
6. **Auto-merge is an actuator, not a risk decision.** Only allowlisted, reversible R1 work may eventually qualify. R2 requires owner and CODEOWNER review; R3 requires specialists, two independent signatures outside native one-of environment-review semantics, and production approval; R4 remains proposal-only. Environment reviewer lists can contain up to six entries but only one approval is required ([deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
7. **Observability should create planned work, not autonomous fixes.** Normalize, redact, deduplicate, cluster, qualify, then create or reopen one issue per incident family. Keep paging separate from backlog creation. Telemetry and logs are untrusted evidence. Only a signed, bounded, recently drilled runbook may execute automatically.
8. **Self-improvement must not become self-governance.** Evaluation replay can be automated; ground truth, policy, hidden tests, permission changes, and promotion cannot. Use isolated offline evaluation, zero-authority shadow mode, limited canary, exact-digest promotion, rollback, and delayed outcome checks.
9. **Central reuse needs immutable distribution.** Ship thin local workflows and a signed central bundle. Consumers pin Actions/reusable workflows by full SHA and record a release/digest lock. The `tj-actions/changed-files` compromise shows why movable tags are not a trust boundary ([CISA alert](https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-tj-actionschanged-files-cve-2025-30066)).
10. **Production claims must await a staged pilot.** Studies show material limits: a scoped METR randomized trial found a 19% slowdown for experienced developers using early-2025 tools ([METR](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)); an AI review study surfaced only 42% of injected issues ([study](https://arxiv.org/abs/2411.11401)); ITBench reported low pass@1 diagnosis and mitigation in its setting ([ITBench](https://arxiv.org/abs/2502.05352)). These do not prove agents are always ineffective. They do rule out assuming safety or productivity from model capability alone.

## Detailed evidence

### 1. Issues, Projects, and the exact state contract

Issue forms belong under `.github/ISSUE_TEMPLATE` on the default branch. Their responses become ordinary Markdown, and preselected labels must already exist or may not be added ([issue-form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)). Use them as intake UX, not as the canonical typed record.

Project v2 is not repository-local. GraphQL supports discovery and mutations for projects, fields, items, options, values, and views, but callers must resolve node/field/option IDs. Multi-field changes are not a cross-resource transaction, and add/update are separate calls ([GraphQL schema](https://docs.github.com/public/fpt/schema.docs.graphql), [Projects guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)). Project webhooks remain a trigger rather than durable truth; schedule full inventory reconciliation as recovery ([Project webhook](https://docs.github.com/en/webhooks/webhook-events-and-payloads#projects_v2_item)).

Use the lifecycle:

`INBOX → TRIAGED → PLANNING ↔ CLARIFICATION_REQUIRED → READY_REVIEW → READY → LEASED → EXECUTING → PROPOSED → VERIFYING → REVIEW_REQUIRED → MERGE_READY → MERGED → RELEASE_READY → CANARY → DEPLOYED | ROLLED_BACK | HUMAN_INCIDENT → VERIFIED | LEARN → CLOSED`

Keep `BLOCKED`, `DEFERRED`, `REJECTED`, and `CANCELLED` explicit. Only the controller appends a transition. Each event should carry `event_id`, `event_type`, `schema_version`, source/subject, actor, correlation and causation IDs, GitHub delivery ID when relevant, aggregate version, spec hash, policy version, payload digest, and typed data. CloudEvents is a useful naming model, but do not claim wire conformance unless implemented ([CloudEvents 1.0.2](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md)).

Separate configuration reconciliation from item transitions:

- Git desired state defines stable logical keys, fields/options, legal transitions, and ownership mode.
- Controller events define current workflow state.
- GitHub is the observed collaboration projection.
- Unknown remote objects are preserved by default.
- Renames, removals, type changes, permission/ruleset weakening, or ambiguous mappings produce a plan and human gate.
- Manual edits to controller-owned status are authenticated transition requests. They are accepted only if legal; otherwise revert or quarantine with an audit trail.

### 2. Planning and READY

The planner starts read-only. It inspects a pinned base SHA and produces:

- problem and desired behavior;
- scope and explicit non-goals;
- product and technical owners;
- acceptance IDs with positive, negative, authorization, and regression oracles;
- interfaces, migrations, observability, rollout, and rollback;
- a typed acyclic task DAG with dependencies, expected paths/write sets, budgets, capability profile, and stop rules;
- risk floor and unresolved questions.

GitHub supports sub-issues and dependencies, but these are collaboration primitives, not proof that the plan is acyclic or executable ([sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues), [dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)). Validate the DAG and write/resource conflicts outside the model.

READY should bind:

`work_item_id + repository_id + base_sha + spec_hash + plan_dag_hash + acceptance_oracle_hash + risk_tier + policy_commit_sha + capability_profile + approvers + issued_at + expires_at`.

A new material spec, base incompatibility, dependency result, requested capability, relevant policy change, expired token, or removed approver role returns the item to PLANNING. Cosmetic changes are only those excluded by a reviewed canonicalization policy. For ambiguity, ask one bounded, owned question with evidence, options, trade-offs, and a deadline. A narrow disposable spike can answer an empirical question, but its code cannot silently become the production implementation.

Evidence supports caution rather than a universal checklist: no controlled study in the result set isolates PStack, Spec Kit, or a Definition of Ready as the cause of production improvement. A fresh-task benchmark and correctness audits also show that benchmark readiness and tests do not transfer cleanly to live repositories ([SWE-bench-Live](https://arxiv.org/abs/2505.23419), [SWE-bench correctness audit](https://arxiv.org/abs/2503.15223)).

### 3. Fresh-agent bootstrap bundle

On `POST /v1/claims/next`, the worker supplies identity, engine/version, supported capabilities, and an idempotency key. The controller refreshes stale observations, atomically chooses one eligible item, creates an attempt and fenced lease, and returns a signed **Run Context Bundle (RCB)** with four trust classes:

- **A — authoritative controller facts:** work and attempt IDs, state version, exact spec/plan/base/policy hashes, approval token, lease epoch/expiry, budgets, and allowed next actions.
- **B — reviewed repository facts:** protected-base `AGENTS.md`, architecture, interfaces, command catalog, ownership, and their hashes.
- **C — curated memory:** reviewed ADR/runbook/eval summaries with provenance, owner, confidence, TTL, supersession, and digest.
- **D — untrusted evidence:** issue bodies, comments, PR text, logs, repository code, external pages, and MCP resources, labeled `authority=data`.

A capability proxy, not the model, enforces paths, tools, network, secrets, and state transitions. This is required because prompt injection remains unsolved by instruction prompting ([AgentDojo](https://arxiv.org/abs/2406.13352), [OWASP prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).

The worker verifies signature, schema, digests, time, identity, and fence before tools run. It checks out the exact base SHA from a clean mirror and records the actual instruction chain, precedence, bytes, conflicts, and truncation. A structured start acknowledgement states the objective, spec hash, next action, expected files, command IDs, and blockers. A different clean worker must be able to continue from the ledger, RCB, and checkpoint without chat history. Failure of this handoff is a bootstrap failure.

### 4. Admission, leases, concurrency, and effects

Use `SELECT ... FOR UPDATE SKIP LOCKED` in the dispatch transaction for competing consumers ([PostgreSQL](https://www.postgresql.org/docs/current/sql-select.html)). Admission verifies exact READY revision, hard dependencies, risk, budgets, and resource/write conflicts. Rank by explicit priority plus aging and quota; never infer urgency from comment volume.

A lease is `(work_item, attempt, holder, expires_at, heartbeat_at, fencing_token, capability_profile)`. Heartbeat renewal must match holder, attempt, fence, and active status. On expiry, revoke credentials and increment the fence before requeue. Every state commit and external-effect gateway checks the current fence because expiry alone cannot stop a paused process from later writing ([fencing analysis](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)).

Each external operation gets a stable logical effect key. Persist intent before the call, store the receipt, and query remote state before retrying an ambiguous result. Durable engines can replay workflow decisions, but external activities are still at-least-once around lost acknowledgment ([Temporal error handling](https://docs.temporal.io/develop/python/best-practices/error-handling)).

Start with one implementation worker. Parallelize only read-only analysis or DAG nodes with disjoint declared resources and deterministic join criteria. Multi-agent coordination adds failure modes, so compare against a single-agent baseline ([MAST](https://arxiv.org/abs/2503.13657)). Cancellation is a saga: record the cancellation epoch, revoke credentials, fence the lease, signal the worker, wait a bounded grace period, destroy the sandbox, reconcile effects, and then mark cancellation complete.

### 5. Implementation, verification, review, merge, and cleanup

Use separated identities for controller, author, verifier, reviewer, merger, and deployer. The author gets one attempt branch such as `agent/<task-id>/<attempt-id>` and no default-branch, approval, merge, deployment, or policy rights.

After authoring, verification starts clean at the exact head SHA. It installs from a lockfile without author caches, verifies undeclared/untracked outputs, and runs the risk-specific set of formatting, lint, types, unit/integration/contract tests, secret and dependency scans, license/SBOM checks, and policy tests. A bug fix should show base-fail/candidate-pass evidence. GitHub-hosted jobs are fresh VMs; a persistent self-hosted job is not clean merely because it is a new job ([hosted runners](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners), [self-hosted runners](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners)).

`evidence.json` should include task/spec/attempt/PR, base/head/merge-group SHA, workflow/action/tool/image digests, commands, check-run IDs and URLs, test counts/results, regression proof, security and supply-chain results, changed paths/risk, artifact digests/attestation IDs, reviewer decisions, timestamps, and redactions. Artifact digest and attestation prove identity/provenance, not test adequacy or correctness ([artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations), [SLSA 1.2](https://slsa.dev/spec/v1.2/requirements)).

AI review is advisory during the pilot. It must not satisfy required approval. Its limitations are supported by industrial and controlled evidence ([BitsAI-CR](https://arxiv.org/abs/2501.15134), [professional review study](https://arxiv.org/abs/2411.11401)). Recompute the merge predicate on every push. Bind approval to `task_revision + head_sha + policy_version + evidence_digest + risk_tier`. Enable stale-review dismissal and most-recent-push review where appropriate ([protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)).

Run the required subset on merge queue `merge_group`. After merge, record the merged SHA, revoke tokens, remove registered worktrees, prune metadata, delete only owned and safe refs, minimize bot comments, and apply retention rules. Cleanup is its own retryable saga; it does not undo a successful merge ([Git worktree](https://git-scm.com/docs/git-worktree), [Git refs API](https://docs.github.com/en/rest/git/refs), [Actions artifacts API](https://docs.github.com/en/rest/actions/artifacts)).

### 6. Risk tiers and auto-merge

Use `effective_risk = max(ticket declaration, deterministic path/diff/dependency/capability detectors, runtime findings)`. An agent may raise risk but never lower the computed floor.

| Tier | Meaning | Required gate |
|---|---|---|
| R0 | Read-only analysis, no mutation | No execution approval; human controls consequential publication/priority |
| R1 | Closed, reversible, low-risk class | Human approves during pilot; later conditional auto-merge only after local promotion, independent checks, bounded diff, no protected paths/new suppliers, easy rollback, and continuing audits |
| R2 | Material behavior | Exact-spec product/technical approval, independent path-qualified CODEOWNER approval at exact head, staged release approval |
| R3 | Auth/IAM/crypto, sensitive data, destructive migration, CI/policy, infrastructure, package publishing, large blast radius | Specialist plan approval, two qualified independent signatures, exact-artifact production approval, canary and rollback plan |
| R4 | Ambiguous, irreversible, missing oracle/rollback, exception to core controls, or self-governance | Human-led; agent gathers evidence or drafts only |

Edits to workflows, CODEOWNERS, rulesets, governance, evaluator/hidden tests, deployment/IAM, lockfiles/new suppliers, migrations, public APIs, or rollback/telemetry controls raise the floor. Native CODEOWNERS only routes review until a branch or ruleset requires it ([CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)). Bind critical status checks to the expected verifier App where supported. Treat a skipped or neutral mandatory policy path as failure.

Do not build untrusted PR code with secrets or write tokens under `pull_request_target`; that pattern can enable repository compromise ([GitHub Security Lab](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)). Pin third-party Actions to a full commit SHA and minimize permissions. The 2025 `tj-actions` compromise is direct evidence that a popular moving tag can be changed maliciously ([CISA](https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-tj-actionschanged-files-cve-2025-30066)).

### 7. Observability intake

The intake layer should consume only allowlisted GitHub, CI, security, dependency, deployment, logs, metrics, and trace events. Verify and redact before model use. Normalize to a versioned envelope, then form a stable fingerprint from tenant/repo, signal class, service/component, environment, detector/rule ID, normalized error/failure signature, dependency/advisory or workflow/job. Exclude timestamps, trace IDs, and secrets.

Maintain cluster states such as `OBSERVED → QUALIFYING → SUPPRESSED | TRIAGE → INCIDENT and/or PROPOSED_ISSUE → PLANNING`. READY is never granted by observability. Use upstream SARIF/Alertmanager fingerprints as evidence, not universal incident identity. GitHub SARIF fingerprints help recognize logically identical scanner results, but analysis/category changes can still create duplicates ([SARIF support](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning)). Alertmanager provides grouping, inhibition, and silencing, but a silence is not proof of resolution ([Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)).

Policy can choose `DROP_WITH_AUDIT`, `HOLD`, `UPDATE_CLUSTER`, `CREATE_PRIVATE_SECURITY_CASE`, `CREATE_OR_REOPEN_PLANNED_ISSUE`, `PAGE`, or `REQUEST_RUNBOOK`. Secrets and embargoed security findings use a private queue. Page urgent user-visible symptoms; do not ticket every raw event ([Google SRE monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)). Close only on explicit fixed/resolved evidence plus cooldown and reconciliation. A signed, idempotent, bounded, recently drilled runbook may act under a separate short-lived operations identity; novelty, ambiguity, destructive scope, missing postconditions, or rollback failure routes to a human incident.

### 8. Governed self-improvement

Use the following one-way lifecycle:

`OBSERVED → TRIAGED → POSTMORTEM/CURATION → EVAL_REVIEW → EVAL_APPROVED → PROPOSED → OFFLINE_RUNNING → OFFLINE_PASSED → SHADOW_RUNNING → CANARY_PENDING_APPROVAL → CANARY_RUNNING → PROMOTED | ROLLED_BACK → CLOSED`.

Curators minimize and de-identify cases, record consent/licensing/provenance, deduplicate, time-split holdouts, and independently define oracles. The agent proposes one small change and a rollback handle. Offline evaluation uses a clean sandbox, deterministic invariants, repeated stochastic trials, private temporal holdouts, adversarial/metamorphic slices, cost/latency, and expert-calibrated grading. Shadow mode has zero-authority adapters. Canary limits cohort, traffic, time, actions, spend, and error-budget burn. Inconclusive evidence pauses; it never counts as a pass.

This separation is needed because benchmark leakage and weak tests can materially inflate scores. SWE-Bench+ reported large leakage/suspicious-pass effects in its studied benchmark ([SWE-Bench+](https://arxiv.org/abs/2410.06992)). Use multiple outcome dimensions rather than one composite target: task success, safety invariants, escaped defects, rollback, user/SLO effect, cost, reviewer/on-call load, grader/expert agreement, data provenance, shadow divergence, and delayed outcome. SPACE likewise warns against a single productivity metric ([SPACE](https://queue.acm.org/detail.cfm?id=3454124)).

All policy, permission, identity, secret, audit, ruleset, CODEOWNERS, evaluator, hidden-test, and Project-schema changes require independent human approval. The proposer cannot curate its own holdout, see hidden expected outputs, approve exceptions, edit evidence, or promote a release.

### 9. Repository and distribution layout

Recommended consumer layout:

```text
AGENTS.md
.github/
  ISSUE_TEMPLATE/{task,bug}.yml
  PULL_REQUEST_TEMPLATE.md
  CODEOWNERS
  copilot-instructions.md
  instructions/security.instructions.md
  workflows/{agent-policy,agent-intake,agent-verify,merge-queue,release,reconcile}.yml
.agent-os/
  config.yaml
  distribution.lock
  schemas/{config,work-item,event,spec,evidence,bootstrap}.schema.json
  workflow/{states,transitions,failure-classes}.yaml
  policy/{risk-tiers,capabilities,approval-bindings}.yaml
  policy/rego/
  project/{desired,mapping}.yaml
  migrations/
  context/catalog.yaml
  architecture/{components,interfaces,ownership}.yaml
  commands.yaml
  memory/index.yaml
  evals/{manifest.yaml,cases/,proposals/}
  runbooks/{webhook-replay,project-drift,stale-lease,token-revoke,queue-backlog,rollback,kill-switch,break-glass}.md
  VERSION
  CHANGELOG.md
docs/{adr/,agent-os/architecture.md,agent-os/threat-model.md,agent-os/approval-matrix.md,agent-os/rollout.md}
tests/agent-os/{contracts,fixtures,attacks,reconcile}/
```

Use a top-level `apiVersion: agent-os.dev/v1alpha1`, `kind: RepositoryAgentPolicy`, owners and schema version, then repository/project selectors, symbolic states, guarded transitions, risk tiers, capability profiles, reusable workflow refs, gates, reconciliation mode, and distribution compatibility. JSON Schema should reject unknown security-critical fields ([JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-core)). Remote node IDs and live item status do not belong in the portable manifest. A generated binding lock may cache observed IDs, but it is non-authoritative.

Central distribution should contain reusable workflows directly under `.github/workflows`, composite actions, schemas, migrations, CLI/controller adapters, policy, fixtures, compatibility matrix, changelog, SBOM, and provenance. Consumers keep thin callers and pin full SHAs/digests in `.agent-os/distribution.lock`. GitHub supports nested reusable workflows but permissions cannot be elevated through the chain; keep nesting shallow for auditability ([reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)). Templates are day-zero scaffolds, not an upgrade mechanism ([repository templates](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)).

## Conflicts and uncertainty

- **Git status-as-code versus remote state:** resolved by declaring Git authoritative only for desired schema/policy and keeping the controller ledger plus GitHub observations authoritative for operational facts. Any claim that a YAML file alone makes Project v2 declarative is false.
- **Human-editable Projects versus one writer:** preserve human authority through authenticated transition commands and field-specific `managed`, `adopt`, and `report` modes. Do not permit silent competing writes to managed lifecycle fields.
- **Webhook immediacy versus durability:** webhook events reduce latency, but can be duplicated, delayed, out of order, or missed. Use inbox dedupe, outbox, read-after-write, and scheduled inventory. Do not claim exactly-once delivery.
- **Natural-language instructions versus enforcement:** vendor instruction files help orientation, but their resolution differs and content can conflict or truncate. Enforce authorization outside the model.
- **Durable workflow versus exactly-once effects:** a workflow history can replay deterministically while external calls remain ambiguous or at-least-once. Effect receipts and reconciliation are mandatory.
- **AI review and benchmarks versus correctness:** studies support assistance but show misses, weak oracles, contamination, and variable productivity. AI review remains additive, and benchmark gains do not authorize production actions.
- **Environment reviewer count versus multi-party approval:** GitHub's native list is one-of, not all-of. R3 needs an external signed second approval or custom gate.
- **Automatic rollback versus irreversible state:** only automatically restore proven compatible immutable bundles or reversible flags. Migrations and external side effects need compensation and human control.
- **Central reuse versus supply-chain concentration:** centralization improves consistency but enlarges the trust surface. Use full-SHA/digest pins, narrow permissions, provenance, cohort upgrade PRs, and rollback.
- **Future cutoff and living documentation:** the requested date is 2026-09-13, while many official pages have no stable revision. Re-run tenant-specific schema, plan, permission, and limits tests before implementation.
- **Unknown outcomes:** no representative public denominator establishes Project drift/lost-event rates, approval fatigue, ruleset bypass, autonomous defect escapes, safe concurrency, or economic benefit for this exact system. The proposed lease times, retries, sample sizes, diff ceilings, alert windows, and performance gates require local calibration.

## Recommendation

Approve a **read-only then assistive pilot** of the thin controller. Use PostgreSQL inbox/event/outbox/lease/effect tables and a GitHub App. Do not begin with Temporal or a multi-agent framework. Adopt a durable workflow engine only if measured histories, retries, timers, or operator burden justify it.

Keep these non-negotiable invariants from day one:

- no work starts without exact revision-bound READY;
- no model output directly mutates canonical state;
- no assignee, label, Project field, or comment is a lock or approval;
- every active attempt has one fenced lease;
- every external effect has stable identity and reconciliation;
- implementation, verification, merge, deployment, and governance use separate principals;
- all approval/evidence is bound to exact spec, head/artifact, and policy versions;
- remote enforcement is inventoried and read back;
- untrusted content cannot expand capability;
- destructive drift, missing oracle, permission expansion, or inconclusive evidence fails closed;
- agents cannot approve or promote their own code, policy, evaluator, prompt, tool, or permissions.

Auto-merge should remain off until one R1 profile meets predeclared local gates. Never auto-merge governance, workflow, dependency-supplier, credential, auth, data migration, public API, infrastructure, or self-improvement changes.

## Implementation or next steps

### Stage 0 — observe and reconcile, proposed 2–4 weeks

Commit schemas, state machine, risk/capability policy, approval bindings, event/evidence contracts, threat model, and runbooks. Install a read-only GitHub App. Build signed webhook intake, event ledger, scheduled Project/ruleset inventory, dry-run diff, replay, and drift dashboard. Exercise duplicate, out-of-order, lost-event, rate-limit, and restore drills.

**Proposed exit evidence:** 14 consecutive days of reconciled inventory with no unexplained loss; duplicate replay is idempotent; restore/replay drill passes; zero remote writes. These are proposed pilot thresholds.

### Stage 1 — assistive planning and verification

Generate specs, acceptance traces, DAGs, risk recommendations, draft evidence checks, and drift plans. Humans approve and execute all changes. Test hostile issue/log content and deny every undeclared tool/permission request.

**Proposed exit evidence:** at least 30 representative tickets; all READY records trace criteria to owners/tests/rollback; no unauthorized capability succeeds; evidence usefulness reaches a predeclared human rubric, suggested starting target 80%; false-block and missed-risk rates are reported with denominators.

### Stage 2 — draft PRs for allowlisted R0/R1

Enable atomic claim, signed RCB, ephemeral worker, short-lived task-branch credentials, clean verifier, evidence bundle, and cleanup saga. The agent opens draft PRs. Humans still merge and deploy.

**Proposed exit evidence:** at least 50 accepted or closed attempts and 30 days; zero privilege escapes or accepted stale-fence writes; every candidate is reproducible from exact SHA; escaped-defect performance is no worse than a matched human baseline under a predeclared non-inferiority margin; review time, lead time, and total cost are measured.

### Stage 3 — conditional auto-merge for one R1 profile

Enable only one closed, reversible profile. Use expected-source checks, merge queue, exact-head invalidation, automatic low-risk canary rollback, and at least a 10% human audit sample.

**Proposed exit evidence:** at least 100 eligible changes and 60 days; all predicates evaluated at current head; rollback drills pass; no high-severity escape; SLO/error-budget guards remain within predeclared bounds. Any privilege escape, false approval, high-severity defect, evidence tampering, or rollback failure freezes expansion.

### Stage 4 — controlled expansion and fleet distribution

Expand one capability, risk class, repository cohort, or model/tool version at a time. Pin central releases by SHA/digest, open upgrade PRs, test N and N-1 compatibility, canary on 1–2 repositories, and switch reconcilers to report-only during rollback. Never graduate on volume alone.

### Metrics to instrument from the first run

Report numerator, denominator, risk/task mix, policy/model/bundle version, baseline, and observation window for:

- webhook ingest and reconciliation lag; duplicate, gap, drift, and read-back failures;
- READY first-pass, clarification loops, invalidations, and implementation starts without valid READY (target: zero);
- queue age, claim conflicts, lease expiries/steals, heartbeat lag, stale writes rejected, unknown effects, and cancellation quiescence;
- clean verification completeness, flake reruns, merge-group coverage, review edits/rejections, and stale-approval merges (target: zero);
- accepted/retained changes, escaped defects by severity, rollback/change-failure rate, user/SLO outcome, and recurrence;
- cleanup age, orphan workspaces/refs, evidence retention gaps, and drift age;
- human planning/review/on-call minutes, CI/model/token spend, latency, and cost per retained change;
- observability duplicate precision, missed-impact rate, pages per incident, issue churn, disclosure leakage (target: zero), and runbook abort/rollback;
- eval provenance, grader-to-blinded-expert agreement, leakage/contamination, shadow divergence, canary exposure, aborts, inconclusive results, and delayed regressions.

## Sources

### GitHub and platform contracts

- [GitHub issue forms syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [GitHub issue form schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema)
- [Using the API to manage Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
- [GitHub public GraphQL schema](https://docs.github.com/public/fpt/schema.docs.graphql)
- [Project webhook events](https://docs.github.com/en/webhooks/webhook-events-and-payloads#projects_v2_item)
- [Webhook best practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)
- [Actions concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
- [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Secure use of GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use)
- [Reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [Artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations)

### Standards and implementation patterns

- [OpenGitOps principles](https://github.com/open-gitops/documents/blob/main/PRINCIPLES.md)
- [CloudEvents 1.0.2](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md)
- [PostgreSQL `SELECT`](https://www.postgresql.org/docs/current/sql-select.html)
- [JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-core)
- [SLSA 1.2](https://slsa.dev/spec/v1.2/requirements)
- [NIST SSDF SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final)
- [OpenSSF Scorecard](https://github.com/ossf/scorecard)
- [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/)
- [Prometheus Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Google SRE monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)

### Independent and counterevidence

- [AgentDojo: prompt-injection attacks and defenses](https://arxiv.org/abs/2406.13352)
- [OWASP LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
- [METR experienced-developer randomized study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)
- [SWE-bench-Live](https://arxiv.org/abs/2505.23419)
- [SWE-bench correctness audit](https://arxiv.org/abs/2503.15223)
- [SWE-Bench+ leakage and weak-test analysis](https://arxiv.org/abs/2410.06992)
- [MAST multi-agent failure taxonomy](https://arxiv.org/abs/2503.13657)
- [ITBench](https://arxiv.org/abs/2502.05352)
- [GitHub Security Lab: preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/)
- [CISA: `tj-actions/changed-files` compromise](https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-tj-actionschanged-files-cve-2025-30066)
- [ARGUS GitHub Actions security study](https://www.usenix.org/conference/usenixsecurity23/presentation/muralee)
- [AI-assisted professional code-review study](https://arxiv.org/abs/2411.11401)
- [BitsAI-CR industrial code-review evidence](https://arxiv.org/abs/2501.15134)
- [Fencing tokens and distributed locks](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)
- [SPACE productivity framework](https://queue.acm.org/detail.cfm?id=3454124)
