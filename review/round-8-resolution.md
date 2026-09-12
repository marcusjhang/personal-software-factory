# Round-8 formal/plan resolution

## Scope and status

This register maps every raw critical/high finding in all five `review/round-8-closure/*.json` files. The raw count is **15/15** across **5/5** files: **1 critical and 14 high**. Duplicate reports remain individually mapped. They deduplicate into eight stable clauses, R8-C01 through R8-C08.

The current combined plan-only artifact set includes the formal correction and schema-3 candidate-only material-graph regeneration. The graph matches the current PLAN and manifest digests and dynamically covers all 28 headings. No implementation, exhaustive model proof, fresh evidence retrieval, semantic evidence review, or independent closure is claimed.

## Stable correction clauses

### R8-C01 — Closed rollback remediation and cancellation projection

Manifest §§15.1, 15.3.1, and 15.8 add `REMEDIATION_WAIT` to the closed `rollback_state` vocabulary. Reducer priorities 2 and 7 now have positionally equal six-entry input/result lists and map it exactly to `BLOCKED`. The checker must execute IRB06→RO09→IRB09→IRB03→IRB07 under cancellation `NONE`, `REQUESTED`, and `QUIESCING`, with IRB08 or IX03/IX04 as the sole applicable cleanup/terminal owner.

### R8-C02 — Control continuity and fail-safe degradation

PLAN §8.4 and manifest §§15.6–15.8 define `CURRENT_CONTINUITY` as no degradation in the current generation or fresh IH03 after the latest degradation. IH05 is limited to protected no-exposure/no-active-generation restoration and invalidates old decisions. IH01 is non-active only. IH01-C/W/A/P/D/O exhaustively record degradation and atomically move every HEALTHY-only active rollout state to its exact pause/review/abort/rollback tuple. Progress requires HEALTHY plus `CURRENT_CONTINUITY`; grants and effects cannot remain active behind `BLOCKED`.

### R8-C03 — Total terminal Effect products

Manifest §§15.3 and 15.8 add mutually exclusive exposure/no-exposure product exits for direct terminal Effect edges E09, E10, E30, E31, E33, and E35 in both `WIDENING_EFFECT` and `PROMOTING`, alongside E20/E21/E24/E25/E28/E29/E37/E39. Failure, risk, and compensation outcomes abort, roll back, or fail and later use one cleanup owner. Only verified E06 or E17 rows apply widening or promotion successfully. The checker requires reachable-edge/product-row set equality.

### R8-C04 — Single widening rollback entry

Every exposed `IW*X` and `IWD*X` row atomically changes rollback `IDLE->REQUESTED` and creates the one bound rollback saga. Manifest §15.3.1 names IR19, IR22, all exposed IW/IWD/IP/IPD rows, and applicable synchronized degradation rows as the complete rollback-entry owner set. Every entry requires IDLE and duplicate creation rejects.

### R8-C05 — Legal final C12 failure cleanup

Manifest §§15.7–15.8 allow ICL02 to consume either final C02 or legal-retention C12 under the exact failure conjunction. ICL01/02/03 and IX04 remain mutually exclusive final-fold owners; generic C02/C09/C12 cannot terminalize the parent.

### R8-C06 — Release failure reaches the exact terminal conjunction

Manifest §§15.4 and 15.8 replace broad IA07/IA08 exits with disjoint synchronized IA07-* and IA08-* rows for every legal offline/shadow candidate phase. Each atomically moves the candidate to `OFFLINE_FAILED` or `SHADOW_FAILED` and the release attempt to `FAILURE_PENDING_CLEANUP`. IA16 preserves the cleanup split and IA17 alone reaches immutable release `FAILED`; witnesses cover EXECUTING and VERIFYING through cleanup for every phase and reject any unmapped release FAILED tuple.

### R8-C07 — Transactional remediation revocation

PLAN §13 and manifest §§13–13.1 partition C11 signals. Non-revoking resurfacing/review reminders use RO03–RO06. Revocation with no live generation creates an exact REVOKED generation through RO01-R/RO02-R with no active authority. Revocation from OPEN/IN_PROGRESS/VERIFYING uses RO11/RO12/RO13 in the same transaction to append the event, change status, fence grants, quiesce the child, and settle/reconcile effects. Event lookup precedes status routing, so same-event replay returns its original receipt after the transition; a later distinct REVOKED signal uses RO06. RO14 is the sole reauthorization and no work precedes it.

### R8-C08 — Unambiguous evidence currentness

`review/requirements-traceability.md` §§6–8 now describe superseded checkpoints historically. The completed round-7 checkpoint is stated as matching its 28-heading dynamically derived graph. Current §11 and README state that round-8 schema-3 regeneration completed against the new normative bytes and all 28 headings. The rule remains dynamic full-heading-set equality. Fresh retrieval, semantic review, reviewed-edge regeneration, implementation/model proof, and independent closure remain separate gates.

## Raw finding map

| Source file | Raw finding | Severity | Stable clause | Exact repair anchor |
|---|---|---:|---|---|
| `evidence-status.json` | R8-EVID-001 | high | R8-C08 | traceability §§6–11; README Status |
| `formal-state.json` | R8-FS-001 | critical | R8-C01 | manifest §§15.1, 15.3.1, 15.8 |
| `formal-state.json` | R8-FS-002 | high | R8-C06 | manifest §§15.4, 15.8 |
| `formal-state.json` | R8-FS-003 | high | R8-C02 | PLAN §8.4; manifest §§15.6–15.8 |
| `formal-state.json` | R8-FS-004 | high | R8-C07 | PLAN §13; manifest §§13–13.1, 15.8 |
| `formal-state.json` | R8-FS-005 | high | R8-C08 | traceability §§6–11; README Status |
| `improvement-product.json` | R8-IMP-001 | high | R8-C01 | manifest §§15.1, 15.3.1, 15.8 |
| `improvement-product.json` | R8-IMP-002 | high | R8-C02 | PLAN §8.4; manifest §§15.6–15.8 |
| `improvement-product.json` | R8-IMP-003 | high | R8-C03 | manifest §§15.3, 15.8 |
| `improvement-product.json` | R8-IMP-004 | high | R8-C04 | manifest §§15.3–15.3.1, 15.8 |
| `improvement-product.json` | R8-IMP-005 | high | R8-C05 | manifest §§15.7–15.8 |
| `improvement-product.json` | R8-IMP-006 | high | R8-C08 | traceability §§6–11; README Status |
| `cleanup-reclaim.json` | R8-CR-001 | high | R8-C07 | PLAN §13; manifest §§13–13.1, 15.8 |
| `cleanup-reclaim.json` | R8-CR-002 | high | R8-C08 | traceability §§6–11; README Status |
| `requirements-architecture.json` | R8-REQ-001 | high | R8-C08 | traceability §§6–11; README Status |

## Preservation and remaining gates

The correction preserves the full RemediationObligation machine, A11 reclaim ordering, runtime terminal immutability, Effect reconciliation origin separation, publication paths, cancellation coverage, and all earlier repairs. Material regeneration now matches the normative byte change. The package still requires the declared immutable evidence, semantic review, reviewed-edge regeneration, implementation, exhaustive generated checks/model proof, and independent closure gates. This register does **not** declare closure.
