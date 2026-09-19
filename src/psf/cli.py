"""Command-line interface for the Personal Software Factory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .audit import FAIL, WARN, run_audit
from .bench import run_benchmark
from .events import EventLog
from .foreman import Foreman
from .improve import run_improvement
from .schema import FactoryError, load as load_factory
from .state import GateError, Workflow

DEFAULT_FACTORY = "factory"
DEFAULT_LEDGER = ".psf/factory.db"

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
Set `feedback.publish: true` to make `psf feedback export` publish there by default.
Recurring verify-failures and blocks become evaluation cases and improvements in
the upstream factory. This is evidence, never authority: it cannot change policy.

Do **not** put secrets, customer data, or raw source in a feedback envelope.
"""


def _agent_files() -> list[Path]:
    """Instruction files different coding agents read automatically."""
    return [
        Path("AGENTS.md"),                          # Codex, opencode, Factory, many
        Path("CLAUDE.md"),                          # Claude Code
        Path(".github/copilot-instructions.md"),    # GitHub Copilot
        Path(".cursor/rules/psf.mdc"),              # Cursor
        Path("GEMINI.md"),                          # Gemini CLI
    ]


def _feedback_cfg(args) -> tuple[str | None, str]:
    try:
        factory = load_factory(args.factory)
    except FactoryError:
        return None, "hint"
    fb = getattr(factory, "feedback", {}) or {}
    mode = fb.get("mode") or ("auto" if fb.get("publish") else "hint")
    return fb.get("upstream"), mode


def _set_feedback(*, mode: str | None = None, upstream: str | None = None,
                  factory_path: str = "factory") -> Path:
    import re

    import yaml

    p = Path(factory_path)
    p = p / "factory.yml" if p.is_dir() else p
    raw = yaml.safe_load(p.read_text()) or {}
    fb = raw.setdefault("feedback", {})
    if mode is not None:
        fb["mode"] = mode
        fb.pop("publish", None)
    if upstream is not None:
        fb["upstream"] = upstream
    text = yaml.safe_dump(raw, sort_keys=False)
    # YAML 1.1 parses bare `off`/`on` as booleans; keep mode a string.
    text = re.sub(r"(?m)^(\s*mode:\s*)(off|on|hint|auto)\s*$", r"\1'\2'", text)
    p.write_text(text)
    return p


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

    # Feedback consent is chosen at install time and changeable anytime.
    upstream = args.upstream or "marcusjhang/personal-software-factory"
    fb_mode = args.feedback
    if fb_mode is None:
        if sys.stdin.isatty():
            try:
                ans = input("Share anonymous usage feedback upstream? [off/hint/auto] (hint): ").strip().lower()
            except EOFError:
                ans = ""
            fb_mode = ans if ans in ("off", "hint", "auto") else "hint"
        else:
            fb_mode = "hint"

    # Autonomy mode is chosen at install and switchable anytime (`psf mode`).
    mode = args.mode
    if mode is None:
        if sys.stdin.isatty():
            try:
                ans = input("Autonomy mode? [hitl = you approve; yolo = autonomous] (hitl): ").strip().lower()
            except EOFError:
                ans = ""
            mode = ans if ans in ("hitl", "yolo") else "hitl"
        else:
            mode = "hitl"

    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "factory.yml").write_text(
        FACTORY_YML.replace("{upstream}", upstream).replace("{fb_mode}", fb_mode).replace("{mode}", mode))
    for role, prompt in PROMPTS.items():
        (root / "agents" / f"{role}.md").write_text(prompt + "\n")
    (root / "AGENTS.md").write_text(AGENTS_MD)
    written = []
    for p in _agent_files():
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(AGENTS_MD)
            written.append(str(p))
    Path(".psf").mkdir(exist_ok=True)
    from .evaluation import ensure_eval_dir

    ensure_eval_dir("eval")
    print(f"initialized factory in {root}/  (agents/, factory.yml, eval/)")
    print(f"agent instructions written for discoverability: {', '.join(written) or '(already present)'}")
    print(f"autonomy: mode={mode}  (switch anytime: `psf mode hitl|yolo`)")
    print(f"feedback: mode={fb_mode} upstream={upstream}  (change with `psf feedback opt-out|opt-in`)")
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


def cmd_improve(args) -> int:
    factory = load_factory(args.factory)
    # YOLO mode promotes automatically (still eval/audit/canary gated); HITL needs --promote.
    promote = args.promote or (factory.autonomous and not args.rollback)
    cand = args.candidate
    if cand is not None and str(cand).isdigit():
        cand = int(cand)
    r = run_improvement(args.factory, args.ledger, promote=promote, rollback=args.rollback,
                        field=args.field, candidate=cand)
    if args.rollback:
        print("rolled back" if r.rolled_back else "nothing to roll back")
        return 0 if r.rolled_back else 1
    p = r.proposal
    print(f"proposal: {p.field} {p.current} -> {p.candidate}  ({p.reason})")
    for n in r.notes:
        print(f"  {n}")
    if r.promoted:
        print("status: PROMOTED — the factory improved itself with human authorization")
        return 0
    if not r.actionable:
        print("status: no actionable improvement — no human action needed")
        return 0
    return 10  # recommendation made, awaiting human authorization


def _set_mode(mode: str, factory_path: str = "factory") -> Path:
    if mode not in ("hitl", "yolo"):
        raise ValueError("mode must be hitl or yolo")
    import yaml

    p = Path(factory_path)
    p = p / "factory.yml" if p.is_dir() else p
    raw = yaml.safe_load(p.read_text()) or {}
    raw["mode"] = mode
    # yolo/hitl are not YAML booleans, but quote for safety/consistency
    text = yaml.safe_dump(raw, sort_keys=False)
    import re
    text = re.sub(r"(?m)^(mode:\s*)(hitl|yolo)\s*$", r"\1'\2'", text)
    p.write_text(text)
    return p


def cmd_mode(args) -> int:
    if args.value:
        _set_mode(args.value, args.factory)
        print(f"autonomy mode set to {args.value}  (hitl = you approve; yolo = autonomous)")
        return 0
    f = load_factory(args.factory)
    print(f"autonomy mode: {f.mode}")
    return 0


def cmd_run(args) -> int:
    factory, log, wf = _load(args)
    if getattr(args, "runner", None):
        factory.runner = args.runner
    if getattr(args, "command", None):
        import shlex
        factory.runner_options["command"] = shlex.split(args.command)

    # Autonomy mode: flag > interactive prompt (each run) > factory default.
    mode = getattr(args, "mode", None) or factory.mode
    if getattr(args, "mode", None) is None and sys.stdin.isatty() and not getattr(args, "no_ask", False):
        try:
            ans = input(f"Autonomy mode? [hitl/yolo] ({factory.mode}): ").strip().lower()
        except EOFError:
            ans = ""
        if ans in ("hitl", "yolo"):
            mode = ans
    factory.mode = mode
    log.append("ModeSelected", {"mode": mode, "surface": "run"}, actor="owner")

    # Classifier / supervisor overrides (advisory only).
    if getattr(args, "classifier", None):
        factory.classifier["provider"] = args.classifier
    if getattr(args, "supervise", False):
        factory.classifier.setdefault("supervisor", {})["enabled"] = True
    from .classifier import build_classifier

    classifier = build_classifier(factory.classifier) if factory.supervisor_enabled else None

    repo = Path.cwd() if args.git else None
    from .durability import Durability

    durability = Durability(Path(args.ledger).with_name("durability.db"))
    result = Foreman(factory, wf, durability=durability, classifier=classifier).run(
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

    if getattr(args, "github", False) and work.state in ("HANDOFF", "DONE") and repo is not None:
        from .github import available, find_pr_for_branch, publish_draft_pr

        if not available():
            print("  github: `gh` not available; skipping draft PR", file=sys.stderr)
        else:
            wt = repo / ".psf" / "worktrees" / work.id
            branch = f"psf/{work.id}"
            key = f"{work.id}:github.pr"

            def _sender():
                url, err = publish_draft_pr(wt, title=work.goal,
                                            body=f"Work item {work.id}\nspec {work.spec_digest}")
                if err:
                    raise RuntimeError(err)
                return {"url": url}

            item = durability.record_effect(work.id, "github.pr", {"branch": branch}, key=key)
            if item.status == "UNKNOWN":
                # reconcile by observing the remote before any resend
                existing = find_pr_for_branch(branch)
                item = durability.reconcile(key, lambda: {"url": existing} if existing else None)
            if item.status != "CONFIRMED":
                item = durability.send(key, _sender)
            detail = item.response_digest or item.status
            print(f"  github: draft PR {item.status} ({detail})")
    return 0 if work.state in ("DONE", "HANDOFF") else 3


def cmd_status(args) -> int:
    _, log, wf = _load(args)
    ids = [args.work_id] if args.work_id else log.work_ids()
    if args.json:
        print(json.dumps([wf.fold(wid).to_dict() for wid in ids], indent=2))
        return 0
    if not ids:
        print("no work items")
        return 0
    for wid in ids:
        w = wf.fold(wid)
        print(f"{w.id}  {w.state:12}  {w.goal}  attempts {w.attempts}/{w.max_attempts}")
    return 0


def cmd_feedback(args) -> int:
    from .feedback import export, ingest, publish_issue, report

    if args.action == "opt-out":
        _set_feedback(mode="off", factory_path=args.factory)
        print("feedback: OFF — nothing will be sent; re-enable with `psf feedback opt-in`")
        return 0
    if args.action == "opt-in":
        mode = "auto" if getattr(args, "auto", False) else "hint"
        _set_feedback(mode=mode, factory_path=args.factory)
        upstream, _ = _feedback_cfg(args)
        print(f"feedback: {mode.upper()} (upstream={upstream or '(unset)'})")
        return 0
    if args.action == "status":
        upstream, mode = _feedback_cfg(args)
        print(f"feedback: mode={mode} upstream={upstream or '(unset)'}")
        return 0

    if args.action == "export":
        upstream, mode = _feedback_cfg(args)
        if mode == "off":
            print("feedback is OFF — `psf feedback opt-in` to enable (nothing was sent)")
            return 0
        target = args.github or (upstream if mode == "auto" else None)
        path = export(args.factory, args.ledger, out=args.out, repo=target)
        print(f"wrote {path}")
        if target:
            import json as _json
            env = _json.loads(Path(path).read_text())
            url, err = publish_issue(target, env)
            print(url or f"issue create failed: {err}")
        elif upstream:
            print(f"hint: send this upstream with `psf feedback export --github {upstream}`")
            print("      (`psf feedback opt-in --auto` to publish by default; `psf feedback opt-out` to disable)")
    elif args.action == "ingest":
        if not args.path:
            print("error: ingest needs a file or directory", file=sys.stderr)
            return 2
        n = ingest(".psf/feedback/inbox", args.path)
        print(f"ingested {n} envelope(s)")
    else:  # report
        print(json.dumps(report(".psf/feedback/inbox"), indent=2))
    return 0


def cmd_calibrate(args) -> int:
    from .calibrate import records_from_ledger, reliability, sweep

    _, log, _ = _load(args)
    recs = records_from_ledger(log, question=args.question)
    rep = {"question": args.question, "n": len(recs), "sweep": sweep(recs),
           "reliability": reliability(recs)}
    print(json.dumps(rep, indent=2))
    return 0


def cmd_eval_supervisor(args) -> int:
    from .supveval import run_supervisor_eval

    rep = run_supervisor_eval()
    if args.out:
        Path(args.out).write_text(json.dumps(rep, indent=2) + "\n")
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        for e in rep["evals"]:
            print(f"[{'PASS' if e['status'] == 'pass' else 'FAIL'}] {e['id']:4} {e['name']}")
        print(f"supervisor evals: {rep['passed']}/{rep['total']} passed")
        for i in rep["issues"]:
            print(f"  - {i['id']} {i['name']}: {i['detail']}")
    return 0 if rep["failed"] == 0 else 1


def cmd_eval_oss(args) -> int:
    from .ossbench import run_oss_task

    specs = (args.repos or "/tmp/oss/flask:change").split(",")
    results = []
    for spec in specs:
        path, _, kind = spec.partition(":")
        results.append(run_oss_task(path, kind=kind or "change", claude_script=args.claude_script))
    rep = {"total": len(results), "resolved": sum(1 for r in results if r.get("resolved")),
           "results": results}
    if args.out:
        Path(args.out).write_text(json.dumps(rep, indent=2) + "\n")
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        for r in results:
            print(f"{r['repo']:10} {r['kind']:12} resolved={r.get('resolved')} "
                  f"state={r.get('state')} attempts={r.get('attempts')} "
                  f"stats={r.get('stats', {}).get('files')} files "
                  f"{r.get('error') or ''}")
        print(f"resolved {rep['resolved']}/{rep['total']}")
    return 0 if rep["resolved"] == rep["total"] else 1


def cmd_eval_repos(args) -> int:
    from .repobench import run_matrix

    rep = run_matrix(
        sizes=args.sizes.split(",") if args.sizes else None,
        domains=args.domains.split(",") if args.domains else None,
        mode=args.mode, root=args.root, claude_script=args.claude_script,
    )
    if args.out:
        Path(args.out).write_text(json.dumps(rep, indent=2) + "\n")
    if args.json:
        print(json.dumps(rep, indent=2))
        return 0 if rep["resolve_rate"] == 1.0 else 1
    print(f"mode={args.mode}  repos={rep['total']}  resolved={rep['resolved']} "
          f"({rep['resolve_rate']:.0%})")
    print("by size:", {k: f"{v['resolved']}/{v['total']}" for k, v in rep["by_size"].items()})
    for r in rep["repos"]:
        if not r["resolved"]:
            print(f"  UNRESOLVED {r['repo']}  state={r['state']} attempts={r['attempts']}")
    if args.out:
        print(f"wrote {args.out}")
    return 0 if rep["resolve_rate"] == 1.0 else 1


def cmd_evals(args) -> int:
    from .evalgov import (add_candidate, approve_candidate, integrity, retire_case,
                          rotate_holdout, status as gov_status)

    d = args.eval_dir
    if args.action == "add":
        p = add_candidate(d, case_id=args.case_id, goal=args.goal,
                          solves_on_attempt=args.solves_on_attempt, source=args.source,
                          owner=args.owner)
        print(f"candidate added to {p} (provenance {args.source})")
    elif args.action == "approve":
        case = approve_candidate(d, args.case_id, approver=args.approver, author=args.author)
        print(f"approved {case['id']} by {args.approver} (author {args.author})")
    elif args.action == "rotate":
        out = rotate_holdout(d, n=args.n, approver=args.approver, author=args.author)
        print(f"rotated: {out}")
    elif args.action == "retire":
        case = retire_case(d, args.case_id, reason=args.reason, approver=args.approver, author=args.author)
        print(f"retired {case['id']}: {case['reason']}")
    else:  # status
        print(json.dumps({"status": gov_status(d), "integrity": integrity(d)}, indent=2))
    return 0


def cmd_eval_gov(args) -> int:
    from .evalgov import run_governance_eval

    rep = run_governance_eval()
    if args.out:
        Path(args.out).write_text(json.dumps(rep, indent=2) + "\n")
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        for e in rep["evals"]:
            print(f"[{'PASS' if e['status'] == 'pass' else 'FAIL'}] {e['id']:5} {e['name']}")
        print(f"governance evals: {rep['passed']}/{rep['total']} passed")
        for i in rep["issues"]:
            print(f"  - {i['id']} {i['name']}: {i['detail']}")
    return 0 if rep["failed"] == 0 else 1


def cmd_eval_self(args) -> int:
    from .selfeval import run_self_eval

    rep = run_self_eval()
    if args.out:
        Path(args.out).write_text(json.dumps(rep, indent=2) + "\n")
    if args.json:
        print(json.dumps(rep, indent=2))
        return 0 if rep["failed"] == 0 else 1
    for e in rep["evals"]:
        mark = "PASS" if e["status"] == "pass" else "FAIL"
        print(f"[{mark}] {e['id']:5} {e['name']}")
    print(f"self-eval: {rep['passed']}/{rep['total']} passed")
    if rep["issues"]:
        print("issues:")
        for i in rep["issues"]:
            print(f"  - {i['id']} {i['name']}: {i['detail']}")
    if args.out:
        print(f"wrote {args.out}")
    return 0 if rep["failed"] == 0 else 1


def cmd_eval_suite(args) -> int:
    from .evalsuite import run_suite

    rep = run_suite(seeds=args.seeds, per_tier=args.per_tier, q=args.q, verify_quorum=args.verify_quorum)
    if args.out:
        Path(args.out).write_text(json.dumps(rep, indent=2) + "\n")
    if args.json:
        print(json.dumps(rep, indent=2))
        return 0
    print(f"{'tier':7} {'att':>4} {'base ok':>8} {'base def':>9} {'resolved':>9} "
          f"{'shipped def':>12} {'unres':>6} {'attempts':>9}")
    for tier, t in rep["process"]["tiers"].items():
        print(f"{tier:7} {t['attempted']:>4} {t['baseline_success']:>8} {t['baseline_defects']:>9} "
              f"{t['resolved']:>9} {t['shipped_defects']:>12} {t['unresolved']:>6} {t['avg_attempts']:>9}")
    v = rep["verifier"]
    print(f"verifier: TP {v['tp_rate']:.0%} ({v['true_positive']}/{v['n_bad']}, ci {v['tp_ci']})  "
          f"FP {v['fp_rate']:.0%} ({v['false_positive']}/{v['n_good']})")
    print("findings:")
    for f in rep["findings"]:
        print(f"  [{f['status']:8}] {f['id']} ({f['severity']}) {f['claim']}")
    if args.out:
        print(f"wrote {args.out}")
    return 0


def cmd_eval(args) -> int:
    from .evaluation import run_eval

    factory, _, _ = _load(args)
    candidate = args.candidate or (factory.max_attempts + 1)
    ev = run_eval("eval", baseline_attempts=factory.max_attempts, candidate_attempts=candidate)
    print(json.dumps(ev.to_dict(), indent=2))
    return 0 if ev.decision == "PROMOTE" else 1


def cmd_outcome(args) -> int:
    _, log, _ = _load(args)
    log.append("OutcomeRecorded", {
        "accepted": args.accepted, "review_escape": args.escape,
        "cost_usd": args.cost, "human_minutes": args.minutes,
    }, work_id=args.work_id, actor="owner")
    print(f"recorded outcome for {args.work_id}")
    return 0


def cmd_metrics(args) -> int:
    _, log, wf = _load(args)
    states: dict[str, int] = {}
    attempts = retries = blocked = 0
    for wid in log.work_ids():
        w = wf.fold(wid)
        states[w.state] = states.get(w.state, 0) + 1
        attempts += w.attempts
        retries += max(0, w.attempts - 1)
        if w.state == "BLOCKED":
            blocked += 1
    ok, msg = log.verify_chain()
    # outcome signals (M4)
    accepted = escapes = 0
    cost = minutes = 0.0
    for e in log.all():
        if e.type == "OutcomeRecorded":
            accepted += int(bool(e.payload.get("accepted")))
            escapes += int(bool(e.payload.get("review_escape")))
            cost += float(e.payload.get("cost_usd", 0) or 0)
            minutes += float(e.payload.get("human_minutes", 0) or 0)
    if args.json:
        print(json.dumps({
            "work_items": sum(states.values()),
            "states": {s: states[s] for s in sorted(states)},
            "attempts": attempts, "retries": retries, "blocked": blocked,
            "outcomes": {
                "accepted": accepted, "review_escape": escapes,
                "cost_usd": cost, "human_minutes": minutes,
            },
            "events": log.count(),
            "chain": {"ok": ok, "message": msg},
        }, indent=2))
        return 0 if ok else 4
    print(f"work items: {sum(states.values())}")
    for s in sorted(states):
        print(f"  {s:12} {states[s]}")
    print(f"attempts: {attempts}  retries: {retries}  blocked: {blocked}")
    print(f"outcomes: accepted {accepted}  review-escape {escapes}  cost ${cost:.2f}  human {minutes:.0f} min")
    print(f"events: {log.count()}  chain: {msg}")
    return 0 if ok else 4


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


def cmd_audit(args) -> int:
    report = run_audit(args.factory, args.ledger, include_bench=not args.fast)
    for c in report.checks:
        mark = {"ok": "OK  ", "warn": "WARN", "fail": "FAIL"}[c.status]
        print(f"[{mark}] {c.name:32} {c.detail}")
    print(f"healthy: {report.healthy}")
    if not report.healthy:
        return 4
    return 0


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
    s.add_argument("--feedback", choices=["off", "hint", "auto"],
                   help="feedback consent at install time (default: ask, else hint)")
    s.add_argument("--upstream", help="upstream repo for feedback (owner/repo)")
    s.add_argument("--mode", choices=["hitl", "yolo"],
                   help="autonomy at install time (default: ask, else hitl)")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("validate", help="compile-check the factory definition")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("run", help="run one goal through the factory")
    s.add_argument("goal")
    s.add_argument("--no-approve", action="store_true", help="stop at SPEC_REVIEW and wait")
    s.add_argument("--finish", action="store_true", default=True)
    s.add_argument("--git", action="store_true", help="isolate work in a git worktree and keep it as the handoff branch")
    s.add_argument("--runner", choices=["mock", "subprocess"], help="override the factory runner")
    s.add_argument("--command", help="command for the subprocess runner (shell-split)")
    s.add_argument("--github", action="store_true", help="publish the handoff as a draft GitHub PR (needs gh)")
    s.add_argument("--mode", choices=["hitl", "yolo"], help="autonomy for this run (overrides the factory default)")
    s.add_argument("--no-ask", action="store_true", help="do not prompt for the mode")
    s.add_argument("--classifier", choices=["mock", "jev"], help="advisory classifier provider")
    s.add_argument("--supervise", action="store_true", help="enable the advisory supervisor for this run")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("mode", help="show or set autonomy mode (hitl | yolo); switchable anytime")
    s.add_argument("value", nargs="?", choices=["hitl", "yolo"])
    s.set_defaults(func=cmd_mode)

    s = sub.add_parser("status", help="show work items")
    s.add_argument("work_id", nargs="?")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("metrics", help="outcome signals from the ledger")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_metrics)

    s = sub.add_parser("eval", help="run the protected evaluation (M3)")
    s.add_argument("--candidate", type=int, help="candidate max_attempts (default: current+1)")
    s.set_defaults(func=cmd_eval)

    s = sub.add_parser("eval-self", help="run the self-improvement eval suite (E2/E5/E6/E7/E10/E15/E16/E19)")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", help="write the JSON report to this path")
    s.set_defaults(func=cmd_eval_self)

    s = sub.add_parser("eval-gov", help="run the eval-governance eval suite (G1..G8)")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", help="write the JSON report to this path")
    s.set_defaults(func=cmd_eval_gov)

    s = sub.add_parser("eval-repos", help="multi-repo capability eval (sizes x domains)")
    s.add_argument("--mode", choices=["process", "real"], default="process")
    s.add_argument("--sizes", help="comma list: tiny,small,medium,large")
    s.add_argument("--domains", help="comma list: cli,api,etl,lib,script")
    s.add_argument("--claude-script", help="path to the claude runner script (real mode)")
    s.add_argument("--root", help="root dir to build repos under")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", help="write the JSON report to this path")
    s.set_defaults(func=cmd_eval_repos)

    s = sub.add_parser("eval-oss", help="real OSS-repo eval (localization / change)")
    s.add_argument("--repos", help="comma list of path[:kind], e.g. /tmp/oss/flask:change")
    s.add_argument("--claude-script", help="path to the claude runner script")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", help="write the JSON report to this path")
    s.set_defaults(func=cmd_eval_oss)

    s = sub.add_parser("eval-supervisor", help="supervisor/classifier evals (S1..S8)")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", help="write the JSON report to this path")
    s.set_defaults(func=cmd_eval_supervisor)

    s = sub.add_parser("calibrate", help="calibrate classifier thresholds from recorded outcomes")
    s.add_argument("--question", default="worker_stuck")
    s.set_defaults(func=cmd_calibrate)

    s = sub.add_parser("evals", help="govern the eval suite: add / approve / rotate / retire / status")
    s.add_argument("action", choices=["add", "approve", "rotate", "retire", "status"])
    s.add_argument("--eval-dir", default="eval")
    s.add_argument("--case-id")
    s.add_argument("--goal")
    s.add_argument("--solves-on-attempt", type=int, default=1)
    s.add_argument("--source", help="provenance: finding id / issue / spec")
    s.add_argument("--owner", default="owner")
    s.add_argument("--approver", default="owner")
    s.add_argument("--author", default="system")
    s.add_argument("--n", type=int, default=1, help="cases to rotate into the holdout")
    s.add_argument("--reason", default="")
    s.set_defaults(func=cmd_evals)

    s = sub.add_parser("eval-suite", help="run the process + verifier eval suite (see docs/EVAL-PLAN.md)")
    s.add_argument("--seeds", type=int, default=5)
    s.add_argument("--per-tier", type=int, default=20)
    s.add_argument("--q", type=float, default=0.9, help="verifier detection probability")
    s.add_argument("--verify-quorum", type=int, default=1, help="independent verifications per build")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", help="write the JSON report to this path")
    s.set_defaults(func=cmd_eval_suite)

    s = sub.add_parser("outcome", help="record an outcome for a work item (M4)")
    s.add_argument("work_id")
    s.add_argument("--accepted", action="store_true")
    s.add_argument("--escape", action="store_true", help="review escaped a defect")
    s.add_argument("--cost", type=float, default=0.0)
    s.add_argument("--minutes", type=float, default=0.0, help="human minutes spent")
    s.set_defaults(func=cmd_outcome)

    s = sub.add_parser("feedback", help="consumer feedback loop (export / ingest / report / opt-out / opt-in / status)")
    s.add_argument("action", choices=["export", "ingest", "report", "opt-out", "opt-in", "status"])
    s.add_argument("path", nargs="?", help="for ingest: an export file or directory")
    s.add_argument("--out", help="for export: output file")
    s.add_argument("--github", help="for export: file the envelope as an issue in this repo")
    s.add_argument("--auto", action="store_true", help="for opt-in: publish automatically")
    s.set_defaults(func=cmd_feedback)

    s = sub.add_parser("log", help="print the ledger")
    s.add_argument("work_id", nargs="?")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_log)

    s = sub.add_parser("improve", help="governed improvement: propose -> evaluate -> canary -> human promote")
    s.add_argument("--promote", action="store_true", help="authorize promotion if the candidate is safe and better")
    s.add_argument("--rollback", action="store_true", help="restore the previous factory revision")
    s.add_argument("--field", help="propose a specific allow-listed field (protected fields are refused)")
    s.add_argument("--candidate", help="candidate value for --field")
    s.set_defaults(func=cmd_improve)

    s = sub.add_parser("audit", aliases=["doctor"], help="self-check: ledger, factory, state integrity, benchmark")
    s.add_argument("--fast", action="store_true", help="skip the benchmark check")
    s.set_defaults(func=cmd_audit)

    s = sub.add_parser("bench", help="run the internal benchmark")
    s.add_argument("--max-attempts", type=int, default=2)
    s.set_defaults(func=cmd_bench)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FactoryError, GateError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
