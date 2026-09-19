"""Adapter conformance evals (A1..A4).

Prove the harness seam is real and offline-testable: a stub harness that speaks
the runner protocol is driven through the actual SubprocessRunner and the full
foreman loop, and each harness's command is constructed correctly.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from .adapters import common
from .agents import SubprocessRunner, build_runner
from .evalkit import EvalResult, make_factory
from .events import EventLog
from .foreman import Foreman
from .schema import Factory
from .state import Workflow

STUB = '''\
import json, sys, pathlib, hashlib
task = json.load(sys.stdin); role = task["role"]; ws = pathlib.Path(task.get("workspace") or ".")
def emit(ok, output=None, summary=""):
    print(json.dumps({"ok": ok, "output": output or {}, "summary": summary})); sys.exit(0)
if role == "implement":
    ws.mkdir(parents=True, exist_ok=True); data = b"ok"; (ws / "artifact.txt").write_bytes(data)
    emit(True, {"artifact_digest": "sha256:" + hashlib.sha256(data).hexdigest()})
if role == "verify":
    ok = (ws / "artifact.txt").exists(); emit(ok, {"passed": ok, "findings": [] if ok else ["missing"]})
if role == "triage":
    emit(True, {"decision": "spec"})
if role == "spec":
    emit(True, {"title": task["goal"], "body": "x", "acceptance": ["artifact"]})
emit(True, {"decision": "approve"})
'''


def _stub(tmp: Path) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    p = tmp / "stub_harness.py"
    p.write_text(STUB)
    return p


def eval_A1(tmp: Path) -> EvalResult:
    """The protocol seam: a subprocess harness returns the typed result."""
    from .agents import AgentTask
    stub = _stub(tmp / "a1")
    (tmp / "a1").mkdir(parents=True, exist_ok=True)
    runner = SubprocessRunner(default_command=[sys.executable, str(stub)])
    res = runner.run(AgentTask("implement", "g", workspace=tmp / "a1work"))
    ok = res.ok and str(res.output.get("artifact_digest", "")).startswith("sha256:")
    return EvalResult("A1", "runner protocol over subprocess", "pass" if ok else "fail",
                      {"ok": res.ok, "digest": res.output.get("artifact_digest")})


def eval_A2(tmp: Path) -> EvalResult:
    """End to end: the full loop runs through a (stub) external harness."""
    root = tmp / "a2"
    make_factory(root, max_attempts=2)
    stub = _stub(root)
    factory = Factory(name="a2", schema_version="psf/v1", path=root / "factory.yml",
                      runner="subprocess", mode="yolo",
                      gates={"spec_approval": True, "verify_quorum": 1},
                      limits={"max_attempts": 2})
    log = EventLog(tmp / "a2.db")
    res = Foreman(factory, Workflow(log), SubprocessRunner(default_command=[sys.executable, str(stub)])).run(
        "stub goal", use_git=False)
    log.close()
    ok = res.work.state == "DONE" and res.verify_passed
    return EvalResult("A2", "full loop via external harness", "pass" if ok else "fail",
                      {"state": res.work.state, "verify": res.verify_passed})


def eval_A3(tmp: Path) -> EvalResult:
    """Each harness builds the correct command."""
    c = common.command("claude", "p", "/ws", "sonnet")
    o = common.command("opencode", "p", "/ws", "deepseek/deepseek-v4-pro")
    x = common.command("codex", "p", "/ws", "gpt-5-codex", out_file="/tmp/o.txt")
    ok = (c[0] == "claude" and "-p" in c and c[-2:] == ["--model", "sonnet"]
          and o[0] == "opencode" and "deepseek/deepseek-v4-pro" in o and "--auto" in o
          and x[:2] == ["codex", "exec"] and "--skip-git-repo-check" in x
          and x[-1] == "-" and "-o" in x and "-m" in x)
    return EvalResult("A3", "harness command construction", "pass" if ok else "fail",
                      {"claude": c[:3], "opencode": o[:3], "codex": x[:4]})


def eval_A4(tmp: Path) -> EvalResult:
    """Factory prompts reach the harness; unknown harnesses are rejected."""
    p = common.build_prompt({"role": "spec", "goal": "g", "context": {"prompt": "FACTORY SPEC POLICY"}})
    rejected = False
    try:
        common.command("nope", "p", "/ws", None)
    except ValueError:
        rejected = True
    ok = "FACTORY SPEC POLICY" in p and rejected
    return EvalResult("A4", "prompt passthrough + harness validation", "pass" if ok else "fail",
                      {"prompt_used": "FACTORY SPEC POLICY" in p, "unknown_rejected": rejected})


def eval_A5(tmp: Path) -> EvalResult:
    """One normalized permission profile maps consistently across harnesses."""
    cl_safe = common.command("claude", "p", "/ws", None, permissions="safe")
    cl_full = common.command("claude", "p", "/ws", None, permissions="full")
    cx_safe = common.command("codex", "p", "/ws", None, permissions="safe")
    cx_full = common.command("codex", "p", "/ws", None, permissions="full")
    op_safe = common.command("opencode", "p", "/ws", None, permissions="safe")
    op_ws = common.command("opencode", "p", "/ws", None, permissions="workspace")
    bad = False
    try:
        common.command("codex", "p", "/ws", None, permissions="nope")
    except ValueError:
        bad = True
    ok = ("default" in cl_safe and "--dangerously-skip-permissions" in cl_full
          and "read-only" in cx_safe and "--dangerously-bypass-approvals-and-sandbox" in cx_full
          and "--auto" not in op_safe and "--auto" in op_ws and bad)
    return EvalResult("A5", "permission profile mapping", "pass" if ok else "fail",
                      {"claude_safe": cl_safe[3:6], "codex_safe": cx_safe[-3:], "op_safe_auto": "--auto" in op_safe})


def eval_A6(tmp: Path) -> EvalResult:
    """Capability manifest advertises what each harness supports."""
    caps = {h: common.capabilities(h) for h in ("claude", "opencode", "codex")}
    ok = (caps["opencode"].get("acp") is True and "sandbox" in caps["codex"]
          and caps["claude"].get("approvals") == "prompt")
    return EvalResult("A6", "capability manifest", "pass" if ok else "fail", caps)


def eval_A7(tmp: Path) -> EvalResult:
    """Claude structured output: the {"result": ...} wrapper is unwrapped."""
    import json

    class FakeProc:
        returncode = 0
        stderr = ""
        stdout = json.dumps({"type": "result", "is_error": False,
                             "result": '{"passed": true, "findings": []}'})

    (tmp / "a7ws").mkdir(parents=True, exist_ok=True)
    task = {"role": "verify", "goal": "g", "workspace": str(tmp / "a7ws"), "context": {}}
    _, rc, out, _ = common.run_task(task, "claude", runner=lambda *a, **k: FakeProc())
    ok = out.strip().startswith('{"passed"')
    return EvalResult("A7", "claude structured-output unwrap", "pass" if ok else "fail", {"out": out[:80]})


def eval_A8(tmp: Path) -> EvalResult:
    """Codex: prompt on stdin (last arg '-'), model optional, output file wired."""
    c = common.command("codex", "p", "/ws", None, out_file="/tmp/o.txt")
    ok = (c[-1] == "-" and "-o" in c and "-m" not in c  # no model -> use codex default
          and "--skip-git-repo-check" in c)
    return EvalResult("A8", "codex stdin/output-file + optional model", "pass" if ok else "fail", {"cmd": c})


def run_adapter_eval() -> dict:
    evals = []
    with tempfile.TemporaryDirectory(prefix="psf-adapt-") as d:
        tmp = Path(d)
        for fn in (eval_A1, eval_A2, eval_A3, eval_A4, eval_A5, eval_A6, eval_A7, eval_A8):
            try:
                evals.append(fn(tmp))
            except Exception as e:  # noqa: BLE001
                evals.append(EvalResult(fn.__name__, fn.__name__, "fail", {"error": repr(e)}))
    passed = sum(1 for e in evals if e.status == "pass")
    issues = [{"id": e.id, "name": e.name, "detail": e.detail} for e in evals if e.status != "pass"]
    return {"passed": passed, "failed": len(evals) - passed, "total": len(evals),
            "evals": [{"id": e.id, "name": e.name, "status": e.status, "detail": e.detail} for e in evals],
            "issues": issues}
