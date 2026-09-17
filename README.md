# Personal Software Factory

**A downloadable software factory you run inside your own repository.**

Install it once. In any repo, run `psf init`. Then tell it a goal — "add CSV export
to the metrics page" — and a **foreman** agent drives the work end to end:

```
intake → triage → spec → [your approval] → build → verify → review → handoff
```

Specialist agents do the work, an independent verifier checks it against the spec,
and you get a reviewable change (a diff or draft PR). Every step is written to a
durable, tamper-evident ledger, and the guardrails are enforced by code — not by
hoping the model follows the prompt.

It is model-agnostic. Bring your own agent harness (Claude Code, Codex, a local
script, anything that speaks the runner protocol). The factory owns the process;
you own the model.

- [PLAN.md](./PLAN.md) — the finalised product plan
- [docs/TECH-SPEC.md](./docs/TECH-SPEC.md) — the full technical specification

> Status: **specification**. This repo is the plan and tech spec for the product.
> No implementation ships from here yet.

---

## Why

Coding agents are good at editing files and bad at running a software process.
They forget decisions, skip verification, retry blindly, and declare victory on
unfinished work. A factory fixes the *process* around the model:

- **One durable process.** Intake, spec, approval, build, verify, review, handoff.
- **Enforced gates.** The controller refuses illegal transitions; a spec cannot
  go to build without an approval bound to its exact digest.
- **Independent verification.** The verifier is a different role with a different
  identity than the implementer, running against the frozen spec.
- **A real ledger.** Append-only and hash-chained, so you can inspect and replay
  exactly what happened.
- **Repo-native.** The factory lives in your repo as versioned config, not in
  someone else's cloud.

## What you get

```
your-repo/
├── factory/                  # factory-as-code (committed, reviewed)
│   ├── factory.yml           # roles, runner, gates, limits
│   ├── agents/*.md           # role prompts
│   └── policies/*.yml        # risk + gate policy (later)
└── .psf/                     # local runtime (gitignored)
    ├── factory.db            # append-only event ledger
    └── work/                 # isolated workspaces
```

## Quickstart

```bash
# install (any one of these)
uvx personal-software-factory init          # zero-install
pipx install personal-software-factory      # isolated install
docker run -v "$PWD:/repo" ghcr.io/<you>/personal-software-factory init

# in your repository
psf init                                     # scaffold factory/ + .psf/
psf validate                                 # compile-check the factory definition
psf run "add CSV export to the metrics page" # run one goal through the factory
psf status                                   # show work items + ledger state
```

## The factory loop

| Stage | Who | Gate / output |
|---|---|---|
| Intake | owner | `WorkCreated` |
| Triage | triage agent | scope, risk; may reject |
| Spec | spec agent | typed spec + acceptance criteria (digest-bound) |
| Spec review | **you** | approval bound to the exact spec digest |
| Build | implement agent | patch/artifact in an isolated workspace |
| Verify | verifier agent | pass/fail against the frozen spec, independent identity |
| Review | reviewer agent | approve or send back for another attempt |
| Handoff | owner | diff / draft PR for you to merge |

Failure loops back to Build within a bounded retry budget. Nothing merges or
deploys on its own.

## Design principles

1. **Agents propose; the controller decides.** No agent writes lifecycle state.
2. **Prompt text is never authority.** Gates are compiled and enforced in code.
3. **Everything is digest-bound.** Specs, approvals, artifacts, and events.
4. **Independent verification.** Different role, different identity.
5. **Bounded and reversible.** Budgets, retries, cancellation, cleanup.
6. **Bring your own model.** The runner is a small, documented interface.
7. **Local-first and private.** State stays in your repo; nothing phones home.

## Non-goals

- Not an autonomous software company. Humans hold spec approval and merge.
- Not a fleet/multi-tenant SaaS, not a universal workflow language, not a
  replacement for Git, GitHub, CI, or branch protection.
- Not a claim of unattended production readiness.

See [PLAN.md](./PLAN.md) for scope and milestones and
[docs/TECH-SPEC.md](./docs/TECH-SPEC.md) for the implementation contract.

## License

MIT — see [LICENSE](./LICENSE).
