# Round-15 formal/status correction register

**Status:** historical round-15 formal PLAN/manifest and reader-status correction plus then-current-digest schema-3 candidate-graph regeneration completed at that checkpoint; round-16 formal bytes now supersede it and round-16 graph regeneration is pending. This memo does **not** claim independent closure, implementation, exhaustive reachable-product proof, semantic evidence validation, production safety, or autonomous self-government.

## Scope and counts

All **6/6 raw high findings** in all **5/5** `review/round-15-closure/*.json` files are mapped below. The source reviews report **0 critical and 6 high**. The six raw findings represent **4 unique defects**. The corrected normative manifest contains **799 unique edge rows**: **96 canonical** and **703 private/product** rows. No research source-evidence record or evidence-edge semantic relation changed; generated graph metadata, source digests, checkpoint, and material-graph bytes were regenerated for the then-current round-15 bytes.

## Finding map

| Raw finding | Unique defect | Formal/status correction | Status |
|---|---|---|---|
| `R15-REC-001` | Release-attempt failure cleanup can strand cancellation | Added mutually exclusive IA18-F/IA18-C cancellation adoption and settlement for failure-origin `FAILURE_PENDING_CLEANUP` and `CLEANING`. They preserve the one IA07/IA08 CleanupManifest, create no duplicate parent cleanup, seal attempt-local `CANCELLED`, and leave IX03/IX04 as sole parent cleanup/terminal owners. IA16/IA17 now require cancellation NONE. Witnesses race IX01 before/after IA16 and before IA17, include IX05, CAS/replay conflicts, and allow IX04 only after attempt and parent guards pass. | Mapped in formal text; generated execution pending |
| `R15-IR-001` | Cancellation-first degradation was unrecordable | Added IXH01-R/Q/C for every generated reachable nonterminal HEALTHY cancellation tuple in `REQUESTED\|QUIESCING\|CLEANING`. Each atomically records `TELEMETRY_DEGRADED` and a deterministic generation/source-bound receipt, preserves IX Effect/rollout/rollback/cleanup identities and ownership, keeps the fence active, and creates no saga or CleanupManifest. Source equality, settlement/CAS races, replay conflicts, and terminal immutability are explicit. | Mapped in formal text; generated equality/race execution pending |
| `R15-IR-002` | IX revocation omitted FROZEN and EVIDENCE_STALE | Extended the exact REQUESTED/QUIESCING IX06 UNSETTLED/N/X revocation partitions to `SHADOW_PASSED\|FROZEN\|EVIDENCE_STALE -> REVOKED`. The generated relation must equal the six IX06 guards and be pairwise exclusive with IC32 at IX01. Effect/rollback identity and ownership are preserved; no unlisted candidate delta, second saga, or cleanup is allowed. | Mapped in formal text; generated equality/race execution pending |
| `R15-IR-003`, `R15-XC-001`, `R15-ER-001` | Round-14 generated-byte provenance contradiction | Round-14 line 7 now states the exact boundary: no research source-evidence record or evidence-edge semantic relation changed; generated graph metadata, then-current-source digests, checkpoint, coverage locations, and material-graph bytes were regenerated. The R14-XC row now says round-14 regeneration completed, not pending. README and traceability distinguish the historical round-14 graph from the then-current round-15 formal bytes. | Mapped in reader/status text |

## Preserved coverage and pending gates

The correction preserves all earlier mappings and contracts, including exact Effect identity, protected X/N classification, one rollback saga, immutable rollback origin, cancellation dominance, sole parent cleanup and terminal ownership, rollback-safety block release, immutable terminals, and research publication paths. Requirements remain structurally mapped **16/16**.

The PLAN, normative-manifest bytes, and matching schema-3 candidate-only material graph were round 15 and covered all 28 headings at that checkpoint. Round-16 formal bytes now supersede them; the material graph remains historical round 15 and regeneration against round-16 digests is pending. Generated witness/model execution, generated witness/model execution, fresh immutable retrieval, same-run human semantic review, implementation/full-model checks, production validation, and independent closure re-review remain pending. **No closure is claimed.**

## Validation performed

- Parsed all **5/5** round-15 review JSON files and reproduced the exact high-ID set: `R15-IR-001`, `R15-IR-002`, `R15-IR-003`, `R15-XC-001`, `R15-REC-001`, `R15-ER-001`.
- Parsed **799/799** unique manifest edge IDs with no duplicate and verified every Markdown data-row width against its table header.
- Verified the canonical graph remains **96** rows and the private/product inventory is **703** rows.
- Verified each new IA18 projection is an IX-dominant canonical stutter and each IXH projection re-enters `REDUCE-V1`; no new explicit canonical adjacency is unlisted.
- Verified IA16/IA17 reject after IX01, IA18-F/IA18-C preserve the one failure CleanupManifest, and IX04 remains the sole improvement-parent `CANCELLED` row.
- Verified IXH01-R/Q/C exactly name REQUESTED/QUIESCING/CLEANING HEALTHY nonterminal sources and exclude terminal CANCELLED.
- Verified the IX revocation candidate set is exactly `SHADOW_PASSED|FROZEN|EVIDENCE_STALE` across REQUESTED/QUIESCING and UNSETTLED/N/X.
- Verified README and traceability identified the then-current round-15 formal bytes and matching regenerated schema-3 candidate graph at that checkpoint. This register is now historical; round-16 formal bytes supersede it and graph regeneration is pending.

## Historical round-15 formal-source digests

- `PLAN.md`: `9a9a3aba3f7a98824ba475830ba4adb6e2d0fce798903b9cd956b3327cdb1d3c`
- `docs/state-transition-manifests.md`: `4a35900ab71d43b9b28d6f220a7a883ab47edf206b5dbc29610524b5ee6b046d`
