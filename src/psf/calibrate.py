"""Calibration — turn classifier answers + real outcomes into thresholds.

Jev (or any classifier) is advisory and unproven; we calibrate its questions
against labelled outcomes before trusting thresholds. Records are
``{"score": float, "label": 0|1}``.
"""

from __future__ import annotations

from dataclasses import dataclass


def sweep(records: list[dict], thresholds: tuple[float, ...] = tuple(round(0.1 * i, 1) for i in range(1, 10))) -> dict:
    """Pick the threshold maximizing accuracy of ``score >= t`` predicting label."""
    if not records:
        return {"best_threshold": 0.5, "accuracy": 0.0, "n": 0}
    best = None
    for t in thresholds:
        correct = sum(1 for r in records if (r["score"] >= t) == bool(r["label"]))
        acc = correct / len(records)
        if best is None or acc > best[1]:
            best = (t, acc)
    return {"best_threshold": best[0], "accuracy": best[1], "n": len(records)}


def reliability(records: list[dict], bins: int = 5) -> dict:
    """Expected calibration error over equal-width probability bins."""
    if not records:
        return {"ece": 0.0, "bins": []}
    buckets: list[list[dict]] = [[] for _ in range(bins)]
    for r in records:
        idx = min(bins - 1, int(float(r["score"]) * bins))
        buckets[idx].append(r)
    ece = 0.0
    detail = []
    n = len(records)
    for i, b in enumerate(buckets):
        if not b:
            continue
        conf = sum(r["score"] for r in b) / len(b)
        acc = sum(int(bool(r["label"])) for r in b) / len(b)
        ece += (len(b) / n) * abs(conf - acc)
        detail.append({"bin": i, "n": len(b), "conf": round(conf, 3), "acc": round(acc, 3)})
    return {"ece": round(ece, 4), "bins": detail}


def records_from_ledger(log, *, question: str = "worker_stuck") -> list[dict]:
    """Best-effort: pair SupervisorAssessed answers with the item's fatal outcome.

    Label = 1 if the work item ended BLOCKED (a real "stuck") else 0.
    """
    from .state import Workflow

    wf = Workflow(log)
    labels: dict[str, int] = {}
    for wid in log.work_ids():
        w = wf.fold(wid)
        labels[wid] = 1 if w.state == "BLOCKED" else 0
    out: list[dict] = []
    for e in log.all():
        if e.type == "SupervisorAssessed" and e.work_id in labels:
            val = (e.payload.get("answers") or {}).get(question)
            if isinstance(val, (int, float)):
                out.append({"score": float(val), "label": labels[e.work_id]})
    return out
