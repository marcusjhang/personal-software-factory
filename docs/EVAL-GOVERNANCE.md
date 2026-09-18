# Eval Governance — plan

How the eval suite is allowed to grow. The goal: the factory gets healthier as it
is used, without the system being able to grade its own homework.

## 1. Why govern

A self-improving factory is only as trustworthy as its eval. Ungoverned growth
produces Goodharting, leakage, evaluator poisoning, brittleness, and erosion
(see the risks in [EVAL-PLAN-SELF-IMPROVING.md](./EVAL-PLAN-SELF-IMPROVING.md)).
Governance makes growth safe.

## 2. The two tiers (never conflated)

| Tier | File | Role | who may change it |
|---|---|---|---|
| **Optimization set** | `eval/tasks.json` | candidates are proposed against it | human, via governed flow |
| **Protected holdout** | `eval/holdout.json` | *judges* candidates; never optimized on | human, via governed rotation only |
| Candidate cases | `eval/candidates.json` | proposed, not yet active | the capture step |
| Retired | `eval/retired.json` | quarantined, never deleted | the retire step |

A case is in exactly one tier. Optimization set and holdout must stay **disjoint**.

## 3. Lifecycle

```
capture            validate             approve                 rotate / retire
finding  ──▶  candidate case  ──▶  active (optimization)  ──▶  holdout  /  retired
(psf eval-add)   (eval/candidates)   (psf eval-approve)        (psf eval-rotate/retire)
   ▲                                                                     │
   └────────────────────── provenance + independent approval ───────────┘
```

1. **Capture** — a *validated* finding (reproduced, denominators/CIs) becomes a
   **candidate** case. Requires provenance (`source`). Never writes to the
   optimization set or holdout.
2. **Approve** — a human with a **different identity** than the author promotes a
   candidate into the optimization set. Self-approval is refused.
3. **Rotate** — periodically move some optimization cases into the holdout and
   refill from candidates, so the holdout stays honest and the proxy stays
   representative. Refuses self-approval.
4. **Retire** — quarantine (status `retired`), never delete; a reason is required.

## 4. Governance rules (enforced in code)

| id | rule |
|---|---|
| G1 | **Provenance required** — a case must name its source (`finding_id` / issue / spec). |
| G2 | **Separate approval** — the approver ≠ the author (distinct principal). |
| G3 | **Protected custody** — candidates and the system cannot edit `eval/`; digests are pinned. |
| G4 | **No leakage** — a case carries the behavior to check, not the fix/patch/answer; the holdout is never auto-updated. |
| G5 | **Rotation** — the holdout is refreshed from the optimization set on a schedule; the two stay disjoint. |
| G6 | **Retirement is quarantine** — cases are marked `retired`, never deleted; reason recorded. |
| G7 | **Expiry/review** — cases carry `created`/`expires`; expired cases must be re-validated. |
| G8 | **Isolation** — optimization ∩ holdout ∩ retired = ∅; integrity-checked. |

Change flow: `psf evals add → approve → rotate → retire`; eval changes are
protected config requiring an approver distinct from the code author.

## 5. Separation of duties

| Actor | May | Must not |
|---|---|---|
| Candidate (the system) | propose changes to config it is allowed to | write `eval/`, approve evals, promote itself |
| Finding capture | write **candidate** cases | touch active/holdout cases |
| Human approver | approve/rotate/retire evals, promote improvements | approve their own authored case (G2) |
| Protected store | hold digests, proofs | be edited outside the governed flow |

## 6. What we build

- `src/psf/evalgov.py` — lifecycle ops + governance checks (G1–G8) + a governance
  eval suite.
- `src/psf/evalkit.py` — shared harness helpers (factory fixture, eval-dir
  fixture, `EvalResult`, Wilson) used by **both** the self-eval suite and the
  governance suite, so their logic is not duplicated.
- CLI: `psf evals add|approve|rotate|retire|status`, and `psf eval-gov` to run
  the governance evals.
- Evals: `G1..G8` (governance) alongside `E1..E22` (self-improvement).

## 7. Failure modes guarded

Goodharting (holdout, G5) · leakage (G4) · poisoning (G3) · self-grading (G2) ·
erosion-by-deletion (G6) · staleness (G7) · tier confusion (G8).
