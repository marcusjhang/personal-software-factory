# Round 3 plan-contract resolution register

**Scope.** This register covers every finding in all four `review/round-3-closure/*.json` files. “Addressed at plan-contract level” means the revised plan now states a normative contract and future proof gate. It does **not** mean implemented, model-checked, empirically validated, provenance-validated, production-safe, or independently closed. Evidence-file repair and final claim regeneration are required parts of the combined deliverable, not proof that the future fresh-run gate passed. Independent re-review is required; this register does not claim the reviewers’ closure criteria pass.

**Stable references.** Locations use section/clause names, not volatile line numbers. This register supersedes prior line-number parentheticals for locating the revised clauses; it does not rewrite historical reviewer evidence.

## Deduplicated correction groups

| Group | Contract |
|---|---|
| G1 | Complete closed legal-edge manifests and generated oracle |
| G2 | Versioned improvement tuple reducer and synchronized legal projections |
| G3 | Exact four-timestamp database-time lease semantics |
| G4 | Universal tenant plus typed ScopeRef; conditional repository identity |
| G5 | Total R0–R4 × closed-threat sandbox matrix |
| G6 | Signed dual-owner cross-scope export/import dependency envelope |
| G7 | Distinct stage-bound canary, widening, and promotion decisions |
| G8 | Protected principal identity and controlling-relationship resolution |
| G9 | Runtime/Wait terminal, stale, cancellation, and exhaustion relations |
| G10 | Durable UnconfirmedQuiescence saga |
| G11 | Exact UNKNOWN disposition edges and receipts |
| G12 | Cleanup retries, exhaustion, escalation, risk retention, and resurfacing |
| G13 | Exception-driven R0/R1 delegated admission, separate from human issuance |
| G14 | Generic typed owner decision command and editorial/roadmap repair |
| G15 | Evidence provenance wording and mandatory final material-claim regeneration |

## Finding-by-finding mapping

| # | Finding | Severity | Group | Status | Exact revised clause(s) | Plan-contract resolution |
|---|---|---|---|---|---|---|
| 1 | `R3-STATESEC-001` | high | G1 | Addressed at plan-contract level | PLAN “Factory flows and total canonical projection”; normative manifest “Manifest notation and universal rules”, “Canonical work graph v1”, factory §§4–7, “Manifest completeness and generated proof gate” | Publishes every built-in private edge with exact endpoints, guard, canonical sequence/stutter, waits/stale/retry, effects/cleanup, and disposition; forbids wildcard/inference and derives tests from rows. |
| 2 | `R3-STATESEC-002` | high | G2 | Addressed at plan-contract level | PLAN “Improvement: orthogonal protected machines”, “Signed EvidenceBundle and separate enablement decision”, “IMPROVEMENT”; manifest “Improvement product and reducer v1” | Defines one versioned reachable tuple, fail-closed precedence, invariants, synchronized edges, impossible-tuple rejection, and terminal masking prohibition. |
| 3 | `R3-STATESEC-003` | high | G3 | Addressed at plan-contract level | PLAN “Signed bootstrap and execution context”; “Admission and leases”; “Contract and persistence tests” | Lease/context carry `issued_at < renew_by < expires_at <= max_expires_at`; renewal uses DB time; gateways reject at expiry; reclaim starts at renew-by; boundary tests are required. |
| 4 | `R3-STATESEC-004` | high | G4 | Addressed at plan-contract level | PLAN “Durable record catalog”; “One canonical contract and compiler”; “Security, isolation, approvals, sandbox, and supply chain” / “Tenant and scope boundary” | Makes tenant plus typed ScopeRef universal across records/storage/queues/cache/audit/idempotency. Repository identity is required only for engineering/repository and cannot authorize another domain. |
| 5 | `R3-STATESEC-005` | high | G5 | Addressed at plan-contract level | PLAN “Security, isolation, approvals, sandbox, and supply chain” / sandbox profiles, threat definitions, and total selection matrix | Enumerates every R0–R4 × T0–T3 cell, including trusted secretless R2→S3, strongest-wins order, and S4 for conflict/unmatched/unsupported cases. |
| 6 | `R3-STATESEC-006` | high | G6 | Addressed at plan-contract level | PLAN “Dependencies and retries”; “Tenant and scope boundary”; “Adversarial security tests” | Requires exact source/destination ScopeRefs, dual signatures, ports/classes/purpose/consent/expiry/revocation/import receipt; ordering must prove non-disclosure or use the same envelope. |
| 7 | `R3-STATESEC-007` | medium | G7 | Addressed at plan-contract level | PLAN “Signed EvidenceBundle and separate enablement decision”; “IMPROVEMENT”; manifest “Rollout machine v1” | Separates enablement, CanaryAdmissionDecision, WideningDecision, and post-canary PromotionDecision and binds stage-complete bundles, telemetry, purpose, independence, expiry, and exact inputs. |
| 8 | `R3-STATESEC-008` | medium | G8 | Addressed at plan-contract level | PLAN “Architecture and separated authorities”; “Durable record catalog”; “Human-needed decision engine”; “Adversarial security tests” | Defines signed, fresh PrincipalIdentitySnapshot and ControlRelationshipSnapshot, alias/controller/org resolution, conflict fail-close, and decision digest binding. |
| 9 | `R3-STATESEC-009` | high | G9 | Addressed at plan-contract level | Manifest “FactoryInstance aggregate v1”, “NodeRun aggregate v1”, “Attempt aggregate v1”, “Wait aggregate v1” | Gives initial/terminal sets and all explicit answer/expiry/withdraw/cancel/stale/retry/exhaustion/cleanup edges; STOPPED remains unfinished. |
| 10 | `R3-STATESEC-010` | high | G10 | Addressed at plan-contract level | PLAN “Admission and leases”; manifest “UnconfirmedQuiescence saga v1” | Defines actor/quorum, old authority, disjoint proof, isolation attestation, allowed resources, expiry/revoke/monitor/close and keeps old attempt unfinished for shared-resource/terminal checks. |
| 11 | `R3-STATESEC-011` | medium | G11 | Addressed at plan-contract level | PLAN “Effect and reconciliation machine”; manifest “Effect and reconciliation aggregate v1” and “UNKNOWN disposition receipts and work eligibility” | Maps ACCEPT_APPLICATION→ACCEPTED_RISK, DECLARE_FAILED→FAILED_FINAL, and AUTHORIZE_COMPENSATION→COMPENSATION_PENDING under fresh authority; accepted risk stays distinct from verified. |
| 12 | `R3-STATESEC-012` | medium | G12 | Addressed at plan-contract level | PLAN “Review, merge, auto-merge, and cleanup”; manifest “CleanupItem aggregate v1” | Defines bounded retries/exhaustion/CLEANUP_FAILED, authorized disposition, retained-risk monitoring/resurface/remediation, and exact DONE/FAILED/CANCELLED eligibility. |
| 13 | `ROAD-EVID-R3-001` | high | G15 | Addressed at plan-contract level; evidence artifact repair remains part of combined revision | PLAN “Evidence and method”, “Immediate next actions”, and provenance-qualified “Primary sources and supporting research”; final evidence index/cutoff repair | Removes the plan’s unqualified “sources used” wording and preserves the fresh immutable re-fetch/human semantic gate. Timing claims must be labeled unverified in evidence artifacts; no gate is claimed passed. |
| 14 | `ROAD-EVID-R3-002` | high | G15 | Addressed at plan-contract level; final generated artifact required | PLAN “Evidence and method”; “Immediate next actions” item for final claim regeneration; final material-claim artifact | Requires regeneration against exact final PLAN digest, canonical work/source-observation identity, typed support/refute/context edges, superseded-claim versioning, and external-evidence versus local-outcome claim types. |
| 15 | `R3-REQ-001` | high | G13 | Addressed at plan-contract level | PLAN “Human-needed decision engine”; “Admission and leases”; walkthrough READY step | Adds protected, human-issued closed R0/R1 DelegatedAdmissionPolicy and deterministic controller-derived PolicyAdmissionReceipt. All human-needed predicates must be false; changes/expiry/revoke/stop/quota restore human exact-digest gate. |
| 16 | `R3-REQ-002` | high | G2 | Addressed at plan-contract level | Manifest “Improvement product and reducer v1” through “Improvement synchronized checks” | Same tuple reducer closes concurrent projection ambiguity and requires every coordinate edge to project legally or reject. |
| 17 | `R3-REQ-003` | high | G4 | Addressed at plan-contract level | PLAN “Durable record catalog”, artifact envelope in “One canonical contract and compiler”, “Tenant and scope boundary” | Removes universal repository identity from artifact and persistence contracts and applies conditional schema constraints. |
| 18 | `R3-REQ-004` | medium | G14 | Addressed at plan-contract level | PLAN “Normative owner interaction contract” / “Typed factory decision” row | Adds one closed typed decision action for DecisionRecord, ResearchDecision, curation, canary, widening, and promotion with digest/diff, principal/quorum, durable result, stale/error behavior, transition and recovery. |
| 19 | `R3-REQ-005` | low | G14 | Addressed at plan-contract level | PLAN “Reader-visible end-to-end walkthrough” | Walkthrough is consecutively numbered 1–11. |
| 20 | `CEC-R3-001` | high | G1, G2 | Addressed at plan-contract level | PLAN “Factory flows and total canonical projection”; manifest “Improvement product and reducer v1” | Normative transition mapping removes VERIFYING→READY and READY→OBSERVING shortcuts, routes mutation through admission/lease, and makes canary a separately admitted child trace. |
| 21 | `CEC-R3-002` | high | G4 | Addressed at plan-contract level | Same clauses as findings 4 and 17 | One universal tenant+ScopeRef contract now governs artifacts and all persistence namespaces; repository identity is conditional. |
| 22 | `CEC-R3-003` | medium | G15 | Addressed at plan-contract level; evidence artifact repair remains part of combined revision | Same clauses as finding 13 | Plan wording is provenance-qualified and the contradictory legacy timing narrative must be labeled unverified; no semantic/provenance closure is inferred. |
| 23 | `CEC-R3-004` | low | G14 | Addressed at plan-contract level | PLAN walkthrough and Effect reconciliation list; this register’s “Stable references” rule | Both ordered lists are consecutive. Current resolution locations use stable headings/clause names; volatile prior line parentheticals are superseded, not relied upon. |
| 24 | `CEC-R3-005` | low | G14 | Addressed at plan-contract level | README “Status”; PLAN “Sole implementation roadmap” Increment 0; “Immediate next actions” prototype-absence item | Replaces stale archive work with checkout-verifiable absence while preserving review/resolution evidence; no external archive is implied. |

## Count and verification statement

- Findings mapped: **24/24**.
- Severity: **15 high, 6 medium, 3 low**.
- Deduplicated plan-contract groups: **15**.
- Files reviewed for this register: all four round-3 JSON reviews, `PLAN.md`, `README.md`, requirements traceability, round-2 resolution and all round-1 resolution memos.
- Closure status: revised at the **plan-contract level only**. Future compilation, model checking, schema/runtime tests, fresh evidence retrieval, semantic review, pilot evidence, and independent round-3 re-review remain unperformed. This document does not claim the closure criteria pass.
