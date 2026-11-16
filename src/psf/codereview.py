"""OCR delegate-mode code-review loop: the deterministic mechanics.

The review itself (reading code against the rules, judging findings) is agent
work and lives in the ``code-review-loop`` skill and ``agents/code-review.md``.
This module does the parts that must not depend on judgment:

- **select** the files to review: the diff (``ocr delegate preview``) or, in
  full-repo mode, every tracked code file;
- **resolve** the review rules for those files (``ocr delegate rule``);
- **record** each round's findings in ``.psf/review/<session>.json`` and decide
  CONTINUE / DONE / STOP.

Stop rule: a round is DONE when it has at most ``max_highs`` *verified* findings of
severity high or critical. Unverified findings and anything below high (medium,
low, taste, style, info) never block. The loop is capped at ``max_rounds``. If the cap
is reached with too many highs, the result is STOP, which must be reported and not hidden.

The loop fails closed: if ``ocr`` is missing or errors, no review session starts.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BLOCKING = frozenset({"critical", "high"})
SEVERITIES = frozenset({"critical", "high", "medium", "low", "info", "taste", "style"})
DEFAULT_MAX_HIGHS = 2
DEFAULT_MAX_ROUNDS = 5
REVIEW_DIR = Path(".psf/review")

# Full-repo mode reviews code, not prose or data (same scope as the diff mode's
# "reviewable" files for this repo's history). Extensions are lowercase.
CODE_EXTS = frozenset({
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte",
    ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".swift", ".m", ".mm", ".c", ".h",
    ".cc", ".cpp", ".hpp", ".cs", ".rb", ".php", ".sh", ".bash", ".zsh", ".sql", ".lua",
    ".dart", ".ex", ".exs", ".erl", ".clj", ".r", ".jl", ".pl", ".ps1",
})
CODE_NAMES = frozenset({"Dockerfile", "Makefile"})

DONE, CONTINUE, STOP = "DONE", "CONTINUE", "STOP"


class ReviewError(Exception):
    """The review loop cannot proceed (missing ocr, bad input, bad state)."""


@dataclass(frozen=True)
class Settings:
    max_highs: int = DEFAULT_MAX_HIGHS
    max_rounds: int = DEFAULT_MAX_ROUNDS

    @classmethod
    def from_gates(cls, gates: dict[str, Any] | None) -> "Settings":
        cr = (gates or {}).get("code_review") or {}
        if not isinstance(cr, dict):
            return cls()
        return cls(int(cr.get("max_highs", DEFAULT_MAX_HIGHS)),
                   int(cr.get("max_rounds", DEFAULT_MAX_ROUNDS)))


def ocr_bin() -> str:
    """Resolve the ocr CLI: $PSF_OCR, then PATH. Fail closed when absent."""
    cand = os.environ.get("PSF_OCR") or shutil.which("ocr")
    if not cand or not Path(cand).exists():
        raise ReviewError("ocr CLI not found: install open-code-review or set PSF_OCR")
    return cand


def _ocr_json(repo: Path, args: list[str]) -> dict[str, Any]:
    cmd = [ocr_bin(), "delegate", *args, "--format", "json", "--color", "never"]
    try:
        r = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ReviewError(f"ocr failed to run: {e}") from e
    if r.returncode != 0:
        msg = (r.stderr or r.stdout).strip().splitlines()
        raise ReviewError(f"ocr {args[0]} failed (rc={r.returncode}): {msg[0] if msg else ''}")
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise ReviewError(f"ocr {args[0]} returned non-JSON output") from e
    if not isinstance(data, dict):
        raise ReviewError(f"ocr {args[0]} returned an unexpected shape")
    return data


def is_code(path: str) -> bool:
    p = Path(path)
    return p.name in CODE_NAMES or p.suffix.lower() in CODE_EXTS


def tracked_code_files(repo: Path) -> list[str]:
    try:
        r = subprocess.run(["git", "ls-files", "-z"], cwd=repo, capture_output=True,
                           text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ReviewError(f"git ls-files failed: {e}") from e
    if r.returncode != 0:
        raise ReviewError("not a git repository (full-repo review needs git)")
    return sorted(f for f in r.stdout.split("\0") if f and is_code(f))


def select_files(repo: Path, *, full: bool = False, base: str | None = None,
                 head: str = "HEAD") -> tuple[str, list[str]]:
    """Return (mode, files). Diff mode asks ocr; full mode lists tracked code."""
    if full:
        return "full", tracked_code_files(repo)
    args = ["preview"] + (["--from", base, "--to", head] if base else [])
    data = _ocr_json(repo, args)
    files = [f["path"] for f in data.get("reviewable_files") or []
             if isinstance(f, dict) and f.get("path") and f.get("status") != "deleted"]
    return str(data.get("mode") or ("range" if base else "workspace")), files


def resolve_rules(repo: Path, files: list[str], batch: int = 200) -> list[dict[str, Any]]:
    """Rule groups for files, merged across batches by (source, pattern)."""
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for i in range(0, len(files), batch):
        data = _ocr_json(repo, ["rule", *files[i:i + batch]])
        for g in data.get("groups") or []:
            key = (str(g.get("source")), str(g.get("pattern")))
            slot = merged.setdefault(key, {"source": g.get("source"), "pattern": g.get("pattern"),
                                           "rule": g.get("rule", ""), "files": []})
            slot["files"].extend(g.get("files") or [])
    return list(merged.values())


def _state_path(repo: Path, session: str) -> Path:
    if not session or "/" in session or session.startswith("."):
        raise ReviewError(f"bad session id: {session!r}")
    return repo / REVIEW_DIR / f"{session}.json"


def _save(repo: Path, state: dict[str, Any]) -> Path:
    p = _state_path(repo, state["session"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n")
    tmp.replace(p)
    (repo / REVIEW_DIR / "LATEST").write_text(state["session"] + "\n")
    return p


def load(repo: Path, session: str | None = None) -> dict[str, Any]:
    if session is None:
        latest = repo / REVIEW_DIR / "LATEST"
        if not latest.exists():
            raise ReviewError("no review session; run `psf review start` first")
        session = latest.read_text().strip()
    p = _state_path(repo, session)
    if not p.exists():
        raise ReviewError(f"no such review session: {session}")
    try:
        state = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise ReviewError(f"review session {session} is unreadable: {e}") from e
    required = ("session", "rounds", "max_highs", "max_rounds", "files", "mode")
    if not isinstance(state, dict) or any(k not in state for k in required) \
            or not isinstance(state["rounds"], list):
        raise ReviewError(f"review session {session} is malformed")
    return state


def start(repo: Path, *, full: bool = False, base: str | None = None,
          settings: Settings = Settings()) -> dict[str, Any]:
    """Open a review session: files + rules packet for the reviewing agent."""
    if settings.max_highs < 0 or settings.max_rounds < 1:
        raise ReviewError("max_highs must be >= 0 and max_rounds >= 1")
    mode, files = select_files(repo, full=full, base=base)
    rules = resolve_rules(repo, files) if files else []
    state = {
        "schema": "psf.review/v1",
        "session": f"R-{uuid.uuid4().hex[:8]}",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": mode, "base": base, "files": files, "rule_groups": rules,
        "max_highs": settings.max_highs, "max_rounds": settings.max_rounds,
        "rounds": [], "result": DONE if not files else None,
    }
    _save(repo, state)
    return state


def _normalize(findings: Any) -> list[dict[str, Any]]:
    if isinstance(findings, dict):
        findings = findings.get("findings")
    if not isinstance(findings, list):
        raise ReviewError("findings must be a list (or {\"findings\": [...]})")
    out = []
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            raise ReviewError(f"finding #{i} must be an object")
        sev = str(f.get("severity", "")).strip().lower()
        if sev not in SEVERITIES:
            raise ReviewError(f"finding #{i} has unknown severity {f.get('severity')!r}; "
                              f"use one of {sorted(SEVERITIES)}")
        verified = f.get("verified")
        if not isinstance(verified, bool):
            raise ReviewError(f"finding #{i} needs verified: true|false")
        out.append({"id": str(f.get("id") or f"F{i + 1}"), "severity": sev,
                    "file": str(f.get("file") or ""), "summary": str(f.get("summary") or ""),
                    "verified": verified, "disposition": str(f.get("disposition") or "open")})
    return out


def blocking(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Verified high/critical findings: the only ones that count against the stop rule."""
    return [f for f in findings if f["verified"] and f["severity"] in BLOCKING]


def decide(highs: int, round_no: int, settings: Settings) -> str:
    if highs <= settings.max_highs:
        return DONE
    if round_no >= settings.max_rounds:
        return STOP
    return CONTINUE


def record(repo: Path, findings: Any, session: str | None = None) -> dict[str, Any]:
    """Record one review round; returns the round with its decision."""
    state = load(repo, session)
    if state.get("result") in (DONE, STOP):
        raise ReviewError(f"session {state['session']} already finished: {state['result']}")
    items = _normalize(findings)
    settings = Settings(int(state["max_highs"]), int(state["max_rounds"]))
    n = len(state["rounds"]) + 1
    highs = blocking(items)
    decision = decide(len(highs), n, settings)
    rnd = {"round": n, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "findings": items, "verified_highs": len(highs), "decision": decision}
    state["rounds"].append(rnd)
    if decision in (DONE, STOP):
        state["result"] = decision
    _save(repo, state)
    return rnd


def summary_markdown(state: dict[str, Any]) -> str:
    """A round table suitable for docs/CODE-REVIEW-ROUNDS.md."""
    lines = [f"### Review {state['session']} ({state['mode']}, {len(state['files'])} files) "
             f"→ {state.get('result') or 'in progress'}", "",
             f"Stop rule: ≤{state['max_highs']} verified high/critical; cap {state['max_rounds']} rounds.", "",
             "| round | findings | verified high+ | decision |", "|---|---|---|---|"]
    for r in state["rounds"]:
        lines.append(f"| {r['round']} | {len(r['findings'])} | {r['verified_highs']} | {r['decision']} |")
    return "\n".join(lines) + "\n"
