# Round 1 resolution memo: factory and implementation contracts

## Scope and resolution rule

This memo resolves only the findings in `factory-cross-domain.json`, `implementation-review.json`, and `root-integration.json`. The repository remains a **plan-only feasibility package**. The prototype is evidence about missing contracts; it is not production code and this memo does not require patching it in this PR.

I applied `review-protocol.md`: each finding was reproduced against the cited artifact or an executable command, then merged by root cause. I also reviewed the 23 validated research records in `results/`, `lifecycle-extension/results/`, and `domain-extension/results/`. Those records support the control boundaries below, but repeatedly mark exact schemas, numeric thresholds, runtime outcomes, and GTM value as local-validation questions.

### Reproduction summary

The following checks were rerun in the project environment:

- `uv run agent-os config-validate --path .agent-os/config.yaml` — failed on the checked-in config/model mismatch.
- `uv run agent-os factory-validate .agent-os/factories/build.yaml` and the same command for `deep-research.yaml` — failed on the checked-in DSL/model mismatch.
- `uv run agent-os decision-validate .agent-os/factories/example.conversation-decision.json` — failed on the checked-in decision/model mismatch.
- `uv run agent-os transition MERGED OBSERVING` — rejected a transition allowed by `.agent-os/lifecycle.yaml`.
- `canonical_bytes({'n': 1.0, 'z': -0.0})` produced `{"n":1.0,"z":-0.0}`, contrary to the configured RFC 8785 representation.
- Source inspection confirmed: readiness never checks `READY_REVIEW` and trusts a caller digest; context creation permits unsigned output and two base revisions; the factory validator skips registry/composition and performs no graph compilation; SQL lacks aggregate/tenant ownership constraints and grants `polar_runtime` DELETE on all tables; reconciliation treats every same-name difference as an update; CI runs only the JSON-schema script.

## Verified root causes

There are **16 fully confirmed unique root causes**, plus two partially confirmed roots. No assigned finding was rejected. The review JSONs also deviate from the protocol issue shape (`requirement`/`evidence.urls`/`recommendation`, with no `status` or `owner`); implementation triage **MUST** normalize them to the protocol schema before tracking closure.

| Root | Verified root cause | Findings |
|---|---|---|
| RC-01 | Two independently evolved contract families exist: reviewed JSON Schema/YAML and private Pydantic/CLI shapes. | FCD-001, IMPL-001, ROOT-R1-001, ROOT-R1-002 |
| RC-02 | Individual “factory validation” is shape checking, not a typed compiler. | FCD-002, IMPL-009 |
| RC-03 | Registry/composition examples were added without schemas, graph resolution, authority calculation, or compiler ownership. | FCD-003 |
| RC-04 | The enabled research factory has prose evidence rules and an incomplete lifecycle rather than typed claim/provenance/freshness semantics. | FCD-004 |
| RC-05 | The relational runtime has no immutable project/environment tenant key or database-enforced cross-project isolation. | FCD-005 |
| RC-06 | Consumer distribution has no verifiable release, compatibility, effective-config, migration, rollback, canary, or dogfood contract. | FCD-006 |
| RC-07 | Architecture states engineering-first separation and dogfood, but measured extraction/GTM phases, owners, denominators, and stop gates remain outside the operative roadmap. | FCD-007 |
| RC-08 | Protected lifecycle policy and executable lifecycle code are contradictory sources of truth. | IMPL-002 |
| RC-09 | READY is a weak library predicate over caller assertions, not an authenticated command over canonical state. | IMPL-003, ROOT-R1-003 |
| RC-10 | The executable context model diverges from the protected schema and has no mandatory signature, full lease/holder authority, cancellation/budget/action bounds, or verifier; the protected schema does contain `attempt_id`, fencing token, and lease expiry. | IMPL-004 |
| RC-11 | Context accepts a redundant base revision without enforcing equality with the ticket base. | ROOT-R1-004 |
| RC-12 | The configured cross-component canonicalization is not the implemented serialization. | IMPL-005 |
| RC-13 | Single-column foreign keys permit cross-owner provenance substitution. | IMPL-006 |
| RC-14 | The event/ingress ledger lacks aggregate CAS, schema/policy/candidate identities, and the declared installation delivery scope. | IMPL-007 |
| RC-15 | Broad runtime DELETE/UPDATE privileges defeat append-oriented authorization and operational history. | IMPL-008 |
| RC-16 | Reconciliation has no identity, precondition, drift/risk classification, ambiguity gate, or read-back contract. | IMPL-010 |
| RC-17 | Required Python, SQL, cross-contract, and end-to-end suites are not CI merge gates. | IMPL-011 |
| RC-18 | R0–R4 research policy is silently collapsed into incompatible R0–R3 and string taxonomies. | IMPL-012 |

## Finding mapping

`duplicate-of` means the facts were reproduced but the finding adds no independent root cause.

| Finding | Severity | Resolution | Canonical root | Reproduction result |
|---|---:|---|---|---|
| FCD-001 | high | confirmed | RC-01 | Both shipped factories fail the CLI loader. |
| FCD-002 | high | confirmed | RC-02 | Unknown phases and unconstrained semantic strings pass JSON Schema. |
| FCD-003 | high | confirmed | RC-03 | The validator explicitly skips `registry.yaml` and `composition.yaml`; unlike FCD-002, this is the distinct inter-factory resolution/authority boundary. |
| FCD-004 | high | confirmed | RC-04 | Research artifacts are paths/prose; `BLOCKED` is undeclared and cancel/resume/stale/refresh closure is absent. |
| FCD-005 | high | confirmed | RC-05 | Schema has free-text repository/scope, no project FK/RLS, and one global runtime role. |
| FCD-006 | high | confirmed | RC-06 | Consumer schema lacks manifest hashes, compatibility, migration/rollback/canary and stable dogfood data. |
| FCD-007 | medium | partially-confirmed | RC-07 | Architecture already covers engineering-first separation, distribution, feedback, and dogfood; the measured extraction/GTM sequence, owners, denominators, and stop gates are absent from the operative roadmap/ADR. The review’s cited `report.md:338-397` range is stale because the current file ends earlier. |
| IMPL-001 | high | duplicate-of FCD-001 | RC-01 | Config and factory CLI failures reproduce the shared contract split. |
| IMPL-002 | high | confirmed | RC-08 | Git permits transitions rejected by Python; Python has BLOCKED resumes absent from Git. |
| IMPL-003 | high | confirmed | RC-09 | INBOX, branch-like base, caller digest, claimed human, and no expiry can satisfy READY. |
| IMPL-004 | high | partially-confirmed | RC-10 | The executable model is unsigned by default and lacks attempt/lease/fence/expiry/worker/cancellation/budget fields and a verify API. The title is overbroad because the separate protected JSON Schema does require `attempt_id`, `lease.fencing_token`, and `lease.expires_at`. |
| IMPL-005 | high | confirmed | RC-12 | Python output differs from RFC 8785 for integral float and negative zero. |
| IMPL-006 | high | confirmed | RC-13 | Cited FKs do not carry work-item/effect ownership. |
| IMPL-007 | high | confirmed | RC-14 | Required aggregate, event, candidate and installation columns/constraints are absent. |
| IMPL-008 | high | confirmed | RC-15 | `polar_runtime` has DELETE on all tables and listed history tables lack immutable guards. |
| IMPL-009 | high | duplicate-of FCD-002 | RC-02 | Same missing typed compiler and composition resolver. |
| IMPL-010 | medium | confirmed | RC-16 | A type-changing same-name field becomes an unconditional `update`. |
| IMPL-011 | medium | confirmed | RC-17 | Workflow runs only `.agent-os/bin/validate.py`. |
| IMPL-012 | medium | confirmed | RC-18 | Report, YAML/schema, SQL, and Python expose incompatible tier sets. |
| ROOT-R1-001 | critical | duplicate-of FCD-001 | RC-01 | Same shipped-factory/Pydantic mismatch. |
| ROOT-R1-002 | critical | duplicate-of FCD-001 | RC-01 | Same split contract root, also reproduced for config and conversation decision. |
| ROOT-R1-003 | high | duplicate-of IMPL-003 | RC-09 | Same untrusted READY predicate; dependency modeling detail is included in RC-09. |
| ROOT-R1-004 | high | confirmed | RC-11 | `create_run_context` digests the separate argument without equality validation. |

Totals: **16 fully confirmed unique roots, 2 partially confirmed roots, 5 duplicate findings, and 0 rejected findings**.

## Exact normative plan corrections

These are corrections to the final implementation plan, not requests to modify the prototype in this PR.

### 1. Contract authority and compilation

1. The plan **MUST** name one versioned canonical schema registry for config, ticket, approval, decision, context, lifecycle, factory, registry, composition, consumer, event, and artifact contracts. Generated language models **MUST** be derived from, or conformance-tested bidirectionally against, that registry. Parallel private shapes **MUST NOT** be accepted.
2. Every bundled and enabled artifact **MUST** validate through JSON Schema, the runtime loader, and the compiler and **MUST** produce one deterministic canonical digest. Registry entries **MUST** bind `{factory_id, schema_version, factory_version, path, content_digest, enabled}`.
3. A factory **MUST** compile to a normalized typed DAG/IR. Nodes **MUST** declare typed input/output ports, role, capability and sandbox/tool bindings, budgets, read/write/resource sets, retry class, idempotency key derivation, compensation, timeout, cancellation, cleanup/retention, evaluator, and projection references. Edges **MUST** use structured predicates and typed joins rather than executable prose.
4. Compilation **MUST** reject unresolved or duplicate symbols, empty IDs, missing producers, incompatible ports, undeclared transitions, unreachable terminals, implicit cycles, unbound approval gates, parallel write conflicts, widened child authority/budget, and missing cancellation/cleanup paths.
5. Registry and composition **MUST** be versioned contracts. Child references **MUST** be immutable digests. Composition **MUST** preserve or reduce authority and budget, reject cycles, define deterministic port mappings and joins, and propagate child failure, cancellation, compensation, and cleanup. A child **MUST NOT** manufacture READY or approval.
6. The plan **SHOULD** keep domain-neutral IR small. It **MUST NOT** add GTM nouns or promise a public plugin SDK until the extraction gates in section 6 pass.

### 2. Lifecycle, readiness, and run authority

1. Protected lifecycle policy **MUST** be the only authored transition source. Runtime tables, docs, and tests **MUST** be generated from its compiled form. Every state **MUST** define legal entry, exit, cancellation, stale-input, retry/exhaustion, timeout, cleanup-in-progress/failure, resume, rollback, and terminal behavior. BLOCKED resume **MUST** store prior state and revalidate current policy/input digests.
2. READY **MUST** be a controller command over canonical stored revisions while the aggregate is in `READY_REVIEW`; it **MUST NOT** trust a caller-supplied expected digest. The controller **MUST** recompute a versioned authorization digest from exact spec, plan, acceptance-oracle, base commit, policy, capabilities, dependencies, risk tier, and repository/project/environment identity.
3. READY approval **MUST** include approval ID, purpose, subject digest, authenticated subject/role, issue time, mandatory expiry, policy version, and invalidation state. Removed roles, stale inputs, expired approvals, wrong purposes, and non-human/self approval **MUST** fail closed. Dependencies **MUST** be typed edges with observed state/version; resolved dependencies **MUST** be allowed and unresolved ones **MUST** block.
4. A production Run Context Bundle **MUST** contain one exact base commit and **MUST** reject any ticket/top-level mismatch. It **MUST** bind repository/project/environment, ticket/spec/plan/policy/capability digests, attempt and worker IDs, lease ID, fencing token, lease expiry, cancellation epoch, budgets, allowed actions, key ID, issued/expiry times, and approval reference.
5. Production contexts **MUST** be signed by a controller-managed asymmetric or managed key and **MUST** have a fail-closed consumer verification API. “Unsigned” **MAY** exist only as a separately named inert demo artifact that cannot reach a runner or effect gateway. Every side-effect boundary **MUST** independently recheck tenant, permission, approval, attempt, lease, fence, cancellation, budget, and idempotency.
6. Authorization canonicalization **MUST** either implement versioned RFC 8785 with official vectors or adopt another precisely specified versioned byte format. Unsupported values **MUST** be rejected. All producer/consumer languages **MUST** share digest fixtures.

### 3. Deep-research factory contract

1. Research work **MUST** use typed `ResearchItem`, `FieldDefinition`, `Claim`, `Observation`, `SourceSnapshot`, `SourceFamily`, `Conflict`, `CoverageResult`, `ValidationResult`, `ArtifactRef`, and `ResearchDecision` records. Each record **MUST** carry schema version, stable identity, content digest, producer/run identity, timestamps, and provenance links.
2. A claim **MUST** link to observations and retrievable source snapshots. Source count alone **MUST NOT** imply corroboration. Independence/source-family classification, access metadata, entailment result, coverage, freshness, conflicts, and explicit `UNKNOWN` **MUST** be preserved.
3. Fan-out/join **MUST** be deterministic. Gap audit **MUST** use an independent role where it affects publication. Resume **MUST** reuse only schema-valid artifacts whose input/config/source digests match. Refresh **MUST** invalidate only declared dependents and surface stale evidence.
4. Scope, collection, validation, conflict/gap audit, synthesis, human handoff, refresh, BLOCKED, cancel, exhaustion, cleanup, and terminal states **MUST** have complete transitions. The human handoff **MUST** bind the exact report, evidence-index, conflict, coverage, and policy digests.

### 4. Relational state, tenancy, and history

1. The plan **MUST** define immutable `tenant_id`, `project_id`, `environment_id`, and repository binding. All aggregates, inbox/outbox, idempotency, events, revisions, attempts, leases, approvals, evidence, effects, receipts, deployments, outcomes, artifacts, and audit records **MUST** carry or inherit enforceable compound ownership. Repository aliases **MUST NOT** change ownership identity.
2. Project-scoped service identities **MUST** be enforced with PostgreSQL RLS plus session claims, or separate databases/roles where the threat model requires it. Missing claims and cross-project reads, writes, leases, effects, idempotency reuse, export, and backup access **MUST** fail closed. Fleet metadata and cross-project handoffs **MUST** be separate; a handoff **MUST** be typed, digest-bound, and approved by both owners.
3. `event_ledger` **MUST** carry `{aggregate_id, aggregate_version, event_id, event_schema_version, command/idempotency_key, policy_commit, occurred_at, causation_id, correlation_id, actor, before_state, after_state, input_digests}` with uniqueness on aggregate version and compare-and-append semantics.
4. Webhook identity **MUST** include provider installation and delivery identity plus repository/project binding. Evidence **MUST** bind exact candidate/head and merge-group SHA. Every approval/deployment/outcome/effect/receipt FK **MUST** include the owning work item/effect and required subject digest/purpose.
5. Runtime grants **MUST** be per table and operation. Service roles **MUST NOT** DELETE durable authorization, decision, attempt, effect, deployment, evaluation, event, evidence, receipt, or audit history. Invalidation and retention **MUST** append attributable events or use narrow audited procedures. Direct writes **SHOULD** be removed where a guarded procedure is required for current-policy checks.

### 5. Reconciliation and risk policy

1. The existing reconciler is a non-mutating dry run, but its plan classifies unsafe differences too weakly. Reconciliation resources **MUST** have stable provider IDs/logical IDs, observed version/fingerprint, desired fingerprint, ownership, precondition, drift class, risk class, and ambiguity result. Semantic/type/permission/destructive/ambiguous drift **MUST** freeze automatic apply. Unknown objects **MUST** be preserved by default.
2. Mutations **MUST** use a reviewed plan, expected-before precondition, idempotency key, bounded pagination/inventory evidence, receipt, read-back, and convergence check. Delete **MAY** occur only under an explicit high-risk policy with rollback and human authorization.
3. One authoritative R0–R4 taxonomy **MUST** be used by report, schemas, SQL, policy, UI, approvals, and code. R4 **MUST** remain human-led. Unknown/ambiguous risk **MUST** fail to the highest applicable gate. Any deliberate tier collapse **MUST** be recorded as a versioned compatibility decision and may only preserve or increase controls.

### 6. Consumer release, dogfood, and extraction gates

1. A consumer manifest at a named path **MUST** bind bundle version/content digest, signed hash manifest or attestation, controller/schema/domain/factory/adapter compatibility ranges and exact pins, tenant/project/environment, required permissions, capability reductions, effective-config provenance/digest, migration state, rollback pin, release channel, and canary ring.
2. Install/verify/update/rollback tooling **MUST** verify every managed file and reject tampering, unsupported combinations, mutable refs, capability expansion, and unexplained commit/workflow pin divergence. Upgrades **MUST** show permission, schema/migration, and effective-config diffs and retain a tested rollback.
3. Dogfood **MUST** run the last stable release in a separate tenant from candidate validation/promotion. Candidate code **MUST NOT** approve or promote itself. Feedback **MUST** be a privacy-filtered typed outcome/eval proposal; raw consumer content **MUST NOT** enter a central corpus by default.
4. The authoritative rollout/ADR **MUST** assign owners and evidence artifacts for: a 14-day stable shadow, 2–3 consumer repositories, three materially different workflows, two adapters stable for two releases/60 days, and the documented duplication threshold before SDK extraction. Thresholds are proposed local gates and **MAY** be changed only by an explicit, evidence-backed decision with denominator and stop rule.
5. Failure to meet a gate **MUST** keep abstractions internal. GTM **MUST** remain a separate repository/domain, read-only or draft-only until its own volume, consent/privacy, governance, quality, and authority gates pass.

### 7. Merge-gate validation

CI **MUST** install the locked project environment and gate JSON Schema validation, Python tests, all shipped cross-loader golden fixtures, factory compilation, lifecycle conformance, RFC 8785 vectors, SQL migrations/negative tests, and one end-to-end plan fixture. A changed architecture or safety boundary **MUST** trigger another independent cross-discipline review. Required jobs **SHOULD** run for pull requests and merge groups with least privilege and immutable action pins.

## Required data/schema/state contracts

The implementation plan cannot enter coding until it names versions, owners, storage authority, mutation authority, retention, migration compatibility, and canonical digest rules for these minimum contracts:

| Contract family | Minimum required contents |
|---|---|
| Schema registry/lock | schema ID/version/digest, compatibility rule, generator/conformance version, migration, deprecation, owner |
| Factory/IR/composition | factory/version/digest; typed nodes, ports, edges, predicates, roles, capabilities, sandboxes, budgets, resources, joins, retries, compensation, cancellation, cleanup, evals; immutable child lock |
| Aggregate/event/command | tenant/project/environment, aggregate ID/version, event schema, actor, command/idempotency, causation/correlation, policy commit, input/output digests, before/after state |
| Approval/decision | purpose, exact subject/input digests, authenticated principal and role, policy version, timestamps/expiry, decision, rationale, invalidation/supersession |
| Attempt/lease/context | attempt/worker, lease/fence/expiry, cancellation epoch, exact base/candidate, scope, budgets, allowed actions, signing key ID/signature |
| Artifact/provenance | stable ID, media/schema type/version, digest, size/location, producer/run/tool, parents, created/accessed/snapshot time, integrity/attestation, retention/classification |
| Research evidence | item/field, claim/observation/source/source-family/conflict, entailment, independence, coverage, freshness, UNKNOWN, validation/audit decision |
| Effect/receipt | owner aggregate, effect ID/type, idempotency, attempt/fence, request digest, UNKNOWN state, receipt/provider identity, reconcile/compensate outcome |
| Tenant/project | immutable IDs, repository/environment binding, service identity, quota/queue, credential selector, workspace/artifact namespace, RLS claim |
| Consumer/release | release and file digests/signature, compatibility/pins, permissions/capability reductions, effective config, migration/rollback/canary/dogfood, feedback policy |
| Reconciliation | logical/provider ID, desired/observed versions and fingerprints, ownership, drift/risk/ambiguity, precondition, plan/receipt/read-back/convergence |
| Risk policy | R0–R4 meanings, triggers, required approvers/checks, authority ceiling, escalation, exception/expiry, calibration evidence |

## Implementation entry and exit tests

### Entry tests: required before implementation begins

- A schema inventory proves there is one owner and one canonical version for every contract above; no duplicate private model remains in the plan.
- Golden and adversarial fixtures specify cross-language acceptance/rejection and canonical digests before model generation.
- The lifecycle table is exhaustive for every state and event, including invalid transitions, cancellation, stale/retry/exhaustion, timeout, cleanup failure, resume, rollback, and terminal behavior.
- The threat model selects RLS versus database/role isolation and documents tenant, worker, controller, reconciler, auditor, promoter, and emergency-admin powers.
- Factory IR and composition semantics, research evidence schemas, rollout owners, metrics/denominators, stop rules, and rollback rules are approved plan artifacts.
- The target GitHub tenant/API/plan and PostgreSQL version are pinned for contract testing. Retention/privacy/legal decisions have named owners.

### Exit tests: required before any capability is represented as delivered

- Every shipped config/example/factory loads through JSON Schema and generated runtime models, compiles, and yields the same digest; all alternate old shapes fail.
- Property/mutation tests reject every invalid factory and composition case listed in sections 1 and 3. All engineering factories compile; no GTM extension is required.
- Exhaustive state-pair/event tests prove code, policy, docs, cancellation, retry, rollback, cleanup, and terminal behavior agree. Stale approvals and invalid transitions fail closed.
- READY tests reject INBOX, caller digest substitution, mutable base refs, missing expiry, wrong/removed roles, invalidation, wrong purpose, and unresolved dependencies; resolved versioned dependencies pass.
- Context tests reject unsigned production bundles, unknown keys, tampering, base mismatch, wrong worker/tenant, expiry, stale fence, cancellation, changed digest, exceeded budget, and invocation before verification.
- Official RFC 8785 plus numeric, Unicode/non-BMP ordering, escaping, and cross-language vectors agree byte-for-byte.
- Two-project SQL tests reject foreign SELECT/INSERT/UPDATE/lease/effect/idempotency/provenance/export; missing RLS claims fail. Cross-owner FK substitution and duplicate aggregate versions fail. Runtime DELETE/unauthorized UPDATE fails on all durable history.
- Crash/replay tests cover every commit/effect boundary, duplicate/out-of-order delivery, UNKNOWN effects, lease expiry/fencing, compensation, restoration/replay, and cleanup failure without duplicate effects or false completion.
- Reconciliation tests cover rename/type/permission/destructive/ambiguous drift, provider-ID collision, stale precondition, pagination loss, unknown preservation, read-back mismatch, and convergence.
- An external clean repository installs a pinned signed release, verifies all file hashes, rejects tampering/incompatibility/authority expansion, completes migration/canary/rollback, and emits only approved redacted feedback.
- CI runs all of the above applicable suites on pull requests and merge groups. A non-author reviewer verifies closure. Exit still requires zero open critical/high, owned/gated medium findings, and no new critical/high in the final audit.

## Residual uncertainty and blockers

- There is no production controller, artifact store, signing service, project-scoped database identity, release registry, external consumer, or GTM repository. Therefore runtime isolation, recovery rates, throughput, cost, false-block rate, defect escape, and tenant escape cannot be measured yet.
- The validated research supports the proposed boundaries more strongly than exact schema/API choices. Numeric dogfood/extraction/canary thresholds are falsifiable starting gates, not universal empirical constants.
- GitHub documentation and tenant capabilities are living and plan-dependent. Live sandbox contract tests remain mandatory before rollout.
- PostgreSQL RLS is one candidate boundary; the threat model may require separate databases or roles. Backup, export, retention, privacy, and emergency-admin policy still need owners.
- Deep-research semantic entailment, source-family independence, evaluator accuracy, and safe selective invalidation need repository-specific labeled fixtures. A schema cannot prove truth.
- **Blocking decision-grade-plan gaps:** canonical schema/IR ownership; complete lifecycle table; READY/context authorization tuple; tenant-isolation choice; relational ownership/CAS envelope; consumer release/rollback contract; single R0–R4 policy; and named rollout owners/metrics/stop gates. Until these are written into the authoritative plan, all affected capabilities remain blocked.

## Evidence URLs

Primary and standards sources already validated in the research set and relevant to these corrections:

- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12 and https://json-schema.org/draft/2020-12/json-schema-core
- RFC 8785 JSON Canonicalization Scheme: https://www.rfc-editor.org/rfc/rfc8785
- CloudEvents v1.0.2: https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md
- Warp Factory as Code: https://docs.warp.dev/factories/factory-as-code/
- Amazon States Language and Argo DAG/exit semantics: https://states-language.net/spec.html ; https://argo-workflows.readthedocs.io/en/latest/walk-through/dag/#fail-fast ; https://argo-workflows.readthedocs.io/en/latest/walk-through/exit-handlers/
- Temporal event history and retry semantics: https://docs.temporal.io/workflow-execution/event and https://docs.temporal.io/encyclopedia/retry-policies
- Kubernetes controller and lease patterns: https://kubernetes.io/docs/concepts/architecture/controller/ and https://kubernetes.io/docs/concepts/architecture/leases/
- PostgreSQL locking/queue primitive: https://www.postgresql.org/docs/current/sql-select.html
- GitHub webhook validation and delivery practice: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries and https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks
- GitHub Actions permissions and secure use: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions and https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- GitHub reusable workflow behavior: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- GitHub rulesets, merge queue, and CODEOWNERS: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets ; https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue ; https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- GitHub Projects API and mutation surface: https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects and https://docs.github.com/en/graphql/reference/mutations#updateprojectv2itemfieldvalue
- SLSA requirements and provenance: https://slsa.dev/spec/v1.2/requirements and https://slsa.dev/spec/v1.2/provenance
- W3C provenance and in-toto statement subjects: https://www.w3.org/TR/prov-o/ and https://in-toto.io/Statement/v1
- NIST SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
- Kubernetes multi-tenancy limits: https://kubernetes.io/docs/concepts/security/multi-tenancy/
- GitHub installation-token repository/permission scoping: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app
- OWASP prompt injection and excessive agency: https://genai.owasp.org/llmrisk/llm01-prompt-injection/ and https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
- GitHub Security Lab on privileged workflow attacks: https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/
- OpenAI evaluation guidance and Anthropic agent-eval guidance: https://developers.openai.com/api/docs/guides/evaluation-best-practices and https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

These URLs establish mechanism and control constraints. They do not establish local production outcomes or safe unattended autonomy.
