# Round 1 resolution memo: evidence integrity and human experience

## Scope and resolution rule

This memo resolves `evidence-integrity.json` and `human-experience.json` under `review-protocol.md`. It is a plan-only deliverable. It does not treat the absence of a production controller as a defect and does not authorize prototype implementation.

I reproduced the findings against the checked-in research, plan documents, schemas, SQL, Python models, examples, and CLI. I parsed all 23 validated research result files: 10 base, 8 lifecycle-extension, and 5 domain-extension results. On the review clock (`2026-09-12T17:19:16Z`), all 23 results had `as_of: 2026-09-13`; hundreds of source records also claimed that future access date. The current GitHub concurrency page was fetched successfully on 2026-09-12 and describes both `queue: single` and `queue: max`.

Resolution totals: **6 verified root causes, 14 confirmed findings, 1 partially-confirmed finding, 0 rejected findings, and 1 duplicate finding**.

## Verified root causes

### RC-1 — Research time provenance is not tied to an observed run

All 23 result files and the report use a 2026-09-13 cutoff while the audit ran on 2026-09-12. A requested cutoff was copied into provenance fields as if retrieval had already happened. Living pages have no retained digest or snapshot that would disambiguate observation time from intended scope.

### RC-2 — Evidence is not represented as one complete, typed claim/source graph

`report.md` says its evidence set is 10 JSON results and `evidence-matrix.md` has 10 data rows, while the expanded scope contains 23 results. Records are heterogeneous: `sources`, `primary_evidence`, and `independent_evidence` occur as object lists, bibliography strings, or large prose strings. The factory schema and `.agent-os/bin/validate.py` check shape/presence but do not define claim-to-source edges, lineage independence, support/refute direction, snapshot integrity, or conflict closure. This also explains repeated METR citations being counted without a common work identity.

### RC-3 — Platform-fact, architecture-inference, and local-outcome claims are not versioned separately

The final report, ADR, and security plan retain the old unconditional GitHub Actions “one pending/arbitrary ordering” statement. Current official documentation distinguishes default `queue: single` from `queue: max` (up to 100 pending and FIFO by wait-start time, while actual start timing means ordering is not guaranteed). The need for a transactional fenced lease remains supported, but the capability statement is overbroad. The matrix also uses `High` without consistently distinguishing documented primitives from an untested composition. The confidence issue is partial because the report does explicitly disclose that no controller or target-repository benchmark was run.

### RC-4 — The plan has no nominated contract authority or phase-local gate semantics

The checked-in JSON Schemas accept the YAML factory/config/decision examples, but the package CLI uses incompatible Pydantic models. Reproduction commands all exited 1:

- `.venv/bin/agent-os config-validate`
- `.venv/bin/agent-os factory-validate .agent-os/factories/ideation.yaml`
- `.venv/bin/agent-os decision-validate .agent-os/factories/example.conversation-decision.json`
- `.venv/bin/agent-os demo --factory .agent-os/factories/ideation.yaml`

The factory schema models guards and gates as untyped strings. Every normal factory edge uses the same global guard, so a literal evaluator can require final approval, lease, or verification before the phase that creates it.

### RC-5 — Durable lifecycle contracts omit normal wait, repair, maintenance, and recovery paths

The maintenance factory omits the documented correlation, suppression/expiry, scheduling, observation, resurface, rollback, and resolution states. Ideation exhausts into undeclared `NEEDS_CLARIFICATION`. Build and ticket review omit normal request-changes loops. The canonical `BLOCKED` state cannot return to `VERIFYING`, `REVIEW`, or `MERGE_QUEUED`, despite `docs/architecture.md` promising resume to a saved prior state. Neither project fields nor `work_items` store the owner, deadline, prior state, notification state, or resume token needed to honor that promise.

### RC-6 — Human authority and interaction are prose, not executable plan contracts

The consumer schema forbids role bindings even though operations requires them. Conversation decisions allow `status: answered` with `answer: null` and allow an unknown `option_id`; both mutations produced zero Draft 2020-12 schema errors. The approval schema allows `purpose: exception` but cannot encode scope, reason, controls, follow-up, or a required candidate SHA. There is no shared bounded notification/silence policy. These gaps prevent deterministic recipient resolution, authorization, reminders, escalation, and fail-closed resumption.

## Finding mapping

| Finding | Severity | Resolution | Root cause | Reproduction result / reason |
|---|---:|---|---|---|
| EVID-001 | High | **confirmed** | RC-1 | Audit clock was 2026-09-12; all 23 `as_of` values and the report cutoff are 2026-09-13. Source records also assert future access. |
| EVID-002 | High | **confirmed** | RC-2 | Report explicitly says “all 10 JSON results”; matrix has 10 rows; 13 extension results are absent from the synthesis. |
| EVID-003 | Medium | **confirmed** | RC-3 | Current official page documents `queue: single` and `queue: max`; report/ADR/security use an unconditional older limitation. Lease conclusion still stands. |
| EVID-004 | High | **confirmed** | RC-2 | Research field runtime types vary across strings/lists/objects; no versioned claim/source graph or semantic independence/conflict predicates exist. |
| EVID-005 | Medium | **duplicate-of EVID-004** | RC-2 | METR arXiv and blog URLs identify the same study across multiple items. Missing family identity is the lineage defect already resolved by EVID-004. |
| EVID-006 | Medium | **partially-confirmed** | RC-3 | `High` can be read as composition confidence, but the report also expressly says the controller and local benchmark were not run. Separate confidence dimensions are still required. |
| HX-002 | High | **confirmed** | RC-4 | All four documented CLI reproduction commands fail with Pydantic shape errors. |
| HX-003 | High | **confirmed** | RC-4 | Global prose guards include artifacts unavailable at early phases; schema supplies no phase-local predicate semantics. |
| HX-013 | High | **confirmed** | RC-6 | `consumer.schema.json` has no role bindings and has `additionalProperties: false`; operations requires risk/owner bindings. |
| HX-006 | High | **confirmed** | RC-5 | Maintenance factory state/artifact set does not implement the durable maintenance lifecycle in architecture and operations. |
| HX-007 | Medium | **confirmed** | RC-5 | Ideation retry target is absent from `phases` and has no entry/resume transitions. |
| HX-008 | Medium | **confirmed** | RC-5 | Canonical lifecycle permits review repair; build and ideation factories do not. |
| HX-009 | High | **confirmed** | RC-5 | `BLOCKED` lacks complete return edges and durable wait metadata despite the documented saved-state promise. |
| HX-010 | Medium | **confirmed** | RC-6 | `answered` plus null answer and a nonexistent option both pass the JSON Schema. |
| HX-011 | Medium | **confirmed** | RC-6 | Exception-specific evidence is absent and rejected as additional properties; `candidate_sha` is optional. |
| HX-014 | Medium | **confirmed** | RC-6 | No common delivery, acknowledgement, batching, cadence/cap, dedupe, escalation, quiet-hours, or timeout contract exists. |

## Exact normative plan corrections

### PC-1 — Evidence run and provenance

1. The plan **MUST** define one immutable `research_run` with `run_id`, `scope_cutoff`, `started_at`, `completed_at`, validator version, and audit clock. `scope_cutoff` **MUST NOT** be used as a retrieval timestamp.
2. Every source observation **MUST** record an actual UTC `retrieved_at` not later than validation time, resolved URL, HTTP/result status, content digest, and either an immutable snapshot reference or an explicit `snapshot_unavailable_reason`.
3. Validation **MUST** fail future retrieval times, observations outside their run, missing material-source digests, and reports built from an incomplete or different run.
4. Living sources **SHOULD** be re-fetched at release review. Versioned primary artifacts **MAY** retain a repository commit or standards version instead of a page snapshot when that identity is immutable.

### PC-2 — Complete evidence graph and synthesis

1. The final plan **MUST** regenerate `report.md` and `evidence-matrix.md` from all 23 outline items, not only the base 10.
2. Every normative architecture decision **MUST** link to stable claim IDs. Every material claim **MUST** link to one or more source observations with `supports`, `refutes`, or `context_only` scope.
3. Sources **MUST** have canonical work identity, publisher/owner, source class, vendor relationship, and `evidence_family_id`. Independent corroboration **MUST** count unique evidence families, not URL or local-ID occurrences.
4. The matrix **MUST** preserve conflicts, unsupported claims, transfer assumptions, and explicit unknowns. Vendor capability pages **MUST NOT** establish efficacy, safety, legal compliance, or ROI by themselves.
5. The METR arXiv paper and METR blog page **MUST** resolve to one evidence family. Per-claim reuse **MAY** remain visible but **MUST NOT** increase the independent-study count.

### PC-3 — Versioned claims and confidence

1. The concurrency claim **MUST** identify the observed documentation date and distinguish default `queue: single` from `queue: max`, including each mode's queue/cancellation/order limits.
2. The plan **MUST** retain the narrower conclusion that neither mode supplies a renewable lease, fencing token, transactional work-item admission, or dependency-aware durable orchestration.
3. Each decision confidence record **MUST** separately rate `primitive_fact`, `architectural_inference`, and `local_outcome`; an outcome **MUST** remain `unvalidated` until target-repository security, failure, recovery, tenant-isolation, and operational pilots pass.
4. Conflict resolution **SHOULD** name affected document versions and superseded wording. A dated compatibility appendix **MAY** retain old platform modes when still relevant.

### PC-4 — Authoritative artifacts and factory compiler

1. The plan **MUST** nominate one versioned source of truth per artifact (`config`, `factory`, `conversation_decision`, `approval`, `consumer`, and generated runtime model). JSON Schema and language models **MUST** be generated from it or checked for semantic equivalence.
2. A factory transition **MUST** reference typed gate IDs, not a global prose guard. Each gate **MUST** declare required input artifact types and revisions, producing phase, evaluator, outcome, failure state, and audit receipt.
3. A transition **MUST NOT** require an artifact first produced by a later phase. Deferred gates **MAY** be declared, but **MUST** name the phase where they become binding and **MUST NOT** authorize the earlier transition.
4. The plan **MUST** specify compiler failures for unknown phases/gates/artifacts, forward references, unreachable nonterminal states, missing cleanup, absent cancellation, and incompatible schema versions.

### PC-5 — Complete lifecycle and wait behavior

1. The maintenance contract **MUST** represent `SIGNAL_RECEIVED`, `CORRELATED`, `DIAGNOSED`, `PROPOSED`, `SCHEDULED`, `EXECUTING`, `VERIFIED`, `OBSERVING`, and `RESOLVED`, plus `SUPPRESSED`, `BLOCKED`, `CANCELLED`, and `ROLLED_BACK` with expiry/resurface and follow-up behavior.
2. Ideation **MUST** have a declared `NEEDS_INPUT` or `NEEDS_CLARIFICATION` state with legal enter, answer/resume, expiry, withdrawal, and cancellation paths.
3. Build review **MUST** support `REVIEW -> IMPLEMENT`; ticket review **MUST** support `TICKET_REVIEW -> SYNTHESIZE` or `CLARIFY`. Any changed artifact **MUST** create a new revision/digest and invalidate stale approval.
4. Every nonterminal state **MUST** have defined legal success, block/wait, cancellation, retry/stale, cleanup, and terminal behavior. Repair loops **MUST** have bounded budgets and a deterministic exhaustion state.
5. `BLOCKED` and other waits **MUST** resume only to the recorded prior state, then re-evaluate all affected gates. They **MUST NOT** skip approval or verification.

### PC-6 — Human authority, decisions, exceptions, and notifications

1. A consumer **MUST** bind every required role to authenticated provider/org/repository principals before compilation. Bindings **MUST** include eligible roles, scope, teams/principals, separation constraints, quorum, fallback/on-call, validity, and provenance and **MUST** be included in the effective-config digest.
2. An answered conversation decision **MUST** contain an attributable answer event, an authorized actor, a timely decision, and either a declared `option_id` or an explicit typed override with rationale. Open/expired/withdrawn decisions **MUST NOT** authorize resume.
3. Exceptions **MUST** bind an exact subject and candidate SHA where code is affected, bounded scope, rationale, compensating controls, owner, incident/follow-up, issue and expiry, revocation, and non-waivable controls. An agent **MUST NOT** grant its own exception.
4. One typed human-interaction policy **MUST** govern every human-needed wait. It **MUST** define severity, channel, recipient resolution, digest-bound action, acknowledgement, batch key/window, reminder cadence/cap, dedupe key, due time, escalation, quiet-hours behavior, expiry, and fail-closed pause/cancel outcome. Silence **MUST NOT** imply consent.
5. Lower-risk informational notices **MAY** be batched. Safety-critical escalation **MAY** override quiet hours only when the policy names the severity and recipient.

## Required data, schema, and state contracts

| Contract | Minimum required fields and invariants |
|---|---|
| `research_run.v1` | `run_id`, scope/item IDs, `scope_cutoff`, `started_at`, `completed_at`, audit clock, generator/validator versions, output digest; all result/report records reference the same completed run. |
| `source.v1` / `source_observation.v1` | Stable source and observation IDs, canonical work ID, title, authors/publisher/owner, source/vendor class, family ID, URL/resolved URL, publication/version, actual retrieval time, result status, digest/snapshot; retrieval cannot be in the future. |
| `claim.v1` / `claim_evidence_edge.v1` | Claim text/scope/version, claim class, decision IDs, uncertainty, edge direction and quoted locator; referential integrity, conflict state, and unique-family independence count. |
| `decision_confidence.v1` | Separate primitive, inference, and local-outcome ratings; basis claim IDs, pilot evidence, promotion requirement, last-reviewed time. |
| `factory.vNext` | Stable phase/artifact/gate/transition IDs; typed inputs/outputs; phase-local gates; entry/exit/cancel/retry/stale/cleanup rules; budgets; terminal states; no undeclared or unreachable state. |
| `role_binding.v1` | Provider/org/repository/tenant scope, role, authenticated principal/team, eligibility, quorum, separation-of-duty constraints, fallback/on-call, valid-from/to, provenance and digest inclusion. |
| `wait.v1` | Wait ID/type, work item and factory, prior state, reason and missing fields, owner principal/role, created/due/expiry, policy ID, notification/dedupe/ack state, escalation route, resume token/version and terminal timeout action. |
| `conversation_decision.vNext` | Revision/digest, question, bounded options, recommendation/evidence, owner, deadline, status-conditional answer, authenticated actor, answer event, option membership or typed override, resume target/token. |
| `exception.v1` | Exact subject/digest/SHA, action and bounded scope, reason, controls, owner/approvers/quorum, incident/follow-up, issue/expiry/revocation, non-waivable-control evaluation and use receipt. |
| `human_interaction_policy.v1` | Severity-to-channel mapping, recipient resolution, digest action, ack, batching, reminder cap/cadence, stable dedupe, due/expiry, quiet hours, escalation, unavailable-owner fallback and fail-closed outcome. |
| `maintenance_signal_group.v1` | Authenticated signals and source revisions, correlation key, dedupe lineage, suppression owner/reason/expiry, diagnosis, schedule, remediation/build link, verification and observation windows, rollback/resurface/follow-up. |
| State/event contract | Expected aggregate version, prior/current state, artifact revisions, gate receipts, actor, UTC time, idempotency key and resume token. Invalid transitions, stale tokens/approvals, and missing required roles fail closed. |

## Implementation entry tests

These tests gate implementation work; they do not require code in this plan PR.

1. **Corpus coverage:** enumerate all three outlines and prove that all 23 item IDs occur in the generated report/matrix and every normative plan decision has a claim edge.
2. **Clock/provenance negatives:** reject future `retrieved_at`, absent run identity, material living source without digest/snapshot disposition, and a report mixing runs.
3. **Lineage negatives:** collapse both METR URLs to one family; reject duplicate URL/publisher lineage presented as two independent sources, vendor-only “independent” support, uncited claims, and unresolved contradictions presented as settled.
4. **Contract parity:** compile source contracts into JSON Schema and Python/runtime models; validate config, every registered factory, every example, and demo inputs through both paths with identical accept/reject results.
5. **Factory static analysis:** reject unknown gate/state/artifact IDs, future-artifact dependencies, unreachable states, unbounded repair cycles, and missing cancel/cleanup behavior.
6. **Authority completeness:** reject a consumer missing any role used by the intervention/risk matrix, ambiguous team membership, removed/expired principals, self-conflicting roles, and insufficient quorum.
7. **Human record negatives:** reject answered/null, unknown option without typed override, missing answer event, unauthorized/expired answer, exception without exact scope/control/owner/expiry, prohibited waiver, and self-grant.

## Implementation exit tests

1. **All-factory traces:** execute happy paths plus every declared invalid edge for ideation, build, maintenance, and deep research. At each edge, assert only phase-available artifacts are required.
2. **Clarification traces:** enter a wait from every nonterminal source, persist owner/deadline/prior state, restart the controller, accept a valid answer, resume the exact saved state, and recheck affected gates; also test expiry, withdrawal, cancellation, stale token, and unavailable owner.
3. **Review repair traces:** run one and multiple request-change rounds, changed head/artifact revision, stale approval invalidation, budget exhaustion, and final acceptance only on the newest digest.
4. **Maintenance traces:** cover duplicate correlation, suppression with expiry, resurface, scheduled remediation, delegation to BUILD, observation success/failure, rollback, cancellation, explicit resolution, and owned follow-up.
5. **Notification traces:** for every human-needed event, simulate answer, duplicate delivery, no response, unavailable principal, quiet hours, and restart. Assert bounded sends, stable dedupe, acknowledgement state, visible ownership/deadline, deterministic escalation/pause, and no consent from silence.
6. **Evidence re-fetch and report build:** run from a clean checkout; validate retrieval timestamps and stored digests; generate the 23-item report/matrix; publish unique-family counts, conflicts, confidence dimensions, and audit output.
7. **Platform claim check:** compare concurrency text with the pinned/observed official page and assert named modes and limits; separately verify that the architecture never treats Actions concurrency as the fenced lease.
8. **Full regression:** after focused tests pass, run schema/config/SQL/Python/end-to-end suites. An independent reviewer who did not author corrections **MUST** verify closure, as required by `review-protocol.md`.

Exit is blocked until there are zero open critical/high findings, every medium is fixed or has an owner and gate, every declared state has complete entry/exit/cancel/stale/retry/cleanup/terminal behavior, invalid transitions and stale approvals fail closed, and the final independent audit finds no new critical/high issue.

## Residual uncertainty

- This audit re-fetched the current GitHub concurrency page, but it did not re-fetch the full source corpus. Availability, page revisions, and claimed retrieval times remain unverified until PC-1 runs.
- A future cutoff or clock mismatch could explain the dates, but it cannot make an unobserved future time valid provenance.
- The exact intended semantics of the prose factory guards are unknown. The checked-in representation is ambiguous even if an eventual compiler author had a safe interpretation in mind.
- The report labels the architecture proposed and not deployed. Reliability, security, human load, cost, tenant isolation, and notification volume remain local-outcome unknowns until pilots and adversarial/fault tests run.
- The package Python tests currently pass, but they do not validate parity with the checked-in JSON/YAML contracts. The standalone `.agent-os/bin/validate.py` could not run in the project environment because its `jsonschema` dependency was absent; this strengthens the need for a clean-install entry test but is not treated as a separate assigned finding.

## Evidence URLs

Primary URLs reproduced or carried by the validated research and directly relevant to these resolutions:

- GitHub Actions concurrency modes and limits: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- Temporal durable workflow message handling: https://docs.temporal.io/encyclopedia/workflow-message-passing
- Temporal workflow execution: https://docs.temporal.io/workflow-execution
- LangGraph durable interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- OASIS WS-HumanTask 1.1: https://docs.oasis-open.org/bpel4people/ws-humantask-1.1-spec-cs-01.html
- GitHub webhook operational guidance: https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks
- Renovate noise reduction: https://docs.renovatebot.com/noise-reduction/
- Prometheus Alertmanager webhook configuration: https://prometheus.io/docs/alerting/latest/configuration/#webhook_config
- Google SRE alerting on SLOs: https://sre.google/workbook/alerting-on-slos/
- NIST SP 800-61 Rev. 3 incident response: https://csrc.nist.gov/pubs/sp/800/61/r3/final
- Kubernetes deployment rollback: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment
- Deep-Research-skills versioned validator: https://github.com/Weizhena/Deep-Research-skills/blob/6ce38f60e3f8b22502c29873f96503a4e0c5addb/skills/research-codex-en/research/validate_json.py
- METR paper identity: https://arxiv.org/abs/2507.09089
- METR publication page for the same study: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- Fencing-token rationale cited by the plan: https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html
