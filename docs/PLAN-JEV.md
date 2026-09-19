# Plan — Jev + Supervisor in the Personal Software Factory

Status: **P0 + P1 implemented; P2–P4 planned.** Two goals:

1. **Use Jev** (TypeSafe's System One model) as the factory's fast, typed judgment
   layer — without ever letting it become authority.
2. Adopt the **live supervisor** idea from [`thruwire/foreman`](https://github.com/thruwire/foreman)
   (adapted, not copied) so long worker runs can be watched and steered.

Everything here respects the factory's existing invariants: the deterministic
controller is the sole writer of lifecycle state, model output is **advisory**,
approvals are digest-bound, and promotion is human-gated.

---

## 1. What Jev is (from TypeSafe's docs)

- Send a **state** + typed **questions**; get typed **answers**. No free text.
- Three primitives:
  | type | answers | returns |
  |---|---|---|
  | `Noul` | is this true? | `noul` (probability 0–1) |
  | `Choice` | which option? | `choice`, `probabilities`, `confidence` |
  | `Score` | which level? | `score`, `legend`, `probabilities`, `confidence` |
- **One call, many questions**, evaluated in parallel and in isolation; adding
  questions barely changes latency. Budget ≈ 32k tokens shared by state+questions.
- **Confidence** (Choice/Score) collapses the distribution; use it to act, confirm,
  or route to a human. Noul carries only the probability.
- Guidance: ask **atomic** questions (a few-seconds judgment), decompose complex
  judgments, compose answers in code; use **speculative fan-out** (ask questions
  you might ignore) and **confidence-gated** thresholds that scale with risk.
- SDK: `typesafe_sdk` (`TypeSafeClient` / `AsyncTypeSafeClient`), `system_one(state=…, questions=…)`,
  `TYPESAFE_API_KEY`, model `jev-latest`.

**Why it fits:** the factory already treats model output as untrusted signal and
makes decisions in code. Jev is exactly a *signal generator* for narrow judgments
("is this stuck?", "are tests sufficient?"), which is the safe way to use a model
here. It is not a reasoner and must not be asked to reason.

---

## 2. Where Jev plugs in (advisory only)

Every Jev answer recommends; the controller decides. Each use is one batched call.

| PSF stage | Questions (batched, speculative) | Type | Use |
|---|---|---|---|
| **Triage** | `is_out_of_scope`, `needs_clarification` | Noul | recommend reject / spec-first vs direct |
| | `ticket_kind` | Choice(feature,bug,chore,question) | route |
| | `risk_level` | Score(low,medium,high) | seed risk tier (human-confirmed) |
| **Spec readiness** | `spec_behavioral`, `acceptance_testable`, `acceptance_complete` | Noul | warn before SPEC_REVIEW |
| **Supervisor (during BUILD)** | `worker_stuck`, `work_off_track`, `meaningful_progress`, `looping`, `needs_human` | Noul | steer / stop / retry / escalate |
| **Verify/Review advisory** | `implementation_complete`, `tests_sufficient`, `requirements_satisfied`, `needs_independent_verification` | Noul | corroborate the verifier; flag low confidence |
| **Feedback/Improvement** | `feedback_looks_valid`, `failure_class` (flaky, spec_gap, capability, env) | Noul / Choice | cluster findings, suggest eval cases |
| **Eval advisory** | `finding_severity` | Score(low,medium,high) | prioritize findings (never decides promotion) |

**Hard rule:** Jev can never approve a spec, pass verification, promote an
improvement, edit `eval/`, or finish work. Those require the existing
deterministic gates and a human.

---

## 3. Architecture

```
                 ┌────────────────────────── controller (deterministic) ──────────────────────────┐
                 │  lifecycle · gates · ledger · protected eval · improvement · supervisor policy  │
                 └───────▲────────────────────────────▲───────────────────────────▲───────────────┘
                         │ advisory answers            │ interventions (events)    │ recommendations
                 ┌───────┴────────┐            ┌───────┴────────┐          ┌───────┴────────┐
                 │  Classifier     │            │  Supervisor     │          │  Improvement   │
                 │  (interface)    │            │  (from foreman) │          │  feedback      │
                 └───────▲────────┘            └───────▲────────┘          └────────────────┘
                         │                             │
            ┌────────────┴────────────┐   observe bounded evidence (diff, tails, git status, events)
       MockClassifier           JevClassifier
       (offline, deterministic)  (opt-in, TYPESAFE_API_KEY)
```

### 3.1 Classifier interface (`src/psf/classifier.py`)

```python
class Classifier(Protocol):
    def ask(self, state: dict, questions: dict[str, Q]) -> dict[str, Answer]: ...
```

- `MockClassifier` — deterministic rules; used by all evals so they stay offline.
- `JevClassifier` — builds one `system_one` request, batches all questions,
  validates answers to `[0,1]`, times out (default 10 s), retries 429/5xx with
  backoff, and never logs secrets.

### 3.2 Supervisor (`src/psf/supervisor.py`) — adapted from `thruwire/foreman`

- Wraps **one long-running worker** (our runner). While it runs, a debounced loop
  (floor 5 s, periodic 30 s) assembles bounded evidence and asks the classifier
  `{worker_stuck, work_off_track, meaningful_progress, needs_human, looping}`.
- A **deterministic Python policy** maps answers to actions, safety-first:
  `needs_human → ESCALATE` · iteration/timeouts → stop · stuck/off-track →
  steer once, then grace, then stop/retry · progress → continue. Thresholds are
  typed config, not model output.
- **Every intervention is a ledger event** (`SupervisorAssessed`,
  `WorkerSteered`, `WorkerStopped`, `WorkerRetried`, `Escalated`).
- Bounded: max steers/worker (default 1), grace period, retry cap, overall
  timeout. No oscillation (state tracks steers/verifications).
- HITL: `ESCALATE` stops and waits for a human. YOLO: policy may steer/stop/retry
  within budget, but **cannot FINISH** — completion still needs independent
  verification to pass.

### 3.3 Config (`factory.yml`)

```yaml
classifier:
  provider: mock          # mock | jev
  model: jev-latest
  timeout_s: 10
  min_interval_s: 5        # debounce
  supervisor:
    enabled: false          # opt-in; YOLO-friendly
    thresholds: {needs_human: 0.80, off_track: 0.80, stuck: 0.80, progress: 0.40}
    max_steers_per_worker: 1
    grace_s: 30
```

### 3.4 Optional: live steering transport

`thruwire/foreman` steers a **Codex App Server** turn (`turn/steer`). We add this
as an **optional runner capability** behind our worker protocol — used only when
the harness supports mid-turn guidance; otherwise the supervisor decides at step
boundaries (stop/retry). No core dependency on Codex types.

---

## 4. Safety invariants (non-negotiable)

1. **Advisory only.** Classifier output is a signal; the controller acts. No Jev
   answer can write state, approve, verify, promote, or finish.
2. **Uncertainty → escalate.** Low confidence (Choice/Score) or Noul near 0.5
   means "don't act": pause/escalate rather than guess.
3. **Fail closed.** Classifier timeout/error/rate-limit ⇒ no intervention, log it;
   never block the worker on a failed judgment.
4. **Bounded.** Every supervisor action is capped (steers, retries, timeouts).
5. **Auditable.** All state, questions, answers, thresholds, and interventions are
   recorded; the ledger stays canonical.
6. **Eval/protected config untouched.** Jev cannot influence `eval/`; Jev-based
   signals are themselves subject to our evals and governance.

---

## 5. Privacy and egress

- **Local-first default:** `provider: mock`; nothing leaves the machine.
- **Opt-in** `provider: jev` with an explicit `TYPESAFE_API_KEY`; treated as an
  allowlisted egress (like any other external call), recorded as an effect.
- **Redaction & bounding before send:** no secrets, no `.env`, no credentials, no
  raw customer data; bounded diff (e.g. 20k chars), output tails (12k), recent
  events (30) — mirroring `thruwire/foreman`'s limits.
- **Never** send raw repository dumps or full files beyond the evidence bundle.

---

## 6. Calibration and trust

Jev is unproven for these judgments; treat it like a scorer needing local calibration.

1. Record every `(state_digest, question, answer, confidence)` with the eventual
   **outcome** (worker actually stuck? verify failed? human accepted?).
2. Build a **confusion matrix / ROC per question**; choose thresholds to bound
   false positives (a wrong STOP is costlier than a missed steer).
3. **Abstain** below confidence; route to human (HITL) or continue (YOLO).
4. **Thresholds scale with risk** (TypeSafe guidance): high-stakes actions need
   higher confidence.
5. Re-calibrate on drift; publish the calibration as a protected artifact.

---

## 7. Cost, latency, limits

- One **batched** call per assessment (speculative fan-out); questions are cheap.
- Debounce (≥5 s) and periodic (30 s) assessment; assess on meaningful events.
- Timeout 10 s; retry 429/transient 5xx within the assessment window.
- Budget the assessment calls per work item; count them like other effects.

---

## 8. Evals (S-series) — added to the self-eval suite

| id | eval | checks |
|---|---|---|
| S1 | advisory-only | classifier can never approve/finish/promote; gates unchanged |
| S2 | mock determinism | supervisor decisions reproducible offline |
| S3 | stuck detection | stops a stuck worker, not a progressing one (mock) |
| S4 | bounded / no oscillation | steers/retries capped; no flip-flop |
| S5 | uncertainty handling | low confidence ⇒ no action / escalate |
| S6 | fail-closed | classifier error/timeout ⇒ no intervention |
| S7 | privacy | evidence bundle excludes secrets/`.env`; bounds respected |
| S8 | cost bound | assessment calls per item within budget |

These use the **MockClassifier**, so they run offline and deterministic; Jev is
exercised behind an opt-in integration test.

---

## 9. Phased roadmap

- **P0 — interface + mock + evals.** `classifier.py`, `MockClassifier`, ledger
  events, S1–S8. No Jev, no behaviour change. *(Offline; safe to ship.)*
- **P1 — Jev advisory (read-only).** `JevClassifier` for triage/spec/verify
  *recommendations*; nothing acts; answers recorded; calibration harness collects
  labels. Opt-in flag.
- **P2 — supervisor (mock policy first).** Watch long worker runs; steer/stop/retry
  bounded; HITL escalates; YOLO acts within budget. Still cannot FINISH.
- **P3 — optional live steering.** Codex App Server transport behind the runner
  protocol; reuse `thruwire/foreman`'s approach, not its persistence.
- **P4 — calibrated, confidence-gated routing.** Promote specific questions to
  advisory authority per risk tier after calibration evidence; keep human gates.

---

## 10. Risks / open questions

- **Calibration**: Jev accuracy for these judgments is unknown; false STOPs are
  the main risk → conservative thresholds, abstain, calibrate.
- **External dependency & privacy**: egress + cost + latency; keep opt-in and
  local-first; record as effects.
- **Protocol churn**: Codex App Server is experimental; keep the transport optional.
- **Over-trust**: the temptation to let Jev "decide" — forbidden by §4.
- **Token budget**: state+questions share ~32k tokens; bound evidence.

---

## 11. Relationship to `thruwire/foreman`

**Reuse the idea, not the code:** the two-loop supervisor (worker loop + debounced
assessment loop), the bounded evidence bundle, the deterministic safety-first
policy, and optional Codex App Server steering. **Do not** adopt its
`state.json`/`events.jsonl` persistence (we have a hash-chained ledger), make Jev
authority (it agrees: "Jev only assesses"), or couple the core to Codex types.

## 13. Progress

- **P0 — DONE.** `src/psf/classifier.py` (Noul/Choice/Score, `MockClassifier`,
  `ErrorClassifier`, `CountingClassifier`, `JevClassifier`, `build_classifier`);
  `src/psf/supervisor.py` (bounded+redacted evidence, questions, deterministic
  policy, fail-closed `supervise_step`); evals **S1–S8** in `src/psf/supveval.py`
  (`psf eval-supervisor`) — **8/8**, offline.
- **P1 — DONE.** `JevClassifier` verified against real TypeSafe Jev
  (`TYPESAFE_API_KEY` in env; `typesafe-sdk` in `.jev-venv`). One batched call
  returns typed answers and drives the supervisor (`CONTINUE`). Still advisory.
- **P2 — DONE.** Supervisor wired into the foreman build loop (`_supervise`):
  on a retry it assembles bounded evidence, asks the classifier, records
  `SupervisorAssessed`, and acts — `STEER` (guidance into the next attempt),
  `RETRY`, `STOP`/`ESCALATE` → `BLOCKED`. Enabled per factory/`--supervise`.
- **P3 — DONE as an interface.** Steering is delivered as guidance into the next
  attempt, plus an optional `runner.steer(msg)` hook for live mid-run transports
  (a Codex App Server adapter is the documented future transport; the core stays
  transport-agnostic).
- **P4 — DONE.** `src/psf/calibrate.py` + `psf calibrate` (threshold sweep,
  reliability/ECE, records derived from the ledger).
- **Evals:** **S1–S13 + C1–C3 (16/16)** offline via Mock; real Jev exercised
  through the foreman.

Real-Jev smoke (advisory only):

```
questions: worker_stuck, work_off_track, meaningful_progress, needs_human
answers:   0.16, 0.15, 0.77, 0.15      (one batched call)
decision:  CONTINUE
```

**F11 (finding):** with shallow evidence, real Jev judged failing attempts as
`CONTINUE` (did not flag stuck). The deterministic retry budget still blocked the
item — *advisory-only held*. Calibration (P4) plus richer evidence is the fix,
not letting Jev decide.


## 12. Deliverables / acceptance

- `src/psf/classifier.py` (interface + `MockClassifier`), `src/psf/supervisor.py`.
- `factory.yml` `classifier:` config; ledger events; CLI `psf supervise`/flags.
- Evals **S1–S8** green, twice; `psf audit` green; offline (mock) by default.
- Optional `JevClassifier` behind `provider: jev` with a calibration report.
- Docs: this plan + a `docs/JEV.md` usage/calibration page; Excalidraw updated.
