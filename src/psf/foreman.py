"""The foreman: the orchestration loop.

Routes a goal through the lifecycle, delegating to specialist agents, while the
:class:`Workflow` controller enforces gates. The foreman never writes state
directly; it proposes steps the controller validates.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .agents import AgentTask, Runner, build_runner
from .schema import Factory
from .state import GateError, WorkItem, Workflow
from .workspace import Workspace

LEASE_TTL_SECONDS = 3600


@dataclass
class RunResult:
    work: WorkItem
    diff: str = ""
    verify_passed: bool = False
    findings: list[str] | None = None


class Foreman:
    def __init__(self, factory: Factory, workflow: Workflow, runner: Runner | None = None,
                 durability=None):
        self.factory = factory
        self.wf = workflow
        self.runner = runner or build_runner(factory)
        self.durability = durability  # optional Durability: lease + effect ledger

    def run(self, goal: str, *, work_id: str | None = None, approve: bool = True,
            repo: str | Path | None = None, use_git: bool = False, finish: bool = True) -> RunResult:
        work = self.wf.create(goal, work_id, max_attempts=self.factory.max_attempts)

        # Fenced lease: only one worker may advance a serialized work item.
        owner = f"psf-{os.getpid()}"
        epoch = None
        if self.durability is not None:
            epoch = self.durability.claim(work.id, owner, ttl=LEASE_TTL_SECONDS)
            if epoch is None:
                raise GateError(f"{work.id} is already leased by another worker")
        try:
            return self._run(work, goal, approve=approve, repo=repo, use_git=use_git, finish=finish)
        finally:
            if self.durability is not None and epoch is not None:
                self.durability.release(work.id, owner, epoch)

    def _run(self, work: WorkItem, goal: str, *, approve: bool, repo, use_git: bool,
             finish: bool) -> RunResult:
        work = self.wf.transition(work, "TRIAGE", actor="foreman")

        triage = self.runner.run(AgentTask("triage", goal))
        if not triage.ok or triage.output.get("decision") == "reject":
            work = self.wf.transition(work, "REJECTED", actor="foreman", reason="triage rejected")
            return RunResult(work)

        work = self.wf.transition(work, "SPEC", actor="foreman")
        spec_res = self.runner.run(AgentTask("spec", goal))
        spec = spec_res.output or {"title": goal}
        work = self.wf.record_spec(work, spec, actor="spec")

        # Gate: READY requires an approval bound to the spec digest.
        approver = "owner" if self.factory.spec_approval else "policy:auto"
        if self.factory.spec_approval and not approve:
            return RunResult(work)  # durable wait in SPEC_REVIEW
        work = self.wf.approve_spec(work, approver=approver)

        ws = Workspace.create(work.id, repo=repo, use_git=use_git)
        try:
            work = self.wf.transition(work, "BUILD", actor="foreman")
            findings: list[str] = []
            while True:
                build = self.runner.run(AgentTask(
                    "implement", goal, workspace=ws.path, attempt=work.attempts,
                    feedback=findings,
                    context={"spec": work.spec,
                             "acceptance": (work.spec or {}).get("acceptance", [])},
                ))
                work = self.wf.record_build(work, build.output.get("artifact_digest", ""),
                                            summary=build.summary, actor="implement")
                # Quorum: run the independent verifier N times; every run must pass.
                passed, findings = True, []
                for _ in range(self.factory.verify_quorum):
                    verify = self.runner.run(AgentTask("verify", goal, workspace=ws.path,
                                                       context={"spec": work.spec}))
                    passed = passed and bool(verify.output.get("passed", verify.ok))
                    for f in verify.output.get("findings", []) or []:
                        if f not in findings:
                            findings.append(f)
                work = self.wf.record_verification(work, passed, findings=findings, actor="verify")
                if work.state == "REVIEW":
                    break
                if work.state != "BUILD":
                    break  # BLOCKED: retry budget exhausted
            diff = ws.diff()
        finally:
            if not use_git:
                ws.cleanup()

        if work.state == "REVIEW":
            review = self.runner.run(AgentTask("review", goal, context={"artifact": work.artifact_digest}))
            decision = review.output.get("decision", "approve")
            work = self.wf.record_review(work, decision, actor="review")
            if work.state == "HANDOFF":
                self.wf.log.append("HandoffProduced", {"diff": diff[:16000]}, actor="foreman", work_id=work.id)
                if finish:
                    work = self.wf.finish(work)

        return RunResult(work, diff=diff,
                         verify_passed=bool(work.verification and work.verification.get("passed")),
                         findings=findings)
