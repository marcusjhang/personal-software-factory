"""Supervisor — watch a long worker run and decide to continue/steer/stop/retry.

Adapted from the ``thruwire/foreman`` two-loop idea: a debounced assessment loop
asks a fast classifier narrow questions; a deterministic policy acts. The
classifier is advisory; the policy is code; every action is bounded and meant to
be recorded as a ledger event.

Safety-first ordering: human need → verification/FINISH → off-track → stuck →
continue. Uncertainty (below threshold) does nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .classifier import Classifier, Noul

DEFAULT_THRESHOLDS = {"needs_human": 0.80, "off_track": 0.80, "stuck": 0.80, "progress": 0.40}

QUESTIONS = {
    "worker_stuck": Noul("The worker is looping, repeatedly failing, or unable to make progress."),
    "work_off_track": Noul("The work has drifted from the original goal or is unrelated to it."),
    "meaningful_progress": Noul("The worker made meaningful progress on the goal since the last assessment."),
    "needs_human": Noul("Human judgment, credentials, clarification, or permission is required to proceed."),
}

ACTIONS = ("CONTINUE", "STEER", "STOP", "RETRY", "ESCALATE", "FINISH")


@dataclass
class SupervisorState:
    steers: int = 0
    retries: int = 0
    last_action: str | None = None
    verified: bool = False       # set only by the deterministic verifier, never by the classifier
    grace_elapsed: bool = False
    max_steers: int = 1
    max_retries: int = 1


@dataclass
class Decision:
    action: str
    reason: str
    answers: dict[str, Any] = field(default_factory=dict)


def evidence_bundle(*, goal: str, status: str, diff: str = "", output_tail: str = "",
                    events: list | None = None, redact: tuple[str, ...] = (),
                    max_diff: int = 20000, max_tail: int = 12000, max_events: int = 30) -> dict:
    """Bounded, redacted evidence. Never a repo dump; never secrets."""
    d = (diff or "")[:max_diff]
    t = (output_tail or "")[:max_tail]
    for secret in redact:
        if secret:
            d = d.replace(secret, "***")
            t = t.replace(secret, "***")
    return {"goal": goal, "status": status, "diff": d, "output_tail": t,
            "events": (events or [])[:max_events]}


def decide(answers: dict[str, Any], state: SupervisorState,
           thresholds: dict[str, float] | None = None) -> Decision:
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    def p(k: str) -> float:
        a = answers.get(k)
        return float(a.noul) if a is not None else 0.0

    # 1. human need dominates
    if p("needs_human") >= th["needs_human"]:
        return Decision("ESCALATE", "needs_human", answers)
    # 2. completion only when the deterministic verifier has passed
    if state.verified:
        return Decision("FINISH", "verified", answers)
    # 3. off-track
    if p("work_off_track") >= th["off_track"]:
        if state.steers < state.max_steers and state.last_action != "STEER":
            return Decision("STEER", "off_track", answers)
        return Decision("RETRY" if state.retries < state.max_retries else "STOP", "off_track", answers)
    # 4. stuck
    if p("worker_stuck") >= th["stuck"]:
        if state.steers < state.max_steers and not state.grace_elapsed:
            return Decision("STEER", "stuck", answers)
        return Decision("RETRY" if state.retries < state.max_retries else "STOP", "stuck", answers)
    # 5. otherwise keep going
    return Decision("CONTINUE", "progress" if p("meaningful_progress") >= th["progress"] else "observe", answers)


def supervise_step(classifier: Classifier, evidence: dict, state: SupervisorState,
                   thresholds: dict[str, float] | None = None) -> Decision:
    """One assessment. Fails closed: any classifier error means no intervention."""
    try:
        answers = classifier.ask(evidence, QUESTIONS)
    except Exception as e:  # noqa: BLE001 - fail closed
        return Decision("CONTINUE", f"fail_closed:{type(e).__name__}", {})
    return decide(answers, state, thresholds)
