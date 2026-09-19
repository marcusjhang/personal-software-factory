#!/usr/bin/env python3
"""Multi-repo eval orchestrator.

For a matrix of repos (size x domain): build the repo, `psf init`, run the task
through the factory, then GROW that repo's eval set from the outcome (under
governance) and run the self-improvement loop in that repo. Records everything.

Run:  PYTHONPATH=src python3 scripts/multi_repo_eval.py [--real] [--sizes ...]
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from psf import cli  # noqa: E402
from psf.evalgov import integrity, status as gov_status  # noqa: E402
from psf.events import EventLog  # noqa: E402
from psf.foreman import Foreman  # noqa: E402
from psf.improve import run_improvement  # noqa: E402
from psf.repobench import (DOMAINS, SIZES, RepoProcessRunner, RepoRealRunner,  # noqa: E402
                           build_repo, task_goal)
from psf.schema import load as load_factory  # noqa: E402
from psf.state import Workflow  # noqa: E402


def run_one(size, domain, root, real, claude_script):
    repo = build_repo(root / f"{size}-{domain}", size, domain)
    cwd = os.getcwd()
    os.chdir(repo)
    try:
        cli.main(["init", "--feedback", "off", "--mode", "yolo"])
    finally:
        os.chdir(cwd)
    log = EventLog(repo / ".psf" / "factory.db")
    runner = (RepoRealRunner(claude_script) if real else RepoProcessRunner(domain))
    result = {"repo": f"{size}-{domain}", "size": size, "domain": domain, "real": real}
    try:
        res = Foreman(load_factory(repo / "factory"), Workflow(log), runner).run(
            task_goal(size, domain), repo=repo, use_git=True, finish=False)
        result.update(state=res.work.state, attempts=res.work.attempts,
                      resolved=bool(res.verify_passed and res.work.state in
                                    ("REVIEW", "HANDOFF", "DONE")))
    except Exception as e:  # noqa: BLE001
        result.update(state="ERROR", attempts=0, resolved=False, error=repr(e))
    log.close()

    # grow this repo's eval set from the outcome, then run the self-improvement loop
    os.chdir(repo)
    try:
        from psf.repobench import grow_evals_per_repo
        grow = grow_evals_per_repo(repo / "eval", domain=domain, size=size,
                                   source=f"repo:{size}-{domain}:resolved={result.get('resolved')}")
        result["eval_status"] = grow["status"]
        result["eval_integrity"] = grow["integrity"]
        imp = run_improvement("factory", ".psf/factory.db", promote=(load_factory("factory").autonomous))
        result["improve"] = {"promoted": imp.promoted, "actionable": imp.actionable,
                             "notes": imp.notes[:2]}
    except Exception as e:  # noqa: BLE001
        result["improve_error"] = repr(e)
    finally:
        os.chdir(cwd)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--sizes")
    ap.add_argument("--domains")
    ap.add_argument("--root", default="/tmp/psf-multirepo")
    ap.add_argument("--claude-script")
    ap.add_argument("--out", default="docs/reports/multi-repo.json")
    args = ap.parse_args()

    sizes = args.sizes.split(",") if args.sizes else list(SIZES)
    domains = args.domains.split(",") if args.domains else list(DOMAINS)
    root = Path(args.root)
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)

    repos = [run_one(s, d, root, args.real, args.claude_script) for s in sizes for d in domains]
    resolved = sum(1 for r in repos if r.get("resolved"))
    by_size = {}
    for r in repos:
        s = by_size.setdefault(r["size"], {"total": 0, "resolved": 0})
        s["total"] += 1
        s["resolved"] += int(r.get("resolved", False))
    report = {"real": args.real, "total": len(repos), "resolved": resolved,
              "resolve_rate": resolved / len(repos) if repos else 0.0,
              "by_size": by_size, "repos": repos}
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(f"real={args.real} repos={len(repos)} resolved={resolved} ({report['resolve_rate']:.0%})")
    print("by size:", {k: f"{v['resolved']}/{v['total']}" for k, v in by_size.items()})
    bad = [r["repo"] for r in repos if not r.get("resolved")]
    if bad:
        print("unresolved:", bad)
    gi = [r["repo"] for r in repos if r.get("eval_integrity")]
    if gi:
        print("eval-integrity problems:", gi)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
