"""The foreman: the orchestration loop.

Routes a goal through the lifecycle, delegating to specialist agents, while the
:class:`Workflow` controller enforces gates. The foreman never writes state
directly; it proposes steps the controller validates.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .agents import AgentTask, Runner, build_runner
from .classifier import Classifier, build_classifier
from .schema import Factory
from .state import GateError, WorkItem, Workflow
from .supervisor import SupervisorState, evidence_bundle, supervise_step
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
                 durability=None, classifier: Classifier | None = None):
        self.factory = factory
        self.wf = workflow
        self.runner = runner or build_runner(factory)
        self.durability = durability  # optional Durability: lease + effect ledger
        self.classifier = classifier
        if self.classifier is None and factory.supervisor_enabled:
            self.classifier = build_classifier(factory.classifier)
        self._sup_state: SupervisorState | None = None

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

    def _role_prompt(self, role: str) -> str:
        try:
            return self.factory.agent(role).prompt or ""
        except Exception:  # noqa: BLE001 - optional; factories may omit roles
            return ""

    def _run(self, work: WorkItem, goal: str, *, approve: bool, repo, use_git: bool,
             finish: bool) -> RunResult:
        work = self.wf.transition(work, "TRIAGE", actor="foreman")

        triage = self.runner.run(AgentTask("triage", goal,
                                           context={"prompt": self._role_prompt("triage")}))
        if not triage.ok or triage.output.get("decision") == "reject":
            work = self.wf.transition(work, "REJECTED", actor="foreman", reason="triage rejected")
            return RunResult(work)

        work = self.wf.transition(work, "SPEC", actor="foreman")
        spec_res = self.runner.run(AgentTask("spec", goal, context={"prompt": self._role_prompt("spec")}))
        spec = spec_res.output or {"title": goal}
        work = self.wf.record_spec(work, spec, actor="spec")

        # Gate: READY requires an approval bound to the spec digest. In YOLO mode
        # the policy auto-approves; in HITL it needs the owner (or the flag).
        autonomous = self.factory.autonomous
        if self.factory.spec_approval and not autonomous and not approve:
            return RunResult(work)  # durable wait in SPEC_REVIEW
        approver = "policy:auto:yolo" if autonomous else (
            "owner" if self.factory.spec_approval else "policy:auto")
        work = self.wf.approve_spec(work, approver=approver)

        ws = Workspace.create(work.id, repo=repo, use_git=use_git)
        started = time.monotonic()
        budget = self.factory.max_minutes
        try:
            work = self.wf.transition(work, "BUILD", actor="foreman")
            findings: list[str] = []
            # One delivery cycle: build -> verify (quorum) -> review. A review that
            # requests changes loops back into build until it is approved or the
            # retry budget is exhausted (BLOCKED).
            while True:
                if budget and (time.monotonic() - started) > budget * 60:
                    findings.append(f"advisory: wall-clock budget {budget:g} min exceeded")
                    work = self.wf.transition(work, "BLOCKED", actor="foreman",
                                              reason="budget:max_minutes")
                    break
                while True:
                    build = self.runner.run(AgentTask(
                        "implement", goal, workspace=ws.path, attempt=work.attempts,
                        feedback=findings,
                        context={"spec": work.spec,
                                 "acceptance": (work.spec or {}).get("acceptance", []),
                                 "prompt": self._role_prompt("implement")},
                    ))
                    work = self.wf.record_build(work, build.output.get("artifact_digest", ""),
                                                summary=build.summary, actor="implement")
                    passed, findings = True, []
                    for _ in range(self.factory.verify_quorum):
                        verify = self.runner.run(AgentTask("verify", goal, workspace=ws.path,
                                                           context={"spec": work.spec,
                                                                    "prompt": self._role_prompt("verify")}))
                        passed = passed and bool(verify.output.get("passed", verify.ok))
                        for f in verify.output.get("findings", []) or []:
                            if f not in findings:
                                findings.append(f)
                    # Deterministic gate: run the project's own check (e.g. tests).
                    if self.factory.verify_command:
                        ok_cmd, out = self._run_verify_command(ws)
                        passed = passed and ok_cmd
                        if not ok_cmd:
                            findings.append(f"verify_command failed: {out[-300:]}")
                    work = self.wf.record_verification(work, passed, findings=findings, actor="verify")
                    if work.state == "BUILD" and self.classifier is not None:
                        work, findings = self._supervise(work, goal, ws, findings)
                    if work.state != "BUILD":
                        break  # REVIEW (verified) or BLOCKED (budget/supervisor)
                if work.state != "REVIEW":
                    break
                review = self.runner.run(AgentTask("review", goal,
                                                   context={"artifact": work.artifact_digest,
                                                            "spec": work.spec,
                                                            "prompt": self._role_prompt("review")}))
                decision = review.output.get("decision", "approve")
                notes = str(review.output.get("notes", "") or "").strip()
                blocking = bool(review.output.get("blocking", False))
                # Review is ADVISORY by default: it only blocks when it explicitly
                # sets blocking=true AND names the defect. Independent verification
                # is the gate; review cannot silently veto verified-correct work.
                if decision != "approve" and (not blocking or not notes):
                    findings.append(
                        "advisory: review requested changes without a blocking, actionable verdict; treated as approve")
                    decision = "approve"
                work = self.wf.record_review(work, decision, notes=notes, actor="review")
                if work.state != "BUILD":
                    break  # HANDOFF (approved) or BLOCKED (budget after revise)
            diff = ws.diff()
        finally:
            if not use_git:
                ws.cleanup()

        if work.state == "HANDOFF":
            self.wf.log.append("HandoffProduced", {"diff": diff[:16000]}, actor="foreman", work_id=work.id)
            if finish:
                work = self.wf.finish(work)

        return RunResult(work, diff=diff,
                         verify_passed=bool(work.verification and work.verification.get("passed")),
                         findings=findings)

    def _run_verify_command(self, ws: Workspace) -> tuple[bool, str]:
        """Run the deterministic project check (e.g. `pytest -q`) in the workspace."""
        cmd = self.factory.verify_command
        if not cmd:
            return True, ""
        try:
            p = subprocess.run(shlex.split(cmd), cwd=str(ws.path),
                               capture_output=True, text=True, timeout=600)
        except (OSError, subprocess.SubprocessError) as e:
            return False, f"verify_command error: {e}"
        return p.returncode == 0, ((p.stdout or "") + (p.stderr or "")).strip()

    def _supervise(self, work: WorkItem, goal: str, ws: Workspace, findings: list[str]) -> tuple[WorkItem, list[str]]:
        """Consult the advisory supervisor before a retry; record and act on it."""
        cfg = self.factory.supervisor_config
        if self._sup_state is None:
            self._sup_state = SupervisorState(
                max_steers=int(cfg.get("max_steers", 1)),
                max_retries=int(cfg.get("max_retries", 1)),
            )
        st = self._sup_state
        evidence = evidence_bundle(goal=goal, status=work.state, diff=ws.diff(),
                                   output_tail="; ".join(findings)[:2000],
                                   events=[f"attempt {work.attempts}"])
        d = supervise_step(self.classifier, evidence, st, cfg.get("thresholds"))
        self.wf.log.append(
            "SupervisorAssessed",
            {"action": d.action, "reason": d.reason,
             "answers": {k: getattr(v, "value", None) for k, v in (d.answers or {}).items()}},
            actor="supervisor", work_id=work.id)
        if d.action == "STEER":
            st.steers += 1
            st.last_action = "STEER"
            msg = f"supervisor: steer ({d.reason}) — address the verification findings"
            findings = findings + [msg]
            # optional live steering: a runner may support mid-run guidance
            if hasattr(self.runner, "steer"):
                try:
                    self.runner.steer(msg)  # type: ignore[attr-defined]
                except Exception:  # noqa: BLE001 - steering is best-effort, advisory
                    pass
            self.wf.log.append("WorkerSteered", {"steers": st.steers}, actor="supervisor", work_id=work.id)
        elif d.action == "RETRY":
            st.retries += 1
            st.last_action = "RETRY"
            self.wf.log.append("WorkerRetried", {"retries": st.retries}, actor="supervisor", work_id=work.id)
        elif d.action in ("STOP", "ESCALATE"):
            self.wf.log.append("WorkerStopped" if d.action == "STOP" else "Escalated",
                               {"reason": d.reason}, actor="supervisor", work_id=work.id)
            work = self.wf.transition(work, "BLOCKED", actor="supervisor", reason=f"supervisor:{d.reason}")
        return work, findings
