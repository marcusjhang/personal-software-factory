# Ready to use

Status: **usable on another project today.** This page is the short, honest
version: how to start, what has been proven, and what has not.

## Install & start (3 commands)

```bash
pipx install git+https://github.com/marcusjhang/personal-software-factory   # or: uv tool install ...
psf init            # scaffolds factory/ + .psf/ + AGENTS.md (asks about feedback)
psf run "your goal"
```

Point it at a real model (bring your own harness):

```bash
psf run --git --runner subprocess \
  --command "python3 scripts/psf_agent_claude.py" "your goal"
```

Everyday commands: `psf validate · run · status --json · audit · metrics --json ·
eval · eval-suite · eval-self · improve · feedback`.

## What is proven (and how)

| Claim | Evidence |
|---|---|
| Installs and runs as a package | `pip install .` → `psf --version`; cold-start in a fresh dir → `DONE` |
| Enforced gates, digest-bound approvals, hash-chained ledger | tests + `psf audit` green |
| Independent verification cuts shipped defects | process eval: 123 baseline defects → 18 (quorum 1) → **2** (quorum 2) / 300 tasks |
| Self-improvement works and is safe | `psf eval-self`: **27/27**, `psf eval-gov`: **8/8**, run twice |
| Works across repo sizes and domains | multi-repo eval: **20/20** (4 sizes × 5 domains); real-harness runs graded by tests |
| Change is reversible | rollback drill (E10), invariant immutability (E15) |
| It builds itself | three self-builds via a real harness; `verify_quorum` and prompt fixes were factory-built |

Test suite: **43 tests** (`PYTHONPATH=src pytest`). Eval plans and findings:
[EVAL-PLAN](./EVAL-PLAN.md), [EVAL-PLAN-SELF-IMPROVING](./EVAL-PLAN-SELF-IMPROVING.md),
[EVAL-FINDINGS](./EVAL-FINDINGS.md).

## Default safety posture

- `gates.spec_approval: true` — no build without a human approval bound to the spec digest.
- `gates.verify_quorum: 2` — the independent verifier runs twice; all must pass.
- Promotion is **human-authorized**; rollback is one command (`psf improve --rollback`).
- `feedback.mode: off | hint | auto` — privacy-filtered envelopes, opt-in, revocable.

## Point it at another project

1. `cd your-project && psf init` (choose feedback consent).
2. Commit `factory/` and `AGENTS.md`.
3. `psf run "<first goal>"`; review the handoff diff / draft PR.
4. Add tasks you care about to `eval/tasks.json` and a protected `eval/holdout.json`.
5. Periodically: `psf eval-self`, `psf eval-suite`, `psf audit`, `psf improve`.

## What is *not* proven (do not over-claim)

- Small samples, one harness, single machine; capability results are directional.
- This is a **self-eval** by the authors — not independent validation.
- No production ROI, uptime, or safety-certification claim.
- Improvement candidate space is narrow (numeric policy today); prompts/config
  are dogfooded by hand, not searched automatically.
- SQLite only; the PostgreSQL path is planned, not built.
