#!/usr/bin/env python3
"""Minimal bring-your-own agent for the subprocess runner.

Speaks the PSF runner protocol: reads an AgentTask JSON on stdin, writes an
AgentResult JSON on stdout. It performs a real, tiny change in the workspace so
the factory can be dogfooded end-to-end (worktree isolation -> gate -> diff).

A real deployment points `command` at Claude Code, Codex, or any harness.
"""
import json
import pathlib
import sys


def emit(ok, output=None, summary=""):
    print(json.dumps({"ok": ok, "output": output or {}, "summary": summary}))
    sys.exit(0)


def main():
    task = json.load(sys.stdin)
    role = task["role"]
    goal = task["goal"]
    ws = pathlib.Path(task["workspace"]) if task.get("workspace") else None

    if role == "triage":
        emit(True, {"decision": "spec", "scope": goal})
    if role == "spec":
        emit(True, {"title": goal, "body": f"Deliver: {goal}",
                    "acceptance": ["a self-build marker exists"]})
    if role == "implement":
        ws.mkdir(parents=True, exist_ok=True)
        slug = "".join(c if c.isalnum() else "-" for c in goal)[:60].strip("-")
        f = ws / f"self-build-{slug}.md"
        f.write_text(f"# Self-build\n\nGoal: {goal}\nAttempt: {task['attempt']}\n")
        emit(True, {"path": f.name, "artifact_digest": ""}, f"wrote {f.name}")
    if role == "verify":
        found = bool(ws and ws.exists() and list(ws.glob("self-build-*.md")))
        emit(found, {"passed": found, "findings": [] if found else ["marker missing"]})
    if role == "review":
        emit(True, {"decision": "approve", "notes": "ok"})
    emit(False, {}, f"unknown role {role}")


if __name__ == "__main__":
    main()
