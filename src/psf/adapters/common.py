"""Shared runner-adapter core, harness-agnostic.

One implementation of the PSF runner protocol used by the Claude Code and
opencode (DeepSeek) backends. It builds the role prompt (using the factory's
`factory/agents/*.md` text passed in the task context), invokes the harness
non-interactively in the workspace, and returns the typed AgentResult.

Harnesses are selected by name; the command construction is the only difference.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

DEFAULT_MODEL = {
    "claude": "sonnet",
    "opencode": "deepseek/deepseek-flash",
    "codex": None,  # use the codex default model
}

# Tools the Claude harness may use (edits + running tests), no network surprises.
CLAUDE_TOOLS = ["Bash", "Edit", "Write", "Read", "Glob", "Grep"]
CLAUDE_READONLY_TOOLS = ["Read", "Glob", "Grep"]

PROFILES = ("safe", "workspace", "full")


def capabilities(harness: str) -> dict:
    """Advertised harness capabilities (mirrors ACP `initialize` negotiation)."""
    return {
        "claude": {"sandbox": "permission-modes", "approvals": "prompt",
                   "steering": False, "streaming": False, "acp": False},
        "opencode": {"sandbox": "none", "approvals": "auto",
                     "steering": False, "streaming": False, "acp": True},
        "codex": {"sandbox": "read-only|workspace-write|danger-full-access",
                  "approvals": "approve-for-me|bypass", "steering": False,
                  "streaming": True, "acp": False},
    }.get(harness, {})


def emit(ok, output=None, summary=""):
    print(json.dumps({"ok": ok, "output": output or {}, "summary": summary}))
    sys.exit(0)


def last_json(text: str):
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def tree_digest(ws: str):
    files = {str(p.relative_to(ws)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in pathlib.Path(ws).rglob("*")
             if p.is_file() and ".git" not in p.parts}
    return "sha256:" + hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), list(files)


def build_prompt(task: dict) -> str:
    """Compose the role prompt: factory prompt (if provided) + goal + context."""
    role = task["role"]
    goal = task["goal"]
    ctx = task.get("context") or {}
    base = (ctx.get("prompt") or "").strip() or f"You are the {role.upper()} agent in a software factory."
    parts = [base, f"Goal: {goal}"]
    if ctx.get("spec"):
        parts.append("Spec: " + json.dumps(ctx["spec"])[:2000])
    if ctx.get("acceptance"):
        parts.append("Acceptance: " + json.dumps(ctx["acceptance"])[:1500])
    if task.get("feedback"):
        parts.append("Prior feedback: " + "; ".join(map(str, task["feedback"]))[:1500])
    if role == "triage":
        parts.append('End with exactly one JSON line: {"decision":"spec"} (or "reject").')
    elif role == "spec":
        parts.append('End with exactly one JSON line: {"title": "...", "body": "...", "acceptance": ["..."]}.')
    elif role == "verify":
        parts.append('Inspect the current directory and end with exactly one JSON line: '
                     '{"passed": true|false, "findings": ["..."]}.')
    elif role == "review":
        parts.append('End with exactly one JSON line: '
                     '{"decision":"approve"|"revise", "notes":"...", "blocking": true|false}.')
    elif role == "implement":
        parts.append("Make the smallest correct change in the current directory. Do not commit. "
                     "End with a line: SUMMARY: <one sentence>.")
    return "\n\n".join(parts)


def command(harness: str, prompt: str, ws: str, model: str | None,
            out_file: str | None = None, permissions: str = "workspace") -> list[str]:
    if permissions not in PROFILES:
        raise ValueError(f"unknown permissions profile: {permissions}")
    if harness == "claude":
        if permissions == "full":
            cmd = ["claude", "-p", prompt, "--dangerously-skip-permissions",
                   "--output-format", "json"]
        else:
            mode = "acceptEdits" if permissions == "workspace" else "default"
            tools = CLAUDE_READONLY_TOOLS if permissions == "safe" else CLAUDE_TOOLS
            cmd = ["claude", "-p", prompt, "--permission-mode", mode, "--allowedTools", *tools,
                   "--output-format", "json"]
        if model:
            cmd += ["--model", model]
        return cmd
    if harness == "opencode":
        cmd = ["opencode", "run", "--dir", ws]
        if permissions in ("workspace", "full"):
            cmd += ["--auto"]
        cmd += ["--model", model or DEFAULT_MODEL["opencode"], prompt]
        return cmd
    if harness == "codex":
        if permissions == "full":
            cmd = ["codex", "exec", "--cd", ws, "--skip-git-repo-check",
                   "--dangerously-bypass-approvals-and-sandbox"]
        else:
            sandbox = "read-only" if permissions == "safe" else "workspace-write"
            cmd = ["codex", "exec", "--cd", ws, "--skip-git-repo-check", "--sandbox", sandbox]
        if model:
            cmd += ["-m", model]
        if out_file:
            cmd += ["-o", out_file]
        cmd += ["-"]  # prompt is read from stdin (last)
        return cmd
    raise ValueError(f"unknown harness: {harness}")


def run_task(task: dict, harness: str, *, model: str | None = None, timeout: int = 900,
             permissions: str = "workspace", runner=subprocess.run):
    ws = task.get("workspace") or os.getcwd()
    prompt = build_prompt(task)
    if harness == "codex":
        # codex reads the prompt from stdin and can write its last message to a file
        import tempfile
        fd, out_file = tempfile.mkstemp(prefix="psf-codex-", suffix=".txt")
        os.close(fd)
        try:
            cmd = command(harness, prompt, ws, model, out_file=out_file, permissions=permissions)
            p = runner(cmd, input=prompt, capture_output=True, text=True, timeout=timeout, cwd=ws)
            try:
                out = pathlib.Path(out_file).read_text().strip()
            except OSError:
                out = ""
            return ws, p.returncode, out or (p.stdout or "").strip(), (p.stderr or "").strip()
        finally:
            try:
                os.unlink(out_file)
            except OSError:
                pass
    cmd = command(harness, prompt, ws, model, permissions=permissions)
    p = runner(cmd, capture_output=True, text=True, timeout=timeout, cwd=ws)
    out = (p.stdout or "").strip()
    if harness == "claude":
        # `--output-format json` wraps the agent's final text in {"result": ...}
        try:
            wrapper = json.loads(out)
            if isinstance(wrapper, dict) and "result" in wrapper:
                out = str(wrapper["result"]).strip()
        except ValueError:
            pass
    return ws, p.returncode, out, (p.stderr or "").strip()


def handle(task: dict, harness: str, *, model: str | None = None, timeout: int = 900,
           permissions: str = "workspace") -> None:
    role = task["role"]
    ws, rc, out, err = run_task(task, harness, model=model, timeout=timeout, permissions=permissions)
    if role == "implement":
        digest, files = tree_digest(ws)
        emit(rc == 0, {"artifact_digest": digest, "files": files},
             out.strip().splitlines()[-1] if out.strip() else err[-200:])
    data = last_json(out)
    if role == "triage":
        emit(True, data or {"decision": "spec"}, out[-200:])
    if role == "spec":
        emit(True, data or {"title": task["goal"], "body": out[:500], "acceptance": []}, out[-200:])
    if role == "verify":
        passed = bool((data or {}).get("passed"))
        emit(passed, {"passed": passed, "findings": (data or {}).get("findings", [])}, out[-200:])
    if role == "review":
        emit(True, data or {"decision": "approve"}, out[-200:])
    emit(False, {}, f"unknown role {role}")


def main(harness: str, argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    model = None
    permissions = os.environ.get("PSF_PERMISSIONS", "workspace")
    timeout = int(os.environ.get("PSF_TIMEOUT", "900"))
    for i, a in enumerate(argv):
        if a in ("--model", "-m") and i + 1 < len(argv):
            model = argv[i + 1]
        if a == "--timeout" and i + 1 < len(argv):
            timeout = int(argv[i + 1])
        if a == "--permissions" and i + 1 < len(argv):
            permissions = argv[i + 1]
    if model is None:
        model = os.environ.get("PSF_MODEL") or None
    task = json.load(sys.stdin)
    handle(task, harness, model=model, timeout=timeout, permissions=permissions)
