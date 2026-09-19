"""Self-audit / health check.

The factory checks its own health before it is trusted to change anything. This
is deliberately a factory mechanism, not an external script: ``psf audit`` is the
thing the periodic loop runs, and later the improvement controller requires a
green audit before it will promote a candidate.

Checks
- ledger:    hash chain verifies (tamper/gap detection)
- factory:   factory.yml compiles
- integrity: every recorded transition is legal; READY/HANDOFF require a
             matching, digest-bound approval
- benchmark: the process still catches what a single pass misses, without
             regression
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bench import run_benchmark
from .events import EventLog
from .schema import FactoryError, load as load_factory
from .state import TERMINAL, TRANSITIONS, Workflow

OK, WARN, FAIL = "ok", "warn", "fail"


@dataclass
class Check:
    name: str
    status: str
    detail: str


@dataclass
class AuditReport:
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str) -> None:
        self.checks.append(Check(name, status, detail))

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.status == FAIL]

    @property
    def healthy(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        return {"healthy": self.healthy,
                "checks": [{"name": c.name, "status": c.status, "detail": c.detail} for c in self.checks]}


def _legal(from_state: str, to_state: str) -> bool:
    if to_state == "BLOCKED":
        return from_state not in TERMINAL and from_state != "BLOCKED"
    return to_state in TRANSITIONS.get(from_state, ())


def audit_ledger(log: EventLog, wf: Workflow) -> list[Check]:
    checks: list[Check] = []
    ok, msg = log.verify_chain()
    checks.append(Check("ledger.chain", OK if ok else FAIL, msg))

    ids = log.work_ids()
    illegal, unapproved = [], []
    for wid in ids:
        w = wf.fold(wid)
        for t in w.transitions:
            a, b = t.split("->")
            if not _legal(a, b) and b != w.blocked_from:
                illegal.append(f"{wid}:{t}")
        if w.state in ("READY", "BUILD", "VERIFY", "REVIEW", "HANDOFF", "DONE"):
            if not (w.spec_digest and w.approval_digest == w.spec_digest):
                unapproved.append(f"{wid}:{w.state}")
    checks.append(Check("state.illegal_transitions", OK if not illegal else FAIL,
                        "none" if not illegal else ", ".join(illegal[:5])))
    checks.append(Check("state.digest_bound_approval", OK if not unapproved else FAIL,
                        "all approved work items are digest-bound" if not unapproved
                        else "missing/mismatched approval: " + ", ".join(unapproved[:5])))
    checks.append(Check("ledger.work_items", OK, f"{len(ids)} work item(s)"))
    return checks


def run_audit(factory_path: str | Path = "factory", ledger_path: str | Path = ".psf/factory.db",
              *, include_bench: bool = True) -> AuditReport:
    report = AuditReport()

    fp = Path(factory_path)
    if fp.exists():
        try:
            f = load_factory(fp)
            report.add("factory.compile", OK, f"{f.name} runner={f.runner} max_attempts={f.max_attempts}")
        except FactoryError as e:
            report.add("factory.compile", FAIL, str(e).splitlines()[0])
    else:
        report.add("factory.compile", WARN, f"no factory at {fp} (run `psf init`)")

    lp = Path(ledger_path)
    if lp.exists():
        log = EventLog(lp)
        try:
            for c in audit_ledger(log, Workflow(log)):
                report.add(c.name, c.status, c.detail)
        finally:
            log.close()
    else:
        report.add("ledger.chain", WARN, f"no ledger at {lp}")

    if include_bench:
        try:
            r = run_benchmark()
            status = OK if (r.factory_pass == r.total and r.factory_pass >= r.baseline_pass) else FAIL
            report.add("benchmark.non_regression", status,
                       f"baseline {r.baseline_rate:.0%} -> factory {r.factory_rate:.0%} ({r.factory_pass}/{r.total})")
        except Exception as e:  # noqa: BLE001 - audit must never crash the caller
            report.add("benchmark.non_regression", FAIL, f"benchmark error: {e}")

        # Guardrails and harness adapters are part of health: run their suites.
        from .adaptereval import run_adapter_eval
        from .guardeval import run_guardrail_eval

        for name, suite in (("guardrails.suite", run_guardrail_eval),
                            ("adapters.suite", run_adapter_eval)):
            try:
                r = suite()
                report.add(name, OK if r["failed"] == 0 else FAIL, f"{r['passed']}/{r['total']} passed")
            except Exception as e:  # noqa: BLE001
                report.add(name, FAIL, f"suite error: {e}")
    return report
