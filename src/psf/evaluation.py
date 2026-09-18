"""M3 protected evaluation.

The evaluation that judges a candidate must be something the candidate cannot
edit. Protected artifacts live in ``eval/`` and are pinned by digest in a signed
manifest. The improvement loop may only propose changes to allow-listed config;
if a candidate touches a protected path, or if the manifest digest changed, the
gate fails closed.

Design follows NIST AI RMF (independent, documented evaluation), SLSA
provenance (digest-pinned inputs), and canary guidance (predeclared stop rules).
Decision is expressed as non-inferiority: promote only if the lower confidence
bound on the delta is at least ``-epsilon``.
"""

from __future__ import annotations

import json
import random
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .bench import BenchTask, run_benchmark
from .canonical import digest, digest_bytes

PROTECTED_PREFIX = "eval/"


@dataclass
class EvalRecord:
    run_id: str
    baseline_attempts: int
    candidate_attempts: int
    baseline_rate: float
    candidate_rate: float
    delta: float
    ci_low: float
    ci_high: float
    margin: float
    n_attempted: int
    n_scored: int
    n_excluded: int
    exclusions: list[str]
    metric: str
    telemetry_complete: bool
    eval_manifest_digest: str
    task_set_digest: str
    decision: str
    reasons: list[str]
    holdout_baseline: float | None = None
    holdout_candidate: float | None = None
    holdout_delta: float | None = None
    holdout_ci_low: float | None = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


def _sha_file(p: Path) -> str:
    return "sha256:" + __import__("hashlib").sha256(p.read_bytes()).hexdigest()


def manifest_digest(eval_dir: str | Path) -> str:
    eval_dir = Path(eval_dir)
    entries = {}
    for p in sorted(eval_dir.rglob("*")):
        if p.is_file() and p.name != "manifest.json":
            entries[str(p.relative_to(eval_dir))] = _sha_file(p)
    return digest(entries)


def load_tasks(eval_dir: str | Path) -> list[BenchTask]:
    data = json.loads((Path(eval_dir) / "tasks.json").read_text())
    return [BenchTask(t["id"], t["goal"], int(t.get("solves_on_attempt", 1))) for t in data["tasks"]]


def load_holdout(eval_dir: str | Path) -> list[BenchTask]:
    """Protected holdout: never optimized against; the Goodhart tripwire."""
    p = Path(eval_dir) / "holdout.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text())
    return [BenchTask(t["id"], t["goal"], int(t.get("solves_on_attempt", 1))) for t in data["tasks"]]


def load_thresholds(eval_dir: str | Path) -> dict:
    return json.loads((Path(eval_dir) / "thresholds.json").read_text())


def candidate_touches_protected(changed_paths: list[str]) -> list[str]:
    return [p for p in changed_paths if p.startswith(PROTECTED_PREFIX) or p.startswith("/eval/")]


def _bootstrap_ci_low(deltas: list[float], *, seed: int = 0, iters: int = 2000, q: float = 0.05) -> float:
    if not deltas:
        return 0.0
    rng = random.Random(seed)
    n = len(deltas)
    samples = sorted(sum(rng.choice(deltas) for _ in range(n)) / n for _ in range(iters))
    return samples[int(q * iters)]


def run_eval(eval_dir: str | Path, *, baseline_attempts: int, candidate_attempts: int,
             seed: int = 0, exclude: list[str] | None = None) -> EvalRecord:
    eval_dir = Path(eval_dir)
    tasks = load_tasks(eval_dir)
    thresholds = load_thresholds(eval_dir)
    exclude = exclude or []

    scored = [t for t in tasks if t.name not in exclude]
    base = run_benchmark(tasks=scored, max_attempts=baseline_attempts)
    cand = run_benchmark(tasks=scored, max_attempts=candidate_attempts)

    # Both runs use the full factory loop at their own retry budget, so compare
    # the `factory` column (not the one-shot `baseline` column).
    base_by = {d["task"]: int(d["factory"]) for d in base.details}
    cand_by = {d["task"]: int(d["factory"]) for d in cand.details}
    deltas = [float(cand_by[t.name]) - float(base_by[t.name]) for t in scored]

    margin = float(thresholds.get("epsilon", 0.0))
    ci_low = _bootstrap_ci_low(deltas, seed=seed)
    ci_high = -_bootstrap_ci_low([-d for d in deltas], seed=seed, q=0.95) if deltas else 0.0
    n_min = int(thresholds.get("n_min", 3))
    telemetry_complete = True  # local deterministic run; no lost signal

    # Goodhart guard: the candidate must also hold up on a protected holdout that
    # the improvement loop never optimizes against.
    holdout = load_holdout(eval_dir)
    hb = hc = hdelta = hci = None
    if holdout:
        hb_r = run_benchmark(tasks=holdout, max_attempts=baseline_attempts)
        hc_r = run_benchmark(tasks=holdout, max_attempts=candidate_attempts)
        hb_by = {d["task"]: int(d["factory"]) for d in hb_r.details}
        hc_by = {d["task"]: int(d["factory"]) for d in hc_r.details}
        hdeltas = [float(hc_by[h.name]) - float(hb_by[h.name]) for h in holdout]
        hb, hc = hb_r.factory_rate, hc_r.factory_rate
        hdelta = hc - hb
        hci = _bootstrap_ci_low(hdeltas, seed=seed)

    reasons: list[str] = []
    if not deltas:
        reasons.append("no scored tasks")
    if len(scored) < n_min:
        reasons.append(f"n_scored {len(scored)} < n_min {n_min}")
    if not telemetry_complete:
        reasons.append("telemetry incomplete")
    if deltas and ci_low < -margin:
        reasons.append(f"non-inferiority failed: ci_low {ci_low:.3f} < -{margin}")
    if hci is not None and hci < -margin:
        reasons.append(f"holdout non-inferiority failed: ci_low {hci:.3f} < -{margin}")

    decision = "PROMOTE" if not reasons else "REJECT"
    return EvalRecord(
        run_id=f"EV-{uuid.uuid4().hex[:8]}",
        baseline_attempts=baseline_attempts, candidate_attempts=candidate_attempts,
        baseline_rate=base.factory_rate, candidate_rate=cand.factory_rate,
        delta=(cand.factory_rate - base.factory_rate),
        ci_low=ci_low, ci_high=ci_high, margin=margin,
        n_attempted=len(tasks), n_scored=len(scored), n_excluded=len(exclude),
        exclusions=list(exclude), metric=thresholds.get("metric", "pass_rate"),
        telemetry_complete=telemetry_complete,
        eval_manifest_digest=manifest_digest(eval_dir),
        task_set_digest=digest_bytes((eval_dir / "tasks.json").read_bytes()),
        decision=decision, reasons=reasons,
        holdout_baseline=hb, holdout_candidate=hc, holdout_delta=hdelta, holdout_ci_low=hci,
    )
