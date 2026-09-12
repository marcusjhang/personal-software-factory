# Round-7 formal/plan resolution

## Scope and status

This file maps every raw critical/high finding in all five `review/round-7-closure/*.json` files to the current combined plan-only artifact set. Formal corrections and the schema-3 candidate-only graph regeneration are current. It does not claim implementation, a full reachable-product proof, fresh evidence retrieval, semantic review, or independent closure.

There are **14 raw high findings** representing **13 distinct defects**. `R7-FT-001` and `R7-INT-001` are the same rollback/cancellation defect. `R7-LCA-001` and `R7-FT-002` independently report the missing remediation machine and remain mapped separately. `R7-REQ-001` is one raw combined architecture finding with two explicitly mapped subfindings. No raw ID is dropped.

## Raw finding map

| Review file | Raw ID | Stable correction clauses | Resolution |
|---|---|---|---|
| `lease-cleanup-adversary.json` | `R7-LCA-001` | Manifest §§13–13.1 RO01–RO14; §17; PLAN §§13, 21 | Adds exact OPEN initial, five-state closed machine, authorities/CAS/replay, child/effect/cleanup bindings, revoke/re-authorize/retry/expiry, sole CLOSED terminal/unblock, and reachability/no-sink tests. |
| `lease-cleanup-adversary.json` | `R7-LCA-002` | Manifest §13 C11 and §13.1 RO01–RO06 | Separates first absent-or-same materialization, same-event replay, later distinct signal append without child reset, and post-CLOSED next generation with exact IDs. |
| `formal-transitions.json` | `R7-FT-001` | Manifest §§15.1, 15.3.1 IRB06/IRB09, 15.5 IX03/IX04, 15.8; PLAN §8.4 | Final rollback failure enters REMEDIATION_WAIT/BLOCKED. Only protected remediation closure, real verification, ROLLED_BACK, IX03 and IX04 can finish cancellation. Unresolved risk stays nonterminal. |
| `formal-transitions.json` | `R7-FT-002` | Manifest §§13–13.1 RO01–RO14; §17 | Same independently reported missing remediation lifecycle; mapped without deduplication loss. |
| `formal-transitions.json` | `R7-FT-003` | Manifest §§1, 8–10, 15.1, 15.4 | Introduces `FAILURE_PENDING_CLEANUP` and `RETRY_DISPOSITION`; reserves runtime `FAILED` as final immutable; every declared runtime terminal has zero outgoing rows. |
| `formal-transitions.json` | `R7-FT-004` | Manifest §15.7 ICL01–ICL03 and IX04 | Adds sole synchronized owner for the last improvement CleanupItem/fold and exact CLEANING→DONE/FAILED projections; generic C02/C09/C12 cannot falsely claim S. |
| `formal-transitions.json` | `R7-FT-005` | PLAN §§13, 15; manifest §§13–13.1 | Removes parent-resurface wording. Parent Work and CleanupItem remain immutable; obligation/child remain visible and resources blocked through closure. |
| `improvement-interleavings.json` | `R7-INT-001` | Manifest IRB06/IRB09, IX03/IX04, §15.8; PLAN §8.4 | Same rollback/cancellation defect as FT-001; the request is always accepted, but final CANCELLED waits for genuine safety settlement and cannot be waived. |
| `improvement-interleavings.json` | `R7-INT-002` | Manifest IR03/IR04/IR24, canary-generation invariant, §§15.7–15.8 | Models active generation plus history; replacement requires prior terminal/quiescent/effect-and-rollback-settled/clean pair; delayed old WorkerStarted is fenced. |
| `improvement-interleavings.json` | `R7-INT-003` | Manifest IR38 and IR56; §15.8 | Direct E06 and reconstructed E17 are mutually exclusive widening success rows with the same decision/bounds/generation/effect identity and CANARY_RUNNING result. |
| `improvement-interleavings.json` | `R7-INT-004` | Manifest IW20X–IP39N, CW-R12, IR18/IR38/IR56/IR57, §§15.7–15.8 | Enumerates widening and promotion E20/E21/E24/E25/E28/E29/E37/E39 settled results across protected exposure/no-exposure. Only E06/E17 can widen or cross MERGED; all others abort/rollback/fail with later single-owner cleanup. |
| `improvement-interleavings.json` | `R7-INT-005` | Manifest IR06, IR17/18, IR27–IR33, IR36–IR40, IR56/57, control-health invariant, §15.8 | Requires HEALTHY and completed IH03 continuity for resume/exposure/progress and forbids reachable active exposure under degraded/paused/failed control. |
| `requirements-architecture.json` | `R7-REQ-001` | PLAN §5.1 and §§13, 15; manifest §§13–13.1 | Combined subfinding A: no terminal parent/item reopen. Combined subfinding B: catalogs RemediationObligation, RemediationResurfaceReceipt and RemediationClosureReceipt with protected durable ownership. |
| `requirements-architecture.json` | `R7-REQ-002` | Traceability §§6–7, 9–10; README status | Recasts prior graph states historically and records that schema-3 regeneration now matches the round-7 bytes and 28 current headings. |

`evidence-currentness.json` reports no finding. After formal edits, the candidate-only graph was regenerated against the round-7 digests and all 28 current headings; it still claims no semantic or provenance validation.

## Preserved contracts

- A11 must commit before any successor Attempt, Lease, fence, context, or outbox.
- DEEP-RESEARCH no-publication, direct publication, reconstructed publication, and proved-absence paths remain unchanged.
- ORIGINAL and COMPENSATION Effect origins and all declared terminal dispositions remain disjoint.
- Existing whole-work cancel admission coverage remains; only the terminal promise is narrowed to require real safety settlement.
- All prior formal repairs remain normative unless an exact round-7 row refines them.

## Validation record

Ephemeral deterministic checks on the edited documents report:

- five review files read; **14/14 raw high IDs mapped**, **13 distinct defects**, including both parts of the combined architecture finding;
- **679 unique manifest row IDs**, zero duplicates, and uniform column counts in every Markdown table;
- **28 actual numbered normative headings** derived from current bytes; the regenerated material graph covers exactly that set;
- FactoryInstance **29** rows, NodeRun **32**, Attempt **24**, and release-attempt **17**: all declared states reachable from initial; only declared terminals are sinks; declared terminals have zero outgoing rows;
- RemediationObligation **14** rows: all five states reachable, `CLOSED` is the sole sink, and CLOSED has zero outgoing rows;
- canonical manifest has **90** listed edges; every explicit new canonical sequence is listed, including protected-exposure rollback and remediation-to-verification resume;
- direct/reconstructed widening, exhaustive E20/E21/E24/E25/E28/E29/E37/E39 product rows, HEALTHY/IH03 guards, canary generation races, rollback final-remediation paths, and final improvement cleanup ownership have explicit §15.8 witnesses.

These are plan-table checks, not a full model proof. The candidate-only material graph is regenerated against the current formal digests; fresh immutable retrieval and human semantic review remain future gates.

## Current edited-file SHA-256
- `PLAN.md`: `25f6960b677d7d4a62c7a55c6bcbbe6ebe744e176c41855cbf08ffa5ed2f6acc`
- `docs/state-transition-manifests.md`: `b1cd4933042162367d7e6a3d8e42f07f85ad3308ffd5d38b5882500a3f542413`
- `review/requirements-traceability.md` and `README.md`: current status text updated after formal correction to record completed schema-3 regeneration; their bytes are not inputs to the material graph.
