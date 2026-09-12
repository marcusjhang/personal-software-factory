# Round-5 resolution register

**Status:** combined plan-only correction. The formal contract and current-digest schema-3 candidate-only material-claim regeneration are complete. No controller, factory, database, external write, fresh research retrieval, semantic evidence review, or full model check was performed.

## Counts and deduplication

The five `review/round-5-closure/*.json` files contain **14 raw findings: 12 high and 2 low**. All 14 are mapped below. Repeated findings are deduplicated into ten stable clauses without dropping an ID. `requirements-authority.json` has zero findings and remains represented in the file coverage table.

| Stable clause | Plan-level correction |
|---|---|
| R5-C01 evidence semantics | PLAN §4 now defines the legacy graph as editorial association only. Every external legacy edge is unreviewed and uses `candidate_support\|candidate_refute\|context_only`; `supports\|refutes` are reserved for future same-run human-reviewed observations. Categorical platform/research/queue-mode prose is candidate attribution. The regenerated schema-3 graph uses only candidate/unreviewed legacy relations and matches the current PLAN and manifest digests. |
| R5-C02 unconfirmed quiescence | PLAN §13 and manifest §§1, 10, 14 remove `ACTIVE_DISJOINT_ONLY`. A disposition permits only monitoring, isolation, kill, reconciliation, and closure. It cannot create a successor Attempt, Lease, fence, context, output, command, effect, credential, workspace, or alternate authority carrier. The node stays blocked and the old Attempt unfinished until exact termination, U09, and A18. |
| R5-C03 release-attempt projections | Manifest IA01 and IA05 are `S`; IC06 owns `READY_REVIEW>READY`; IC13 consumes the durable IA05 receipt and owns `VERIFYING>REVIEW`. §15.7 fixes separate transaction order, and §15.8 publishes concrete tuple witnesses. |
| R5-C04 rollback | IR19 and IR22 explicitly synchronize rollout `->FAILED` and rollback `IDLE->REQUESTED`. IRB01–IRB08 name every later coordinate edge through retry, verification, `ROLLED_BACK`, separate cleanup scheduling, and later terminalization. Reducer priority 7 no longer masks cleanup/terminal after settled rollback. |
| R5-C05 widening UNKNOWN | IR42 synchronizes E11 with the exact legal `REVIEW>BLOCKED>QUARANTINED` sequence. The effect fold keeps reconciliation evidence unresolved until a verified/final receipt. CW-Q2/CW-Q3 are exact verified-reconciliation resume edges. §15.8 gives the durable UNKNOWN witness and exits. |
| R5-C06 pre-exposure abort | IR13A is the rollback-required branch. IR13B requires protected `NoExposureReceipt`, complete absence, child clean, and settled effects. Both reach `CANARY_ABORT_SETTLED`; only separate IR13C enters `CLEANING`. No rollback is fabricated. |
| R5-C07 Release 0 research | D19 accepts a protected `NoPublicationDisposition`/`NoPublicationReceipt` and uses CW-N1 without CW14 or an external write. D19P1/P2/P3 split publication intent, dispatch, and verified receipt; only P3 crosses CW14. D19C1/C2 enter cleanup later. |
| R5-C08 promotion | `PROMOTING` now maps pre-merge. IR17 dispatch stutters at `MERGE_QUEUED`. Only verified IR18 crosses `MERGE_QUEUED>MERGED` and the guarded deploy/observe edges. IR54/IR55 plus ORIGINAL reconciliation cover UNKNOWN, verified apply, and proven no-apply before MERGED. |
| R5-C09 cancellation | The four built-in tables now contain one explicit owner cancel, cancel-adopt, or safety-defer event for every reachable nonterminal private state, including both CREATED states, IDEATION STALE/QUARANTINED, MAINTENANCE UNKNOWN_EFFECT/QUARANTINED, rollback states, QUIESCING, and CLEANING. No wildcard supplies coverage. |
| R5-C10 Effect partitions/status | E30–E39 and the exhaustive partition clause cover invalid/missing receipts, identity mismatch, stale/forbidden/exhausted retry, invalid reconstructed receipt, compensation ambiguity, and bounded expiry. ORIGINAL and COMPENSATION remain disjoint. Traceability and README distinguish completed round-4 editorial repair from regeneration newly required by this PLAN/manifest edit. |

## Raw finding map

| Review file | Finding | Severity | Stable clause(s) |
|---|---|---:|---|
| `architecture-consistency.json` | R5-ARCH-001 | high | R5-C02 |
| `architecture-consistency.json` | R5-ARCH-002 | low | R5-C10 |
| `architecture-consistency.json` | R5-ARCH-003 | high | R5-C07 |
| `architecture-consistency.json` | R5-ARCH-004 | high | R5-C08 |
| `evidence-integrity.json` | R5-EVID-001 | high | R5-C01 |
| `evidence-integrity.json` | R5-EVID-002 | low | R5-C10 |
| `formal-transition.json` | R5-FT-001 | high | R5-C03 |
| `formal-transition.json` | R5-FT-002 | high | R5-C04 |
| `formal-transition.json` | R5-FT-003 | high | R5-C09 |
| `formal-transition.json` | R5-FT-004 | high | R5-C10 |
| `improvement-product.json` | R5-IMP-001 | high | R5-C03 |
| `improvement-product.json` | R5-IMP-002 | high | R5-C04 |
| `improvement-product.json` | R5-IMP-003 | high | R5-C05 |
| `improvement-product.json` | R5-IMP-004 | high | R5-C06 |
| `requirements-authority.json` | No finding (`0` total; 16/16 mapped) | — | Existing authority/requirements repairs preserved; round-5 corrections do not widen authority. |

## Ephemeral validation performed

A temporary in-memory parser/checker read the edited Markdown. It was not committed as an implementation or proof artifact.

- Parsed all four built-in tables with eight columns: IDEATION **37** rows, BUILD **74**, MAINTENANCE **61**, DEEP-RESEARCH **69** (header excluded).
- Parsed **88** unique canonical edges. Every explicit built-in canonical sequence used only listed adjacency. Every built-in endpoint resolved through PLAN §14.0. Every explicit built-in `S` row had equal source/target lookup projections.
- Reachability from each declared initial covered all declared private states: IDEATION **16/16**, BUILD **31/31**, MAINTENANCE **28/28**, DEEP-RESEARCH **27/27**.
- Reachable nonterminal cancellation coverage was exactly one explicit owner cancel/adopt/defer per state: IDEATION **13/13**, BUILD **28/28**, MAINTENANCE **25/25**, DEEP-RESEARCH **24/24**.
- Parsed **39** Effect rows over **21** states. Every one of the **15** nonterminal Effect states had an outgoing row. The source partition text explicitly covers each mutually exclusive outcome or a bounded wait with a named expiry edge.
- Checked split cleanup: no row sourced outside `CLEANING` both entered cleanup and terminalized. Research no-publish/publish and both canary-abort branches enter cleanup only in a later transaction.
- Checked explicit improvement projections against canonical adjacency and found no unlisted adjacent pair. Replayed the published §15.8 witnesses for IA01/IA05/IC13; IR19/IR22 and IRB rollback through cleanup/terminal; widening UNKNOWN; both pre-exposure abort branches; research no-publish/publish; and promotion dispatch/verified/UNKNOWN/no-apply.
- Searched the edited authority documents for removed categorical phrases and `ACTIVE_DISJOINT_ONLY`; none remain. Named-coordinate rules reject inferred deltas.

These are deterministic editorial checks, **not a full model check**, implementation test, or operational-safety proof.

## Remaining gates

The schema-3 candidate-only `material-claims.json` has been regenerated against the current PLAN and normative-manifest digests without rewriting the research corpus. Fresh immutable retrieval, same-run human semantic review, deterministic regeneration of reviewed relations, and independent closure re-review remain required before Increment 1.
