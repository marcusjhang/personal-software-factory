"""Command-line interface for the Personal Software Factory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .bench import run_benchmark
from .events import EventLog
from .foreman import Foreman
from .schema import FactoryError, load as load_factory
from .state import GateError, Workflow

DEFAULT_FACTORY = "factory"
DEFAULT_LEDGER = ".psf/factory.db"

FACTORY_YML = """schemaVersion: psf/v1
name: default
description: Default personal software factory.
runner: mock
agents:
  triage:    { prompt: agents/triage.md }
  spec:      { prompt: agents/spec.md }
  implement: { prompt: agents/implement.md }
  verify:    { prompt: agents/verify.md }
  review:    { prompt: agents/review.md }
gates:
  spec_approval: true
limits:
  max_attempts: 2
"""

PROMPTS = {
    "triage": "You scope a goal: restate it, classify risk, and decide spec-first vs direct. Reply reject only for a non-goal.",
    "spec": "You write a typed spec: title, desired behavior, non-goals, and acceptance criteria that a verifier can check.",
    "implement": "You make the smallest change that satisfies the spec in the given workspace. Report an artifact digest.",
    "verify": "You independently reproduce and check the change against the frozen spec. You are not the implementer. Return pass/fail and findings.",
    "review": "You assess quality, risk, and fit. Approve or send back with specific notes.",
}


def _load(args) -> tuple:
    factory = load_factory(args.factory)
    ledger = Path(args.ledger)
    log = EventLog(ledger)
    return factory, log, Workflow(log)


def cmd_init(args) -> int:
    root = Path(args.factory)
    if root.exists() and any(root.iterdir()) and not args.force:
        print(f"refusing to overwrite existing {root} (use --force)", file=sys.stderr)
        return 2
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "factory.yml").write_text(FACTORY_YML)
    for role, prompt in PROMPTS.items():
        (root / "agents" / f"{role}.md").write_text(prompt + "\n")
    Path(".psf").mkdir(exist_ok=True)
    print(f"initialized factory in {root}/  (agents/, factory.yml)")
    print("next: psf validate && psf run \"<your goal>\"")
    return 0


def cmd_validate(args) -> int:
    try:
        factory = load_factory(args.factory)
    except FactoryError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"valid: {factory.name} — roles {sorted(factory.agents)} runner={factory.runner}")
    return 0


def cmd_run(args) -> int:
    factory, log, wf = _load(args)
    repo = Path.cwd() if args.git else None
    result = Foreman(factory, wf).run(
        args.goal, approve=not args.no_approve, finish=args.finish,
        repo=repo, use_git=args.git,
    )
    ok, msg = log.verify_chain()
    work = result.work
    print(f"{work.id}  {work.state}  {work.goal}")
    print(f"  attempts {work.attempts}/{work.max_attempts}  spec {work.spec_digest}")
    if result.diff:
        print("  diff:")
        for line in result.diff.splitlines()[:20]:
            print("    " + line)
    print(f"  ledger: {log.count()} events, chain {msg}")
    if not ok:
        return 4
    return 0 if work.state in ("DONE", "HANDOFF") else 3


def cmd_status(args) -> int:
    _, log, wf = _load(args)
    ids = [args.work_id] if args.work_id else log.work_ids()
    if not ids:
        print("no work items")
        return 0
    for wid in ids:
        w = wf.fold(wid)
        print(f"{w.id}  {w.state:12}  {w.goal}  attempts {w.attempts}/{w.max_attempts}")
    return 0


def cmd_log(args) -> int:
    _, log, _ = _load(args)
    events = log.for_work(args.work_id) if args.work_id else log.all()
    if args.json:
        print(json.dumps([e.to_dict() for e in events], indent=2))
    else:
        for e in events:
            print(f"{e.seq:4} {e.ts}  {e.type:18} {e.work_id or '-':14} {e.actor}")
    ok, msg = log.verify_chain()
    print(f"chain: {msg}", file=sys.stderr)
    return 0 if ok else 4


def cmd_bench(args) -> int:
    report = run_benchmark(max_attempts=args.max_attempts)
    print(f"{'task':10} {'baseline':>9} {'factory':>8}")
    for d in report.details:
        print(f"{d['task']:10} {str(d['baseline']):>9} {str(d['factory']):>8}")
    print("-" * 29)
    print(f"{'PASS RATE':10} {report.baseline_rate:>8.0%} {report.factory_rate:>8.0%}")
    return 0 if report.factory_pass >= report.baseline_pass else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="psf", description="Personal Software Factory")
    p.add_argument("--factory", default=DEFAULT_FACTORY, help="factory directory (default: ./factory)")
    p.add_argument("--ledger", default=DEFAULT_LEDGER, help="ledger path (default: .psf/factory.db)")
    p.add_argument("--version", action="version", version=f"psf {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="scaffold factory/ and .psf/")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("validate", help="compile-check the factory definition")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("run", help="run one goal through the factory")
    s.add_argument("goal")
    s.add_argument("--no-approve", action="store_true", help="stop at SPEC_REVIEW and wait")
    s.add_argument("--finish", action="store_true", default=True)
    s.add_argument("--git", action="store_true", help="isolate work in a git worktree and keep it as the handoff branch")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("status", help="show work items")
    s.add_argument("work_id", nargs="?")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("log", help="print the ledger")
    s.add_argument("work_id", nargs="?")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_log)

    s = sub.add_parser("bench", help="run the internal benchmark")
    s.add_argument("--max-attempts", type=int, default=2)
    s.set_defaults(func=cmd_bench)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FactoryError, GateError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
