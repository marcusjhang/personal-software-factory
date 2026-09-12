# Round-13 formal/plan correction register

**Status:** narrow formal PLAN/manifest correction and current-digest candidate-only material-graph regeneration complete. This memo does **not** claim independent closure, implementation, exhaustive reachable-product proof, semantic evidence validation, or production safety.

## Scope and counts

All **3/3 raw high findings** in all **5/5** `review/round-13-closure/*.json` files are mapped below. The source reviews report **0 critical and 3 high**. `R13-FM-001` and `R13-XC-001` report the same IC24 rollback-dispatch defect, so the inventory represents **2 unique defects**. The corrected normative manifest contains **787 unique edge rows**: **96 canonical** and **691 private/product** rows. No research source-evidence record or evidence-edge semantic relation changed; generated graph metadata, current-source digests, checkpoint, and coverage locations were regenerated.

## Finding map

| Raw finding | Unique defect | Formal correction | Status |
|---|---|---|---|
| `R13-IR-001` | Already-reconciling unsettled degradation interrupt | Added exact `IH01-WR` and `IH01-PR` rows for `HEALTHY` tuples already in `WIDENING_RECONCILING` or `PROMOTION_RECONCILING` after IC24-A or IC32-UW/UP while the exact original Effect remains UNSETTLED. Each atomically changes health to `TELEMETRY_DEGRADED`, preserves exact Effect identity/state and reconciliation rollout, fences every remaining grant/authority/send, stops or quiesces the child, and creates no rollback or cleanup before X/N. A degraded tuple continues only through matching IH06 X/N; without the health interrupt, candidate-specific IC24/IC32 X/N owns settlement. The derived interrupt equality and before/after initiation/settlement witnesses include both rows. | Mapped in formal text; generated equality/race execution pending |
| `R13-FM-001` | IC24 protected-X legal rollout exit and rollback dispatch | IC24-RWX now atomically takes `WIDENING_RECONCILING->CANARY_ABORTING` with rollback `IDLE->REQUESTED` and immutable `WIDENING_ABORT` origin. IC24-RPX atomically takes `PROMOTION_RECONCILING->FAILED` with rollback `IDLE->REQUESTED` and immutable `CANDIDATE_REVOCATION` origin. Both preserve exact original Effect/reconciliation identity, use exact `BLOCKED>ROLLBACK_REQUESTED` canonical adjacency, require no unrelated revoke, and produce a tuple that admits IRB01 dispatch. Witnesses exercise both branches and their adjacent races. | Mapped in formal text; generated path/race execution pending |
| `R13-XC-001` | Same IC24 protected-X legal rollout exit and rollback dispatch defect as `R13-FM-001` | Mapped to the same atomic IC24-RWX/RPX rollout, rollback, origin, adjacency, replay/conflict, no-unrelated-revoke, and IRB01-dispatch correction. The duplicate raw ID remains explicit. | Mapped in formal text; generated path/race execution pending |

## Preserved coverage and pending gates

The correction preserves all earlier mappings and contracts, including exact Effect identity, the IC24/IC32 protected X/N partition, one rollback saga, immutable rollback origin, sole cleanup ownership, cancellation priority, rollback-safety block release, BUILD/MAINTENANCE settlement, A11 reclaim ordering, immutable terminals, and research publication paths. Requirements remain structurally mapped **16/16**.

The schema-3 candidate-only material graph now binds the current round-13 PLAN/manifest bytes and all 28 dynamically derived headings. Fresh immutable retrieval, same-run human semantic review, deterministic reviewed-edge regeneration, implementation/full-model checks, production validation, and independent closure re-review remain pending. **No closure is claimed.**

## Validation performed

- Parsed all **5/5** round-13 review JSON files and reproduced the exact high-ID set: `R13-IR-001`, `R13-FM-001`, `R13-XC-001`.
- Parsed **787/787** unique manifest edge IDs with no duplicate and verified every data-row width against its table header.
- Verified `IH01-WR` and `IH01-PR` occur in the exact derived interrupt source equality and in ordering witnesses before/after IC24-A, IC32-UW/UP, and Effect settlement.
- Verified IC24-RWX has synchronized `WIDENING_RECONCILING->CANARY_ABORTING`, rollback `IDLE->REQUESTED`, `WIDENING_ABORT`, and legal `BLOCKED>ROLLBACK_REQUESTED` adjacency.
- Verified IC24-RPX has synchronized `PROMOTION_RECONCILING->FAILED`, rollback `IDLE->REQUESTED`, `CANDIDATE_REVOCATION`, and legal `BLOCKED>ROLLBACK_REQUESTED` adjacency.
- Verified both IC24 protected-X targets satisfy IRB01's prohibition on dispatch from reconciliation rollout states.

## Current formal-source digests

- `PLAN.md`: `012934597727e4946f274a4033fc3f0dc0b2337c224155f4e1535323f8682c1a`
- `docs/state-transition-manifests.md`: `da76752e03a289075e2a02e3614fccd11448899c2dab639621542cf7f7709c05`
