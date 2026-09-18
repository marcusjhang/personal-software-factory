"""Consumer feedback loop.

The point: when you use the factory on other projects, their *usage signals*
flow back to the main repo and become evaluation cases and improvement
proposals — without leaking source code, prompts, or secrets.

Privacy rules (enforced here, not by convention):

- Envelopes contain **counts, digests, and versions only**. No goal text, no
  source, no prompts, no file paths, no secrets.
- Export is explicit (`psf feedback export`). Nothing is sent automatically.
- Publishing to GitHub (`--github`) files a structured issue in the main repo.
  The main repo's own factory then intakes those issues via its GitHub adapter.

Flow:

    consumer repo                         main repo (personal-software-factory)
    psf feedback export --github  ──────▶ issue labeled `factory-feedback`
                                          psf feedback ingest <issue/export>
                                          psf feedback report   -> suggestions
                                          psf improve           -> gated change
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any

from .canonical import digest
from .events import EventLog
from .improve import _factory_file  # reuse path resolution
from .state import Workflow

SCHEMA = "psf.feedback/v1"
NOTE = "counts, digests, and versions only; no source, prompts, or secrets"


def _sha_file(p: Path) -> str:
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def factory_digest(factory_path: str | Path) -> str:
    p = Path(factory_path)
    root = p.parent if p.is_file() else p
    entries = {str(f.relative_to(root)): _sha_file(f)
               for f in sorted(root.rglob("*")) if f.is_file()}
    return digest(entries)


def build_envelope(factory_path: str | Path, ledger_path: str | Path,
                   *, repo: str | None = None, psf_version: str = "0.1.0") -> dict[str, Any]:
    log = EventLog(ledger_path)
    wf = Workflow(log)
    states: dict[str, int] = {}
    attempts = retries = blocked = 0
    for wid in log.work_ids():
        w = wf.fold(wid)
        states[w.state] = states.get(w.state, 0) + 1
        attempts += w.attempts
        retries += max(0, w.attempts - 1)
        if w.state == "BLOCKED":
            blocked += 1
    accepted = escapes = 0
    cost = minutes = 0.0
    verify_failures = 0
    for e in log.all():
        if e.type == "OutcomeRecorded":
            accepted += int(bool(e.payload.get("accepted")))
            escapes += int(bool(e.payload.get("review_escape")))
            cost += float(e.payload.get("cost_usd", 0) or 0)
            minutes += float(e.payload.get("human_minutes", 0) or 0)
        if e.type == "VerifyCompleted" and not e.payload.get("passed"):
            verify_failures += 1
    log.close()

    eval_manifest = Path("eval/manifest.json")
    return {
        "schema": SCHEMA,
        "envelope_id": f"FB-{uuid.uuid4().hex[:8]}",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "psf_version": psf_version,
        "factory_digest": factory_digest(factory_path),
        "eval_manifest_digest": json.loads(eval_manifest.read_text()).get("manifest_digest")
        if eval_manifest.exists() else None,
        "repo": repo,  # optional; user opts in
        "metrics": {
            "work_items": sum(states.values()),
            "states": states,
            "attempts": attempts,
            "retries": retries,
            "blocked": blocked,
            "outcomes": {"accepted": accepted, "review_escape": escapes,
                         "cost_usd": round(cost, 4), "human_minutes": minutes},
        },
        "failures": {"verify_failures": verify_failures},
        "note": NOTE,
    }


def export(factory_path: str | Path, ledger_path: str | Path, *, out: str | Path | None = None,
           repo: str | None = None) -> Path:
    env = build_envelope(factory_path, ledger_path, repo=repo)
    dest = Path(out) if out else Path(".psf/feedback") / f"{env['envelope_id']}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(env, indent=2) + "\n")
    return dest


def publish_issue(repo: str, envelope: dict[str, Any]) -> tuple[str | None, str | None]:
    """File the envelope as an issue in the main repo (uses gh)."""
    import subprocess

    body = ("Automated feedback envelope from a consumer repository.\n"
            f"_{envelope.get('note', NOTE)}_\n\n"
            "```json\n" + json.dumps(envelope, indent=2) + "\n```\n")
    p = subprocess.run(
        ["gh", "issue", "create", "--repo", repo, "--label", "factory-feedback",
         "--title", f"[factory-feedback] {envelope['envelope_id']} ({envelope['metrics']['work_items']} work items)",
         "--body", body],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        return None, p.stderr.strip()
    return p.stdout.strip(), None


def ingest(inbox: str | Path, item: str | Path) -> int:
    """Copy one or more exported envelopes into the main repo's feedback inbox."""
    inbox = Path(inbox)
    inbox.mkdir(parents=True, exist_ok=True)
    src = Path(item)
    files = [src] if src.is_file() else sorted(src.glob("*.json"))
    n = 0
    for f in files:
        env = json.loads(f.read_text())
        (inbox / f"{env.get('envelope_id', f.stem)}.json").write_text(json.dumps(env, indent=2) + "\n")
        n += 1
    return n


def report(inbox: str | Path) -> dict[str, Any]:
    """Aggregate ingested envelopes into signals the improvement loop can use."""
    inbox = Path(inbox)
    items = [json.loads(f.read_text()) for f in sorted(inbox.glob("*.json"))] if inbox.exists() else []
    total = {"work_items": 0, "blocked": 0, "retries": 0, "accepted": 0, "review_escape": 0,
             "verify_failures": 0, "cost_usd": 0.0, "human_minutes": 0.0}
    versions: dict[str, int] = {}
    for e in items:
        m = e.get("metrics", {})
        total["work_items"] += m.get("work_items", 0)
        total["blocked"] += m.get("blocked", 0)
        total["retries"] += m.get("retries", 0)
        total["verify_failures"] += e.get("failures", {}).get("verify_failures", 0)
        o = m.get("outcomes", {})
        total["accepted"] += o.get("accepted", 0)
        total["review_escape"] += o.get("review_escape", 0)
        total["cost_usd"] += o.get("cost_usd", 0.0)
        total["human_minutes"] += o.get("human_minutes", 0.0)
        versions[e.get("psf_version", "?")] = versions.get(e.get("psf_version", "?"), 0) + 1

    suggestions: list[str] = []
    if total["blocked"] or total["retries"]:
        suggestions.append("retries/blocks observed — consider raising limits.max_attempts (psf improve)")
    if total["review_escape"]:
        suggestions.append("review escapes observed — strengthen the verify role or acceptance criteria")
    if total["verify_failures"]:
        suggestions.append("verify failures observed — add these as protected eval cases")
    return {"envelopes": len(items), "by_version": versions, "totals": total,
            "suggestions": suggestions}
