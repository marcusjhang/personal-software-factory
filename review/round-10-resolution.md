# Round-10 formal/plan correction register

**Status:** formal PLAN/manifest correction and current-digest candidate-only graph regeneration complete. This memo does **not** claim independent closure, implementation, full reachable-product proof, semantic evidence validation, or production safety.

## Scope and counts

All **9/9 raw high findings** in all **5/5** `review/round-10-closure/*.json` files are mapped below. The source reviews report **0 critical, 9 high** in total: seven formal-model findings, one improvement-race finding, and one recovery-adversary finding. The evidence/status and requirements/architecture reviews reported no critical/high findings. The corrected manifest contains **764 unique edge rows**: **96 canonical** and **668 private/product** rows.

## Finding map

| Raw finding | Formal correction | Status |
|---|---|---|
| `R10-FM-001` | PLAN §14.0 now includes `WIDENING_RECONCILING` and `PROMOTION_RECONCILING`. The manifest declares the same closed rollout set, and validation requires exact PLAN/manifest set equality. | Mapped in formal text; generated check pending |
| `R10-FM-002` | Added tightly guarded canonical safety edges and changed every post-reconciliation X row to exact `BLOCKED>ROLLBACK_REQUESTED`; N rows use exact `BLOCKED>CLEANING`. | Mapped in formal text; model regeneration pending |
| `R10-FM-003` | `IH01-WV/PV` cover degradation after durable E06 but before IR38/IR18. Verified application is protected X, degradation and fencing commit with rollback, and N is forbidden. | Mapped in formal text |
| `R10-FM-004` | IC32 now covers the actual generated rollout coordinates, canary abort active/settled rollback states, pre-promotion exposure, reconciliation entered before revocation, X/N/unsettled classes, no-duplicate rollback, stop/quiescence/replay, and exact cleanup owners. The checker must compare the actual generated reachable relation for equality. | Mapped in formal text; exhaustive generated equality pending |
| `R10-FM-005` | IR34/IR35 atomically create a generation-bound protected `NoExposureReceipt` only after rechecking that no exposure Effect was dispatched. A possible exposure race rejects and routes to an X rollback row. IR13B witnesses include both paths. | Mapped in formal text |
| `R10-FM-006` | Reducer prose now states the exact cleanup partition: `WIDENING_ABORT+NONE -> IR13C`; other origin plus NONE -> IRB08; pending cancellation -> IX03. | Mapped in formal text |
| `R10-FM-007` | IR13A and the exposed branch of IR13C require rollback state exactly `ROLLED_BACK`, reached through IRB07. Witnesses cover NONE and cancellation. | Mapped in formal text |
| `R10-RACE-001` | Cancellation has a closed safety allowlist with exact unsettled, N, and X variants. IX03 with rollback IDLE requires a protected all-target `NoExposureReceipt`; any exposure/reversible application requires exactly `ROLLED_BACK`. IX01-first and safety-event-first witnesses require one cleanup owner. | Mapped in formal text; exhaustive race execution pending |
| `R10-REC-001` | BUILD and MAINTENANCE use distinct private `ROLLBACK_REMEDIATION_WAIT` states, protected rollback-safety obligations, retained exposure/resources, no generic BLOCKED exits, cancellation adoption without terminality, and RO09 + genuine restoration + independent verification before verified/rolled-back and cleanup/cancellation. Exhaustion, revocation, retry, success, and permanent-wait witnesses are named. | Mapped in formal text; model execution pending |

## Preserved coverage and pending gates

The correction retains prior A11 reclaim ordering, immutable terminals, research publication partitions, remediation generations, Effect reconciliation, final-cleanup ownership, canary generation fencing, and all earlier raw-finding mappings. The schema-3 candidate-only material graph was subsequently regenerated and now matches the current PLAN/manifest digests and all 28 headings.

Formal editorial checks and candidate-only graph regeneration are complete. Pending gates are independent closure re-review and, before Increment 1, fresh immutable retrieval, human semantic review, reviewed-edge regeneration, implementation/model checks, and production validation.

## Current formal-source digests

- `PLAN.md`: `29804814db262399090c60bbd5d6c15527ed9fdce2f72cecce7eea0be9d31063`
- `docs/state-transition-manifests.md`: `d8e3c02cdffd28a7b8c33ab2cb9133ecc5dd4be8e99cf3a251b9ced50af65599`
