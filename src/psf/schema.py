"""Factory-as-code: load and validate a ``factory.yml`` definition.

The factory definition is the authored authority: which specialist agents exist,
which runner executes them, and the gate/limit policy. The compiler rejects
missing roles, dangling prompt files, and unknown keys rather than guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REQUIRED_ROLES = ("triage", "spec", "implement", "verify", "review")
SUPPORTED_SCHEMA = "psf/v1"
ALLOWED_TOP_KEYS = {
    "schemaVersion",
    "name",
    "description",
    "runner",
    "runnerOptions",
    "agents",
    "gates",
    "limits",
    "feedback",
}
ALLOWED_AGENT_KEYS = {"prompt", "command", "model", "description"}


class FactoryError(Exception):
    pass


@dataclass
class AgentSpec:
    role: str
    prompt: str = ""
    prompt_path: str | None = None
    command: list[str] | None = None
    model: str | None = None
    description: str = ""


@dataclass
class Factory:
    name: str
    schema_version: str
    path: Path
    runner: str = "mock"
    runner_options: dict[str, Any] = field(default_factory=dict)
    agents: dict[str, AgentSpec] = field(default_factory=dict)
    gates: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, Any] = field(default_factory=dict)
    feedback: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @property
    def max_attempts(self) -> int:
        return int(self.limits.get("max_attempts", 2))

    @property
    def spec_approval(self) -> bool:
        return bool(self.gates.get("spec_approval", True))

    def agent(self, role: str) -> AgentSpec:
        if role not in self.agents:
            raise FactoryError(f"factory '{self.name}' has no agent role '{role}'")
        return self.agents[role]


def load(path: str | Path) -> Factory:
    """Load and validate a factory definition from a file or directory."""
    p = Path(path)
    if p.is_dir():
        p = p / "factory.yml"
    if not p.exists():
        raise FactoryError(f"factory definition not found: {p}")
    raw = yaml.safe_load(p.read_text())
    errors = validate(raw, base_dir=p.parent)
    if errors:
        raise FactoryError("invalid factory definition:\n  - " + "\n  - ".join(errors))
    return _build(raw, p)


def _build(raw: dict[str, Any], path: Path) -> Factory:
    base = path.parent
    agents: dict[str, AgentSpec] = {}
    for role, spec in (raw.get("agents") or {}).items():
        spec = spec or {}
        prompt, prompt_path = "", spec.get("prompt")
        if prompt_path:
            fp = (base / prompt_path).resolve()
            prompt = fp.read_text() if fp.exists() else ""
        agents[role] = AgentSpec(
            role=role,
            prompt=prompt,
            prompt_path=prompt_path,
            command=spec.get("command"),
            model=spec.get("model"),
            description=spec.get("description", ""),
        )
    return Factory(
        name=raw["name"],
        schema_version=raw["schemaVersion"],
        path=path,
        runner=raw.get("runner", "mock"),
        runner_options=raw.get("runnerOptions") or {},
        agents=agents,
        gates=raw.get("gates") or {},
        limits=raw.get("limits") or {},
        feedback=raw.get("feedback") or {},
        description=raw.get("description", ""),
    )


def validate(raw: Any, *, base_dir: Path) -> list[str]:
    """Return a list of human-readable errors (empty means valid)."""
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ["top level must be a mapping"]

    unknown = set(raw) - ALLOWED_TOP_KEYS
    if unknown:
        errors.append(f"unknown top-level keys: {sorted(unknown)}")
    if raw.get("schemaVersion") != SUPPORTED_SCHEMA:
        errors.append(
            f"schemaVersion must be '{SUPPORTED_SCHEMA}', got {raw.get('schemaVersion')!r}"
        )
    if not raw.get("name"):
        errors.append("'name' is required")

    agents = raw.get("agents")
    if not isinstance(agents, dict) or not agents:
        errors.append("'agents' must be a non-empty mapping")
        return errors
    for role in REQUIRED_ROLES:
        if role not in agents:
            errors.append(f"missing required agent role '{role}'")

    for role, spec in agents.items():
        spec = spec or {}
        if not isinstance(spec, dict):
            errors.append(f"agent '{role}' must be a mapping")
            continue
        bad = set(spec) - ALLOWED_AGENT_KEYS
        if bad:
            errors.append(f"agent '{role}' has unknown keys: {sorted(bad)}")
        prompt = spec.get("prompt")
        if prompt and not (base_dir / prompt).resolve().exists():
            errors.append(f"agent '{role}' prompt not found: {prompt}")

    limits = raw.get("limits") or {}
    if "max_attempts" in limits and int(limits["max_attempts"]) < 1:
        errors.append("limits.max_attempts must be >= 1")
    gates = raw.get("gates") or {}
    if "spec_approval" in gates and not isinstance(gates["spec_approval"], bool):
        errors.append("gates.spec_approval must be a boolean")

    feedback = raw.get("feedback") or {}
    if not isinstance(feedback, dict):
        errors.append("feedback must be a mapping")
    else:
        if "upstream" in feedback and not isinstance(feedback["upstream"], str):
            errors.append("feedback.upstream must be a string (owner/repo)")
        if "publish" in feedback and not isinstance(feedback["publish"], bool):
            errors.append("feedback.publish must be a boolean")
        if "mode" in feedback and feedback["mode"] not in ("off", "hint", "auto"):
            errors.append("feedback.mode must be one of: off, hint, auto")
    return errors
