# Code Review — whole codebase

Method: Open Code Review **delegation mode** (`ocr delegate preview` + `ocr delegate
rule`, v1.12.6) for deterministic file selection and rule resolution; the review
itself was performed by the agent against the source. Range reviewed:
`82e2a32..HEAD` (all code added to this repo). Findings are ordered by severity;
High/Medium were **fixed and re-verified** (58 tests, all eval suites green).

## Coverage

- **In depth (line-by-line):** `state`, `events`, `durability`, `audit`, `schema`,
  `agents`, `workspace`, `adapters/common`, `evaluation`, `improve`, `foreman`,
  `classifier`, `supervisor`, `feedback`, `github`, `bench`, `canonical`,
  `calibrate`, `evalkit`.
- **Pattern-scanned** (targeted greps for `except`, missing `subprocess` timeouts,
  `assert` in library code, unchecked `int()/float()`, resource opens in loops):
  `cli`, `evalsuite`, `selfeval`, `evalgov`, `supveval`, `adaptereval`,
  `repobench`, `ossbench`, adapters, `scripts/*`.

## Findings

| id | severity | file | finding | status |
|---|---|---|---|---|
| H1 | **high** | `agents.py` | `SubprocessRunner.run` let `FileNotFoundError` (harness CLI absent), `TimeoutExpired`, and `OSError` propagate, aborting `Foreman.run` and leaving the work item mid-lifecycle with no event. | **fixed** — returns `AgentResult(ok=False)` for missing binary/timeout/OS error |
| H2 | **high** | `workspace.py` | `git worktree add -b psf/<id>` with `check=True` crashes if the branch already exists (e.g. re-running an aborted work id). | **fixed** — reuse an existing worktree; delete a stale branch before adding; timeout added |
| M1 | medium | `schema.py` | `int(limits["max_attempts"])` raised `ValueError/TypeError` on non-numeric input instead of a validation error (config crash). | **fixed** — explicit int/≥1 check (rejects bool) |
| M2 | medium | `adapters/common.py` | `tree_digest` read **every** file except `.git` — including `node_modules`, `.venv`, `.psf`, build output, and large binaries; slow and noisy on real repos. | **fixed** — prunes heavy/runtime dirs and files > 1 MB |
| M3 | medium | `events.py` | Ledger append is a non-atomic read-modify-write (`_last_hash()` then `INSERT`); concurrent writers can fork the chain. | **accepted** — single-process local use by design; documented (PostgreSQL/`BEGIN IMMEDIATE` is the planned fix) |
| M4 | medium | `classifier.py` | `JevClassifier.timeout` was stored but never used, so `timeout_s` config had no effect. | **fixed** — passed to the SDK client (with a fallback for older SDKs) |
| M5 | medium | `bench.py` | `_factory` opened an `EventLog` per task and never closed it — connection leak across a benchmark run. | **fixed** — `try/finally` close |
| L1 | low | `state.py`, `classifier.py` | `assert` used for control flow (`assert work is not None`, `assert self.kind == ...`) — stripped under `python -O`. | **fixed** — explicit `raise` |
| L2 | low | `adapters/common.py` | Module docstring still said "Claude Code and opencode" after Codex was added. | **fixed** |
| L3 | low | `github.py` | `_run` had no timeout → a hung `gh` could block indefinitely. | **fixed** — 180 s timeout |
| L4 | low | `improve.py` | `EventLog` is not closed if an exception other than the protected-field path is raised inside `run_improvement`. | **accepted** — CLI lifetime; noted |
| L5 | low | `feedback.py` | Imports the private `improve._factory_file` (layering smell). | **accepted** — small, internal |
| L6 | low | `schema.py` | `feedback.publish` is validated but unused (superseded by `feedback.mode`). | **accepted** — harmless back-compat key |

## Notes

- No injection/XSS/SQLi surface found: SQL uses parameterized statements; the only
  dynamic SQL is a static column list in `durability._set`.
- Secrets: adapters do not log prompts/env; `JevClassifier` reads the key from env
  and never persists it; feedback envelopes carry counts/digests only.
- Reproduced after fixes: **58 tests**, `psf audit` green, self 27/27, governance
  8/8, supervisor 16/16, adapters 8/8, process eval, 20/20 multi-repo.
