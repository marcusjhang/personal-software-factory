# Evaluation Report — run 1 (baseline)

Companion to [EVAL-PLAN.md](./EVAL-PLAN.md). All numbers are from
`psf eval-suite`; raw JSON in `docs/reports/`.

## Config

- Suites: process (stochastic implementer + independent verifier) and verifier.
- Model: implement succeeds with `p` per tier (fresh 0.70, mid 0.55, full 0.45);
  verifier catches a bad artifact with `q = 0.9`.
- `max_attempts = 2`. Tiers: fresh (greenfield), mid (half-built), full (mature).
- Seeds: run 1 = 5×20/tier; run 2 (reproduce) = 8×25/tier.

## Results

Run 1 (5×20 per tier):

| tier | attempted | baseline good | baseline defects | resolved | factory shipped defects | unresolved | avg attempts |
|---|---|---|---|---|---|---|---|
| fresh | 100 | 70 | 30 | 87 | **3** | 13 | 1.32 |
| mid | 100 | 58 | 42 | 87 | **6** | 13 | 1.35 |
| full | 100 | 45 | 55 | 73 | **8** | 27 | 1.54 |

Run 2 (8×25 per tier, independent seeds — reproduction):

| tier | attempted | baseline defects | resolved | factory shipped defects | unresolved |
|---|---|---|---|---|---|
| fresh | 200 | 61 | 178 | **5** | 22 |
| mid | 200 | 98 | 175 | **12** | 25 |
| full | 200 | 117 | 155 | **19** | 45 |

Verifier: **TP 80%** (16/20, 95% CI 0.58–0.92), **FP 0%** (0/20) — no false
rejections of good artifacts.

## Validated findings

Validation rule (§5 of the plan): reproduce on a fresh run, report denominators,
predeclared thresholds, no confounds.

| id | claim | evidence | reproduced | status |
|---|---|---|---|---|
| **F1** | Independent verification cuts shipped defects vs a one-shot baseline. | baseline defects 127 vs factory 17 (run 1) | yes (run 2: 276 vs 36) | **valid** |
| **F2** | A single verifier still ships residual defects (miss rate `1-q`). | 17 shipped of 247 resolved; `q=0.9` | yes (36 shipped) | **valid** |
| **F3** | Bounded retries reduce unresolved work but not shipped defects. | unresolved falls, shipped defects persist | yes | **valid** |

**Interpretation.** The factory's core claim holds: independent verification
removes most defects a one-shot pass ships (F1). But it is **not** defect-free:
because the verifier can miss (`1-q`), every reviewed change carries residual
risk (F2), and **retries do not help** — each retry is another chance to ship a
missed defect (F3). This is the highest-severity actionable finding.

## Action (from validated F2)

**Change:** add independent **double verification** (`gates.verify_quorum`): when
set to 2, the verifier runs twice and both must pass before a change proceeds to
review.

**Projected effect:** miss rate goes from `1-q = 0.10` to `(1-q)² = 0.01` — a
~10× reduction in residual shipped defects, at the cost of a second verifier pass.

**Method:** implement it *with the factory itself* (dogfood), then re-run the
eval to confirm the effect and that nothing regressed.

## Run 3 — after the improvement (verify_quorum = 2)

Implemented by the factory via a real Claude harness; adopted by the owner.

| tier | attempted | baseline defects | resolved | shipped defects | unresolved | avg attempts |
|---|---|---|---|---|---|---|
| fresh | 100 | 41 | 88 | **0** | 12 | 1.34 |
| mid | 100 | 41 | 77 | **0** | 23 | 1.47 |
| full | 100 | 57 | 74 | **1** | 26 | 1.55 |

**Total shipped defects: 17 → 1** across the two runs (fresh/mid to zero). The
verifier is still imperfect (TP 80%) but agreeing double verification drives the
residual to `(1-q)² ≈ 0.01`, as projected. **F2 is now resolved** — it no longer
reproduces, so it is marked invalid. F1/F3 still hold; resolve rate is essentially
unchanged (the second verification costs a little, as expected), and unresolved
work rises slightly — the honest cost of the change.

## Validated finding F4 — from the dogfood run

| id | claim | evidence | status |
|---|---|---|---|
| **F4** | The spec agent writes **brittle acceptance criteria** (e.g. exact error-string wording, invented ledger fields), which causes **false-negative verification** that blocks correct work. | The quorum change was functionally correct and its tests passed, but the verifier blocked it 3× over "must be 'an integer 1 or 2'" (comma) and an unrequested ledger field. | **valid** |

F4 is a real factory defect: verification is only valuable if it is both
*independent* and *correctly specified*. The next improvement should make the
spec agent prefer behavioral acceptance criteria over exact strings/incidental
internals, and/or have the verifier treat cosmetic mismatches as advisory.

## Round-trip summary

```
eval (F1/F2/F3)  ->  validate (reproduce, seeds)  ->  propose (double verify)
   ->  build with the factory (dogfood)  ->  owner adopt  ->  re-eval (F2 resolved)
```

> Note: this is a self-eval by the authors; treat it as directional evidence,
> not independent validation. No ROI or safety claims are made.

