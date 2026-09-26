"""Verify-gate analysis — close the "all gates green, artifact can't run" gap.

Findings from a real consumer cycle: the deterministic gate was a keyless
self-check that never touched the integration, acceptance was prose satisfiable
by plausible code, and nothing exercised a second run. These helpers add the
cheap static/runtime checks that catch those classes:

- ``command_is_vacuous``        — a verify command that passes on a baseline
                                  (change-free) workspace proves nothing (R1).
- ``verify_reachability``       — the change touches an integration but the
                                  verify command cannot connect (R3).
- ``dead_logic_under_test``     — code added only to satisfy tests, never called
                                  by the runtime path (R4).
- ``failure_masked_by_optimize`` — the check relies on bare ``assert`` and is
                                  neutered by ``python -O`` (R6).
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

INTEGRATION_MARKERS = (
    "requests", "httpx", "aiohttp", "urllib", "http.client", "socket",
    "websocket", "websockets", "grpc", "openai", "anthropic", "boto3",
    "twilio", "elevenlabs", "deepgram", "google.cloud", "stripe",
)

_DEF_RE = re.compile(r"^\+\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)")
_CONNECT_MARKERS = ("curl", "http", "connect", "smoke", "e2e", "integration",
                    "server", "serve", "--live", "pytest")


def run(ws: str | Path, command: str, *, env: dict | None = None, timeout: int = 600):
    e = {**os.environ, **(env or {})}
    try:
        p = subprocess.run(shlex.split(command), cwd=str(ws), capture_output=True,
                           text=True, timeout=timeout, env=e)
        return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()
    except (OSError, subprocess.SubprocessError) as exc:  # noqa: BLE001
        return 127, f"error: {exc}"


def command_is_vacuous(baseline_ws: str | Path, command: str) -> bool:
    """True if the command passes on a change-free (baseline) workspace.

    A gate that passes before the change is even applied cannot be verifying
    that change (R1).
    """
    rc, _ = run(baseline_ws, command)
    return rc == 0


def failure_masked_by_optimize(ws: str | Path, command: str) -> bool:
    """True if the command fails normally but passes under ``python -O`` (R6)."""
    rc1, _ = run(ws, command)
    rc2, _ = run(ws, command, env={"PYTHONOPTIMIZE": "1"})
    return rc1 != 0 and rc2 == 0


def parse_diff(diff: str) -> dict[str, list[str]]:
    """Map changed file -> added lines (without the leading '+')."""
    files: dict[str, list[str]] = {}
    current: str | None = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:].strip()
            files.setdefault(current, [])
        elif line.startswith("+++ "):
            current = None
        elif line.startswith("+") and not line.startswith("+++") and current:
            files[current].append(line[1:])
    return files


def integration_surface(diff: str) -> list[str]:
    files = parse_diff(diff)
    hits: set[str] = set()
    for lines in files.values():
        blob = "\n".join(lines)
        for m in INTEGRATION_MARKERS:
            if re.search(rf"(?<![\w.]){re.escape(m)}(?![\w])", blob):
                hits.add(m)
    return sorted(hits)


def verify_reachability(diff: str, verify_commands: list[str], *, has_env: bool = False) -> list[str]:
    surfaces = integration_surface(diff)
    if not surfaces:
        return []
    warns: list[str] = []
    joined = " ".join(verify_commands or []).lower()
    if not any(k in joined for k in _CONNECT_MARKERS):
        warns.append(
            f"change touches an integration ({', '.join(surfaces)}) but the verify "
            "command(s) appear not to connect to it; verification may be shape-only")
    if not has_env:
        warns.append("workspace has no credentials/.env; an integration check cannot reach the dependency")
    return warns


def dead_logic_under_test(diff: str) -> list[str]:
    """Added defs/classes referenced only from test files (R4)."""
    files = parse_diff(diff)
    test_files = {p for p in files if "test" in Path(p).name.lower()}
    runtime_files = {p for p in files if p not in test_files}
    added: dict[str, str] = {}
    for p in runtime_files:
        for line in files[p]:
            m = _DEF_RE.match("+" + line if not line.startswith("+") else "+" + line)
            if m:
                added.setdefault(m.group(1), p)
    out: list[str] = []
    for name, path in added.items():
        pat = re.compile(rf"(?<![\w.]){re.escape(name)}(?![\w])")
        ref_test = sum(bool(pat.search(ln)) for p in test_files for ln in files[p])
        ref_runtime = sum(bool(pat.search(ln)) and not _DEF_RE.match("+" + ln) for p in runtime_files for ln in files[p])
        if ref_test and not ref_runtime:
            out.append(f"{name} (defined in {path}) is referenced only from tests, not the runtime path")
    return out
