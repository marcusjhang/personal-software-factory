# Real OSS-Repo Eval — report

The factory run against **large, mature, real codebases**, not generated fixtures.

## Repos (pinned SHAs, shallow-cloned)

| repo | files | language | SHA |
|---|---|---|---|
| **cal.com** | 7,708 | TS/TSX + SQL | `6bc4529` |
| **django** | 7,094 | Python | `862ade3` |
| **flask** | 236 | Python | `d73fa1c` |

## Tasks and grading

- **localization** — find the single file defining a symbol (ground truth computed
  from the repo with `git grep`); write its path to `ANSWER.txt`. Scores
  navigation on huge repos without a build.
- **change** — add a small, self-contained module + hermetic test at the repo root
  and make `pytest` pass. Real repo, real worktree, real env.
- Grading is deterministic (path match / pytest); the real Claude harness only
  implements, so verification is local.

Run: `psf eval-oss --repos "<path>:<kind>,..." --claude-script scripts/psf_agent_claude.py`

## Results

| run | flask change | django localization | django change | cal.com localization | resolved |
|---|---|---|---|---|---|
| before fix | BLOCKED | BLOCKED | BLOCKED | **HANDOFF** | 1/4 |
| after fix | **HANDOFF** | **HANDOFF** | **HANDOFF** | **HANDOFF** | **4/4** |

Notably, the localization on **cal.com (7.7k files)** and **django (7.1k files)**
resolved on the first attempt, and the result was correct.

## Finding F10 — the review step vetoed verified-correct work

| id | finding | evidence | fix |
|---|---|---|---|
| **F10** | On real repos the **review** agent returned "revise" even though the project's tests passed, blocking correct work (`BLOCKED`). The independent verification had already passed. | flask/django change and django localization blocked after `VERIFY -> REVIEW` with `verify passed=True`; OSS resolution 1/4 | Review is now **advisory**: it blocks only when it explicitly sets `blocking: true` *and* names the defect. Independent verification is the gate. **1/4 → 4/4.** |

Guarded by the same unit tests (empty revise not a blocker; always-revise with
`blocking: true` terminates `BLOCKED`) and eval **E27**.

## Honest limits

- Localization ground truth came from `git grep`; the agent was not asked to fix
  anything on cal.com (its toolchain is too heavy to build here).
- One task per repo; one harness (Claude). Not a leaderboard.
- We did **not** clone/run full test suites of the large repos; we used hermetic
  probes to isolate the factory's behaviour from each repo's build system.
