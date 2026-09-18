#!/usr/bin/env python3
"""Real bring-your-own-agent adapter: Claude Code via `claude -p`.

Speaks the PSF runner protocol (AgentTask JSON on stdin -> AgentResult JSON on
stdout) and drives Claude Code non-interactively in the task workspace. This is
the path from "the process works" to "the factory actually changes code".
"""
import hashlib
import json
import pathlib
import subprocess
import sys

TIMEOUT = 900


def emit(ok, output=None, summary=""):
    print(json.dumps({"ok": ok, "output": output or {}, "summary": summary}))
    sys.exit(0)


def ask(prompt, cwd):
    p = subprocess.run(
        ["claude", "-p", prompt,
         "--permission-mode", "acceptEdits",
         "--allowedTools", "Bash", "Edit", "Write", "Read", "Glob", "Grep",
         "--output-format", "text"],
        cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT,
    )
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


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


def main():
    task = json.load(sys.stdin)
    role, goal = task["role"], task["goal"]
    ws = task.get("workspace") or "."
    spec = (task.get("context") or {}).get("spec")

    if role == "triage":
        rc, out, _ = ask(f'You are the TRIAGE agent. Goal: "{goal}". '
                         'Reply with exactly one JSON line: {"decision":"spec"} '
                         '(or {"decision":"reject"} if clearly out of scope).', ws)
        emit(True, last_json(out) or {"decision": "spec"}, out[-200:])
    if role == "spec":
        rc, out, _ = ask(f'You are the SPEC agent. Goal: "{goal}". Reply with exactly one JSON line: '
                         '{"title": "...", "body": "...", "acceptance": ["..."]}.', ws)
        emit(True, last_json(out) or {"title": goal, "body": out[:500], "acceptance": []}, out[-200:])
    if role == "implement":
        prompt = (f"You are the IMPLEMENT agent in a software factory. Workspace: {ws}. Goal: {goal}. "
                  "Make the smallest correct change that satisfies the goal by editing files in the workspace. "
                  "Do not run destructive commands; do not commit. "
                  "When finished, end your reply with one line: SUMMARY: <one sentence>.")
        rc, out, err = ask(prompt, ws)
        d, files = tree_digest(ws)
        emit(rc == 0, {"artifact_digest": d, "files": files}, out.strip().splitlines()[-1] if out.strip() else err[-200:])
    if role == "verify":
        prompt = (f"You are the independent VERIFY agent. Workspace: {ws}. Goal: {goal}. "
                  f"Spec: {spec}. Inspect the files and decide whether the goal is actually satisfied. "
                  'End with exactly one JSON line: {"passed": true|false, "findings": ["..."]}.')
        rc, out, _ = ask(prompt, ws)
        d = last_json(out) or {"passed": False, "findings": [out[-200:]]}
        emit(bool(d.get("passed")), {"passed": bool(d.get("passed")), "findings": d.get("findings", [])}, out[-200:])
    if role == "review":
        prompt = (f"You are the REVIEW agent. Goal: {goal}. Workspace: {ws}. "
                  'End with exactly one JSON line: {"decision":"approve"|"revise","notes":"..."}.')
        rc, out, _ = ask(prompt, ws)
        emit(True, last_json(out) or {"decision": "approve", "notes": ""}, out[-200:])
    emit(False, {}, f"unknown role {role}")


if __name__ == "__main__":
    main()
