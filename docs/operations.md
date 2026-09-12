# Operations Guide

**Status:** Proposed operating model and runbooks. Targets are initial recommendations to validate in a pilot; they are not measured production SLOs.

## 1. Operating principles

1. PostgreSQL runtime state is canonical. Rebuild GitHub projections from events and authoritative GitHub reads; never rebuild leases or approvals from labels.
2. Reconciliation is continuous control: observe, normalize, diff, classify, plan, apply only permitted changes, read back, and record receipts.
3. Agents produce proposals and evidence. Deterministic policy and human exact-digest approvals authorize consequential actions.
4. Unknown effect outcomes stop blind retry. Destructive or permission drift stops automatic repair.
5. Revoke capabilities before cleanup, retry, requeue, rollback, or incident investigation.
6. Preserve evidence by digest, minimize raw sensitive content, and make retention/deletion explicit.

## 2. Reconciliation loops

### Event-driven loop

- Validate webhook signature and installation/repository allowlist.
- Insert `X-GitHub-Delivery` into a unique durable inbox record.
- Return 2xx quickly and process asynchronously, as GitHub recommends ([webhook best practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)).
- Normalize the event, then reread the affected GitHub resource. Webhook payload is a hint, not a complete current snapshot.
- Compare expected aggregate version/fingerprint. Append a canonical transition only if policy permits it.
- Project accepted canonical state back to managed GitHub fields with an effect key and read-after-write.

### Scheduled full loop

Run a complete paginated inventory on a configurable cadence. An initial pilot can use every 15 minutes for live work plus a daily deep inventory, then tune from observed API cost and drift time. Cover issues, project items/fields/options, pull requests, checks, reviews, merge queue state, branches, runs/artifacts, deployments, and controller-owned resources.

Webhooks can be missed and failed deliveries require explicit handling ([failed deliveries](https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries)). Full reconciliation repairs gaps. Observe current REST and GraphQL rate headers and paginate every connection ([REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api), [GraphQL rate limits](https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api)).

### Reconcile algorithm

1. Load exact protected desired Git revision and validate schema/semantic invariants.
2. Acquire repository/project-scoped controller lease.
3. Read all remote pages and runtime bindings; reject ambiguous logical-key matches.
4. Normalize away unstable ordering and opaque IDs where possible.
5. Calculate drift and emit a redacted dry-run plan with `desired_sha`, plan hash, before fingerprints, mutations, and risk class.
6. Apply allowed non-destructive mutations in dependency order and bounded serial batches.
7. Record intent/receipt for each mutation; on ambiguous timeout reread before retry.
8. Read back, calculate residual drift, publish metrics, and release the controller lease.

Project item add and value update require separate GraphQL calls, so operate them as a saga rather than one assumed transaction ([Projects API guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)).

## 3. Drift policy

| Class | Example | Default response |
|---|---|---|
| Projection lag | Project says `READY`, DB says `LEASED` | Reapply canonical managed field; read back |
| Legal human transition request | Owner moves a managed status | Validate as a command; append event or restore with explanation |
| Unmanaged human state | Notes/custom field outside managed set | Preserve; observe only |
| Safe additive schema drift | Missing managed label/field/option with unique key | Plan, apply from approved config, read back |
| Semantic/destructive drift | Field type change, populated option removal/rename, deletion | Freeze apply; snapshot; reviewed migration |
| Access/security drift | App permission, collaborator, visibility, ruleset/bypass change | Kill affected writer lane; incident and human review |
| Ambiguous binding | Duplicate names or missing stable mapping | Quarantine; do not guess |
| Unsupported API feature | Built-in automation/view cannot be fully managed | Report-only/manual assertion |

Never commit observed item statuses back to Git as desired configuration. Importing an intentional schema change requires a normal reviewed config PR.

## 4. Recovery model

- Events, approvals, effects, and artifact metadata are append-oriented and backed up with point-in-time recovery.
- Projections are rebuildable from the event journal plus current remote observations.
- Transactional inbox/outbox prevents accepting a webhook or state transition without a durable follow-up record.
- Restores start read-only. Compare restored event sequence, aggregate versions, active fences, and remote receipts before enabling dispatch.
- On suspected controller/key compromise: pause dispatch and reconcile writes; revoke installation/worker/deploy tokens; rotate keys; bump all affected cancellation/fencing epochs; snapshot effects; verify desired Git; then resume one low-risk lane.
- Schema upgrades use expand/migrate/contract, versioned events, replay tests, and canary controller versions. Do not destructively migrate the only ledger copy.

## 5. Cleanup and retention

Cleanup uses explicit ownership records and two phases: mark intended deletion, then verify preconditions and delete by resource ID. It covers expired credentials, sandboxes, worktrees, branches, processes, caches, temporary artifacts, webhook dead letters, stale readiness approvals, and orphan Project bindings.

Recommended cadence for a pilot:

- heartbeat/lease sweeper several times within one lease TTL;
- expired credential/sandbox scan daily;
- orphan worktree/branch/artifact review weekly;
- dead-letter and unknown-effect queue continuously with named ownership;
- App permission, egress, MCP/tool, environment reviewer, and ruleset bypass inventory monthly;
- restore, signing-key rotation, webhook loss, stale-worker, prompt-injection, and rollback exercises quarterly.

Remove registered worktrees with Git-aware commands and then prune metadata; direct directory deletion is incomplete ([git-worktree](https://git-scm.com/docs/git-worktree)). Keep compact event/approval/effect/evidence manifests for the policy period. Store large logs and patches in immutable artifact storage by digest and delete them on a shorter data-class TTL. Never retain secrets or full prompts merely because storage is available. Legal hold is an audited human decision.

GitHub audit logs are supporting evidence, not the lifecycle ledger. Export required audit evidence before provider retention expires ([GitHub organization audit log](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/managing-the-audit-log-for-your-organization)).

## 6. Metrics and alerts

### Queue and planning

- count and age by lifecycle/sub-lifecycle/risk/repository;
- intake dedupe ratio and private-routing failures;
- planning time, clarification rate/age/rounds, DoR failure reasons;
- readiness approval latency, invalidations, expired approvals, `READY` without valid token (must remain zero);
- dependency-block age and cycle detections.

### Admission and execution

- eligible queue age, claim latency, worker utilization, no-work ratio;
- active leases, heartbeat lag, expiry/reclaim count, fence regressions and stale-write rejects;
- retry by failure class, dead letters, cancellation-to-quiescence;
- tokens/cost/time/diff size and budget stops;
- side effects by confirmed/unknown/compensated and reconciliation age.

### Delivery and outcome

- clean verification duration/pass rate/infrastructure retries;
- head/evidence invalidations, human review latency, change-request loops;
- merge-queue wait/failure/rebase churn;
- cleanup age/orphans;
- deploy success/rollback/time-to-healthy and observation-window outcomes;
- escaped defect/security finding/change failure rate with local denominators.

### Control and security

- webhook lag, signature failures, duplicates, unknown actions and detected gaps;
- inbox/outbox backlog, reconciliation duration/API cost/throttles, residual drift by class/age;
- permission/ruleset/bypass/secret/egress changes;
- policy denials, prompt-injection suspicions, secret findings;
- audit sequence gaps, backup age/restore verification;
- self-improvement offline/shadow/canary deltas, regressions, rollback count, and human overrides.

Trace claim, context, tools, GitHub calls, checks, deploy, and observation under `work_item_id/attempt_id/fence` using standard trace context ([OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/), [W3C Trace Context](https://www.w3.org/TR/trace-context/)).

Page immediately on an accepted stale write, unauthorized effect, fence regression, audit gap, secret exposure, compromised identity, kill-switch failure, destructive/access drift, unknown production effect, or rollback failure. Freeze only the smallest safe lane, unless compromise scope is unknown.

## 7. Core runbooks

### Stale lease or zombie worker

1. Pause the work item/resource set; increase cancellation epoch and fence in one transaction.
2. Revoke brokered token and close effect gateways, then terminate sandbox.
3. Inventory branch/PR/comments/artifacts/external effects by attempt and effect key.
4. Quarantine late output. Reconcile unknown effects with remote reads.
5. Cleanup owned resources. Revalidate readiness/base/dependencies before a new attempt.
6. Page if any stale write was accepted.

### Unknown external effect

1. Stop retries for the logical effect key and block dependent transitions.
2. Capture request hash, timestamps, provider IDs/errors, expected revision, and candidate receipt.
3. Query the authoritative remote system using a read identity.
4. Mark confirmed absent/present, compensate under policy, or request a human choice.
5. Resume with the same key only after the outcome is resolved. Add a regression/chaos case.

### Webhook gap/backlog

1. Keep ingestion accepting signed deliveries if safe; scale consumers within API limits.
2. Detect missing sequence/time windows and obtain provider redeliveries where available.
3. Run repository-scoped authoritative full scans.
4. Dedupe, replay normalized events, rebuild projection, and compare counts/fingerprints.
5. Do not infer “no event” means “no change.”

### GitHub Project drift

1. Freeze destructive/schema writes; snapshot complete fields/options/items/access and desired revision.
2. Classify managed/unmanaged, additive/destructive/access, and ambiguity.
3. Apply only already-approved safe repair. For intentional/destructive change, open a config/migration PR with inventory.
4. Read back every mutation and calculate residual drift.
5. Unfreeze only after bindings are unique and policy checks pass.

### Permission denied

1. Do not broaden the App/token automatically.
2. Confirm installation, repository selection, token expiry, requested endpoint, and minimum documented permission.
3. If current approved permission should suffice, rotate/reissue and test read-only.
4. Any expansion is a protected policy/App change with security approval and exact scope.

### Prompt injection or secret exposure

1. Stop/fence the worker and revoke all possibly exposed credentials.
2. Preserve redacted input/output/tool/effect evidence; restrict access.
3. Search logs/artifacts/branches and provider access records; rotate secrets.
4. Assess external effects and data access; notify incident/security owners.
5. Fix capability/context boundary, add curated adversarial eval, and reapprove before enabling the lane.

### Merge queue failure

1. Confirm `merge_group` workflow ran for the current group SHA.
2. Distinguish candidate defect, interaction with another candidate, infrastructure failure, missing trigger, or stale approval.
3. Never reuse a check from another SHA. Reverify/review after new commits.
4. Fix or remove from queue under policy; record diagnosis evidence.

### Deployment guardrail breach / rollback

1. Freeze further rollout; record current and target artifact/environment.
2. Invoke the reviewed rollback mechanism or obtain incident commander approval.
3. Confirm provider receipt and deployed digest; observe health.
4. Move to `ROLLED_BACK`, revoke deploy capability, preserve evidence, and open incident/follow-up/eval candidate.
5. Reach `DONE` only after rollback health and cleanup are verified.

### Database restore/controller disaster

1. Stop dispatch and all mutation gateways. Restore to an isolated database.
2. Verify backups, journal sequence/hash, aggregate versions, approval digests, and maximum fences.
3. Reread GitHub/external systems and reconcile effects created after restore point.
4. Increase affected fences; revoke old capabilities. Rebuild projections.
5. Run dry plan and a low-risk canary; obtain controller owner approval before lane-by-lane resume.

### Kill switch

1. Persist scope/reason/actor and deny new claims/capabilities immediately.
2. Fence/revoke active attempts as policy requires; deployment lanes stop first for broad incidents.
3. Continue read-only observation and evidence preservation.
4. Restart only with named human authorization, incident resolution, exact controller/policy digest, and a canary.

## 8. Durable sub-lifecycle operations

Every work item has a durable sub-lifecycle rather than treating all agent work as one opaque run.

### IDEATION

`CAPTURED -> RESEARCHING -> SYNTHESIZING -> DECISION_REVIEW -> DECIDED`, with `NEEDS_INPUT`, `BLOCKED`, `CANCELLED`.

Conversation is stored as attributed revisions and evidence references, not hidden chat memory. Research queries, sources, snapshots, contradictions, confidence, and field-level citations are durable. A decision record names alternatives, criteria, trade-offs, open uncertainty, decision owner, and exact evidence/spec digest. New evidence creates a new revision; it does not rewrite history. `DECIDED` may generate a BUILD candidate only after normal DoR and readiness approval.

### BUILD

Uses the canonical planning-to-delivery states: `PLANNING`, `NEEDS_CLARIFICATION`, `READY_REVIEW`, `READY`, `LEASED`, `IMPLEMENTING`, `VERIFYING`, `REVIEW`, `MERGE_QUEUED`, `MERGED`, `DEPLOYING`, `OBSERVING`, `DONE`. It preserves spec, attempt, evidence, approval, artifact, deploy, and cleanup digests.

### MAINTENANCE

`SIGNAL_RECEIVED -> CORRELATED -> DIAGNOSED -> PROPOSED -> SCHEDULED -> EXECUTING -> VERIFIED -> OBSERVING -> RESOLVED`, with `SUPPRESSED`, `BLOCKED`, `CANCELLED`, `ROLLED_BACK`.

Signals from SLOs, security scanners, dependencies, CI, and user reports are authenticated, normalized, clustered, and deduplicated. Suppression has an owner/expiry. Diagnosis links exact telemetry/source revisions. Consequential remediation becomes a BUILD work item and passes the same gates. Only a tiny preapproved allowlist of reversible operations can execute directly; results still require effect receipts and verification. “Alert disappeared” is not proof of resolution.

Each sub-lifecycle emits standard envelopes into the same ledger and links parent/child work items. This allows ideation to produce several builds and a maintenance incident to produce research, rollback, and follow-up builds without losing causality.

## 9. Factory-as-code operations

A **workflow factory** is reviewed Git configuration that composes reusable, versioned modules. It is not an agent that invents authority. A factory instance pins:

- lifecycle template and schema versions;
- inputs/outputs and JSON Schema contracts;
- deterministic transition predicates;
- role/quorum and risk policy references;
- worker role, prompt/instruction digest, model class, tool/capability profile;
- sandbox image, command catalog, egress/secret class;
- retry, timeout, budget, lease, idempotency, compensation, cleanup, and retention policy;
- evaluation suite and promotion channel;
- GitHub projection mapping.

Composition is a typed DAG. Nodes exchange digest-addressed artifacts. Edges declare required output schemas and failure behavior. Parallel nodes must declare disjoint writes/resources; joins use deterministic predicates, not agent consensus. The compiler resolves pinned module versions, rejects cycles/conflicting capabilities/unbound outputs, computes a factory digest, and produces a reviewable execution plan. PostgreSQL stores each instance/run/node/attempt; GitHub shows a projection.

### Deep-research factory

A reusable deep-research workflow should compose:

1. scope/question revision and decision owner;
2. research object/item list and field/evidence schema;
3. query/source plan with source-class and time-range requirements;
4. parallel bounded researchers with read-only web/repository access;
5. per-item structured JSON output with direct sources, quotations/facts, dates, conflicts, uncertainty, and provenance;
6. schema/coverage/source-quality validation and deduplication;
7. adversarial gap/conflict review;
8. synthesis report generated only from validated records;
9. human decision review bound to outline, field schema, result-set manifest, and report digests;
10. archival/refresh schedule and downstream proposal generation.

Research content is untrusted data and cannot change tools or workflow policy. A source list is not itself a decision. Refresh creates a new result-set revision. Factory upgrades follow offline replay -> shadow -> canary -> human exact-digest promotion.

### Factory rollout and maximum safe automation

Start with dry compile and read-only shadow. Then run one sandbox repository and low-risk factory instance. Compare to a manual baseline, inject crashes/replays, and verify cleanup/rebuild. Canary exact factory digests by repository/risk cohort. Roll back to a known-good digest automatically on predefined guardrails.

Factories may automatically instantiate preapproved templates, perform deterministic validation, run read-only research, propose artifacts, reconcile managed projections, and execute already-approved low-risk nodes within fixed scopes. They may not generate or approve their own authority, widen permissions, change risk/gates/evals, or promote a factory digest. Those boundaries remain human controlled.

## 10. Self-improvement operations

Treat every improvement as another governed release. Store proposal, curated dataset/oracles, baseline and candidate digests, offline runs, shadow comparisons, canary cohort/results, human promotion, and rollback as linked events.

Use predeclared denominator-based gates. Include correctness, safety/policy violations, abstention, regression slices, reviewer effort, cost, latency, and incident rate. Curators add postmortem cases only after privacy and representativeness review; incidents never become automatic training data. Follow established evaluation guidance to define task-specific criteria and inspect traces, not only end scores ([OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices), [trace grading](https://developers.openai.com/api/docs/guides/trace-grading)). Canary design needs a baseline, staged cohorts, guardrails, and rollback ([Google SRE canarying](https://sre.google/workbook/canarying-releases/)).

Maximum safe self-improvement stops at proposing, evaluating in an already-approved harness, non-authoritative shadowing, bounded preapproved canary execution after human admission, and automatic rollback. Humans retain exact-digest promotion, permissions, risk policy, eval/oracle curation, thresholds, exceptions, and production authority.


## 11. Distribution, installation, upgrades, and dogfooding

### Installation contract

A consumer opts in through a reviewed installation PR and an organization-side App installation approval. The manifest pins:

- control product and artifact digest;
- controller/config/event schema compatibility range;
- domain pack and factory versions;
- effective policy layers and expected digest;
- required GitHub App permissions/repository selection;
- Project logical identifier and managed fields;
- risk/owner role bindings, environment names, retention/data region;
- rollout ring, telemetry sharing level, previous known-good pin.

The installer runs read-only preflight: schema/semantic compile, permission delta, repository/ruleset/CODEOWNERS/workflow conflict, GitHub API capabilities, Project inventory, migration needs, sandbox/eval compatibility, and a no-side-effect reconcile plan. Human repository/security owners approve before write enablement.

### Per-repository isolation

Use a repository/installation tenant key on every database row, idempotency key, queue, artifact, token, and trace. Apply database row-level/connection authorization or equivalent defense in depth. Mint App installation tokens only for the selected repository. Use separate ephemeral workspaces, cache trust partitions, quotas, encryption context, kill switches, and retention. Do not let a Project link or shared organization membership create cross-repository authority.

### Inheritance and overrides

Compile `product defaults -> organization policy -> repository policy -> approved instance parameters`. Schemas define merge semantics. Mandatory denies, separation of duties, audit fields, maximum capabilities, and minimum retention/security gates are non-overridable. Repository policy may tighten them. Emit the resolved provenance and digest in every run context/evidence record.

### Compatibility and migration

Release metadata declares supported controller, database/event, repository-config, factory, domain-pack, and adapter versions. CI tests upgrade and rollback across every supported adjacent version. Use expand/migrate/contract, dual readers where needed, resumable idempotent migration steps, backups, and dry-run inventory. Destructive Project/config migrations require explicit human approval. Deprecation has dates and an owned upgrade path; no silent forced migration.

### Upgrade PR and canary rings

A release service proposes, but does not merge, a consumer upgrade PR with exact old/new pins, changelog, resolved-config/permission delta, migration/dry-run plan, eval and compatibility results, canary ring, rollback pin, and expected observation window. Rings progress from this product repository's isolated self-test tenant and sandboxes, to opt-in low-risk repositories, to bounded cohorts, then broad availability. Human promotion is exact-digest and guardrails can roll back to the recorded prior pin. Measure each version separately.

### Privacy-filtered outcomes and eval contribution

Export only the consumer-approved outcome schema. Default fields are pseudonymous tenant/cohort, pinned component digests, task/risk/failure class, count denominators, latency/cost bands, check/policy verdicts, rollback and human-override indicators. Filter free text and identifiers locally. Never export source, diffs, prompts, issue/comment bodies, secrets, raw logs, user/customer data, or artifact contents by default.

A consumer may submit a redacted candidate evaluation case with provenance, license/consent, risk class, expected behavior, and expiry. Independent curators decide whether to accept and how to partition it. Contribution does not imply training consent and cannot alter current promotion results.

### Dogfooding runbook

1. Keep this repository pinned to the last promoted stable control-product digest in its own isolated consumer manifest/tenant.
2. Let that stable version plan and check candidate changes. Candidate code has no controller, merge, deploy, eval-curation, or promotion credential.
3. Run candidate offline and in a non-authoritative shadow against frozen cases, then sandbox canary with privacy-filtered results.
4. Human owners approve and publish the exact candidate release digest outside candidate authority.
5. Open a normal upgrade PR changing this repository's consumer pin. Run compatibility/migration dry-run and self-test canary.
6. Promote rings only after observation. On a guardrail breach, disable automation and restore the previous immutable pin.
7. Preserve bootstrap recovery: human operators can install/restore stable control code without relying on the broken candidate.
