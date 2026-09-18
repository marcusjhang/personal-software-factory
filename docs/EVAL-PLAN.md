# Evaluation Plan

How we evaluate the personal software factory, what we will and will not claim,
and how eval findings become factory improvements (only after they are validated).

## 1. What we are evaluating

The factory is a **process shell** around a model. So we evaluate two different
things and never conflate them:

| | **Process correctness** | **Capability** |
|---|---|---|
| Question | Do the gates, verification, retries, ledger and handoff behave correctly? | Can it actually solve real tasks on real repos? |
| Runner | deterministic scripted runner | a real harness (Claude/Codex) |
| Grading | outcome states, gate behavior, verifier catch rate | tests pass (resolve rate) |
| Cost | cheap, runs at scale | expensive, small n |
| Risk | none | flakiness, contamination, cost |

## 2. Hypotheses (predeclared)

- **H1.** The factory's independent verification catches defective artifacts that
  a single pass would ship (verifier true-positive rate > 0) without rejecting
  good ones (false-positive rate low).
- **H2.** The factory resolves more tasks than a one-shot baseline at equal
  budget, because failure loops back to build within a bounded retry budget.
- **H3.** Gate integrity holds: no work item advances past a gate without a
  digest-bound approval; illegal transitions are refused.
- **H4.** Results degrade with repo maturity (fresh < mid < full difficulty), and
  localization is the dominant cost on larger repos.

These are **predeclared**; the thresholds are set before running.

## 3. Repo tiers (fixtures)

Fixtures are generated fresh each run and pinned by digest, so runs are
reproducible and there is no contamination.

| Tier | Fixture | Task shape |
|---|---|---|
| **Fresh** | empty repo | create a module + tests from a spec |
| **Mid** | partial package with a half-built feature and stale tests | complete/fix the feature, keep existing tests green |
| **Full** | complete small package, all tests green | add a feature with no regressions |
| **Large (design only)** | cal.com-scale OSS | see §6 |

## 4. Metrics and denominators

Always report the full funnel; never drop cases silently.

- attempted, applied, scored, resolved (and excluded, with reasons)
- **resolve rate** = resolved / scored, with a 95% CI (Wilson)
- **attempts** per resolved task, **retries**, **blocked**
- **verifier** true-positive (caught a real defect) and false-positive (rejected a
  good artifact) rates
- **interventions** (human touches), **cost proxy** (attempts × unit)
- **localization** (mid/full): was the right file touched (recall@1)

## 5. Validity checks (must pass or the finding is invalid)

1. Pinned fixture digest; deterministic seed.
2. Predeclared thresholds, fixed before the run.
3. n ≥ 3 seeds; report mean and CI, never best-of.
4. Denominators reported (attempted vs scored); exclusions logged with reasons.
5. No leakage: the checker is not readable by the implementer.
6. Reproduce: a finding must reproduce on a fresh run before it counts.
7. One variable at a time; freeze the harness between comparisons.
8. Timeouts/errors count as failures, not exclusions.

## 6. Large-repo evaluation (cal.com-scale) — design

You do not clone-and-run the world. Design:

- **Pin** base SHA + a **Docker image per task**; reproduce the exact test command.
- **Task selection**: draw from *merged fix PRs* where the issue does not contain
  the fix; require `FAIL_TO_PASS` to fail pre-patch and `PASS_TO_PASS` to be
  representative; **stratified sample**, e.g. n = 50 by module/difficulty.
- **Budgets**: cap tokens/$/wall per task; count timeouts as failures.
- **Flakiness**: run N no-op trials and quarantine flaky tests before scoring.
- **Score separately**: localization (recall@k of touched files) vs patch resolve;
  report $/task and p50/p95 latency.
- **Contamination**: decontaminate against model cutoffs; prefer fresh issues.
- This is a **design** here; the adapter interface is defined but not run in this
  repo's first eval pass.

## 7. From finding → improvement (validated only)

A raw eval observation is **not** an improvement. Each candidate finding is a
record:

```
Finding { id, claim, evidence (suite run + metrics), reproduce (run N), validity
          checks passed, severity, status: candidate|valid|invalid }
```

Rules:
- A finding is **valid** only if it reproduces and passes §5.
- Invalid or unreproducible findings are logged and **not** acted on.
- Only **valid** findings become improvement proposals, and those still pass the
  protected eval + self-audit + human promote (§8). Eval feedback is **evidence,
  not authority**.

## 8. Improvement loop (dogfooded)

For each valid finding:

1. Create a work item in this repo describing the fix.
2. Run it through the factory itself, with a real harness as the runner.
3. The factory's independent verifier checks it; the owner adopts or rejects.
4. Re-run the eval suite to confirm the finding moved (and nothing regressed).

So: **eval → validate → propose → build with the factory → verify → adopt →
re-eval.**

## 9. Threats to validity / what we will not claim

- Deterministic process evals measure the *mechanism*, not model quality.
- Capability evals here are tiny (small n, one harness) → directional only.
- The evaluator is not independent of the author (we are building both); this is
  a self-eval and is labelled as such.
- No production ROI, safety, or "self-improving" effect-size claims from this
  pass. Self-improvement remains human-gated and narrow.

## 10. Deliverables

- `psf eval-suite` — runs the process + verifier suites, writes a JSON report.
- `docs/EVAL-REPORT.md` — the run's results, validated findings, and actions.
- Findings that pass validation → factory self-builds (dogfood) → re-eval.
