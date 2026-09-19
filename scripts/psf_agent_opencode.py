#!/usr/bin/env python3
"""opencode + DeepSeek runner adapter (BYO model).

Speaks the PSF runner protocol (AgentTask JSON on stdin -> AgentResult JSON on
stdout) by driving `opencode run` non-interactively in the task workspace. The
factory's per-role prompt (from factory/agents/*.md) is passed in the task
context and used as the system instruction.

Config (env):
- PSF_OPENCODE_BIN      (default: opencode)
- PSF_OPENCODE_MODEL    (default: deepseek/deepseek-flash)
- PSF_OPENCODE_TIMEOUT  (default: 900 seconds)

Usage:
  psf run --git --runner subprocess \
    --command "python3 /path/to/repo/scripts/psf_agent_opencode.py" "your goal"
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys

BIN = os.environ.get("PSF_OPENCODE_BIN", "opencode")
MODEL = os.environ.get("PSF_OPENCODE_MODEL", "deepseek/deepseek-flash")
TIMEOUT = int(os.environ.get("PSF_OPENCODE_TIMEOUT", "900"))


def emit(ok, output=None, summary=""):
    print(json.dumps({"ok": ok, "output": output or {}, "summary": summary}))
    sys.exit(0)


def last_json(text):
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def tree_digest(ws):
    files = {str(p.relative_to(ws)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in pathlib.Path(ws).rglob("*")
             if p.is_file() and ".git" not in p.parts}
    return "sha256:" + hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), list(files)


def build_prompt(task):
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
        parts.append('End with exactly one JSON line: {"decision":"approve"|"revise", "notes":"...", "blocking": true|false}.')
    elif role == "implement":
        parts.append("Make the smallest correct change in the current directory. Do not commit. "
                     "End with a line: SUMMARY: <one sentence>.")
    return "\n\n".join(parts)


def run_opencode(prompt, ws):
    cmd = [BIN, "run", "--model", MODEL, "--dir", ws, "--auto", prompt]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def main():
    task = json.load(sys.stdin)
    role = task["role"]
    ws = task.get("workspace") or os.getcwd()
    rc, out, err = run_opencode(build_prompt(task), ws)
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


if __name__ == "__main__":
    main()
