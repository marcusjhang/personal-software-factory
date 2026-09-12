# End-to-End Operating Model

**Status:** Proposed workflow. This is an implementation blueprint, not evidence of a deployed production system.

## 1. Common contract

Each step consumes an exact prior aggregate version and emits an event. Each external mutation uses a stable effect key. PostgreSQL is the canonical runtime ledger. GitHub issues, pull requests, checks, and Project fields are reconciled projections. Git holds reviewed policy and immutable spec/plan/evaluation revisions.

An agent can only propose an action. The controller decides whether the requested transition and capability are allowed. No workflow trusts a lifecycle label, issue assignment, comment command, or Project field as proof of authorization.

## 2. Intake: `INBOX -> TRIAGED`

1. Receive an issue form, authorized API submission, signed observability event, dependency/security finding, or human issue.
2. For webhooks, verify `X-Hub-Signature-256` over the raw body, record the provider delivery ID in the durable inbox, enqueue processing, and return quickly ([GitHub validation](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries), [GitHub webhook best practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks)).
3. Normalize source, repository, reporter, evidence references, timestamps, data classification, and a dedupe fingerprint. Do not place secrets or raw sensitive telemetry in a public issue.
4. Correlate duplicates while retaining all provenance. A human can split or merge candidates through recorded commands.
5. Route private security or privacy reports to the approved private channel. Do not project them to a public Project.
6. Create the canonical work item in `INBOX`. Project membership/status is an idempotent follow-up effect, not part of authorization.
7. Triage assigns type, product owner, technical owner, priority, risk floor, affected service/repository, and initial dependencies. Unknown ownership or sensitive scope moves to `BLOCKED`, not to an agent guessed owner.
8. Accepting triage appends `TRIAGED`. Rejecting/cancelling preserves the decision record and reaches `CANCELLED`.

Issue forms can validate only a limited shape and responses become Markdown, so the normalizer validates all fields again ([issue-form schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema)).

## 3. Planning: `TRIAGED -> PLANNING -> READY_REVIEW`

1. The controller pins `base_sha`, desired policy commit, capability profile, and evidence snapshot.
2. A read-only planner receives a bounded context bundle. It produces a versioned spec and typed plan DAG. Required spec fields are problem, desired behavior, non-goals, acceptance oracles, negative/auth cases, dependencies, planned files/resources, risk, migration, rollout, rollback, observability, budgets, and unanswered questions.
3. A deterministic validator checks schema, contradictions, DAG cycles, overlapping parallel write sets, observable acceptance, risk floor, permission and egress requests, rollback feasibility, dependency ownership, and required specialist review.
4. An empirical unknown may receive a narrow, time-boxed, isolated spike. The spike declares method, budget, no-production-side-effect constraint, and disposable outputs. Prototype code does not become implementation merely because it works.
5. A value, product, legal, privacy, security, irreversible, or risk-acceptance decision always goes to the named human.
6. If blocked, append `NEEDS_CLARIFICATION` with one concise question, 2–3 options and trade-offs, a recommendation, evidence, owner, and deadline. Stop implementation spend.
7. An attributable answer or approved spike result creates a new spec revision and returns to `PLANNING`. Never edit an old approved revision in place.
8. If the full deterministic DoR passes, calculate the candidate digest and append `READY_REVIEW`. This transition does not authorize coding.

### Deterministic Definition of Ready

The DoR is a versioned predicate. At minimum it verifies:

- authenticated work item and named product/technical owners;
- precise scope and explicit non-goals;
- positive, negative, regression, authorization, and operability acceptance oracles as applicable;
- reproducible evidence or a reviewed exception;
- acyclic dependency DAG with hard dependencies satisfied or explicitly scheduled;
- declared write/resource sets and safe serialization;
- risk tier, required reviewers, permission/secret/egress profile, and budget;
- migration, rollback, deploy, observation, and cleanup plan where applicable;
- pinned repository/base and compatible current policy;
- no unresolved blocking clarification or destructive drift.

## 4. Readiness: `READY_REVIEW -> READY`

1. Present humans with the exact spec diff, plan DAG, acceptance trace, risk and exception set, base SHA, policy commit, and canonical digest.
2. Product owner approves behavior and non-goals. Technical owner approves feasibility, decomposition, and evidence. Risk policy adds security, data, privacy, operations, or legal owners. Pilot operation should require human readiness approval for every implementation.
3. Verify GitHub principal, role, quorum, separation of duties, exact digest, source review/comment ID, and expiry.
4. Store the approval in PostgreSQL. Recompute DoR and append `READY` only if every predicate still passes.
5. Project `READY` is written after the event and read back. Manually applying that label/status never creates the underlying approval.
6. Any material spec, plan, oracle, dependency, risk, capability, base, policy, or owner-role change revokes the approval and returns to `PLANNING` or `READY_REVIEW`.

GitHub rulesets and protected branches should enforce exact-head reviews and required checks on policy/spec changes ([rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)).

## 5. Admission and lease: `READY -> LEASED`

1. A worker authenticates with short-lived workload identity and submits engine/version, supported capability profile, and an idempotency key.
2. The dispatcher refreshes stale GitHub/dependency observations. In one PostgreSQL transaction it selects eligible rows using explicit priority, aging, quotas, and row locks.
3. Recheck exact approval digest/expiry, aggregate version, `READY`, base compatibility, dependency terminal success, risk, budgets, worker compatibility, global/repository kill switch, and nonoverlapping write/resource sets.
4. Create an attempt. Increase the fencing epoch. Create one expiring lease and scoped outbox job. A database constraint prevents a second active implementation lease.
5. After commit, mirror `LEASED` and assignment to GitHub. Mirror failure creates drift; it does not invalidate or duplicate the lease.
6. Mint a short-lived capability only after admission. Bind repository, branch prefix, paths, commands, egress, secret classes, attempt, fence, and expiry.
7. Assemble and sign a context manifest containing authoritative hashes, protected-base instructions, curated reviewed memory, and untrusted evidence references. The worker verifies all digests before tool use.
8. Heartbeats are explicit authenticated protocol calls. Model output or comments cannot renew a lease.

GitHub Actions concurrency is only an extra run-level guard: its ordering and pending-run behavior do not provide a durable work-item lock ([Actions concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)).

## 6. Implementation: `LEASED -> IMPLEMENTING`

1. Provision a clean, disposable sandbox at the exact `base_sha`; mount protected policy read-only.
2. Register a unique branch/workspace such as `agent/<work-item>/<attempt>`. Refuse existing unowned resources.
3. Worker acknowledges objective, spec digest, planned paths, command IDs, and blockers. The controller denies scope expansion.
4. Execute only allowlisted commands through the capability proxy. Deny production credentials by default. Enforce time, token, cost, diff, process, filesystem, and network budgets.
5. Every remote write carries attempt, fence, expected revision, and effect key. Record intent before the call. If the response is lost, query remote state before retry.
6. Heartbeat and checkpoint independently of model turns. Checkpoints store patch/artifact digests, not authority.
7. On lost lease, cancellation, policy denial, budget exhaustion, or kill switch, stop capabilities first. Late artifacts remain quarantined.
8. Push the exact candidate and open or update one draft PR linked to work item, revision, attempt, and evidence manifest. Confirm remote head SHA. Append `VERIFYING`.

## 7. Clean verification: `VERIFYING`

1. Destroy or disconnect the authoring environment and credentials.
2. Start a fresh ephemeral verifier with no author cache, no write token, and no production secrets. Fetch only the allowlisted repository and exact candidate SHA.
3. Verify the tree has no undeclared generated or untracked output. Install dependencies from locks with integrity checks.
4. Run repository-defined format, lint, type, unit, integration, contract, policy, secret, dependency, license, SBOM, and security checks as applicable. A bug fix should include base-fail/candidate-pass regression evidence when feasible.
5. Record toolchain/image, workflow/action SHAs, commands, check IDs/URLs, counts, results, redactions, artifact digests, candidate/base SHA, and policy/spec versions in machine-readable evidence.
6. Bind all results to the exact current PR head. A new push invalidates prior evidence.
7. Permit only narrowly classified infrastructure retries with the same logical key and a capped budget. Semantic test failure returns to `IMPLEMENTING` if the lease/policy remains valid; otherwise block or replan.
8. Successful independent evidence appends `REVIEW`.

GitHub artifact attestations can bind build provenance to artifacts ([artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations)). Verification should pin third-party Actions to full commit SHAs, which GitHub describes as the only immutable release reference ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)).

## 8. Review: `REVIEW -> MERGE_QUEUED`

1. An AI reviewer may comment and triage. It cannot satisfy the required human/CODEOWNER approval during the baseline and cannot approve its own implementation.
2. Reviewers inspect exact head SHA, spec/acceptance trace, diff/risk, generated code provenance, verification evidence, migrations, rollout/rollback, and protected paths.
3. Configure rulesets for required checks, CODEOWNER review, stale approval dismissal, most-recent-push approval, conversation resolution, signed commits where chosen, and narrow/no bypass.
4. Any new push invalidates head-bound approval and returns through verification.
5. The controller recomputes the merge predicate from current GitHub reads and PostgreSQL records. It requires exact head/revision, clean evidence, current risk quorum, resolved conversations, no blocking drift, and queue eligibility.
6. Exceptions are human-issued records with exact SHA/scope, reason, compensating controls, expiry, and incident/follow-up. Agents cannot request and grant the same exception.
7. Only the merger identity may enqueue. Append `MERGE_QUEUED` after GitHub confirms queue membership.

## 9. Merge: `MERGE_QUEUED -> MERGED`

1. A `merge_group` workflow tests the synthesized merge-group SHA against the latest base. Required workflows must subscribe to the `merge_group` event ([trigger reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group)).
2. Failure, timeout, base change, or invalidated approval removes/blocks the candidate per policy and returns to `REVIEW`; no bypass is inferred.
3. On the merged webhook, reread the PR and repository. Confirm merged status and exact merged commit SHA.
4. Record the terminal merge receipt, revoke implementation lease/capability, and append `MERGED`.
5. Reconcile issue and Project fields from the event. Do not call a closed PR or moved Project card proof of merge.

## 10. Cleanup

Cleanup is a retryable saga, not rollback of the merge.

1. Revoke tokens, lease, sessions, and sandbox credentials.
2. Stop processes and delete the disposable workspace/worktree; prune only registered resources.
3. Delete the agent branch only after confirming merge/no open dependent PR and repository policy. Never pattern-delete human branches.
4. Remove attempt-scoped caches and temporary artifacts. Retain redacted decision/evidence records under policy.
5. Reconcile unknown effects and orphan resources. A failed cleanup stays visible as `BLOCKED`/cleanup debt; it does not undo `MERGED`.
6. Record every deletion receipt and read back critical resources.

GitHub exposes explicit Git ref and Actions artifact deletion APIs; cleanup should use IDs and preconditions rather than shell globs ([Git refs API](https://docs.github.com/en/rest/git/refs), [Actions artifacts API](https://docs.github.com/en/rest/actions/artifacts)).

## 11. Deploy: `MERGED -> DEPLOYING`

1. Determine whether the reviewed spec requires deployment. If not, transition directly to `OBSERVING` with a reason.
2. Recompute deployment predicate over merged SHA/artifact digest, environment, change window, risk tier, approval/exception, health baseline, rollback target, and current policy.
3. Use a separate deployment identity and GitHub Environment protection. Implementation credentials cannot deploy.
4. High-risk/production changes require named human approval of the exact artifact/environment. An agent cannot approve its own release.
5. Record intent before deployment and provider receipt after it. Use staged rollout where supported. Stop on unknown outcome and reconcile rather than redeploy blindly.
6. Verify deployed version/digest. Append `OBSERVING` only after a confirmed receipt and initial health gate.
7. On a guardrail breach, invoke the preapproved rollback or require incident-command approval, verify the restored version, and append `ROLLED_BACK`.

GitHub Environments can require reviewers, prevent self-review, restrict branches/tags, and gate environment secrets ([deployment protection rules](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).

## 12. Observation: `OBSERVING -> DONE`

1. Observe a policy-defined window and compare release cohort to baseline using named SLOs, error budget, correctness/business signals, security alerts, and rollback thresholds.
2. Bind telemetry to deployed artifact/revision. Authenticate sources and deduplicate alert groups.
3. A deterministic evaluator recommends pass, extend, block, or rollback. Ambiguous or high-impact decisions go to the owner/on-call.
4. A pass requires verified cleanup, no unresolved critical effect, evidence retention record, and linked follow-up items. Then append `DONE`.
5. A rollback remains `ROLLED_BACK` until rollback health, cleanup, incident ownership, and follow-up are verified; then it can reach `DONE` without pretending the original change succeeded.
6. Operational signals may open deduplicated `INBOX` items. They cannot silently edit current policy or promote a fix.

## 13. Self-improvement flow

1. **Proposal:** telemetry, incident, reviewer feedback, or agent analysis opens a minimal change proposal with hypothesis, affected component, risk, rollback, and evidence. Proposer has no promotion right.
2. **Curated evaluation:** a human/eval curator accepts or writes versioned representative, regression, security, prompt-injection, and abstention cases. Freeze dataset and evaluator digests. Do not let the candidate write its decisive test after seeing the expected answer without review.
3. **Offline:** replay baseline and candidate in isolated, non-authoritative environments. Report denominators, confidence, regressions, cost/latency, policy denials, and slices—not only aggregate success.
4. **Shadow:** run the candidate on live-shaped inputs with no side-effect authority. Compare decisions against current policy/humans and review disagreements.
5. **Canary:** after human approval of exact candidate/eval digests, enable a narrow repository/task cohort, fixed duration/budget, guardrails, and automatic rollback. Never canary permission/ruleset weakening through agent choice.
6. **Promotion:** an independent human promoter approves the exact digest and rollout scope. Store approval, policy revision, metrics, and rollback pointer. Expand gradually.
7. **Rollback/review:** regressions revert to the known-good digest. Preserve evidence and add a curated case. The proposer cannot alter thresholds, evaluator, evidence, or approver quorum to pass itself.

## 14. Human intervention matrix

| Event/condition | Required human | Binding and action |
|---|---|---|
| Product intent, priority, non-goals | Product owner | Approve spec revision/digest or answer clarification |
| Feasibility, architecture, decomposition, oracle adequacy | Technical owner | Approve exact readiness digest |
| Security, auth, crypto, privacy, legal, billing, public API, data migration, production/IaC | Named specialist(s) | Join readiness, review, and deploy quorum per risk policy |
| New secret, egress, MCP/tool, repo/path write, App permission | Security/platform owner | Approve exact capability, principal, TTL; policy change via protected PR |
| Ambiguous/destructive GitHub schema or access drift | Project/platform owner, often two-person | Freeze; approve inventory and migration plan |
| Failed/waived required verification | Independent risk owner | Normally fix; exception needs exact SHA, expiry, controls, incident |
| Unknown remote side effect | On-call/service owner | Choose query/reconcile/compensate/accept; no blind retry |
| Stale lease touched remote state | On-call/controller owner | Fence, revoke, inventory effects, quarantine/requeue |
| Ruleset/CODEOWNERS/workflow or bypass change | Repository/security owner | Protected exact-head review; agent excluded |
| Merge of ordinary code | CODEOWNER/reviewer per ruleset | Exact head approval; merger identity enqueues |
| Production deploy | Environment reviewer/service owner | Exact artifact/environment approval; prevent self-review |
| Rollback/incident action | Incident commander under runbook | Narrow scope and expiry; later review/backfill |
| Self-improvement eval curation | Independent eval curator | Approve dataset/oracle digest |
| Self-improvement promotion | Independent human promoter/policy owner | Exact candidate/eval digest, canary scope, rollback pointer |
| Cancellation | Product owner or authorized controller policy | Persist reason, revoke/fence, cleanup; never erase evidence |
| Legal hold/evidence deletion | Data/legal owner | Override retention deletion only through audited policy |

## 15. Stop conditions

Fail closed and move to `BLOCKED`, `CANCELLED`, or a prior gated state when there is ambiguous identity, invalid signature, stale approval, missing ownership, cyclic dependency, unsupported API schema, permission expansion, prompt-injection suspicion, secret exposure, destructive drift, unknown effect, lost fence, unverifiable candidate SHA, missing required check, failed rollback predicate, or audit gap.


## 16. Exact durable sub-lifecycle flows

### IDEATION: conversation to decision

1. `CAPTURED`: record question, decision owner, participants, scope, constraints, and the first attributed conversation revision.
2. `RESEARCHING`: approve a bounded research plan. Persist item/field schemas, source requirements, queries, source snapshots/URLs, findings, conflicts, confidence, and researcher identity. Retrieved content is untrusted.
3. `NEEDS_INPUT`: when evidence cannot resolve a value choice, ask the named human and stop dependent work. The answer creates a new attributed revision.
4. `SYNTHESIZING`: validate records and compare alternatives against named criteria. Keep contrary evidence and uncertainty.
5. `DECISION_REVIEW`: present the exact outline, result manifest, synthesis, alternatives, and digests to the decision owner.
6. `DECIDED`: store chosen option, rationale, rejected alternatives, assumptions, review/expiry date, and human exact-digest approval.
7. If implementation is requested, create linked BUILD item(s) in `PLANNING`. Re-run the normal DoR; an ideation decision is input, not implementation authorization.

### BUILD

BUILD follows sections 3–12: planning and clarification, exact readiness, fenced lease, isolated implementation, clean verification, human review, merge queue, merge, cleanup, deployment, observation, and `DONE`/`ROLLED_BACK`. Every revision and attempt remains linked to its originating IDEATION/MAINTENANCE work.

### MAINTENANCE: signal to resolution

1. `SIGNAL_RECEIVED`: authenticate SLO alert, error group, trace, CI failure, dependency/security finding, or user report. Preserve source revision and data class.
2. `CORRELATED`: cluster and deduplicate with stable fingerprint and time window. Keep contributing provenance. A suppression needs owner, reason, and expiry.
3. `DIAGNOSED`: reproduce or correlate to version/deploy, estimate scope, and distinguish symptom from cause. Missing evidence stays explicit.
4. `PROPOSED`: recommend no action, rollback, config/operational action, or linked BUILD item with risk and acceptance evidence.
5. `SCHEDULED`: human/policy prioritizes it. Consequential code/config change enters BUILD and passes the same readiness gates.
6. `EXECUTING`: only a tiny preapproved reversible maintenance action may run directly; otherwise this state follows the linked BUILD attempt. All effects remain fenced and receipted.
7. `VERIFIED` and `OBSERVING`: confirm exact deployed/fixed revision and evaluate the named signal plus broader guardrails over a window.
8. `RESOLVED`: require verified outcome, cleanup, and follow-up ownership. A quiet alert alone is not proof.
9. Guardrail breach invokes rollback and `ROLLED_BACK`, then incident review and a new durable revision.

## 17. Factory-as-code execution

1. A human selects a reviewed factory and supplies schema-valid inputs.
2. The compiler resolves exact module/policy/tool/eval/image versions, checks DAG cycles, schemas, role bindings, capability conflicts, parallel write sets, cleanup, and rollback. It emits a factory digest and reviewable plan.
3. Required humans approve the instance digest. The controller stores the instance in PostgreSQL and creates linked work/sub-lifecycle records.
4. Each node receives only its declared inputs and capability. Outputs are schema-validated, digest-addressed artifacts. Retries use stable node/effect keys.
5. Joins run deterministic predicates over required artifacts. Missing, conflicting, or low-quality output blocks or routes to human review.
6. Completion verifies outputs, cleanup, retention, and GitHub projection. Factory configuration remains in Git; runtime node state does not.

A **deep-research factory** executes: scope revision -> item/field/evidence schema -> query/source plan -> bounded parallel collection -> structured JSON with direct citations/provenance/conflicts/uncertainty -> deterministic validation/deduplication -> adversarial gap review -> synthesis -> human exact-digest decision -> archive/refresh. A source or agent output cannot edit the factory or grant a new tool.

Factory improvements use the same proposal -> human-curated eval -> offline -> non-authoritative shadow -> human-admitted bounded canary -> human exact-digest promotion path. Maximum safe automation includes proposing, validation, approved eval execution, shadowing, and automatic rollback. It excludes permission/gate/eval/threshold changes and self-promotion.

## 18. Engineering-first domain boundary

The current design targets engineering. The shared runtime may later support other domain packs, but their authority is separate. A future GTM domain must live in a separately gated repository/domain and define its own workflows, tools/connectors, graders, owners, approvals, retention, privacy/legal/compliance controls, and publish/deploy rules. It may reuse orchestration, artifact, evaluation, and policy infrastructure only through reviewed interfaces. No engineering agent, approval, capability, factory, or outcome authorizes GTM work. GTM is not delivered by these documents.
