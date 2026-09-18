"""Internal benchmark harness.

Compares two policies on the same task set at equal budget:

- **baseline**: one strong agent, no independent verification (a single
  implement attempt; if the artifact is wrong, the work is simply wrong).
- **factory**: the full loop with an independent verifier and bounded retries.

The point is not to beat a model. It is to show that the *process* catches
failures a single pass does not, and to keep that property under regression.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .agents import AgentResult, AgentTask, MockRunner
from .events import EventLog
from .foreman import Foreman
from .schema import Factory
from .state import Workflow

SOLVED = "SOLVED"


@dataclass
class BenchTask:
    name: str
    goal: str
    solves_on_attempt: int = 1  # implement succeeds on this 1-based attempt


class ScriptedRunner(MockRunner):
    """Deterministic runner where 'implement' succeeds only on a chosen attempt.

    This models the real observation that agents often fail the first try and
    get there on feedback.
    """

    def __init__(self, tasks: list[BenchTask]):
        self.by_goal = {t.goal: t for t in tasks}

    def run(self, task: AgentTask) -> AgentResult:
        if task.role == "implement":
            t = self.by_goal.get(task.goal)
            succeeds = t is None or (task.attempt + 1) >= t.solves_on_attempt
            ws = task.workspace or Path(tempfile.mkdtemp())
            ws.mkdir(parents=True, exist_ok=True)
            (ws / "artifact.txt").write_text(f"{SOLVED if succeeds else 'WRONG'}: {task.goal}\n")
            return AgentResult(True, {"artifact_digest": f"attempt-{task.attempt}", "path": "artifact.txt"},
                               summary=f"attempt {task.attempt} success={succeeds}")
        if task.role == "verify":
            ws = task.workspace
            ok = bool(ws) and (ws / "artifact.txt").read_text().startswith(SOLVED)
            return AgentResult(ok, {"passed": ok, "findings": [] if ok else ["artifact does not match spec"]})
        return super().run(task)


def _baseline(task: BenchTask, workdir: Path) -> bool:
    """One shot: a single implement attempt, then check the artifact."""
    runner = ScriptedRunner([task])
    ws = workdir / task.name
    ws.mkdir(parents=True, exist_ok=True)
    runner.run(AgentTask("implement", task.goal, workspace=ws, attempt=0))
    return (ws / "artifact.txt").read_text().startswith(SOLVED)


def _factory(task: BenchTask, workdir: Path, max_attempts: int) -> bool:
    factory = Factory(
        name="bench", schema_version="psf/v1", path=workdir / "factory.yml",
        runner="mock", gates={"spec_approval": False}, limits={"max_attempts": max_attempts},
    )
    log = EventLog(workdir / f"{task.name}.db")
    result = Foreman(factory, Workflow(log), ScriptedRunner([task])).run(task.goal, finish=False)
    return result.verify_passed


@dataclass
class BenchReport:
    total: int
    baseline_pass: int
    factory_pass: int
    details: list[dict] = field(default_factory=list)

    @property
    def baseline_rate(self) -> float:
        return self.baseline_pass / self.total if self.total else 0.0

    @property
    def factory_rate(self) -> float:
        return self.factory_pass / self.total if self.total else 0.0


def default_tasks() -> list[BenchTask]:
    return [
        BenchTask("easy-1", "add a health endpoint", 1),
        BenchTask("easy-2", "fix a typo in the docs", 1),
        BenchTask("easy-3", "rename a variable", 1),
        BenchTask("hard-1", "add CSV export", 2),
        BenchTask("hard-2", "fix the flaky retry test", 2),
        BenchTask("hard-3", "add pagination to the API", 2),
        BenchTask("hard-4", "handle the empty-state edge case", 2),
    ]


def stretch_tasks() -> list[BenchTask]:
    """Tasks that need more than the default retry budget — used to evaluate a
    candidate improvement (does raising the budget actually help?)."""
    return [
        BenchTask("s-easy", "add a health endpoint", 1),
        BenchTask("s-hard", "add CSV export", 2),
        BenchTask("s-deep-1", "add a database migration", 3),
        BenchTask("s-deep-2", "refactor the auth flow", 3),
        BenchTask("s-deep-3", "add rate limiting", 3),
    ]


def run_benchmark(tasks: list[BenchTask] | None = None, max_attempts: int = 2) -> BenchReport:
    tasks = tasks or default_tasks()
    report = BenchReport(total=len(tasks), baseline_pass=0, factory_pass=0)
    with tempfile.TemporaryDirectory(prefix="psf-bench-") as d:
        workdir = Path(d)
        for t in tasks:
            b = _baseline(t, workdir)
            f = _factory(t, workdir, max_attempts)
            report.baseline_pass += int(b)
            report.factory_pass += int(f)
            report.details.append({"task": t.name, "baseline": b, "factory": f})
    return report
