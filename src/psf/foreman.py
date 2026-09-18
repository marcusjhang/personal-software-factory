"""The foreman: the orchestration loop.

Routes a goal through the lifecycle, delegating to specialist agents, while the
:class:`Workflow` controller enforces gates. The foreman never writes state
directly; it proposes steps the controller validates.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .agents import AgentTask, Runner, build_runner
from .schema import Factory
from .state import GateError, WorkItem, Workflow
from .workspace import Workspace


@dataclass
class RunResult:
    work: WorkItem
    diff: str = ""
    verify_passed: bool = False
    findings: list[str] | None = None


class Foreman:
    def __init__(self, factory: Factory, workflow: Workflow, runner: Runner | None = None):
        self.factory = factory
        self.wf = workflow
        self.runner = runner or build_runner(factory)

    def run(self, goal: str, *, work_id: str | None = None, approve: bool = True,
            repo: str | Path | None = None, use_git: bool = False, finish: bool = True) -> RunResult:
        work = self.wf.create(goal, work_id, max_attempts=self.factory.max_attempts)
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
                verify = self.runner.run(AgentTask("verify", goal, workspace=ws.path,
                                                   context={"spec": work.spec}))
                passed = bool(verify.output.get("passed", verify.ok))
                findings = list(verify.output.get("findings", []) or [])
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
