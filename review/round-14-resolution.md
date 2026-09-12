# Round-14 formal/status correction register

**Status:** narrow formal PLAN/manifest and reader-status correction plus current-digest schema-3 candidate-graph regeneration complete for round 14. This memo does **not** claim independent closure, implementation, exhaustive reachable-product proof, semantic evidence validation, production safety, or autonomous self-government.

## Scope and counts

All **5/5 raw high findings** in all **5/5** `review/round-14-closure/*.json` files are mapped below. The source reviews report **0 critical and 5 high**. The five raw findings represent **5 unique defects**. The corrected normative manifest contains **794 unique edge rows**: **96 canonical** and **698 private/product** rows. No research source-evidence record or evidence-edge semantic relation changed in round 14; generated graph metadata, current-source digests, checkpoint, coverage locations, and material-graph bytes were regenerated.

## Finding map

| Raw finding | Unique defect | Formal/status correction | Status |
|---|---|---|---|
| `R14-REC-001` | Release-attempt-only parent cancellation | IA09-IA15 now require matching whole-work IX cancellation context and are canonical stutters under IX dominance. Reducer priority 13 maps attempt-local `CANCEL_REQUESTED\|QUIESCING\|CLEANING\|CANCELLED` to `SAVED`. IA14 schedules attempt-local cleanup only; IA15 seals only an attempt-local terminal. IX03 remains the sole parent cancellation cleanup owner and IX04 the sole canonical parent `CANCELLED` owner. A generated witness forbids every release-attempt-only parent terminal path. | Mapped in formal text; generated path execution pending |
| `R14-IR-001` | Degradation after protected-X rollback creation | Added the exact generated rollback-adoption partition `IH01-RAQ/RAR/RAV/RAD/RAF/RAM/RAO` for HEALTHY protected-X nonterminal active/exposure tuples with matching rollback `REQUESTED\|ROLLING_BACK\|VERIFYING\|VERIFIED\|FAILED\|REMEDIATION_WAIT\|ROLLED_BACK`. Each requires cancellation NONE, changes only health to `TELEMETRY_DEGRADED`, preserves byte-identical Effect, rollout, saga state/identity, immutable origin, blocks and cleanup owner, fences remaining authority, creates no second saga or cleanup, and stutters canonically under rollback/cleanup dominance. Witnesses race after IC24/IC32 X continuations and every rollback advance. | Mapped in formal text; generated equality/race execution pending |
| `R14-IR-002` | Inconsistent interrupt-union equality | PLAN, the manifest invariant, and generated validation now use the identical closed union: IH01-C/W/WR/WV/A/P/PR/PV/D/O plus residual IH01-RX/RN and rollback-adoption IH01-RAQ/RAR/RAV/RAD/RAF/RAM/RAO. Validation requires literal equality, pairwise disjointness, and failure on every omitted or extra guard. | Mapped in formal text; generated equality execution pending |
| `R14-IR-003` | IH06/IX continuation conflict | Every IH06-WX/WN/PX/PN guard now requires `work_cancel_state=NONE`. If IX01 or IX02 wins before settlement, IH06 rejects and the matching IX06 REQUESTED/QUIESCING X/N row exclusively consumes settlement; IX03 remains the sole parent cleanup owner. Exact X/N witnesses race settlement before and after IX01 and IX02. | Mapped in formal text; generated race execution pending |
| `R14-XC-001` | Ambiguous historical/current graph checkpoint | README now calls round 12 and round 13 then-current historical checkpoints and names the current round-14 formal bytes and records graph regeneration as complete. The round-13 register now states the exact historical boundary: no research source-evidence record or evidence-edge semantic relation changed; generated graph metadata, current-source digests, checkpoint, and coverage locations were regenerated. Traceability uses the same status. | Mapped in reader/status text |

## Preserved coverage and pending gates

The correction preserves all earlier mappings and contracts, including exact Effect identity, protected X/N classification, one rollback saga, immutable rollback origin, cancellation priority, sole cleanup ownership, rollback-safety block release, BUILD/MAINTENANCE settlement, A11 reclaim ordering, immutable terminals, and research publication paths. Requirements remain structurally mapped **16/16**.

The current formal sources and schema-3 candidate-only material graph are round 14 and match all 28 dynamically derived headings. Fresh immutable retrieval, same-run human semantic review, deterministic reviewed-edge regeneration, implementation/full-model checks, production validation, and independent closure re-review remain pending. **No closure is claimed.**

## Validation performed

- Parsed all **5/5** round-14 review JSON files and reproduced the exact high-ID set: `R14-IR-001`, `R14-IR-002`, `R14-IR-003`, `R14-XC-001`, `R14-REC-001`.
- Parsed **794/794** unique manifest edge IDs with no duplicate and verified every Markdown data-row width against its table header.
- Verified the canonical graph remains **96** rows and the private/product inventory is **698** rows.
- Verified release-attempt cancellation rows IA09-IA15 are parent-canonical stutters and only IX04 derives improvement-parent canonical `CANCELLED`.
- Verified the identical interrupt union occurs in PLAN, the normative invariant, and generated validation with no omitted or extra rollback-adoption row.
- Verified the rollback-adoption state set is exactly `REQUESTED|ROLLING_BACK|VERIFYING|VERIFIED|FAILED|REMEDIATION_WAIT|ROLLED_BACK`, and each row preserves the existing saga and origin.
- Verified IH06-WX/WN/PX/PN require cancellation NONE and the witness inventory selects matching IX06 X/N after IX01/IX02.
- Verified README, traceability, and this register identify round-14 formal bytes and matching candidate graph as current.

## Current formal-source digests

- `PLAN.md`: `89d3d1a3864cae50e4236052ff345f33c309ec20b59e787176b658a090835ddd`
- `docs/state-transition-manifests.md`: `70e23025d0fcec99f11c6d037ef65e234384c8551a2c385687c9e3f7fccbf271`
