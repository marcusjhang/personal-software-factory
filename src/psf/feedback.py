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
import re
import time
import uuid
from pathlib import Path
from typing import Any

from . import __version__
from .canonical import digest, sha256_file
from .events import EventLog
from .state import Workflow

SCHEMA = "psf.feedback/v1"
NOTE = "counts, digests, and versions only; no source, prompts, or secrets"
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def envelope_filename(env: dict[str, Any]) -> str:
    """A safe inbox filename for an envelope.

    ``envelope_id`` arrives from a fetched issue, i.e. it is untrusted: never
    let it traverse out of the inbox. Fall back to a content digest.
    """
    eid = str(env.get("envelope_id") or "")
    if not _SAFE_ID.match(eid) or ".." in eid:
        eid = "FB-" + hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest()[:8]
    return f"{eid}.json"


def source_id(ledger_path: str | Path) -> str:
    """A stable, random id for this consumer repo, kept next to its ledger.

    It lets ``report`` keep only the newest envelope per repo (exports are
    cumulative). It is random, not derived from any path, so it reveals nothing,
    and it stays the same from any working directory or after the repo moves.
    """
    f = Path(ledger_path).parent / "source-id"
    try:
        sid = f.read_text().strip()
        if _SAFE_ID.match(sid) and sid.startswith("src-"):
            return sid
    except OSError:
        pass
    sid = "src-" + uuid.uuid4().hex[:16]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(sid + "\n")
    return sid


def latest_export(directory: str | Path) -> dict[str, Any] | None:
    """The newest envelope previously exported into ``directory`` (or None)."""
    best: tuple[str, dict[str, Any]] | None = None
    for f in Path(directory).glob("FB-*.json"):
        try:
            env = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(env, dict) or env.get("schema") != SCHEMA:
            continue
        key = str(env.get("generated_at") or "")
        if best is None or key > best[0]:
            best = (key, env)
    return best[1] if best else None


def has_new_work(env: dict[str, Any], prev: dict[str, Any] | None) -> bool:
    """True when ``env`` carries activity the previous export did not."""
    if prev is None:
        return bool(env.get("metrics", {}).get("work_items"))
    return (env.get("metrics"), env.get("failures")) != (prev.get("metrics"), prev.get("failures"))


def factory_digest(factory_path: str | Path) -> str:
    p = Path(factory_path)
    root = p.parent if p.is_file() else p
    entries = {str(f.relative_to(root)): sha256_file(f)
               for f in sorted(root.rglob("*")) if f.is_file()}
    return digest(entries)


def build_envelope(factory_path: str | Path, ledger_path: str | Path,
                   *, repo: str | None = None, psf_version: str | None = None) -> dict[str, Any]:
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
        "psf_version": psf_version or __version__,
        "factory_digest": factory_digest(factory_path),
        "eval_manifest_digest": json.loads(eval_manifest.read_text()).get("manifest_digest")
        if eval_manifest.exists() else None,
        "repo": repo,  # optional; user opts in
        "source": source_id(ledger_path),  # random per-repo id (.psf/source-id), never a path
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
           repo: str | None = None, env: dict[str, Any] | None = None) -> Path:
    env = env or build_envelope(factory_path, ledger_path, repo=repo)
    dest = Path(out) if out else Path(".psf/feedback") / f"{env['envelope_id']}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(env, indent=2) + "\n")
    return dest


def ensure_label(repo: str, label: str = "factory-feedback") -> None:
    """Best-effort: make sure the intake label exists upstream."""
    import subprocess

    subprocess.run(
        ["gh", "label", "create", label, "--repo", repo, "--force",
         "--color", "1d76db", "--description", "Consumer factory feedback envelope"],
        capture_output=True, text=True,
    )


def publish_issue(repo: str, envelope: dict[str, Any]) -> tuple[str | None, str | None]:
    """File the envelope as an issue in the main repo (uses gh).

    Ensures the intake label exists first, and returns ``(url, error)``; the
    caller must treat a missing URL as a failure (never report silent success).
    """
    import subprocess

    ensure_label(repo)
    body = ("Automated feedback envelope from a consumer repository.\n"
            f"_{envelope.get('note', NOTE)}_\n\n"
            "```json\n" + json.dumps(envelope, indent=2) + "\n```\n")
    p = subprocess.run(
        ["gh", "issue", "create", "--repo", repo, "--label", "factory-feedback",
         "--title", f"[factory-feedback] {envelope['envelope_id']} ({envelope['metrics']['work_items']} work items)",
         "--body", body],
        capture_output=True, text=True,
    )
    url = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
    if p.returncode != 0 or not url.startswith("http"):
        return None, (p.stderr.strip() or "no issue URL returned")
    return url, None


def ingest(inbox: str | Path, item: str | Path) -> int:
    """Copy one or more exported envelopes into the main repo's feedback inbox."""
    inbox = Path(inbox)
    inbox.mkdir(parents=True, exist_ok=True)
    src = Path(item)
    files = [src] if src.is_file() else sorted(src.glob("*.json"))
    n = 0
    for f in files:
        env = json.loads(f.read_text())
        (inbox / envelope_filename(env)).write_text(json.dumps(env, indent=2) + "\n")
        n += 1
    return n


def parse_envelope(text: str) -> dict[str, Any] | None:
    """Extract a feedback envelope from a fenced ```json block in issue text."""
    import re

    m = re.search(r"```json\s*(\{.*?\})\s*```", text or "", re.S)
    if not m:
        return None
    try:
        env = json.loads(m.group(1))
    except ValueError:
        return None
    return env if isinstance(env, dict) and env.get("schema") == SCHEMA else None


def ingest_issues(inbox: str | Path, *, repo: str | None = None,
                  label: str = "factory-feedback") -> int:
    """Intake path: read `factory-feedback` issues and ingest their envelopes.

    This is the GitHub half of the transfer — a consumer files an issue, the
    main repo reads it here and the envelopes land in the inbox for `report`.
    """
    from .github import list_issues

    inbox = Path(inbox)
    inbox.mkdir(parents=True, exist_ok=True)
    n = 0
    for issue in list_issues(repo=repo, label=label):
        env = parse_envelope(issue.get("body") or "")
        if env:
            (inbox / envelope_filename(env)).write_text(json.dumps(env, indent=2) + "\n")
            n += 1
    return n


def report(inbox: str | Path) -> dict[str, Any]:
    """Aggregate ingested envelopes into signals the improvement loop can use."""
    inbox = Path(inbox)
    raw = [json.loads(f.read_text()) for f in sorted(inbox.glob("*.json"))] if inbox.exists() else []
    items = dedupe_newest(raw)
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
    return {"envelopes": len(items), "superseded": len(raw) - len(items),
            "by_version": versions, "totals": total, "suggestions": suggestions}


def dedupe_newest(envelopes: list[Any]) -> list[dict[str, Any]]:
    """Keep only the newest envelope per ``source`` (exports are cumulative).

    Envelopes are untrusted (they may come from issues). One without a usable
    string ``source`` (older psf, or malformed) cannot be grouped and is kept,
    as before. Non-mapping entries are dropped.
    """
    newest: dict[str, dict[str, Any]] = {}
    legacy: list[dict[str, Any]] = []
    for e in envelopes:
        if not isinstance(e, dict):
            continue
        src = e.get("source")
        if not isinstance(src, str) or not src:
            legacy.append(e)
            continue
        cur = newest.get(src)
        if cur is None or str(e.get("generated_at") or "") > str(cur.get("generated_at") or ""):
            newest[src] = e
    return legacy + list(newest.values())
