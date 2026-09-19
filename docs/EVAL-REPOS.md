# Multi-Repo Capability Eval — report

The factory evaluated against **many repositories across sizes and domains**, in
two modes, with per-repo eval growth and self-improvement.

## Matrix

- **Sizes:** tiny (1 module), small (5), medium (20), large (60).
- **Domains:** cli, api, etl, lib, script.
- **Repos:** 4 × 5 = **20**, each a real git repo with code + tests and a task
  (add a feature module without breaking existing tests).
- Harness: `psf eval-repos` (`src/psf/repobench.py`) and
  `scripts/multi_repo_eval.py`.

## Modes

- **process** (deterministic): a reference solver applies the known-correct
  change; the project's tests grade it. Exercises the factory's plumbing
  (worktree, gates, verify, review, handoff, ledger) across 20 repo shapes.
- **real**: the Claude harness implements; the project's tests grade it.
  Small-n, slower, and — as it turned out — the best bug-finder.

## Results

| run | mode | repos | resolved |
|---|---|---|---|
| process matrix | deterministic | 20 | **20/20 (100%)** — tiny 5/5, small 5/5, medium 5/5, large 5/5 |
| real #1 | Claude | 4 (tiny/medium × cli/lib) | 1/4 (25%) |
| real #2 | Claude | 4 | 3/4 (75%) — after F8 fix |
| real #3 | Claude | 4 | 3/4 (75%) — variance |
| real #4 | Claude | 4 | **4/4 (100%)** — after F9 fix |

Per-repo **eval growth** ran for all 20 process repos: each repo's eval set grew
from its outcome under governance (`add → approve`), **integrity clean**, and the
self-improvement loop ran in each repo.

## Findings (found by this eval, all fixed)

| id | finding | evidence | fix |
|---|---|---|---|
| **F7** | Harness bug: generated repos had an empty `__init__` and unimported submodules, so the base tests errored. | all 20 repos BLOCKED at first run | base tests now `import app.modN` |
| **F8** | **Factory bug:** when the reviewer returned "revise", the foreman ended the run in `BUILD` and never re-implemented; review rejections were also not budget-bounded. | real runs ended `state=BUILD, attempts=1`; resolution 1/4 | foreman now loops build→verify→review until approval or `BLOCKED`; `record_review` respects the retry budget. **1/4 → 3/4.** |
| **F9** | **Factory robustness:** a reviewer returning a bare "revise" (no notes) blocked correct, verified work. Also the Claude adapter hardcodes role prompts and ignored the factory's `agents/*.md`, so prompt fixes did not reach it. | tiny-cli BLOCKED with two empty "revise" verdicts though tests passed | the factory now treats a non-actionable revise (no notes) as **approve** for any harness; review prompt/user contract requires concrete notes. **3/4 → 4/4.** |

Regression-guarded by: `E27` (review revise loops back), and unit tests for
empty-revise-not-a-blocker and always-revise-terminates-BLOCKED.

## Honest limits

- Real-mode n is small (4 repos) and the harness is stochastic — failure
  *location* varied run to run; the fixes raised the floor, not a guarantee.
- Domains are structurally similar (generated), not truly diverse codebases.
- A large real-world OSS repo (cal.com scale) is still only **designed**, not run
  (needs pinned SHA + Docker-per-task + stratified sampling).

## Reproduce

```bash
PYTHONPATH=src python3 -m psf.cli eval-repos --mode process --out docs/reports/repo-matrix-process.json
PYTHONPATH=src python3 scripts/multi_repo_eval.py --real --sizes tiny,medium --domains cli,lib \
  --claude-script scripts/psf_agent_claude.py --out docs/reports/multi-repo-real.json
```
