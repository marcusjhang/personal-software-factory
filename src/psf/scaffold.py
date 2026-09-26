"""The factory template: one source of truth for `psf init` and `psf upgrade`.

Everything a factory needs — ``factory.yml``, the role prompts, and the agent
instruction files — is *rendered* here from a single set of definitions.
`psf init` writes them into a repo; `psf upgrade` reconciles a repo's existing
files against a newer rendering. Nothing else may re-declare this content, so the
template can never drift from itself.

Provenance lives in ``psf.lock.json`` at the repo root (tracked, so CI sees it):

- ``base``      — a pristine snapshot of the template as installed: the merge
  base for a future upgrade. Keeping the bytes (not just a git ref) makes an
  upgrade offline and exact, the way Copier keeps the template revision.
- ``revision`` / ``template_digest`` / ``migrations`` — the pin, and which
  structural migrations have already run.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LOCK_REL = Path("psf.lock.json")
LOCK_SCHEMA = "psf.lock/v1"
DEFAULT_UPSTREAM = "marcusjhang/personal-software-factory"

FACTORY_YML = """schemaVersion: psf/v1
name: default
description: Default personal software factory.
runner: mock
mode: "{mode}"          # hitl = human in the loop; yolo = human out (autonomous)
agents:
  triage:    { prompt: agents/triage.md }
  spec:      { prompt: agents/spec.md }
  implement: { prompt: agents/implement.md }
  verify:    { prompt: agents/verify.md }
  review:    { prompt: agents/review.md }
gates:
  spec_approval: true
  verify_quorum: 2
limits:
  max_attempts: 2
feedback:
  upstream: {upstream}
  mode: "{fb_mode}"          # off | hint | auto; change anytime with `psf feedback opt-out|opt-in`
classifier:
  provider: "mock"          # mock | jev (TypeSafe). Advisory only.
  supervisor:
    enabled: false           # opt-in: watch a worker and steer/stop/retry
    thresholds: {needs_human: 0.80, off_track: 0.80, stuck: 0.80, progress: 0.40}
    max_steers: 1
    max_retries: 1
"""

AGENTS_MD = """# AGENTS.md — how agents should use this repository

This repository is driven by a **personal software factory** (`psf`). If you are
an agent working here, follow this process instead of ad-hoc editing — route
changes through the factory so they get a spec, approval, independent
verification, and review:

1. `psf validate` — confirm the factory definition compiles.
2. `psf run "<goal>"` — run the goal through the factory (intake -> spec ->
   approval -> build -> **independent verify** -> review -> handoff).
3. `psf status` / `psf audit` — check state and health before you finish.
4. Record the real outcome: `psf outcome <work-id> --accepted [--cost N --minutes N]`.

## Feedback to the factory

At the end of a work cycle, send a **privacy-filtered** usage envelope back to the
factory that powers this repo. It contains **counts, digests, and versions only** —
never source code, prompts, file paths, or secrets:

    psf feedback export --github <upstream-repo>

`<upstream-repo>` is the `feedback.upstream` value in `factory/factory.yml`.
Set `feedback.mode: auto` to make `psf feedback export` publish there by default.
Recurring verify-failures and blocks become evaluation cases and improvements in
the upstream factory. This is evidence, never authority: it cannot change policy.

Do **not** put secrets, customer data, or raw source in a feedback envelope.
"""

PROMPTS = {
    "triage": "You scope a goal: restate it, classify risk, and decide spec-first vs direct. Reply reject only for a non-goal.",
    "spec": (
        "You write a typed spec: title, desired behavior, non-goals, and acceptance criteria that a verifier can check.\n\n"
        "Acceptance criteria must be behavioral and testable:\n"
        "- Each criterion states an observable outcome: given input X, the system does Y (succeeds, rejects, returns, persists, a test passes). A verifier must be able to run it.\n"
        "- Do not quote exact error, log, or message wording.\n"
        "- Do not require internal fields, names, or structure the goal did not ask for.\n"
        "- Do not require particular test cases, test names, or coverage counts. Ask that the project's tests pass; do not dictate which cases they contain.\n"
        "- If a criterion cannot be stated behaviorally, drop it or record it as a non-goal."
    ),
    "implement": "You make the smallest change that satisfies the spec in the given workspace. Report an artifact digest.",
    "verify": (
        "You independently reproduce and check the change against the frozen spec. You are not the implementer. Return pass/fail and findings.\n\n"
        "Fail only on behavioral or acceptance failures: an acceptance criterion is not met, a test fails, the change does not do what the spec says, or it breaks existing behavior.\n\n"
        "Cosmetic wording and incidental internal differences are advisory, never failures: exact error/log/message text, naming, formatting, file layout, and internal fields the spec did not require. Report them as findings prefixed \"advisory:\" and still pass.\n\n"
        "Test-coverage completeness (which specific cases exist) is advisory unless the goal explicitly required those cases. If the tests pass and the behavior is correct, pass."
    ),
    "review": (
        "You assess quality, risk, and fit against the spec. Approve or request changes.\n\n"
        "Approve when the acceptance criteria are met and the project's tests pass. Do not request changes for style, naming, test-coverage preferences, or hypothetical improvements.\n\n"
        "If you request changes, you MUST give concrete notes naming the defect and the fix. Never revise without actionable notes; if you cannot name a real defect, approve."
    ),
}

# The template is exactly these paths; anything else in factory/ is a local file.
FIXED_TEMPLATE_FILES = ("factory.yml", "AGENTS.md")


def agent_files() -> list[Path]:
    """Instruction files different coding agents read automatically."""
    return [
        Path("AGENTS.md"),                          # Codex, opencode, Factory, many
        Path("CLAUDE.md"),                          # Claude Code
        Path(".github/copilot-instructions.md"),    # GitHub Copilot
        Path(".cursor/rules/psf.mdc"),              # Cursor
        Path("GEMINI.md"),                          # Gemini CLI
    ]


def render_template(upstream: str, fb_mode: str, mode: str) -> dict[str, str]:
    """The canonical template as a mapping of factory-relative path -> text."""
    files = {
        "factory.yml": FACTORY_YML.replace("{upstream}", upstream)
                                  .replace("{fb_mode}", fb_mode)
                                  .replace("{mode}", mode),
        "AGENTS.md": AGENTS_MD,
    }
    for role, prompt in PROMPTS.items():
        files[f"agents/{role}.md"] = prompt + "\n"
    return files


def is_template_file(rel: str) -> bool:
    return rel in FIXED_TEMPLATE_FILES or (rel.startswith("agents/") and rel.endswith(".md"))


def digest(files: dict[str, str]) -> str:
    """Content-address a template (path + bytes), independent of ordering."""
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode())
        h.update(b"\0")
        h.update(files[rel].encode())
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


def read_template(dest: Path) -> dict[str, str]:
    """Read only the template files from a factory/template directory."""
    dest = Path(dest)
    if not dest.exists():
        return {}
    out = {}
    for p in sorted(dest.rglob("*")):
        if p.is_file() and is_template_file(str(p.relative_to(dest))):
            out[str(p.relative_to(dest))] = p.read_text()
    return out


def write_template(dest: Path, files: dict[str, str]) -> None:
    dest = Path(dest)
    for rel, text in files.items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


def factory_file(path: str | Path) -> Path:
    """Resolve a factory path (dir or file) to its ``factory.yml``."""
    p = Path(path)
    return p / "factory.yml" if p.is_dir() else p


def as_str(value: object, default: str) -> str:
    """Coerce a config value a YAML parser may have turned into a bool back to a string.

    YAML 1.1 reads bare ``off``/``on`` as booleans, so ``feedback.mode: off`` can
    arrive as ``False``. Round-trip it to the token the schema expects.
    """
    if isinstance(value, bool):
        return "off" if value is False else "on"
    return value if isinstance(value, str) else default


@dataclass
class Lock:
    revision: str = "unknown"
    template_digest: str = ""
    migrations: list[str] = field(default_factory=list)
    applied_at: str = ""
    base: dict[str, str] = field(default_factory=dict)
    schema: str = LOCK_SCHEMA

    def stamp(self) -> "Lock":
        self.applied_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return self


def lock_path(repo_root: Path) -> Path:
    return Path(repo_root) / LOCK_REL


def read_lock(repo_root: Path) -> Lock | None:
    p = lock_path(repo_root)
    if not p.exists():
        return None
    raw = json.loads(p.read_text())
    return Lock(revision=raw.get("revision", "unknown"),
                template_digest=raw.get("template_digest", ""),
                migrations=list(raw.get("migrations", [])),
                applied_at=raw.get("applied_at", ""),
                base=dict(raw.get("base", {})),
                schema=raw.get("schema", LOCK_SCHEMA))


def write_lock(repo_root: Path, lock: Lock) -> Path:
    p = lock_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(lock), indent=2, sort_keys=True) + "\n")
    return p


def write_scaffold(root: Path, repo_root: Path, upstream: str, fb_mode: str,
                   mode: str, *, force: bool = False) -> tuple[list[str], list[str]]:
    """Write factory files + agent instructions. Returns (factory files, instructions)."""
    root = Path(root)
    if root.exists() and any(root.iterdir()) and not force:
        raise FileExistsError(str(root))
    files = render_template(upstream, fb_mode, mode)
    write_template(root, files)
    instructions = []
    for p in agent_files():
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(AGENTS_MD)
            instructions.append(str(p))
    return sorted(files), instructions
