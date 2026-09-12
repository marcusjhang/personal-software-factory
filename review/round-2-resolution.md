# Round 2 finding resolution register

**Scope:** plan-only resolution. “Addressed” means the revised documents specify the required contract and future proof gate. It does not claim implementation, semantic evidence validation, production safety, or autonomous self-government.

All six `review/round-2/*.json` reviews were read. Every one of their 25 findings appears below.

| # | Finding | Severity | Status | Exact revised location | Resolution |
|---|---|---|---|---|---|
| 1 | `ARCH-R2-001` | high | **Addressed** | PLAN §§1 (12), 5 (113–119), 20 (459–479), 21.2/21.4 | PostgreSQL CAS/outbox/restore/two-session race is mandatory before any writer; SQLite is no-write only; RLS/cross-repo proof precedes second repo; Temporal is separate and optional. |
| 2 | `ARCH-R2-002` | medium | **Addressed** | PLAN §5 (86–111), §10 (252–260), §13 (326–328) | Separates record custody, human decision/issuance gateway, runtime validation/consumption and narrow actuator authority in table and diagram. |
| 3 | `ARCH-R2-003` | medium | **Addressed** | PLAN §5 Release 0 envelope (111–113), §20 Increment 2 | Defines atomic journal, clean restart/replay, corruption quarantine/export; excludes host loss and in-flight real effects. |
| 4 | `ARCH-R2-004` | medium | **Addressed** | PLAN §20 (459–479) | Defines IncrementAdmissionDecision and applies IAD-03 through IAD-10 with predeclared metric/evidence, window/sample, denominator, owner, uncertainty, expiry, stop and rollback. |
| 5 | `EVID-R2-001` | high | **Addressed** | PLAN status (3–4), §4 (71–84), §20 Increment 0, §24 item 1 | Calls dates unverified legacy provenance, treats cutoff as intended scope, and blocks implementation on immutable re-fetch plus human semantic review; no unsupported UTC history. |
| 6 | `EVID-R2-002` | high | **Addressed** | PLAN §4 (71–84), §14.4, §21.5 | States 37 structurally validated records only and links manifest, 23-item coverage, material claim graph and evidence repair, preserving conflicts/unknowns without claiming semantic validation. |
| 7 | `STATE-R2-001` | high | **Addressed** | PLAN §§8.1–8.4 (192–242), §14.0 (352–366), §21.1 | Publishes state-based, versioned, total per-factory mapping with every normal/exception state; edges must project to legal canonical edge/stutter. |
| 8 | `STATE-R2-002` | high | **Addressed** | PLAN §8.2 (210–216), §13 Admission and leases (310–315), §21.4 | Defines fence/revoke/stop/quiesce/effect classification before new authority; old compute is effect-gated and isolated; shared resources wait; one unfinished attempt per node across fences. |
| 9 | `STATE-R2-003` | high | **Addressed** | PLAN §8.1 (194–208), §14.0, §21.4 | Uses only REQUESTED -> ROLLING_BACK -> VERIFYING -> VERIFIED -> ROLLED_BACK -> CLEANING; failure blocks/human after bounded retry. |
| 10 | `STATE-R2-004` | medium | **Addressed** | PLAN §8.3 (218–226), §13, §21.4 | Defines zero/one/ambiguous lookup exits, receipts, safe retry authorization, settled classes, human dispositions and compensation UNKNOWN/failure. |
| 11 | `R2-RJ-001` | high | **Addressed** | PLAN §14.0 (352–366), §8.4 | Same total mapping closure as STATE-R2-001, including improvement rejection/freeze/expiry/revocation/retirement. |
| 12 | `R2-RJ-002` | high | **Addressed** | PLAN §20; requirements-traceability §§1–2 | Makes PLAN §20 sole roadmap authority and maps R-01–R-16 to exact increment names/numbers and PLAN sections. |
| 13 | `R2-RJ-003` | high | **Addressed** | PLAN §4, §20 Increment 0, §24 item 1 | Makes fresh-run provenance and human semantic review a pre-implementation gate while accurately using current structural repair artifacts. |
| 14 | `R2-RJ-004` | medium | **Addressed** | PLAN §10.1 (262–284) | Specifies future Issue/CLI commands, views, responses, events, waits, recovery, retention/export, first run and uninstall; no CLI implementation is claimed. |
| 15 | `R2-RJ-005` | medium | **Addressed** | PLAN §10.2 (286–290), §21.3 | Adds narrow separately authenticated break-glass states, allowed emergency actions, non-waivable boundaries, expiry, quarantine, independent retrospective and denial. |
| 16 | `CDD-R2-001` | high | **Addressed** | PLAN §17 (422–432), §21.2 | Defines complete signed ConsumerReleaseManifest over all managed/generated/workflow/action/image/tool/model/schema/migration/policy pins, full rehash verification and signed rollback receipts. |
| 17 | `CDD-R2-002` | high | **Addressed** | PLAN §18 (434–440), §20 IAD-08/IAD-10 | Adds DomainExtractionDecision and GTM scorecards with frozen local metrics/windows/samples/denominators/uncertainty/owners/pass-stop/rollback and no invented universal values. |
| 18 | `CDD-R2-003` | medium | **Addressed** | PLAN §14.4 (380–386), §21.5 | Defines ResearchArtifact/Checkpoint lineage, atomic commit, exact resume eligibility, source comparison, minimal transitive invalidation and stale-dependent completion denial. |
| 19 | `CDD-R2-004` | medium | **Addressed** | PLAN §5.1 (121–136), §18 (434–440) | Uses tenant plus typed domain ScopeRef; repository is mandatory only for engineering repository authority and cannot substitute for other-domain scope/consent. |
| 20 | `SECIMP-R2-001` | high | **Addressed** | PLAN §8.4 (228–236), §14.0 IMPROVEMENT row, §14.5 | Defines orthogonal candidate/release-attempt/control-health machines with explicit pass/fail/pause/abort and verified rollback states and determinate guards. |
| 21 | `SECIMP-R2-002` | high | **Addressed** | PLAN §8.5 (238–242), §14.5, §20 Increments 6–7 | Defines complete signed EvidenceBundle resolved from protected state and separate external enablement flag/decision requiring 100% safety mapping and independent zero critical/high closure. |
| 22 | `SECIMP-R2-003` | high | **Addressed** | PLAN §13 Cancellation/effects (322–328), §10.1, §21.3 | All canonical actor/scope/assurance/role values derive from authenticated session/service identity; payload IDs are assertions that must exactly match; AuthoritySnapshot is bound. |
| 23 | `SECIMP-R2-004` | high | **Addressed** | PLAN §16 sandbox profiles (400–420), §21.3 | Defines S0–S4 closed threat/risk-selected classes, baseline kernel/namespace/egress controls, microVM/VM high-consequence gates and fail-closed attestation. |
| 24 | `SECIMP-R2-005` | medium | **Addressed** | PLAN §12 (300–306), §21.3 | Adds key ID/algorithm/profile, issue/not-before/expiry/audience/nonce, authority-bounded lifetime, rotation overlap, compromise revocation/cache refresh and retired-key rejection. |
| 25 | `SECIMP-R2-006` | medium | **Addressed** | PLAN §5 (109), §14.5, §20 Increments 6–7 | Independence is canonical-principal/controlling-organization based; evaluator and approver dependencies are explicit; solo owner cannot enable canary/promotion. |

## Counts and residual status

- Findings mapped: **25/25**.
- High findings mapped: **15/15**.
- Medium findings mapped: **10/10**.
- Unresolved critical findings in this plan revision: **0** (none were filed in round 2).
- Unresolved high findings at the plan-contract level: **0**.
- Implementation proof remains **0**. External writes stay disabled until the PostgreSQL gate passes. Second-repository work stays disabled until RLS/cross-repository proof passes. Improvement canary/promotion stays disabled until the separate enablement decision and independent-principal gates pass.
- Evidence provenance and semantic support are not claimed complete. They are an explicit pre-implementation gate in PLAN §4 and Increment 0.
