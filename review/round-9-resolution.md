# Round-9 formal/plan resolution register

## Status

**Formal PLAN/manifest correction and current-digest candidate-only graph regeneration complete; closure not claimed.**

This register maps all **8/8 raw high findings** from all **5/5** files in `review/round-9-closure/`. The edits preserve remediation, reclaim, control, release, cleanup, and Effect coverage. The schema-3 candidate-only graph was subsequently regenerated against the current PLAN/manifest digests and all 28 headings.

## Stable correction clauses

### R9-C01 — Exact rollback cleanup ownership

Reducer priority 7a now partitions `rollback_origin` exactly. With cancellation `NONE`, `WIDENING_ABORT` remains `ROLLED_BACK` through IR12/IR13A and IR13C alone schedules cleanup. IRB08 is sole only for non-`WIDENING_ABORT`. With cancellation `REQUESTED|QUIESCING`, IX03 alone schedules cleanup. The checker enumerates the complete, disjoint partition.

### R9-C02 — Effect-first degradation

IH01-W/P atomically record degradation, fence sends, and enter explicit safe reconciliation rollout states without starting rollback. The exact original Effect must settle or reconcile first. Only IH06-X/N then selects protected exposure rollback or proved-no-application failure/abort. IRB01 rejects while the original mutation Effect is live, `SENDING`, `UNKNOWN`, or unsettled.

### R9-C03 — Reachable direct-terminal Effect relation

E09, E10, E30, E31, E33, and E35 require a signed target-effect `NoApplicationReceipt` or no-send proof. Without it, UNKNOWN/reconciliation is required. These edges have only reachable N product rows; their impossible X rows were removed. A conflicting same-target `ExposureReceipt` rejects. Coverage is exact equality with the declared reachable edge/classification relation rather than a Cartesian product.

### R9-C04 — Candidate revocation by exact coordinates

IC32 is partitioned across protected no-exposure, proved exposure, and unsettled original-Effect classes. Pre-exposure revocation enters failure cleanup without rollback. Proved exposure atomically revokes the candidate, changes the exact rollout, and creates one rollback saga. Unsettled mutation enters safe reconciliation first. IC32 rollback-entry owners are listed exhaustively and have tuple witnesses; no coordinate is inferred.

### R9-C05 — Canary abort X/N settlement

IR07, IR09→IR11, IR10, IR53, and degradation-pause continuation have mutually exclusive exposed/no-exposure paths. Exposed abort entry creates rollback once. No-exposure persists a protected classifier. IR13B now accepts all bound effects settled with proved non-application, including an E34 terminal record from IR43, instead of requiring an empty Effect set. Exact paths end through IR13A or IR13B, then IR13C under cancellation `NONE` or IX03 under cancellation.

### R9-C06 — Historical/current traceability

Traceability §10 now says the round-8 regeneration completed and §11 is the historical checkpoint authority. New §12 records the current round-9 state: formal edits and new-digest graph regeneration complete. README says the same. Future immutable retrieval, same-run semantic review, reviewed-edge regeneration, implementation/model proof, production validation, and independent closure remain unperformed gates.

## Raw finding map (8/8)

| Raw ID | Severity | Resolution |
|---|---|---|
| R9-ET-001 | high | R9-C06 |
| R9-FS-001 | high | R9-C04 |
| R9-FS-002 | high | R9-C05 |
| R9-FS-003 | high | R9-C06 |
| R9-INT-001 | high | R9-C01 |
| R9-INT-002 | high | R9-C02 |
| R9-INT-003 | high | R9-C03 |
| R9-REQ-001 | high | R9-C06 |

Mapped raw findings: **8/8**. Unmapped: **0**.

## Preserved gates

- No implementation or production-safety proof is claimed.
- No exhaustive reachable-product/full-model result is claimed beyond the specified ephemeral checker assertions.
- No fresh immutable evidence retrieval or same-run human semantic review is claimed.
- Candidate evidence remains candidate-only.
- Material-graph regeneration is complete; a new independent closure audit remains pending.
