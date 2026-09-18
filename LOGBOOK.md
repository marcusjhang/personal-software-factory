# Logbook

Append-only record of what was actually done, newest last. One line per action
with its commit when committed. See `docs/DIARY.md` for the narrative and
reasoning; see `PLAN.md` / `docs/TECH-SPEC.md` for the intended design.

## 2026-09

- 09-18 — Repo renamed `agent-project-management` → `personal-software-factory`; history wiped to a clean root; plan + tech spec committed (`82e2a32`).
- 09-18 — Built M0 walking skeleton: canonical digest, hash-chained ledger, factory-as-code schema/compiler, closed-transition state machine with gates, mock + subprocess runners, foreman, worktree isolation, benchmark, CLI. `08b02d9`.
- 09-18 — Added `psf audit` (self health check) and governed improvement loop (`psf improve`: propose → offline eval → shadow → canary → human promote → rollback). Fixed a real bug the loop exposed: `max_attempts` was not persisted in the ledger. `2246612`.
- 09-18 — Added `psf metrics`; wired the audit as a promotion gate (health must be green to promote). `9431981`.
- 09-18 — Ran a research pass (Postgres locking, Kleppmann fencing, outbox, Temporal, Stripe idempotency, AWS jitter) to design M2.
- 09-18 — Wrote `LOGBOOK.md` and `docs/DIARY.md`; began M2 durability (leases/fencing, outbox, idempotency, retry classification).
- 09-18 — Implemented M2 durability from a research pass (Postgres locking, Kleppmann fencing, outbox, Temporal, Stripe, AWS jitter): atomic lease claim with monotonic epoch, fenced renew/release, transactional outbox, `UNKNOWN` reconciled-not-retried, idempotency same-key/different-bytes rejection, retry classification + full-jitter backoff. 8 durability tests. `a1abe0f`.
- 09-18 — Adopted **GitHub as the assumed host**; added `src/psf/github.py` (issue intake, push + draft-PR handoff) and `psf run --runner/--command/--github`.
- 09-18 — **Dogfooded a self-build**: ran the factory on this repository in a git worktree via the subprocess agent; produced branch `psf/W-7df7e359` with a real diff, 46 ledger events, chain verified, `DONE`. Demo worktree cleaned up after review.
- 09-18 — M3 **protected evaluation**: digest-pinned `eval/` (tasks + thresholds + manifest), non-inferiority gate (`ci_low >= -epsilon`, `n_scored >= n_min`, telemetry complete), wired as a promotion gate alongside the audit. M4 **outcome capture** (`psf outcome`, metrics) and **packaging** (Dockerfile, install.sh, .dockerignore). Test caught a real eval bug (read the one-shot baseline column); fixed. `223740a`, `694ba0a`.
- 09-18 — **Deep self-build with a real harness.** Pointed the runner at Claude Code (`scripts/psf_agent_claude.py`). The factory edited its own source (`src/psf/cli.py`, adding a `doctor` alias). The independent verifier **blocked** it for a missing acceptance test. Discovery: *implement was never given the spec*, so it could not satisfy acceptance — fixed in the foreman. Owner completed the test; the factory's edit was adopted. `cd3c497`.
- 09-18 — **Self-build #2 — end-to-end success.** With the foreman fix and Bash enabled for the harness, the factory (Claude runner) made a real change to its own source: added `--json` to `psf metrics` plus a test. Independent verification passed, work item `DONE` on the **first attempt**, 25/25 tests in the worktree. Owner reviewed and adopted the diff (discarding the agent's stray `uv.lock`). Pushed to GitHub (`main`). `999539a`.
- 09-18 — **Self-build #3.** Factory (Claude runner) added `--json` to `psf status` plus a test; `DONE` first attempt; 26/26 tests. Owner adopted and pushed. `6583820`.
- 09-18 — **Durability wired in (#1):** the foreman now takes a fenced lease per work item and refuses if held; the GitHub draft-PR is an idempotent outbox effect (reconcile-before-retry). 28/28 tests.
- 09-18 — **Improvement widened (#2):** multi-candidate search over an allow-list (`limits.max_attempts`; protected fields refused), best candidate chosen by offline eval then eval/audit/canary-gated. 30/30 tests.
- 09-18 — **Consumer feedback loop:** `psf feedback export|ingest|report`, privacy-filtered digests-only envelopes, GitHub issue template, `docs/FEEDBACK.md`. 32/32 tests. Pushed.
- 09-18 — README gained the diagram (Mermaid + rendered PNG in `docs/images/` + Excalidraw link); Excalidraw scene extended with the consumer feedback loop. Ran protected evals; `psf improve --promote` raised `limits.max_attempts` 2→3 through the gated loop (audit green, eval PROMOTE, human-authorized). Re-eval at the new baseline is non-inferior.
- 09-18 — **Eval plan + suite.** `docs/EVAL-PLAN.md`, `psf eval-suite` (process + verifier suites, Wilson CIs, findings with reproducibility), `docs/reports/`. Fixed an inverted verifier probability (my model bug). Findings F1–F3 validated across seeds.
- 09-18 — **Feedback→improvement round trip.** Validated F2 (single verifier ships residual defects). Implemented `gates.verify_quorum` **with the factory itself** (Claude harness); verifier blocked on brittle spec wording, owner adjudicated and adopted. Re-ran the eval: **shipped defects 17 → 1**, F2 resolved. New finding **F4**: the spec agent writes brittle acceptance criteria causing false-negative verification. See `docs/EVAL-REPORT.md`.
- 09-18 — **Self-improvement eval suite (Phase 1).** `psf eval-self` implements E2/E5/E6/E7/E10/E15/E16/E19 (proposal precision, gate denial, evaluator poisoning, rollback drill, invariant immutability, replay determinism, canary stop, non-regression) + `docs/EVAL-PLAN-SELF-IMPROVING.md`. **8/8 passed.**
- 09-18 — **Eval-driven fixes.** F2: enabled `verify_quorum: 2` by default (shipped defects **18 → 2** over 300 tasks, resolve rate unchanged). F4: rewrote `spec.md`/`verify.md` prompt (behavioral acceptance; cosmetic mismatches advisory) via the factory. Logged in `docs/EVAL-FINDINGS.md`; Excalidraw gained the evaluation program.
- 09-18 — **Round 2: eval set grown to 14 self-evals, run twice.** Added E1 (trajectory vs frozen control), E3 (held-out transfer), E4 (Goodhart divergence), E17 (forgetting), E18 (meta-improvement), E22 (F4 regression). First run flagged **F5**: proxy gains did not transfer to a holdout — fixed by adding a protected `eval/holdout.json` and a holdout non-inferiority gate in `run_eval`. Both self-eval (14/14) and process suites now run twice; audit green.
- 09-18 — **Round 3: self-eval set complete (22), factory declared READY.** Added E8/E9/E11/E12/E13/E14/E20/E21. Flagged **F6** (human burden inflated by non-actionable promotions) — fixed via `ImprovementResult.actionable` + "no action needed" signalling. Packaging verified (`pip install .` → `psf init` → run) and cold-start smoke test added as **E21**. **22/22 twice**, 37 tests, `docs/READY.md` written, README status updated, Excalidraw progress updated.
- 09-18 — **Eval governance.** Planned in `docs/EVAL-GOVERNANCE.md`; implemented `src/psf/evalkit.py` (shared harness, so the two suites share one implementation) and `src/psf/evalgov.py` (lifecycle: add/approve/rotate/retire; rules G1–G8; `run_governance_eval`). CLI: `psf evals add|approve|rotate|retire|status`, `psf eval-gov`. G5 flagged missing provenance in seeded cases → fixed (`make_eval_dir` + repo `eval/` cases now carry `source`). **Governance 8/8 · self-eval 22/22, run twice**; 39 tests; Excalidraw gained the governance section.











