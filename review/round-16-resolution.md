# Round-16 formal/status correction register

**Status:** narrow round-16 PLAN/manifest and reader-status correction plus current-digest schema-3 candidate-graph regeneration complete. This memo does **not** claim independent closure, implementation, exhaustive reachable-product proof, semantic evidence validation, production safety, or autonomous self-government.

## Scope and counts

All **4/4 raw high findings** in all **5/5** `review/round-16-closure/*.json` files are mapped below. The source reviews report **0 critical and 4 high**. The four raw findings represent **3 unique defects**. The corrected normative manifest contains **801 unique edge rows**: **96 canonical** and **705 private/product** rows. No research source-evidence record or evidence-edge semantic relation changed; generated graph metadata, source digests, checkpoint, and material-graph bytes were subsequently regenerated for round 16.

## Finding map

| Raw finding | Unique defect | Formal/status correction | Status |
|---|---|---|---|
| `R16-IR-001` | IX revocation lacks an already-reconciling UNSETTLED owner | Added IX06-HUR/HUQ for REQUESTED/QUIESCING revocation from exact `WIDENING_RECONCILING\|PROMOTION_RECONCILING` sources while the original Effect remains UNSETTLED. They map exactly `SHADOW_PASSED\|FROZEN\|EVIDENCE_STALE -> REVOKED`, preserve Effect/reconciliation/rollback/cleanup identities and states and the existing fence, and create no saga or cleanup. `CancellationRevocationCoordinatesV1` now equals the eight-row IX06 union. Pairwise exclusion uses cancellation state, rollout/classifier, revocation trigger, and tuple-version CAS. Witnesses cover revocation before/after IX06-U and before/after settlement. | Mapped in formal text; generated equality/race execution pending |
| `R16-XC-002` | Cancellation-side degradation is undefined without an active generation | Partitioned every HEALTHY REQUESTED/QUIESCING/CLEANING IXH source into exact `ACTIVE_GENERATION` and `NO_ACTIVE_GENERATION` coordinates. The exact `CancellationDegradationReceipt` V1 schema uses canonical nullable generation identity and binds repository/work, cancellation epoch/control event, pre-event tuple, and degradation event without inventing a generation. Source equality covers both partitions; replay and every identity/partition/digest conflict are exact; inactive IX01-before-IH01 witnesses and terminal immutability are explicit. | Mapped in formal text; generated equality/race execution pending |
| `R16-XC-001`, `R16-ER-001` | README labels the historical round-14 graph current | Replaced the stale sentence with the exact historical boundary. Reader status now identifies round-16 formal bytes and matching candidate graph as current and the round-15 graph as historical. The round-15 register is explicitly historical. | Mapped in reader/status text |

## Preserved coverage and pending gates

The correction preserves all earlier mappings and contracts, including cancellation dominance, exact Effect identity, protected X/N classification, one rollback saga, immutable rollback origin, sole parent cleanup and terminal ownership, terminal immutability, and the plan-only boundary. Requirements remain structurally mapped **16/16**.

Current PLAN, normative-manifest bytes, and the matching schema-3 candidate-only material graph are round 16 and cover all 28 headings. Generated witness/full-model execution, generated witness/full-model execution, fresh immutable retrieval, same-run human semantic review, implementation, production validation, and independent closure re-review remain pending. **No closure is claimed.**

## Validation performed

- Parsed all **5/5** round-16 review JSON files and reproduced the exact high-ID set: `R16-IR-001`, `R16-ER-001`, `R16-XC-001`, `R16-XC-002`.
- Parsed **801/801** unique manifest edge IDs with no duplicates and verified Markdown table widths.
- Verified the canonical inventory remains **96** rows and the private/product inventory is **705** rows.
- Verified IX06-HUR/HUQ are canonical stutters and add no canonical projection adjacency.
- Verified the exact revocation union names IX06-UR/UQ/HUR/HUQ/NR/NQ/XR/XQ and the candidate source set remains exactly `SHADOW_PASSED|FROZEN|EVIDENCE_STALE`.
- Verified IXH01-R/Q/C each name the disjoint active/no-active partition; receipt identity uses a canonical nullable generation and no fake generation; terminal sources remain excluded.
- Verified README, traceability, and the historical round-15 register identify current round-16 formal bytes and matching candidate graph.

## Current round-16 formal-source digests

- `PLAN.md`: `31a7c01db2def3d0d708c448dc5f2bbbe60aa53346261e24c2c873ec5bdf6e6f`
- `docs/state-transition-manifests.md`: `7708c3e89309e06f02681a2b5618a56e46c04b6d22daa87f67a2f25f99611917`
