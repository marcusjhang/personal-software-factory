"""Agent runners.

A runner executes one specialist role against a bounded task and returns a
structured result. PSF is model-agnostic: swap ``mock`` for ``subprocess`` and
point ``command`` at any harness. The controller never trusts agent prose as
authority; it consumes only the typed result and enforces the gate.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from .canonical import digest_bytes


@dataclass
class AgentTask:
    role: str
    goal: str
    context: dict[str, Any] = field(default_factory=dict)
    workspace: Path | None = None
    attempt: int = 0
    feedback: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role, "goal": self.goal, "context": self.context,
            "workspace": str(self.workspace) if self.workspace else None,
            "attempt": self.attempt, "feedback": self.feedback,
        }


@dataclass
class AgentResult:
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "output": self.output, "summary": self.summary, "usage": self.usage}


class Runner(Protocol):
    def run(self, task: AgentTask) -> AgentResult:  # pragma: no cover - protocol
        ...


class MockRunner:
    """Deterministic offline runner for tests and benchmarks.

    The implement role writes a real artifact into the workspace and returns its
    digest. No network, no model.
    """

    def run(self, task: AgentTask) -> AgentResult:
        role = task.role
        if role == "triage":
            return AgentResult(True, {"decision": "spec", "scope": task.goal})
        if role == "spec":
            return AgentResult(True, {
                "title": task.goal,
                "body": f"Deliver: {task.goal}",
                "acceptance": ["artifact exists and matches the goal"],
            })
        if role == "implement":
            ws = task.workspace or Path(tempfile.mkdtemp())
            ws.mkdir(parents=True, exist_ok=True)
            content = f"goal={task.goal}\nattempt={task.attempt}\n".encode()
            (ws / "artifact.txt").write_bytes(content)
            return AgentResult(True, {"artifact_digest": digest_bytes(content), "path": "artifact.txt"},
                               summary=f"wrote artifact.txt on attempt {task.attempt}")
        if role == "verify":
            ws = task.workspace
            ok = bool(ws) and (ws / "artifact.txt").exists()
            return AgentResult(ok, {"passed": ok, "findings": [] if ok else ["artifact.txt missing"]})
        if role == "review":
            return AgentResult(True, {"decision": "approve", "notes": "looks good"})
        return AgentResult(False, {}, summary=f"unknown role {role}")


class SubprocessRunner:
    """Bring-your-own-agent runner.

    Serializes the :class:`AgentTask` as JSON on stdin and reads a JSON
    ``AgentResult`` (``{ok, output, summary}``) from stdout's last line.
    """

    def __init__(self, default_command: list[str] | None = None, timeout: int = 900):
        self.default_command = default_command
        self.timeout = timeout

    def run(self, task: AgentTask) -> AgentResult:
        command = task.context.get("command") or self.default_command
        if not command:
            raise RuntimeError("subprocess runner has no command configured")
        try:
            proc = subprocess.run(command, input=json.dumps(task.to_dict()),
                                  capture_output=True, text=True, timeout=self.timeout)
        except FileNotFoundError:
            return AgentResult(False, {}, summary=f"harness command not found: {command[0]}")
        except subprocess.TimeoutExpired:
            return AgentResult(False, {}, summary=f"harness timed out after {self.timeout}s")
        except OSError as e:  # noqa: BLE001 - never abort the loop on a runner failure
            return AgentResult(False, {}, summary=f"harness failed to start: {e}")
        if proc.returncode != 0:
            return AgentResult(False, {"returncode": proc.returncode}, summary=proc.stderr.strip()[:2000])
        try:
            data = json.loads(proc.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return AgentResult(False, {"raw": proc.stdout[:2000]}, summary="unparseable agent output")
        return AgentResult(
            ok=bool(data.get("ok", False)),
            output=data.get("output", {}) or {},
            summary=data.get("summary", ""),
            usage=data.get("usage", {}) or {},
        )


def build_runner(factory: Any) -> Runner:
    """Instantiate the runner named by the factory definition."""
    if factory.runner == "mock":
        return MockRunner()
    if factory.runner in ("subprocess", "cli"):
        cmd = factory.runner_options.get("command")
        timeout = int(factory.runner_options.get("timeout", 900))
        return SubprocessRunner(default_command=cmd, timeout=timeout)
    raise ValueError(f"unknown runner '{factory.runner}'")
