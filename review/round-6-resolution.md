# Round-6 formal/plan resolution

**Scope and status.** This register maps all nine high findings in all five `review/round-6-closure/*.json` files. The current combined plan-only artifact set includes the formal correction, reader-facing evidence-prose repair, and schema-3 candidate-only graph regeneration. It does not claim implementation, semantic evidence validation, model-check completion, independent closure, or a passing re-review.

The formal files, reader-facing legacy evidence banners/status, and `research/repository-agent-operating-system/material-claims.json` are now synchronized. The graph matches the current PLAN and manifest digests, covers all 27 current numbered manifest headings, and uses only candidate/unreviewed legacy relations. Fresh immutable retrieval and human semantic review remain future blocking gates.

## Finding map

| Review file | Finding | Current formal correction | Verification contract | Status |
|---|---|---|---|---|
| `adversarial-consistency.json` | `R6-AC-001` | PLAN §13 now requires A10 termination/effect settlement, predecessor cleanup receipts, and committed A11 `CANCELLED` before any later successor Attempt/Lease/fence/epoch/outbox transaction. Admission explicitly rejects an unfinished predecessor. A10/A11 state the same boundary. | A11-before-successor transaction-order and one-unfinished-attempt race tests. | Formal text corrected; implementation/re-review pending. |
| `adversarial-consistency.json` | `R6-AC-002` | Terminal Work and terminal CleanupItems are immutable. C11 stutters the historical item and atomically creates/recovers a deterministic `RemediationObligation`, link, and MAINTENANCE child at `INBOX`. The obligation has exact status, owner, closure receipt, visibility, and resource-reuse blocking rules. No parent reopens. | Resurface/revoke/review-due tests prove exact absent-or-same identity, independent visibility, blocked resource reuse, and unchanged parent terminal state. | Formal text corrected; implementation/re-review pending. |
| `formal-model.json` | `R6-FM-001` | D19P3 and D19P6 now bind both the verified publication receipt for CW14 and a protected purpose-bound `NoDeploymentReceipt` for CW16. D19P5 uses CW-B44 to `BLOCKED`; later D19P7 uses CW-X2 to `CLEANING`, without CW12. Exact direct, reconciled, and no-apply witnesses name every guard and defer cleanup. | Replay all three closed traces and reject any missing intermediate guard or same-transaction cleanup. | Formal text corrected; implementation/re-review pending. |
| `evidence-semantics.json` | `R6-EVID-001` | PLAN candidate propositions are explicitly attributed to legacy records. GitHub reviewer/token, webhook/security, JSON Schema/RFC, SLSA, OWASP, OpenTelemetry, and METR wording separates conservative local requirements from unverified premises and fails closed on fresh review/target probes. | Re-scan every candidate claim excerpt against the regenerated graph. | Corrected in current combined artifact set; independent re-review pending. |
| `evidence-semantics.json` | `R6-EVID-002` | The research report and matrix are prominently marked superseded/non-authoritative; synthesis is traceability-only; the schema-3 graph is candidate-only. | Verify banners, candidate wording, and current graph digests. | Corrected in current combined artifact set; independent re-review pending. |
| `improvement-recovery.json` | `R6-IMP-001` | IRB07 is split into exact `NONE`, `REQUESTED`, and `QUIESCING` rows with canonical sequences through `ROLLED_BACK`. IRB08 permits only `NONE`; IX03 owns cancellation cleanup and requires rollback `IDLE\|ROLLED_BACK`. Witnesses cover IX01/IX02 at each active/failed rollback state through rollback, cleanup, and `CANCELLED`. | Exhaustive interleaving checker must prove one row owner, reducer equality, legal adjacency, and later cleanup/terminal transactions. | Formal text corrected; implementation/re-review pending. |
| `improvement-recovery.json` | `R6-IMP-002` | IR04 derives deterministic child/link IDs from parent, stage, and `CanaryAdmissionDecision` digest, uses atomic absent-or-same CAS, and creates exactly one pair. Same bytes replay; different identity/payload/key rejects. IR27–IR35 and all exposure/cancel/rollback/cleanup predicates bind the pair. | Sequential/concurrent duplicate tests and receipt-substitution tests. | Formal text corrected; implementation/re-review pending. |
| `improvement-recovery.json` | `R6-IMP-003` | EvidenceBundle has unconditional denial for every missing, duplicate, unexpected, failed, inconclusive, or unaccounted tuple. Protected disposition selects only deny/abort/quarantine/new-manifest rerun and never waives equality. Predeclared exclusions are outside the executable expected set. | Partition tests prove every defective bundle denies every enablement stage. | Formal text corrected; implementation/re-review pending. |
| `architecture-requirements.json` | `R6-ARCH-001` | PLAN §21.1 requires exact set equality from all current numbered manifest headings, with no hard-coded count. The regenerated graph covers 27/27 current headings. | Recompute heading-set equality from current bytes. | Corrected in current combined artifact set; independent re-review pending. |

## File and count accounting

- Review files mapped: **5/5**.
- High findings mapped: **9/9**.
- Formal source files corrected: `PLAN.md` and `docs/state-transition-manifests.md`.
- Status/index files corrected: this register, `review/requirements-traceability.md`, and `README.md`.
- Reader-facing evidence artifacts repaired in the combined change: `report.md`, `evidence-matrix.md`, and `synthesis-coverage.md`.
- Material-claim artifact regenerated: schema-3 `material-claims.json`, current PLAN/manifest digests, 27/27 headings.
- Closure passes claimed: **0**.

## Remaining blocking work

1. Run independent closure re-review.
2. Later, before Increment 1, complete the fresh immutable evidence run, same-run human semantic review, and reviewed-edge regeneration.
3. Run future implementation and model gates. Until then, this register is a correction map, not implementation or closure proof.
