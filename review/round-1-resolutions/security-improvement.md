# Round 1 resolution: security and governed improvement

## Scope and disposition

This memo resolves `security-red-team.json` and `self-improvement.json`. It is a correction to the implementation **plan**, not an implementation patch. The prototype remains non-shipping and default-disabled. I inspected the cited source, schemas, migrations, tests, desired configuration, and the validated research tree. I also ran `.venv/bin/pytest -q` (22 passed). The desired-config validator could not run in the project `.venv` because `yaml` and `jsonschema` are absent there. An independent reproduction ran it in an available dependency environment: the baseline passed 8 schemas, and temporary malicious capability and workflow fixtures also passed as described below. An independent reproduction also applied all migrations to fresh PostgreSQL 16 and confirmed cross-repository access/update, rejected-expired approval reuse, mutable `UNKNOWN` effects, concurrent unfinished attempts, cross-effect receipts, forged authority/audit rows, and cross-work-item spec substitution.

Disposition: **16 confirmed root causes, 1 partially confirmed root cause, 0 rejected findings, and 3 findings deduplicated into other roots**. Passing prototype tests is not production evidence.

## Verified root causes

| Root | Severity | Verified root cause | Findings |
|---|---|---|---|
| RC-01 | high | Tenant identity is not a first-class immutable key. Tables, uniqueness scopes, roles, queues, artifacts, and improvement records therefore do not enforce repository/installation isolation. | SEC-R1-001; SI-007 |
| RC-02 | high | Approval is caller-asserted data, not a purpose-bound authority record resolved from authenticated identity, current roles, quorum, and revocation state. | SEC-R1-002; SI-003 |
| RC-03 | high | Desired-config validation parses files but does not enforce the maximum capability lattice, mandatory denies, safe composition, registry paths, or typed tool/secret/egress classes. | SEC-R1-003 |
| RC-04 | high | Workflow validation ignores `.yaml` and lacks semantic GitHub Actions security rules. | SEC-R1-004 |
| RC-05 | medium | Plans and repository checks expose executable shell strings instead of protected command IDs plus typed arguments. This is a contract flaw even though no controller currently executes them. | SEC-R1-005 |
| RC-06 | high | Effect intent and transition authority are mutable. `UNKNOWN` can be blindly reset, concurrent unfinished attempts are possible, and receipts are not relationally bound to the same effect as their attempt. | SEC-R1-006 |
| RC-07 | high | Blanket runtime DML collapses controller, approval, lifecycle, deploy, promote, and audit authority. Authority-bearing transitions are rows that a broad role can manufacture instead of checked procedures/events. | SEC-R1-007; SI-001 |
| RC-08 | high | Bare-ID foreign keys do not prove same tenant/work item/subject. Valid evidence, spec, approval, attempt, deployment, observation, or receipt can be substituted across aggregates. | SEC-R1-008 |
| RC-09 | medium | Execution context may be unsigned and is not bound to issuer, audience/worker, tenant, attempt, fence, cancellation epoch, expiry, replay nonce, or exact resource capabilities. | SEC-R1-009 |
| RC-10 | medium | The policy gate installs version-pinned but not fully resolved/hash-verified dependencies and is not bound to a digest-pinned tool image. | SEC-R1-010 |
| RC-11 | medium | Role migrations neither normalize nor reject hostile pre-existing attributes, memberships, ownership, direct grants, and default privileges. | SEC-R1-011 |
| RC-12 | critical | Promotion trusts proposer booleans and arbitrary hashes instead of independently signed, fresh, complete evaluation evidence resolved from protected state. | SI-002 |
| RC-13 | high | The improvement graph conflates review, approval, execution, and result. Canary admission/widening has no signed bounded rollout envelope or fail-closed pause/abort states. | SI-004 |
| RC-14 | high | Promotion does not bind a tested compatible last-known-good target. Rollback is one unverified terminal label rather than an observed recovery workflow. | SI-005 |
| RC-15 | medium | Delayed-harm windows, denominators, release review/expiry, missing telemetry, freeze, revocation, and retirement are absent from durable state. | SI-006 |
| RC-16 | medium | Privacy, consent/license, provenance, classification, retention, redaction, deletion, and legal hold are prose rather than enforced evidence contracts. | SI-008 |
| RC-17 | medium | The research protocol has explicit closure criteria, but no repository-executable acceptance manifest maps the researched self-improvement matrix one-to-one to tests or names a separate enablement gate. The green suite therefore has unsafe coverage blindness. | SI-009 |

## Finding mapping

| Finding | Disposition | Reproduction and rationale | Root |
|---|---|---|---|
| SEC-R1-001 | confirmed (severity corrected to high) | `docs/database.md` declares the current database one trust domain, so this is not a current tenant escape. It is a multi-repository production-admission blocker: `work_items.repository` is free text; inbox, idempotency, outbox, audit, and eval rows lack a tenant FK; no table enables/forces RLS; shared runtime/auditor grants span all rows. | RC-01 |
| SEC-R1-002 | confirmed | Python accepts `approved_by`/`approver_kind` supplied by the caller and permits `expires_at=None`. SQL stores no issuer, role snapshot, quorum, source review, or purpose-dependent target. Deployment/promotion use bare `approval_id`. | RC-02 |
| SEC-R1-003 | confirmed | `validate.py` only forbids four strings in `may`. Capability `network`, `secrets`, GitHub permissions, unrestricted factory `tools`, registry, and composition are not semantically bounded. | RC-03 |
| SEC-R1-004 | confirmed | Workflow glob is `.github/**/*.yml`; only YAML parsing occurs. `.yaml`, mutable `uses`, broad permissions, unsafe `pull_request_target`, and expression-to-shell are not rejected. | RC-04 |
| SEC-R1-005 | confirmed (medium latent sink) | Ticket `verification.commands` accepts arbitrary strings and repository checks define command strings. There is no command catalog, typed argv, resolver, or shell prohibition. Exploit is contingent on a future executor, so it is an implementation-admission blocker rather than a claim of current RCE. | RC-05 |
| SEC-R1-006 | confirmed | Reconciler has UPDATE on outbox; no transition or immutable-intent trigger exists; unfinished attempts have no partial unique constraint; receipt has independent FKs to effect and attempt. | RC-06 |
| SEC-R1-007 | confirmed | `polar_runtime` has all DML on all tables, including approvals, work items, eval candidates, deployments, event ledger, and audit. Reconciler can append ledger/audit rows. | RC-07 |
| SEC-R1-008 | confirmed | `work_items.current_spec_revision_id`, evidence attempt, deployments approval, outcomes deployment, drift observation, and receipt attempt links use bare IDs despite composite keys existing elsewhere. | RC-08 |
| SEC-R1-009 | confirmed | `create_run_context(signing_key=None)` emits `signature_scheme='none'`; the published context schema lacks the authority-binding fields and forbids adding them. | RC-09 |
| SEC-R1-010 | confirmed | Requirements contain direct versions without hashes/transitive lock; workflow installation does not use `--require-hashes` or a digest-pinned validator image. | RC-10 |
| SEC-R1-011 | confirmed | Conditional role creation leaves an existing role unchanged; security migration revokes PUBLIC but does not assert role attributes/membership or stale direct/default grants. | RC-11 |
| SI-001 | duplicate-of SEC-R1-007 | Direct `eval_candidates.stage='PROMOTED'` is the same broad-DML/unguarded-transition root. Its unrelated-approval aspect is also covered by RC-02/RC-08. No stage-history trigger or guarded transition exists. | RC-07 (also RC-02/08) |
| SI-002 | confirmed | `validate_improvement_promotion` compares hashes and two proposer-supplied booleans; it loads no suite, result, attestation, trials, slices, denominators, thresholds, signer, or environment. Invented SHA-256 values satisfy the contract. | RC-12 |
| SI-003 | duplicate-of SEC-R1-002 | Whitespace/alias identities bypass exact-string self-check; no authenticated canonical principal, role, quorum, curator/evaluator separation, or revocation check exists. | RC-02 |
| SI-004 | confirmed | `validate_improvement_transition` checks graph adjacency only. Shadow-to-canary takes no approval/evidence, and the proposal has no cohort, exposure, budget, effects, stop rules, or widening control. | RC-13 |
| SI-005 | confirmed | Promotion digest omits previous-good, compatibility, reversibility, drill, and RTO evidence. `PROMOTED -> ROLLED_BACK` needs no receipt or health observation and has no failure path. | RC-14 |
| SI-006 | confirmed | Neither Python nor SQL improvement state carries observation window/sample/cohort/review expiry. No metrics-unavailable/frozen/expired/revoked/retired state exists. | RC-15 |
| SI-007 | duplicate-of SEC-R1-001 | The improvement-specific exposure is the same missing tenant key and shared-role boundary, including eval candidates and evidence. | RC-01 |
| SI-008 | confirmed | Arbitrary JSON accepts raw text. Required privacy/provenance/retention fields, export approval, filter receipt, deletion job, and legal-hold workflow do not exist. | RC-16 |
| SI-009 | partially-confirmed | `review-protocol.md` already defines exit criteria, and the lifecycle research defines a test matrix, so “no closure gate” is too broad. The confirmed gap is that no repository-executable one-to-one conformance/enablement gate covers identity/evidence attacks, canary faults, tenant/privacy, concurrency, rollback, or the researched state matrix. | RC-17 |

## Exact normative plan corrections

1. **Isolation and referential integrity (RC-01, RC-08).** Every persisted, queued, cached, audited, or object-stored record **MUST** carry immutable `tenant_id` and `repository_id` (plus `work_item_id` where aggregate-scoped). All primary/unique/idempotency/object-prefix keys **MUST** be tenant-namespaced. Relationships **MUST** use composite tenant/aggregate foreign keys. Production connections **MUST** enforce tenant isolation with `FORCE ROW LEVEL SECURITY` and non-owner/non-`BYPASSRLS` roles, or a stronger per-tenant database boundary. Cross-repository evidence **MUST** use a separately authorized export/import envelope with both owners; ordinary joins **MUST NOT** cross the boundary.
2. **Authenticated approvals (RC-02).** Consequential approval **MUST** be append-only and created only by a narrow authority gateway from an authenticated principal. It **MUST** bind issuer, immutable subject, authentication assurance, role snapshot/version, source review ID, quorum members, independence constraints, tenant/work item, purpose/action, subject and artifact/config/policy/eval/rollout/environment digests, risk, issuance, finite expiry, and revocation/invalidation. Gates **MUST** resolve current authority and compare canonical identities, not caller strings. An absent, rejected, expired, revoked, wrong-purpose, wrong-tenant, stale-role, self, or under-quorum approval **MUST** deny.
3. **Protected configuration and workflows (RC-03, RC-04, RC-10, RC-11).** Capability/factory/registry/composition schemas **MUST** be closed and typed. Effective rights **MUST** be the intersection of parent maximums and child requests; mandatory denies **MUST NOT** be overridden. Workflow scanning **MUST** include `.yml` and `.yaml` and enforce default/explicit least permissions, full-SHA allowed actions, safe trigger/checkout combinations, secret/environment separation, cache partitions, and no untrusted expression-to-shell. The gate **MUST** run `actionlint` and `zizmor` or equivalent pinned checks. Dependencies **MUST** be fully resolved and hash verified from an approved source in a digest-pinned tool image. Role setup **MUST** normalize safe attributes and privileges or abort on pre-existing mismatch.
4. **Typed executable authority and contexts (RC-05, RC-09).** Plans **MUST** contain protected `command_id` plus schema-validated argv/data, never executable shell text. A digest-pinned command catalog outside model control **MUST** resolve IDs; execution **MUST** use direct argv without shell evaluation and enforce path, environment, egress, secret, resource, time, and cost bounds. Admission contexts **MUST** be signed and bind issuer, key ID/algorithm, audience/worker, tenant/repository/work item, attempt, current fence, cancellation epoch, nonce, issued/expiry times, base/spec/policy/catalog digests, and exact capabilities. Unsigned, replayed, expired, altered, wrong-audience, revoked-epoch, or stale-fence contexts **MUST** fail closed. Key rotation and revocation **SHOULD** support overlap without accepting retired keys.
5. **Effects and database authority (RC-06, RC-07).** Intent fields **MUST** be immutable. Authority tables **MUST NOT** grant raw DML to general runtime identities. Separate ingress, controller, dispatcher, reconciler, merger, deployer, promoter, and audit-writer roles **MUST** call narrow security-definer procedures that derive actor/tenant from authenticated session context, enforce CAS state revision/fence, validate approvals and composite relationships, and append events/outbox atomically. `UNKNOWN` **MUST** leave only after bound observation/receipt or explicit reviewed resolution; blind requeue **MUST** be impossible. One unfinished effect attempt **MUST** be enforced. Receipt `(attempt_id,effect_id,tenant_id)` **MUST** reference the same attempt/effect. Audit **SHOULD** be exported to an independently controlled tamper-evident anchor.
6. **Attested evaluation (RC-12).** Promotion **MUST** resolve the protected suite, evaluator, policy, thresholds, expected shards, and environment from trusted current state, not proposal fields. An `EvidenceBundle` **MUST** carry authenticated signer/builder, subject and all control digests, nonce/freshness, complete shard set, trial seeds/counts, slice numerators/denominators/confidence intervals, raw outcome references, hard invariants, failures, costs, and explicit `PASS|FAIL|INCONCLUSIVE`. Missing, stale, unknown, selected-away, wrong-signer, wrong-environment, zero-trial, or inconclusive evidence **MUST NOT** promote. Proposer assertions such as `safety_regression=false` **MAY** be diagnostic but **MUST NOT** authorize.
7. **Canary, delayed harm, and rollback (RC-13, RC-14, RC-15).** Candidate and release machines **MUST** separate pending approval, queued, running, paused, failed, passed, aborting, rollback pending/running/failed, rollback verified, expired, revoked, and retired states. Shadow-to-canary and every widening **MUST** require approval of an immutable rollout manifest containing cohort, exposure ceiling, action/effect classes, budgets, guardrails, observation windows, minimum samples, telemetry freshness, stop rules, owner, and kill switch. Widening without new approval **MUST** deny. Missing metrics or inconclusive results **MUST** pause/freeze, not pass. Promotion **MUST** bind a tested compatible last-known-good digest, migration/compensation and reversibility evidence, drill freshness, owner, and RTO. Rollback completes only as `ROLLED_BACK_VERIFIED` after exact observed digest plus health-window evidence; late breaches **MUST** freeze/revoke and trigger rollback policy.
8. **Privacy and contribution (RC-16).** Outcome/eval/export records **MUST** be typed and include tenant, data class, provenance, purpose, consent or license, owner, residency, retention deadline, legal hold, redaction/filter version and receipt, and export approval. Raw webhook/prompt/customer content **MUST** be minimized, encrypted, access-controlled, TTL-bound, and excluded from normal logs/artifacts. Cross-repo contribution **MUST** default to redacted aggregates or reviewed immutable cases. Deletion and legal-hold workflows **MUST** preserve only the minimum safe audit metadata and prove ordinary recovery paths cannot restore deleted content.
9. **Objective enablement gate (RC-17).** Self-improvement **MUST** remain separately feature-flagged off. A versioned acceptance manifest **MUST** map every state, edge, invariant, actor, digest, evidence condition, fault, cleanup, privacy, tenant, cancellation, retry/stale case, and terminal behavior one-to-one to executable tests. Mutation/property/stateful, fault-injection, private-holdout access-audit, tenant/privacy, and rollback-drill suites **MUST** pass. An independent reviewer **MUST** reproduce closure with zero critical/high findings before any canary. Medium exceptions **MAY** proceed only with a named owner, bounded constraint, expiry, and explicit future gate.

## Required data, schema, and state contracts

| Contract | Minimum required fields/invariants |
|---|---|
| `TenantScope` | `tenant_id`, `repository_id`, `installation_id`, immutable registration revision; composite FK root; deny foreign substitution. |
| `PrincipalAuthority` | `issuer`, canonical `subject`, assurance, tenant, role/capability, role-policy revision, authenticated session ID, issued/expiry/revoked state. |
| `ApprovalRecord` | authority above; kind/purpose/action; tenant/work item; exact subject plus candidate/artifact/config/policy/eval/rollout/environment digests; source review; ordered quorum set; independence result; finite expiry; invalidation/revocation; signature/receipt. Append-only. |
| `CommandCatalogEntry` / `RunContext` | catalog digest and command ID; typed argv schema; path/env/egress/secret/budget bounds; issuer/key/audience; tenant and aggregate; attempt/fence/cancellation epoch/nonce/time; all input digests; signature. |
| `EffectIntent` / `Attempt` / `Receipt` | tenant/work item, immutable intent digest/payload/key/destination; state revision; one active attempt; dispatcher identity; remote request ID; observation/receipt bound by composite effect+attempt key; `UNKNOWN` resolution decision. |
| `EvalCase` | case/revision, fixture ref, oracle/invariants, risk/slices, public/private/temporal split, provenance/consent/license/privacy/retention, curator/adjudication, retirement, digest. |
| `EvidenceBundle` | candidate/baseline/dataset/evaluator/harness/environment/policy digests; signer/build provenance; expected and received shards; trials/seeds; slice numerator/denominator/CI; invariant results; failures and raw refs; cost; freshness; `PASS\|FAIL\|INCONCLUSIVE`; signature. |
| `RolloutManifest` | candidate and release digest; cohort/exposure/action classes; time/cost/error budgets; guardrails/telemetry/SLO; minimum sample/window; widening revision; kill switch; owner; approval digest; expiry. |
| `RollbackManifest` | current and last-known-good digests; compatibility envelope; migration/compensation/reversibility; drill receipt/time; RTO; authority; observed restore and health receipts. |
| `PrivacyFilteredOutcome` / `ExportEnvelope` | tenant, lineage, classification, purpose, consent/license, residency, retention/legal hold, redaction version/receipt, opaque storage reference, dual-owner export/import decisions. Free text is forbidden in shared envelopes by default. |
| State event | immutable event ID, tenant/aggregate/revision, source/target, actor authority, expected revision/fence, causation/correlation, all decision digests, evidence refs, outcome/reason, timestamps; append plus outbox in one transaction. |

The implementation plan **MUST** use orthogonal candidate, release, attempt, and control-health machines rather than one overloaded `stage`. Required notable states include `CANARY_PENDING_APPROVAL`, `CANARY_RUNNING`, `CANARY_PAUSED`, `CANARY_FAILED`, `CANARY_PASSED`, `PROMOTION_PENDING`, `PROMOTION_FROZEN`, `METRICS_UNAVAILABLE`, `EVIDENCE_STALE`, `ABORTING`, `ROLLBACK_PENDING`, `ROLLING_BACK`, `ROLLBACK_FAILED`, `ROLLED_BACK_VERIFIED`, `EXPIRED`, `REVOKED`, and `RETIRED`.

## Implementation entry and exit tests

### Entry tests (must fail before capability work starts)

- Apply migrations to a disposable PostgreSQL instance and run hostile fixtures proving the current shared role can see both tenants, directly promote a candidate, mutate an effect, create multiple unfinished attempts, and cross-bind a receipt/foreign key. Preserve these as regression tests.
- Run malicious desired-config fixtures for network default allow, production secrets, admin GitHub permission, unknown/unrestricted tool, weakened inherited deny, registry path escape, `.yaml` syntax error, mutable action, `write-all`, privileged `pull_request_target` checkout, fork secret use, and expression-to-shell.
- Run Python contract fixtures for forged human kind, absent expiry, alias self-approval, invented evidence hashes, unsigned/wrong-audience context, canary without admission, promotion without rollback, and instant `ROLLED_BACK`.
- Produce a matrix gap report from the research lifecycle catalog. Entry is complete only when every uncovered cell has a test ID and implementation owner; the capability stays disabled.

### Exit tests (production/pilot admission)

- **Tenant/role matrix:** under every role and prepared-statement/owner-bypass variant, cross-tenant SELECT/INSERT/UPDATE/DELETE, FK substitution, queue/idempotency collision, artifact URI access, and eval contribution fail. An approved dual-owner export/import is the sole positive cross-tenant case.
- **Approval matrix:** wrong issuer, kind, role, quorum, purpose, tenant/item, SHA, artifact, eval, rollout, environment, expiry, revocation, reused review, alias self-approval, curator/evaluator/promoter conflict, and stale role all fail; one exact authorized decision succeeds once.
- **State/concurrency:** direct table DML fails; guarded sequential transitions succeed once; CAS races have one winner; stale fence/cancellation blocks writes/effects; crash/out-of-order/duplicate inputs converge without skipped success. Every state has entry, exit, cancellation, stale/retry, cleanup, and terminal behavior.
- **Effect recovery:** payload/key mutation, blind `UNKNOWN` requeue, two live attempts, and cross-effect receipt fail. Crash-before/after-send tests reconcile remote observed state and never duplicate a non-convergent effect.
- **Context/tool security:** unsigned, altered, expired, replayed, wrong-key/audience/tenant, revoked epoch, stale fence, injected command ID, metacharacters, substitution, newline, environment expansion, and path escape all fail before sandbox execution.
- **Eval/Goodhart:** invented suite, wrong signer/builder, stale/nonced replay, incomplete shard/denominator, zero/insufficient trials, changed evaluator/environment, contaminated holdout, selected-away failure, forged boolean, failed invariant, and inconclusive run all deny. Holdout queries are audited and candidate access fails.
- **Canary/rollback:** admission without exact rollout approval, budget/cohort widening, missing telemetry, every guardrail breach, approval expiry, and post-cancel effect all pause/abort. Inject rollback failure and stale receipts. Only observed exact last-known-good digest plus a completed health window yields `ROLLED_BACK_VERIFIED`.
- **Privacy/retention:** seed PII/secrets and prove filter/redaction, tenant denial, export rejection for free text/unlicensed data, TTL deletion, legal-hold override, cryptographic/object deletion, and non-recovery from normal logs/caches/artifacts.
- **Supply chain/config:** changed wheel hash, missing transitive dependency, unapproved index/image/action, hostile pre-existing role, and each policy-escalation fixture fail. Full-SHA/digest approved fixtures pass.
- **Closure:** generated coverage is 100% over the versioned acceptance manifest; removing each guard causes mutation tests to fail; focused suites and full suite pass; independent review reports zero critical/high and records every medium owner/gate.

## Residual uncertainty and blockers

1. There is no controller, ingress, GitHub App broker, capability proxy, sandbox launcher, evaluator service, object store, merger, deployer, promoter, or canary platform to test dynamically. Their contracts remain unverified.
2. The SQL exploits reproduced on fresh PostgreSQL 16, but corrected migrations and RLS do not yet exist. Exit tests must still run on every exact supported PostgreSQL version and cover RLS owner, `BYPASSRLS`, `SECURITY DEFINER`, prepared statement, pooled-connection reset, partition, and backup/restore cases.
3. External GitHub rulesets, CODEOWNERS enforcement, App installation permissions, environment protection, bypass lists, IdP roles, key/secret stores, and object-store policy were not observable. Admission must reconcile effective remote controls, not accept repository declarations.
4. The validator dependencies are absent from `.venv`; another available environment can run it, but the named main test environment cannot reproduce the gate. A locked, digest-pinned validator environment is a blocker.
5. No source establishes a universal canary sample/window or proves that graders predict production value. Each risk class must predeclare power/non-inferiority, minimum samples/windows, and hard safety rules. Rare, delayed, irreversible, and cohort-specific harm remains possible.
6. No finite suite proves correctness or prompt-injection immunity. Isolation, narrow authority, independent evidence, monitoring, and automatic abort remain necessary after admission.
7. Until RC-01 through RC-17 pass their exit gates, **multi-tenant operation, mutating agent execution, canary exposure, promotion, and claims of production readiness are blocked**.

## Evidence URLs

Primary and validated research support for the corrections:

- GitHub Actions secure use and least privilege: https://docs.github.com/en/actions/reference/security/secure-use
- Preventing privileged `pull_request_target`/artifact “pwn request” patterns: https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/
- GitHub artifact attestations: https://docs.github.com/en/actions/concepts/security/artifact-attestations
- GitHub deployment environments and review limits: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- GitHub App installation tokens: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app
- OWASP prompt injection and excessive agency: https://genai.owasp.org/llmrisk/llm01-prompt-injection/ and https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
- OpenAI evaluation best practices: https://developers.openai.com/api/docs/guides/evaluation-best-practices
- Anthropic agent evaluation guidance: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Google SRE canary design: https://sre.google/workbook/canarying-releases/
- Argo Rollouts analysis/canary/rollback: https://argo-rollouts.readthedocs.io/en/stable/features/analysis/ , https://argo-rollouts.readthedocs.io/en/stable/features/canary/ , https://argo-rollouts.readthedocs.io/en/stable/features/rollback/
- Stateful property testing and bounded formal checking: https://hypothesis.readthedocs.io/en/latest/stateful.html and https://lamport.azurewebsites.net/tla/tla.html
- SLSA provenance and verification: https://slsa.dev/spec/v1.2/provenance and https://slsa.dev/spec/v1.2/verifying-artifacts
- PostgreSQL row-level security: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- PostgreSQL foreign keys and role security: https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK , https://www.postgresql.org/docs/current/role-attributes.html , and https://www.postgresql.org/docs/current/role-membership.html
- Secure Python dependency installation: https://pip.pypa.io/en/stable/topics/secure-installs/
- Signed context standards and implementation guidance: https://www.rfc-editor.org/rfc/rfc7515 and https://www.rfc-editor.org/rfc/rfc8725
- Kubernetes multi-tenancy limits: https://kubernetes.io/docs/concepts/security/multi-tenancy/
- OpenTelemetry sensitive-data handling: https://opentelemetry.io/docs/security/handling-sensitive-data/
- NIST AI RMF GenAI Profile: https://doi.org/10.6028/NIST.AI.600-1
- Benchmark leakage challenge evidence (SWE-Bench+): https://arxiv.org/abs/2410.06992
- Prompt-injection benchmark challenge evidence (AgentDojo): https://arxiv.org/abs/2406.13352
- GDPR source for minimization/retention governance: https://eur-lex.europa.eu/eli/reg/2016/679/oj

These sources support design mechanisms and risk arguments. They do not certify this repository or remove the blockers above.
