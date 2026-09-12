# Round-11 formal/plan correction register

**Status:** formal PLAN/manifest correction and then-current-digest candidate-only graph regeneration complete. This memo does **not** claim independent closure, implementation, full reachable-product proof, semantic evidence validation, or production safety.

## Scope and counts

All **9/9 raw high findings** in all **5/5** `review/round-11-closure/*.json` files are mapped below. The source reviews report **0 critical and 9 high**. The corrected manifest contains **776 unique edge rows**: **96 canonical** and **680 private/product** rows. No source-evidence record or evidence-edge semantics changed; generated material-graph metadata and bound digests were regenerated.

## Finding map

| Raw finding | Formal correction | Status |
|---|---|---|
| `R11-REC-001` | Added exact absent-to-OPEN rollback-safety creation rows `RO00-B`, `RO00-M`, and `RO00-I`, invoked atomically by B37, M28, and IRB06. Each transaction changes the Work/tuple and creates the obligation, link, MAINTENANCE child, event, and receipt with deterministic generation, absent-or-same CAS, identical replay, and conflict rejection. These rows require neither CleanupItem nor C11. | Mapped in formal text; generated race execution pending |
| `R11-REC-002` | Made RO09 purpose-specific. Cleanup-resurface closure may unblock only exact keys proved remediated. Rollback-safety RO09 closes the remediation child but retains all blocks through B74/M62 and B34/M25; only B38/M29 remove the exact blocks atomically while sealing `ROLLED_BACK`. | Mapped in formal text; generated ordering proof pending |
| `R11-ER-001` | Reworded the control-health invariant: generic IH01 is outside the active set, while IH01-C/W/WV/A/P/PV/D/O are the sole legal HEALTHY-to-degraded interrupts inside it. Ordinary progress/exposure still requires HEALTHY/current continuity, and every other row rejects after stale health. | Mapped in formal text; generated active-set equality pending |
| `R11-RACE-001` | Added synchronized cancellation rows IX06-E2R/E2Q/E3R/E3Q for exact E02/E03 pre-send Effect settlement. Defined exact `PreExposureCancellationSourcesV1`, generation fencing, child stop/cleanup, precise Effect-set settlement, deterministic once-only all-target NoExposureReceipt creation, replay/conflict semantics, and IX03 as sole cleanup owner. Witnesses cover IX01-before-E02/E03, every source, and child terminal races. | Mapped in formal text; exhaustive race execution pending |
| `R11-XC-001` | The same closed N-classifier contract now includes initial `DISABLED`, `ENABLEMENT_REVIEW`, `CANARY_PENDING_APPROVAL`, unstarted-child `CANARY_READY`, `WIDENING_REVIEW`, `PROMOTION_PENDING_APPROVAL`, and no-send `APPROVED`, with generated source-set equality and an explicit safe-target map. IX03 still requires the protected receipt and never invents it. | Mapped in formal text; generated equality pending |
| `R11-RACE-002` | Added explicit FROZEN-to-REVOKED and EVIDENCE_STALE-to-REVOKED rows plus IC24-A active-rollout digest invalidation. `IC32SafetyPartitionV1` covers every actual X/N/UNSETTLED rollout/Effect/rollback coordinate, fences grants/sends, reuses or creates rollback exactly once, assigns only named later cleanup owners, and excludes impossible tuples. Witnesses include IC30-before-revoke, IC24-before-revoke, and digest change during canary/widening/promotion/observation. | Mapped in formal text; fixed-point generation pending |
| `R11-FS-001` | Split IR13C into `IR13C-X` and `IR13C-N`. The exposed branch requires IR13A and rollback exactly `ROLLED_BACK`, then projects `ROLLED_BACK>CLEANING`; the no-exposure branch requires IR13B and rollback `IDLE`, then projects `REVIEW>CLEANING`. Origin/cancellation ownership remains disjoint. | Mapped in formal text; exact witness execution pending |
| `R11-FS-002` | Added IC32-CA for reachable rollout `FAILED\|RETIRED` cleanup tuples while candidate remains SHADOW_PASSED. It records revocation, preserves the byte-identical CleanupManifest/rollback/origin, creates no rollback or duplicate cleanup, and requires exact stutter/reducer behavior plus before/after fixed-point equality. | Mapped in formal text; fixed-point generation pending |
| `R11-FS-003` | B39/M30 now require no persisted cancellation. B71/M59 require the authenticated persisted cancellation disposition. Their exact-version CAS, replay, and conflict guards are mutually exclusive. Witnesses follow cancellation during remediation through `ROLLED_BACK`, cleanup, and `CANCELLED`. | Mapped in formal text; race execution pending |

## Preserved coverage and pending gates

The correction preserves prior canonical adjacency, A11 reclaim ordering, immutable terminals, Effect reconciliation, research publication paths, canary generation fencing, rollback/cleanup ownership, and all earlier raw-finding mappings. Requirements remain structurally mapped **16/16**.

Formal sources and status/traceability text changed, followed by schema-3 candidate-only material-graph regeneration against the then-current round-11 PLAN/manifest digests and all 28 headings. Fresh immutable retrieval, same-run human semantic review, reviewed-edge regeneration, implementation/full-model checks, production validation, and independent closure re-review remain pending. **No closure is claimed.**

## Round-11 formal-source digests (historical)

- `PLAN.md`: `5b320a71b86912845960ad67081137ed270bdf83d4ea019a32923df041d917ab`
- `docs/state-transition-manifests.md`: `8186b5724f24a60342a40e89d6e8ebb1795cdcbac0700a7dbc0723495dfd2f29`
