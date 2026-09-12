# Round-12 formal/plan correction register

**Status:** formal PLAN/manifest correction and current-digest candidate-only graph regeneration complete. This memo does **not** claim independent closure, implementation, full reachable-product proof, semantic evidence validation, or production safety.

## Scope and counts

All **8/8 raw high findings** in all **5/5** `review/round-12-closure/*.json` files are mapped below. The source reviews report **0 critical and 8 high**. The corrected normative manifest contains **785 unique edge rows**: **96 canonical** and **689 private/product** rows. No research source-evidence record or evidence-edge semantic relation changed. The generated material graph metadata/digests were subsequently regenerated against the new formal bytes.

## Finding map

| Raw finding | Formal correction | Status |
|---|---|---|
| `R12-FM-001` | Replaced the six-state control-health hand list with generated `ReachableActiveExposureInterruptCoordinatesV1` equality. Residual IH01-RX/RN synchronously cover exposure-bearing `WIDENING_REVIEW` and every other derived omission; X fences/stops and creates or reuses one rollback, N requires protected no exposure, and generic IH01 is inactive-only. Adjacent-edge races are explicit. | Mapped in formal text; generated equality/race execution pending |
| `R12-FM-002` | B71/M59 now own first cancellation arriving after B38/M29 under an absent-disposition/expected-version CAS. B71-P/M59-P separately continue cancellation persisted during rollback, and B71-R/M59-R are byte-identical replay only. B39/M30 race the first arrival under the same disposition/version boundary. | Mapped in formal text; generated race execution pending |
| `R12-XC-001` | RO09 retains RO00-I blocks through IRB09 remediation and IRB03 independent verification. IRB07-N/R/Q now require the closure, restoration, independent-verification, purpose/generation/key-set receipts and atomically remove only the exact blocks while sealing/adopting actual `ROLLED_BACK`; cleanup/terminal guards require the BlockReleaseReceipt. | Mapped in formal text; generated release-order proof pending |
| `R12-XC-002` | Added exact EVIDENCE_STALE reconciliation continuations IC24-RWX, IC24-RPX, and IC24-RN after IC24-A. They preserve original Effect identity, require no unrelated revocation, select settled protected X/N exactly, create or reuse at most one rollback for X, and assign the one N cleanup owner. | Mapped in formal text; generated X/N witness execution pending |
| `R12-XC-003` | Corrected the round-11 no-edit sentence to distinguish unchanged source/edge semantics from regenerated metadata/digests, marked round-10 wording “then-current,” made round-11 graph/digests explicitly historical, and records completed round-12 regeneration. | Mapped in status/traceability text |
| `R12-IA-001` | Added exposed `CANARY_PASSED` to IX06-XR/XQ and exact `ExposedCancellationSourcesV1` equality. The transaction maps safely to `CANARY_ABORTING`, stops/fences exposure, takes rollback `IDLE->REQUESTED`, fixes `WIDENING_ABORT` origin, and specifies expected-version replay/conflict behavior plus IX01 races before/after IR08 and IR14. | Mapped in formal text; generated race execution pending |
| `R12-IA-002` | The derived control-interrupt relation explicitly covers exposed `CANARY_PASSED`, pre-rollback `CANARY_FAILED`, exposure-bearing `WIDENING_REVIEW`, exposed `PROMOTION_PENDING_APPROVAL`, and every actual omission through synchronized IH01-RX/RN X/N branches. Sole-interrupt equality and adjacent-edge witnesses replace hand-list completeness. | Mapped in formal text; generated equality/race execution pending |
| `R12-REC-001` | The same improvement rollback-safety release contract binds RO00-I purpose, generation, exact key-set digest, RO09 closure, genuine restoration, IRB03 verification, absent-or-same release receipt, replay/conflict behavior, cancellation races, and later sole cleanup ownership. | Mapped in formal text; generated receipt/race execution pending |

## Preserved coverage and pending gates

The correction does not change BUILD/Maintenance rollback settlement owners B38/M29, and it does not move release into RO09. It preserves Effect identity, rollback origin, exact-once cleanup ownership, canonical adjacency, A11 reclaim ordering, immutable terminals, research publication paths, and every earlier raw-finding mapping. Requirements remain structurally mapped **16/16**.

The round-11 schema-3 candidate-only material graph remains complete for the then-current round-11 bytes and 28 dynamically derived headings. Round-12 schema-3 metadata/digests now match the current PLAN and normative manifest and all 28 headings. Fresh immutable retrieval, same-run human semantic review, deterministic reviewed-edge regeneration, implementation/full-model checks, production validation, and independent closure re-review remain pending. **No closure is claimed.**

## Current formal-source digests (pre-regeneration)

- `PLAN.md`: `19fea5cc0f6df092eec3fa4f0b0488465b4e3460c8c54fe94c85006a795bea1c`
- `docs/state-transition-manifests.md`: `8fb9782a8e20310ce8975486a8e0742a02e76148fba85624e4197ff1073f0a1d`
