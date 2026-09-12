# Round 1 resolution memo: state and orchestration

## Scope and disposition

This memo resolves the findings in `state-model.json` and `orchestration-reliability.json`. It is a correction to the implementation plan. It does **not** approve the prototype as production code and does not require edits to the disposable prototype in this PR.

I compared the reviews with the protected YAML/JSON artifacts, Python models and validators, SQL migrations and tests, operating documents, `report.md`, and the validated lifecycle/domain/core research results. I also reproduced the public factory-loader failure and the misleading green Python suite:

- `uv run pytest -q` passes all 22 tests.
- `load_factory('.agent-os/factories/build.yaml')` fails with 15 Pydantic errors.
- All four registered factories target undeclared `BLOCKED`; none declares an initial state or terminal set.
- `work_items` has neither `aggregate_version` nor a compare-and-append transition API. The schema has no durable factory instance/node run, cancellation epoch, or blocked continuation.

Disposition: **11 verified root causes; 0 rejected findings**. `ORCH-PLAN-001` is a duplicate of `STATE-001`. Other findings sometimes share a correction surface, but describe independently testable failures and are retained.

## Verified root causes and exact normative plan corrections

### RC-1 — lifecycle authority is fragmented

`report.md:63`, `docs/architecture.md`, `.agent-os/lifecycle.yaml`, Python `_ALLOWED`, and SQL do not express one vocabulary and graph. For example, YAML allows `MERGED -> OBSERVING|DONE` and `ROLLED_BACK -> DONE`, while Python rejects them; Python allows `TRIAGED -> BLOCKED`, while YAML rejects it.

- The plan **MUST** designate one protected, versioned lifecycle IR as the only source of state identifiers, legal edges, guards, entry/exit effects, and terminal predicates.
- Generated docs, application enums/tables, database constraints/procedures, projections, and tests **MUST** carry the lifecycle version and **MUST** be graph-equivalent to that IR.
- A domain factory **MUST NOT** claim its private phase names are canonical work-item states. It **MUST** define an explicit, versioned product mapping between factory state and the work-item aggregate.
- The selected graph **MUST** resolve no-deploy completion, post-rollback verification, and every `BLOCKED` return. Direct `MERGED -> DONE` **MUST NOT** bypass required outcome and cleanup predicates.

### RC-2 — the factory contract is neither executable nor durable

The JSON Schema admits free-text guards and unconstrained objects; transition endpoints are not bound to phases. The registered YAML and `FactoryDefinition` are incompatible. The database cannot persist a pinned factory instance, phase/node attempt, continuation, or parent-child causality. The documented ideation and maintenance names also differ from their YAML names.

- The plan **MUST** define one versioned factory IR with stable factory/node/edge IDs; explicit initial, terminal, exception, cancellation, compensation, cleanup, and resume nodes; typed input/output artifact schemas; deterministic guard IDs plus typed parameters; effect class and identity; authority/resource scope; lease/heartbeat bounds; retry classes/backoff/budget; and terminal predicates.
- Every edge endpoint **MUST** resolve. Every node **MUST** be reachable from the initial node or explicitly marked migration-only. Every nonterminal sink **MUST** fail validation.
- Retry, stale attempt, invalidation, block/unblock, cancellation, compensation, and cleanup **MUST** be machine-readable semantics, not prose.
- Completion **MUST** require receipts for all mandatory cleanup nodes. Compensation **MUST NOT** be described as undoing an already successful merge.
- Registry resolution **MUST** load the referenced contract with the public loader, validate its semantic graph, compute its canonical digest, and pin that digest to the instance.
- Ideation, build, maintenance, deep-research, and composition **MUST** use the same IR. The plan **MUST** select canonical private-state names or publish explicit migration/mapping tables.
- Composed children **MUST** be durable aggregates linked to a parent node and delegated budget/capability snapshot. Child authority **MUST** be the intersection of parent delegation and the named profile. Parent resume **MUST** wait for child terminal cleanup.

### RC-3 — block/unblock has no continuation contract

Neither `Ticket` nor `work_items` records the prior state. A caller can select one of several unrelated `BLOCKED` exits.

- Entering `BLOCKED` **MUST** atomically persist `blocked_from_state`, lifecycle/factory version, node/attempt/fence, reason code, required resolution, owner, bound input/policy/base/dependency digests, expiry, and continuation revision.
- Unblock **MUST** occur under aggregate lock/CAS. It **MUST** return only to the saved continuation when all bindings remain current.
- Expired or materially changed bindings **MUST** invalidate the continuation and route to a policy-defined re-plan/review state. A caller-selected target **MUST NOT** skip readiness, approval, lease, or verification gates.

### RC-4 — PostgreSQL does not enforce compare-and-append

The runtime role can directly update lifecycle state, and the row has no aggregate version or database-enforced coupling to its event. Cancellation can be written while attempts and leases remain live.

- The runtime aggregate **MUST** have a monotonic `aggregate_version`.
- Normal runtime roles **MUST NOT** receive direct lifecycle-column update authority.
- One least-privilege transaction API **MUST** accept expected aggregate/lifecycle version, transition ID, actor, idempotency key, bound evidence, and guard inputs; lock the aggregate; validate the generated edge and guards; append the immutable event/audit record; update the projection; and commit all or none.
- Repeated identical idempotency requests **MUST** return the prior result. Key reuse with different request bytes **MUST** fail closed.
- Cancellation and approval invalidation **MUST** use the same transition boundary and atomically advance the applicable epoch/fence or enqueue its mandatory saga work.

### RC-5 — cancellation conflates request with completed quiescence

The narrative describes a saga, but the graph makes `CANCELLED` immediately terminal.

- The plan **MUST** represent `CANCEL_REQUESTED` and `QUIESCING/CLEANING` states, or an orthogonal cancellation saga whose state is part of the aggregate terminal predicate.
- Cancellation request **MUST** atomically advance `cancellation_epoch`, prevent new capability issuance, revoke active capability handles, fence/release the active lease, and enqueue worker-stop, effect-reconciliation, and cleanup work.
- Terminal `CANCELLED` **MUST** require worker termination or an explicit unconfirmed-quiescence escalation disposition, all effects classified, required cleanup receipts present, and no active lease/attempt/capability.
- New execution **MUST NOT** overlap an unquiesced prior attempt. Cleanup-only authority **MAY** survive cancellation, but **MUST NOT** permit business writes.

### RC-6 — lease renewal and reclaim races lack a transaction protocol

The plan gives a TTL concept but not an authoritative clock, renewal CAS, deadline, maximum lifetime, or reclaim order.

- Lease issue and renewal **MUST** use database time.
- Renewal **MUST** CAS on lease ID, work item, holder, attempt, fence, cancellation epoch, unreleased status, and `now < renew_by`; it **MUST** reject renewal at or after the deadline.
- A lease **MUST** have `issued_at`, `renew_by`, `expires_at`, and `max_expires_at`. Renewal **MUST NOT** extend beyond the configured maximum without a new admission and fence.
- Reclaim **MUST** close the old lease, advance the fence/epoch, revoke its capabilities, and only then issue new authority.
- Every protected state/effect gateway **MUST** re-read current authority immediately before commit/send. Results arriving after expiry **MAY** be retained as quarantined evidence but **MUST NOT** advance state.

### RC-7 — GitHub effect idempotency is not operation-specific

The SQL comment assumes receivers deduplicate an `idempotency_key`; GitHub has no universal caller-supplied idempotency contract for the targeted mutations.

- The plan **MUST** contain a versioned effect catalog for every enabled GitHub mutation.
- Each entry **MUST** specify endpoint/version, logical effect identity, natural or embedded marker, expected-before fingerprint/version, lookup and pagination algorithm, request digest, success receipt match, ambiguity rule, safe retry/compensation, read-after-write rule, and whether automatic retry is forbidden.
- The plan **MUST NOT** claim receiver deduplication unless the endpoint contract guarantees it.
- Timeout/lost-response outcomes **MUST** enter `UNKNOWN`; automatic replay **MUST** remain blocked until the catalog algorithm identifies exactly one matching effect or a human resolves ambiguity.

### RC-8 — improvement promotion is split and bypassable

Python accepts promotion validation in `CANARY_REVIEW`; SQL uses different stages and only checks non-null fields for `PROMOTED`. The approval FK does not prove exact subject/kind/expiry/separation or ordered evaluation.

- The plan **MUST** define one protected improvement lifecycle and generate application/database representations from it.
- Promotion **MUST** be allowed only from `APPROVED`, after immutable ordered stage events prove curation, offline evaluation, shadow, canary admission/results, and independent exact-digest approval.
- The promotion digest **MUST** bind candidate, configuration, protected evaluator identity/version, baseline/candidate results, canary cohort/window/results, policy version, and known-good rollback pointer.
- The transaction **MUST** verify approval kind, exact subject, quorum/role, expiry, invalidation, proposer/curator/approver separation, unchanged protected criteria, and no safety regression.
- Protected evals, policies, permissions, evidence, and rollback controls **MUST NOT** be self-approved. Rollback **MUST** be a first-class ordered transition with receipts.

### RC-9 — dependency and scheduler semantics are incomplete

Dependencies are untyped strings and admission alternates between “satisfied or scheduled” and terminal success. Queue ordering, quotas, overlap, and lock order are not reproducible.

- A dependency edge **MUST** record stable ID, type (`hard_success`, `ordering`, or another reviewed closed enum), source/target tenant/repository/item and bound versions, required outcomes, owner, propagation policy, and optional waiver authority/digest/expiry.
- Hard dependencies **MUST** require their declared current outcomes; “scheduled” **MUST NOT** satisfy hard success. Rollback/cancel/failure behavior and upstream rollback after admission **MUST** be explicit.
- Admission **MUST** validate acyclicity for the scoped graph and **MUST** define quarantine/repair for discovered or cross-repository cycles.
- In the same aggregate/admission transaction, the controller **MUST** bind the dependency snapshot/version and recheck it before attempt/lease creation.
- The scheduler **MUST** define a total queue tuple with a stable tie breaker, bounded aging/starvation policy, tenant/repository quotas, worker compatibility, canonical resource/conflict keys, glob/rename/generated-file rules, and a global lock acquisition order. Ambiguous overlap **MUST** serialize or block.

### RC-10 — reconciliation apply lacks optimistic concurrency

The prose dry run mentions desired SHA and observations, but `ReconciliationPlan` and its port do not bind either.

- A versioned apply plan **MUST** include tenant/repository/project scope, desired Git commit/digest, observation IDs and remote fingerprints/versions, operation dependency order, canonical plan digest, risk class, approval binding, creation/expiry, and per-operation expected-before/postcondition.
- Apply **MUST** revalidate desired revision, plan digest/approval, scope, expiry, and current remote fingerprint immediately before every mutation.
- A mismatch **MUST** perform no stale mutation. It **MUST** re-observe and classify conflict/replan/escalation. Partial application **MUST** persist receipts and resume from the operation DAG, not recreate completed effects.
- Unknown remote objects **SHOULD** remain preserved by default. Destructive adoption/removal **MUST** require a higher-risk reviewed plan.

### RC-11 — proof gates do not establish the claimed invariants

The passing unit suite misses known graph and loader defects. SQL tests omit lifecycle CAS, cancellation, formerly valid stale tokens, crash recovery, dependency races, and cleanup. Stage 2 relies on lagging field metrics after write enablement.

- Before any Stage-2 GitHub writer is enabled, the plan **MUST** require a published invariant-to-test matrix and passing target-version artifacts for graph/IR conformance, PostgreSQL two-session races, deterministic-clock lease tests, process-kill recovery, effect response-loss reconciliation, replay/restore, dependency admission, cancellation/quiescence, and cleanup restart.
- CI **MUST** enumerate every legal/illegal state pair and required exceptional trace for lifecycle, factories, composition, and improvement.
- Mutation tests **MUST** remove each authority/fence/CAS/digest/cleanup guard and demonstrate that a named test fails.
- “Zero observed stale writes” **MAY** remain a rollout metric, but **MUST NOT** substitute for a pre-enable stale-write rejection proof.
- A reviewer independent of the plan correction author **MUST** verify closure. No critical/high issue may remain open before affected capability enablement.

## Finding mapping

| Finding | Disposition | Root cause | Reproduced resolution |
|---|---|---:|---|
| STATE-001 | confirmed | RC-1 | YAML/Python/report graph mismatches reproduced. |
| STATE-002 | confirmed | RC-2 | Four factories target undeclared `BLOCKED`; no initial/terminal declarations or recovery edges. |
| STATE-003 | confirmed | RC-2 | Docs/YAML vocabularies differ; no durable instance/node/parent-child records exist. |
| STATE-004 | confirmed | RC-2 | Public loader fails on registered `build.yaml` with 15 errors. |
| STATE-005 | confirmed | RC-3 | No prior-state/continuation field; unconstrained valid Python unblock targets exist. |
| STATE-006 | confirmed | RC-4 | No aggregate version or transition procedure; broad runtime `UPDATE` grant exists. |
| STATE-007 | confirmed | RC-8 | Python permits validation from `CANARY_REVIEW`; SQL stage/checks differ and do not bind approval semantics. |
| STATE-008 | confirmed | RC-11 | 22 tests pass despite reproduced STATE-001/004; exceptional graph coverage is absent. |
| ORCH-PLAN-001 | duplicate-of STATE-001 | RC-1 | Same fragmented canonical lifecycle root cause and examples. |
| ORCH-PLAN-002 | confirmed | RC-5 | Direct terminal cancellation conflicts with the documented quiescence saga. |
| ORCH-PLAN-003 | confirmed | RC-2 | Schema lacks typed orchestration semantics and model/YAML shapes disagree. |
| ORCH-PLAN-004 | confirmed | RC-6 | No renewal/reclaim transaction, deadline rule, max lifetime, or race ordering. |
| ORCH-PLAN-005 | confirmed | RC-7 | No per-operation GitHub idempotency/reconciliation catalog exists. |
| ORCH-PLAN-006 | confirmed | RC-11 | Stage 2 has no named pre-write concurrency/fault proof gate. |
| ORCH-PLAN-007 | confirmed | RC-9 | Dependency meanings, versions, propagation, cycles, and atomic predicate are undefined. |
| ORCH-PLAN-008 | confirmed | RC-9 | Queue tuple, fairness, quotas, conflict normalization, and lock order are undefined. |
| ORCH-PLAN-009 | confirmed | RC-10 | Executable reconciliation plan omits desired/observed version bindings. |

## Required data, schema, and state contracts

The implementation plan **MUST** define these versioned logical records before code begins. Names may change, but semantics may not be omitted.

1. **`lifecycle_definition` / generated transition catalog:** version, state IDs, edge IDs, guard IDs/parameters, state classes, entry/exit effects, and terminal predicates.
2. **`work_item`:** aggregate/lifecycle version, lifecycle definition version, projected state, cancellation epoch, current spec/plan/policy/dependency digests, and repository/project/tenant scope.
3. **`transition_event`:** event/schema IDs and versions, expected/new aggregate version, before/after state, edge, actor, causation/correlation, bound digests, idempotency key/request digest, timestamp, and guard evidence digest.
4. **`blocked_continuation`:** prior state/node, revision, reason/resolution/owner/expiry, attempt/fence, and all invalidation bindings.
5. **`cancellation_saga`:** requested epoch/reason/actor, authority-revocation receipts, worker stop status/deadline, effect dispositions, cleanup DAG/receipts, escalation status, and terminal predicate result.
6. **`factory_definition`, `factory_instance`, `node_run`, `artifact_ref`, `composition_link`:** protected IR version/digest, state/version, node/edge/attempt/fence, typed inputs/outputs and digests, continuation, retry budget, delegated capability/budget, parent-child causality, and cleanup state.
7. **`lease` / `capability_grant`:** holder/attempt/scope, fence and cancellation epoch, issue/renew-by/expiry/max-expiry using DB time, renewal count, revocation/release, approved digests, and credential handle (not secret bytes).
8. **`dependency_edge` / `dependency_snapshot`:** typed and versioned endpoints/outcomes/propagation/waiver plus a digest bound at admission.
9. **`resource_claim` / queue contract:** canonical resource keys, normalized write sets, queue tuple components, quota bucket, claim order, and expiry.
10. **`effect_definition`, `effect_intent`, `effect_attempt`, `effect_receipt`:** catalog version, logical identity/request digest, expected-before, authority/fence, `PENDING|IN_FLIGHT|SUCCEEDED|FAILED|UNKNOWN|COMPENSATED|CANCELLED`, remote lookup/receipt data, and ambiguity resolution.
11. **`reconciliation_plan` / operation DAG:** desired revision, observations/fingerprints, plan digest/approval/expiry/risk, operation dependencies, expected-before/postcondition, receipts, and conflict disposition.
12. **`improvement_candidate` / immutable stage event:** unified state/version, candidate/config/eval/result/canary/rollback digests, separation-of-duty principals, approval binding, and promotion/rollback receipts.

All security-critical JSON/YAML schemas **MUST** reject unknown fields. Canonical byte serialization and digest algorithms **MUST** be versioned. Schema migrations **MUST** state forward/backward compatibility and fail-closed behavior for unknown versions.

## Implementation entry and exit tests

### Entry gate for implementation work

Implementation may start only when:

- the lifecycle and factory IRs, mappings, record schemas, stored-procedure/API contracts, effect catalog, and invariant-to-test matrix are reviewed and pinned;
- each high-severity correction above has an owner and traceable acceptance test;
- the target PostgreSQL version and GitHub API/App permission matrix are named;
- unknown endpoint behavior is either probed or its mutation remains disabled.

### Exit gate before any write pilot

The implementation **MUST** pass:

- exhaustive graph equivalence and all-state-pair tests across IR, generated code, SQL transition API, docs, and factory adapters;
- graph property tests for unknown endpoints, reachability, nonterminal sinks, cancellation, retry, stale/invalidation, rollback, compensation, and cleanup-before-terminal;
- crash-and-resume at every built-in factory node/edge, proving reconstruction from PostgreSQL alone with identical pinned node/fence/artifact/parent-child links;
- direct lifecycle `UPDATE` denied as runtime; compare-and-append success/idempotent replay/wrong-request reuse/concurrent-version race tests;
- block from every nonterminal state, every possible unblock target, and changed/expired-binding invalidation tests;
- cancellation at every lifecycle/effect point, including nonresponsive worker, controller crash, failed cleanup, unknown effect, and concurrent requeue;
- deterministic-clock, two-session lease tests immediately before/at/after deadline plus sweeper, delayed heartbeat, failover, cancellation, and in-flight call races;
- effect-catalog adapter tests for loss before send, after send, after remote commit, pagination, duplicate lookalikes, concurrent human edit, rate limit, and ambiguity quarantine;
- dependency model tests for cycles, diamonds, mixed outcomes, waiver expiry, cross-repository boundaries, admission race, upstream rollback, cancellation cascade, and queue fairness/deadlock;
- stale reconciliation tests that change desired Git or each remote resource between plan/apply and assert no stale write;
- improvement negative tests for every skipped stage, direct write, wrong/self/expired/unrelated approval, changed result, missing rollback pointer, plus valid promotion and rollback traces;
- restore/replay and mutation-test artifacts, followed by independent closure review and the full suite.

A capability **MUST** stay disabled when its required target integration test is unavailable or inconclusive.

## Residual uncertainty and blockers

- No PostgreSQL service was configured during review. SQL conclusions are confirmed by migration/grant inspection, but PostgreSQL 16 two-session and deployed-role tests remain a **blocker to the write pilot**.
- No controller implementation or crash trace exists. The plan contracts above are therefore design requirements, not claims of proven runtime behavior.
- No target GitHub tenant/API probe exists. Endpoint-specific marker, pagination, permission, rate-limit, ruleset, and concurrent-edit behavior remain a **blocker for each uncataloged mutation**.
- A future external controller could implement some missing controls, but no pinned interface or evidence currently makes that auditable.
- Research supports the mechanisms and cautions, not universal safety thresholds. Pilot counts and “zero observed” metrics cannot prove absence of races.
- Closure still requires a reviewer independent of the correction author. Until the corrected plan and proof matrix receive that review, critical/high closure is not final.

## Evidence URLs

Primary and authoritative sources used by the validated research and this resolution:

- PostgreSQL row locking and `SKIP LOCKED`: https://www.postgresql.org/docs/current/sql-select.html
- PostgreSQL transaction isolation and serialization failures: https://www.postgresql.org/docs/current/transaction-iso.html
- GitHub REST API best practices, including avoiding concurrent requests and handling errors/rate limits: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- GitHub webhook validation: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
- GitHub webhook delivery best practices: https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks
- GitHub Projects API behavior and separate item/field mutations: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects
- GitHub GraphQL `updateProjectV2ItemFieldValue`: https://docs.github.com/en/graphql/reference/mutations#updateprojectv2itemfieldvalue
- GitHub issue dependencies (collaboration primitive): https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies
- GitHub Actions concurrency limits (not the canonical database lock): https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- Temporal activity retry/unknown external-effect context: https://docs.temporal.io/develop/python/best-practices/error-handling
- JSON Schema 2020-12 core: https://json-schema.org/draft/2020-12/json-schema-core
- CloudEvents event envelope specification: https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md
- Fencing-token race analysis (non-authoritative but directly relevant engineering evidence): https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html

Repository evidence is pinned by path in the finding mapping and root-cause sections. Repeated research summaries were not counted as independent corroboration.
