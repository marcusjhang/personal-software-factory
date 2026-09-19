# Comparison — PSF vs other agent "software factories"

Structures compared from primary docs (fetched 2026-09-19):

- **Warp Factories** — <https://docs.warp.dev/factories/how-factories-work/>
- **Factory.ai (Droid / Software Factory)** — <https://docs.factory.ai/software-factory/overview>
- **GitHub Copilot cloud agent** — <https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent>
- **OpenHands** — <https://docs.all-hands.dev/usage/architecture/runtime>
- **Claude Code subagents** — <https://docs.anthropic.com/en/docs/claude-code/sub-agents>

## Structural comparison

| | **PSF (ours)** | **Warp Factories** | **Factory.ai** | **GitHub Copilot agent** | **OpenHands** | **Claude Code** |
|---|---|---|---|---|---|---|
| Core model | deterministic controller + advisory agents | foreman + stage agents (cloud) | Droid agents across SDLC automations | one cloud agent per task | agent runtime (action/observation) | subagents within a session |
| Lifecycle | closed states: intake→triage→spec→**approval**→build→verify→review→handoff | intake→triage→planning→(human)→building→reviewing→handoff | SDLC stages: triage·code-gen·validate·release·document·monitor | research→plan→branch→PR | event stream, no fixed SDLC | none (delegation) |
| Canonical state | **hash-chained ledger** + rebuildable projections | app-hosted, app-run history | dashboard/metrics | GitHub commits/logs | event stream | transcript |
| Gates/approvals | **digest-bound approval enforced in code** | spec/questions = prompt policy; merge by repo | autonomy & safety settings; merge by repo | repo rulesets/branch protection | n/a | permission modes |
| Verification | **independent verifier + quorum**, protected eval + holdout | review agent verdict **advisory** | Validate stage (review/security/QA) | code review / checks | test execution in sandbox | hooks |
| Isolation | git worktree (fs-level) | cloud run workspace | cloud/self-host | **GitHub Actions ephemeral env** | **Docker sandbox** | worktree (`isolation: worktree`) |
| Self-improvement | **propose→protected eval→shadow→canary→human promote→rollback**, audit+holdout-gated | scorers + follow-up PRs (human review) | agent effectiveness / automations | PR-lifecycle metrics | none | memory |
| Config-as-code | `factory/` (YAML + prompts), `AGENTS.md` | factory files in Git (agents/automations/runners/scorers) | AGENTS.md, skills, hooks, subagents, MCP | custom instructions/agents/hooks/skills/MCP | plugins | agents/skills/hooks/memory |
| Distribution | **local CLI, MIT, `psf init`** | cloud SaaS (Early Access) | app/CLI/cloud (Private Preview) | GitHub-hosted (paid plans) | OSS runtime | CLI |
| Multi-repo | one repo at a time | one factory = sized set of repos | many repos, coverage map | **one repo, one PR, one branch** | one workspace | many projects (user scope) |
| Limits | SQLite, not a security sandbox | Early Access, control plane theirs | Private Preview, enterprise | **59-min cap, no cross-repo** | not a factory | no gates/ledger |

## What we already match or exceed

- **Enforced gates + approvals** — they mostly use *prompt policy* (Warp: "the first two are workflow policy, written into the foreman's instructions"); we compile and enforce them, and bind approvals to exact spec digests.
- **Canonical, tamper-evident state** — a hash-chained ledger they don't expose.
- **Independent verification with a defect budget** — Warp's review is explicitly *advisory*; we gate on verifier quorum and measure shipped defects.
- **Governed self-improvement** — protected eval + protected holdout + non-inferiority + human promotion + rollback; Warp/Factory propose PRs, but don't disclose Goodhart/holdout governance.
- **Local-first, model-agnostic, downloadable** — they are cloud/SaaS (Warp/Factory Early/Private Preview; Copilot GitHub-only).

## What they have that we lack

- **OS/cloud isolation**: OpenHands runs in a **Docker sandbox**; Copilot uses **ephemeral GitHub Actions**; Warp/Factory use cloud compute. We use worktrees (fs-level only) — *the biggest structural gap*.
- **Integrations & intake**: Slack/Linear/Jira/GitLab, webhooks, MCP, plugins. We have GitHub intake + a feedback loop only.
- **Always-on service + dashboards**: 24/7 automation and SDLC coverage/metrics dashboards (Factory) vs our per-invocation CLI.
- **Shortest-path routing**: Warp's foreman skips stages when unnecessary and can start partway in; our lifecycle is fixed.
- **Harness customization breadth**: Factory/Copilot/Claude expose skills, hooks, custom agents, MCP servers, memory; we have prompts + a runner protocol.
- **Scale**: Fleet/multi-repo dashboards vs our single-repo, SQLite.

## What to borrow (concrete)

1. **Sandboxed workers** (OpenHands/Copilot model): run each work item in a container with an egress allowlist and resource caps. Closes our top gap.
2. **Stage shortest-path routing** (Warp): let the foreman skip triage/planning for well-specified work, still hitting all gates.
3. **Hooks + custom agents + skills** (Factory/Copilot/Claude): allow project-specific hooks (lint/security/notify) and specialized agent roles beyond the fixed five.
4. **SDLC coverage + metrics view** (Factory): a `psf metrics` dashboard over stages, pass rates, cycle time, cost — we already emit the data.
5. **Action/observation event model + deterministic image tags** (OpenHands): if we add containers, mirror their runtime-image hashing for reproducibility.
6. **Subagent context isolation + tool allowlists** (Claude Code): restrict each role's tools, not just its prompt.

## Where we deliberately differ

- We are a **deterministic process shell with a durable ledger**, not a cloud fleet. Our bet: *trustworthy, auditable, local, model-agnostic* beats *broad but opaque*.
- Nothing merges/deploys on its own; self-improvement is **human-gated by design**.
- We keep the eval as a **protected artifact with governance** — a place the industry is still weak.

## Sources

Warp Factories (`how-factories-work`); Factory.ai (`software-factory/overview`); GitHub
Copilot cloud agent (`about-coding-agent`); OpenHands (`usage/architecture/runtime`);
Claude Code (`sub-agents`). Fetched 2026-09-19; vendors' docs, not independent audits.
