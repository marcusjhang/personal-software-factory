"""Work-item lifecycle: states, transitions, and enforced gates.

The controller is the only writer of lifecycle state. Agents propose; the
controller validates a transition against the closed transition table and its
guard, then appends an event. An illegal transition or failed guard raises
``GateError`` and changes nothing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .canonical import digest
from .events import EventLog

STATES: tuple[str, ...] = (
    "INTAKE", "TRIAGE", "SPEC", "SPEC_REVIEW", "READY", "BUILD", "VERIFY",
    "REVIEW", "HANDOFF", "DONE", "BLOCKED", "CANCELLED", "REJECTED",
)

TERMINAL = frozenset({"DONE", "CANCELLED", "REJECTED"})

# Closed transition table. No prose, wildcard, or inferred pair adds an edge.
TRANSITIONS: dict[str, tuple[str, ...]] = {
    "INTAKE": ("TRIAGE", "CANCELLED"),
    "TRIAGE": ("SPEC", "REJECTED", "BLOCKED", "CANCELLED"),
    "SPEC": ("SPEC_REVIEW", "BLOCKED", "CANCELLED"),
    "SPEC_REVIEW": ("READY", "SPEC", "BLOCKED", "CANCELLED"),
    "READY": ("BUILD", "BLOCKED", "CANCELLED"),
    "BUILD": ("VERIFY", "BLOCKED", "CANCELLED"),
    "VERIFY": ("REVIEW", "BUILD", "BLOCKED", "CANCELLED"),
    "REVIEW": ("HANDOFF", "BUILD", "BLOCKED", "CANCELLED"),
    "HANDOFF": ("DONE", "BLOCKED"),
    "BLOCKED": (),  # returns to the saved prior state only
}


class GateError(Exception):
    """Raised when a transition is illegal or a required gate does not pass."""


@dataclass
class WorkItem:
    id: str
    goal: str
    state: str = "INTAKE"
    spec: dict[str, Any] | None = None
    spec_digest: str | None = None
    approval_digest: str | None = None
    approval_actor: str | None = None
    artifact_digest: str | None = None
    attempts: int = 0
    max_attempts: int = 2
    verification: dict[str, Any] | None = None
    review: dict[str, Any] | None = None
    blocked_from: str | None = None
    transitions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "goal": self.goal, "state": self.state,
            "spec_digest": self.spec_digest, "approval_digest": self.approval_digest,
            "artifact_digest": self.artifact_digest, "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "verification": self.verification, "review": self.review,
            "transitions": self.transitions,
        }


class Workflow:
    """Deterministic controller over an :class:`EventLog`."""

    def __init__(self, log: EventLog):
        self.log = log

    # -- creation -------------------------------------------------------------

    def create(self, goal: str, work_id: str | None = None, *, max_attempts: int = 2) -> WorkItem:
        work_id = work_id or f"W-{uuid.uuid4().hex[:8]}"
        if self.log.for_work(work_id):
            raise GateError(f"work item {work_id} already exists")
        self.log.append("WorkCreated", {"goal": goal, "max_attempts": max_attempts},
                        work_id=work_id, actor="owner")
        return self.fold(work_id)

    # -- projection -----------------------------------------------------------

    def fold(self, work_id: str) -> WorkItem:
        events = self.log.for_work(work_id)
        if not events:
            raise GateError(f"unknown work item {work_id}")
        work: WorkItem | None = None
        for e in events:
            p = e.payload
            if e.type == "WorkCreated":
                work = WorkItem(id=work_id, goal=p["goal"], max_attempts=int(p.get("max_attempts", 2)))
            elif work is None:
                continue
            elif e.type == "SpecProduced":
                work.spec = p["spec"]
                work.spec_digest = p["digest"]
            elif e.type == "ApprovalRecorded":
                work.approval_digest = p["subject_digest"]
                work.approval_actor = p["approver"]
            elif e.type == "BuildCompleted":
                work.artifact_digest = p["artifact_digest"]
                work.attempts += 1
            elif e.type == "VerifyCompleted":
                work.verification = p
            elif e.type == "ReviewCompleted":
                work.review = p
            elif e.type == "StateChanged":
                work.state = p["to"]
                work.transitions.append(f"{p['from']}->{p['to']}")
                if p["to"] == "BLOCKED":
                    work.blocked_from = p["from"]
                elif p["from"] == "BLOCKED":
                    work.blocked_from = None
        assert work is not None
        return work

    # -- transitions ----------------------------------------------------------

    def transition(self, work: WorkItem, to: str, *, actor: str = "controller", reason: str = "") -> WorkItem:
        from_state = work.state
        if to == "BLOCKED":
            if from_state in TERMINAL or from_state == "BLOCKED":
                raise GateError(f"cannot block from {from_state}")
        elif from_state == "BLOCKED":
            if to != work.blocked_from:
                raise GateError(f"unblock must return to saved prior state {work.blocked_from}, not {to}")
        elif to not in TRANSITIONS.get(from_state, ()):
            raise GateError(f"illegal transition {from_state} -> {to}")

        self._check_guard(work, to)
        self.log.append(
            "StateChanged",
            {"from": from_state, "to": to, "reason": reason},
            actor=actor,
            work_id=work.id,
        )
        return self.fold(work.id)

    def _check_guard(self, work: WorkItem, to: str) -> None:
        if to == "READY":
            if not work.spec_digest:
                raise GateError("cannot become READY without a spec")
            if not work.approval_digest:
                raise GateError("cannot become READY without an approval")
            if work.approval_digest != work.spec_digest:
                raise GateError(
                    "approval is not bound to the current spec digest "
                    f"({work.approval_digest} != {work.spec_digest})"
                )

    # -- typed steps ----------------------------------------------------------

    def record_spec(self, work: WorkItem, spec: dict[str, Any], *, actor: str) -> WorkItem:
        d = digest(spec)
        self.log.append("SpecProduced", {"spec": spec, "digest": d}, actor=actor, work_id=work.id)
        return self.transition(self.fold(work.id), "SPEC_REVIEW", actor=actor, reason="spec drafted")

    def approve_spec(self, work: WorkItem, *, approver: str) -> WorkItem:
        if not work.spec_digest:
            raise GateError("no spec to approve")
        self.log.append(
            "ApprovalRecorded",
            {"subject_digest": work.spec_digest, "approver": approver},
            actor=approver, work_id=work.id,
        )
        return self.transition(self.fold(work.id), "READY", actor=approver, reason="spec approved")

    def request_spec_changes(self, work: WorkItem, *, actor: str, reason: str = "") -> WorkItem:
        return self.transition(work, "SPEC", actor=actor, reason=reason or "changes requested")

    def record_build(self, work: WorkItem, artifact_digest: str, *, summary: str = "", actor: str) -> WorkItem:
        self.log.append(
            "BuildCompleted",
            {"artifact_digest": artifact_digest, "summary": summary},
            actor=actor, work_id=work.id,
        )
        return self.transition(self.fold(work.id), "VERIFY", actor=actor, reason="build complete")

    def record_verification(self, work: WorkItem, passed: bool, *, findings: list[str], actor: str) -> WorkItem:
        self.log.append(
            "VerifyCompleted", {"passed": passed, "findings": findings}, actor=actor, work_id=work.id
        )
        work = self.fold(work.id)
        if passed:
            return self.transition(work, "REVIEW", actor=actor, reason="verification passed")
        if work.attempts < work.max_attempts:
            return self.transition(work, "BUILD", actor=actor, reason="verification failed; retry")
        return self.transition(work, "BLOCKED", actor=actor, reason="retry budget exhausted")

    def record_review(self, work: WorkItem, decision: str, *, notes: str = "", actor: str) -> WorkItem:
        self.log.append("ReviewCompleted", {"decision": decision, "notes": notes}, actor=actor, work_id=work.id)
        work = self.fold(work.id)
        to = "HANDOFF" if decision == "approve" else "BUILD"
        return self.transition(work, to, actor=actor, reason="review")

    def finish(self, work: WorkItem, *, actor: str = "owner") -> WorkItem:
        return self.transition(work, "DONE", actor=actor, reason="handed off")
