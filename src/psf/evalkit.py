"""Shared eval-harness helpers.

Used by BOTH the self-improvement eval suite (``selfeval``) and the eval
governance suite (``evalgov``), so their harness logic is implemented once.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

FACTORY_TEMPLATE = """schemaVersion: psf/v1
name: evalself
runner: mock
agents:
{agents}
gates:
  spec_approval: true
limits:
  max_attempts: {max_attempts}
"""


@dataclass
class EvalResult:
    id: str
    name: str
    status: str  # pass | fail
    detail: dict = field(default_factory=dict)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - m) / d), min(1.0, (c + m) / d))


def make_factory(root: Path, *, max_attempts: int = 2) -> Path:
    """Write a minimal valid factory into ``root`` and return the yml path."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "agents").mkdir(exist_ok=True)
    for r in ("triage", "spec", "implement", "verify", "review"):
        (root / "agents" / f"{r}.md").write_text("p")
    agents = "".join(f"  {r}: {{ prompt: agents/{r}.md }}\n"
                     for r in ("triage", "spec", "implement", "verify", "review"))
    (root / "factory.yml").write_text(FACTORY_TEMPLATE.format(agents=agents, max_attempts=max_attempts))
    return root / "factory.yml"


def make_eval_dir(root: Path, *, tasks: list[dict], holdout: list[dict] | None = None) -> Path:
    """Write a minimal protected eval directory and return it.

    Every seeded case carries provenance, as G1 requires of all active cases.
    """
    def _with_source(items: list[dict]) -> list[dict]:
        return [{**t, "source": t.get("source", "seed")} for t in items]

    d = Path(root) / "eval"
    d.mkdir(parents=True, exist_ok=True)
    (d / "tasks.json").write_text(json.dumps({"tasks": _with_source(tasks)}, indent=2) + "\n")
    (d / "thresholds.json").write_text(
        json.dumps({"metric": "pass_rate", "epsilon": 0.0, "n_min": 3}, indent=2) + "\n")
    if holdout is not None:
        (d / "holdout.json").write_text(json.dumps({"tasks": _with_source(holdout)}, indent=2) + "\n")
    return d
