"""M2 durability: leases with fencing, transactional outbox, idempotency, retry.

Design is drawn from primary sources (see LOGBOOK): DB-time leases with a
monotonic epoch (fencing token), an effect intent written before the send, an
``UNKNOWN`` outbox state that is reconciled before any retry, and idempotency
keys that reject same-key/different-bytes. SQLite-first; the same conditional
UPDATEs port to PostgreSQL, where ``FOR UPDATE SKIP LOCKED`` is added to claims.
"""

from __future__ import annotations

import random
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .canonical import digest

SCHEMA = """
CREATE TABLE IF NOT EXISTS leases (
  work_id    TEXT PRIMARY KEY,
  owner      TEXT NOT NULL,
  epoch      INTEGER NOT NULL,
  expires_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id        TEXT,
  effect_name    TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  request_digest TEXT NOT NULL,
  status         TEXT NOT NULL,            -- INTENT|PENDING|CONFIRMED|UNKNOWN|COMPENSATED
  response_digest TEXT,
  attempt_count  INTEGER NOT NULL DEFAULT 0,
  last_error     TEXT,
  created_at     REAL NOT NULL,
  updated_at     REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency (
  key            TEXT PRIMARY KEY,
  request_digest TEXT NOT NULL,
  response_digest TEXT,
  status         TEXT NOT NULL,
  created_at     REAL NOT NULL,
  updated_at     REAL NOT NULL
);
"""

TRANSIENT, CORRECTABLE, TERMINAL, POLICY = "transient", "correctable", "terminal", "policy"


class DuplicateEffect(Exception):
    """Same idempotency key with different request bytes."""


class Fenced(Exception):
    """A write was rejected because its lease epoch is stale."""


@dataclass
class OutboxItem:
    id: int
    work_id: str | None
    effect_name: str
    key: str
    request_digest: str
    status: str
    response_digest: str | None
    attempt_count: int

    @property
    def settled(self) -> bool:
        return self.status in ("CONFIRMED", "COMPENSATED")


class TerminalError(Exception):
    """A permanent failure that must not be retried."""


def classify(error: Any) -> str:
    """Classify a failure so the caller knows whether to retry."""
    if isinstance(error, TerminalError):
        return TERMINAL
    if isinstance(error, PermissionError):
        return POLICY
    if isinstance(error, (TimeoutError, ConnectionError, OSError)):
        return TRANSIENT
    if isinstance(error, (ValueError, TypeError, KeyError)):
        return CORRECTABLE
    return TERMINAL


def retryable(error: Any) -> bool:
    return classify(error) == TRANSIENT


def backoff_seconds(attempt: int, *, base: float = 1.0, cap: float = 100.0,
                    rng: random.Random | None = None) -> float:
    """Capped exponential backoff with full jitter (AWS)."""
    rng = rng or random
    ceiling = min(cap, base * (2 ** max(0, attempt)))
    return rng.uniform(0, ceiling)


class Durability:
    def __init__(self, path: str | Path, *, clock: Callable[[], float] = time.time):
        self.path = Path(path)
        if self.path.parent and str(self.path.parent) not in ("", "."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self.clock = clock

    def _now(self, now: float | None) -> float:
        return self.clock() if now is None else now

    # -- leases ---------------------------------------------------------------

    def claim(self, work_id: str, owner: str, ttl: float, *, now: float | None = None) -> int | None:
        """Atomically acquire the lease. Returns the new epoch, or None if held."""
        t = self._now(now)
        row = self.conn.execute("SELECT epoch, expires_at FROM leases WHERE work_id=?", (work_id,)).fetchone()
        if row is None:
            try:
                self.conn.execute(
                    "INSERT INTO leases(work_id,owner,epoch,expires_at,updated_at) VALUES(?,?,1,?,?)",
                    (work_id, owner, t + ttl, t),
                )
                self.conn.commit()
                return 1
            except sqlite3.IntegrityError:
                return None  # lost the insert race
        if row["expires_at"] < t:
            cur = self.conn.execute(
                "UPDATE leases SET owner=?, epoch=epoch+1, expires_at=?, updated_at=?"
                " WHERE work_id=? AND expires_at=?",
                (owner, t + ttl, t, work_id, row["expires_at"]),
            )
            self.conn.commit()
            if cur.rowcount:
                return int(self.conn.execute(
                    "SELECT epoch FROM leases WHERE work_id=?", (work_id,)).fetchone()["epoch"])
        return None

    def renew(self, work_id: str, owner: str, epoch: int, ttl: float, *, now: float | None = None) -> bool:
        t = self._now(now)
        cur = self.conn.execute(
            "UPDATE leases SET expires_at=?, updated_at=?"
            " WHERE work_id=? AND owner=? AND epoch=? AND expires_at>?",
            (t + ttl, t, work_id, owner, epoch, t),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def release(self, work_id: str, owner: str, epoch: int) -> bool:
        cur = self.conn.execute(
            "DELETE FROM leases WHERE work_id=? AND owner=? AND epoch=?", (work_id, owner, epoch)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def lease(self, work_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM leases WHERE work_id=?", (work_id,)).fetchone()
        return dict(row) if row else None

    # -- effects --------------------------------------------------------------

    def record_effect(self, work_id: str | None, effect_name: str, request: Any, *,
                      key: str | None = None, now: float | None = None) -> OutboxItem:
        """Record the intent to perform an effect, before sending it."""
        t = self._now(now)
        req_digest = digest(request)
        key = key or f"{work_id}:{effect_name}:{req_digest}"
        existing = self.outbox(key)
        if existing:
            if existing.request_digest != req_digest:
                raise DuplicateEffect(f"key {key} reused with different request")
            return existing
        self.conn.execute(
            "INSERT INTO outbox(work_id,effect_name,idempotency_key,request_digest,status,attempt_count,created_at,updated_at)"
            " VALUES(?,?,?,?, 'INTENT', 0, ?, ?)",
            (work_id, effect_name, key, req_digest, t, t),
        )
        self.conn.execute(
            "INSERT OR IGNORE INTO idempotency(key,request_digest,status,created_at,updated_at)"
            " VALUES(?,?, 'INTENT', ?, ?)",
            (key, req_digest, t, t),
        )
        self.conn.commit()
        return self.outbox(key)  # type: ignore[return-value]

    def send(self, key: str, sender: Callable[[], Any]) -> OutboxItem:
        """Send a recorded effect. Never blindly resends an UNKNOWN."""
        item = self.outbox(key)
        if item is None:
            raise KeyError(f"unknown effect {key}")
        if item.status == "CONFIRMED":
            return item  # idempotent replay: do not resend
        if item.status == "UNKNOWN":
            raise RuntimeError("effect is UNKNOWN; reconcile before resending")
        self._set(key, "PENDING", bump_attempt=True)
        try:
            response = sender()
        except Exception as e:  # noqa: BLE001 - any failure may leave the effect unknown
            self._set(key, "UNKNOWN", error=repr(e))
            return self.outbox(key)  # type: ignore[return-value]
        self._set(key, "CONFIRMED", response=digest(response))
        return self.outbox(key)  # type: ignore[return-value]

    def reconcile(self, key: str, checker: Callable[[], Any]) -> OutboxItem:
        """Resolve an UNKNOWN effect by observing the target. No blind retry."""
        item = self.outbox(key)
        if item is None:
            raise KeyError(f"unknown effect {key}")
        if item.status != "UNKNOWN":
            return item
        observed = checker()
        if observed is not None:
            self._set(key, "CONFIRMED", response=digest(observed))
        else:
            self._set(key, "INTENT")  # proven absent -> safe to resend
        return self.outbox(key)  # type: ignore[return-value]

    def outbox(self, key: str) -> OutboxItem | None:
        r = self.conn.execute("SELECT * FROM outbox WHERE idempotency_key=?", (key,)).fetchone()
        return self._item(r) if r else None

    def pending(self) -> list[OutboxItem]:
        rows = self.conn.execute(
            "SELECT * FROM outbox WHERE status IN ('INTENT','PENDING','UNKNOWN') ORDER BY id"
        ).fetchall()
        return [self._item(r) for r in rows]

    def _set(self, key: str, status: str, *, response: str | None = None,
             error: str | None = None, bump_attempt: bool = False) -> None:
        t = self.clock()
        sets = ["status=?", "updated_at=?"]
        args: list[Any] = [status, t]
        if response is not None:
            sets.append("response_digest=?"); args.append(response)
        if error is not None:
            sets.append("last_error=?"); args.append(error)
        if bump_attempt:
            sets.append("attempt_count=attempt_count+1")
        args.append(key)
        self.conn.execute(f"UPDATE outbox SET {', '.join(sets)} WHERE idempotency_key=?", args)
        self.conn.execute(
            "UPDATE idempotency SET status=?, updated_at=?, response_digest=COALESCE(?, response_digest)"
            " WHERE key=?",
            (status, t, response, key),
        )
        self.conn.commit()

    @staticmethod
    def _item(r: sqlite3.Row) -> OutboxItem:
        return OutboxItem(
            id=r["id"], work_id=r["work_id"], effect_name=r["effect_name"],
            key=r["idempotency_key"], request_digest=r["request_digest"], status=r["status"],
            response_digest=r["response_digest"], attempt_count=r["attempt_count"],
        )

    def close(self) -> None:
        self.conn.close()
