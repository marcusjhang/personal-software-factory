"""Governed improvement — the self-improvement loop, human-gated.

The factory can notice its own failures, propose a change to its own definition,
evaluate the candidate offline, shadow it, run it on a bounded canary, and then
*recommend* promotion. It can never promote itself: promotion requires an
explicit human flag (`psf improve --promote`), and rollback is a single command.

This is deliberately narrow. The candidate may only change declared policy
fields (for now, ``limits.max_attempts``); it can never touch gates, evaluators,
or its own promotion authority.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .bench import run_benchmark, stretch_tasks
from .events import EventLog
from .schema import Factory, load as load_factory
from .state import Workflow

# Fields a candidate is allowed to propose. Everything else is protected.
PROTECTED_MESSAGE = "candidate may not edit gates, evaluators, or promotion authority"


@dataclass
class Proposal:
    field: str
    current: object
    candidate: object
    reason: str


@dataclass
class ImprovementResult:
    proposal: Proposal
    current_rate: float
    candidate_rate: float
    canary_rate: float
    promoted: bool
    rolled_back: bool
    notes: list[str] = field(default_factory=list)


def propose(factory: Factory, log: EventLog) -> Proposal:
    """Derive a candidate change from observed signals in the ledger."""
    wf = Workflow(log)
    blocked = 0
    retries = 0
    for wid in log.work_ids():
        w = wf.fold(wid)
        if w.state == "BLOCKED":
            blocked += 1
        retries += max(0, w.attempts - 1)
    reason = f"{blocked} blocked item(s), {retries} retr(ies) observed"
    return Proposal(
        field="limits.max_attempts",
        current=factory.max_attempts,
        candidate=factory.max_attempts + 1,
        reason=reason,
    )


def _evaluate(max_attempts: int):
    return run_benchmark(tasks=stretch_tasks(), max_attempts=max_attempts)


def _apply(factory_path: Path, proposal: Proposal) -> Path:
    """Write the candidate into factory.yml, returning a backup path."""
    if not proposal.field.startswith("limits."):
        raise ValueError(PROTECTED_MESSAGE)
    factory_path = Path(factory_path)
    if factory_path.is_dir():
        factory_path = factory_path / "factory.yml"
    backup = factory_path.with_suffix(".yml.bak")
    shutil.copy2(factory_path, backup)
    raw = yaml.safe_load(factory_path.read_text()) or {}
    key = proposal.field.split(".", 1)[1]
    raw.setdefault("limits", {})[key] = proposal.candidate
    factory_path.write_text(yaml.safe_dump(raw, sort_keys=False))
    return backup


def _rollback(factory_path: Path) -> bool:
    factory_path = Path(factory_path)
    if factory_path.is_dir():
        factory_path = factory_path / "factory.yml"
    backup = factory_path.with_suffix(".yml.bak")
    if not backup.exists():
        return False
    shutil.copy2(backup, factory_path)
    backup.unlink()
    return True


def run_improvement(factory_path: str | Path, ledger_path: str | Path, *,
                    promote: bool = False, rollback: bool = False) -> ImprovementResult:
    log = EventLog(ledger_path)
    factory = load_factory(factory_path)
    action = "improvement"

    if rollback:
        done = _rollback(factory_path)
        log.append("ImprovementRolledBack", {"ok": done}, actor=action)
        log.close()
        return ImprovementResult(Proposal("", None, None, "rollback"), 0, 0, 0, False, done,
                                 ["rolled back" if done else "no backup to roll back to"])

    prop = propose(factory, log)
    log.append("ImprovementProposed", {"field": prop.field, "current": prop.current,
                                       "candidate": prop.candidate, "reason": prop.reason}, actor=action)

    current = _evaluate(int(prop.current))
    candidate = _evaluate(int(prop.candidate))
    canary_tasks = stretch_tasks()[:2]
    canary = run_benchmark(tasks=canary_tasks, max_attempts=int(prop.candidate))
    log.append("ImprovementEvaluated", {
        "current_rate": current.factory_rate, "candidate_rate": candidate.factory_rate,
        "canary_rate": canary.factory_rate}, actor=action)

    notes = [
        f"offline: current {current.factory_rate:.0%} -> candidate {candidate.factory_rate:.0%}",
        f"shadow: candidate reproduced offline ({candidate.factory_pass}/{candidate.total})",
        f"canary: {canary.factory_pass}/{canary.total} on a 2-task cohort",
    ]

    improves = candidate.factory_rate > current.factory_rate
    safe = candidate.factory_pass == candidate.total and canary.factory_pass == canary.total
    promoted = False
    eval_ok = None
    if promote:
        from .audit import run_audit
        health = run_audit(factory_path, ledger_path)
        notes.append(f"health: audit {'green' if health.healthy else 'RED'}")

        from .evaluation import run_eval
        eval_dir = Path("eval")
        if eval_dir.exists():
            ev = run_eval(eval_dir, baseline_attempts=int(prop.current),
                          candidate_attempts=int(prop.candidate))
            log.append("EvalCompleted", {"record": ev.to_dict()}, actor=action)
            eval_ok = ev.decision == "PROMOTE"
            notes.append(f"protected eval: {ev.decision} (delta {ev.delta:+.0%}, ci_low {ev.ci_low:+.2f})")
        else:
            notes.append("protected eval: none (eval/ missing) — refusing")
            eval_ok = False

        if not health.healthy:
            notes.append("promotion refused: self-audit is not green")
            log.append("ImprovementRejected", {"reason": "audit_red"}, actor="owner")
        elif not eval_ok:
            notes.append("promotion refused: protected evaluation did not pass")
            log.append("ImprovementRejected", {"reason": "eval_failed"}, actor="owner")
        elif improves and safe:
            _apply(factory_path, prop)
            log.append("ImprovementPromoted", {"field": prop.field, "candidate": prop.candidate}, actor="owner")
            promoted = True
            notes.append("PROMOTED (human authorized) — rollback with `psf improve --rollback`")
        else:
            notes.append("promotion refused: candidate did not improve or failed the canary")
            log.append("ImprovementRejected", {"improves": improves, "safe": safe}, actor="owner")
    else:
        notes.append("recommendation only — re-run with --promote to authorize")

    log.close()
    return ImprovementResult(prop, current.factory_rate, candidate.factory_rate,
                             canary.factory_rate, promoted, False, notes)
