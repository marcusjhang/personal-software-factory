"""Governed improvement — the self-improvement loop, human-gated.

Notices failures, proposes candidate changes to the factory's own definition,
evaluates them offline (protected evaluation), shadows/canaries the best, and
*recommends* promotion. It can never promote itself or touch protected fields:
promotion requires an explicit human flag and passes the audit + protected-eval
gates; rollback is one command.

Candidate space: an explicit allow-list of evaluable policy fields. Numeric
retry policy is what the offline benchmark can actually measure today; prompt
and model changes require the real-harness benchmark and are refused for now
rather than faked.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field as dc_field
from pathlib import Path

import yaml

from .bench import run_benchmark, stretch_tasks
from .events import EventLog
from .schema import Factory, load as load_factory
from .state import Workflow

# Only these fields may be proposed. Protected fields are refused outright.
PROPOSABLE = {"limits.max_attempts"}
PROTECTED = {"gates.spec_approval", "gates", "runner", "runnerOptions", "agents", "schemaVersion"}
MAX_ATTEMPTS_CAP = 5


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
    notes: list[str] = dc_field(default_factory=list)
    actionable: bool = False  # an improving, safe candidate exists -> human should decide


def _get(raw: dict, dotted: str):
    node = raw
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _factory_file(factory_path: str | Path) -> Path:
    p = Path(factory_path)
    return p / "factory.yml" if p.is_dir() else p


def propose_candidates(factory: Factory, log: EventLog) -> list[Proposal]:
    """Derive a small grid of candidate changes from observed signals."""
    wf = Workflow(log)
    blocked = sum(1 for wid in log.work_ids() if wf.fold(wid).state == "BLOCKED")
    retries = sum(max(0, wf.fold(wid).attempts - 1) for wid in log.work_ids())
    reason = f"{blocked} blocked item(s), {retries} retr(ies) observed"
    current = factory.max_attempts
    grid = sorted({min(current + d, MAX_ATTEMPTS_CAP) for d in (1, 2, 4)} - {current})
    grid = [g for g in grid if g > current]
    return [Proposal("limits.max_attempts", current, g, reason) for g in grid] or [
        Proposal("limits.max_attempts", current, current, "no candidate within cap")
    ]


def _evaluate(max_attempts: int):
    return run_benchmark(tasks=stretch_tasks(), max_attempts=max_attempts)


def _apply(factory_path: Path, proposal: Proposal) -> Path:
    if proposal.field in PROTECTED or proposal.field not in PROPOSABLE:
        raise ValueError(f"field '{proposal.field}' is protected and cannot be proposed")
    factory_path = Path(factory_path)
    if factory_path.is_dir():
        factory_path = factory_path / "factory.yml"
    backup = factory_path.with_suffix(".yml.bak")
    shutil.copy2(factory_path, backup)
    raw = yaml.safe_load(factory_path.read_text()) or {}
    *parents, leaf = proposal.field.split(".")
    node = raw
    for p in parents:
        node = node.setdefault(p, {})
    node[leaf] = proposal.candidate
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
                    promote: bool = False, rollback: bool = False,
                    field: str | None = None, candidate: object | None = None) -> ImprovementResult:
    log = EventLog(ledger_path)
    factory = load_factory(factory_path)
    action = "improvement"

    if rollback:
        done = _rollback(factory_path)
        log.append("ImprovementRolledBack", {"ok": done}, actor=action)
        log.close()
        return ImprovementResult(Proposal("", None, None, "rollback"), 0, 0, 0, False, done,
                                 ["rolled back" if done else "no backup to roll back to"])

    if field:
        if field in PROTECTED or field not in PROPOSABLE:
            log.append("ImprovementRejected", {"reason": "protected_field", "field": field}, actor=action)
            log.close()
            raise ValueError(f"field '{field}' is protected and cannot be proposed")  # noqa: B904
        current = _get(yaml.safe_load(_factory_file(factory_path).read_text()), field)
        candidates = [Proposal(field, current, candidate, "operator-specified")]
    else:
        candidates = propose_candidates(factory, log)

    evaluated = [(p, _evaluate(int(p.candidate))) for p in candidates]
    current = _evaluate(int(factory.max_attempts))
    # pick the best candidate, preferring the smallest change on a tie
    best_prop, best_report = max(evaluated, key=lambda pr: (pr[1].factory_rate, -int(pr[0].candidate)))

    log.append("ImprovementProposed", {
        "candidates": [{"field": p.field, "current": p.current, "candidate": p.candidate} for p, _ in evaluated],
        "chosen": {"field": best_prop.field, "candidate": best_prop.candidate},
    }, actor=action)

    canary = run_benchmark(tasks=stretch_tasks()[:2], max_attempts=int(best_prop.candidate))
    log.append("ImprovementEvaluated", {
        "current_rate": current.factory_rate, "candidate_rate": best_report.factory_rate,
        "canary_rate": canary.factory_rate}, actor=action)

    notes = [
        f"candidates: " + ", ".join(f"{p.candidate}" for p, _ in evaluated),
        f"offline: current {current.factory_rate:.0%} -> candidate {best_report.factory_rate:.0%}",
        f"canary: {canary.factory_pass}/{canary.total} on a small cohort",
    ]

    improves = best_report.factory_rate > current.factory_rate
    safe = best_report.factory_pass == best_report.total and canary.factory_pass == canary.total
    actionable = improves and safe
    promoted = False
    if not actionable and not promote:
        notes.append("no improving candidate — no human action needed")
    if promote:
        from .audit import run_audit
        from .evaluation import run_eval

        health = run_audit(factory_path, ledger_path)
        notes.append(f"health: audit {'green' if health.healthy else 'RED'}")
        eval_dir = Path("eval")
        if eval_dir.exists():
            ev = run_eval(eval_dir, baseline_attempts=int(factory.max_attempts),
                          candidate_attempts=int(best_prop.candidate))
            log.append("EvalCompleted", {"record": ev.to_dict()}, actor=action)
            eval_ok = ev.decision == "PROMOTE"
            notes.append(f"protected eval: {ev.decision} (delta {ev.delta:+.0%}, ci_low {ev.ci_low:+.2f})")
        else:
            eval_ok = False
            notes.append("protected eval: none (eval/ missing) — refusing")

        if not health.healthy:
            notes.append("promotion refused: self-audit is not green")
            log.append("ImprovementRejected", {"reason": "audit_red"}, actor="owner")
        elif not eval_ok:
            notes.append("promotion refused: protected evaluation did not pass")
            log.append("ImprovementRejected", {"reason": "eval_failed"}, actor="owner")
        elif improves and safe:
            _apply(factory_path, best_prop)
            log.append("ImprovementPromoted", {"field": best_prop.field, "candidate": best_prop.candidate}, actor="owner")
            promoted = True
            notes.append("PROMOTED (human authorized) — rollback with `psf improve --rollback`")
        else:
            notes.append("promotion refused: candidate did not improve or failed the canary")
            log.append("ImprovementRejected", {"improves": improves, "safe": safe}, actor="owner")
    else:
        notes.append("recommendation only — re-run with --promote to authorize")

    log.close()
    return ImprovementResult(best_prop, current.factory_rate, best_report.factory_rate,
                             canary.factory_rate, promoted, False, notes, actionable)
