"""Personal Software Factory (PSF).

A repo-native, downloadable software factory. A foreman drives work through
INTAKE -> TRIAGE -> SPEC -> SPEC_REVIEW -> READY -> BUILD -> VERIFY -> REVIEW ->
HANDOFF, delegating to specialist agents, while a deterministic controller
enforces gates and records every transition in an append-only hash-chained
ledger. See PLAN.md and docs/TECH-SPEC.md.
"""

__version__ = "0.1.0"

from .canonical import canonical_bytes, digest  # noqa: F401
from .events import EventLog  # noqa: F401
from .schema import Factory, load as load_factory  # noqa: F401
from .state import WorkItem, Workflow, STATES, GateError  # noqa: F401

__all__ = [
    "__version__",
    "canonical_bytes",
    "digest",
    "EventLog",
    "Factory",
    "load_factory",
    "WorkItem",
    "Workflow",
    "STATES",
    "GateError",
]
