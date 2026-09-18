"""Eval governance — the lifecycle that lets the eval suite grow safely.

Implements the plan in docs/EVAL-GOVERNANCE.md: two tiers (optimization vs
protected holdout), a candidate staging area, and retirement as quarantine.
Enforces G1–G8 in code and exposes `run_governance_eval()` (evals G1..G8).
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from .evalkit import EvalResult, make_eval_dir, wilson  # noqa: F401  (wilson re-exported)

TIERS = {"optimization": "tasks.json", "holdout": "holdout.json",
         "candidate": "candidates.json", "retired": "retired.json"}
LEAK_MARKERS = ("```", "diff --git", "def ", "patch", "solution:")


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _expiry(days: int) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(time.time() + days * 86400))


def _read(eval_dir: Path, tier: str) -> dict:
    p = Path(eval_dir) / TIERS[tier]
    return json.loads(p.read_text()) if p.exists() else {"tasks": []}


def _write(eval_dir: Path, tier: str, data: dict) -> None:
    (Path(eval_dir) / TIERS[tier]).write_text(json.dumps(data, indent=2) + "\n")


def _all_cases(eval_dir: Path) -> list[tuple[str, dict]]:
    out = []
    for tier in TIERS:
        for c in _read(eval_dir, tier).get("tasks", []):
            out.append((tier, c))
    return out


def _ids(eval_dir: Path) -> set[str]:
    return {c["id"] for _, c in _all_cases(eval_dir)}


def looks_like_solution(goal: str) -> bool:
    low = goal.lower()
    return any(m in low for m in LEAK_MARKERS)


def add_candidate(eval_dir: str | Path, *, case_id: str, goal: str, solves_on_attempt: int,
                  source: str, owner: str, ttl_days: int = 90) -> Path:
    """G1 provenance + G4 no-leakage + unique id. Writes only the candidate tier."""
    eval_dir = Path(eval_dir)
    if not source:
        raise ValueError("provenance required: a case must name its source (G1)")
    if looks_like_solution(goal):
        raise ValueError("case looks like it embeds a solution/patch — refused (G4)")
    if case_id in _ids(eval_dir):
        raise ValueError(f"duplicate case id {case_id}")
    data = _read(eval_dir, "candidate")
    data["tasks"].append({
        "id": case_id, "goal": goal, "solves_on_attempt": int(solves_on_attempt),
        "source": source, "owner": owner, "status": "candidate",
        "created": _today(), "expires": _expiry(ttl_days),
    })
    _write(eval_dir, "candidate", data)
    return eval_dir / TIERS["candidate"]


def _move(eval_dir: Path, case_id: str, frm: str, to: str, *, extra: dict | None = None) -> dict:
    frm_data = _read(eval_dir, frm)
    case = next((c for c in frm_data["tasks"] if c["id"] == case_id), None)
    if case is None:
        raise KeyError(f"{case_id} not in {frm}")
    frm_data["tasks"] = [c for c in frm_data["tasks"] if c["id"] != case_id]
    _write(eval_dir, frm, frm_data)
    case = dict(case)
    if extra:
        case.update(extra)
    to_data = _read(eval_dir, to)
    to_data["tasks"].append(case)
    _write(eval_dir, to, to_data)
    return case


def approve_candidate(eval_dir: str | Path, case_id: str, *, approver: str, author: str) -> dict:
    """G2 separate approval: promote a candidate into the optimization set."""
    if not approver or approver == author:
        raise ValueError("self-approval refused: approver must differ from author (G2)")
    case = _move(Path(eval_dir), case_id, "candidate", "optimization",
                 extra={"status": "active", "approved_by": approver, "approved": _today()})
    return case


def rotate_holdout(eval_dir: str | Path, *, n: int, approver: str, author: str) -> dict:
    """G2/G5/G8: move n optimization cases into the holdout and refill from candidates."""
    if not approver or approver == author:
        raise ValueError("self-approval refused: rotation approver must differ (G2)")
    eval_dir = Path(eval_dir)
    opt = _read(eval_dir, "optimization")["tasks"]
    moved = []
    for case in opt[:max(0, n)]:
        moved.append(_move(eval_dir, case["id"], "optimization", "holdout",
                           extra={"status": "holdout", "rotated": _today()}))
    # refill the optimization set from candidates, if any
    cands = _read(eval_dir, "candidate")["tasks"]
    for case in cands[:len(moved)]:
        _move(eval_dir, case["id"], "candidate", "optimization",
              extra={"status": "active", "approved_by": approver, "approved": _today()})
    return {"moved_to_holdout": [c["id"] for c in moved]}


def retire_case(eval_dir: str | Path, case_id: str, *, reason: str, approver: str, author: str) -> dict:
    """G2/G6: quarantine a case (never delete)."""
    if not approver or approver == author:
        raise ValueError("self-approval refused: retirement approver must differ (G2)")
    if not reason:
        raise ValueError("retirement requires a reason (G6)")
    eval_dir = Path(eval_dir)
    tier = next((t for t, c in _all_cases(eval_dir) if c["id"] == case_id), None)
    if tier is None:
        raise KeyError(case_id)
    return _move(eval_dir, case_id, tier, "retired",
                 extra={"status": "retired", "reason": reason, "retired": _today()})


def status(eval_dir: str | Path) -> dict:
    eval_dir = Path(eval_dir)
    return {tier: len(_read(eval_dir, tier)["tasks"]) for tier in TIERS}


def integrity(eval_dir: str | Path) -> list[str]:
    """G1/G7/G8 checks. Returns a list of problems (empty = healthy)."""
    eval_dir = Path(eval_dir)
    problems: list[str] = []
    seen: dict[str, str] = {}
    for tier, case in _all_cases(eval_dir):
        cid = case["id"]
        if cid in seen:
            problems.append(f"G8 duplicate id {cid} in {seen[cid]} and {tier}")
        seen[cid] = tier
        if not case.get("source"):
            problems.append(f"G1 {cid} missing provenance")
        exp = case.get("expires")
        if exp and exp < _today():
            problems.append(f"G7 {cid} expired ({exp}) needs re-validation")
    opt = {c["id"] for c in _read(eval_dir, "optimization")["tasks"]}
    hol = {c["id"] for c in _read(eval_dir, "holdout")["tasks"]}
    overlap = opt & hol
    if overlap:
        problems.append(f"G8 optimization and holdout overlap: {sorted(overlap)}")
    return problems


# --- governance eval suite (G1..G8) ------------------------------------------

def _temp_eval(tmp: Path) -> Path:
    return make_eval_dir(tmp, tasks=[{"id": "e1", "goal": "add x", "solves_on_attempt": 1}],
                         holdout=[{"id": "h1", "goal": "add y", "solves_on_attempt": 1}])


def eval_G1(tmp: Path) -> EvalResult:
    d = _temp_eval(tmp / "g1")
    refused = False
    try:
        add_candidate(d, case_id="c1", goal="add z", solves_on_attempt=2, source="", owner="o")
    except ValueError:
        refused = True
    add_candidate(d, case_id="c1", goal="add z", solves_on_attempt=2, source="F1", owner="o")
    ok = refused and status(d)["candidate"] == 1
    return EvalResult("G1", "provenance required", "pass" if ok else "fail",
                      {"refused_without_source": refused, **status(d)})


def eval_G2(tmp: Path) -> EvalResult:
    d = _temp_eval(tmp / "g2")
    add_candidate(d, case_id="c1", goal="add z", solves_on_attempt=2, source="F1", owner="alice")
    self_refused = False
    try:
        approve_candidate(d, "c1", approver="alice", author="alice")
    except ValueError:
        self_refused = True
    approve_candidate(d, "c1", approver="bob", author="alice")
    ok = self_refused and status(d)["optimization"] == 2
    return EvalResult("G2", "separate approval", "pass" if ok else "fail",
                      {"self_approval_refused": self_refused, **status(d)})


def eval_G3(tmp: Path) -> EvalResult:
    from .evaluation import candidate_touches_protected, manifest_digest
    d = _temp_eval(tmp / "g3")
    before = manifest_digest(d)
    add_candidate(d, case_id="c1", goal="add z", solves_on_attempt=2, source="F1", owner="o")
    approve_candidate(d, "c1", approver="bob", author="o")
    after = manifest_digest(d)
    detected = candidate_touches_protected(["eval/tasks.json", "src/psf/cli.py"]) == ["eval/tasks.json"]
    # capture/approve changed eval/ (expected); the point is the system can't edit it silently
    ok = detected and after != before
    return EvalResult("G3", "protected custody", "pass" if ok else "fail",
                      {"protected_path_detected": detected, "manifest_changed_on_governed_edit": after != before})


def eval_G4(tmp: Path) -> EvalResult:
    d = _temp_eval(tmp / "g4")
    refused = False
    try:
        add_candidate(d, case_id="c1", goal="apply this diff --git a/x b/x", solves_on_attempt=1,
                      source="F1", owner="o")
    except ValueError:
        refused = True
    hol_before = json.dumps(_read(d, "holdout"))
    add_candidate(d, case_id="c2", goal="reject an invalid quorum", solves_on_attempt=2,
                  source="F1", owner="o")
    hol_unchanged = json.dumps(_read(d, "holdout")) == hol_before
    ok = refused and hol_unchanged
    return EvalResult("G4", "no leakage / holdout untouched", "pass" if ok else "fail",
                      {"solution_refused": refused, "holdout_unchanged": hol_unchanged})


def eval_G5(tmp: Path) -> EvalResult:
    d = _temp_eval(tmp / "g5")
    add_candidate(d, case_id="c1", goal="add z", solves_on_attempt=2, source="F1", owner="o")
    before = status(d)
    rotate_holdout(d, n=1, approver="bob", author="o")
    after = status(d)
    disjoint = not (integrity(d))
    rotated = after["holdout"] == before["holdout"] + 1
    refilled = after["optimization"] == before["optimization"]  # one out, one in
    ok = rotated and refilled and disjoint
    return EvalResult("G5", "holdout rotation stays disjoint", "pass" if ok else "fail",
                      {"before": before, "after": after, "integrity_clean": disjoint})


def eval_G6(tmp: Path) -> EvalResult:
    d = _temp_eval(tmp / "g6")
    no_reason = False
    try:
        retire_case(d, "e1", reason="", approver="bob", author="o")
    except ValueError:
        no_reason = True
    retire_case(d, "e1", reason="superseded", approver="bob", author="o")
    retired_file_exists = (d / "retired.json").exists()
    active = {c["id"] for c in _read(d, "optimization")["tasks"]}
    ok = no_reason and retired_file_exists and "e1" not in active
    return EvalResult("G6", "retirement is quarantine", "pass" if ok else "fail",
                      {"reason_required": no_reason, "retired_file_exists": retired_file_exists,
                       "removed_from_active": "e1" not in active})


def eval_G7(tmp: Path) -> EvalResult:
    d = _temp_eval(tmp / "g7")
    add_candidate(d, case_id="c1", goal="add z", solves_on_attempt=2, source="F1", owner="o",
                  ttl_days=-1)  # already expired
    problems = integrity(d)
    flagged = any("G7" in p for p in problems)
    return EvalResult("G7", "expiry / review flagged", "pass" if flagged else "fail",
                      {"problems": problems})


def eval_G8(tmp: Path) -> EvalResult:
    d = _temp_eval(tmp / "g8")
    # force a duplicate across tiers
    tasks = _read(d, "optimization")
    tasks["tasks"].append({"id": "h1", "goal": "dup", "solves_on_attempt": 1, "source": "F1", "status": "active"})
    _write(d, "optimization", tasks)
    problems = integrity(d)
    flagged = any("G8" in p for p in problems)
    return EvalResult("G8", "tier isolation (no overlap)", "pass" if flagged else "fail",
                      {"problems": problems})


def run_governance_eval() -> dict:
    evals = []
    with tempfile.TemporaryDirectory(prefix="psf-gov-") as d:
        tmp = Path(d)
        for fn in (eval_G1, eval_G2, eval_G3, eval_G4, eval_G5, eval_G6, eval_G7, eval_G8):
            try:
                evals.append(fn(tmp))
            except Exception as e:  # noqa: BLE001
                evals.append(EvalResult(fn.__name__, fn.__name__, "fail", {"error": repr(e)}))
    passed = sum(1 for e in evals if e.status == "pass")
    issues = [{"id": e.id, "name": e.name, "detail": e.detail} for e in evals if e.status == "fail"]
    return {"passed": passed, "failed": len(evals) - passed, "total": len(evals),
            "evals": [{"id": e.id, "name": e.name, "status": e.status, "detail": e.detail} for e in evals],
            "issues": issues}
