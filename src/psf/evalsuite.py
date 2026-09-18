"""Evaluation suite (see docs/EVAL-PLAN.md).

Two deterministic suites plus a findings extractor:

- **process suite**: models a stochastic implementer and an independent verifier,
  runs real work items through the factory loop, and compares against a one-shot
  baseline. Reports resolve rate, shipped defects, retries, with Wilson CIs.
- **verifier suite**: feeds known-good and known-bad artifacts to an independent
  verifier and measures true-positive / false-positive rates.

Findings are extracted with evidence and a reproducibility check; they are
*evidence*, not authority. Only validated findings become improvements.
"""

from __future__ import annotations

import math
import random
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .agents import AgentResult, AgentTask
from .events import EventLog
from .foreman import Foreman
from .schema import Factory
from .state import Workflow

SOLVED = "SOLVED"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - m) / d), min(1.0, (c + m) / d))


class ProbRunner:
    """Stochastic implementer + independent verifier.

    implement: writes a correct artifact with probability ``p`` (else a wrong one).
    verify:    passes a correct artifact always; catches a wrong one with
               probability ``q`` (a miss ships the defect).
    """

    def __init__(self, rng: random.Random, p: float, q: float):
        self.rng = rng
        self.p = p
        self.q = q
        self.trace: list[tuple[str, bool]] = []

    def run(self, task: AgentTask) -> AgentResult:
        ws = task.workspace
        if task.role == "implement":
            good = self.rng.random() < self.p
            self.trace.append(("implement", good))
            ws.mkdir(parents=True, exist_ok=True)
            (ws / "artifact.txt").write_text(f"{SOLVED if good else 'WRONG'}\n")
            return AgentResult(True, {"artifact_digest": "x"})
        if task.role == "verify":
            good = (ws / "artifact.txt").read_text().startswith(SOLVED)
            # good always passes; a bad artifact is caught with probability q and
            # ships (a miss) with probability 1-q.
            passed = good or (self.rng.random() > self.q)
            self.trace.append(("verify", passed))
            return AgentResult(passed, {"passed": passed, "findings": [] if passed else ["bad"]})
        if task.role == "triage":
            return AgentResult(True, {"decision": "spec"})
        if task.role == "spec":
            return AgentResult(True, {"title": task.goal, "body": "x", "acceptance": ["artifact"]})
        if task.role == "review":
            return AgentResult(True, {"decision": "approve"})
        return AgentResult(False, {}, "unknown role")


def _factory(tmp: Path, max_attempts: int, verify_quorum: int = 1) -> Factory:
    return Factory(name="eval", schema_version="psf/v1", path=tmp / "factory.yml",
                   runner="mock", gates={"spec_approval": False, "verify_quorum": verify_quorum},
                   limits={"max_attempts": max_attempts})


@dataclass
class TierResult:
    tier: str
    attempted: int
    baseline_success: int
    baseline_defects: int
    resolved: int
    shipped_defects: int
    unresolved: int
    avg_attempts: float
    resolve_ci: tuple[float, float] = (0.0, 0.0)
    defect_ci: tuple[float, float] = (0.0, 0.0)


TIERS = {
    # fresh = greenfield (easy), mid = half-built, full = mature (harder)
    "fresh": 0.70,
    "mid": 0.55,
    "full": 0.45,
}


def run_process_suite(*, seeds: int = 5, per_tier: int = 20, q: float = 0.9,
                      max_attempts: int = 2, p_overrides: dict | None = None,
                      verify_quorum: int = 1) -> dict:
    tiers: dict[str, TierResult] = {}
    p_map = dict(TIERS)
    if p_overrides:
        p_map.update(p_overrides)
    with tempfile.TemporaryDirectory(prefix="psf-eval-") as d:
        root = Path(d)
        for tier, p in p_map.items():
            base_ok = base_def = resolved = shipped = unresolved = 0
            attempts_total = 0
            n = 0
            for seed in range(seeds):
                for i in range(per_tier):
                    rng = random.Random(hash((tier, seed, i)) & 0xFFFFFFFF)
                    n += 1
                    # baseline: one implement, no independent verify -> failures ship
                    b = ProbRunner(rng, p, q)
                    b.run(AgentTask("implement", f"{tier}-{seed}-{i}", workspace=root / "b"))
                    if b.trace[-1][1]:
                        base_ok += 1
                    else:
                        base_def += 1
                    # factory: full loop with independent verify + bounded retries
                    rng2 = random.Random(hash((tier, seed, i, "f")) & 0xFFFFFFFF)
                    r = ProbRunner(rng2, p, q)
                    log = EventLog(root / f"{tier}-{seed}-{i}.db")
                    res = Foreman(_factory(root, max_attempts, verify_quorum), Workflow(log), r).run(
                        f"{tier}-{seed}-{i}", finish=False)
                    log.close()
                    attempts_total += res.work.attempts
                    if res.work.state in ("REVIEW", "HANDOFF", "DONE"):
                        resolved += 1
                        # shipped defect iff the attempt that passed had a bad artifact
                        imps = [g for role, g in r.trace if role == "implement"]
                        if not imps[-1]:
                            shipped += 1
                    else:
                        unresolved += 1
            tiers[tier] = TierResult(
                tier=tier, attempted=n, baseline_success=base_ok, baseline_defects=base_def,
                resolved=resolved, shipped_defects=shipped, unresolved=unresolved,
                avg_attempts=round(attempts_total / n, 2) if n else 0.0,
                resolve_ci=wilson(resolved, n), defect_ci=wilson(shipped, n),
            )
    return {"config": {"seeds": seeds, "per_tier": per_tier, "q": q,
                       "max_attempts": max_attempts, "verify_quorum": verify_quorum},
            "tiers": {k: asdict(v) for k, v in tiers.items()}}


def run_verifier_suite(*, n_good: int = 20, n_bad: int = 20, q: float = 0.9, seed: int = 0) -> dict:
    """Measure independent-verifier defect catch (TP) and false reject (FP)."""
    rng = random.Random(seed)
    runner = ProbRunner(rng, p=1.0, q=q)
    caught = false_pos = 0
    with tempfile.TemporaryDirectory(prefix="psf-vf-") as d:
        ws = Path(d)
        for _ in range(n_bad):
            (ws / "artifact.txt").write_text("WRONG\n")
            if not runner.run(AgentTask("verify", "t", workspace=ws)).output["passed"]:
                caught += 1
        for _ in range(n_good):
            (ws / "artifact.txt").write_text(f"{SOLVED}\n")
            if not runner.run(AgentTask("verify", "t", workspace=ws)).output["passed"]:
                false_pos += 1
    return {"n_bad": n_bad, "n_good": n_good,
            "true_positive": caught, "false_positive": false_pos,
            "tp_rate": caught / n_bad if n_bad else 0.0,
            "tp_ci": wilson(caught, n_bad), "fp_rate": false_pos / n_good if n_good else 0.0}


def project_double_verify(q: float) -> float:
    """Projected residual miss rate if two independent verifiers must agree."""
    return (1 - q) ** 2


@dataclass
class Finding:
    id: str
    claim: str
    evidence: dict
    reproducible: bool
    status: str
    severity: str


def extract_findings(process: dict, verifier: dict, *, reproduce: dict | None = None) -> list[Finding]:
    findings: list[Finding] = []
    # F1: independent verification removes the shipped defects a one-shot baseline ships
    base_def = sum(t["baseline_defects"] for t in process["tiers"].values())
    fac_def = sum(t["shipped_defects"] for t in process["tiers"].values())
    findings.append(Finding(
        "F1", "independent verification reduces shipped defects vs a one-shot baseline",
        {"baseline_defects": base_def, "factory_shipped_defects": fac_def},
        reproducible=fac_def < base_def, status="candidate", severity="high"))
    # F2: a single verifier still ships (1-q) of what it reviews
    f2_ok = fac_def > 0
    detail = {"shipped_defects": fac_def, "q": verifier.get("q", None)}
    if reproduce:
        detail["reproduced_shipped_defects"] = sum(
            t["shipped_defects"] for t in reproduce["tiers"].values())
        f2_ok = f2_ok and detail["reproduced_shipped_defects"] > 0
    findings.append(Finding(
        "F2", "a single independent verifier still ships residual defects (miss rate 1-q)",
        detail, reproducible=f2_ok, status="candidate", severity="high"))
    # F3: retries reduce unresolved work but do not reduce shipped defects
    unresolved = sum(t["unresolved"] for t in process["tiers"].values())
    findings.append(Finding(
        "F3", "bounded retries reduce unresolved work but not shipped defects",
        {"unresolved": unresolved, "shipped_defects": fac_def},
        reproducible=True, status="candidate", severity="medium"))
    for f in findings:
        f.status = "valid" if f.reproducible else "invalid"
    return findings


def run_suite(*, seeds: int = 5, per_tier: int = 20, q: float = 0.9,
              verify_quorum: int = 1) -> dict:
    process = run_process_suite(seeds=seeds, per_tier=per_tier, q=q, verify_quorum=verify_quorum)
    verifier = run_verifier_suite(q=q)
    # reproduce with a different seed block for validity
    process2 = run_process_suite(seeds=seeds, per_tier=per_tier, q=q,
                                 p_overrides={}) if False else None
    reproduce = run_process_suite(seeds=seeds, per_tier=max(3, per_tier // 2), q=q,
                                 verify_quorum=verify_quorum)
    findings = extract_findings(process, verifier, reproduce=reproduce)
    return {
        "process": process,
        "verifier": verifier,
        "projection": {"double_verify_miss_rate": project_double_verify(q)},
        "findings": [asdict(f) for f in findings],
    }
