# Normative state-transition manifests

**Status and authority.** This is a normative part of `PLAN.md`. It is a plan contract, not an implementation or proof result. The compiler must ingest the versioned equivalent of every row below. Prose, diagrams, state lookup tables, and examples cannot add an edge. `*`, “any state,” implicit fall-through, and inferred transitions are forbidden. Every FactoryInstance, NodeRun, Attempt, and release-attempt symbol declared terminal is immutable and has zero outgoing transition rows; pre-cleanup or retryable failure always uses a distinct nonterminal symbol.

## 1. Manifest notation and universal rules

Each edge row is a closed edge: `ID`, exact `source`, exact `target`, guard, canonical projection, wait/stale/retry rule, effect/cleanup rule, and terminal result. `S` means one canonical stutter event with the private edge ID recorded. `A>B>C` means those canonical edges commit in the listed order in one compare-and-append transaction; every intermediate guard is rechecked. `CHILD(X)` creates or advances a distinct child work aggregate at `X`; it never moves the parent backwards. A projection is invalid unless every adjacent pair appears in §2. `REDUCE-V1` means recompute the improvement tuple by §15; it is not permission to invent an edge. A row marked `REDUCE-V1` must yield `S`, one §2 edge, or the exact guarded sequence named by the synchronized release-attempt row.

Guard codes are conjunctive:

- `valid`: expected aggregate/schema/lifecycle/factory versions, immutable `tenant_id` and exact typed `ScopeRef`, authenticated authority snapshot, current bound digests, and CAS all match.
- `ready`: `valid` plus a current `PolicyAdmissionReceipt` or per-item human `Approval` allowed by PLAN §10.
- `lease`: `valid` plus current database-time lease/fence/epoch/context and sandbox attestation.
- `settled`: no live lease/grant/unfinished attempt; all effects have a settled disposition; children satisfy their terminal predicate.
- `clean`: `settled` plus every required cleanup item is `CLEANED` or has an eligible `CleanupEscalationDisposition` under §13.
- `quiescence-closed`: the bound UnconfirmedQuiescence saga reached `CLOSED` specifically through U09, its closure receipt verifies, the bound old Attempt reached A18, every shared-resource ownership predicate is false, and every effect is settled. `DENIED`, `REVIEW`, `ISOLATING`, and `REVOKED` never satisfy this guard.
- `fresh`: required evidence, dependency, identity/control, policy, base and telemetry digests are current.
- `budget`: retry/time/cost budget remains. `exhausted` means the relevant closed budget is spent.

`W(kind)` creates the exact Wait row in §11. Answer/resume, expiry, withdrawal, cancellation and stale input can occur only through the explicit edges for that aggregate and §11. No wait authorizes work. `fx-none` means no external effect. `fx-intent` means only a typed `EffectIntent`; dispatch still uses §12. `cleanup` creates/schedules the required CleanupItems and persists canonical `CLEANING`; it never supplies a cleanup receipt in that transaction. Every entry to `CLEANING` stops there. Only a separate row sourced at `CLEANING` may reach `DONE|FAILED|CANCELLED`, and it requires `clean` from previously committed receipts. Every nonterminal row has an outgoing row. Terminal statuses are only those explicitly marked. Once Work reaches `DONE|FAILED|CANCELLED`, its lifecycle and historical terminal CleanupItems are immutable; later risk is carried only by the §13 RemediationObligation/MAINTENANCE child and never reopens Work. `FAILED` is not terminal while authority, an effect, rollback, or cleanup is live.

## 2. Canonical work graph v1

The initial state is `INBOX`. Terminal states are `DONE`, `FAILED`, and `CANCELLED`, but only under `clean`. `BLOCKED` resumes only through the saved continuation receipt. The following is the complete legal edge set; no cross-cutting shortcut exists.
| ID | Source | Target | Guard |
|---|---|---|---|
| CW01 | INBOX | TRIAGED | valid |
| CW02 | TRIAGED | PLANNING | valid |
| CW03 | PLANNING | READY_REVIEW | fresh |
| CW04 | READY_REVIEW | READY | ready |
| CW05 | READY | LEASED | lease-created |
| CW06 | LEASED | IMPLEMENTING | worker-started |
| CW07 | IMPLEMENTING | VERIFYING | outputs-sealed |
| CW08 | VERIFYING | REVIEW | oracle-pass |
| CW09 | VERIFYING | IMPLEMENTING | repair-authorized |
| CW10 | REVIEW | IMPLEMENTING | changes-requested |
| CW11 | REVIEW | MERGE_QUEUED | review-pass |
| CW12 | MERGE_QUEUED | REVIEW | head-or-check-change |
| CW13 | MERGE_QUEUED | READY_REVIEW | material-plan-change |
| CW14 | MERGE_QUEUED | MERGED | verified-effect |
| CW15 | MERGED | DEPLOYING | deployment-authorized |
| CW16 | MERGED | OBSERVING | no-deploy-receipt |
| CW17 | DEPLOYING | OBSERVING | deploy-receipt |
| CW18 | OBSERVING | CLEANING | outcome-recorded |
| CW19 | CLEANING | DONE | clean+success |
| CW20 | CLEANING | FAILED | clean+failed-disposition |
| CW21 | CLEANING | CANCELLED | clean+cancel-disposition |
| CW22 | BLOCKED | INBOX | resume(INBOX) |
| CW23 | BLOCKED | TRIAGED | resume(TRIAGED) |
| CW24 | BLOCKED | PLANNING | resume(PLANNING) |
| CW25 | BLOCKED | READY_REVIEW | resume(READY_REVIEW) |
| CW26 | BLOCKED | READY | resume(READY) |
| CW27 | BLOCKED | LEASED | resume(LEASED) |
| CW28 | BLOCKED | IMPLEMENTING | resume(IMPLEMENTING) |
| CW29 | BLOCKED | VERIFYING | resume(VERIFYING) |
| CW30 | BLOCKED | REVIEW | resume(REVIEW) |
| CW31 | BLOCKED | MERGE_QUEUED | resume(MERGE_QUEUED) |
| CW32 | BLOCKED | MERGED | resume(MERGED) |
| CW33 | BLOCKED | DEPLOYING | resume(DEPLOYING) |
| CW34 | BLOCKED | OBSERVING | resume(OBSERVING) |
| CW-B35 | INBOX | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B36 | TRIAGED | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B37 | PLANNING | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B38 | READY_REVIEW | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B39 | READY | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B40 | LEASED | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B41 | IMPLEMENTING | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B42 | VERIFYING | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B43 | REVIEW | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B44 | MERGE_QUEUED | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B45 | MERGED | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B46 | DEPLOYING | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B47 | OBSERVING | BLOCKED | wait/guard-fail; save exact continuation |
| CW-B48 | BLOCKED | BLOCKED | wait/guard-fail; save exact continuation |
| CW-C49 | INBOX | CANCEL_REQUESTED | authenticated cancel |
| CW-C50 | TRIAGED | CANCEL_REQUESTED | authenticated cancel |
| CW-C51 | PLANNING | CANCEL_REQUESTED | authenticated cancel |
| CW-C52 | READY_REVIEW | CANCEL_REQUESTED | authenticated cancel |
| CW-C53 | READY | CANCEL_REQUESTED | authenticated cancel |
| CW-C54 | LEASED | CANCEL_REQUESTED | authenticated cancel |
| CW-C55 | IMPLEMENTING | CANCEL_REQUESTED | authenticated cancel |
| CW-C56 | VERIFYING | CANCEL_REQUESTED | authenticated cancel |
| CW-C57 | REVIEW | CANCEL_REQUESTED | authenticated cancel |
| CW-C58 | MERGE_QUEUED | CANCEL_REQUESTED | authenticated cancel |
| CW-C59 | MERGED | CANCEL_REQUESTED | authenticated cancel |
| CW-C60 | DEPLOYING | CANCEL_REQUESTED | authenticated cancel |
| CW-C61 | OBSERVING | CANCEL_REQUESTED | authenticated cancel |
| CW-C62 | BLOCKED | CANCEL_REQUESTED | authenticated cancel |
| CW-C63 | QUARANTINED | CANCEL_REQUESTED | authenticated cancel+effect reconciliation scheduled |
| CW-C64 | ROLLED_BACK | CANCEL_REQUESTED | authenticated cancel first arrives after rollback settlement or was persisted during rollback; exact expected-version/disposition-presence CAS selects the private owner |
| CW-CQ | CANCEL_REQUESTED | QUIESCING | epoch advanced/grants revoked |
| CW-QC | QUIESCING | CLEANING | direct termination receipt or `quiescence-closed` |
| CW-R1 | MERGED | ROLLBACK_REQUESTED | stop/regression |
| CW-R2 | DEPLOYING | ROLLBACK_REQUESTED | stop/regression |
| CW-R3 | OBSERVING | ROLLBACK_REQUESTED | stop/regression |
| CW-R4 | ROLLBACK_REQUESTED | ROLLING_BACK | fresh rollback authority |
| CW-R5 | ROLLING_BACK | ROLLBACK_VERIFYING | restoration receipt |
| CW-R6 | ROLLBACK_VERIFYING | ROLLBACK_VERIFIED | protected verifier+known telemetry |
| CW-R7 | ROLLBACK_VERIFYING | ROLLBACK_FAILED | failed/unknown/timeout |
| CW-R8 | ROLLBACK_FAILED | ROLLING_BACK | approved retry+budget |
| CW-R9 | ROLLBACK_FAILED | BLOCKED | exhausted+human owner |
| CW-R10 | ROLLBACK_VERIFIED | ROLLED_BACK | verification sealed |
| CW-R11 | ROLLED_BACK | CLEANING | rollback outcome recorded |
| CW-R12 | QUARANTINED | ROLLBACK_REQUESTED | protected effect disposition proves exposure; create rollback saga |
| CW-R13 | BLOCKED | ROLLBACK_VERIFYING | protected rollback remediation closed; resume real verification |
| CW-R16 | BLOCKED | ROLLBACK_REQUESTED | protected reconciliation proves exposure; atomically create the unique bound rollback saga |
| CW-R17 | CANCEL_REQUESTED | ROLLBACK_REQUESTED | cancellation safety allowlist proves exposure; atomically create the unique bound rollback saga |
| CW-R18 | QUIESCING | ROLLBACK_REQUESTED | cancellation safety allowlist proves exposure; atomically create the unique bound rollback saga |
| CW-R14 | REVIEW | ROLLBACK_REQUESTED | exposed direct widening-effect failure or synchronized control degradation |
| CW-R15 | MERGE_QUEUED | ROLLBACK_REQUESTED | exposed direct promotion-effect failure or synchronized control degradation |
| CW-Q1 | QUARANTINED | CLEANING | typed disposition; not success unless eligible |
| CW-Q2 | QUARANTINED | REVIEW | verified reconciliation receipt; resume exact saved review continuation |
| CW-Q3 | QUARANTINED | MERGE_QUEUED | verified reconciliation receipt; resume exact saved pre-merge continuation |
| CW-N1 | REVIEW | OBSERVING | verified `NoPublicationReceipt`; no external publication requested or sent |
| CW-F1 | PLANNING | CLEANING | declared failure |
| CW-F2 | VERIFYING | CLEANING | exhausted failure |
| CW-F3 | REVIEW | CLEANING | denied/final failure |
| CW-F4 | MERGE_QUEUED | CLEANING | protected no-exposure promotion-effect failure |
| CW-X1 | READY_REVIEW | PLANNING | request changes / stale subject |
| CW-X2 | BLOCKED | CLEANING | final blocked disposition; cleanup required |
| CW-X3 | BLOCKED | QUARANTINED | unresolved security/effect evidence |
| CW-X4 | DEPLOYING | QUARANTINED | ambiguous deployment effect |

Canonical entry to `BLOCKED` and `CANCEL_REQUESTED` is deliberately enumerated above. States not listed as a source cannot take that cross-cutting edge. `QUARANTINED -> CLEANING` does not itself select success; §12 determines the effect result and the work outcome receipt selects `FAILED` or accepted-risk eligibility.

## 3. Common factory row semantics

In factory tables, `finish-ok` requires `clean` and projects `CLEANING>DONE`; `finish-fail` requires `clean` and projects `CLEANING>FAILED`; `finish-cancel` requires `clean` and projects `CLEANING>CANCELLED`. `cancel-start`, `cancel-quiesce`, and `cancel-clean` always advance the cancellation epoch, revoke authority, settle effects, then enter cleanup. The rows below explicitly include those edges for each built-in; this paragraph only defines their guards and does not create edges.
## 4. IDEATION factory v1

Initial: `CAPTURED`. Terminals: `SUCCEEDED`, `FAILED`, `CANCELLED`. `HANDOFF` maps to parent canonical `READY`; its BUILD child is separate and begins at canonical `INBOX`.

| ID | Source | Target | Guard / trigger | Canonical projection | Wait / stale / retry | Effects / cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| I01 | CAPTURED | DISCOVERING | valid | INBOX>TRIAGED | none | fx-none | - |
| I02 | DISCOVERING | NEEDS_INPUT | material ambiguity | TRIAGED>BLOCKED | W(input) | notify | - |
| I03 | NEEDS_INPUT | DISCOVERING | valid answer+fresh | BLOCKED>TRIAGED | answer receipt | fx-none | - |
| I04 | NEEDS_INPUT | STALE | input changed/expired/withdrawn | BLOCKED>PLANNING | wait closed; replan | fx-none | - |
| I05 | DISCOVERING | SYNTHESIZING | enough evidence | TRIAGED>PLANNING | none | fx-none | - |
| I06 | SYNTHESIZING | DECISION_REVIEW | decision sealed | PLANNING>READY_REVIEW | none | fx-none | - |
| I07 | DECISION_REVIEW | ACCEPTED | DecisionRecord accept | READY_REVIEW>READY | decision receipt | fx-none | - |
| I08 | DECISION_REVIEW | SYNTHESIZING | request changes | READY_REVIEW>PLANNING | wait closed | fx-none | - |
| I09 | ACCEPTED | HANDOFF | child creation admitted and CompositionLink persisted | S | none | CHILD(INBOX); no child advance | - |
| I10 | HANDOFF | CLEANING | bound child SUCCEEDED receipt+child clean | READY>BLOCKED>CLEANING | child wait closed | schedule parent cleanup | - |
| I11 | STALE | SYNTHESIZING | fresh inputs | S | replan | fx-none | - |
| I12 | DISCOVERING | BLOCKED | dependency/policy wait | TRIAGED>BLOCKED | W(dependency) | notify | - |
| I13 | BLOCKED | DISCOVERING | resume receipt | BLOCKED>TRIAGED | resume | fx-none | - |
| I14 | CLEANING | SUCCEEDED | clean+bound child outcome SUCCEEDED | CLEANING>DONE | none | prior cleanup receipts | success |
| I15 | CAPTURED | CANCEL_REQUESTED | cancel | INBOX>CANCEL_REQUESTED | cancel | fx-none | - |
| I16 | DISCOVERING | CANCEL_REQUESTED | cancel | TRIAGED>CANCEL_REQUESTED | cancel | fx-none | - |
| I17 | NEEDS_INPUT | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | wait cancelled | fx-none | - |
| I18 | SYNTHESIZING | CANCEL_REQUESTED | cancel | PLANNING>CANCEL_REQUESTED | cancel | fx-none | - |
| I19 | DECISION_REVIEW | CANCEL_REQUESTED | cancel | READY_REVIEW>CANCEL_REQUESTED | cancel | fx-none | - |
| I20 | ACCEPTED | CANCEL_REQUESTED | cancel | READY>CANCEL_REQUESTED | cancel | fx-none | - |
| I21 | HANDOFF | CANCEL_REQUESTED | cancel parent and propagate child cancellation epoch | READY>CANCEL_REQUESTED | child wait cancelled | stop/cancel child | - |
| I22 | BLOCKED | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | wait cancelled | fx-none | - |
| I23 | CANCEL_REQUESTED | QUIESCING | cancel-start | CANCEL_REQUESTED>QUIESCING | none | revoke | - |
| I24 | QUIESCING | CLEANING | direct termination receipt or quiescence-closed | QUIESCING>CLEANING | none | schedule cleanup | - |
| I25 | CLEANING | CANCELLED | clean+cancel disposition | CLEANING>CANCELLED | none | prior cleanup receipts | cancelled |
| I26 | SYNTHESIZING | CLEANING | irrecoverable contract failure | PLANNING>CLEANING | exhausted/final receipt | schedule cleanup | - |
| I27 | DISCOVERING | QUARANTINED | untrusted/unknown evidence | TRIAGED>BLOCKED>QUARANTINED | human disposition | isolate | - |
| I28 | QUARANTINED | CLEANING | declare failed | QUARANTINED>CLEANING | receipt | schedule cleanup | - |
| I29 | HANDOFF | CLEANING | bound child FAILED receipt+child clean | READY>BLOCKED>CLEANING | child wait closed | schedule parent cleanup | - |
| I30 | HANDOFF | CLEANING | bound child CANCELLED receipt+child clean | READY>BLOCKED>CLEANING | child wait closed | schedule parent cleanup | - |
| I31 | CLEANING | FAILED | clean+failure or child FAILED disposition | CLEANING>FAILED | none | prior cleanup receipts | failed |
| I32 | DECISION_REVIEW | CLEANING | DecisionRecord deny | READY_REVIEW>PLANNING>CLEANING | wait closed | schedule cleanup | - |
| I33 | DECISION_REVIEW | SYNTHESIZING | decision expiry/withdrawal/stale subject | READY_REVIEW>PLANNING | wait closed; replace subject | invalidate downstream authority | - |
| I34 | STALE | CANCEL_REQUESTED | authenticated cancel | PLANNING>CANCEL_REQUESTED | cancel | revoke | - |
| I35 | QUARANTINED | CANCEL_REQUESTED | authenticated cancel; typed disposition/reconciliation scheduled | QUARANTINED>CANCEL_REQUESTED | cancel | revoke; settle effect | - |
| I36 | CLEANING | CLEANING | authenticated cancel adopted before terminalization | S | cancel disposition replaces success/failure | preserve CleanupItems | - |
| I37 | QUIESCING | QUIESCING | repeated authenticated cancel safety-deferred | S | existing quiescence continues | no new authority | - |

## 5. BUILD factory v1

Initial: `CREATED` at canonical `INBOX`. Terminals: `SUCCEEDED`, `FAILED`, `CANCELLED`.

| ID | Source | Target | Guard / trigger | Canonical projection | Wait / stale / retry | Effects / cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| B00 | CREATED | INTAKE | factory creation/entry validated | INBOX>TRIAGED | none | none | - |
| B01 | INTAKE | NEEDS_INPUT | ambiguous | TRIAGED>BLOCKED | W(input) | none | - |
| B02 | NEEDS_INPUT | SPECIFYING | answer+fresh | BLOCKED>PLANNING | answer | none | - |
| B03 | INTAKE | SPECIFYING | valid | TRIAGED>PLANNING | none | none | - |
| B04 | SPECIFYING | PLANNING | spec sealed | S | none | none | - |
| B05 | PLANNING | READY_REVIEW | oracle/risk/rollback complete | PLANNING>READY_REVIEW | none | none | - |
| B06 | READY_REVIEW | ADMISSION_WAIT | admission decision issued | READY_REVIEW>READY | W(admission) | none | - |
| B07 | ADMISSION_WAIT | LEASED | ready+lease-created | READY>LEASED | wait closed | outbox | - |
| B08 | LEASED | IMPLEMENTING | lease | LEASED>IMPLEMENTING | none | typed commands | - |
| B09 | IMPLEMENTING | VERIFYING | outputs sealed | IMPLEMENTING>VERIFYING | none | none | - |
| B10 | VERIFYING | IMPLEMENTING | oracle fail+repair | VERIFYING>IMPLEMENTING | budget | none | - |
| B11 | VERIFYING | REVIEW | oracle pass | VERIFYING>REVIEW | none | none | - |
| B12 | REVIEW | IMPLEMENTING | changes requested | REVIEW>IMPLEMENTING | stale reviews | none | - |
| B13 | REVIEW | MERGE_WAIT | review pass | REVIEW>MERGE_QUEUED | none | fx-intent | - |
| B14 | MERGE_WAIT | REVIEW | head/check changed | MERGE_QUEUED>REVIEW | stale approval | none | - |
| B15 | MERGE_WAIT | READY_REVIEW | plan/policy changed | MERGE_QUEUED>READY_REVIEW | stale decision | none | - |
| B16 | MERGE_WAIT | MERGED | receipt verified | MERGE_QUEUED>MERGED | none | settled effect | - |
| B17 | MERGED | DEPLOYING | deploy authorized | MERGED>DEPLOYING | none | fx-intent | - |
| B18 | MERGED | OBSERVING | no-deploy receipt | MERGED>OBSERVING | none | none | - |
| B19 | DEPLOYING | OBSERVING | deploy receipt | DEPLOYING>OBSERVING | none | settled effect | - |
| B20 | OBSERVING | CLEANING | outcome complete | OBSERVING>CLEANING | none | cleanup | - |
| B21 | CLEANING | SUCCEEDED | finish-ok | CLEANING>DONE | none | cleanup receipts | success |
| B22 | IMPLEMENTING | STALE | bound input changed | IMPLEMENTING>BLOCKED>PLANNING | stale; revoke | settle | - |
| B23 | STALE | PLANNING | fresh replan | S | replan | none | - |
| B24 | ADMISSION_WAIT | BLOCKED | expiry/revoke/quota | READY>BLOCKED | W(admission) | none | - |
| B25 | BLOCKED | READY_REVIEW | resolution changes bound input | BLOCKED>READY_REVIEW | resume | none | - |
| B26 | BLOCKED | ADMISSION_WAIT | same digest resumes | BLOCKED>READY | resume | none | - |
| B27 | DEPLOYING | UNKNOWN_EFFECT | ambiguous response | DEPLOYING>QUARANTINED | §12 | reconcile | - |
| B28 | UNKNOWN_EFFECT | QUARANTINED | unresolved | S | human disposition | isolate | - |
| B29 | MERGED | ROLLBACK_REQUESTED | stop | MERGED>ROLLBACK_REQUESTED | none | revoke | - |
| B30 | DEPLOYING | ROLLBACK_REQUESTED | stop | DEPLOYING>ROLLBACK_REQUESTED | none | revoke | - |
| B31 | OBSERVING | ROLLBACK_REQUESTED | regression | OBSERVING>ROLLBACK_REQUESTED | none | revoke | - |
| B32 | ROLLBACK_REQUESTED | ROLLING_BACK | fresh authority | ROLLBACK_REQUESTED>ROLLING_BACK | none | fx-intent | - |
| B33 | ROLLING_BACK | ROLLBACK_VERIFYING | restoration receipt | ROLLING_BACK>ROLLBACK_VERIFYING | none | verify | - |
| B34 | ROLLBACK_VERIFYING | ROLLBACK_VERIFIED | known good | ROLLBACK_VERIFYING>ROLLBACK_VERIFIED | none | none | - |
| B35 | ROLLBACK_VERIFYING | ROLLBACK_FAILED | fail/unknown | ROLLBACK_VERIFYING>ROLLBACK_FAILED | retry wait | none | - |
| B36 | ROLLBACK_FAILED | ROLLING_BACK | approved+budget | ROLLBACK_FAILED>ROLLING_BACK | retry | fx-intent | - |
| B37 | ROLLBACK_FAILED | ROLLBACK_REMEDIATION_WAIT | exhausted/retry forbidden | ROLLBACK_FAILED>BLOCKED | bounded remediation wait | atomically invoke RO00-B to create protected rollback-safety RemediationObligation bound to rollback saga; revoke authority; retain exposure and every resource block | - |
| B38 | ROLLBACK_VERIFIED | ROLLED_BACK | sealed+fresh independent verification result and genuine restoration receipt still current | ROLLBACK_VERIFIED>ROLLED_BACK | none | atomically remove only the exact rollback-safety exposure/resource blocks by version CAS; same command/bytes replays, conflict rejects | - |
| B39 | ROLLED_BACK | CLEANING | outcome receipt+no persisted cancellation disposition | ROLLED_BACK>CLEANING | none | create ordinary cleanup by exact version CAS; same command/bytes replays, conflict rejects | - |
| B40 | CLEANING | FAILED | finish-fail | CLEANING>FAILED | none | cleanup receipts | failed |
| B41 | QUARANTINED | CLEANING | declare-failed/eligible accepted-risk | QUARANTINED>CLEANING | typed receipt | cleanup | - |
| B42 | INTAKE | CANCEL_REQUESTED | cancel | TRIAGED>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B43 | NEEDS_INPUT | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B44 | SPECIFYING | CANCEL_REQUESTED | cancel | PLANNING>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B45 | PLANNING | CANCEL_REQUESTED | cancel | PLANNING>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B46 | READY_REVIEW | CANCEL_REQUESTED | cancel | READY_REVIEW>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B47 | ADMISSION_WAIT | CANCEL_REQUESTED | cancel | READY>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B48 | LEASED | CANCEL_REQUESTED | cancel | LEASED>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B49 | IMPLEMENTING | CANCEL_REQUESTED | cancel | IMPLEMENTING>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B50 | VERIFYING | CANCEL_REQUESTED | cancel | VERIFYING>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B51 | REVIEW | CANCEL_REQUESTED | cancel | REVIEW>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B52 | MERGE_WAIT | CANCEL_REQUESTED | cancel | MERGE_QUEUED>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B53 | MERGED | CANCEL_REQUESTED | cancel | MERGED>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B54 | DEPLOYING | CANCEL_REQUESTED | cancel | DEPLOYING>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B55 | OBSERVING | CANCEL_REQUESTED | cancel | OBSERVING>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B56 | STALE | CANCEL_REQUESTED | cancel | PLANNING>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B57 | BLOCKED | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | cancel/waits close | revoke/settle | - |
| B58 | UNKNOWN_EFFECT | CANCEL_REQUESTED | authenticated cancel adopted; reconciliation scheduled | QUARANTINED>CANCEL_REQUESTED | cancel/waits close | revoke; reconcile effect | - |
| B59 | QUARANTINED | CANCEL_REQUESTED | authenticated cancel+typed effect disposition bound | QUARANTINED>CANCEL_REQUESTED | waits closed | revoke; settle effect | - |
| B60 | CANCEL_REQUESTED | QUIESCING | cancel-start | CANCEL_REQUESTED>QUIESCING | none | revoke | - |
| B61 | QUIESCING | CLEANING | cancel-quiesce | QUIESCING>CLEANING | none | cleanup | - |
| B62 | CLEANING | CANCELLED | clean+cancel disposition | CLEANING>CANCELLED | none | prior cleanup receipts | cancelled |
| B63 | VERIFYING | CLEANING | oracle failed and repair budget exhausted | VERIFYING>CLEANING | final/exhaustion receipt | schedule cleanup | - |
| B64 | IMPLEMENTING | CLEANING | nonretryable execution failure proven | IMPLEMENTING>VERIFYING>CLEANING | final receipt | schedule cleanup | - |
| B65 | CREATED | CANCEL_REQUESTED | authenticated cancel | INBOX>CANCEL_REQUESTED | cancel adopted/deferred | advance epoch/revoke | - |
| B66 | ROLLBACK_REQUESTED | ROLLBACK_REQUESTED | authenticated cancel adopted; safety rollback continues | S | cancel adopted/deferred | persist cancel disposition | - |
| B67 | ROLLING_BACK | ROLLING_BACK | authenticated cancel adopted; safety rollback continues | S | cancel adopted/deferred | persist cancel disposition | - |
| B68 | ROLLBACK_VERIFYING | ROLLBACK_VERIFYING | authenticated cancel adopted; safety rollback continues | S | cancel adopted/deferred | persist cancel disposition | - |
| B69 | ROLLBACK_FAILED | ROLLBACK_FAILED | authenticated cancel safety-deferred to approved retry or final disposition | S | cancel adopted/deferred | persist cancel disposition | - |
| B70 | ROLLBACK_VERIFIED | ROLLBACK_VERIFIED | authenticated cancel adopted; seal rollback first | S | cancel adopted/deferred | persist cancel disposition | - |
| B71 | ROLLED_BACK | CANCEL_REQUESTED | first authenticated cancellation arrives after B38; cancellation disposition is absent and expected Work version matches | ROLLED_BACK>CANCEL_REQUESTED | cancel adopted | atomically persist disposition, advance epoch, and revoke under one expected-version/absent-disposition CAS; conflicts with B39 and B71-P | - |
| B71-P | ROLLED_BACK | CANCEL_REQUESTED | authenticated cancellation disposition was persisted during rollback and B38 has now settled | ROLLED_BACK>CANCEL_REQUESTED | cancel continuation | exact expected-version/persisted-disposition CAS; no second persistence; conflicts with B39 and B71 | - |
| B71-R | CANCEL_REQUESTED | CANCEL_REQUESTED | exact same authenticated cancellation request/disposition is already persisted | S | replay | return byte-identical original receipt; different bytes or request identity reject | - |
| B72 | CLEANING | CLEANING | authenticated cancel adopted before terminalization | S | cancel adopted/deferred | preserve CleanupItems | - |
| B73 | QUIESCING | QUIESCING | repeated authenticated cancel safety-deferred | S | cancel adopted/deferred | no new authority | - |
| B74 | ROLLBACK_REMEDIATION_WAIT | ROLLBACK_VERIFYING | bound obligation CLOSED by RO09+genuine restoration receipt+fresh independent verification authority | BLOCKED>ROLLBACK_VERIFYING | remediation retry completed | preserve exposure/resource blocks until verification seals | - |
| B75 | ROLLBACK_REMEDIATION_WAIT | ROLLBACK_REMEDIATION_WAIT | authenticated cancel recorded/adopted; safety settlement deferred | S | cancel disposition persists | no cleanup or terminalization; no resource release | - |
| B76 | ROLLBACK_REMEDIATION_WAIT | ROLLBACK_REMEDIATION_WAIT | bound obligation revoked by RO01-R/RO02-R/RO11/RO12/RO13 | S | RO06 bounded resurface; RO14 is sole reauthorization | fence grants; retain exposure/resources | - |
| B77 | ROLLBACK_REMEDIATION_WAIT | ROLLBACK_REMEDIATION_WAIT | bounded reminder/escalation while obligation OPEN/IN_PROGRESS/VERIFYING/REVOKED | S | permanent wait remains observable | no generic BLOCKED resume/cancel/cleanup edge applies | - |


BUILD `ROLLBACK_REMEDIATION_WAIT` is a distinct private safety state even though its canonical projection is `BLOCKED`. B25, B26, B57, and every other generic `BLOCKED` resume/cancel edge match only private `BLOCKED`; they cannot match this state. B75 records cancellation without changing the safety state. Only B74 may leave it, and only after RO09 closure, genuine restoration, and independent verification authority. B34 and B38 must then prove `ROLLBACK_VERIFIED` and `ROLLED_BACK` before B39 cleanup or B71 cancellation continuation. RO09, B74, and B34 release no rollback-safety block; only B38 atomically removes the exact blocks. B39 requires an absent cancellation disposition and B71 atomically persists a first post-B38 request under the same expected-version/absence CAS; B71-P requires a disposition persisted during rollback, and B71-R is only byte-identical replay after persistence. These branches are pairwise exclusive with B39 and replay-stable. An unresolved obligation can remain on B77 forever without releasing exposure or resources.

## 6. MAINTENANCE factory v1

Initial: `SIGNAL_RECEIVED`. Terminals: `SUCCEEDED`, `FAILED`, `CANCELLED`.

| ID | Source | Target | Guard / trigger | Canonical projection | Wait / stale / retry | Effects / cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| M01 | SIGNAL_RECEIVED | CORRELATED | valid | INBOX>TRIAGED | none | none | - |
| M02 | CORRELATED | DIAGNOSED | correlation sealed | TRIAGED>PLANNING | none | none | - |
| M03 | DIAGNOSED | NEEDS_INPUT | ambiguity | PLANNING>BLOCKED | W(input) | notify | - |
| M04 | NEEDS_INPUT | DIAGNOSED | answer+fresh | BLOCKED>PLANNING | answer | none | - |
| M05 | DIAGNOSED | PROPOSED | oracle/window/rollback complete | PLANNING>READY_REVIEW | none | none | - |
| M06 | PROPOSED | SUPPRESSED | signed suppression | READY_REVIEW>BLOCKED | W(suppression expiry) | none | - |
| M07 | SUPPRESSED | PROPOSED | expiry/resurface | BLOCKED>READY_REVIEW | resume | none | - |
| M08 | PROPOSED | SCHEDULED | admission decision | READY_REVIEW>READY | W(admission) | none | - |
| M09 | SCHEDULED | LEASED | ready+lease-created | READY>LEASED | none | outbox | - |
| M10 | LEASED | EXECUTING | lease+BUILD child creation receipt | LEASED>IMPLEMENTING | none | CHILD(INBOX); child follows B00+normal BUILD rows | - |
| M11 | EXECUTING | VERIFIED | bound child SUCCEEDED receipt+child clean+technical oracle | IMPLEMENTING>VERIFYING | child terminal wait closed | consume child receipt | - |
| M12 | VERIFIED | OBSERVING | verification pass | VERIFYING>REVIEW>MERGE_QUEUED>MERGED>OBSERVING | none | effect receipts/no-deploy | - |
| M13 | OBSERVING | RESOLVED | window pass | S | none | outcome | - |
| M14 | RESOLVED | CLEANING | settled | OBSERVING>CLEANING | none | cleanup | - |
| M15 | CLEANING | SUCCEEDED | finish-ok | CLEANING>DONE | none | receipts | success |
| M16 | EXECUTING | UNKNOWN_EFFECT | ambiguous | IMPLEMENTING>BLOCKED>QUARANTINED | §12 | reconcile | - |
| M17 | UNKNOWN_EFFECT | QUARANTINED | unresolved | S | human disposition | isolate | - |
| M18 | CORRELATED | STALE | signal changed | TRIAGED>BLOCKED>PLANNING | stale | none | - |
| M19 | STALE | CORRELATED | fresh recompute | PLANNING>BLOCKED>TRIAGED | resume | none | - |
| M20 | DIAGNOSED | BLOCKED | dependency/policy | PLANNING>BLOCKED | W(dependency) | none | - |
| M21 | BLOCKED | DIAGNOSED | resume | BLOCKED>PLANNING | resume | none | - |
| M22 | OBSERVING | ROLLBACK_REQUESTED | regression | OBSERVING>ROLLBACK_REQUESTED | none | revoke | - |
| M23 | ROLLBACK_REQUESTED | ROLLING_BACK | fresh authority | ROLLBACK_REQUESTED>ROLLING_BACK | none | fx-intent | - |
| M24 | ROLLING_BACK | ROLLBACK_VERIFYING | receipt | ROLLING_BACK>ROLLBACK_VERIFYING | none | verify | - |
| M25 | ROLLBACK_VERIFYING | ROLLBACK_VERIFIED | known good | ROLLBACK_VERIFYING>ROLLBACK_VERIFIED | none | none | - |
| M26 | ROLLBACK_VERIFYING | ROLLBACK_FAILED | fail/unknown | ROLLBACK_VERIFYING>ROLLBACK_FAILED | retry wait | none | - |
| M27 | ROLLBACK_FAILED | ROLLING_BACK | approved+budget | ROLLBACK_FAILED>ROLLING_BACK | retry | fx-intent | - |
| M28 | ROLLBACK_FAILED | ROLLBACK_REMEDIATION_WAIT | exhausted/retry forbidden | ROLLBACK_FAILED>BLOCKED | bounded remediation wait | atomically invoke RO00-M to create protected rollback-safety RemediationObligation bound to rollback saga; revoke authority; retain exposure and every resource block | - |
| M29 | ROLLBACK_VERIFIED | ROLLED_BACK | sealed+fresh independent verification result and genuine restoration receipt still current | ROLLBACK_VERIFIED>ROLLED_BACK | none | atomically remove only the exact rollback-safety exposure/resource blocks by version CAS; same command/bytes replays, conflict rejects | - |
| M30 | ROLLED_BACK | CLEANING | outcome+no persisted cancellation disposition | ROLLED_BACK>CLEANING | none | create ordinary cleanup by exact version CAS; same command/bytes replays, conflict rejects | - |
| M31 | CLEANING | FAILED | finish-fail | CLEANING>FAILED | none | receipts | failed |
| M32 | QUARANTINED | CLEANING | disposition | QUARANTINED>CLEANING | receipt | cleanup | - |
| M33 | SIGNAL_RECEIVED | CANCEL_REQUESTED | cancel | INBOX>CANCEL_REQUESTED | cancel | revoke | - |
| M34 | CORRELATED | CANCEL_REQUESTED | cancel | TRIAGED>CANCEL_REQUESTED | cancel | revoke | - |
| M35 | DIAGNOSED | CANCEL_REQUESTED | cancel | PLANNING>CANCEL_REQUESTED | cancel | revoke | - |
| M36 | NEEDS_INPUT | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | cancel | revoke | - |
| M37 | PROPOSED | CANCEL_REQUESTED | cancel | READY_REVIEW>CANCEL_REQUESTED | cancel | revoke | - |
| M38 | SUPPRESSED | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | cancel | revoke | - |
| M39 | SCHEDULED | CANCEL_REQUESTED | cancel | READY>CANCEL_REQUESTED | cancel | revoke | - |
| M40 | LEASED | CANCEL_REQUESTED | cancel | LEASED>CANCEL_REQUESTED | cancel | revoke | - |
| M41 | EXECUTING | CANCEL_REQUESTED | cancel | IMPLEMENTING>CANCEL_REQUESTED | cancel | revoke | - |
| M42 | VERIFIED | CANCEL_REQUESTED | cancel | VERIFYING>CANCEL_REQUESTED | cancel | revoke | - |
| M43 | OBSERVING | CANCEL_REQUESTED | cancel | OBSERVING>CANCEL_REQUESTED | cancel | revoke | - |
| M44 | RESOLVED | CANCEL_REQUESTED | cancel | OBSERVING>CANCEL_REQUESTED | cancel | revoke | - |
| M45 | STALE | CANCEL_REQUESTED | cancel | PLANNING>CANCEL_REQUESTED | cancel | revoke | - |
| M46 | BLOCKED | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | cancel | revoke | - |
| M47 | CANCEL_REQUESTED | QUIESCING | cancel-start | CANCEL_REQUESTED>QUIESCING | none | revoke | - |
| M48 | QUIESCING | CLEANING | cancel-quiesce | QUIESCING>CLEANING | none | cleanup | - |
| M49 | CLEANING | CANCELLED | clean+cancel or child-CANCELLED disposition | CLEANING>CANCELLED | none | prior cleanup receipts | cancelled |
| M50 | EXECUTING | CLEANING | bound child FAILED receipt+child clean | IMPLEMENTING>VERIFYING>CLEANING | child wait closed | schedule parent cleanup | - |
| M51 | EXECUTING | CANCEL_REQUESTED | bound child CANCELLED receipt+propagation policy | IMPLEMENTING>CANCEL_REQUESTED | child wait closed | revoke/settle | - |
| M52 | UNKNOWN_EFFECT | CANCEL_REQUESTED | authenticated cancel; reconciliation scheduled | QUARANTINED>CANCEL_REQUESTED | cancel adopted/deferred | revoke; reconcile | - |
| M53 | QUARANTINED | CANCEL_REQUESTED | authenticated cancel+typed effect disposition | QUARANTINED>CANCEL_REQUESTED | cancel adopted/deferred | revoke; settle effect | - |
| M54 | ROLLBACK_REQUESTED | ROLLBACK_REQUESTED | authenticated cancel adopted; safety rollback continues | S | cancel adopted/deferred | persist cancel disposition | - |
| M55 | ROLLING_BACK | ROLLING_BACK | authenticated cancel adopted; safety rollback continues | S | cancel adopted/deferred | persist cancel disposition | - |
| M56 | ROLLBACK_VERIFYING | ROLLBACK_VERIFYING | authenticated cancel adopted; safety rollback continues | S | cancel adopted/deferred | persist cancel disposition | - |
| M57 | ROLLBACK_FAILED | ROLLBACK_FAILED | authenticated cancel safety-deferred to retry/final disposition | S | cancel adopted/deferred | persist cancel disposition | - |
| M58 | ROLLBACK_VERIFIED | ROLLBACK_VERIFIED | authenticated cancel adopted; seal rollback first | S | cancel adopted/deferred | persist cancel disposition | - |
| M59 | ROLLED_BACK | CANCEL_REQUESTED | first authenticated cancellation arrives after M29; cancellation disposition is absent and expected Work version matches | ROLLED_BACK>CANCEL_REQUESTED | cancel adopted | atomically persist disposition, advance epoch, and revoke under one expected-version/absent-disposition CAS; conflicts with M30 and M59-P | - |
| M59-P | ROLLED_BACK | CANCEL_REQUESTED | authenticated cancellation disposition was persisted during rollback and M29 has now settled | ROLLED_BACK>CANCEL_REQUESTED | cancel continuation | exact expected-version/persisted-disposition CAS; no second persistence; conflicts with M30 and M59 | - |
| M59-R | CANCEL_REQUESTED | CANCEL_REQUESTED | exact same authenticated cancellation request/disposition is already persisted | S | replay | return byte-identical original receipt; different bytes or request identity reject | - |
| M60 | CLEANING | CLEANING | authenticated cancel adopted before terminalization | S | cancel adopted/deferred | preserve CleanupItems | - |
| M61 | QUIESCING | QUIESCING | repeated authenticated cancel safety-deferred | S | cancel adopted/deferred | no new authority | - |
| M62 | ROLLBACK_REMEDIATION_WAIT | ROLLBACK_VERIFYING | bound obligation CLOSED by RO09+genuine restoration receipt+fresh independent verification authority | BLOCKED>ROLLBACK_VERIFYING | remediation retry completed | preserve exposure/resource blocks until verification seals | - |
| M63 | ROLLBACK_REMEDIATION_WAIT | ROLLBACK_REMEDIATION_WAIT | authenticated cancel recorded/adopted; safety settlement deferred | S | cancel disposition persists | no cleanup or terminalization; no resource release | - |
| M64 | ROLLBACK_REMEDIATION_WAIT | ROLLBACK_REMEDIATION_WAIT | bound obligation revoked by RO01-R/RO02-R/RO11/RO12/RO13 | S | RO06 bounded resurface; RO14 is sole reauthorization | fence grants; retain exposure/resources | - |
| M65 | ROLLBACK_REMEDIATION_WAIT | ROLLBACK_REMEDIATION_WAIT | bounded reminder/escalation while obligation OPEN/IN_PROGRESS/VERIFYING/REVOKED | S | permanent wait remains observable | no generic BLOCKED resume/cancel/cleanup edge applies | - |


MAINTENANCE `ROLLBACK_REMEDIATION_WAIT` has the same closed safety semantics. M21 and M46 match only private `BLOCKED` and cannot resume or cancel it. M63 records cancellation without terminalizing. Only M62 may leave after RO09 closure, genuine restoration, and independent verification authority; M25 and M29 must then prove `ROLLBACK_VERIFIED` and `ROLLED_BACK` before M30 cleanup or M59 cancellation continuation. RO09, M62, and M25 release no rollback-safety block; only M29 atomically removes the exact blocks. M30 requires an absent cancellation disposition and M59 atomically persists a first post-M29 request under the same expected-version/absence CAS; M59-P requires a disposition persisted during rollback, and M59-R is only byte-identical replay after persistence. These branches are pairwise exclusive with M30 and replay-stable. M64 covers revocation and M65 is the permanent observable wait with exposure and resource blocks retained.

## 7. DEEP-RESEARCH factory v1

Initial: `CREATED` at canonical `INBOX`. Terminals: `SUCCEEDED`, `FAILED`, `CANCELLED`.

| ID | Source | Target | Guard / trigger | Canonical projection | Wait / stale / retry | Effects / cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| D00 | CREATED | SCOPING | factory creation/entry validated | INBOX>TRIAGED>PLANNING | none | none | - |
| D01 | SCOPING | NEEDS_INPUT | ambiguity | PLANNING>BLOCKED | W(input) | none | - |
| D02 | NEEDS_INPUT | SCOPING | answer+fresh | BLOCKED>PLANNING | answer | none | - |
| D03 | SCOPING | OUTLINE_REVIEW | outline sealed | PLANNING>READY_REVIEW | none | none | - |
| D04 | OUTLINE_REVIEW | ADMISSION_WAIT | ResearchDecision accept | READY_REVIEW>READY | W(admission) | none | - |
| D05 | OUTLINE_REVIEW | SCOPING | request changes | READY_REVIEW>PLANNING | none | none | - |
| D06 | ADMISSION_WAIT | LEASED | ready+lease-created | READY>LEASED | none | outbox | - |
| D07 | LEASED | COLLECTING | lease | LEASED>IMPLEMENTING | none | research proxy | - |
| D08 | COLLECTING | NORMALIZING | snapshots sealed | S | none | none | - |
| D09 | COLLECTING | REFRESH_WAIT | source unavailable | IMPLEMENTING>BLOCKED | W(refresh) | none | - |
| D10 | REFRESH_WAIT | COLLECTING | fresh snapshot | BLOCKED>IMPLEMENTING | resume | research proxy | - |
| D11 | REFRESH_WAIT | STALE | expiry/withdraw/input change | BLOCKED>PLANNING | wait closed | none | - |
| D12 | NORMALIZING | CONFLICT_REVIEW | claims/edges sealed | IMPLEMENTING>VERIFYING | none | none | - |
| D13 | CONFLICT_REVIEW | GAP_ANALYSIS | conflicts classified | S | none | none | - |
| D14 | GAP_ANALYSIS | REFRESH_WAIT | material gap | VERIFYING>BLOCKED | W(refresh) | none | - |
| D15 | GAP_ANALYSIS | SYNTHESIZING | closure met | VERIFYING>IMPLEMENTING | none | none | - |
| D16 | SYNTHESIZING | COMPLETION_VALIDATION | artifact sealed | IMPLEMENTING>VERIFYING | none | none | - |
| D17 | COMPLETION_VALIDATION | COLLECTING | validation gap | VERIFYING>IMPLEMENTING | retry+changed source | none | - |
| D18 | COMPLETION_VALIDATION | DECISION_REVIEW | validation pass | VERIFYING>REVIEW | none | none | - |
| D19 | DECISION_REVIEW | ACCEPTED_NO_PUBLICATION | ResearchDecision accept+protected `NoPublicationDisposition` and `NoPublicationReceipt` prove publication not requested, no publication intent exists, and no external write occurred | REVIEW>OBSERVING | none | fx-none; consumes CW-N1 receipt | - |
| D19P1 | DECISION_REVIEW | PUBLICATION_QUEUED | ResearchDecision accept+publication explicitly requested+fresh publication authority | REVIEW>MERGE_QUEUED | none | persist publication EffectIntent only | - |
| D19P2 | PUBLICATION_QUEUED | PUBLICATION_DISPATCHED | dispatcher records send attempt | S | none | dispatch publication effect; no merge claim | - |
| D19P3 | PUBLICATION_DISPATCHED | PUBLISHED | verified bound publication effect receipt+remote identity+explicit protected purpose-bound `NoDeploymentReceipt` | MERGE_QUEUED>MERGED>OBSERVING | none | CW14 rechecks verified-effect; CW16 independently rechecks `NoDeploymentReceipt` | - |
| D19P4 | PUBLICATION_DISPATCHED | QUARANTINED | publication effect UNKNOWN | MERGE_QUEUED>BLOCKED>QUARANTINED | bounded reconciliation | stop sends; §12 | - |
| D19P5 | PUBLICATION_DISPATCHED | PUBLICATION_FAILED | signed absence/no-application receipt+retry forbidden or exhausted+publication failure wait guard; save exact publication continuation | MERGE_QUEUED>BLOCKED | none | CW-B44 only; persist final no-application/no-retry disposition; no cleanup yet | - |
| D19P6 | QUARANTINED | PUBLISHED | ORIGINAL reconciliation yields verified publication receipt+remote identity+explicit protected purpose-bound `NoDeploymentReceipt` | QUARANTINED>MERGE_QUEUED>MERGED>OBSERVING | none | CW-Q3 rechecks saved continuation; CW14 rechecks verified effect; CW16 independently rechecks `NoDeploymentReceipt` | - |
| D19C1 | ACCEPTED_NO_PUBLICATION | CLEANING | accepted research outcome recorded | OBSERVING>CLEANING | none | schedule cleanup | - |
| D19C2 | PUBLISHED | CLEANING | published outcome recorded | OBSERVING>CLEANING | none | schedule cleanup | - |
| D19P7 | PUBLICATION_FAILED | CLEANING | previously committed signed final no-application/no-retry disposition+exact saved publication continuation | BLOCKED>CLEANING | none | CW-X2; schedule cleanup in this later transaction | - |
| D20 | DECISION_REVIEW | SYNTHESIZING | request changes | REVIEW>IMPLEMENTING | none | none | - |
| D21 | CLEANING | SUCCEEDED | finish-ok | CLEANING>DONE | none | receipts | success |
| D22 | COLLECTING | STALE | digest changed | IMPLEMENTING>BLOCKED>PLANNING | stale | none | - |
| D23 | NORMALIZING | STALE | digest changed | IMPLEMENTING>BLOCKED>PLANNING | stale | none | - |
| D24 | CONFLICT_REVIEW | STALE | digest changed | VERIFYING>BLOCKED>PLANNING | stale | none | - |
| D25 | STALE | SCOPING | fresh inputs | S | replan | none | - |
| D26 | SCOPING | BLOCKED | policy/dependency | PLANNING>BLOCKED | W(dependency) | none | - |
| D27 | BLOCKED | SCOPING | resume | BLOCKED>PLANNING | resume | none | - |
| D28 | QUARANTINED | CLEANING | declare failed | QUARANTINED>CLEANING | receipt | cleanup | - |
| D29 | CLEANING | FAILED | finish-fail | CLEANING>FAILED | none | receipts | failed |
| D30 | SCOPING | CANCEL_REQUESTED | cancel | PLANNING>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D31 | NEEDS_INPUT | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D32 | OUTLINE_REVIEW | CANCEL_REQUESTED | cancel | READY_REVIEW>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D33 | ADMISSION_WAIT | CANCEL_REQUESTED | cancel | READY>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D34 | LEASED | CANCEL_REQUESTED | cancel | LEASED>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D35 | COLLECTING | CANCEL_REQUESTED | cancel | IMPLEMENTING>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D36 | NORMALIZING | CANCEL_REQUESTED | cancel | IMPLEMENTING>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D37 | REFRESH_WAIT | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D38 | CONFLICT_REVIEW | CANCEL_REQUESTED | cancel | VERIFYING>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D39 | GAP_ANALYSIS | CANCEL_REQUESTED | cancel | VERIFYING>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D40 | SYNTHESIZING | CANCEL_REQUESTED | cancel | IMPLEMENTING>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D41 | COMPLETION_VALIDATION | CANCEL_REQUESTED | cancel | VERIFYING>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D42 | DECISION_REVIEW | CANCEL_REQUESTED | cancel | REVIEW>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D43 | STALE | CANCEL_REQUESTED | cancel | PLANNING>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D44 | BLOCKED | CANCEL_REQUESTED | cancel | BLOCKED>CANCEL_REQUESTED | cancel/wait close | revoke | - |
| D45 | QUARANTINED | CANCEL_REQUESTED | authenticated cancel+typed quarantine disposition | QUARANTINED>CANCEL_REQUESTED | cancel/wait close | revoke; settle effect | - |
| D46 | CANCEL_REQUESTED | QUIESCING | cancel-start | CANCEL_REQUESTED>QUIESCING | none | revoke | - |
| D47 | QUIESCING | CLEANING | cancel-quiesce | QUIESCING>CLEANING | none | cleanup | - |
| D48 | CLEANING | CANCELLED | clean+cancel disposition | CLEANING>CANCELLED | none | prior cleanup receipts | cancelled |
| D49 | COLLECTING | QUARANTINED | unknown/untrusted source or proxy effect after settlement attempt | IMPLEMENTING>BLOCKED>QUARANTINED | waits/effects settled or typed unresolved receipt | isolate evidence | - |
| D50 | COMPLETION_VALIDATION | QUARANTINED | untrusted validation/evidence conflict cannot be classified | VERIFYING>BLOCKED>QUARANTINED | typed quarantine receipt | isolate evidence | - |
| D51 | COMPLETION_VALIDATION | CLEANING | validation failed and refresh budget exhausted | VERIFYING>CLEANING | final/exhaustion receipt | schedule cleanup | - |
| D52 | DECISION_REVIEW | CLEANING | ResearchDecision deny | REVIEW>CLEANING | wait closed | schedule cleanup | - |
| D53 | DECISION_REVIEW | SYNTHESIZING | decision expiry/withdrawal/stale manifest | REVIEW>IMPLEMENTING | wait closed; revise/resubmit | invalidate downstream authority | - |
| D57 | ACCEPTED_NO_PUBLICATION | CANCEL_REQUESTED | authenticated cancel before cleanup entry | OBSERVING>CANCEL_REQUESTED | cancel | revoke | - |
| D58 | PUBLICATION_QUEUED | CANCEL_REQUESTED | authenticated cancel before send | MERGE_QUEUED>CANCEL_REQUESTED | cancel | cancel effect before send | - |
| D59 | PUBLICATION_DISPATCHED | CANCEL_REQUESTED | authenticated cancel; effect reconciliation required | MERGE_QUEUED>CANCEL_REQUESTED | cancel | reconcile/settle effect | - |
| D61 | PUBLICATION_FAILED | CANCEL_REQUESTED | authenticated cancel before later cleanup entry | BLOCKED>CANCEL_REQUESTED | cancel | preserve final no-application disposition; revoke | - |
| D60 | PUBLISHED | CANCEL_REQUESTED | authenticated cancel before cleanup entry | OBSERVING>CANCEL_REQUESTED | cancel | revoke | - |
| D54 | CREATED | CANCEL_REQUESTED | authenticated cancel | INBOX>CANCEL_REQUESTED | cancel | revoke | - |
| D55 | CLEANING | CLEANING | authenticated cancel adopted before terminalization | S | cancel disposition replaces success/failure | preserve CleanupItems | - |
| D56 | QUIESCING | QUIESCING | repeated authenticated cancel safety-deferred | S | existing quiescence continues | no new authority | - |

## 8. FactoryInstance aggregate v1

Initial: `CREATED`. Terminals: `SUCCEEDED`, `FAILED`, `CANCELLED`. `FAILURE_PENDING_CLEANUP` is nonterminal; `FAILED` is final and immutable.

| ID | Source | Target | Guard / trigger | Canonical | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| F01 | CREATED | VALIDATING | definition pinned | S | none | none | - |
| F02 | VALIDATING | WAITING_INPUT | missing typed input | S | W(input) | none | - |
| F03 | WAITING_INPUT | VALIDATING | answer+fresh | S | answer | none | - |
| F04 | WAITING_INPUT | BLOCKED | expiry/withdrawal | S | wait closed; owner disposition | none | - |
| F05 | VALIDATING | READY | compiler+guards pass | S | none | none | - |
| F06 | VALIDATING | FAILURE_PENDING_CLEANUP | invalid final | S | exhausted | cleanup required | not yet |
| F07 | VALIDATING | QUARANTINED | unknown contract/security input | S | human disposition | isolate | - |
| F08 | READY | RUNNING | child/node admitted | S | none | none | - |
| F09 | RUNNING | WAITING_INPUT | node requests human/input | S | W(input/human) | none | - |
| F10 | RUNNING | BLOCKED | dependency/policy/quota | S | W(dependency) | none | - |
| F11 | WAITING_INPUT | RUNNING | answer+continuation valid | S | answer | none | - |
| F12 | BLOCKED | VALIDATING | changed bound input | S | resume/revalidate | none | - |
| F13 | BLOCKED | RUNNING | same-digest continuation | S | resume | none | - |
| F14 | RUNNING | CLEANING | all nodes successful | S | none | cleanup | - |
| F15 | RUNNING | FAILURE_PENDING_CLEANUP | child final failure | S | exhausted | cleanup required | not yet |
| F16 | QUARANTINED | CLEANING | typed disposition | S | receipt | cleanup | - |
| F17 | FAILURE_PENDING_CLEANUP | CLEANING | failure sealed | S | none | cleanup | - |
| F18 | CLEANING | SUCCEEDED | clean+success | S | none | receipts | success |
| F19 | CLEANING | FAILED | clean+failed | S | none | receipts | failed |
| F20 | CREATED | CANCEL_REQUESTED | cancel | S | close wait | revoke/cancel children | - |
| F21 | VALIDATING | CANCEL_REQUESTED | cancel | S | close wait | revoke/cancel children | - |
| F22 | WAITING_INPUT | CANCEL_REQUESTED | cancel | S | close wait | revoke/cancel children | - |
| F23 | READY | CANCEL_REQUESTED | cancel | S | close wait | revoke/cancel children | - |
| F24 | RUNNING | CANCEL_REQUESTED | cancel | S | close wait | revoke/cancel children | - |
| F25 | BLOCKED | CANCEL_REQUESTED | cancel | S | close wait | revoke/cancel children | - |
| F26 | QUARANTINED | CANCEL_REQUESTED | cancel | S | close wait | revoke/cancel children | - |
| F27 | CANCEL_REQUESTED | QUIESCING | epoch advanced | S | none | settle children/effects | - |
| F28 | QUIESCING | CLEANING | direct termination receipt or quiescence-closed | S | none | schedule cleanup | - |
| F29 | CLEANING | CANCELLED | clean+cancel | S | none | receipts | cancelled |

## 9. NodeRun aggregate v1

Initial: `PENDING`. Terminals: `SUCCEEDED`, `FAILED`, `CANCELLED`, `SKIPPED`. `FAILURE_PENDING_CLEANUP` is nonterminal; `FAILED` is final and immutable.

| ID | Source | Target | Guard / trigger | Canonical | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| N01 | PENDING | WAITING_DEPENDENCY | dependency unmet | S | W(dependency) | none | - |
| N02 | PENDING | WAITING_HUMAN | human predicate true | S | W(human) | none | - |
| N03 | PENDING | ADMISSIBLE | guards pass | S | none | none | - |
| N04 | WAITING_DEPENDENCY | ADMISSIBLE | dependency receipt+fresh | S | resume | none | - |
| N05 | WAITING_DEPENDENCY | BLOCKED | expiry/withdraw/cycle | S | wait closed | none | - |
| N06 | WAITING_HUMAN | ADMISSIBLE | exact decision+fresh | S | resume | none | - |
| N07 | WAITING_HUMAN | BLOCKED | expiry/deny/withdraw | S | wait closed | none | - |
| N08 | ADMISSIBLE | RUNNING | attempt+lease committed | S | none | none | - |
| N09 | RUNNING | RETRY_WAIT | retryable attempt failure+budget | S | W(retry) | settle attempt | - |
| N10 | RETRY_WAIT | ADMISSIBLE | wake+changed/fresh input | S | retry | none | - |
| N11 | RETRY_WAIT | FAILURE_PENDING_CLEANUP | exhausted | S | exhausted | cleanup required | not yet |
| N12 | RUNNING | SUCCEEDED | outputs verified+no cleanup | S | none | settled | success |
| N13 | RUNNING | CLEANUP_PENDING | outputs/failure require cleanup | S | none | cleanup | - |
| N14 | CLEANUP_PENDING | SUCCEEDED | clean+success | S | none | receipts | success |
| N15 | CLEANUP_PENDING | FAILED | clean+failed | S | none | receipts | failed |
| N16 | PENDING | SKIPPED | graph-declared skip guard | S | none | none | skipped |
| N17 | RUNNING | QUARANTINED | stale/unknown result | S | human disposition | isolate | - |
| N18 | QUARANTINED | CLEANUP_PENDING | typed disposition | S | receipt | cleanup | - |
| N19 | BLOCKED | PENDING | changed input/replan | S | resume | none | - |
| N20 | BLOCKED | ADMISSIBLE | same-digest resolution | S | resume | none | - |
| N21 | PENDING | CANCEL_REQUESTED | cancel | S | close wait | revoke attempt | - |
| N22 | WAITING_DEPENDENCY | CANCEL_REQUESTED | cancel | S | close wait | revoke attempt | - |
| N23 | WAITING_HUMAN | CANCEL_REQUESTED | cancel | S | close wait | revoke attempt | - |
| N24 | ADMISSIBLE | CANCEL_REQUESTED | cancel | S | close wait | revoke attempt | - |
| N25 | RUNNING | CANCEL_REQUESTED | cancel | S | close wait | revoke attempt | - |
| N26 | RETRY_WAIT | CANCEL_REQUESTED | cancel | S | close wait | revoke attempt | - |
| N27 | BLOCKED | CANCEL_REQUESTED | cancel | S | close wait | revoke attempt | - |
| N28 | QUARANTINED | CANCEL_REQUESTED | cancel | S | close wait | revoke attempt | - |
| N29 | CANCEL_REQUESTED | QUIESCING | epoch advanced | S | none | settle attempt/effects | - |
| N30 | QUIESCING | CLEANUP_PENDING | direct termination receipt or quiescence-closed | S | none | schedule cleanup | - |
| N31 | CLEANUP_PENDING | CANCELLED | clean+cancel | S | none | receipts | cancelled |
| N32 | FAILURE_PENDING_CLEANUP | CLEANUP_PENDING | failure sealed; cleanup required | S | none | cleanup | - |

## 10. Attempt aggregate v1

Initial: `CREATED`. Terminals: `SUCCEEDED`, `FAILED`, `EXHAUSTED`, `CANCELLED`. `RETRY_DISPOSITION` is nonterminal; `FAILED` is final and immutable.

| ID | Source | Target | Guard / trigger | Canonical | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| A01 | CREATED | LEASED | atomic admission+no other unfinished Attempt for node across all fences; ordinary reclaim predecessor must have committed A11 | S | none | atomically create lease/fence/epoch/context/outbox only after predecessor guard | - |
| A02 | LEASED | STARTING | context verified | S | none | none | - |
| A03 | STARTING | RUNNING | worker attested | S | none | none | - |
| A04 | STARTING | RETRY_DISPOSITION | start failure requiring retry/final disposition | S | exhausted or protected disposition | settle/cleanup | not terminal |
| A05 | RUNNING | SUCCEEDED | sealed valid result | S | none | settle | success |
| A06 | RUNNING | RETRY_DISPOSITION | failure requiring retry/final disposition | S | none | settle | not terminal |
| A07 | RUNNING | HEARTBEAT_LOST | db_now>=renew_by | S | none | revoke/fence | - |
| A08 | HEARTBEAT_LOST | STOP_REQUESTED | same reclaim transaction | S | none | stop intent | - |
| A09 | STOP_REQUESTED | QUIESCING | stop delivered | S | none | classify effects/resources | - |
| A10 | QUIESCING | STOPPED | verified termination receipt+every bound effect has settled disposition | S | none | cleanup remains pending until separate receipts | not finished; successor admission forbidden |
| A11 | STOPPED | CANCELLED | all effects settled+every required cleanup item complete from previously committed receipts+no live authority/resource ownership | S | none | consumes receipts; creates no successor | cancelled/finished; ordinary successor admission may occur only in a later transaction |
| A12 | QUIESCING | QUARANTINED | termination unproved | S | §14 | isolate | not finished |
| A13 | RUNNING | STALE | fence/epoch/input mismatch | S | none | quarantine output/revoke | not finished |
| A14 | STALE | STOP_REQUESTED | stop required | S | none | stop intent | - |
| A15 | STALE | QUARANTINED | already physically stopped but effects unresolved | S | human disposition | isolate | not finished |
| A16 | RETRY_DISPOSITION | EXHAUSTED | node retry budget spent+effects and cleanup settled | S | exhausted | cleanup | exhausted |
| A17 | RETRY_DISPOSITION | CANCELLED | cancellation requested+no retry authorized+cleanup complete | S | none | receipts | cancelled |
| A18 | QUARANTINED | CANCELLED | effect disposition+bound saga reached CLOSED via U09+closure receipt verifies+shared-resource ownership false+effects settled+clean | S | receipt | prior receipts | cancelled |
| A19 | CREATED | STOP_REQUESTED | cancel/reclaim | S | none | revoke+stop | - |
| A20 | LEASED | STOP_REQUESTED | cancel/reclaim | S | none | revoke+stop | - |
| A21 | STARTING | STOP_REQUESTED | cancel/reclaim | S | none | revoke+stop | - |
| A22 | RUNNING | STOP_REQUESTED | cancel/reclaim | S | none | revoke+stop | - |
| A23 | HEARTBEAT_LOST | STOP_REQUESTED | cancel/reclaim | S | none | revoke+stop | - |
| A24 | RETRY_DISPOSITION | FAILED | signed nonretryable final disposition+all effects and cleanup settled+no cancellation | S | none | receipts | failed/immutable |

An attempt is **unfinished** unless its state is exactly `SUCCEEDED`, `FAILED`, `EXHAUSTED`, or `CANCELLED` **and** its required effect and cleanup sets are settled. `STOPPED`, `STALE`, and `QUARANTINED` remain unfinished. This predicate is used across all fences and by §14. The invariant “at most one unfinished Attempt per node across all fences” is unconditional. A01 and the admission transaction reject if any other unfinished Attempt exists; isolation, retained cleanup, a different fence, or an idempotency key creates no exception. Ordinary reclaim must commit A10, predecessor cleanup receipts, and A11 in that order before the later A01 transaction may materialize the successor Attempt or any Lease/fence/context/outbox.

## 11. Wait aggregate v1

Initial: `OPEN`. Terminals: `CONSUMED`, `CLOSED_SAFE_DEFAULT`, `CLOSED_BLOCKED`, `CANCELLED`.

| ID | Source | Target | Guard / trigger | Canonical | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| W01 | OPEN | ANSWERED | valid typed answer before deadline | S | answer receipt | none | - |
| W02 | OPEN | EXPIRED | db_now>=expires_at | S | expiry | none | - |
| W03 | OPEN | WITHDRAWN | authorized owner withdrawal | S | withdraw | none | - |
| W04 | OPEN | CANCELLED | parent cancellation epoch changed | S | cancel | none | cancelled |
| W05 | ANSWERED | STALE | bound digest changed before resume | S | stale | none | - |
| W06 | ANSWERED | CONSUMED | resume CAS succeeds | S | resume | none | consumed |
| W07 | STALE | OPEN | new revision creates new deadline | S | new wait revision | notify | - |
| W08 | EXPIRED | ESCALATED | policy names human recovery | S | bounded escalation | notify | - |
| W09 | EXPIRED | CLOSED_SAFE_DEFAULT | pre-authorized reversible default | S | no authority granted | audit | closed |
| W10 | EXPIRED | CLOSED_BLOCKED | no safe default | S | parent stays blocked | audit | closed |
| W11 | WITHDRAWN | CLOSED_BLOCKED | withdrawal disposition | S | parent stays blocked | audit | closed |
| W12 | ESCALATED | ANSWERED | valid escalated answer | S | answer | none | - |
| W13 | ESCALATED | CLOSED_BLOCKED | escalation expires/denied | S | parent stays blocked | audit | closed |
| W14 | ANSWERED | CANCELLED | parent cancellation epoch changed before consume | S | answer not consumed | audit | cancelled |
| W15 | STALE | CANCELLED | parent cancellation epoch changed | S | stale revision closed | audit | cancelled |
| W16 | EXPIRED | CANCELLED | parent cancellation epoch changed before expiry disposition | S | no escalation/default | audit | cancelled |
| W17 | WITHDRAWN | CANCELLED | parent cancellation epoch changed before withdrawal disposition | S | no resume | audit | cancelled |
| W18 | ESCALATED | CANCELLED | parent cancellation epoch changed before escalated answer/disposition | S | escalation closed | audit | cancelled |

For every Wait event, the compare-and-append key is `(wait_id, wait_revision, expected_event_version, parent_cancellation_epoch)`. If cancel and answer/expiry/withdraw/escalation race on the same expected version, database serialization chooses one commit; a committed cancellation-epoch advance causes any later competing event to fail CAS, and if the competing event committed first cancellation retries from the new nonterminal state through W14–W18. Thus every reachable nonterminal state has exactly one cancellation edge. `CONSUMED`, `CLOSED_SAFE_DEFAULT`, `CLOSED_BLOCKED`, and `CANCELLED` are immutable closed terminals; they need no cancellation edge and are already terminal-eligible for the parent predicate.

## 12. Effect and reconciliation aggregate v1

Initial: `INTENT_RECORDED`. Terminals: `RECEIPT_VERIFIED`, `FAILED_FINAL`, `CANCELLED_BEFORE_SEND`, `ACCEPTED_RISK`, `COMPENSATED`, `COMPENSATION_FAILED`.

| ID | Source | Target | Guard / trigger | Canonical | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| E01 | INTENT_RECORDED | READY_TO_SEND | authority+precondition current | S | none | none | - |
| E02 | INTENT_RECORDED | CANCELLED_BEFORE_SEND | cancel epoch changed | S | none | no send receipt | no-send |
| E03 | READY_TO_SEND | CANCELLED_BEFORE_SEND | cancel epoch changed | S | none | no send receipt | no-send |
| E04 | READY_TO_SEND | SENDING | fresh authority immediately before send | S | none | dispatch | - |
| E05 | SENDING | APPLIED | response proves postcondition | S | none | receipt | - |
| E06 | APPLIED | RECEIPT_VERIFIED | receipt+remote identity verify | S | none | seal receipt | verified |
| E07 | SENDING | FAILED_RETRYABLE | typed retryable transport failure | S | budget | none | - |
| E08 | FAILED_RETRYABLE | READY_TO_SEND | budget+fresh authority | S | retry | new effect-attempt ID | - |
| E09 | FAILED_RETRYABLE | FAILED_FINAL | exhausted+target-effect signed `NoApplicationReceipt` from the failed attempt | S | exhausted | conclusive no-application receipt | failed |
| E10 | SENDING | FAILED_FINAL | nonretryable proven failure+target-effect signed `NoApplicationReceipt` | S | none | conclusive no-application receipt; otherwise E11 UNKNOWN | failed |
| E11 | SENDING | UNKNOWN | lost/ambiguous response | S | no retry | none | - |
| E12 | UNKNOWN | RECONCILING | create immutable origin=ORIGINAL, target_effect_id=original_effect_id | S | lookup | read-only lookup | - |
| E13 | RECONCILING | ABSENCE_PROVED | origin=ORIGINAL+target=original effect+zero matches+signed proof | S | none | lookup receipt | - |
| E14 | ABSENCE_PROVED | RETRY_AUTHORIZED | fresh authority+safe retry policy | S | none | authorization receipt | - |
| E15 | RETRY_AUTHORIZED | READY_TO_SEND | new attempt identity | S | budget | none | - |
| E16 | RECONCILING | APPLICATION_RECONCILED | origin=ORIGINAL+target=original effect+one exact match | S | none | observation | - |
| E17 | APPLICATION_RECONCILED | RECEIPT_VERIFIED | reconstructed receipt verifies | S | none | seal | verified |
| E18 | RECONCILING | UNRESOLVED | origin=ORIGINAL+multiple/uncertain | S | none | lookup receipt | - |
| E19 | UNRESOLVED | QUARANTINED | isolation recorded | S | human disposition | isolate | - |
| E20 | QUARANTINED | ACCEPTED_RISK | ACCEPT_APPLICATION receipt §12 | S | none | retain risk | accepted-risk |
| E21 | QUARANTINED | FAILED_FINAL | DECLARE_FAILED receipt §12 or bounded disposition deadline expiry with signed fail-closed system disposition | S | none | seal failure | failed |
| E22 | QUARANTINED | COMPENSATION_PENDING | original-effect reconciliation only; AUTHORIZE_COMPENSATION+fresh authority | S | none | intent | - |
| E23 | COMPENSATION_PENDING | COMPENSATING | authority rechecked before send | S | none | dispatch | - |
| E24 | COMPENSATING | COMPENSATED | verified compensation receipt | S | none | seal | compensated |
| E25 | COMPENSATING | COMPENSATION_FAILED | proven final failure | S | none | receipt | failed |
| E26 | COMPENSATING | COMPENSATION_UNKNOWN | ambiguous response | S | no retry | none | - |
| E27 | COMPENSATION_UNKNOWN | RECONCILING | create immutable origin=COMPENSATION, target_effect_id=compensation_effect_id, bind original_effect_id | S | lookup | read-only lookup | - |
| E28 | RECONCILING | COMPENSATED | origin=COMPENSATION+target=compensation effect+one exact match+verified receipt | S | none | seal compensation | compensated |
| E29 | RECONCILING | COMPENSATION_FAILED | origin=COMPENSATION+target=compensation effect+absence/nonapplication proved final | S | none | lookup receipt; never original retry | failed |
| E30 | INTENT_RECORDED | FAILED_FINAL | cancel false+authority/precondition conclusively invalid before bounded intent deadline+target-effect signed no-send `NoApplicationReceipt` | S | deadline/exhausted | signed no-send failure receipt | failed |
| E31 | READY_TO_SEND | FAILED_FINAL | cancel false+fresh send authority/precondition denied/stale/unavailable at bounded send deadline+target-effect signed no-send `NoApplicationReceipt` | S | deadline/exhausted | signed no-send failure receipt | failed |
| E32 | APPLIED | RECONCILING | receipt missing/invalid/unverifiable or remote identity mismatch/unavailable at bounded verification deadline; origin=ORIGINAL+target=original effect | S | bounded lookup | preserve response; read-only reconciliation | - |
| E33 | FAILED_RETRYABLE | FAILED_FINAL | fresh authority/safe-retry forbidden/stale/revoked/unavailable at bounded retry deadline+target-effect signed `NoApplicationReceipt` for every attempt | S | no retry | signed retry-forbidden and no-application receipt | failed |
| E34 | ABSENCE_PROVED | FAILED_FINAL | fresh authority+safe retry is false because retry is forbidden, stale, revoked, cancelled, or exhausted | S | no retry | signed `NoApplicationReceipt` plus no-retry disposition | failed |
| E35 | RETRY_AUTHORIZED | FAILED_FINAL | new attempt identity or budget/fresh authority fails before dispatch+target-effect signed no-send `NoApplicationReceipt` | S | no retry | signed no-send failure receipt | failed |
| E36 | APPLICATION_RECONCILED | UNRESOLVED | reconstructed receipt missing/invalid/unverifiable or remote identity mismatch at bounded verification deadline; origin=ORIGINAL preserved | S | bounded disposition | typed verification-failure evidence | - |
| E37 | RECONCILING | COMPENSATION_FAILED | origin=COMPENSATION+target=compensation effect+multiple/uncertain/invalid observation at reconciliation deadline | S | deadline/exhausted | signed unresolved-compensation failure receipt; never original retry | failed |
| E38 | UNRESOLVED | QUARANTINED | isolation deadline expires without earlier isolation acknowledgement | S | wait expires | fail-closed isolation record | - |
| E39 | COMPENSATION_PENDING | COMPENSATION_FAILED | fresh compensation authority/precondition denied, stale, revoked, or unavailable at bounded dispatch deadline | S | deadline/exhausted | signed no-send compensation failure receipt | failed |
| E40 | FAILED_RETRYABLE | UNKNOWN | retry exhausted but target-effect no-application proof is missing/invalid/stale | S | no blind retry | create ORIGINAL reconciliation plan next | - |
| E41 | INTENT_RECORDED | UNKNOWN | conclusive-invalidity/deadline predicate reached but target-effect no-send proof is missing/invalid/stale | S | no send | create ORIGINAL reconciliation plan next | - |
| E42 | READY_TO_SEND | UNKNOWN | denial/staleness/deadline predicate reached but target-effect no-send proof is missing/invalid/stale | S | no send | create ORIGINAL reconciliation plan next | - |
| E43 | FAILED_RETRYABLE | UNKNOWN | retry forbidden/stale/unavailable but target-effect no-application proof for every attempt is missing/invalid/stale | S | no blind retry | create ORIGINAL reconciliation plan next | - |
| E44 | RETRY_AUTHORIZED | UNKNOWN | pre-dispatch failure reached but target-effect no-send proof is missing/invalid/stale | S | no send | create ORIGINAL reconciliation plan next | - |

For direct terminal edges E09, E10, E30, E31, E33, and E35, the signed no-send/`NoApplicationReceipt` is target-effect-specific and proves no application for every represented attempt. Without that proof, the Effect enters `UNKNOWN`/reconciliation instead of taking the direct terminal edge. A current `ExposureReceipt` for the same target Effect contradicts the terminal-edge receipt and rejects the transaction.

For each nonterminal Effect source, the table is a mutually exclusive and exhaustive trigger/guard partition. `INTENT_RECORDED`: cancel (E02), valid/current (E01), conclusive invalidity/deadline with no-send proof (E30), or the same failure predicate without valid proof (E41 to UNKNOWN). `READY_TO_SEND`: cancel (E03), fresh send (E04), denial/staleness/deadline with proof (E31), or missing/invalid proof (E42 to UNKNOWN). `SENDING`: proved applied (E05), typed retryable failure (E07), proved final no-application failure (E10), or ambiguity/missing proof at the response deadline (E11). `APPLIED`: valid receipt/identity (E06) or verification failure/deadline (E32). `FAILED_RETRYABLE`: authorized fresh retry (E08), exhausted/forbidden final failure with complete no-application proof (E09/E33), or the matching predicate without complete proof (E40/E43 to UNKNOWN). `UNKNOWN` deterministically creates the ORIGINAL plan (E12). `RECONCILING` partitions first by immutable origin, then by zero, one, or multiple/uncertain matches and verification outcome (E13/E16/E18 or E28/E29/E37). `ABSENCE_PROVED`: safe fresh retry (E14) or its exact complement (E34). `RETRY_AUTHORIZED`: valid new attempt (E15), proved no-send pre-dispatch failure (E35), or missing/invalid no-send proof (E44 to UNKNOWN). `APPLICATION_RECONCILED`: verified reconstructed receipt (E17) or its complement (E36). `UNRESOLVED`: acknowledged isolation (E19) or isolation-deadline expiry (E38). `QUARANTINED`: exactly one disposition outcome (human E20/E21/E22, or bounded-deadline fail-closed E21), with expiry selecting E21 rather than stuttering. `COMPENSATION_PENDING`: fresh dispatch (E23) or its complement at deadline (E39). `COMPENSATING`: verified application (E24), proved final failure (E25), or ambiguity (E26). `COMPENSATION_UNKNOWN` creates only a COMPENSATION-origin plan (E27). No temporary wait is unbounded; its named deadline commits the listed expiry edge. Original and compensation origins remain disjoint.

Every `ReconciliationPlan` and transition from it immutably preserves `{reconciliation_origin, target_effect_id, original_effect_id}`. The origin is exactly `ORIGINAL` or `COMPENSATION`. E13/E14/E15/E16/E17/E18 are enabled only for `ORIGINAL`; E28/E29 are enabled only for `COMPENSATION`. A compensation-origin zero-match result takes E29 and can never take E13, E14, E15, or authorize original replay. Origin/target mismatch rejects the transaction and quarantines the controller event without changing the effect.

## 12.1 UNKNOWN disposition receipts and work eligibility

Every disposition receipt contains `{receipt_id, effect_id, effect_intent_digest, lookup_evidence_digest, tenant_id, ScopeRef, principal, AuthoritySnapshot_digest, action, rationale, accepted_risk_scope, issued_at, expires_at, revocation_ref, remediation_owner, review_due_at}`.

- `ACCEPT_APPLICATION` takes `QUARANTINED -> ACCEPTED_RISK`. It explicitly says application is **not verified** and never creates `RECEIPT_VERIFIED`. Work may reach `DONE` only if the risk policy for that exact effect permits accepted-risk completion, the receipt is current, no safety/financial/data-integrity oracle depends on verification, retained risk is displayed, and all other terminal predicates pass. Otherwise the work outcome is `FAILED` after cleanup.
- `DECLARE_FAILED` takes `QUARANTINED -> FAILED_FINAL`; its receipt selects failed work disposition and cannot imply absence or compensation.
- `AUTHORIZE_COMPENSATION` takes `QUARANTINED -> COMPENSATION_PENDING` only after a new context/grant and current fence, policy, identity/control snapshot, rollback target and effect preconditions are verified. It cannot reuse the old authority.

## 13. CleanupItem aggregate v1

Initial: `PENDING`. Terminals: `CLEANED`, `ESCALATED_DISPOSITION`.

| ID | Source | Target | Guard / trigger | Canonical | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| C01 | PENDING | RUNNING | cleanup-only grant+item due | S | none | no business writes | - |
| C02 | RUNNING | CLEANED | verified deletion/release/retention receipt | S | none | receipt | cleaned |
| C03 | RUNNING | RETRY_WAIT | retryable failure+budget | S | W(retry) | revoke old grant | - |
| C04 | RETRY_WAIT | RUNNING | wake+fresh cleanup authority | S | retry | new attempt | - |
| C05 | RUNNING | CLEANUP_FAILED | nonretryable failure | S | none | revoke | - |
| C06 | RETRY_WAIT | CLEANUP_FAILED | exhausted | S | exhausted | revoke | - |
| C07 | CLEANUP_FAILED | ESCALATION_PENDING | escalation requested | S | W(human) | none | - |
| C08 | ESCALATION_PENDING | RETRY_WAIT | authorized remediation | S | retry budget revision | none | - |
| C09 | ESCALATION_PENDING | ESCALATED_DISPOSITION | authorized retained-risk disposition | S | review deadline | retain risk | disposed |
| C10 | ESCALATION_PENDING | CLEANUP_FAILED | deny/expiry/withdraw | S | parent remains CLEANING | none | - |
| C11 | ESCALATED_DISPOSITION | ESCALATED_DISPOSITION | typed resurface, review-due, reminder, or revocation signal routed by deterministic event ID and latest generation | S; exact RO row executes in the same transaction | no parent/item retry | non-revoking signals use RO01/RO02/RO03-RO06; revocations use RO01-R/RO02-R or atomically RO11-RO13 | historical disposed item remains terminal |
| C12 | PENDING | CLEANED | legal hold/retention receipt satisfies item | S | none | receipt; no deletion | cleaned |

A `CleanupEscalationDisposition` contains item/manifest digests, exact `tenant_id`/`ScopeRef`, failed attempts, retained resource/data/risk, blast radius, compensating isolation, authorized cleanup-risk role and quorum, PrincipalIdentity/ControlRelationship snapshot digest, issue/expiry/revocation, monitor, resurface triggers, remediation owner/deadline, review cadence, and closure receipt. It is terminal-equivalent only for `FAILED` or `CANCELLED` work when policy explicitly lists that cleanup class as retainable. It is never terminal-equivalent for `DONE`, secrets/credentials, live lease/grant, shared mutable workspace, public exposure, or an unclassified item. Any trigger, review due, or revocation uses C11 below and never reopens the item or parent. `DONE` requires every item `CLEANED`.

A `RemediationObligation` is a separate durable aggregate, not Work cleanup state. It has a monotonically increasing `generation`. Its exact IDs are `obligation_id = H("remediation-obligation-v2", tenant_id, ScopeRef, parent_work_id, cleanup_item_id, disposition_digest, generation)`, `link_id = H("remediation-link-v2", obligation_id)`, and `child_id = H("remediation-child-v2", obligation_id)`. For B37/M28/IRB06 rollback safety, `cleanup_item_id` is the protected purpose-bound subject `H("rollback-safety-subject-v1", rollback_saga_id, restoration_target_digest)` and `disposition_digest` is the exhausted rollback-failure receipt digest; this does not create a CleanupItem, invoke C11, or permit cleanup. The closed creation-trigger partition is `cleanup-resurface:C11 -> RO01|RO02` and `rollback-safety:B37 -> RO00-B, M28 -> RO00-M, IRB06 -> RO00-I`; no other trigger may create an `OPEN` obligation. C11 first classifies `trigger_kind` as non-revoking (`resurface|review_due|reminder`) or `revocation`. Non-revoking signals create `OPEN` through RO01/RO02 or append through RO03-RO06 without changing status. A revocation with no generation, or after `CLOSED`, creates the exact generation directly as `REVOKED` through RO01-R/RO02-R with no grant, admission, or active child authority. A revocation of `OPEN|IN_PROGRESS|VERIFYING` uses RO11/RO12/RO13 in the same C11 transaction: append event and receipt, change status, fence grants, quiesce the child, and settle or reconcile every effect before any more work. The historical parent Work and CleanupItem never change. A `RemediationResurfaceReceipt` has deterministic `event_id = H("remediation-signal-v1", obligation_id, trigger_kind, source_event_id, observed_at)` and binds all three IDs, disposition digest, authority snapshot, and canonical payload. Event-ID lookup precedes current-status routing: same-event replay after any state change returns the original byte-identical receipt and performs no new transition; conflicting bytes reject. A later distinct signal in `REVOKED` uses RO06. A distinct event appends once by event-ID CAS. First materialization is one atomic absent-or-same CAS over the obligation, link, child, event, and receipt; non-revoking creation uses `OPEN` plus child-at-`INBOX`, while revocation creation uses `REVOKED` plus a fenced/non-admitted child record.

### 13.1 RemediationObligation aggregate v1

Initial: `OPEN`. States: `OPEN`, `IN_PROGRESS`, `VERIFYING`, `REVOKED`, `CLOSED`. The only terminal is `CLOSED`. Every mutation uses expected aggregate version, expected latest generation, exact tenant/scope/disposition/parent/item/child/link digests, a unique idempotency/event key, and compare-and-append. Only the named protected remediation owner may act, except that the cleanup-risk authority may revoke and the protected verifier may verify. No row changes parent Work or CleanupItem.

| ID | Source | Target | Guard / trigger | Authority, CAS, replay | Child/effect/cleanup binding | Result |
|---|---|---|---|---|---|---|
| RO00-B | absent | OPEN | synchronized B37 exhausted rollback-safety trigger; generation is deterministically 1 when none exists or exact prior+1 only after prior CLOSED | protected rollback gateway; one expected Work/obligation-generation CAS; exact same command/bytes returns the original receipt, conflict/out-of-order rejects | atomically change Work by B37 and create obligation, exact link, MAINTENANCE child at INBOX, deterministic event and creation receipt; no CleanupItem and no C11 | exact exposure/resource keys blocked |
| RO00-M | absent | OPEN | synchronized M28 exhausted rollback-safety trigger; same deterministic generation rule as RO00-B | protected rollback gateway; same atomic CAS/replay/conflict rule | atomically change Work by M28 and create obligation/link/MAINTENANCE child/event/receipt; no CleanupItem and no C11 | exact exposure/resource keys blocked |
| RO00-I | absent | OPEN | synchronized IRB06 exhausted improvement rollback-safety trigger; same deterministic generation rule as RO00-B | protected rollback gateway; same atomic tuple/obligation CAS/replay/conflict rule | atomically change rollback tuple by IRB06 and create obligation/link/MAINTENANCE child/event/receipt; no CleanupItem and no C11 | exact exposure/resource keys blocked |
| RO01 | absent | OPEN | C11 signal and no prior generation; deterministic generation 1 records absent-or-same | cleanup-risk gateway; atomic create CAS; exact replay stutters, conflict rejects | create exact link, MAINTENANCE child at INBOX, event and receipt atomically | resource keys blocked |
| RO02 | absent | OPEN | C11 signal and latest prior generation is CLOSED with verified closure receipt; generation is prior+1 | cleanup-risk gateway; atomic create CAS; exact replay stutters, conflict/out-of-order generation rejects | create new exact link/child/event; prior generation remains immutable | new generation blocked |
| RO01-R | absent | REVOKED | C11 revocation and no prior generation; deterministic generation 1 | cleanup-risk gateway; atomic absent-or-same CAS; event replay returns original receipt | create exact link and fenced/non-admitted child record; append revocation; no grant/effect authority | blocked |
| RO02-R | absent | REVOKED | C11 revocation and latest prior generation is CLOSED; exact prior+1 generation | cleanup-risk gateway; atomic absent-or-same CAS; event replay returns original receipt | create exact link and fenced/non-admitted child record; append revocation; prior generation immutable | blocked |
| RO03 | OPEN | OPEN | distinct later resurface/review-due signal | cleanup-risk gateway; event-ID append CAS; same event stutters | append event only; never reset child | blocked |
| RO04 | IN_PROGRESS | IN_PROGRESS | distinct later resurface/review-due signal | same as RO03 | append event only | blocked |
| RO05 | VERIFYING | VERIFYING | distinct later resurface/review-due signal | same as RO03 | append event; verifier must re-evaluate freshness | blocked |
| RO06 | REVOKED | REVOKED | distinct later signal, including bounded reminder/escalation | same as RO03; bounded cadence and escalation receipt required | append event; no child reset | blocked |
| RO07 | OPEN | IN_PROGRESS | fresh purpose-bound remediation authorization; child admission/start receipt matches IDs | protected remediation owner; version CAS; identical command replays | child may advance; effects use obligation generation as origin | blocked |
| RO08 | IN_PROGRESS | VERIFYING | child terminal-clean; every child effect settled; every CleanupItem terminal-clean; claimed resource release/removal receipts already committed | protected remediation owner; version CAS | bind immutable child outcome/effect/cleanup/resource receipt set | blocked pending closure oracle |
| RO09 | VERIFYING | CLOSED | protected purpose-specific closure oracle passes; signed RemediationClosureReceipt binds purpose, generation, all IDs/digests and receipt set; no child authority/resource ownership remains | independent protected verifier; version CAS; receipt absent-or-same | consumes prior receipts and closes the remediation child; creates no work or cleanup transition | terminal; `cleanup-resurface` may atomically remove only its exact keys when closure proves their remediation; `rollback-safety` retains every exposure/resource block for B74/B34/B38, M62/M25/M29, or IRB09/IRB03/IRB07-N/R/Q; only the final named settlement row removes its exact purpose/generation/key-set |
| RO10 | VERIFYING | IN_PROGRESS | verification failed or stale but bounded retry is authorized and fresh | remediation owner plus protected retry authority; new attempt ID; version CAS | preserve history; retry child remediation without resetting aggregate generation | blocked |
| RO11 | OPEN | REVOKED | C11 revocation, or authorization expiry/withdrawal/deadline | cleanup-risk authority; one version CAS atomically appends signed event/receipt and changes status; replay returns original receipt | revoke/fence every grant; quiesce child; settle/reconcile every effect before commit | blocked |
| RO12 | IN_PROGRESS | REVOKED | C11 revocation, stale/expired/withdrawn authority, or retry exhausted | cleanup-risk authority; one version CAS atomically appends signed event/receipt and changes status; replay returns original receipt | revoke/fence; child quiescence receipt and terminal Effect dispositions commit atomically; no hidden activity behind BLOCKED | blocked |
| RO13 | VERIFYING | REVOKED | C11 revocation, closure denial, invalid/stale receipt, expiry, or final verification failure | protected verifier or cleanup-risk authority; one version CAS atomically appends signed event/receipt and changes status; replay returns original receipt | fence verifier/remediation grants; retain invalid receipt; quiesce child and settle/reconcile effects before commit | blocked |
| RO14 | REVOKED | IN_PROGRESS | new independent purpose-bound authorization, child quiescent, old effects settled, fresh attempt budget; no work/admission/effect before this row commits | protected remediation owner plus cleanup-risk authority; version CAS and new attempt ID | re-authorize same generation/child; no historical reset | blocked |

`RO00-B`, `RO00-M`, `RO00-I`, `RO01`, `RO02`, `RO01-R`, and `RO02-R` are creation transactions, not outgoing edges from an existing aggregate. RO00-B/M/I are the only synchronized exception to “no row changes parent Work”: each performs its named B37/M28/IRB06 parent edge and the complete absent-to-OPEN creation in one transaction. `CLOSED` has zero outgoing rows and is immutable. A future non-revoking signal after closure creates a new exact `OPEN` generation through RO02; a future revocation creates the new generation directly as `REVOKED` through RO02-R. Stale, denied, expired, exhausted, or revoked work stays visibly `REVOKED`; RO06 supplies bounded resurface/escalation and RO14 is its only recovery. Only RO09 is terminal. For a `cleanup-resurface` obligation, admission may remove only its exact bound resource-key block in RO09 and only when `status=CLOSED` and the closure receipt proves remediation of that key. For a `rollback-safety` obligation, RO09 closes the child but releases nothing: BUILD keeps B74, B34, B38 and MAINTENANCE keeps M62, M25, M29 ordered, while IMPROVEMENT keeps IRB09, IRB03, and the selected IRB07-N/R/Q ordered. Only B38, M29, or that selected IRB07 settlement atomically removes the exact purpose/generation/key-set blocks after genuine restoration and independent verification seal or adopt `ROLLED_BACK`, and each emits a bound BlockReleaseReceipt. No human waiver, CleanupEscalationDisposition, child terminal, or accepted risk alone unblocks either purpose. Generated validation starts at `RO00-B|RO00-M|RO00-I|RO01|RO02`-created `OPEN`, proves all five states reachable, requires an outgoing bounded disposition/recovery row for each nonterminal state, treats `CLOSED` as the sole sink, rejects every unlisted pair, and tests same-command replay, same-event replay, distinct-event append, conflict rejection, revoke/re-authorize, stale/expiry/retry exhaustion, and post-close new-generation races.

## 14. UnconfirmedQuiescence saga v1

Initial: `REQUESTED`. Terminals: `DENIED`, `CLOSED`.

| ID | Source | Target | Guard / trigger | Canonical | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| U01 | REQUESTED | REVIEW | termination proof unavailable; every resource key frozen | S | W(human) | revoke old authority | - |
| U02 | REVIEW | DENIED | deny/expiry/withdraw/conflict | S | wait closed | node remains blocked | denied |
| U03 | REVIEW | ISOLATING | authorized exact-digest disposition | S | bounded monitoring deadline | monitoring/isolation/kill/reconciliation only | - |
| U04 | ISOLATING | ISOLATING | fresh isolation/monitoring receipt or bounded kill/reconciliation step | S | monitor until expiry | no successor work authority | - |
| U05 | ISOLATING | REVOKED | revoke/expiry/monitor alarm | S | none | keep old authority revoked; node blocked | - |
| U06 | ISOLATING | CLOSING | exact old-attempt termination+effect classification observed | S | none | closure/cleanup only | - |
| U07 | REVOKED | CLOSING | exact old-attempt termination+effect classification observed | S | none | closure/cleanup only | - |
| U08 | CLOSING | REVIEW | closure evidence stale/incomplete | S | W(human) | remain isolated and blocked | - |
| U09 | CLOSING | CLOSED | closure receipt+clean | S | none | receipts | closed |
| U10 | REVIEW | REVIEW | replacement exact-digest disposition requested before deadline | S | bounded review | no work authority | - |

`UnconfirmedQuiescenceDisposition` binds the authorized human actor/quorum, exact old `AuthoritySnapshot`, attempt/lease/fence/context and revocation receipts, typed resource inventory, isolation and no-reusable-secret attestation, purpose, monitor/kill/reconciliation steps, `issued_at`, `expires_at`, revocation reference, cleanup manifest and closure owner. It authorizes only monitoring, isolation, kill, reconciliation, and closure of the old Attempt. It cannot create or authorize a successor Attempt, Lease, fence, execution context, output, business command, business effect, workspace, credential, or any alternate authority carrier. Every resource class remains blocked for successor work. The old Attempt remains unfinished and node admission remains closed until exact termination, U09, and Attempt A18 complete. A disposition never makes cancellation terminal.

## 15. Improvement product and reducer v1

The authoritative improvement projection is `ImprovementTupleV1 {candidate_state, rollout_state, release_attempt_state, control_health_state, work_cancel_state, effect_set_state, cleanup_set_state, rollback_state, canonical_state, tuple_version, component_versions, digests}`. It is reduced after each component event in the same transaction. The reducer verifies the previous tuple and exact synchronized row, applies only its named coordinate changes, and derives exactly one canonical result. Unknown symbols, no matching row, multiple matching rows, or disagreement with persisted `canonical_state` rejects the transaction.

Closed aggregate vocabularies and deterministic aggregation are:

- `rollout_state={DISABLED,ENABLEMENT_REVIEW,CANARY_PENDING_APPROVAL,CANARY_READY,CANARY_RUNNING,WIDENING_REVIEW,WIDENING_EFFECT,WIDENING_RECONCILING,CANARY_PAUSED,CANARY_PASSED,CANARY_FAILED,CANARY_ABORTING,CANARY_ABORTED,CANARY_ABORT_SETTLED,PROMOTION_PENDING_APPROVAL,APPROVED,PROMOTING,PROMOTION_RECONCILING,PROMOTED,OBSERVING,RETIRED,FAILED}`. This set must equal the PLAN §14.0 rollout set exactly; generated validation fails on either an omitted or extra symbol.
- `effect_set_state={EMPTY,LIVE,UNRESOLVED,SETTLED_SUCCESS,SETTLED_ACCEPTED_RISK,SETTLED_FAILURE}`. Fold all bound Effect states in stable `effect_id` order: any `UNKNOWN|RECONCILING|ABSENCE_PROVED|APPLICATION_RECONCILED|UNRESOLVED|QUARANTINED|COMPENSATION_UNKNOWN` => `UNRESOLVED`; else any nonterminal => `LIVE`; else any `FAILED_FINAL|COMPENSATION_FAILED` => `SETTLED_FAILURE`; else any `ACCEPTED_RISK` => `SETTLED_ACCEPTED_RISK`; else any effect => `SETTLED_SUCCESS`; no effects => `EMPTY`.
- `cleanup_set_state={NOT_REQUIRED,PENDING,RUNNING,RETRY_WAIT,CLEANUP_FAILED,ESCALATION_PENDING,CLEANED,ESCALATED_DISPOSITION}`. Fold required CleanupItems: no manifest => `NOT_REQUIRED`; any `CLEANUP_FAILED` => `CLEANUP_FAILED`; else any `ESCALATION_PENDING` => `ESCALATION_PENDING`; else any `RUNNING` => `RUNNING`; else any `RETRY_WAIT` => `RETRY_WAIT`; else any `PENDING` => `PENDING`; else all `CLEANED` => `CLEANED`; else all terminal with at least one actual `ESCALATED_DISPOSITION` => `ESCALATED_DISPOSITION`. Mixed or empty-invalid sets reject.
- `rollback_state={IDLE,REQUESTED,ROLLING_BACK,VERIFYING,VERIFIED,FAILED,REMEDIATION_WAIT,ROLLED_BACK}`. It is the exact state of the single bound rollback saga. More than one saga or a non-monotone/unlisted edge rejects.
- `work_cancel_state={NONE,REQUESTED,QUIESCING,CLEANING,CANCELLED}`. It is the exact state of IX01–IX04 below.

**Reachability invariants.** Canary states require candidate `SHADOW_PASSED|FROZEN|REVOKED`, except `EVIDENCE_STALE` is legal only in the fenced abort/reconciliation/failure result of IC24-A and can never authorize progress; promotion states require a complete canary bundle and distinct current `PromotionDecision`; widening states require a prior-slice complete bundle and distinct current `WideningDecision`; `PROMOTING|PROMOTED|OBSERVING` require control `HEALTHY`; `PROMOTED|OBSERVING` require promotion effect `RECEIPT_VERIFIED`; rollback cannot coexist with new promotion/widening authority; cleanup cannot be complete while an effect, child, or release attempt is live. `WIDENING_RECONCILING|PROMOTION_RECONCILING` fence all sends and cannot coexist with rollback `REQUESTED|ROLLING_BACK|VERIFYING|VERIFIED`; they leave only after the exact original Effect is settled and classified. Impossible tuples reject rather than normalize.

### 15.1 Deterministic total reducer

Each priority predicate includes “and no earlier priority matched,” so predicates are disjoint. The tables below enumerate every symbol in every coordinate. A component event is legal only when its old/new coordinate edge is listed later and the resulting projection is `S`, one §2 edge, or the exact sequence on that row.

| Priority | Exact predicate | Canonical result |
|---|---|---|
| 1 | invariant/version/digest failure | reject; retain tuple; security audit |
| 2 | cancellation is pending and `rollback_state=REQUESTED\|ROLLING_BACK\|VERIFYING\|VERIFIED\|FAILED\|REMEDIATION_WAIT` | respectively `ROLLBACK_REQUESTED\|ROLLING_BACK\|ROLLBACK_VERIFYING\|ROLLBACK_VERIFIED\|ROLLBACK_FAILED\|BLOCKED`; cancellation blocks every non-safety coordinate and resumes IX projection after rollback settles |
| 2a | cancellation is pending and the pre-cancel canonical state was `CLEANING` | `CLEANING`; IX05 adopts the cancel disposition without leaving cleanup |
| 3 | `work_cancel_state=REQUESTED` | `CANCEL_REQUESTED` |
| 4 | `work_cancel_state=QUIESCING` | `QUIESCING` |
| 5 | `work_cancel_state=CLEANING` | `CLEANING` |
| 6 | `work_cancel_state=CANCELLED` and `clean` | `CANCELLED` |
| 7 | no cancellation pending and `rollback_state=REQUESTED\|ROLLING_BACK\|VERIFYING\|VERIFIED\|FAILED\|REMEDIATION_WAIT` | respectively `ROLLBACK_REQUESTED\|ROLLING_BACK\|ROLLBACK_VERIFYING\|ROLLBACK_VERIFIED\|ROLLBACK_FAILED\|BLOCKED` |
| 7a | no cancellation pending and `rollback_state=ROLLED_BACK` and `cleanup_set_state=NOT_REQUIRED` | `ROLLED_BACK`; if `rollback_origin=WIDENING_ABORT`, the tuple remains `ROLLED_BACK` through IR12/IR13A and IR13C-X alone schedules cleanup; otherwise IRB08 alone schedules cleanup |
| 8 | `effect_set_state=UNRESOLVED` | `QUARANTINED` |
| 9 | exact `DONE` terminal conjunction stated below | `DONE` |
| 10 | exact `FAILED` terminal conjunction stated below | `FAILED` |
| 11 | `cleanup_set_state=PENDING\|RUNNING\|RETRY_WAIT\|CLEANUP_FAILED\|ESCALATION_PENDING\|ESCALATED_DISPOSITION` | `CLEANING` (`ESCALATED_DISPOSITION` is terminal-eligible only under §13 and never for success) |
| 12 | `release_attempt_state=LEASED\|EXECUTING\|VERIFYING` | respectively `LEASED\|IMPLEMENTING\|VERIFYING` |
| 13 | `release_attempt_state=CANCEL_REQUESTED\|QUIESCING\|CLEANING\|CANCELLED` | `SAVED`; release-attempt cancellation is a subordinate coordinate and never derives parent cancellation or terminality |
| 14 | `release_attempt_state=FAILURE_PENDING_CLEANUP` | `CLEANING` until priority 10 applies |
| 15 | `control_health_state=TELEMETRY_DEGRADED\|CONTROL_PAUSED\|CONTROL_FAILED` | `BLOCKED` |
| 16 | exhaustive rollout map yields a value other than `SAVED` | that exact rollout-map value |
| 17 | exhaustive candidate map (always yields a canonical state) | that exact candidate-map value |

| Coordinate | Exhaustive symbol-to-canonical map used at priority 13 or 14 |
|---|---|
| rollout | `DISABLED->SAVED`; `ENABLEMENT_REVIEW\|CANARY_PENDING_APPROVAL\|CANARY_READY\|CANARY_RUNNING\|WIDENING_REVIEW\|CANARY_PAUSED\|CANARY_PASSED\|CANARY_FAILED\|CANARY_ABORTING\|CANARY_ABORTED\|CANARY_ABORT_SETTLED\|PROMOTION_PENDING_APPROVAL->REVIEW`; `WIDENING_EFFECT->REVIEW`; `WIDENING_RECONCILING\|PROMOTION_RECONCILING->BLOCKED`; `APPROVED\|PROMOTING->MERGE_QUEUED`; `PROMOTED\|OBSERVING->OBSERVING`; `FAILED\|RETIRED->CLEANING` |
| candidate | `DISCOVERED->INBOX`; `PROPOSED->PLANNING`; `CURATION_REVIEW\|CURATION_PASSED->READY_REVIEW`; `OFFLINE_PENDING->READY`; `OFFLINE_RUNNING\|OFFLINE_PASSED\|SHADOW_PENDING\|SHADOW_RUNNING->VERIFYING`; `SHADOW_PASSED->REVIEW`; `CURATION_FAILED\|OFFLINE_FAILED\|SHADOW_FAILED\|REJECTED\|EXPIRED\|FAILED\|RETIRED->CLEANING`; `EVIDENCE_STALE\|FROZEN\|REVOKED->BLOCKED` |
| release attempt (remaining values) | `IDLE->SAVED`; `READY->READY`; `SUCCEEDED->SAVED`; `CANCEL_REQUESTED\|QUIESCING\|CLEANING\|CANCELLED->SAVED` (whole-work IX state alone projects cancellation) |
| control health (remaining value) | `HEALTHY->SAVED` |
| effects (remaining values) | `EMPTY\|SETTLED_SUCCESS\|SETTLED_ACCEPTED_RISK\|SETTLED_FAILURE->SAVED`; their exact outcome guard is consumed by terminal rows |
| cleanup (remaining values) | `NOT_REQUIRED\|CLEANED->SAVED` |
| rollback (remaining value) | `IDLE->SAVED` |
| cancellation (remaining value) | `NONE->SAVED` |

`SAVED` means continue to the next lower-priority coordinate, not a default result. Priority 17 always returns because the candidate map enumerates every candidate symbol. Terminal resolution is exact: `DONE` requires candidate/rollout successful retired disposition, rollout observation success, effect set `EMPTY|SETTLED_SUCCESS` (or exact-policy `SETTLED_ACCEPTED_RISK`), rollback `IDLE\|ROLLED_BACK`, release attempt `IDLE|SUCCEEDED`, control `HEALTHY`, cleanup `CLEANED`, and no live child/authority and, for any rollback-safety obligation, its exact purpose/digest-bound BlockReleaseReceipt; `FAILED` requires candidate or rollout failure/rejection/expiry plus effects settled, rollback `IDLE\|ROLLED_BACK`, release attempt `IDLE|FAILED|SUCCEEDED`, cleanup `CLEANED|eligible ESCALATED_DISPOSITION`, no live child/authority, and any rollback-safety BlockReleaseReceipt; `CANCELLED` requires IX04 and the same release-receipt guard. A settled `rollback_state=ROLLED_BACK` does not permanently mask cleanup or a terminal conjunction. The exact cleanup-origin partition is closed: with `work_cancel_state=NONE`, `rollback_origin=WIDENING_ABORT` uses exactly IR13C-X after IR13A or IR13C-N after IR13B, and every other origin uses IRB08; with cancellation `REQUESTED|QUIESCING`, IX03 alone owns cleanup for every origin. Each owner changes cleanup `NOT_REQUIRED->PENDING`, priority 11 requires its stated canonical edge into `CLEANING`, and a later cleanup receipt permits priority 9 or 10. Until exact terminal conjunctions hold the mapped result is `CLEANING` or the higher-priority safe state. Thus failure, stale, frozen, revoked, canary-failed, aborting, aborted, rollout-failed, every release-attempt value, every control value, and every aggregate value have one result.

This reducer does not permit `VERIFYING -> READY` or `READY -> OBSERVING`. Offline/shadow remain in one admitted verification span. Canary is a distinct child beginning at `INBOX`; its real events and receipts drive separate parent synchronization rows. Promotion follows `REVIEW -> MERGE_QUEUED -> MERGED -> DEPLOYING -> OBSERVING`.

### 15.2 Candidate machine v1

Initial: `DISCOVERED`. Terminal dispositions: `REJECTED`, `EXPIRED`, `RETIRED`, `FAILED`; `REVOKED` and `FROZEN` are nonterminal while rollback/authority/cleanup remains.
| ID | Source | Target | Guard / trigger | Canonical projection | Wait/stale | Effects/cleanup | Disposition |
|---|---|---|---|---|---|---|---|
| IC01 | DISCOVERED | PROPOSED | proposal sealed | INBOX>TRIAGED>PLANNING | none | none | - |
| IC02 | PROPOSED | CURATION_REVIEW | curation subject sealed | PLANNING>READY_REVIEW | none | none | - |
| IC03 | CURATION_REVIEW | CURATION_PASSED | CurationDecision accept+fresh identity snapshot | REDUCE-V1 | none | none | - |
| IC04 | CURATION_REVIEW | CURATION_FAILED | CurationDecision deny | READY_REVIEW>PLANNING>CLEANING | wait closes | schedule cleanup | - |
| IC05 | CURATION_FAILED | REJECTED | failure disposition sealed | S | none | cleanup already scheduled | not work-terminal |
| IC06 | CURATION_PASSED | OFFLINE_PENDING | stage manifest bound; candidate projection makes canonical READY before IA01 | READY_REVIEW>READY | none | none | - |
| IC07 | OFFLINE_PENDING | OFFLINE_RUNNING | durable IA04 OutputsSealed receipt after IA01–IA04 occurred as separate transactions | REDUCE-V1 | none | consume protected-evaluator receipt | - |
| IC08 | OFFLINE_RUNNING | OFFLINE_PASSED | complete offline bundle passes | REDUCE-V1 | none | seal evidence | - |
| IC09 | OFFLINE_RUNNING | OFFLINE_FAILED | failed/inconclusive | VERIFYING>CLEANING | none | seal evidence; schedule cleanup | - |
| IC10 | OFFLINE_FAILED | FAILED | failure disposition sealed | S | none | cleanup already scheduled | not work-terminal |
| IC11 | OFFLINE_PASSED | SHADOW_PENDING | shadow manifest bound | REDUCE-V1 | none | none | - |
| IC12 | SHADOW_PENDING | SHADOW_RUNNING | protected shadow starts | REDUCE-V1 | none | read-only shadow | - |
| IC13 | SHADOW_RUNNING | SHADOW_PASSED | complete shadow bundle passes+consume already-durable IA05 success receipt | VERIFYING>REVIEW | none | seal evidence | - |
| IC14 | SHADOW_RUNNING | SHADOW_FAILED | failed/inconclusive | VERIFYING>CLEANING | none | seal evidence; schedule cleanup | - |
| IC15 | SHADOW_FAILED | FAILED | failure disposition sealed | S | none | cleanup already scheduled | not work-terminal |
| IC16 | PROPOSED | EVIDENCE_STALE | bound digest changed | REDUCE-V1 | stale; revoke | settle | - |
| IC17 | CURATION_REVIEW | EVIDENCE_STALE | bound digest changed | REDUCE-V1 | stale; revoke | settle | - |
| IC18 | CURATION_PASSED | EVIDENCE_STALE | bound digest changed | REDUCE-V1 | stale; revoke | settle | - |
| IC19 | OFFLINE_PENDING | EVIDENCE_STALE | bound digest changed | REDUCE-V1 | stale; revoke | settle | - |
| IC20 | OFFLINE_RUNNING | EVIDENCE_STALE | bound digest changed | REDUCE-V1 | stale; revoke | settle | - |
| IC21 | OFFLINE_PASSED | EVIDENCE_STALE | bound digest changed | REDUCE-V1 | stale; revoke | settle | - |
| IC22 | SHADOW_PENDING | EVIDENCE_STALE | bound digest changed | REDUCE-V1 | stale; revoke | settle | - |
| IC23 | SHADOW_RUNNING | EVIDENCE_STALE | bound digest changed | REDUCE-V1 | stale; revoke | settle | - |
| IC24 | SHADOW_PASSED | EVIDENCE_STALE | bound digest changed and rollout is outside `ActiveRolloutDigestCoordinatesV1`; no active Effect/exposure/grant/send | REDUCE-V1 | stale; revoke | settle | - |
| IC25 | EVIDENCE_STALE | PROPOSED | proposal/input changed | REDUCE-V1 | refresh | none | - |
| IC26 | EVIDENCE_STALE | OFFLINE_PENDING | offline-only input changed+prior curation current | REDUCE-V1 | refresh | none | - |
| IC27 | EVIDENCE_STALE | SHADOW_PENDING | shadow-only input changed+prior stages current | REDUCE-V1 | refresh | none | - |
| IC28 | PROPOSED | REJECTED | curator final reject | PLANNING>CLEANING | none | schedule cleanup | not work-terminal |
| IC29 | PROPOSED | EXPIRED | proposal expiry | PLANNING>CLEANING | none | schedule cleanup | not work-terminal |
| IC30 | SHADOW_PASSED | FROZEN | safety/identity/telemetry hold | REVIEW>BLOCKED | wait | revoke | - |
| IC31 | FROZEN | SHADOW_PASSED | fresh resolution | BLOCKED>REVIEW | resume | none | - |
| IC24-A | SHADOW_PASSED | EVIDENCE_STALE | bound digest changes at an actual active rollout/Effect coordinate; exact `IC32SafetyPartitionV1` branch X, N, or UNSETTLED executes atomically | REDUCE-V1 or the exact partition projection | stale; close decisions/waits | fence every grant/send, stop or quiesce child; reuse existing rollback or create exactly one only for X; reconciliation precedes classification for UNSETTLED; later cleanup only IR13C-X/N, IRB08, or IX03 | stale active rollout |
| IC32-F | FROZEN | REVOKED | revocation at any actual reachable rollout/Effect/rollback coordinate; exact `IC32SafetyPartitionV1` branch executes atomically | REDUCE-V1 or exact partition projection | close waits | revoke/fence; stop/quiesce; reuse/create rollback exactly once as partition requires; no cleanup owner change | held candidate revoked |
| IC32-E | EVIDENCE_STALE | REVOKED | revocation at any actual reachable rollout/Effect/rollback coordinate; exact `IC32SafetyPartitionV1` branch executes atomically | REDUCE-V1 or exact partition projection | close waits | revoke/fence; stop/quiesce; reuse/create rollback exactly once as partition requires; no cleanup owner change | stale candidate revoked |
| IC32-N | SHADOW_PASSED | REVOKED | revocation+protected `NoExposureReceipt` for exact rollout/effect coordinate; synchronized rollout in `DISABLED\|ENABLEMENT_REVIEW\|CANARY_PENDING_APPROVAL\|CANARY_READY\|CANARY_RUNNING\|CANARY_PAUSED\|CANARY_PASSED\|CANARY_FAILED\|WIDENING_REVIEW\|PROMOTION_PENDING_APPROVAL` -> `FAILED` and cleanup `NOT_REQUIRED->PENDING` | REVIEW>CLEANING | none | revoke/fence authority; no rollback; create CleanupManifest exactly once | no exposure |
| IC32-NA | SHADOW_PASSED | REVOKED | revocation in `APPROVED`+protected NoExposureReceipt covering prior canary/target effects+protected no-promotion-send fact; synchronized rollout -> `FAILED`, cleanup `NOT_REQUIRED->PENDING` | MERGE_QUEUED>CLEANING | close approval/grant | revoke/fence; no rollback; create CleanupManifest once | no exposure approved |
| IC32-CX | SHADOW_PASSED | REVOKED | revocation+current `ExposureReceipt`; synchronized rollout `CANARY_RUNNING\|CANARY_PAUSED\|CANARY_PASSED->CANARY_ABORTING` and rollback `IDLE->REQUESTED` | REVIEW>ROLLBACK_REQUESTED | none | revoke/fence; create one `WIDENING_ABORT` rollback saga; IR13A then IR13C-X or IX03 owns cleanup | exposed canary |
| IC32-PX | SHADOW_PASSED | REVOKED | revocation+current `ExposureReceipt`; synchronized rollout `PROMOTED\|OBSERVING->FAILED` and rollback `IDLE->REQUESTED` | OBSERVING>ROLLBACK_REQUESTED | none | revoke/fence; create one `CANDIDATE_REVOCATION` rollback saga; IRB08/IX03 owns cleanup | exposed promotion |
| IC32-WX | SHADOW_PASSED | REVOKED | revocation in `WIDENING_EFFECT`+exact original Effect settled/reconciled+current protected `ExposureReceipt`; synchronized rollout -> `CANARY_ABORTING` and rollback `IDLE->REQUESTED` | REVIEW>ROLLBACK_REQUESTED | none | revoke/fence; create one `WIDENING_ABORT` rollback saga | exposed widening |
| IC32-WN | SHADOW_PASSED | REVOKED | revocation in `WIDENING_EFFECT`+all bound effects settled with protected proved non-application; synchronized rollout -> `FAILED` and cleanup `NOT_REQUIRED->PENDING` | REVIEW>CLEANING | none | revoke/fence; no rollback; create CleanupManifest once | no exposure widening |
| IC32-MX | SHADOW_PASSED | REVOKED | revocation in `PROMOTING`+exact original Effect settled/reconciled+current protected `ExposureReceipt`; synchronized rollout -> `FAILED` and rollback `IDLE->REQUESTED` | MERGE_QUEUED>ROLLBACK_REQUESTED | none | revoke/fence; create one `CANDIDATE_REVOCATION` rollback saga | exposed promotion mutation |
| IC32-MN | SHADOW_PASSED | REVOKED | revocation in `PROMOTING`+all bound effects settled with protected proved non-application; synchronized rollout -> `FAILED` and cleanup `NOT_REQUIRED->PENDING` | MERGE_QUEUED>CLEANING | none | revoke/fence; no rollback; create CleanupManifest once | no exposure promotion mutation |
| IC32-UW | SHADOW_PASSED | REVOKED | revocation while exact rollout `WIDENING_EFFECT` and original Effect is `SENDING\|UNKNOWN\|RECONCILING\|ABSENCE_PROVED\|APPLICATION_RECONCILED\|UNRESOLVED\|QUARANTINED` or otherwise unsettled; synchronized rollout -> `WIDENING_RECONCILING` | BLOCKED | reconcile | atomically revoke/fence and stop sends; no rollback yet | unsettled |
| IC32-UP | SHADOW_PASSED | REVOKED | revocation while exact rollout `PROMOTING` and original Effect is unsettled; synchronized rollout -> `PROMOTION_RECONCILING` | BLOCKED | reconcile | atomically revoke/fence and stop sends; no rollback yet | unsettled |
| IC24-RWX | EVIDENCE_STALE | EVIDENCE_STALE | `WIDENING_RECONCILING` entered by IC24-A+`control_health_state=HEALTHY`+`work_cancel_state=NONE`+the exact original Effect has now settled+current protected ExposureReceipt; atomically synchronized rollout `WIDENING_RECONCILING->CANARY_ABORTING` and rollback `IDLE->REQUESTED` | BLOCKED>ROLLBACK_REQUESTED | none | preserve exact original Effect identity and reconciliation receipt; atomically stop/fence exposure and create the one rollback saga with immutable `WIDENING_ABORT` origin under version/absent-or-same CAS; the target tuple admits IRB01 dispatch; same bytes replay and conflicting classification reject; no revocation event or unrelated revoke is required | stale exposed widening continuation |
| IC24-RPX | EVIDENCE_STALE | EVIDENCE_STALE | `PROMOTION_RECONCILING` entered by IC24-A+`control_health_state=HEALTHY`+`work_cancel_state=NONE`+the exact original Effect has now settled+current protected ExposureReceipt; atomically synchronized rollout `PROMOTION_RECONCILING->FAILED` and rollback `IDLE->REQUESTED` | BLOCKED>ROLLBACK_REQUESTED | none | preserve exact original Effect identity and reconciliation receipt; atomically stop/fence exposure and create the one rollback saga with immutable non-widening `CANDIDATE_REVOCATION` origin under version/absent-or-same CAS; the target tuple admits IRB01 dispatch; same bytes replay and conflicting classification reject; no revocation event or unrelated revoke is required | stale exposed promotion continuation |
| IC24-RN | EVIDENCE_STALE | EVIDENCE_STALE | `WIDENING_RECONCILING\|PROMOTION_RECONCILING` entered by IC24-A+`control_health_state=HEALTHY`+`work_cancel_state=NONE`+complete bound Effect set is settled with protected generation/all-target no-application proof; synchronized rollout -> `FAILED`, cleanup `NOT_REQUIRED->PENDING` | BLOCKED>CLEANING | none | preserve original Effect identity; create no rollback; create the one byte-identical CleanupManifest under absent-or-same CAS; this row is the sole N cleanup-entry owner and no revocation event is required | stale no-exposure continuation |
| IC32-RWX | REVOKED | REVOKED | `WIDENING_RECONCILING`+`control_health_state=HEALTHY`+exact original Effect settled+protected current `ExposureReceipt`; synchronized rollout -> `CANARY_ABORTING` and rollback `IDLE->REQUESTED` | BLOCKED>ROLLBACK_REQUESTED | none | create one `WIDENING_ABORT` rollback saga; IR13A then IR13C-X or IX03 | exposed after widening reconciliation |
| IC32-RPX | REVOKED | REVOKED | `PROMOTION_RECONCILING`+`control_health_state=HEALTHY`+exact original Effect settled+protected current `ExposureReceipt`; synchronized rollout -> `FAILED` and rollback `IDLE->REQUESTED` | BLOCKED>ROLLBACK_REQUESTED | none | create one non-widening `CANDIDATE_REVOCATION` rollback saga; IRB08/IX03 | exposed after promotion reconciliation |
| IC32-RN | REVOKED | REVOKED | `WIDENING_RECONCILING\|PROMOTION_RECONCILING`+`control_health_state=HEALTHY`+all bound effects settled with protected proved non-application; synchronized rollout -> `FAILED` and cleanup `NOT_REQUIRED->PENDING` | BLOCKED>CLEANING | none | no rollback; create CleanupManifest exactly once | no exposure after reconciliation |
| IC32-LX | SHADOW_PASSED | REVOKED | revocation in `WIDENING_REVIEW\|PROMOTION_PENDING_APPROVAL`+current protected ExposureReceipt+rollback `IDLE->REQUESTED`; synchronized rollout -> `CANARY_ABORTING` | REVIEW>ROLLBACK_REQUESTED | close decision waits | revoke/fence, stop exposure and child, create one `WIDENING_ABORT` saga; IR13A then IR13C-X or IX03 | exposed before promotion |
| IC32-AX | SHADOW_PASSED | REVOKED | revocation in `APPROVED`+current protected ExposureReceipt+protected no-promotion-send fact+rollback `IDLE->REQUESTED`; synchronized rollout -> `CANARY_ABORTING` | MERGE_QUEUED>ROLLBACK_REQUESTED | close decision/grant | revoke/fence, stop prior exposure, create one `WIDENING_ABORT` saga; no promotion application claimed | exposed approved |
| IC32-FX | SHADOW_PASSED | REVOKED | revocation in `CANARY_FAILED`+durable exposed classifier+rollback `IDLE->REQUESTED`; synchronized rollout -> `CANARY_ABORTING` | REVIEW>ROLLBACK_REQUESTED | stop/quiesce child | create the one `WIDENING_ABORT` saga; no duplicate | exposed failed canary |
| IC32-ABX | SHADOW_PASSED | REVOKED | revocation in `CANARY_ABORTING\|CANARY_ABORTED\|CANARY_ABORT_SETTLED`+durable exposed classifier+rollback already `REQUESTED\|ROLLING_BACK\|VERIFYING\|VERIFIED\|FAILED\|REMEDIATION_WAIT\|ROLLED_BACK` | S | stop/quiesce/replay exact revocation receipt | revoke/fence only; preserve the existing saga and origin; create no duplicate; later IR13A and IR13C-X or IX03 own cleanup | exposed abort already protected |
| IC32-ABN | SHADOW_PASSED | REVOKED | revocation in `CANARY_ABORTING\|CANARY_ABORTED\|CANARY_ABORT_SETTLED`+protected generation-bound NoExposureReceipt+rollback `IDLE` | S | stop/quiesce/replay exact revocation receipt | revoke/fence; preserve no-exposure classifier; no rollback; IR13B then IR13C-N or IX03 owns cleanup | no-exposure abort |
| IC32-HU | SHADOW_PASSED | REVOKED | revocation in `WIDENING_RECONCILING\|PROMOTION_RECONCILING` while original Effect remains unsettled | S | stop/quiesce and continue exact reconciliation | revoke/fence only; no rollback and no cleanup until classification; replay returns same receipt | unsettled reconciliation |
| IC32-HWX | SHADOW_PASSED | REVOKED | revocation in `WIDENING_RECONCILING`+settled original Effect+protected ExposureReceipt+rollback `IDLE->REQUESTED`; synchronized rollout -> `CANARY_ABORTING` | BLOCKED>ROLLBACK_REQUESTED | none | create one `WIDENING_ABORT` saga; no duplicate | exposed reconciled widening |
| IC32-HPX | SHADOW_PASSED | REVOKED | revocation in `PROMOTION_RECONCILING`+settled original Effect+protected ExposureReceipt+rollback `IDLE->REQUESTED`; synchronized rollout -> `FAILED` | BLOCKED>ROLLBACK_REQUESTED | none | create one candidate-revocation saga; no duplicate | exposed reconciled promotion |
| IC32-HN | SHADOW_PASSED | REVOKED | revocation in `WIDENING_RECONCILING\|PROMOTION_RECONCILING`+all bound effects settled+protected proved non-application; synchronized rollout -> `FAILED`, cleanup `NOT_REQUIRED->PENDING` | BLOCKED>CLEANING | none | no rollback; create CleanupManifest once | no-exposure reconciliation |
| IC32-CA | SHADOW_PASSED | REVOKED | revocation while rollout is `FAILED\|RETIRED` and its previously committed CleanupManifest has cleanup `PENDING\|RUNNING\|RETRY_WAIT\|CLEANUP_FAILED\|ESCALATION_PENDING`; all effects are settled or are owned by the existing cleanup/reconciliation record | S or exact `REDUCE-V1` result, with fixed-point equality required | adopt existing cleanup owner | atomically record revocation and fence residual authority; preserve the byte-identical CleanupManifest, rollback saga, cleanup fold, and origin; create no rollback, manifest, item, or duplicate owner; same event stutters and conflicting bytes reject | cleanup adoption |

`IC24-RWX`, `IC24-RPX`, and `IC24-RN` are the only continuations after IC24-A has moved an unsettled original Effect to reconciliation while preserving candidate `EVIDENCE_STALE`. They preserve the exact Effect identity and do not require an unrelated revocation. The X rows atomically leave the forbidden reconciliation coordinates before requesting rollback: widening targets `CANARY_ABORTING` with `WIDENING_ABORT`, promotion targets `FAILED` with `CANDIDATE_REVOCATION`; both then admit IRB01. They create-or-reuse at most one rollback; the N row is the one cleanup-entry owner. Their source-set is exactly the HEALTHY settled X/N outcomes reachable from IC24-A and is disjoint from the REVOKED and SHADOW_PASSED reconciliation rows. If IH01-WR/PR wins before settlement, the health coordinate is no longer HEALTHY and only the matching IH06-WX/WN/PX/PN may consume settlement; if settlement wins first, exactly the healthy IC24 continuation applies before any later interrupt.

`IC32SafetyPartitionV1` is the closed generated relation over every actual reachable `{candidate source in SHADOW_PASSED,FROZEN,EVIDENCE_STALE; rollout; target Effect; rollback}` coordinate while cancellation is NONE. It classifies each coordinate exactly once as protected X, protected N, or UNSETTLED. X atomically fences grants/sends, stops or quiesces the child, reuses an existing matching rollback saga or creates exactly one purpose-bound saga, and never duplicates cleanup. N requires a generation/all-target protected NoExposureReceipt, creates no rollback, and preserves the later sole cleanup owner. UNSETTLED fences first, preserves the exact Effect identity, and enters the named widening/promotion reconciliation state before X/N classification. The relation contains no impossible tuple and assigns later cleanup only to IR13C-X/N, IRB08, or IX03. IC24-A uses the same relation but writes `EVIDENCE_STALE`; IC32-F/E use it while writing `REVOKED`.

The IC32 checker does not compare against a hand-maintained subset. It computes `ActualReachableRevocationCoordinatesV1` from the same generated reachability fixed point and requires exact equality with `IC32RevocationRelationV1`, the union of IC32 guards when cancellation is NONE and the IX06 synchronized revocation-safety guards when cancellation is REQUESTED or QUIESCING, including candidate source `SHADOW_PASSED|FROZEN|EVIDENCE_STALE`, rollout, Effect class `X|N|UNSETTLED`, rollback state, cleanup state, and cancellation state. It separately requires `ActiveRolloutDigestCoordinatesV1 = IC24-A guard relation` and exact fixed-point equality before and after IC32-CA cleanup adoption. The reachable rollout set includes `DISABLED`, `ENABLEMENT_REVIEW`, `CANARY_PENDING_APPROVAL`, `CANARY_READY`, `CANARY_RUNNING`, `CANARY_PAUSED`, `CANARY_PASSED`, `CANARY_FAILED`, `CANARY_ABORTING`, `CANARY_ABORTED`, `CANARY_ABORT_SETTLED`, `WIDENING_REVIEW`, `WIDENING_EFFECT`, `WIDENING_RECONCILING`, `PROMOTION_PENDING_APPROVAL`, `APPROVED`, `PROMOTING`, `PROMOTION_RECONCILING`, `PROMOTED`, `OBSERVING`, `FAILED`, and `RETIRED`. Rows reject coordinates that their receipt class makes impossible: in particular verified `PROMOTED|OBSERVING` is X, while pre-dispatch rows can be N. Existing rollback states never create a duplicate saga. IC32-RWX/RPX/RN are the HEALTHY continuation partition after IC32-UW/UP; if IH01-WR/PR wins before settlement and cancellation remains NONE, only matching IH06-WX/WN/PX/PN consumes settlement; if IX01/IX02 wins first, every IH06 row rejects and matching IX06-XR/XQ or IX06-NR/NQ consumes settlement, with IX03 the sole cleanup owner. Every row atomically revokes/fences, stops or quiesces the child and sends, preserves exact Effect reconciliation, provides deterministic replay, and assigns later cleanup only to IR13C-X/N, IRB08, or IX03.
| IC33 | REVOKED | RETIRED | rollback/authority/effects settled | REDUCE-V1 | none | cleanup | retired |
| IC34 | SHADOW_PASSED | RETIRED | never enabled+retire decision | REVIEW>CLEANING | none | schedule cleanup | retired |
| IC35 | CURATION_REVIEW | PROPOSED | CurationDecision request changes | READY_REVIEW>PLANNING | wait closes; revise/resubmit curation command | invalidate subject | - |
| IC36 | CURATION_REVIEW | EVIDENCE_STALE | CurationDecision expiry/withdrawal/stale evaluation manifest | READY_REVIEW>BLOCKED | wait closes; refresh/reseal/resubmit command | invalidate subject/downstream | - |

### 15.3 Rollout machine v1

Initial: `DISABLED`. Terminal: `RETIRED`; `CANARY_ABORTED` and `FAILED` are nonterminal until rollback/effects/cleanup settle. `WIDENING_REVIEW` and `WIDENING_EFFECT` both project to parent `REVIEW`; the bounded exposure mutation belongs to a separately admitted child/effect aggregate.

| ID | Source | Target | Guard / trigger | Canonical projection | Wait/stale | Effects/cleanup | Disposition |
|---|---|---|---|---|---|---|---|
| IR01 | DISABLED | ENABLEMENT_REVIEW | candidate shadow passed | REDUCE-V1 | W(enablement) | none | - |
| IR02 | ENABLEMENT_REVIEW | CANARY_PENDING_APPROVAL | ImprovementEnablementDecision accept | REDUCE-V1 | close enablement wait; open canary wait | none | - |
| IR03 | CANARY_PENDING_APPROVAL | CANARY_READY | distinct CanaryAdmissionDecision accept+fresh complete bundle+no active generation+every historical pair terminal, quiescent, effects/rollback settled and clean | REDUCE-V1 | wait closes | none | - |
| IR04 | CANARY_READY | CANARY_READY | no active generation+all historical pairs terminal/quiescent/effects-and-rollback-settled/clean+deterministic IDs from `(parent_work_id,stage,canary_generation,CanaryAdmissionDecision_digest)`+atomic child/link absent-or-same CAS | S + CHILD(INBOX) | exact same canonical bytes replay; different identity/payload/idempotency key rejects | create exactly one active pair for generation; no worker/output/effect fabricated | - |
| IR05 | CANARY_RUNNING | CANARY_PAUSED | telemetry gap/non-stop hold | REDUCE-V1 | W(continuity) | stop exposure | - |
| IR06 | CANARY_PAUSED | CANARY_RUNNING | control_health_state=HEALTHY+completed durable IH03 continuity restoration+fresh decision facts+continuity proof+unchanged bounds | REDUCE-V1 | resume | bounded effect remains stopped until child receipt | - |
| IR07-X | CANARY_PAUSED | CANARY_ABORTING | expiry/stop/no continuity+current `ExposureReceipt`+rollback `IDLE->REQUESTED` | REVIEW>ROLLBACK_REQUESTED | wait closes | stop/fence effect; atomically create one `WIDENING_ABORT` rollback saga | exposed |
| IR07-N | CANARY_PAUSED | CANARY_ABORTING | expiry/stop/no continuity+protected `NoExposureReceipt` | REDUCE-V1 | wait closes | stop effect; persist no-exposure abort classifier; no rollback | no exposure |
| IR08 | CANARY_RUNNING | CANARY_PASSED | control_health_state=HEALTHY+CURRENT_CONTINUITY+bound child SUCCEEDED+clean and all IR28–IR33 receipts+final complete bundle | REDUCE-V1 | child wait closes | seal outcome receipt | - |
| IR09-X | CANARY_RUNNING | CANARY_FAILED | bound child FAILED receipt or stop predicate+current `ExposureReceipt` | REDUCE-V1 | child wait closes | stop/fence effect; persist exposed abort classifier; IR11-X must enter rollback | exposed |
| IR09-N | CANARY_RUNNING | CANARY_FAILED | bound child FAILED receipt or stop predicate+protected `NoExposureReceipt` | REDUCE-V1 | child wait closes | stop effect; persist no-exposure abort classifier; IR11-N must preserve it | no exposure |
| IR10-X | CANARY_RUNNING | CANARY_ABORTING | safety stop or whole-work cancel+current `ExposureReceipt`+rollback `IDLE->REQUESTED` | REVIEW>ROLLBACK_REQUESTED | none | stop/fence child/effect; atomically create one `WIDENING_ABORT` rollback saga | exposed |
| IR10-N | CANARY_RUNNING | CANARY_ABORTING | safety stop or whole-work cancel+protected `NoExposureReceipt` | REDUCE-V1 | none | stop child/effect; persist no-exposure abort classifier; no rollback | no exposure |
| IR11-X | CANARY_FAILED | CANARY_ABORTING | stop issued+durable exposed classifier from IR09-X+rollback `IDLE->REQUESTED` | REVIEW>ROLLBACK_REQUESTED | none | atomically create one `WIDENING_ABORT` rollback saga | exposed |
| IR11-N | CANARY_FAILED | CANARY_ABORTING | stop issued+durable protected no-exposure classifier from IR09-N | REDUCE-V1 | none | preserve classifier; no rollback | no exposure |
| IR12 | CANARY_ABORTING | CANARY_ABORTED | child terminal receipt+direct termination or quiescence-closed | REDUCE-V1 | none | child rollback/cleanup | - |
| IR13A | CANARY_ABORTED | CANARY_ABORT_SETTLED | exposure or other reversible child effect existed+bound rollback_state exactly `ROLLED_BACK` through IRB07+child clean+all child effects settled | S | none | protected rollback-required branch receipt; no parent cleanup yet | - |
| IR13B | CANARY_ABORTED | CANARY_ABORT_SETTLED | protected `NoExposureReceipt` proves no ExposureEffect application and every bound effect is settled with proved non-application+child clean | S | none | rollback-not-required branch; no fake rollback; no parent cleanup yet | - |
| IR13C-X | CANARY_ABORT_SETTLED | FAILED | IR13A exposed-branch receipt is durable+`work_cancel_state=NONE`+rollback_state exactly `ROLLED_BACK`+when a rollback-safety obligation exists its exact purpose/digest-bound BlockReleaseReceipt is present+cleanup `NOT_REQUIRED->PENDING`; sole exposed widening/canary-abort cleanup entry | ROLLED_BACK>CLEANING | none | schedule parent CleanupItems; no cleanup receipt assumed | not work-terminal |
| IR13C-N | CANARY_ABORT_SETTLED | FAILED | IR13B no-exposure branch receipt is durable+`work_cancel_state=NONE`+rollback_state exactly `IDLE`+cleanup `NOT_REQUIRED->PENDING`; sole no-exposure widening/canary-abort cleanup entry | REVIEW>CLEANING | none | schedule parent CleanupItems; no cleanup receipt assumed | not work-terminal |
| IR14 | CANARY_PASSED | PROMOTION_PENDING_APPROVAL | post-canary bundle sealed | REDUCE-V1 | W(promotion) | none | - |
| IR15 | PROMOTION_PENDING_APPROVAL | APPROVED | control_health_state=HEALTHY+CURRENT_CONTINUITY+distinct PromotionDecision accept | REVIEW>MERGE_QUEUED | wait closes | promotion intent not sent | - |
| IR16 | PROMOTION_PENDING_APPROVAL | FAILED | PromotionDecision deny | REVIEW>CLEANING | wait closes | schedule cleanup | not work-terminal |
| IR17 | APPROVED | PROMOTING | control_health_state=HEALTHY+CURRENT_CONTINUITY+fresh authority+promotion effect dispatch | S | none | record/send effect; canonical remains MERGE_QUEUED | - |
| IR18 | PROMOTING | PROMOTED | control_health_state=HEALTHY+CURRENT_CONTINUITY+direct E06 verified bound promotion-effect receipt+remote identity+deployment authorization/receipt guards | MERGE_QUEUED>MERGED>DEPLOYING>OBSERVING | none | seal; CW14 occurs only here | - |
| IR19 | PROMOTED | FAILED | immediate post-apply failure; synchronized coordinates `rollout_state PROMOTED->FAILED` and `rollback_state IDLE->REQUESTED` only | OBSERVING>ROLLBACK_REQUESTED | none | create bound rollback saga | - |
| IR20 | PROMOTED | OBSERVING | control_health_state=HEALTHY+CURRENT_CONTINUITY+window starts | S | observation | none | - |
| IR21 | OBSERVING | RETIRED | control_health_state=HEALTHY+CURRENT_CONTINUITY+window pass+retire disposition | OBSERVING>CLEANING | none | schedule cleanup | retired |
| IR22 | OBSERVING | FAILED | delayed harm; synchronized coordinates `rollout_state OBSERVING->FAILED` and `rollback_state IDLE->REQUESTED` only | OBSERVING>ROLLBACK_REQUESTED | none | create bound rollback saga | - |
| IR23 | APPROVED | CANARY_PENDING_APPROVAL | bounds changed before send | MERGE_QUEUED>READY_REVIEW | stale; new decisions | none | - |
| IR24 | CANARY_READY | CANARY_PENDING_APPROVAL | decision expired/withdrawn/stale input+prior active pair has durable cancellation/terminal receipt, confirmed quiescence, all effects and rollback settled, and clean; atomically move pair to history and clear active_generation | S | W(new canary decision) | cancel unstarted child if created | - |
| IR25 | CANARY_PAUSED | WIDENING_REVIEW | control_health_state=HEALTHY+completed IH03 continuity restoration+continuity restored but bounds change | REDUCE-V1 | W(widening) | old bounds remain stopped | - |
| IR26 | FAILED | RETIRED | rollback/effects settled | REDUCE-V1 | none | schedule cleanup | retired |
| IR27 | CANARY_READY | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+durable child WorkerStarted receipt after child independently took B00/admission/lease/start edges+receipt/event binds exact IR04 child_id and link_id | REDUCE-V1 | none | consume receipt | - |
| IR28 | CANARY_RUNNING | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+durable child OutputsSealed receipt+receipt/event binds exact IR04 child_id and link_id | S | none | consume receipt | - |
| IR29 | CANARY_RUNNING | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+durable protected OracleResult receipt+receipt/event binds exact IR04 child_id and link_id | S | none | consume receipt | - |
| IR30 | CANARY_RUNNING | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+durable independent ReviewApproved receipt+receipt/event binds exact IR04 child_id and link_id | S | none | consume receipt | - |
| IR31 | CANARY_RUNNING | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+durable bounded ExposureEffect receipt+receipt/event binds exact IR04 child_id and link_id | S | none | consume receipt | - |
| IR32 | CANARY_RUNNING | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+durable TelemetryObservation receipt+receipt/event binds exact IR04 child_id and link_id | S | none | consume receipt | - |
| IR33 | CANARY_RUNNING | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+durable child cleanup/outcome receipt+receipt/event binds exact IR04 child_id and link_id | S | none | consume receipt | - |
| IR34 | CANARY_READY | CANARY_ABORTING | child FAILED after creation/admission+receipt/event binds exact IR04 generation/child_id/link_id+ExposureEffect was not dispatched+atomically create protected generation-bound `NoExposureReceipt` covering every child/target Effect | REDUCE-V1 | child wait closes | stop/cleanup child; persist no-exposure abort classifier for IR13B; no rollback | no exposure |
| IR35 | CANARY_READY | CANARY_ABORTING | child CANCELLED after creation/admission+receipt/event binds exact IR04 generation/child_id/link_id+ExposureEffect was not dispatched+atomically create protected generation-bound `NoExposureReceipt` covering every child/target Effect | REDUCE-V1 | child wait closes | settle/cleanup child; persist no-exposure abort classifier for IR13B; no rollback | no exposure |

IR34/IR35 are legal only because `CANARY_READY` has no durable WorkerStarted or exposure dispatch. The transaction rechecks the full generation effect set. If a racing receipt makes exposure possible, both rows reject; the tuple must use the reachable protected-X stop path (IR10-X/IR53-X as selected by the child event) and create rollback rather than assert no exposure.
| IR36 | CANARY_RUNNING | WIDENING_REVIEW | control_health_state=HEALTHY+CURRENT_CONTINUITY+healthy slice complete+prior-slice EvidenceBundle set-equal+new bounds proposed | REDUCE-V1 | W(widening) | old bounds remain | - |
| IR37 | WIDENING_REVIEW | WIDENING_EFFECT | control_health_state=HEALTHY+CURRENT_CONTINUITY+distinct current WideningDecision accept+continuity+unexpired exact old/new bounds | REDUCE-V1 | wait closes | create typed bounded widening effect | - |
| IR38 | WIDENING_EFFECT | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+already-durable direct E06 verified widening receipt+known telemetry+same decision/bounds/effect identity | REDUCE-V1 | none | persist new bounds | - |
| IR39 | WIDENING_REVIEW | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+request changes | REDUCE-V1 | close wait; revise/resubmit command | retain old bounds | - |
| IR40 | WIDENING_REVIEW | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+deny/withdraw | REDUCE-V1 | close wait; continue-old-bounds command | retain old bounds | - |
| IR41 | WIDENING_REVIEW | CANARY_PAUSED | decision expiry/stale manifest/telemetry | REDUCE-V1 | W(continuity/new decision) | stop exposure | - |
| IR42 | WIDENING_EFFECT | WIDENING_EFFECT | synchronized widening Effect E11 `SENDING->UNKNOWN` with rollout coordinate unchanged; ambiguous response | REVIEW>BLOCKED>QUARANTINED | bounded reconciliation | stop further exposure; ambiguity fact commits | - |
| IR43 | WIDENING_EFFECT | CANARY_ABORTING | synchronized Effect E34 `ABSENCE_PROVED->FAILED_FINAL` with signed target-effect no-application/no-retry receipt+safety stop | QUARANTINED>REVIEW | none | stop exposure; persist protected no-exposure abort classifier; IR13B accepts the settled non-applied Effect record | no exposure |
| IR44 | ENABLEMENT_REVIEW | ENABLEMENT_REVIEW | request changes | S | replace subject; resubmit enablement command | invalidate downstream | - |
| IR45 | ENABLEMENT_REVIEW | FAILED | deny/withdraw | REVIEW>CLEANING | wait closes | schedule cleanup | not work-terminal |
| IR46 | ENABLEMENT_REVIEW | ENABLEMENT_REVIEW | expiry/stale manifest | S | new enablement subject command | invalidate subject | - |
| IR47 | CANARY_PENDING_APPROVAL | CANARY_PENDING_APPROVAL | request changes | S | revise/resubmit canary command | invalidate subject | - |
| IR48 | CANARY_PENDING_APPROVAL | FAILED | deny/withdraw | REVIEW>CLEANING | wait closes | schedule cleanup | not work-terminal |
| IR49 | CANARY_PENDING_APPROVAL | CANARY_PENDING_APPROVAL | expiry/stale manifest | S | new canary subject command | invalidate subject | - |
| IR50 | PROMOTION_PENDING_APPROVAL | CANARY_PASSED | request changes | S | reseal final bundle/resubmit promotion command | invalidate subject | - |
| IR51 | PROMOTION_PENDING_APPROVAL | FAILED | withdrawal | REVIEW>CLEANING | wait closes | schedule cleanup | not work-terminal |
| IR52 | PROMOTION_PENDING_APPROVAL | CANARY_PASSED | expiry/stale manifest | S | reseal/resubmit promotion command | invalidate subject | - |
| IR53-X | CANARY_RUNNING | CANARY_ABORTING | bound child CANCELLED receipt+current `ExposureReceipt`+rollback `IDLE->REQUESTED` | REVIEW>ROLLBACK_REQUESTED | child wait closes | settle child; atomically create one `WIDENING_ABORT` rollback saga | exposed |
| IR53-N | CANARY_RUNNING | CANARY_ABORTING | bound child CANCELLED receipt+protected `NoExposureReceipt` | REDUCE-V1 | child wait closes | settle child; persist no-exposure classifier; no rollback | no exposure |
| IR54 | PROMOTING | PROMOTING | synchronized promotion Effect E11 `SENDING->UNKNOWN` with rollout unchanged | MERGE_QUEUED>BLOCKED>QUARANTINED | bounded reconciliation | no apply claim; stop sends | - |
| IR55 | PROMOTING | FAILED | synchronized original Effect `ABSENCE_PROVED->FAILED_FINAL` under E34 and rollout `PROMOTING->FAILED`; signed no-application/no-retry receipt | QUARANTINED>CLEANING | none | no rollback required because pre-MERGED; schedule cleanup | not work-terminal |
| IR56 | WIDENING_EFFECT | CANARY_RUNNING | control_health_state=HEALTHY+CURRENT_CONTINUITY+synchronized original Effect E17 `APPLICATION_RECONCILED->RECEIPT_VERIFIED`; verified reconstructed receipt binds the same widening decision, old/new bounds, generation and effect identity | QUARANTINED>REVIEW | none | atomically seal effect and persist new bounds; mutually exclusive with direct E06/IR38 | - |
| IR57 | PROMOTING | PROMOTED | control_health_state=HEALTHY+CURRENT_CONTINUITY+synchronized original Effect E17 `APPLICATION_RECONCILED->RECEIPT_VERIFIED`; verified reconstructed promotion receipt binds the same decision, bounds, remote identity and effect identity+deployment authorization/receipt guards | QUARANTINED>MERGE_QUEUED>MERGED>DEPLOYING>OBSERVING | none | atomically seal effect and cross CW14; mutually exclusive with direct E06/IR18 | - |
| IW20X | WIDENING_EFFECT | CANARY_ABORTING | synchronized E20 terminal `ACCEPTED_RISK`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | stop exposure; preserve disposition; create bound rollback saga; under cancellation NONE, IR13C-X is sole later cleanup scheduler; under REQUESTED/QUIESCING, IX03 is sole owner | - |
| IW20N | WIDENING_EFFECT | FAILED | synchronized E20 terminal `ACCEPTED_RISK`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IP20X | PROMOTING | FAILED | synchronized E20 terminal `ACCEPTED_RISK`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | create bound rollback saga; no MERGED claim; later IRB08/IX03 owns cleanup | not work-terminal |
| IP20N | PROMOTING | FAILED | synchronized E20 terminal `ACCEPTED_RISK`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IW21X | WIDENING_EFFECT | CANARY_ABORTING | synchronized E21 terminal `FAILED_FINAL`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | stop exposure; preserve disposition; create bound rollback saga; under cancellation NONE, IR13C-X is sole later cleanup scheduler; under REQUESTED/QUIESCING, IX03 is sole owner | - |
| IW21N | WIDENING_EFFECT | FAILED | synchronized E21 terminal `FAILED_FINAL`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IP21X | PROMOTING | FAILED | synchronized E21 terminal `FAILED_FINAL`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | create bound rollback saga; no MERGED claim; later IRB08/IX03 owns cleanup | not work-terminal |
| IP21N | PROMOTING | FAILED | synchronized E21 terminal `FAILED_FINAL`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IW24X | WIDENING_EFFECT | CANARY_ABORTING | synchronized E24 terminal `COMPENSATED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | stop exposure; preserve disposition; create bound rollback saga; under cancellation NONE, IR13C-X is sole later cleanup scheduler; under REQUESTED/QUIESCING, IX03 is sole owner | - |
| IW24N | WIDENING_EFFECT | FAILED | synchronized E24 terminal `COMPENSATED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IP24X | PROMOTING | FAILED | synchronized E24 terminal `COMPENSATED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | create bound rollback saga; no MERGED claim; later IRB08/IX03 owns cleanup | not work-terminal |
| IP24N | PROMOTING | FAILED | synchronized E24 terminal `COMPENSATED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IW25X | WIDENING_EFFECT | CANARY_ABORTING | synchronized E25 terminal `COMPENSATION_FAILED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | stop exposure; preserve disposition; create bound rollback saga; under cancellation NONE, IR13C-X is sole later cleanup scheduler; under REQUESTED/QUIESCING, IX03 is sole owner | - |
| IW25N | WIDENING_EFFECT | FAILED | synchronized E25 terminal `COMPENSATION_FAILED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IP25X | PROMOTING | FAILED | synchronized E25 terminal `COMPENSATION_FAILED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | create bound rollback saga; no MERGED claim; later IRB08/IX03 owns cleanup | not work-terminal |
| IP25N | PROMOTING | FAILED | synchronized E25 terminal `COMPENSATION_FAILED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IW28X | WIDENING_EFFECT | CANARY_ABORTING | synchronized E28 terminal `COMPENSATED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | stop exposure; preserve disposition; create bound rollback saga; under cancellation NONE, IR13C-X is sole later cleanup scheduler; under REQUESTED/QUIESCING, IX03 is sole owner | - |
| IW28N | WIDENING_EFFECT | FAILED | synchronized E28 terminal `COMPENSATED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IP28X | PROMOTING | FAILED | synchronized E28 terminal `COMPENSATED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | create bound rollback saga; no MERGED claim; later IRB08/IX03 owns cleanup | not work-terminal |
| IP28N | PROMOTING | FAILED | synchronized E28 terminal `COMPENSATED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IW29X | WIDENING_EFFECT | CANARY_ABORTING | synchronized E29 terminal `COMPENSATION_FAILED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | stop exposure; preserve disposition; create bound rollback saga; under cancellation NONE, IR13C-X is sole later cleanup scheduler; under REQUESTED/QUIESCING, IX03 is sole owner | - |
| IW29N | WIDENING_EFFECT | FAILED | synchronized E29 terminal `COMPENSATION_FAILED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IP29X | PROMOTING | FAILED | synchronized E29 terminal `COMPENSATION_FAILED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | create bound rollback saga; no MERGED claim; later IRB08/IX03 owns cleanup | not work-terminal |
| IP29N | PROMOTING | FAILED | synchronized E29 terminal `COMPENSATION_FAILED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IW37X | WIDENING_EFFECT | CANARY_ABORTING | synchronized E37 terminal `COMPENSATION_FAILED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | stop exposure; preserve disposition; create bound rollback saga; under cancellation NONE, IR13C-X is sole later cleanup scheduler; under REQUESTED/QUIESCING, IX03 is sole owner | - |
| IW37N | WIDENING_EFFECT | FAILED | synchronized E37 terminal `COMPENSATION_FAILED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IP37X | PROMOTING | FAILED | synchronized E37 terminal `COMPENSATION_FAILED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | create bound rollback saga; no MERGED claim; later IRB08/IX03 owns cleanup | not work-terminal |
| IP37N | PROMOTING | FAILED | synchronized E37 terminal `COMPENSATION_FAILED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IW39X | WIDENING_EFFECT | CANARY_ABORTING | synchronized E39 terminal `COMPENSATION_FAILED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | stop exposure; preserve disposition; create bound rollback saga; under cancellation NONE, IR13C-X is sole later cleanup scheduler; under REQUESTED/QUIESCING, IX03 is sole owner | - |
| IW39N | WIDENING_EFFECT | FAILED | synchronized E39 terminal `COMPENSATION_FAILED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IP39X | PROMOTING | FAILED | synchronized E39 terminal `COMPENSATION_FAILED`+protected ExposureReceipt proves application/exposure; rollback `IDLE->REQUESTED` atomically | QUARANTINED>ROLLBACK_REQUESTED | none | create bound rollback saga; no MERGED claim; later IRB08/IX03 owns cleanup | not work-terminal |
| IP39N | PROMOTING | FAILED | synchronized E39 terminal `COMPENSATION_FAILED`+protected NoExposureReceipt proves no application and all bound effects are settled with proved non-application | QUARANTINED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |

| IWD09N | WIDENING_EFFECT | FAILED | synchronized E09 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | REVIEW>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IPD09N | PROMOTING | FAILED | synchronized E09 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | MERGE_QUEUED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IWD10N | WIDENING_EFFECT | FAILED | synchronized E10 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | REVIEW>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IPD10N | PROMOTING | FAILED | synchronized E10 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | MERGE_QUEUED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IWD30N | WIDENING_EFFECT | FAILED | synchronized E30 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | REVIEW>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IPD30N | PROMOTING | FAILED | synchronized E30 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | MERGE_QUEUED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IWD31N | WIDENING_EFFECT | FAILED | synchronized E31 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | REVIEW>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IPD31N | PROMOTING | FAILED | synchronized E31 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | MERGE_QUEUED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IWD33N | WIDENING_EFFECT | FAILED | synchronized E33 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | REVIEW>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IPD33N | PROMOTING | FAILED | synchronized E33 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | MERGE_QUEUED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IWD35N | WIDENING_EFFECT | FAILED | synchronized E35 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | REVIEW>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |
| IPD35N | PROMOTING | FAILED | synchronized E35 terminal `FAILED_FINAL`+protected target-effect `NoApplicationReceipt` proves no send/application and all bound effects are settled with proved non-application | MERGE_QUEUED>CLEANING | none | no rollback; schedule cleanup as sole entry owner; final item uses ICL02/03 | not work-terminal |

The product rows implement an explicit reachable edge/classification relation, not a Cartesian product. Disposition edges E20, E21, E24, E25, E28, E29, E37, and E39 admit mutually exclusive `X` and `N` rows in both `WIDENING_EFFECT` and `PROMOTING`. Direct terminal edges E09, E10, E30, E31, E33, and E35 admit only their `N` rows because their target-effect-specific signed terminal receipt proves no application; the corresponding `X` row is unreachable and absent. The checker requires exact set equality with this declared relation: `{E20,E21,E24,E25,E28,E29,E37,E39} × {WIDENING_EFFECT,PROMOTING} × {X,N}` union `{E09,E10,E30,E31,E33,E35} × {WIDENING_EFFECT,PROMOTING} × {N}`. A same-target `ExposureReceipt` contradicts a direct-edge `NoApplicationReceipt` and rejects; missing, conflicting, unknown, or stale classification leaves the Effect `UNRESOLVED`/canonical `QUARANTINED` and permits no product row. E18/E19 invalid or unresolved reconstruction must first reach one of these exact terminal E20/E21/E24/E25/E28/E29/E37/E39 results; it cannot silently resume. Only direct E06 through IR38/IR18 or reconstructed E17 through IR56/IR57 can widen bounds or cross `MERGED`. Accepted risk, declared failure, compensation success, compensation failure, and invalid reconstructed outcomes never count as application success. No settled outcome projects back to `REVIEW` or `MERGE_QUEUED` without a rollout-coordinate transition. Each failure path has exactly one later cleanup owner; exposed paths first complete real rollback.


**Canary generation invariant.** The rollout stores `active_canary_generation` (zero or one exact pair) and an append-only `historical_canary_pairs` set. IR04 is absent-or-same within one generation. IR24 cannot replace a decision until the prior pair has a durable terminal/cancellation receipt, confirmed quiescence, settled effects and rollback, and clean receipts; it then atomically archives the pair and clears the active generation. IR03 and IR04 reject while any prior pair is live or unsettled. Every child event binds generation, decision digest, child ID and link ID. A delayed or out-of-order `WorkerStarted`, output, effect, terminal, or cleanup receipt for an archived generation is fenced and recorded as stale; it never mutates the active generation. Terminal and safety predicates quantify over the active pair and every historical pair, so no overlap can be masked.

### 15.3.1 Improvement rollback-coordinate machine v1

These are the only legal rollback-coordinate edges. Rollback entry is owned exactly once by IR19, IR22, every reachable exposed `IW*X`, `IWD*X`, `IP*X`, and `IPD*X` product row, IR07-X, IR10-X, IR11-X, IR53-X, IC32-CX, IC32-PX, IC32-WX, IC32-MX, IC32-RWX, IC32-RPX, IC24-RWX, IC24-RPX, IX06-XR/XQ, IH06-WX, IH06-PX, and synchronized post-exposure degradation rows IH01-WV/PV/D/O/RX. IH01-RAQ/RAR/RAV/RAD/RAF/RAM/RAO are adoption-only interrupts for an existing matching saga and never rollback-entry owners. IH01-W/P, IH01-WR/PR, and IC32-UW/UP are expressly not rollback-entry owners: they enter or preserve safe reconciliation until protected X/N settlement. Each listed owner requires `rollback_state=IDLE`, changes it atomically to `REQUESTED`, and creates the one bound saga; no later row may create a duplicate. All later rollback-machine rows change only the named rollback or cleanup coordinate; no delta is inferred. Every exposed owner whose synchronized rollout target is `CANARY_ABORTING` stamps `rollback_origin=WIDENING_ABORT`; promotion/post-promotion owners stamp their named non-widening origin. Origin is immutable.

| ID | Source | Target | Guard / trigger | Canonical projection | Effect / cleanup |
|---|---|---|---|---|---|
| IRB01 | REQUESTED | ROLLING_BACK | fresh rollback authority+tested target+original mutation Effect is terminal/reconciled and protected exposure classification is durable; rollout is not `WIDENING_RECONCILING\|PROMOTION_RECONCILING` | ROLLBACK_REQUESTED>ROLLING_BACK | dispatch rollback effect; reject any race with original Effect `SENDING\|UNKNOWN\|LIVE` |
| IRB02 | ROLLING_BACK | VERIFYING | verified restoration receipt | ROLLING_BACK>ROLLBACK_VERIFYING | start protected verification |
| IRB03 | VERIFYING | VERIFIED | protected verifier pass+known telemetry | ROLLBACK_VERIFYING>ROLLBACK_VERIFIED | seal verification |
| IRB04 | VERIFYING | FAILED | failed/unknown/timeout | ROLLBACK_VERIFYING>ROLLBACK_FAILED | revoke; bounded retry wait |
| IRB05 | FAILED | ROLLING_BACK | approved retry+fresh authority+budget | ROLLBACK_FAILED>ROLLING_BACK | new effect-attempt identity |
| IRB06 | FAILED | REMEDIATION_WAIT | retry forbidden/stale/exhausted | ROLLBACK_FAILED>BLOCKED | atomically invoke RO00-I to create protected rollback-safety RemediationObligation/MAINTENANCE child, revoke rollback authority, retain exposure and schedule bounded resurface/escalation; never claim ROLLED_BACK or clean |
| IRB07-N | VERIFIED | ROLLED_BACK | verification sealed+effect settled+`work_cancel_state=NONE`+if a bound RO00-I rollback-safety generation exists, require current RO09 ClosureReceipt, genuine restoration receipt, fresh IRB03 independent VerificationReceipt, exact purpose/generation/key-set digest, and absent BlockReleaseReceipt| ROLLBACK_VERIFIED>ROLLED_BACK | atomically seal/adopt ROLLED_BACK; when RO00-I is bound, remove only its exact exposure/resource blocks and create the purpose/digest-bound BlockReleaseReceipt under version/absent-or-same CAS; identical replay returns the receipt and conflicting bytes reject; cleanup remains unscheduled |
| IRB07-R | VERIFIED | ROLLED_BACK | verification sealed+effect settled+`work_cancel_state=REQUESTED`+authenticated cancel persisted during rollback+if a bound RO00-I rollback-safety generation exists, require current RO09 ClosureReceipt, genuine restoration receipt, fresh IRB03 independent VerificationReceipt, exact purpose/generation/key-set digest, and absent BlockReleaseReceipt| ROLLBACK_VERIFIED>ROLLED_BACK>CANCEL_REQUESTED | atomically seal/adopt ROLLED_BACK; when RO00-I is bound, remove only its exact exposure/resource blocks and create the purpose/digest-bound BlockReleaseReceipt under version/absent-or-same CAS; identical replay returns the receipt and conflicting bytes reject; cleanup remains unscheduled |
| IRB07-Q | VERIFIED | ROLLED_BACK | verification sealed+effect settled+`work_cancel_state=QUIESCING`+authenticated cancel persisted during rollback+epoch advanced+grants revoked+if a bound RO00-I rollback-safety generation exists, require current RO09 ClosureReceipt, genuine restoration receipt, fresh IRB03 independent VerificationReceipt, exact purpose/generation/key-set digest, and absent BlockReleaseReceipt| ROLLBACK_VERIFIED>ROLLED_BACK>CANCEL_REQUESTED>QUIESCING | atomically seal/adopt ROLLED_BACK; when RO00-I is bound, remove only its exact exposure/resource blocks and create the purpose/digest-bound BlockReleaseReceipt under version/absent-or-same CAS; identical replay returns the receipt and conflicting bytes reject; cleanup remains unscheduled |
| IRB08 | ROLLED_BACK | ROLLED_BACK | `work_cancel_state=NONE`+rollback saga origin is not `WIDENING_ABORT`+when a rollback-safety obligation exists its exact purpose/digest-bound BlockReleaseReceipt is present+create CleanupManifest and named cleanup-coordinate edge `NOT_REQUIRED->PENDING` | ROLLED_BACK>CLEANING | schedule CleanupItems; no cleanup receipt assumed |
| IRB09 | REMEDIATION_WAIT | VERIFYING | bound rollback-safety RemediationObligation reached CLOSED by RO09+fresh independent rollback-verification authority+genuine restoration receipt; cancellation may be NONE, REQUESTED, or QUIESCING | BLOCKED>ROLLBACK_VERIFYING | start real protected verification; obligation closure is not rollback verification |

IRB07-N/R/Q are a complete, mutually exclusive partition of rollback settlement by exact cancellation state; other cancellation values are unreachable while rollback is active. IRB08 is legal only for `NONE` and a non-widening-abort rollback origin. A widening-abort origin under `NONE` proceeds through IR13A and IR13C-X, which is its sole cleanup scheduler. When cancellation is `REQUESTED|QUIESCING`, IRB07-R/Q projects the reducer exactly and IX03 is the sole cancellation cleanup scheduler after rollback is genuinely `ROLLED_BACK`; IR13C-X/N reject because cancellation is pending. IX03 is forbidden while rollback is active, `FAILED`, or `REMEDIATION_WAIT`. It accepts `rollback_state=IDLE` only with a protected NoExposureReceipt covering every bound target Effect and no prior/reversible application; any exposure requires exactly `ROLLED_BACK`.

IRB06 is the exact final-failure owner. It cannot stutter or falsely settle. It commits `FAILED->REMEDIATION_WAIT`, canonical `ROLLBACK_FAILED>BLOCKED`, preserves the exposure/risk receipt, and creates a protected rollback-safety RemediationObligation using §13.1. While unresolved, the parent remains visibly nonterminal `BLOCKED`; RO06 supplies bounded review/resurface/escalation, resource reuse remains blocked, and no human can waive safety settlement. Only independently authorized remediation that reaches RO09 may enable IRB09. IRB09 then enters `VERIFYING` and requires a genuine restoration receipt and fresh independent verifier. IRB03 and IRB07-N/R/Q must still pass before `ROLLED_BACK`. When RO00-I exists, each IRB07-N/R/Q branch is the exact release owner: it consumes the current RO09 closure, restoration, and independent-verification receipts, checks the exact purpose/generation/key-set digest, removes only those blocks, and emits an absent-or-same `BlockReleaseReceipt` atomically with `ROLLED_BACK`. Only after that receipt exists can IRB08, IR13C-X, or IX03 own cleanup. A cancellation request is accepted at every reachable tuple, but final `CANCELLED` is promised only after genuine rollback/remediation safety settlement, quiescence, settled effects, and cleanup; unresolved remediation remains `BLOCKED` rather than becoming `ROLLED_BACK`, clean, or terminal.

### 15.4 Improvement release-attempt machine v1

This coordinate owns the parent admission span. Canary execution is a child FactoryInstance and cannot borrow this lease. Initial: `IDLE`. Attempt-local terminals: `SUCCEEDED`, `FAILED`, `CANCELLED` only after attempt effects/cleanup settle; none is a parent terminal by itself. `FAILURE_PENDING_CLEANUP` is nonterminal; `FAILED` is immutable.
| ID | Source | Target | Guard / trigger | Canonical projection | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| IA01 | IDLE | READY | curation passed+offline manifest; IC06 already made canonical READY | S | none | none | - |
| IA02 | READY | LEASED | admission+lease atomic | READY>LEASED | none | lease/context | - |
| IA03 | LEASED | EXECUTING | attested worker starts | LEASED>IMPLEMENTING | none | protected evaluator | - |
| IA04 | EXECUTING | VERIFYING | outputs sealed | IMPLEMENTING>VERIFYING | none | none | - |
| IA05 | VERIFYING | SUCCEEDED | shadow phase/evidence sealed; candidate remains SHADOW_RUNNING until IC13 | S | none | settle | success |
| IA06 | VERIFYING | EXECUTING | repair with changed input+budget | VERIFYING>IMPLEMENTING | retry | none | - |
| IA07-OP | VERIFYING | FAILURE_PENDING_CLEANUP | exhausted/failed gate; exact synchronized candidate edge `OFFLINE_PENDING->OFFLINE_FAILED`; atomically fail candidate and release attempt | VERIFYING>CLEANING | exhausted | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA07-OR | VERIFYING | FAILURE_PENDING_CLEANUP | exhausted/failed gate; exact synchronized candidate edge `OFFLINE_RUNNING->OFFLINE_FAILED`; atomically fail candidate and release attempt | VERIFYING>CLEANING | exhausted | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA07-OD | VERIFYING | FAILURE_PENDING_CLEANUP | exhausted/failed gate; exact synchronized candidate edge `OFFLINE_PASSED->OFFLINE_FAILED`; atomically fail candidate and release attempt | VERIFYING>CLEANING | exhausted | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA07-SP | VERIFYING | FAILURE_PENDING_CLEANUP | exhausted/failed gate; exact synchronized candidate edge `SHADOW_PENDING->SHADOW_FAILED`; atomically fail candidate and release attempt | VERIFYING>CLEANING | exhausted | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA07-SR | VERIFYING | FAILURE_PENDING_CLEANUP | exhausted/failed gate; exact synchronized candidate edge `SHADOW_RUNNING->SHADOW_FAILED`; atomically fail candidate and release attempt | VERIFYING>CLEANING | exhausted | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA08-OP | EXECUTING | FAILURE_PENDING_CLEANUP | nonretryable failure; exact synchronized candidate edge `OFFLINE_PENDING->OFFLINE_FAILED`; atomically fail candidate and release attempt | IMPLEMENTING>VERIFYING>CLEANING | none | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA08-OR | EXECUTING | FAILURE_PENDING_CLEANUP | nonretryable failure; exact synchronized candidate edge `OFFLINE_RUNNING->OFFLINE_FAILED`; atomically fail candidate and release attempt | IMPLEMENTING>VERIFYING>CLEANING | none | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA08-OD | EXECUTING | FAILURE_PENDING_CLEANUP | nonretryable failure; exact synchronized candidate edge `OFFLINE_PASSED->OFFLINE_FAILED`; atomically fail candidate and release attempt | IMPLEMENTING>VERIFYING>CLEANING | none | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA08-SP | EXECUTING | FAILURE_PENDING_CLEANUP | nonretryable failure; exact synchronized candidate edge `SHADOW_PENDING->SHADOW_FAILED`; atomically fail candidate and release attempt | IMPLEMENTING>VERIFYING>CLEANING | none | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA08-SR | EXECUTING | FAILURE_PENDING_CLEANUP | nonretryable failure; exact synchronized candidate edge `SHADOW_RUNNING->SHADOW_FAILED`; atomically fail candidate and release attempt | IMPLEMENTING>VERIFYING>CLEANING | none | create/preserve one cleanup manifest; IA16/IA17 own later release settlement | not terminal |
| IA09 | READY | CANCEL_REQUESTED | `work_cancel_state=REQUESTED\|QUIESCING`; IX01 already persisted whole-work cancellation | S | none | revoke attempt authority only | attempt-local cancellation |
| IA10 | LEASED | CANCEL_REQUESTED | `work_cancel_state=REQUESTED\|QUIESCING`; IX01 already persisted whole-work cancellation | S | none | revoke attempt lease/authority only | attempt-local cancellation |
| IA11 | EXECUTING | CANCEL_REQUESTED | `work_cancel_state=REQUESTED\|QUIESCING`; IX01 already persisted whole-work cancellation | S | none | revoke attempt authority; reconcile its Effect through IX safety rows | attempt-local cancellation |
| IA12 | VERIFYING | CANCEL_REQUESTED | `work_cancel_state=REQUESTED\|QUIESCING`; IX01 already persisted whole-work cancellation | S | none | revoke attempt authority; preserve settlement | attempt-local cancellation |
| IA13 | CANCEL_REQUESTED | QUIESCING | `work_cancel_state=REQUESTED\|QUIESCING`+attempt epoch advanced | S | none | settle attempt only | attempt-local quiescence |
| IA14 | QUIESCING | CLEANING | `work_cancel_state=QUIESCING\|CLEANING`+direct termination receipt or attempt quiescence-closed | S | none | schedule attempt-local cleanup only; never create or advance parent CleanupManifest/cleanup set | attempt-local cleanup |
| IA15 | CLEANING | CANCELLED | `work_cancel_state=CLEANING`+attempt cleanup origin is ordinary cancellation from IA14+attempt-local clean receipts; IX04 has not yet fired | S | none | seal attempt-local receipts only; never change parent cancellation or cleanup | attempt-local terminal, not work-terminal |
| IA16 | FAILURE_PENDING_CLEANUP | CLEANING | failure sealed+`work_cancel_state=NONE` | S | none | preserve the one existing failure CleanupManifest and advance its attempt-local cleanup only | - |
| IA17 | CLEANING | FAILED | clean+failed+`work_cancel_state=NONE`+failure cleanup origin | CLEANING>FAILED | none | receipts | failed |
| IA18-F | FAILURE_PENDING_CLEANUP | CLEANING | `work_cancel_state=REQUESTED\|QUIESCING\|CLEANING`+failure sealed+the IA07/IA08 CleanupManifest identity and cleanup origin are exact | S | none | adopt and complete the existing attempt-local failure cleanup; preserve the parent CleanupManifest byte-for-byte; create no cleanup, saga, or parent terminal | attempt-local cancellation settlement |
| IA18-C | CLEANING | CANCELLED | `work_cancel_state=REQUESTED\|QUIESCING\|CLEANING`+failure cleanup origin+attempt-local clean receipts+IX04 has not fired | S | none | seal the failure-cleanup attempt-local receipts only; preserve the parent CleanupManifest and cleanup fold; create no parent terminal | attempt-local terminal, not work-terminal |

`IA07-*` and `IA08-*` are exact disjoint synchronized product families. Their five candidate phases are the complete reachable candidate set while the release attempt is respectively `VERIFYING` or `EXECUTING`; every row atomically selects `OFFLINE_FAILED` for an offline phase or `SHADOW_FAILED` for a shadow phase. Thus `IA17` always sees the candidate-failure half of the exact FAILED conjunction. No release-attempt `FAILED` tuple is handled by the remaining-values fallback, and generic candidate failure rows cannot duplicate these owners. IA16 preserves the already-created cleanup manifest; after all receipts, IA17 alone changes the release attempt to immutable `FAILED` and the reducer reaches canonical `FAILED`.

IA09-IA15 and IA18-F/IA18-C are subordinate release-attempt cancellation rows. They are illegal while `work_cancel_state=NONE`, require the matching IX `REQUESTED|QUIESCING|CLEANING` context stated on each row, and are exact canonical stutters because the IX coordinate dominates. IA14 schedules only attempt-local cleanup and cannot create or advance the parent CleanupManifest or cleanup-set coordinate. IA15 seals only the ordinary-cancellation attempt-local `CANCELLED` disposition. IA18-F and IA18-C are the mutually exclusive failure-cleanup-origin partition: the former adopts `FAILURE_PENDING_CLEANUP`, and the latter accepts only the resulting or IA16-produced `CLEANING`; both preserve the existing IA07/IA08 parent CleanupManifest and never create a duplicate. IA16/IA17 require cancellation NONE. IX01 immediately before or after IA16 and immediately before IA17 conflicts by tuple-version CAS; after IX01, IA16/IA17 reject and only the applicable IA18 row can settle the attempt. IX05 may independently adopt the already-canonical CLEANING parent when its exact guards pass and never changes the attempt or duplicates cleanup. It cannot terminalize the work. `FailureCleanupCancellationCoordinatesV1` is the exact generated set of failure-origin attempt tuples at `FAILURE_PENDING_CLEANUP|CLEANING` with IX `REQUESTED|QUIESCING|CLEANING`; it equals the IA18-F/IA18-C source union and is total and pairwise disjoint by attempt source. No member may use IA16/IA17 or become a nonterminal sink. IX03 is the sole parent cancellation-cleanup scheduler and IX04 is the sole row that can derive canonical parent `CANCELLED`.

### 15.5 Whole-work improvement cancellation v1

`ReachableNonterminalTupleV1` is the finite set produced by starting from the declared initial tuple and applying only IC/IR/IA/IH/IX/Effect/Cleanup/Rollback rows. IX01 is authorized for each member of that set; this named generated set is reproducible from this document and is not a wildcard. The event persists the exact pre-cancel tuple digest. While cancellation is not `NONE`, ordinary candidate, rollout, control (including every IH01/IH06 row), widening, promotion, and new business-effect edges are rejected. IA09-IA15 and IA18-F/IA18-C may only advance the release-attempt subaggregate in the matching IX context and are canonical stutters; they never advance parent cancellation or parent cleanup. Cancellation-side degradation rows IXH01-R/Q/C may only record health and its bound receipt while preserving IX ownership. This blanket rejection has one closed safety allowlist only: IXH01-R/Q/C, IX06-UR/UQ/HUR/HUQ/NR/NQ/XR/XQ and IX06-E2R/E2Q/E3R/E3Q may stop and classify children/effects, invoke the exact synchronized pre-send E02/E03 settlement, reconcile the exact original Effect, mint the required all-target no-exposure proof once, and create the required unique rollback; IRB01–IRB07 and IRB09 may advance that already-required rollback; Effect reconciliation rows, U09/A18 quiescence closure, and IX cleanup may advance. E02/E03 during cancellation are legal only through those synchronized IX06 rows. No allowlisted row grants ordinary progress, sends a new business effect, or creates a second rollback saga.

| ID | Source | Target | Guard / trigger | Canonical projection | Wait/retry | Effects/cleanup | Terminal |
|---|---|---|---|---|---|---|---|
| IX01 | NONE | REQUESTED | authenticated cancel+current tuple is a member of `ReachableNonterminalTupleV1` | REDUCE-V1 | close all waits | advance epochs; revoke decisions/grants; propagate cancel to every child; stop/reconcile effects | - |
| IX02 | REQUESTED | QUIESCING | all stop/reconcile/rollback intents durably scheduled; safety rollback may remain active | REDUCE-V1 | none | no new business effects | - |
| IX03 | QUIESCING | CLEANING | all children terminal+direct termination receipts or quiescence-closed+all effects settled; if rollback `IDLE`, protected `NoExposureReceipt` covers every bound target Effect and proves no prior/reversible application; if any exposure or reversible application exists, rollback is exactly `ROLLED_BACK` and any rollback-safety obligation has its exact purpose/digest-bound BlockReleaseReceipt (never REQUESTED/ROLLING_BACK/VERIFYING/VERIFIED/FAILED/REMEDIATION_WAIT) | REDUCE-V1 | none | sole cancellation cleanup owner; schedule CleanupItems; no cleanup receipt assumed | - |
| IX04 | CLEANING | CANCELLED | clean from previously committed receipts+no live child/authority/effect/rollback/attempt | REDUCE-V1 | none | prior receipts | cancelled |
| IX05 | REQUESTED | CLEANING | IX01 pre-cancel tuple was already canonical CLEANING+all stop/effect/rollback predicates settled | S | none | preserve existing CleanupItems; set cancel disposition | - |
| IX06-UR | REQUESTED | REQUESTED | exact original Effect at `WIDENING_EFFECT\|PROMOTING` is unsettled; synchronized rollout -> `WIDENING_RECONCILING\|PROMOTION_RECONCILING`; candidate is exactly `SHADOW_PASSED\|FROZEN\|EVIDENCE_STALE->REVOKED` when revocation is the trigger, or already `REVOKED` on replay/continuation | S | reconcile exact Effect | atomically stop/fence sends and child, preserve Effect identity, create no rollback until classification | unsettled |
| IX06-UQ | QUIESCING | QUIESCING | same unsettled partition, exact revocation candidate mapping, and synchronized rollout mapping as IX06-UR | S | reconcile exact Effect | atomically stop/fence sends and child, preserve Effect identity, create no rollback until classification | unsettled |
| IX06-HUR | REQUESTED | REQUESTED | authenticated revocation while exact rollout is already `WIDENING_RECONCILING\|PROMOTION_RECONCILING`, exact original Effect remains `UNSETTLED`, and candidate is exactly `SHADOW_PASSED\|FROZEN\|EVIDENCE_STALE->REVOKED` | S | continue exact reconciliation | atomically record revocation and keep the existing fence; preserve exact Effect/reconciliation/rollback/cleanup identities and states; create no saga or cleanup; same event replays byte-identically and a conflicting event/classifier rejects | unsettled reconciliation |
| IX06-HUQ | QUIESCING | QUIESCING | same already-reconciling UNSETTLED source, exact candidate mapping, identity preservation, and revocation guard as IX06-HUR | S | continue exact reconciliation | same atomic revocation/fence and byte-identical preservation; create no saga or cleanup; replay/conflict rules are exact | unsettled reconciliation |
| IX06-NR | REQUESTED | REQUESTED | exact source is a member of `PreExposureCancellationSourcesV1`; under generation fence, recheck the complete bound Effect set and prove no dispatch/application; use the exact source-to-safe-target map below; on a revocation trigger candidate is exactly `SHADOW_PASSED\|FROZEN\|EVIDENCE_STALE->REVOKED` | S | stop/quiesce active child | atomically settle the precise Effect set, create-or-bind the deterministic generation/all-target `NoExposureReceipt` once, persist N, create no rollback; IX03 is sole cleanup owner; same bytes replay, conflicting classification rejects | no exposure |
| IX06-NQ | QUIESCING | QUIESCING | same exact `PreExposureCancellationSourcesV1` membership, fence, complete-set proof, source-to-safe-target mapping, and exact revocation candidate mapping as IX06-NR | S | stop/quiesce active child | same atomic settle/create-or-bind/replay rule; no rollback; IX03 sole cleanup owner | no exposure |
| IX06-E2R | REQUESTED | REQUESTED | a bound Effect is exactly `INTENT_RECORDED`; synchronized E02 and generation fence; the complete generation Effect set is locked | S | stop child/send | atomically take E02 to `CANCELLED_BEFORE_SEND`; if this makes the complete set proved non-applied, create-or-bind the one generation/all-target NoExposureReceipt; replay returns identical receipt | pre-send settlement |
| IX06-E2Q | QUIESCING | QUIESCING | same as IX06-E2R at `INTENT_RECORDED` | S | stop child/send | synchronized E02; identical settlement/proof/replay semantics | pre-send settlement |
| IX06-E3R | REQUESTED | REQUESTED | a bound Effect is exactly `READY_TO_SEND`; synchronized E03 and generation fence; the complete generation Effect set is locked | S | stop child/send | atomically take E03 to `CANCELLED_BEFORE_SEND`; if this makes the complete set proved non-applied, create-or-bind the one generation/all-target NoExposureReceipt; replay returns identical receipt | pre-send settlement |
| IX06-E3Q | QUIESCING | QUIESCING | same as IX06-E3R at `READY_TO_SEND` | S | stop child/send | synchronized E03; identical settlement/proof/replay semantics | pre-send settlement |
| IX06-XR | REQUESTED | REQUESTED | protected ExposureReceipt or durable E06 proves application; exact source is `CANARY_RUNNING\|CANARY_PAUSED\|CANARY_PASSED\|CANARY_FAILED\|WIDENING_REVIEW\|WIDENING_EFFECT\|WIDENING_RECONCILING\|PROMOTION_PENDING_APPROVAL\|APPROVED\|PROMOTING\|PROMOTION_RECONCILING\|PROMOTED\|OBSERVING`; synchronized target is `CANARY_ABORTING` for canary/widening/review/approved sources and `FAILED` for promotion-mutation/post-promotion sources, plus rollback `IDLE->REQUESTED` | CANCEL_REQUESTED>ROLLBACK_REQUESTED | stop/classify | atomically record exactly `SHADOW_PASSED\|FROZEN\|EVIDENCE_STALE->REVOKED` when revocation triggered (or preserve REVOKED), fence, and create the unique rollback saga with immutable `WIDENING_ABORT` origin for every canary/widening/review/approved source; expected-version/rollback-IDLE CAS, byte-identical replay, source-set equality, and conflicting origin/classification rejection | exposed |
| IX06-XQ | QUIESCING | QUIESCING | same protected X partition, exact source-set, and exact revocation candidate mapping as IX06-XR, including exposed `CANARY_PASSED`, plus rollback `IDLE->REQUESTED` | QUIESCING>ROLLBACK_REQUESTED | stop/classify | atomically fence and create the unique rollback saga with immutable `WIDENING_ABORT` origin for canary/widening/review/approved sources; exact expected-version CAS and replay/conflict rules; IX03 remains blocked | exposed |
| IXH01-R | REQUESTED | REQUESTED | health exactly `HEALTHY`+member of generated `ReachableCancellationDegradationCoordinatesV1`+exactly one `ACTIVE_GENERATION` or `NO_ACTIVE_GENERATION` receipt partition+continuity/SLO degradation; active requires current-generation continuity, while no-active requires canonical null generation and no live exposure or exposure-capable Effect | REDUCE-V1 | no new wait | atomically set health `TELEMETRY_DEGRADED`, write the deterministic partition/source-bound degradation receipt, fence already-active authority/sends, and preserve exact candidate/rollout/release-attempt/Effect/rollback/cleanup identities and states; no second saga or CleanupManifest | cancellation-side degradation |
| IXH01-Q | QUIESCING | QUIESCING | same health, generated-membership, disjoint `ACTIVE_GENERATION\|NO_ACTIVE_GENERATION` partition, and degradation guard as IXH01-R | REDUCE-V1 | no new wait | same atomic health/receipt/fence transaction and exact preservation; no second saga or CleanupManifest | cancellation-side degradation |
| IXH01-C | CLEANING | CLEANING | health exactly `HEALTHY`+reachable nonterminal IX CLEANING tuple+health event accepted before IX04+exactly one `ACTIVE_GENERATION` or `NO_ACTIVE_GENERATION` partition with the same active/null guard as IXH01-R | REDUCE-V1 | no new wait | same atomic health/receipt/fence transaction; preserve the sole existing CleanupManifest and all attempt/parent cleanup identities and folds | cancellation-side degradation |

`CancellationRevocationCoordinatesV1` is derived from reachable tuples at `work_cancel_state=REQUESTED|QUIESCING` and is exactly equal to the IX06-UR/UQ/HUR/HUQ/NR/NQ/XR/XQ revocation-guard union over candidate sources `SHADOW_PASSED|FROZEN|EVIDENCE_STALE`, partitioned by UNSETTLED-before-reconciliation, UNSETTLED-already-reconciling, N, and X. IX06-HUR/HUQ alone own a revocation whose source rollout is already `WIDENING_RECONCILING|PROMOTION_RECONCILING` and whose original Effect remains UNSETTLED; they preserve the exact Effect, reconciliation, rollback, and cleanup identities and states, keep the existing fence, and create no saga or cleanup. The eight guards are pairwise disjoint by cancellation state, rollout/classifier, revocation trigger, and expected tuple-version CAS. At the IX01 boundary their pre-cancel source projection is exactly equal to IC32's corresponding guards: IC32 wins only while cancellation is NONE, IX06 wins only after IX01, and a stale writer rejects under expected-version CAS. A revocation-triggered IX06 row changes no unlisted candidate coordinate, preserves the exact Effect and any existing rollback identity/origin, creates no duplicate saga or cleanup, and uses the same safe rollout target and branch ownership as its non-revocation IX06 class. Generated witnesses place revocation immediately before and after IX06-U, and immediately before and after protected X/N settlement, for both cancellation states, both reconciliation rollouts, and all three candidate sources; same-event replay returns the original receipt and a conflicting revocation, cancellation epoch, or classifier rejects.

`ReachableCancellationDegradationCoordinatesV1` is the exact generated set of reachable nonterminal tuples with health `HEALTHY` and cancellation `REQUESTED|QUIESCING|CLEANING`. For each cancellation state it is partitioned exactly and pairwise disjointly into `ACTIVE_GENERATION` and `NO_ACTIVE_GENERATION`, and that six-cell partition equals the IXH01-R/Q/C guard union. `ACTIVE_GENERATION` requires the exact current generation identity and continuity binding. `NO_ACTIVE_GENERATION` requires no active generation, live exposure, or exposure-capable Effect and encodes `active_canary_generation` as canonical JSON null; it never invents a generation. `CancellationDegradationReceipt` schema V1 is exact and has fields `{receipt_version="improvement-cancel-degradation-v1", repository_id, parent_work_id, cancellation_epoch, cancellation_control_event_id, generation_partition, active_canary_generation, pre_event_tuple_digest, degradation_event_digest}`. Its identity is `H("improvement-cancel-degradation-v1",repository_id,parent_work_id,cancellation_epoch,cancellation_control_event_id,generation_partition,canonical_nullable(active_canary_generation),pre_event_tuple_digest,degradation_event_digest)`, where `canonical_nullable(null)` is the single encoded no-generation value and non-null is legal only for `ACTIVE_GENERATION`. These fields are constructible from the locked work/repository aggregate, persisted cancellation request/control event, and accepted degradation event. No candidate, rollout, Effect, rollback, release-attempt, cleanup, identity, or ownership delta is permitted beyond the named health change, durable receipt, and already-active fence. Absent-or-same receipt CAS creates it once; identical schema bytes replay the same receipt, while a different nullable generation, partition, work/repository identity, cancellation epoch/control event, event digest, pre-event tuple digest, or tuple version rejects. `CANCELLED` and every other terminal coordinate are immutable and absent from the source set. Generated witnesses include inactive/no-exposure sources where IX01 wins immediately before ordinary IH01, for each `REQUESTED|QUIESCING|CLEANING` continuation, as well as active-generation sources; IX01/IX02 immediately before or after degradation or exact Effect settlement race under one tuple-version CAS and rederive exactly one IXH/IX06 continuation.

`ExposedCancellationSourcesV1` is derived from the generated reachable tuples with a protected ExposureReceipt or durable E06 and is exactly equal to the IX06-XR/XQ source union. It includes exposed `CANARY_PASSED`; that coordinate maps atomically to `CANARY_ABORTING`, stops/fences the live exposure, takes rollback `IDLE->REQUESTED`, and records immutable origin `WIDENING_ABORT`. Generated witnesses race IX01 immediately before and after IR08 and IR14; ordinary IR14 rejects after IX01, and whichever expected-version/source transition loses must replay or reject without changing the protected source set.

`PreExposureCancellationSourcesV1` is exactly `{DISABLED,ENABLEMENT_REVIEW,CANARY_PENDING_APPROVAL,CANARY_READY,CANARY_RUNNING,CANARY_PAUSED,CANARY_PASSED,CANARY_FAILED,WIDENING_REVIEW,WIDENING_EFFECT,WIDENING_RECONCILING,PROMOTION_PENDING_APPROVAL,APPROVED,PROMOTING,PROMOTION_RECONCILING}` intersected with the generated reachable tuples having protected N facts; generated validation requires set equality, not subset inclusion. Its safe-target map keeps `DISABLED|ENABLEMENT_REVIEW|CANARY_PENDING_APPROVAL` at the same rollout state, maps an unstarted `CANARY_READY` active child and canary/widening sources to `CANARY_ABORTING`, and maps promotion sources to `FAILED`; every mapping stutters the cancellation coordinate. `CANARY_READY` requires no WorkerStarted. `WIDENING_REVIEW`, `PROMOTION_PENDING_APPROVAL`, and `APPROVED` require the complete all-target no-application/no-send proof. A possible exposure selects IX06-XR/XQ; a live/unsettled effect selects IX06-UR/UQ. `NoExposureReceipt.id = H("improvement-no-exposure-v1",parent_work_id,active_canary_generation,effect_id_set_digest,target_set_digest)`; absent-or-same CAS makes creation once-only and conflicts with any ExposureReceipt.

When IX01 occurs while rollback is active, reducer priority 2 keeps the safety rollback visible but cancellation still blocks all non-safety projections; after rollback settles, the same persisted cancellation coordinate becomes `CANCEL_REQUESTED`/`QUIESCING` without accepting another request. No reachable nonterminal product tuple lacks IX01 eligibility.

### 15.6 Control-health machine v1

Initial: `HEALTHY`. `CONTROL_FAILED` is a disposition, not work terminal. `CURRENT_CONTINUITY` is exact: either no degradation event exists for the current `active_canary_generation`, or a completed IH03 receipt newer than the latest degradation is bound to that generation, current bounds, telemetry epoch, and decisions. A degradation before a generation is admitted does not taint that later generation. No other receipt satisfies this predicate.
| ID | Source | Target | Guard / trigger | Canonical projection | Wait/retry | Effects/cleanup | Disposition |
|---|---|---|---|---|---|---|---|
| IH01 | HEALTHY | TELEMETRY_DEGRADED | continuity/SLO proof fails and the exact reachable tuple is outside `ReachableActiveExposureInterruptCoordinatesV1` and has no active generation, live exposure, or exposure-capable Effect | BLOCKED | none | durably record degradation; stop admission | - |
| IH01-RX | HEALTHY | TELEMETRY_DEGRADED | exact tuple is in `ReachableActiveExposureInterruptCoordinatesV1` but not an existing specialized IH01-C/W/WR/WV/A/P/PR/PV/D/O coordinate; `work_cancel_state=NONE`; protected X classifier; includes exposed `CANARY_PASSED`, exposure-bearing `WIDENING_REVIEW`, exposed `PROMOTION_PENDING_APPROVAL`, exposed pre-rollback `CANARY_FAILED`, and every generated omission; synchronized rollout uses `SafeDegradationTargetV1` and rollback `IDLE->REQUESTED` | BLOCKED>ROLLBACK_REQUESTED | none | atomically record degradation, revoke/fence all authority and sends, stop exposure, and create-or-reuse exactly one rollback with the source-bound immutable origin; version CAS/replay/conflict rules apply | rollback |
| IH01-RN | HEALTHY | TELEMETRY_DEGRADED | same derived residual coordinate set as IH01-RX+`work_cancel_state=NONE`+protected generation/all-target no-exposure proof; synchronized rollout uses `SafeDegradationTargetV1`; rollback remains `IDLE` | BLOCKED | abort settlement | atomically record degradation, revoke/fence all authority and sends, stop/quiesce child, persist N, and create no rollback; protected proof conflicts with any ExposureReceipt | no exposure |
| IH01-RAQ | HEALTHY | TELEMETRY_DEGRADED | exact tuple is in generated `RollbackAdoptionInterruptCoordinatesV1`+`work_cancel_state=NONE`+protected X+matching rollback is `REQUESTED`; rollout, Effect, rollback identity/state, and immutable origin remain exact | S under rollback dominance | none | atomically record degradation and fence all authority/sends; preserve exact rollout target and existing saga; create no second saga or cleanup | adopt requested rollback |
| IH01-RAR | HEALTHY | TELEMETRY_DEGRADED | same exact generated adoption relation+`work_cancel_state=NONE`+protected X+matching rollback is `ROLLING_BACK`; preserve exact rollout/Effect/rollback/origin | S under rollback dominance | none | record degradation, fence authority, preserve the running saga; no dispatch, second saga, or cleanup | adopt rolling rollback |
| IH01-RAV | HEALTHY | TELEMETRY_DEGRADED | same exact generated adoption relation+`work_cancel_state=NONE`+protected X+matching rollback is `VERIFYING`; preserve exact rollout/Effect/rollback/origin | S under rollback dominance | none | record degradation and fence authority; preserve verification and saga; no second saga or cleanup | adopt verifying rollback |
| IH01-RAD | HEALTHY | TELEMETRY_DEGRADED | same exact generated adoption relation+`work_cancel_state=NONE`+protected X+matching rollback is `VERIFIED`; preserve exact rollout/Effect/rollback/origin | S under rollback dominance | none | record degradation and fence authority; preserve verified saga; no second saga or cleanup | adopt verified rollback |
| IH01-RAF | HEALTHY | TELEMETRY_DEGRADED | same exact generated adoption relation+`work_cancel_state=NONE`+protected X+matching rollback is `FAILED`; preserve exact rollout/Effect/rollback/origin | S under rollback dominance | bounded rollback handling | record degradation and fence authority; preserve failed saga/remediation eligibility; no second saga or cleanup | adopt failed rollback |
| IH01-RAM | HEALTHY | TELEMETRY_DEGRADED | same exact generated adoption relation+`work_cancel_state=NONE`+protected X+matching rollback is `REMEDIATION_WAIT`; preserve exact rollout/Effect/rollback/origin | S under rollback dominance | existing remediation wait | record degradation and fence authority; preserve exact remediation-bound saga and blocks; no second saga or cleanup | adopt remediation-wait rollback |
| IH01-RAO | HEALTHY | TELEMETRY_DEGRADED | same exact generated adoption relation+`work_cancel_state=NONE`+protected X+matching rollback is `ROLLED_BACK` while the work tuple remains nonterminal and active/exposure-derived; preserve exact rollout/Effect/rollback/origin | S under rollback/cleanup dominance | none | record degradation and fence residual authority; preserve settled saga and named cleanup owner; create no second saga or cleanup | adopt settled rollback |
| IH01-C | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+exact synchronized rollout `CANARY_RUNNING->CANARY_PAUSED`; synchronized degradation for active canary | BLOCKED | W(continuity) | atomically record degradation, revoke progress authority, and stop every exposure/effect send | safe pause |
| IH01-W | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+exact synchronized rollout `WIDENING_EFFECT->WIDENING_RECONCILING`; original Effect is unsettled or exposure classification is not protected | BLOCKED | reconcile exact original Effect | atomically record degradation, revoke/fence every send and widening authority; preserve the original Effect coordinate; no rollback may start | safe reconciliation |
| IH01-A | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+exact synchronized rollout `APPROVED->CANARY_PASSED`; synchronized degradation before promotion send | BLOCKED | W(new promotion decision) | atomically record degradation, revoke decision/grant; protected no-send fact | safe review |
| IH01-P | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+exact synchronized rollout `PROMOTING->PROMOTION_RECONCILING`; original Effect is unsettled or exposure classification is not protected | BLOCKED | reconcile exact original Effect | atomically record degradation, revoke/fence every send and promotion authority; preserve the original Effect coordinate; no rollback may start | safe reconciliation |
| IH01-WR | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+candidate `EVIDENCE_STALE\|REVOKED`+exact rollout already `WIDENING_RECONCILING` after IC24-A or IC32-UW (including an IC32-HU-preserved coordinate)+the exact original Effect remains `UNSETTLED`+rollback remains `IDLE`; rollout, Effect identity/state, and reconciliation record are byte-identical | S (`BLOCKED` remains `BLOCKED`) | continue exact original Effect reconciliation | atomically record degradation and revoke/fence every remaining grant, authority, and send; preserve exact original Effect identity and reconciliation rollout; stop/quiesce the child; create no rollback or cleanup before protected X/N settlement | unsettled already-reconciling widening interrupt |
| IH01-PR | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+candidate `EVIDENCE_STALE\|REVOKED`+exact rollout already `PROMOTION_RECONCILING` after IC24-A or IC32-UP (including an IC32-HU-preserved coordinate)+the exact original Effect remains `UNSETTLED`+rollback remains `IDLE`; rollout, Effect identity/state, and reconciliation record are byte-identical | S (`BLOCKED` remains `BLOCKED`) | continue exact original Effect reconciliation | atomically record degradation and revoke/fence every remaining grant, authority, and send; preserve exact original Effect identity and reconciliation rollout; stop/quiesce the child; create no rollback or cleanup before protected X/N settlement | unsettled already-reconciling promotion interrupt |
| IH01-WV | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+exact post-E06/pre-IR38 interval: rollout `WIDENING_EFFECT->CANARY_ABORTING`, direct E06 verified widening application receipt is durable and protected, and rollback `IDLE->REQUESTED` | REVIEW>ROLLBACK_REQUESTED | none | atomically record degradation, revoke/fence authority, stop exposure, and create one `WIDENING_ABORT` rollback saga; no N classification may conflict with E06 | rollback |
| IH01-PV | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+exact post-E06/pre-IR18 interval: rollout `PROMOTING->FAILED`, direct E06 verified promotion application receipt is durable and protected, and rollback `IDLE->REQUESTED` | MERGE_QUEUED>ROLLBACK_REQUESTED | none | atomically record degradation, revoke/fence authority, stop exposure, and create one promotion rollback saga; no N classification may conflict with E06 | rollback |
| IH01-D | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+exact synchronized rollout `PROMOTED->FAILED` and rollback `IDLE->REQUESTED`; synchronized degradation after verified promotion | ROLLBACK_REQUESTED | none | atomically record degradation and create the single rollback saga | rollback |
| IH01-O | HEALTHY | TELEMETRY_DEGRADED | `work_cancel_state=NONE`+exact synchronized rollout `OBSERVING->FAILED` and rollback `IDLE->REQUESTED`; synchronized degradation during observation | ROLLBACK_REQUESTED | none | atomically record degradation and create the single rollback saga | rollback |
| IH02 | TELEMETRY_DEGRADED | CONTROL_PAUSED | pause receipt and no active rollout/effect remains hidden behind canonical BLOCKED | BLOCKED | W(continuity) | stop exposure | - |
| IH03 | CONTROL_PAUSED | HEALTHY | continuity proof+fresh decisions bound after latest degradation to current generation/bounds | REDUCE-V1 | resume saved canonical | none | establishes CURRENT_CONTINUITY |
| IH04 | CONTROL_PAUSED | CONTROL_FAILED | expiry/stop/exhausted | BLOCKED | wait closes | abort/rollback | failed control |
| IH05 | TELEMETRY_DEGRADED | HEALTHY | protected NoExposureReceipt+no active canary generation, rollout exposure, live Effect, promotion authority, or pending receipt; continuity restored before pause | REDUCE-V1 | invalidate old decisions; require newly admitted generation | no exposure to resume; records closed no-exposure episode | restoration only for no-exposure case |
| IH06-WX | TELEMETRY_DEGRADED | CONTROL_PAUSED | `work_cancel_state=NONE`+rollout `WIDENING_RECONCILING`+exact original Effect terminal/reconciled+current protected `ExposureReceipt`+rollback `IDLE->REQUESTED`; synchronized rollout -> `CANARY_ABORTING` | BLOCKED>ROLLBACK_REQUESTED | none | atomically classify exposure and create one `WIDENING_ABORT` rollback saga | exposed after settlement |
| IH06-WN | TELEMETRY_DEGRADED | CONTROL_PAUSED | `work_cancel_state=NONE`+rollout `WIDENING_RECONCILING`+all bound effects settled with protected proved non-application; synchronized rollout -> `CANARY_ABORTING` | BLOCKED | none | persist no-exposure abort classifier; no rollback; IR12/IR13B then IR13C-N or IX03 | no exposure after settlement |
| IH06-PX | TELEMETRY_DEGRADED | CONTROL_PAUSED | `work_cancel_state=NONE`+rollout `PROMOTION_RECONCILING`+exact original Effect terminal/reconciled+current protected `ExposureReceipt`+rollback `IDLE->REQUESTED`; synchronized rollout -> `FAILED` | BLOCKED>ROLLBACK_REQUESTED | none | atomically classify exposure and create one bound promotion rollback saga | exposed after settlement |
| IH06-PN | TELEMETRY_DEGRADED | CONTROL_PAUSED | `work_cancel_state=NONE`+rollout `PROMOTION_RECONCILING`+all bound effects settled with protected proved non-application; synchronized rollout -> `FAILED` and cleanup `NOT_REQUIRED->PENDING` | BLOCKED>CLEANING | none | no rollback; create CleanupManifest once | no exposure after settlement |

### 15.7 Improvement synchronized checks

Every candidate, rollout, release-attempt, control, cancellation, effect, rollback, and cleanup edge is applied as one tuple transaction. IA01–IA05 occur as separate normal transactions. Exact order is IC03, IC06, IA01, IA02, IA03, IA04, IC07, IC08, IC11, IC12, IA05, IC13: IA01 and IA05 are `S`; IC06 supplies `READY_REVIEW>READY`; IC13 consumes the already-durable IA05 receipt and supplies `VERIFYING>REVIEW`. IC07 consumes the already-durable IA04 receipt. IR04 derives `canary_child_id=H("canary-child-v2",parent_work_id,stage,canary_generation,CanaryAdmissionDecision_digest)` and `composition_link_id=H("canary-link-v2",parent_work_id,stage,canary_generation,CanaryAdmissionDecision_digest)`, then creates exactly one active pair at child canonical `INBOX` in a single absent-or-same CAS. Same bytes replay; any different identity, payload, or key rejects. Replacement follows the canary-generation invariant above. IR27–IR35 accept only the current active generation and exact two IDs; delayed historical-generation events are fenced. IR15–IR18 are the only normal parent promotion path; IR54/IR55/IR57 are its pre-MERGED reconciliation branches; IR36–IR43 are the only widening path. A component final state cannot mask earlier safety priorities. The static check enumerates the reachable product, rejects every other combination, and asserts exactly one disjoint reducer predicate and legal projection per row. No row atomically claims worker start, output, oracle, review, external effect, telemetry, and cleanup.


**Improvement final-cleanup ownership.** Generic CleanupItem rows may advance an item and update a nonfinal cleanup fold. They must not claim canonical `S` when that same event changes the improvement parent reducer to a terminal. The following synchronized rows are the only owners of the final item/fold and parent terminalization. IX04 remains the separate cancellation owner.

| ID | Parent source | Parent target | Atomic component event and exact guard | Canonical projection | Ownership |
|---|---|---|---|---|---|
| ICL01 | CLEANING | DONE | final required item takes C02 or C12; atomically fold cleanup `RUNNING/PENDING->CLEANED`; exact success conjunction, settled effects/rollback, no live authority | CLEANING>DONE | sole ordinary-success last-cleanup owner |
| ICL02 | CLEANING | FAILED | final required item takes C02 or C12; atomically fold to `CLEANED`; exact failure conjunction, settled effects/rollback, no live authority | CLEANING>FAILED | sole ordinary-failure last-cleanup owner |
| ICL03 | CLEANING | FAILED | final required eligible retained-risk item takes C09 to `ESCALATED_DISPOSITION`; all other items CLEANED; §13 eligibility and no forbidden resource class; create/bind remediation obligation as required | CLEANING>FAILED | sole eligible-escalation final-fold owner; resource stays blocked |

C02, C09, and C12 reject as generic `S` when they are the last improvement item and one of ICL01–ICL03 applies. ICL01–ICL03 consume the item transition and fold atomically, so no second owner can race. A last item under whole-work cancellation uses IX04, not this table.

**Control-health reachability invariant.** `ReachableActiveExposureInterruptCoordinatesV1` is derived from the complete reachable tuple relation, not a handwritten rollout-state list. It contains every tuple with an active generation, exposure, or exposure-capable Effect, including `CANARY_RUNNING`, exposed `CANARY_PASSED`, exposed pre-rollback `CANARY_FAILED`, exposure-bearing `WIDENING_REVIEW`, `WIDENING_EFFECT`, exposed `PROMOTION_PENDING_APPROVAL`, `APPROVED`, `PROMOTING`, `PROMOTED`, `OBSERVING`, and every actual generated coordinate omitted from that readable list. Its source set must equal exactly the union of IH01-C/W/WR/WV/A/P/PR/PV/D/O plus residual IH01-RX/RN and rollback-adoption IH01-RAQ/RAR/RAV/RAD/RAF/RAM/RAO guards; pairwise intersections are empty, literal equality fails on any omitted or extra guard, and every member has exactly one interrupt after its protected X/N or unsettled classifier is fixed. The derived source set includes every HEALTHY already-reconciling `EVIDENCE_STALE|REVOKED` tuple whose exact original Effect is still UNSETTLED. Generic IH01 is legal only outside this relation and only for truly inactive/no-exposure tuples. `RollbackAdoptionInterruptCoordinatesV1` is generated from that same reachable relation and is exactly every HEALTHY, `work_cancel_state=NONE`, protected-X, nonterminal active/exposure tuple whose matching immutable-origin saga is already `REQUESTED|ROLLING_BACK|VERIFYING|VERIFIED|FAILED|REMEDIATION_WAIT|ROLLED_BACK`. Its exact rollback-state partition is IH01-RAQ/RAR/RAV/RAD/RAF/RAM/RAO. Each row changes only health, preserves the byte-identical Effect, rollout target, rollback identity/state, origin, remediation/block coordinate, and selected later cleanup owner, fences all remaining authority/sends, creates no second saga or cleanup, and is an exact canonical stutter under rollback or cleanup dominance. No member may fall through IH01-RX or generic IH01.

Every X interrupt atomically records degradation, revokes/fences grants and sends, stops exposure, and creates or reuses exactly one rollback. Every N interrupt requires a protected generation/all-target no-exposure proof and creates none. `SafeDegradationTargetV1` maps residual `CANARY_PASSED|CANARY_FAILED|WIDENING_REVIEW|PROMOTION_PENDING_APPROVAL` coordinates to `CANARY_ABORTING`; any further generated coordinate must declare one exact stop/abort/failure target before admission. Existing IH01-W/P enter reconciliation, and IH01-WR/PR atomically record degradation after IC24-A or IC32-UW/UP has already entered reconciliation; all four preserve exact unsettled Effect identity and create no rollback. After IH01-WR/PR, only the matching IH06-WX/WN/PX/PN may consume later protected X/N settlement while `work_cancel_state=NONE`. Without that health interrupt, the only already-reconciling settlement continuations are the candidate-specific IC24-RWX/RPX/RN or IC32-RWX/RPX/RN/HWX/HPX/HN rows; no ordinary progress, inferred rollback, or unrelated revoke is required. Existing IH01-WV/PV cover the complete post-E06/pre-continuation interval and forbid N. No rollback dispatch races an original Effect in `SENDING`, `UNKNOWN`, or any live/unsettled state.

Every ordinary edge adjacent to entry into or exit from the derived set races the interrupt under one tuple-version CAS. The winner fixes the new derived coordinate; the loser must rederive and select exactly one applicable interrupt or reject. After stale health/continuity, every ordinary progress/exposure row rejects until the named restoration contract applies. IH05 remains limited to protected no-exposure/no-active-generation tuples and invalidates old decisions. Projection masking as `BLOCKED` is not authorization.

### 15.8 Exact tuple witnesses required by the plan checker

The ephemeral plan checker instantiates omitted coordinates at their declared initial/settled values and verifies these named deltas without inventing fields:

- **IA01/IA05.** `(CURATION_PASSED, DISABLED, IDLE, HEALTHY, NONE, EMPTY, NOT_REQUIRED, IDLE, READY_REVIEW)` --IC06--> `(OFFLINE_PENDING,...,IDLE,...,READY)` --IA01--> `(OFFLINE_PENDING,...,READY,...,READY)` (`S`). Later `(SHADOW_RUNNING,DISABLED,VERIFYING,HEALTHY,NONE,EMPTY,NOT_REQUIRED,IDLE,VERIFYING)` --IA05--> the same tuple except `SUCCEEDED`, still `VERIFYING` (`S`) --IC13--> `candidate_state=SHADOW_PASSED`, canonical `REVIEW`.
- **BUILD/MAINTENANCE rollback remediation.** Execute B35→B37+RO00-B and M26→M28+RO00-M for exhaustion and assert one atomic Work/obligation/link/MAINTENANCE-child/event/receipt CAS, deterministic generation, exact absent-or-same replay, conflicting-byte rejection, the distinct private `ROLLBACK_REMEDIATION_WAIT`, OPEN obligation, retained exposure/resource blocks, no CleanupItem/C11, and rejection of B25/B26/B57/M21/M46. For each factory, race obligation revocation before/after RO07/RO08/RO09; exercise RO14 retry and purpose-specific RO09 closure. For rollback-safety, prove RO09 and B74/M62 release no block, B34/M25 independently verify, and only B38/M29 seal `ROLLED_BACK` and atomically remove the exact blocks. Race a first authenticated cancellation immediately before and after B38/M29: B71/M59 atomically persist the absent disposition after settlement, B71-P/M59-P adopt one persisted during rollback, B71-R/M59-R alone replay the identical persisted request, and B39/M30 race them under one expected-version/disposition CAS. Assert pairwise exclusion, byte-identical replay, and conflict rejection. Execute cancellation during remediation through B75/M63, RO09, verification, `ROLLED_BACK`, cancellation cleanup, and `CANCELLED`. Also execute a permanently unresolved B77/M65 trace; it cannot become CLEANING, CANCELLED, ordinary READY/PLANNING, or release a resource.
- **Rollback and cancellation interleavings.** For each cancellation coordinate `NONE`, `REQUESTED`, and `QUIESCING`, execute IRB04→IRB06 (`FAILED->REMEDIATION_WAIT`, exactly `BLOCKED`), unresolved RO06, RO09→IRB09 (`REMEDIATION_WAIT->VERIFYING`), real IRB03, and the applicable IRB07-N/R/Q. For an RO00-I generation, assert RO09 retains every exact block and the selected IRB07 branch alone checks the closure/restoration/independent-verification receipts and purpose/generation/key-set digest, atomically releases only that set with `ROLLED_BACK`, and emits the absent-or-same BlockReleaseReceipt; race cancellation, replay, and conflicting bytes around this transaction. Under NONE, IRB08 alone schedules cleanup for `rollback_origin!=WIDENING_ABORT`; a `WIDENING_ABORT` saga remains `ROLLED_BACK` through IR12/IR13A and uses IR13C-X alone. Under REQUESTED/QUIESCING, IX03 alone schedules cleanup and IX04 alone reaches `CANCELLED`. Assert the Cartesian ownership partition over `{WIDENING_ABORT,non-WIDENING_ABORT} × {NONE,REQUESTED,QUIESCING}` is complete and pairwise disjoint, and reject IRB08 for widening-abort or IR13C-X/N for non-widening origin. Also enumerate IX01/IX02 at `REQUESTED|ROLLING_BACK|VERIFYING|VERIFIED|FAILED|REMEDIATION_WAIT`. While the obligation is OPEN/IN_PROGRESS/VERIFYING/REVOKED, IX03 and every clean/terminal row reject. Prove the six-value priority-2 and priority-7 input/result lists are positionally exact and no waiver or false ROLLED_BACK/clean receipt is accepted. Race IX01 first against canary abort, IH01 degradation, IC32 revocation, and Effect response, then race each of those safety events first. Exercise IX06-UR/UQ, IX06-HUR/HUQ, IX06-NR/NQ, and IX06-XR/XQ for `REQUESTED` and `QUIESCING`, including candidate `REVOKED` and exposed `CANARY_PASSED`. Race IX01 immediately before and after IR08 and IR14, require the `CANARY_PASSED->CANARY_ABORTING` X target, stopped/fenced exposure, rollback `IDLE->REQUESTED`, immutable `WIDENING_ABORT` origin, and exact `ExposedCancellationSourcesV1` equality. Assert IX03 with rollback IDLE accepts only a protected NoExposureReceipt covering every bound target Effect/no prior application; any exposure or reversible application requires exactly ROLLED_BACK. Assert one and only one cleanup owner. Derive the exact `PreExposureCancellationSourcesV1` equality and execute IX01 before E02 and before E03, IX01 at each listed source including initial DISABLED, both approval waits, unstarted active-child CANARY_READY, WIDENING_REVIEW, and no-send APPROVED, plus child terminal before/after IX01; IX06-E2R/E2Q/E3R/E3Q must settle the precise Effect set and IX06-NR/NQ must mint the once-only generation/all-target NoExposureReceipt before IX03.

- **Widening ambiguity.** `(rollout=WIDENING_EFFECT,effect=LIVE,canonical=REVIEW)` --IR42+E11--> `(WIDENING_EFFECT,UNRESOLVED,QUARANTINED)`. Direct E06 uses IR38; reconstructed E17 uses IR56; both atomically resume `CANARY_RUNNING`. E34 uses IR43. Every other settled result uses exactly one IW row under the protected exposure partition and never becomes success.
- **Canary abort classification.** Enumerate IR07-X/N, IR09-X/N then IR11-X/N, IR10-X/N, IR53-X/N, IR34/IR35 (protected N), and IH01-C followed by restored IR06 or a later abort. Each reachable abort source has exactly one protected exposed/no-exposure row. X atomically creates rollback exactly once; N persists the classifier and creates none. IR34/IR35 atomically bind the generation-wide NoExposureReceipt and must reject a raced possible exposure in favor of X rollback. After IR12, X can use only IR13A after rollback_state exactly ROLLED_BACK through IRB07 and N can use only IR13B after all bound effects settle with proved non-application, including the existing terminal E34 record from IR43. Under cancellation NONE only IR13C-X schedules after IR13A, and only IR13C-N schedules after IR13B; under REQUESTED/QUIESCING only IX03 does. Exercise exact X and N witnesses through IR13A/IR13B, exposed `ROLLED_BACK>CLEANING` by IR13C-X or no-exposure `REVIEW>CLEANING` by IR13C-N, or IX03, final cleanup, and reject crossed classifiers.
- **Release-attempt failure.** For each exact candidate phase `OFFLINE_PENDING|OFFLINE_RUNNING|OFFLINE_PASSED|SHADOW_PENDING|SHADOW_RUNNING`, execute both the reachable `EXECUTING` IA08-* and `VERIFYING` IA07-* failure tuple, assert atomic projection to `OFFLINE_FAILED|SHADOW_FAILED` plus `FAILURE_PENDING_CLEANUP`, then IA16, all cleanup receipts, and IA17 to immutable release `FAILED` and canonical `FAILED`. Assert no release `FAILED` remains unmapped. Separately race IX01 immediately before and after IA16 and immediately before IA17. In the cancellation-winning traces, require IX05 adoption of the already-canonical CLEANING parent, IA18-F when the attempt is still `FAILURE_PENDING_CLEANUP`, IA18-C from either failure-origin CLEANING path, byte-identical preservation of the one IA07/IA08 CleanupManifest, no duplicate attempt or parent cleanup owner, exact IX-dominant reducer stutters, and eventual IX04 only after both attempt-local clean receipts and the full parent cleanup guard pass. The IA16/IA17 loser rejects by tuple-version CAS; identical IA18 replay returns existing receipts and conflicting origin/receipt bytes reject.
- **Remediation revocation races.** Race each C11 revocation with RO07, RO08, RO09, RO10, and RO14 under version CAS. Exactly RO01-R/RO02-R or RO11/RO12/RO13 atomically records revocation and reaches `REVOKED` with grants fenced, child quiescent, and effects settled/reconciled. Same-event replay after the status change returns the original receipt; a later distinct signal uses RO06. No work occurs before a distinct RO14 reauthorization.
- **Candidate revocation and stale evidence.** Derive `ActualReachableRevocationCoordinatesV1` and require exact equality with the IC32 guard union over candidate sources `SHADOW_PASSED|FROZEN|EVIDENCE_STALE`; enumerate every actually reachable rollout coordinate including cleanup-active `FAILED|RETIRED`, every rollback value, and protected X/N/UNSETTLED Effect class. Race IC30 then revocation and IC24 then revocation. At the IX01 boundary enumerate `SHADOW_PASSED|FROZEN|EVIDENCE_STALE` across protected X/N, UNSETTLED before reconciliation, and UNSETTLED already in `WIDENING_RECONCILING|PROMOTION_RECONCILING` for REQUESTED and QUIESCING; require exact `CancellationRevocationCoordinatesV1` equality with IX06-UR/UQ/HUR/HUQ/NR/NQ/XR/XQ, pairwise exclusion from IC32 and between pre-reconcile/already-reconciling/X/N branches by cancellation state, rollout/classifier, revocation trigger, and tuple-version CAS, the exact candidate delta to REVOKED and no unlisted candidate delta, preserved Effect/reconciliation/rollback/cleanup identity and origin, and no duplicate saga or cleanup. Race revocation immediately before and after IX06-U and immediately before and after settlement. Apply IC24-A to digest changes during canary, widening, promotion, and observation; it must fence before any grant/send and use exactly the same partition, with no impossible tuple. For widening and promotion, race the digest change before Effect settlement and then execute both exact EVIDENCE_STALE outcomes: IC24-RWX atomically takes `WIDENING_RECONCILING->CANARY_ABORTING` plus rollback `IDLE->REQUESTED` with immutable `WIDENING_ABORT` origin; IC24-RPX atomically takes `PROMOTION_RECONCILING->FAILED` plus rollback `IDLE->REQUESTED` with immutable `CANDIDATE_REVOCATION` origin; both preserve exact Effect identity, yield the declared `BLOCKED>ROLLBACK_REQUESTED` sequence, and admit IRB01 without unrelated revocation. IC24-RN preserves identity, proves N, and creates the sole CleanupManifest without any unrelated revocation. Race degradation before and after IC24-A and IC32-UW/UP and before and after settlement; the already-reconciling unsettled interval must select exactly IH01-WR/PR, and a settlement-first ordering must select exactly the applicable IC24/IC32 X/N continuation before any later derived health interrupt. IC32-CA must preserve the existing CleanupManifest and rollback/origin bytes, create no duplicate cleanup/rollback owner, and stutter/reduce exactly; require before/after reachable fixed-point equality. Assert one rollback at most and later cleanup only through IR13C-X/N, IRB08, or IX03.

- **Research.** No publication: D19 checks the protected disposition and `NoPublicationReceipt`, uses CW-N1 `REVIEW>OBSERVING`, and D19C1 later checks `outcome-recorded` for CW18 `OBSERVING>CLEANING`. Direct verified application: D19P1 checks review-pass/publication authority for CW11 `REVIEW>MERGE_QUEUED`; D19P2 dispatches and stutters; D19P3 checks the bound verified publication effect/remote identity for CW14 `MERGE_QUEUED>MERGED`, then separately checks its explicit protected purpose-bound `NoDeploymentReceipt` for CW16 `MERGED>OBSERVING`; D19C2 schedules cleanup only in a later transaction. Reconciled verified application: D19P4 records UNKNOWN through CW-B44 then CW-X3; D19P6 checks ORIGINAL reconciliation and exact saved publication continuation for CW-Q3 `QUARANTINED>MERGE_QUEUED`, checks the reconstructed verified publication effect/remote identity for CW14, then checks the explicit protected purpose-bound `NoDeploymentReceipt` for CW16; D19C2 is again later. Proven no application/no retry: D19P5 checks the signed `NoApplicationReceipt`, retry-forbidden/exhausted predicate, and publication failure-wait guard, takes only CW-B44 `MERGE_QUEUED>BLOCKED`, and persists both exact saved publication continuation and final disposition; later D19P7 rechecks that durable final disposition for CW-X2 `BLOCKED>CLEANING`. No witness uses CW12 or combines cleanup with the outcome transaction.
- **Promotion.** IR15 reaches `MERGE_QUEUED`; IR17 dispatches and stutters. Direct E06 uses IR18 and reconstructed E17 uses IR57; only those mutually exclusive verified-application rows cross `MERGED`. E34 uses IR55. Every other settled result uses exactly one IP row: exposure starts rollback without claiming MERGED; protected no-exposure enters failure cleanup.

- **Canary replacement races.** For every IR24/IR03/IR04 ordering, require prior active pair terminal, quiescent, effects/rollback settled and clean before archive/new generation. Replay within a generation is absent-or-same. A delayed old `WorkerStarted` or terminal receipt is fenced and cannot mutate the new active generation.
- **Widening success partition.** Direct E06 enables only IR38; reconstructed E17 enables only IR56. Both bind identical decision/bounds/generation/effect/remote identity and resume `CANARY_RUNNING`; neither can satisfy the other's guard.
- **Terminal Effect products.** Require exact equality with the declared reachable edge/classification relation, not a Cartesian expansion. In both `WIDENING_EFFECT` and `PROMOTING`, disposition edges `{E20,E21,E24,E25,E28,E29,E37,E39}` have X and N rows, while target-effect-specific no-application edges `{E09,E10,E30,E31,E33,E35}` have N rows only. Assert that each direct edge has its signed no-send/`NoApplicationReceipt`, its impossible X row is absent, a conflicting same-target ExposureReceipt rejects, and missing proof enters UNKNOWN/reconciliation. Exposure atomically creates the one rollback saga before later single-owner cleanup: widening-abort uses branch-exact IR13C-X/N under NONE or IX03 under cancellation, while promotion uses IRB08 under NONE or IX03 under cancellation. No-exposure schedules cleanup without rollback. No fallback to REVIEW/MERGE_QUEUED exists. Only E06/IR38 or IR18 and E17/IR56 or IR57 can widen bounds or cross MERGED.
- **Release-attempt cancellation subaggregate.** For each IA09-IA12 source, prove rejection while `work_cancel_state=NONE`, then run IX01 before the matching IA row and assert the attempt-only transition is `S` while parent cancellation remains IX-derived. Advance IA13/IA14/IA15 only under their matching IX context; assert IA14 creates only attempt-local cleanup, IA15 creates no parent-terminal edge, and release-attempt `CANCEL_REQUESTED|QUIESCING|CLEANING|CANCELLED` reduces through priority 13 to `SAVED`. Hold IX03 until its full safety guard and require IX04 as the sole canonical `CANCELLED` edge. Include a witness with release attempt `CANCELLED`, work cancellation `QUIESCING|CLEANING`, and incomplete parent cleanup; it remains nonterminal and cannot derive parent `CANCELLED`.
- **IH/IX settlement race.** From each tuple produced by IH01-WR/PR, race degradation, protected X and N settlement immediately before and after IX01 and IX02. For each reachable HEALTHY cancellation coordinate `REQUESTED|QUIESCING|CLEANING`, require exactly IXH01-R/Q/C and the explicit pairwise-disjoint `ACTIVE_GENERATION|NO_ACTIVE_GENERATION` partition, exact `ReachableCancellationDegradationCoordinatesV1` source equality for both partitions, deterministic exact-schema nullable-generation receipt bytes bound to repository/work, cancellation epoch/control event, tuple, and degradation event, preserved IX Effect/rollout/rollback/cleanup identities and ownership, an already-active fence, no fake generation, no second saga or CleanupManifest, and terminal immutability. For each cancellation state include an inactive/no-exposure witness where IX01 wins immediately before ordinary IH01. Race IX01/IX02 before and after the IXH transaction and exact Effect settlement under one tuple-version CAS. With cancellation NONE, exactly IH06-WX/WN/PX/PN applies. Once IX wins, every IH06 row rejects and exactly the matching IX06-XR/XQ or IX06-NR/NQ applies; only IX03 may schedule parent cleanup. Assert pairwise-disjoint guards, one saga for X, no saga for N, byte-identical replay, and no ordinary continuation.
- **Control health and effect-first ordering.** From pristine generation history, prove `CURRENT_CONTINUITY` vacuously permits progress. Derive `ReachableActiveExposureInterruptCoordinatesV1` from reachable tuples and require exact equality with IH01-C/W/WR/WV/A/P/PR/PV/D/O plus residual IH01-RX/RN and rollback-adoption IH01-RAQ/RAR/RAV/RAD/RAF/RAM/RAO. Exercise X and N for exposed/potentially exposed `CANARY_PASSED`, pre-rollback `CANARY_FAILED`, `WIDENING_REVIEW`, `PROMOTION_PENDING_APPROVAL`, and every generated omission. Race degradation immediately before and after every adjacent edge into or out of the derived set under tuple-version CAS. Apply all named rows to every active member and Effect interval, including degradation after durable direct E06 but before IR38/IR18. For every reachable original Effect state under IH01-W/P, prove atomic degradation recording and send fencing, transition to the exact reconciliation rollout state, and rejection of rollback entry/IRB01 while the Effect is `SENDING|UNKNOWN|LIVE` or unsettled. Race degradation immediately before and after IC24-A and IC32-UW/UP, and immediately before and after the original Effect settlement transaction. In each after-initiation/before-settlement ordering, IH01-WR/PR alone changes `HEALTHY->TELEMETRY_DEGRADED`, keeps the exact reconciliation rollout and original Effect bytes, fences every remaining grant/send, and leaves rollback IDLE. Then exercise exactly one IH06-X/N classification after settlement: X creates one rollback saga; N creates none and selects abort/failure cleanup. In the post-E06 interval exercise only IH01-WV/PV as protected X, atomically recording degradation and rollback; reject every N classifier as conflicting with E06. After each HEALTHY protected-X continuation IC24-RWX/RPX and IC32-RWX/RPX/HWX/HPX, race degradation before and after the continuation and after each reachable IRB advance through `REQUESTED`, `ROLLING_BACK`, `VERIFYING`, `VERIFIED`, `FAILED`, `REMEDIATION_WAIT`, and nonterminal `ROLLED_BACK`; require exactly the matching IH01-RAQ/RAR/RAV/RAD/RAF/RAM/RAO row, exact rollout/Effect/rollback/origin preservation, no second saga or cleanup, authority fencing, and an exact canonical stutter. Exercise IH05 only with protected no-exposure/no-active-generation facts. Generated validation treats generic IH01 as only truly inactive/no-exposure, treats the exact union of IH01-C/W/WR/WV/A/P/PR/PV/D/O plus residual IH01-RX/RN and rollback-adoption IH01-RAQ/RAR/RAV/RAD/RAF/RAM/RAO as the sole legal HEALTHY-to-degraded derived active/exposure interrupts rather than forbidden progress, and rejects every other row after stale health/continuity.
- **Final improvement cleanup.** Execute the last C02 and C12 under both success and failure, plus eligible C09 escalation and cancellation. Exact guards select only ICL01, ICL02, ICL03, or IX04 as the atomic fold/terminal owner; generic C02/C09/C12 cannot claim `S` and no duplicate owner exists.

## 16. Decision subject/action dispatch v1

This is the closed decision dispatch catalog. Each listed action and system closure has exactly one named manifest edge. An omitted action is rejected before event append. `expiry`, `withdraw`, and `stale` are explicit wait/subject closures, not aliases for deny. Status always reports the resulting private/canonical state and the exact recovery command shown.

| Subject | Accept | Request changes | Deny | Expiry / withdrawal / stale-manifest | Durable event and recovery |
|---|---|---|---|---|---|
| `DecisionRecord` | I07 | I08 | I32 | I33 (each trigger recorded distinctly) | `DecisionRecordAccepted\|ChangesRequested\|Denied\|Expired\|Withdrawn\|Stale`; recovery `/factory decide DecisionRecord ... --action request-changes` or reseal and resubmit |
| `ResearchDecision` | D19 with NoPublicationDisposition, or D19P1 when publication requested | D20 | D52 | D53 (distinct trigger field) | `ResearchDecisionAccepted\|ChangesRequested\|Denied\|Expired\|Withdrawn\|Stale`; recovery reseal synthesis/manifest then resubmit |
| `CurationDecision` | IC03 | IC35 | IC04 then IC05 | IC36 (distinct trigger field) | `CurationDecisionAccepted\|ChangesRequested\|Denied\|Expired\|Withdrawn\|Stale`; recovery revise proposal or refresh ExpectedEvaluationManifest then resubmit |
| `ImprovementEnablementDecision` | IR02 | IR44 | IR45 | IR46 for expiry/stale; IR45 for withdrawal | `ImprovementEnablementDecisionAccepted\|ChangesRequested\|Denied\|Expired\|Withdrawn\|Stale`; recovery revise/reseal and resubmit; deny/withdraw starts cleanup |
| `CanaryAdmissionDecision` | IR03 | IR47 | IR48 | IR49 for expiry/stale; IR48 for withdrawal | `CanaryAdmissionDecisionAccepted\|ChangesRequested\|Denied\|Expired\|Withdrawn\|Stale`; recovery revise bounds/bundle and resubmit; deny/withdraw starts cleanup |
| `WideningDecision` | IR37 | IR39 | IR40 | IR41 for expiry/stale; IR40 for withdrawal | `WideningDecisionAccepted\|ChangesRequested\|Denied\|Expired\|Withdrawn\|Stale`; recovery retain old bounds, restore continuity, reseal prior slice, resubmit |
| `PromotionDecision` | IR15 | IR50 | IR16 | IR52 for expiry/stale; IR51 for withdrawal | `PromotionDecisionAccepted\|ChangesRequested\|Denied\|Expired\|Withdrawn\|Stale`; recovery reseal final bundle and resubmit; deny/withdraw starts cleanup |

Every dispatch closes the bound Wait by its explicit Wait edge/event version. The generated CLI/UI check takes the Cartesian set represented by this table, not a uniform action promise, and verifies subject digest, event, wait closure, canonical projection, status, and recovery. `CanaryAdmissionDecision` is rejected at IR37 even if all other fields match.

## 17. Manifest completeness and generated proof gate

A reproducible static check starts from each declared initial and the closed rows in this file. It compares declared symbols with endpoints; checks Markdown widths; exact private/canonical endpoints and `S` equality; §2 adjacency; terminal target/guard agreement; reachability; nonterminal sources; Wait cancellation coverage; per-subject decision dispatch; reducer symbol closure and mutually exclusive precedence; separate CLEANING entry/terminal transactions; and absence of an atomic asynchronous child lifecycle. The round-4 repair ran that ephemeral check; `review/round-4-resolution.md` records its scope, not implementation proof. Increment 1 must turn the same parse into committed compiler/model tests for exact illegal-pair rejection, wait/stale/retry/exhaustion, UNKNOWN, cleanup escalation/resurface, U09/A18 quiescence, one unfinished attempt, every reachable improvement tuple/event, and terminal masking. Future implementation gates are not claimed to have passed.
