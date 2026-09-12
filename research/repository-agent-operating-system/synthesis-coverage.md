# Synthesis coverage for the 37-track research corpus

> **CURRENT STATUS — TRACEABILITY ONLY, NOT SEMANTIC SUPPORT:** Every legacy source-to-claim relationship described here is an **unreviewed candidate association**. This file does not establish verified truth, current product behavior, semantic entailment, or decision evidence. The controlling scope cutoff and evidence semantics are [`PLAN.md` §4](../../PLAN.md#4-evidence-and-method), [`evidence-cutoff.md`](evidence-cutoff.md), and the schema-3 graph in [`material-claims.json`](material-claims.json). A pre-implementation immutable re-fetch from one run plus human semantic review is required before any candidate edge can become decision evidence.
>
> **Purpose.** This is a coverage and traceability map for `PLAN.md`, not a new effectiveness claim. It records how every requested track informed the plan, including negative findings, conflicts, and uncertainty. The underlying result JSON remains the detailed source for each track.

## Corpus and interpretation

- **Track count:** 37 result files: 14 broad self-managing-software tracks, 10 repository-agent-OS tracks, 5 cross-domain extension tracks, and 8 lifecycle/factory extension tracks. Each file parsed as JSON during this coverage audit and was paired by ordinal with its item in the applicable `outline.yaml`.
- **Also reviewed:** all four outline/field pairs; both prior reports; the self-managing synthesis audit; repository evidence matrix and indexes; repository review protocol/scope decision; `review/plan-link-check.json`; all nine round-1 reviews; all four round-1 resolution memos; and `evidence-cutoff.md`. The resolution memos supersede contradictory prototype behavior.
- **Material** means the track directly changes a normative architecture, lifecycle, policy, state, validation, or rollout decision in `PLAN.md`. **Background** means it supplies landscape, caution, or transfer limits without making a component the selected design. Background evidence still constrains claims.
- **Validation boundary:** JSON parsing, expected-file count, required-field shape, and this mapping establish structural completeness only. They do **not** establish source truth, source independence, semantic correctness, current product behavior, or effectiveness of the proposed composition.
- **Time/provenance boundary:** `evidence-cutoff.md` sets the controlling decision cutoff to **2026-09-12 UTC**. The earlier UTC+08/local-date explanation is only an **unverified legacy process narrative**. Labels such as `access_date`, `as_of`, “accessed,” “observed,” or “snapshot accessed” establish no host timezone, UTC retrieval time, or cutoff compliance. A fresh immutable re-fetch plus human semantic review is a **PRE-IMPLEMENTATION** gate that blocks Increment 1; it is not implementation-time work. No publication or product change first released after the UTC cutoff may support the plan.

## Track-by-track coverage

> **Interpretation rule:** Every “Central conclusion” below is an unverified candidate synthesis or an architecture proposal drawn from legacy records. Structural presence does not establish that external content semantically entails it. Provenance and semantic entailment remain unresolved pending the PRE-IMPLEMENTATION gate.


### A. Broad self-managing-software research (14)

#### SM-01 — Autonomous coding agent platforms

- **File:** `research/self-managing-software-projects/results/01-autonomous-coding-agent-platforms.json`
- **Category / research question:** `platforms` — Devin, OpenAI Codex cloud, GitHub Copilot coding agent, Claude Code and comparable hosted/local agents.
- **PLAN sections informed:** §§1–3, 5, 12, 16, 20, 22–24
- **Use:** **Background**.
- **Central conclusion:** Hosted coding agents can execute bounded issue-to-draft-PR work; keep issue/Git and an independent controller authoritative, with isolated execution and no merge/deploy power.
- **Central uncertainty / transfer limit:** Reported success varies sharply by generation, task selection, coaching, and outcome definition; no transferable unattended production rate.

#### SM-02 — Open-source agent frameworks

- **File:** `research/self-managing-software-projects/results/02-open-source-agent-frameworks.json`
- **Category / research question:** `platforms` — OpenHands, SWE-agent, Aider and extensible orchestration frameworks suitable for issue-to-PR automation.
- **PLAN sections informed:** §§5, 12–13, 16, 20, 22
- **Use:** **Background**.
- **Central conclusion:** Open-source workers are usable behind a two-plane controller/execution design; headless convenience is not an approval or safety boundary.
- **Central uncertainty / transfer limit:** Benchmarks are leakage/test-sensitive, and longitudinal production acceptance, rollback, cost, and security data are missing.

#### SM-03 — Issue and specification driven development

- **File:** `research/self-managing-software-projects/results/03-issue-and-specification-driven-development.json`
- **Category / research question:** `workflow` — Spec-driven planning, backlog intake, issue decomposition, acceptance criteria, and issue-to-PR loops.
- **PLAN sections informed:** §§2, 8.1, 9–10, 14.1–14.2, 20
- **Use:** **Material**.
- **Central conclusion:** Use separate readiness-gated planning and delivery loops, revision-bound READY approval, observable criteria, and clarification/decomposition paths.
- **Central uncertainty / transfer limit:** The intended “PStack” referent and comparative outcome evidence for planning products remain uncertain.

#### SM-04 — CI/CD and agent execution integration

- **File:** `research/self-managing-software-projects/results/04-ci-cd-and-agent-execution-integration.json`
- **Category / research question:** `workflow` — How agents run in GitHub Actions, GitLab, sandboxes, ephemeral workspaces, and deployment pipelines.
- **PLAN sections informed:** §§5, 13, 15–17, 21.3–21.4
- **Use:** **Material**.
- **Central conclusion:** Separate an untrusted disposable agent sandbox, clean-room verifier, and trusted build/deploy path; split author and promoter credentials.
- **Central uncertainty / transfer limit:** Integrations prove execution primitives, not code correctness; production injection/incident rates and comparative cost remain unknown.

#### SM-05 — Dependency and security maintenance

- **File:** `research/self-managing-software-projects/results/05-dependency-and-security-maintenance.json`
- **Category / research question:** `maintenance` — Dependabot, Renovate, security scanners, autofix tools, patch validation, and safe auto-merge.
- **PLAN sections informed:** §§7, 14.3, 15–17, 19–21
- **Use:** **Material**.
- **Central conclusion:** Use evidence-gated routine and security maintenance lanes; only narrow allowlisted updates may advance automatically after independent checks.
- **Central uncertainty / transfer limit:** No universal detector accuracy or safe auto-merge threshold exists; vendor packaging and ecosystem behavior change.

#### SM-06 — Observability to autonomous remediation

- **File:** `research/self-managing-software-projects/results/06-observability-to-autonomous-remediation.json`
- **Category / research question:** `maintenance` — Logs, errors, traces, incidents, Sentry and AIOps-style diagnosis-to-fix workflows.
- **PLAN sections informed:** §§7, 14.3, 17, 19–22
- **Use:** **Material**.
- **Central conclusion:** Use closed-loop automation only for known, versioned, reversible runbooks; unknown/code remediation remains evidence gathering plus human-approved PR and rollout.
- **Central uncertainty / transfer limit:** No independent apples-to-apples remediation benchmark or audited production RCA/patch distribution was found.

#### SM-07 — Automated testing, review, and quality gates

- **File:** `research/self-managing-software-projects/results/07-automated-testing-review-and-quality-gates.json`
- **Category / research question:** `assurance` — Test generation, static analysis, AI review, confidence scoring, evals, and merge gates.
- **PLAN sections informed:** §§7, 14.2, 15–16, 21
- **Use:** **Material**.
- **Central conclusion:** Use a protected deterministic evidence ladder, exact-SHA checks, merge-queue reruns, and risk-tiered human gates; AI review stays advisory.
- **Central uncertainty / transfer limit:** AI reviewer precision/recall and any universal confidence mapping are unvalidated; benchmark validity is disputed.

#### SM-08 — Human oversight, governance, and security

- **File:** `research/self-managing-software-projects/results/08-human-oversight-governance-and-security.json`
- **Category / research question:** `assurance` — Approval boundaries, permissions, sandboxing, prompt injection, supply-chain threats, audit and rollback.
- **PLAN sections informed:** §§5, 7, 10, 15–17, 21.3, 22
- **Use:** **Material**.
- **Central conclusion:** Adopt zero-standing-privilege proposal agents, ephemeral containment, independent approval, signed artifacts, staged release, audit, and rollback.
- **Central uncertainty / transfer limit:** Current sandbox/firewall effectiveness lacks independent audit; living feature behavior is plan- and tenant-dependent.

#### SM-09 — Academic autonomous software engineering

- **File:** `research/self-managing-software-projects/results/09-academic-autonomous-software-engineering.json`
- **Category / research question:** `evidence` — Research systems, benchmarks, repair agents, repository-level agents, and measured limitations.
- **PLAN sections informed:** §§4, 15, 21.6, 22, 25
- **Use:** **Background**.
- **Central conclusion:** Treat academic agents as candidate-patch workers; evaluate prospectively on fresh private tasks with full denominators and protected tests.
- **Central uncertainty / transfer limit:** Leaderboard results shift with harness, contamination, budget, and task freshness and do not establish production outcomes.

#### SM-10 — Production case studies and operational evidence

- **File:** `research/self-managing-software-projects/results/10-production-case-studies-and-operational-evidence.json`
- **Category / research question:** `evidence` — Documented real-world deployments, success rates, failure modes, costs, and maintenance burden.
- **PLAN sections informed:** §§1, 4, 20, 21.6, 22–24
- **Use:** **Background**.
- **Central conclusion:** The legacy records motivate a proposal for supervised, staged autonomy and local promotion gates rather than general self-management; human entailment review remains pending.
- **Central uncertainty / transfer limit:** Customer stories omit comparable denominators and conflict with field studies showing low success or slowdown.

#### SM-11 — Multi-agent orchestration and control planes

- **File:** `research/self-managing-software-projects/results/11-multi-agent-orchestration-and-control-planes.json`
- **Category / research question:** `architecture` — Task routing, durable queues, state, retries, memory, event-driven agents, and supervisor patterns.
- **PLAN sections informed:** §§5, 8, 13, 14, 19, 21.4, 22
- **Use:** **Material**.
- **Central conclusion:** Use one durable authoritative workflow with bounded activities; start single-agent and fan out only where measured independent value exceeds cost/failure risk.
- **Central uncertainty / transfer limit:** Multi-agent gains depend on topology, model strength, task decomposability, and verifier quality; fair scheduling and semantic correctness are not supplied by queues.

#### SM-12 — Self-improvement and feedback loops

- **File:** `research/self-managing-software-projects/results/12-self-improvement-and-feedback-loops.json`
- **Category / research question:** `architecture` — Telemetry, user feedback, postmortems, eval datasets, policy updates, and safe workflow evolution.
- **PLAN sections informed:** §§5, 8.4–8.5, 14.5, 17, 19, 21, 22
- **Use:** **Material**.
- **Central conclusion:** Build an asymmetric governed evidence flywheel: agents may collect/propose, but cannot own evaluators, approval, permissions, evidence deletion, or blast-radius expansion.
- **Central uncertainty / transfer limit:** No evidence supports safe general recursive self-improvement; offline gains may not transfer and task-horizon trends are not authorization evidence.

#### SM-13 — End-to-end reference architectures

- **File:** `research/self-managing-software-projects/results/13-end-to-end-reference-architectures.json`
- **Category / research question:** `architecture` — Existing blueprints that connect planning, building, review, deploy, observe, repair, and learn.
- **PLAN sections informed:** §§1–2, 5, 13–20, 23–24
- **Use:** **Material**.
- **Central conclusion:** Use a proposal-first hub-and-spoke architecture: deterministic controller, replaceable workers, PR/artifact/GitOps/telemetry contracts, staged autonomy.
- **Central uncertainty / transfer limit:** No audited reviewed example proves the complete loop; GA/availability and component capability do not establish end-to-end efficacy.

#### SM-14 — Adoption maturity and build-vs-buy landscape

- **File:** `research/self-managing-software-projects/results/14-adoption-maturity-and-build-vs-buy-landscape.json`
- **Category / research question:** `decision` — What is solved now, what remains experimental, tool selection, incremental rollout, and economics.
- **PLAN sections informed:** §§1, 3, 12, 20, 21.6, 22–24
- **Use:** **Material**.
- **Central conclusion:** Buy or reuse the worker initially, but build a thin vendor-neutral policy/evaluation wrapper and expand only after local task-class economics and safety evidence.
- **Central uncertainty / transfer limit:** No independent census or apples-to-apples total-cost/ROI evidence exists; headline speed results conflict across task settings.


### B. Repository-agent operating system research (10)

#### ROS-01 — GitHub Issues and Projects as code

- **File:** `research/repository-agent-operating-system/results/01-github-issues-and-projects-as-code.json`
- **Category / research question:** `github-control-plane` — Issue forms, labels, Project v2 fields/statuses, APIs, declarative reconciliation, limitations, permissions, and drift.
- **PLAN sections informed:** §§5, 8.1, 11, 13, 19–21
- **Use:** **Material**.
- **Central conclusion:** Treat repository files as desired Project schema/policy and reconcile them non-destructively with remote Projects state; keep a durable ledger and preserve unknowns.
- **Central uncertainty / transfer limit:** Full Projects-as-code parity is conditional on preview APIs, opaque IDs, pagination, races, permissions, and target-tenant behavior.

#### ROS-02 — Ticket planning and readiness gates

- **File:** `research/repository-agent-operating-system/results/02-ticket-planning-and-readiness-gates.json`
- **Category / research question:** `planning` — State machine, Definition of Ready, revision-bound approval, clarification, decomposition, specs, PStack and comparable patterns.
- **PLAN sections informed:** §§2, 8.1, 9–11, 14.1–14.2, 20–21
- **Use:** **Material**.
- **Central conclusion:** Use a deterministic planning state machine with revision/hash-bound READY authority; Project status is a projection, not authorization.
- **Central uncertainty / transfer limit:** GitHub provides parts, not the composed readiness service; role semantics and thresholds require local policy and tests.

#### ROS-03 — Agent bootstrap and instant context

- **File:** `research/repository-agent-operating-system/results/03-agent-bootstrap-and-instant-context.json`
- **Category / research question:** `agent-runtime` — How a newly started agent discovers objectives, current state, project rules, architecture, commands, memory, leases, and next eligible work without chat history.
- **PLAN sections informed:** §§5.1, 6, 8.4, 12–13, 16, 21.2
- **Use:** **Material**.
- **Central conclusion:** Issue a signed, bounded execution-context bundle plus atomic fenced claim; never infer authority from chat, labels, memory, or instruction files.
- **Central uncertainty / transfer limit:** Instruction discovery and precedence differ across tools; the composed instant-context system has no local reliability evidence yet.

#### ROS-04 — Issue claiming, orchestration, and concurrency

- **File:** `research/repository-agent-operating-system/results/04-issue-claiming-orchestration-and-concurrency.json`
- **Category / research question:** `orchestration` — Admission, priority, dependencies, leases, heartbeats, idempotency, retries, parallelism, cancellation, stale work, and durable state.
- **PLAN sections informed:** §§5, 8.3–8.5, 13, 19–21
- **Use:** **Material**.
- **Central conclusion:** Use a PostgreSQL fenced-lease/outbox controller, one disposable worker, idempotent effects, reconciliation, and human-gated merge before adding Temporal or parallel writers.
- **Central uncertainty / transfer limit:** Mature primitives do not prove the composition; fairness, retry safety, workload limits, and GitHub race behavior need fault/pilot evidence.

#### ROS-05 — Implementation, verification, review, and cleanup

- **File:** `research/repository-agent-operating-system/results/05-implementation-verification-review-and-cleanup.json`
- **Category / research question:** `delivery` — Branch/worktree lifecycle, evidence bundles, clean-room CI, AI/human review, merge queues, cleanup of branches/workspaces/comments/artifacts.
- **PLAN sections informed:** §§5.1, 8.4–8.5, 14.2, 15–16, 21
- **Use:** **Material**.
- **Central conclusion:** Use disposable implementation, exact-head clean-room verification, independent approval, merge queue, evidence manifests, and cleanup/revocation sagas.
- **Central uncertainty / transfer limit:** Exact-head evidence and cleanup composition need custom validation; AI approval accuracy and artifact-attestation coverage are conditional.

#### ROS-06 — Risk-tiered human gates and merge policy

- **File:** `research/repository-agent-operating-system/results/06-risk-tiered-human-gates-and-merge-policy.json`
- **Category / research question:** `governance` — Human intervention rules, CODEOWNERS, rulesets, auto-merge predicates, exceptions, production approval, permissions, security and audit.
- **PLAN sections informed:** §§7, 10, 15–17, 21.3, 22
- **Use:** **Material**.
- **Central conclusion:** Enforce R0–R4 with separate identities, protected control paths, live ruleset/environment inventory, hash-bound approvals, and narrowly earned auto-merge.
- **Central uncertainty / transfer limit:** Git-native declarations are not live enforcement; plan features, bypasses, CI trust, and human behavior remain deployment-specific.

#### ROS-07 — Observability-driven issue creation and maintenance

- **File:** `research/repository-agent-operating-system/results/07-observability-driven-issue-creation-and-maintenance.json`
- **Category / research question:** `operations` — Logs/errors/traces/dependency/security/CI events to deduplicated planned issues; known runbooks, escalation, rollback, and noise controls.
- **PLAN sections informed:** §§8.1, 13, 14.3, 19–21
- **Use:** **Material**.
- **Central conclusion:** Turn signals into deduplicated planned work through authenticated durable intake, source-aware fingerprints, privacy partitions, noise budgets, and human triage first.
- **Central uncertainty / transfer limit:** Cross-source identity, useful thresholds, ownership, flake detection, and closure policy are repository-specific.

#### ROS-08 — Governed self-improvement

- **File:** `research/repository-agent-operating-system/results/08-governed-self-improvement.json`
- **Category / research question:** `improvement` — Feedback and telemetry to postmortems, eval cases, workflow/prompt/tool proposals, offline/shadow/canary tests, promotion, rollback, and anti-self-governance boundaries.
- **PLAN sections informed:** §§8.4–8.5, 14.5, 17, 19–22
- **Use:** **Material**.
- **Central conclusion:** Use a governed proposal/evaluation/promotion/rollback loop with protected evaluators and separate identities; reconcile remote operational state.
- **Central uncertainty / transfer limit:** Graders and automatic low-risk promotion are only conditionally useful after local calibration; recursive policy/evaluator ownership remains prohibited.

#### ROS-09 — Repository-native configuration and reusable distribution

- **File:** `research/repository-agent-operating-system/results/09-repository-native-configuration-and-reusable-distribution.json`
- **Category / research question:** `configuration` — Exact schemas, directory layout, reusable workflows/actions, versioning, bootstrapping multiple repositories, portability and upgrades.
- **PLAN sections informed:** §§5, 6, 11–13, 16, 18, 20–21
- **Use:** **Material**.
- **Central conclusion:** Freeze a versioned repository contract, compiler/renderer, locks and conformance fixtures; distribute pinned reusable workflows, then add bounded remote reconciliation.
- **Central uncertainty / transfer limit:** Fleet portability and migration safety require custom engineering; Project/ruleset state remains mutable, remote, and plan-dependent.

#### ROS-10 — End-to-end reference implementation and rollout

- **File:** `research/repository-agent-operating-system/results/10-end-to-end-reference-implementation-and-rollout.json`
- **Category / research question:** `synthesis` — Minimum viable stack, event/state contracts, GitHub integration, end-to-end scenarios, tests, operational runbooks, staged adoption and success criteria.
- **PLAN sections informed:** §§1–2, 5–24
- **Use:** **Material**.
- **Central conclusion:** Roll out observe-only, assisted, draft-PR, narrow auto-merge, and canary stages with fault, security, state, and outcome stop gates.
- **Central uncertainty / transfer limit:** Numeric gates are hypotheses to preregister and calibrate; model planning, repair, semantic dedupe, and broad autonomy remain experimental.


### C. Cross-domain extension research (5)

#### DOM-01 — Cross-domain artifact factory abstraction

- **File:** `research/repository-agent-operating-system/domain-extension/results/01-cross-domain-artifact-factory-abstraction.json`
- **Category / research question:** `architecture` — Find the smallest domain-neutral model that supports engineering, research/writing, and GTM without reducing everything to agents/chats or prematurely building a plugin platform.
- **PLAN sections informed:** §§5–6, 8–10, 13–14, 18, 20–21
- **Use:** **Material**.
- **Central conclusion:** Use the smallest domain-neutral kernel for runs, steps, artifacts, decisions, policy, effects, and provenance; keep domain schemas and adapters outside it.
- **Central uncertainty / transfer limit:** No production validation exists, and vendor/API capabilities plus the best constraint/schema language require deployment-time tests.

#### DOM-02 — GTM factory workflows and current systems

- **File:** `research/repository-agent-operating-system/domain-extension/results/02-gtm-factory-workflows-and-current-systems.json`
- **Category / research question:** `gtm` — Research how current teams/products define AI-assisted market research, ICP/positioning, campaigns, content, CRM enrichment, outreach, experiments, attribution, review, publication and feedback; distinguish safe automation and vendor claims.
- **PLAN sections informed:** §§3, 7, 10, 14, 18, 20, 22–24
- **Use:** **Material**.
- **Central conclusion:** Build the kernel inside engineering first; do not launch GTM or a general plugin SDK until reuse and outcome gates are met.
- **Central uncertainty / transfer limit:** GTM vendor capabilities lack independent end-to-end outcome evidence; privacy, licensing, approval, attribution, and causal lift remain unknown.

#### DOM-03 — Multi-repository project and domain isolation

- **File:** `research/repository-agent-operating-system/domain-extension/results/03-multi-repository-project-and-domain-isolation.json`
- **Category / research question:** `fleet` — Design one shared runtime serving separate engineering and GTM repositories with project isolation, configuration inheritance, secrets, quotas, identities, artifact stores, events, upgrades and cross-repo handoffs.
- **PLAN sections informed:** §§5, 6.3, 12–13, 16, 18, 20–21
- **Use:** **Material**.
- **Central conclusion:** Share a thin kernel but isolate projects/domains through signed bundles, identities, quotas, secrets, stores, and policies; namespaces alone are not hard isolation.
- **Central uncertainty / transfer limit:** Isolation, reliability, cost, and productivity are unmeasured; exact provider permissions vary.

#### DOM-04 — Engineering-first extension and extraction gates

- **File:** `research/repository-agent-operating-system/domain-extension/results/04-engineering-first-extension-and-extraction-gates.json`
- **Category / research question:** `roadmap` — Define exactly what the engineering implementation must make generic now, what stays engineering-specific, and evidence/trigger gates for extracting a domain SDK and starting GTM.
- **PLAN sections informed:** §§1, 3, 6, 18, 20–24
- **Use:** **Material**.
- **Central conclusion:** Make generic envelopes, ledger/outbox/leases, isolation, capability ports, budgets, locks, and telemetry now; extract only after measured cross-workflow/domain reuse.
- **Central uncertainty / transfer limit:** Suggested thresholds are decision rules, not universal evidence; the proposed runtime/connectors have no independent audit.

#### DOM-05 — Team and organizational factory patterns

- **File:** `research/repository-agent-operating-system/domain-extension/results/05-team-and-organizational-factory-patterns.json`
- **Category / research question:** `evidence` — Compare how Warp Factories, Anthropic, OpenAI, Microsoft/GitHub, GitLab and other credible teams define roles, workflows, artifacts, evals, human gates and domain-specific factories; extract transferable patterns and conflicts.
- **PLAN sections informed:** §§1, 5–7, 10, 14, 18, 20, 22–23
- **Use:** **Material**.
- **Central conclusion:** Credible teams support simple workflows, specialized roles, explicit artifacts/evals/gates, and engineering-first extraction rather than a universal multi-agent marketplace.
- **Central uncertainty / transfer limit:** Public organizational cases are selected and often vendor-reported; Warp runtime semantics and outcome denominators are incomplete.


### D. Lifecycle/factory extension research (8)

#### LIFE-01 — Warp Factories and factory-as-code model

- **File:** `research/repository-agent-operating-system/lifecycle-extension/results/01-warp-factories-and-factory-as-code-model.json`
- **Category / research question:** `reference-system` — Trace current official Warp factory definitions, roles, workflows, scorers, benchmarks, triggers, state, human review and self-improvement claims; distinguish documented capability from evidence.
- **PLAN sections informed:** §§4–6, 8, 10, 13–14, 18, 22
- **Use:** **Material**.
- **Central conclusion:** Use Warp v1alpha1 as a pinned adapter/UX reference, not canonical authority; add a repository-owned typed extension and durable controller.
- **Central uncertainty / transfer limit:** Warp public material omits authoritative runtime state, retries, effect semantics, retention/export guarantees, and outcome denominators.

#### LIFE-02 — Conversational ideation and discovery lifecycle

- **File:** `research/repository-agent-operating-system/lifecycle-extension/results/02-conversational-ideation-and-discovery-lifecycle.json`
- **Category / research question:** `ideation` — Design durable user-agent back-and-forth from raw idea through research, alternatives, product decisions, specifications, prototypes, deferral/cancellation and READY review.
- **PLAN sections informed:** §§2, 5.1, 8.1, 9–10, 14.1, 14.1/IDEATION, 21
- **Use:** **Material**.
- **Central conclusion:** Represent ideation as durable events, decisions, artifacts, and explicit wait/ready/cancel states, not a long chat or framework checkpoint.
- **Central uncertainty / transfer limit:** No universal optimal question count, readiness score, timeout, or memory policy exists; Warp-specific parity was not established here.

#### LIFE-03 — Build lifecycle and phase orchestration

- **File:** `research/repository-agent-operating-system/lifecycle-extension/results/03-build-lifecycle-and-phase-orchestration.json`
- **Category / research question:** `building` — Exhaustively model decomposition, dependencies, leases, implementation, checkpoints, verification, review, cleanup, merge, deploy and exception paths.
- **PLAN sections informed:** §§5.1, 6–8, 10, 13, 14.0, 14.2, 15, 21
- **Use:** **Material**.
- **Central conclusion:** Model build as explicit aggregates and paths for decomposition, leases, checkpoints, verification, revision, merge, deploy, cancel, stale, and cleanup; begin sequential/shadow.
- **Central uncertainty / transfer limit:** Optimal decomposition, parallelism, retries, and review gates are local; GitHub plan and repository controls must be inventoried.

#### LIFE-04 — Maintenance and operations lifecycle

- **File:** `research/repository-agent-operating-system/lifecycle-extension/results/04-maintenance-and-operations-lifecycle.json`
- **Category / research question:** `maintenance` — Model intake from users/logs/CI/security/dependencies, triage, dedupe, diagnosis, planned remediation, runbooks, incidents, rollback, postmortem and recurrence prevention.
- **PLAN sections informed:** §§5.1, 8, 10, 13, 14.3, 17, 19–21
- **Use:** **Material**.
- **Central conclusion:** Use a thin durable reconciliation controller around existing operations tools; begin authenticated shadow triage and only automate proven reversible runbooks.
- **Central uncertainty / transfer limit:** No evidence proves broad autonomous observe-to-repair safety; vendor pages are mutable and local noise/risk thresholds are unknown.

#### LIFE-05 — Deep-research factory as a reusable workflow

- **File:** `research/repository-agent-operating-system/lifecycle-extension/results/05-deep-research-factory-as-a-reusable-workflow.json`
- **Category / research question:** `factory` — Define a factory-as-code workflow for outlining, adding items/fields, parallel primary-source research, validation, conflict audit, report generation, user decisions, resume and evidence refresh.
- **PLAN sections informed:** §§4, 5.1, 6, 10, 14.4, 21.5, 22, 25
- **Use:** **Material**.
- **Central conclusion:** Make research a resumable deterministic factory with typed source/claim/result manifests, digests, conflict audit, validation, selective refresh, and human decisions.
- **Central uncertainty / transfer limit:** Living-source snapshots and retrieval lineage are incomplete in this corpus; schema validation alone cannot prove truth or independence.

#### LIFE-06 — General factory DSL and orchestrator runtime

- **File:** `research/repository-agent-operating-system/lifecycle-extension/results/06-general-factory-dsl-and-orchestrator-runtime.json`
- **Category / research question:** `factory` — Define versioned declarative factory schemas for roles, phases, transitions, artifacts, tools, budgets, parallel fanout/join, checkpoints, gates, escalation, retries, cleanup and composition.
- **PLAN sections informed:** §§5–6, 8, 10, 13–14, 18, 20–21
- **Use:** **Material**.
- **Central conclusion:** Compile a small versioned DSL to normalized IR executed by a deterministic event/outbox/lease/policy controller; treat agents and Warp as adapters.
- **Central uncertainty / transfer limit:** Hosted runtime semantics and universal DSL completeness are unknown; composition and migration need conformance/fault tests.

#### LIFE-07 — Human-need decision engine and interaction contract

- **File:** `research/repository-agent-operating-system/lifecycle-extension/results/07-human-need-decision-engine-and-interaction-contract.json`
- **Category / research question:** `governance` — Define deterministic plus evidence-based policies for when agents continue, ask clarifying questions, request approval, escalate, pause or stop across ideation/build/maintenance.
- **PLAN sections informed:** §§5.1, 7, 9–10, 14, 16, 21
- **Use:** **Material**.
- **Central conclusion:** Use deterministic R0–R4 rules and typed DecisionRecords to continue, ask, approve, escalate, pause, or stop; prompts provide UX, not enforcement.
- **Central uncertainty / transfer limit:** Risk appetite, role map, provider editions, regulated-data context, and classifier calibration are deployment-specific.

#### LIFE-08 — Full self-improvement loop and exhaustive state testing

- **File:** `research/repository-agent-operating-system/lifecycle-extension/results/08-full-self-improvement-loop-and-exhaustive-state-testing.json`
- **Category / research question:** `improvement` — Define maximal safe automated improvement, protected invariants, evaluator governance, state-machine model testing, fault/adversarial tests, promotion/rollback and what cannot be made autonomous.
- **PLAN sections informed:** §§5.1, 6–8, 14.5, 16–17, 19–22
- **Use:** **Material**.
- **Central conclusion:** Automate observation, proposal, testing, shadowing, and narrow canaries, but protect invariants/evaluators/promotion/rollback with separate authority and exhaustive model/fault tests.
- **Central uncertainty / transfer limit:** Safe general recursive self-improvement is unsupported; offline metrics miss delayed harms and no universal promotion sample/window exists.


## PLAN section coverage audit

Every numbered PLAN section has at least one material research edge. The compact index below identifies the main edges; the track entries above contain the fuller many-to-many mapping.

| PLAN section | Main research tracks |
|---|---|
| §1 Decision | SM-13, SM-14, ROS-10, DOM-04, DOM-05 |
| §2 Reader-visible walkthrough | SM-03, SM-13, ROS-02, ROS-10, LIFE-02 |
| §3 Goals and non-goals | SM-01, SM-14, DOM-02, DOM-04 |
| §4 Evidence and method | SM-09, SM-10, LIFE-05, LIFE-01 |
| §5 Architecture / three authorities and §5.1 records | SM-11–SM-13, ROS-03–ROS-05, DOM-01, LIFE-02–LIFE-08 |
| §6 Contract/compiler, guards, composition, cleanup | ROS-03, ROS-09, DOM-01, DOM-03–DOM-04, LIFE-03, LIFE-06, LIFE-08 |
| §7 Risk R0–R4 | SM-05–SM-08, ROS-06, DOM-02, LIFE-07–LIFE-08 |
| §8 Separate aggregate state models | SM-11–SM-12, ROS-01–ROS-05, ROS-07–ROS-08, LIFE-02–LIFE-04, LIFE-08 |
| §9 Conversation/Decision artifacts | SM-03, ROS-02, LIFE-02, LIFE-07 |
| §10 Human-needed engine | SM-03, SM-08, ROS-02, ROS-06, DOM-01–DOM-02, LIFE-02–LIFE-08 |
| §11 Issues and Projects as code | ROS-01–ROS-02, ROS-09 |
| §12 Signed bootstrap/context | SM-01–SM-02, SM-14, ROS-03, ROS-09, DOM-03 |
| §13 Orchestration/effects | SM-04, SM-11, ROS-01, ROS-03–ROS-04, ROS-07, ROS-09, DOM-01, LIFE-03–LIFE-07 |
| §14.0 Cross-cutting states/projections | SM-11–SM-13, ROS-10, DOM-01–DOM-02, LIFE-03, LIFE-06–LIFE-08 |
| §14.1 IDEATION | SM-03, ROS-02, LIFE-02, LIFE-07 |
| §14.2 BUILD | SM-03, SM-07, ROS-02, ROS-05, LIFE-03 |
| §14.3 MAINTENANCE | SM-05–SM-06, ROS-07, LIFE-04 |
| §14.4 DEEP-RESEARCH | LIFE-05 |
| §14.5 IMPROVEMENT | SM-12, ROS-08, LIFE-08 |
| §15 Review/merge/cleanup | SM-04, SM-07–SM-09, SM-13, ROS-05–ROS-06, LIFE-03 |
| §16 Security/isolation/approvals/supply chain | SM-04, SM-07–SM-08, ROS-03, ROS-05–ROS-06, DOM-03, LIFE-07–LIFE-08 |
| §17 Releases/dogfood/canaries/feedback | SM-04–SM-06, SM-08, SM-12–SM-13, ROS-06, ROS-08, LIFE-04, LIFE-08 |
| §18 Engineering-first domain/GTM | ROS-09, DOM-01–DOM-05, LIFE-01, LIFE-06 |
| §19 Observability/metrics | SM-05–SM-06, SM-10–SM-13, ROS-01, ROS-04, ROS-07–ROS-08, LIFE-04, LIFE-08 |
| §20 Roadmap/stop gates | SM-01, SM-03, SM-05–SM-06, SM-10, SM-13–SM-14, all ROS tracks, all DOM tracks, LIFE-03–LIFE-08 |
| §21 Validation | SM-04–SM-09, SM-11–SM-14, all ROS tracks, all DOM tracks, LIFE-02–LIFE-08 |
| §22 Risks/conflicts/uncertainty | All 37 tracks; especially SM-09–SM-14, ROS-06, ROS-08, ROS-10, DOM-02–DOM-05, LIFE-01, LIFE-04–LIFE-08 |
| §23 Recommendation | SM-10, SM-13–SM-14, ROS-10, DOM-02, DOM-04–DOM-05 |
| §24 Immediate actions | SM-01, SM-10, SM-13–SM-14, ROS-10, DOM-02, DOM-04 |
| §25 Sources/supporting research | All 37 result files through their source records; LIFE-05 sets the future provenance contract. |

## Conflicts retained in the synthesis

These are not averaged away. They constrain the plan and remain unresolved until the stated local evidence exists.

1. **Agent availability versus agent effectiveness (SM-01, SM-02, SM-04, SM-10, SM-13).** Products can run issue-to-PR workflows. This does not prove correct, secure, economical, unattended completion. Vendor/customer merge and speed figures conflict with Answer.AI’s small-task experience and METR’s measured slowdown. The plan therefore treats workers as replaceable proposal producers and makes outcomes pilot hypotheses.
2. **Benchmark progress versus benchmark validity/freshness (SM-02, SM-07, SM-09, LIFE-08).** SWE-bench and Verified show reproducible progress. SWE-bench+, SWE-rebench, UTBoost, and related audits show leakage, weak tests, erroneous passes, harness sensitivity, and fresh-task gaps. The plan requires protected local tasks and outcome follow-up, not leaderboard-based authorization.
3. **More agents versus simpler workflows (SM-11, DOM-05).** Parallel sampling can help broad, decomposable research. Multi-agent systems also add coordination failures, token cost, correlated errors, and weak gains with stronger base models. The default is one worker; fan-out needs a measured value case and deterministic join.
4. **“Projects/status as code” versus mutable remote truth (ROS-01, ROS-02, ROS-06, ROS-08, ROS-09, ROS-10, DOM-01).** Git can own reviewed desired definitions. Project fields/items, rulesets, environments, grants, leases, and approvals are remote or transactional actual state. The plan uses three authorities and reconciliation rather than claiming Git owns live state.
5. **Repository-native versus cross-domain runtime (DOM-01, DOM-03).** A repository is the right home for versioned domain definitions, but not for leases, event order, effects, secrets, or cross-system observations. The shared kernel stays narrow; domain artifacts and authorization remain domain/project-owned.
6. **Reusable kernel versus premature platform (DOM-01–DOM-05, LIFE-06).** Reuse is valuable, but a plugin marketplace or universal ontology before two real consumers would fossilize guesses. The plan makes a few envelopes/ports generic and gates extraction on demonstrated reuse and migration evidence.
7. **Warp “factory as code/complete state” versus documented exclusions (LIFE-01, LIFE-05, LIFE-06, DOM-05).** Official Warp material exposes useful versioned factory configuration and human handoff, while also excluding work items, runs, and metrics and not publishing key durability/effect semantics. Warp is an adapter/reference, not the canonical ledger or authorization layer.
8. **“Self-improving” versus self-governance (SM-12, ROS-08, LIFE-06, LIFE-08).** Automated failure aggregation, candidate generation, evaluation execution, shadowing, and canaries can be useful. They do not justify control over ground truth, evaluators, protected policy, permissions, promotion, evidence deletion, or rollback authority.
9. **Framework durability versus business correctness (SM-11, LIFE-02, LIFE-03, LIFE-06).** Temporal/LangGraph/checkpoint and queue primitives help resume computation. They do not by themselves supply fair admission, fenced external writes, exactly-once effects, authorization, semantic idempotency, audit, or correct lifecycle state.
10. **AI review/RCA confidence versus independent assurance (SM-06, SM-07, ROS-05, LIFE-04).** Vendors document review, diagnosis, and repair features. Independent evidence does not establish representative production precision or safe approval power. AI outputs remain hypotheses/advice; exact-head deterministic verification and accountable approval remain separate.
11. **Security features versus residual prompt/supply-chain risk (SM-04, SM-08, ROS-06).** Sandboxes, firewalls, rulesets, OIDC, attestations, and scanning reduce risk. Their own documentation preserves bypass, configuration, MCP/setup, dependency, and tenant limits. The plan uses defense in depth and zero standing privilege, not a “secure agent” conclusion.
12. **Detector-local grouping versus operational work identity (ROS-07, LIFE-04).** Sentry/SARIF/Alertmanager-style fingerprints are useful inputs but do not prove that cross-source events share one root cause or desired fix. Semantic dedupe starts in shadow mode with merge/split audit and human triage.
13. **GTM “end-to-end” claims versus causal business evidence (DOM-02).** Vendor pages show functions and selected narratives, not representative uplift, complaint/brand harm, reviewer cost, or attribution validity. GTM execution is deferred and would require separate privacy, consent, licensing, brand, and outcome gates.
14. **Universal thresholds versus local policy (all rollout/evaluation tracks).** Suggested counts, windows, rates, and risk cutoffs are preregistered decision rules, not facts that transfer across repositories. Baselines, denominators, confidence intervals, delayed harms, reviewer burden, and rollback outcomes must be measured locally.
15. **Cutoff narrative versus retrieval proof (LIFE-05 and the evidence resolution memo).** The UTC/local-date explanation makes the dates internally plausible but does not prove when each URL was fetched or what bytes were observed. The plan’s future `ResearchRun`/`SourceObservation` contract is a correction, not evidence that this corpus already meets it.

## Repeated evidence families and independence rules

Repeated URLs or documents from one work/publisher are useful corroborating detail, but must not be counted as independent outcome evidence.

| Evidence family | Repeated across | Independence treatment |
|---|---|---|
| GitHub official documentation/API/security family | SM-01–SM-08, SM-13–SM-14; ROS-01–ROS-10; several LIFE/DOM tracks | Unreviewed legacy candidate associations to vendor descriptions of primitives and stated limits; not verified current behavior or semantic support. Multiple GitHub pages are not independent proof that this composition is safe or effective. Target plan/tenant behavior must be probed. |
| Warp Factories official documentation/marketing/examples family | DOM-05; LIFE-01, LIFE-05–LIFE-07 | One first-party capability family. Marketing, docs, schema examples, and repeated quotations do not independently establish durability or outcomes. |
| METR task-horizon paper and METR explanatory blog | SM-10, SM-12, SM-14 and downstream reports/PLAN | **One canonical-work family**, as `PLAN.md` already states. The blog must not be counted as independent corroboration of the paper; the slowdown study is a distinct METR work but still shares publisher context. |
| SWE-bench ecosystem | SM-02, SM-07, SM-09, SM-13 | Base benchmark, Verified curation, leaderboards, and papers have related lineage. Independent audits such as SWE-bench+/SWE-rebench/UTBoost may challenge the family, but shared tasks/harnesses and author overlap must be recorded before counting families. |
| Coding-agent vendor docs and customer stories (Cognition/Devin, GitHub Copilot, OpenAI/Codex, Anthropic/Claude, OpenHands, Aider, SWE-agent) | SM-01–SM-04, SM-08–SM-10, SM-14; DOM-05 | Separate publisher/product families, but each vendor’s docs, benchmark, blog, and customer story remain first-party/selected legacy material. They are unreviewed candidate associations to claimed capability or deployment existence; they do not establish semantic support, verified current behavior, or representative effectiveness. |
| Durable-control primitives (PostgreSQL, Temporal, Kubernetes leases/controllers, transactional outbox literature) | SM-11; ROS-03–ROS-05, ROS-10; DOM-01, DOM-03–DOM-04; LIFE-02–LIFE-08 | The legacy inventory associates distinct primary-mechanism sources with individual semantics. Repeated appearance motivates an architecture inference only; semantic entailment remains unresolved and this is not empirical validation of the combined controller. |
| GitHub supply-chain controls, SLSA, OpenSSF/secure-use guidance, OIDC and artifact attestations | SM-04, SM-08; ROS-05–ROS-06, ROS-09–ROS-10 | Related standards/platform-control families. Count standards and platform implementations separately only for their own claims; neither proves the local pipeline is configured correctly. |
| OWASP/NIST-style agent and prompt-injection guidance | SM-08, ROS-06, LIFE-07–LIFE-08 | Risk taxonomy/guidance, not measured effectiveness. Repeated citations to pages within one standard are one family. |
| OpenTelemetry/W3C telemetry context family | SM-06, SM-12–SM-13; ROS-07–ROS-08, ROS-10; LIFE-04 | Candidate association with correlation/telemetry primitives only. Semantic entailment remains unresolved; the inventory does not prove RCA, dedupe, remediation, or improvement quality. |
| Observability/security/dependency vendor documentation (Sentry, Datadog, Dynatrace, PagerDuty, Renovate, Dependabot, scanners) | SM-05–SM-06; ROS-07; LIFE-04 | Treat each publisher as a capability family. Cross-vendor pages are not comparable outcome studies, and detector-specific grouping is not semantic incident identity. |
| LangGraph/OpenAI agent SDK and related framework docs | SM-02, SM-11; LIFE-02, LIFE-06–LIFE-07 | Candidate association with declared checkpoint/handoff behavior only. Semantic entailment remains unresolved; repeated docs do not turn framework state into audit, authorization, or durable business truth. |
| Organizational engineering/factory case studies | SM-10, DOM-05 | Often selected and first-party. Use as pattern or existence evidence; do not pool headline percentages without common denominators, task classes, baselines, and outcome definitions. |
| GTM vendor/product pages | DOM-01–DOM-04, especially DOM-02 | Capability-discovery families only. Multiple pages from one vendor do not establish compliant operation, causal revenue lift, or safe automation. |

## Synthesis disposition

The 37-track legacy inventory led to a narrower **architecture proposal** than “autonomous software factory”: build a repository-declared but controller-enforced proposal system; separate desired configuration, durable execution truth, and provider projections; keep workers replaceable and least-privileged; represent waits, decisions, effects, revisions, cleanup, and rollback explicitly; start read-only; and promote only bounded task classes using protected local evidence. The legacy structure does not semantically establish the external content or the availability of the listed primitives. Provenance and entailment remain unresolved. It does **not** validate the proposed end-to-end composition, its safety, its productivity, its ROI, universal numeric gates, broad GTM automation, or general recursive self-improvement.

Final `material-claims.json` regeneration is complete for the current digest recorded in that artifact. That editorial completion is separate from the future fresh immutable re-fetch and human semantic review, which remain a PRE-IMPLEMENTATION gate blocking Increment 1. Detailed per-source edge dispositions belong in that future immutable research run. This coverage map must not be used to inflate source count, erase contradictions, or convert an architecture proposal into a demonstrated local outcome.
