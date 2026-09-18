"""Append-only, hash-chained event ledger.

The ledger is the canonical record of everything that happened. Each event
stores the hash of the previous event, so tampering or a gap is detectable by
``verify_chain``. Projections are derived by folding events, never edited in
place.

SQLite is used deliberately for the local, no-write envelope of the first
milestone. The durable mutation foundation swaps to PostgreSQL with the same
interface.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .canonical import GENESIS_HASH, canonical_bytes

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq       INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id  TEXT NOT NULL UNIQUE,
    ts        TEXT NOT NULL,
    type      TEXT NOT NULL,
    work_id   TEXT,
    actor     TEXT NOT NULL,
    payload   TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    hash      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_work ON events(work_id, seq);
"""


@dataclass(frozen=True)
class Event:
    seq: int
    event_id: str
    ts: str
    type: str
    work_id: str | None
    actor: str
    payload: dict[str, Any]
    prev_hash: str
    hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "event_id": self.event_id,
            "ts": self.ts,
            "type": self.type,
            "work_id": self.work_id,
            "actor": self.actor,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _hash_event(prev_hash: str, body: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(
        prev_hash.encode("utf-8") + canonical_bytes(body)
    ).hexdigest()


class EventLog:
    """Durable event ledger backed by SQLite."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if self.path.parent and str(self.path.parent) not in ("", "."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # -- writes ---------------------------------------------------------------

    def append(
        self,
        type: str,
        payload: dict[str, Any] | None = None,
        *,
        actor: str = "controller",
        work_id: str | None = None,
    ) -> Event:
        prev = self._last_hash()
        body = {
            "event_id": str(uuid.uuid4()),
            "ts": _now(),
            "type": type,
            "work_id": work_id,
            "actor": actor,
            "payload": payload or {},
            "prev_hash": prev,
        }
        h = _hash_event(prev, body)
        cur = self.conn.execute(
            "INSERT INTO events (event_id, ts, type, work_id, actor, payload, prev_hash, hash)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (
                body["event_id"],
                body["ts"],
                body["type"],
                body["work_id"],
                body["actor"],
                json.dumps(body["payload"], sort_keys=True),
                prev,
                h,
            ),
        )
        self.conn.commit()
        return Event(
            seq=cur.lastrowid,
            event_id=body["event_id"],
            ts=body["ts"],
            type=body["type"],
            work_id=body["work_id"],
            actor=body["actor"],
            payload=body["payload"],
            prev_hash=prev,
            hash=h,
        )

    # -- reads ----------------------------------------------------------------

    def _last_hash(self) -> str:
        row = self.conn.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return row["hash"] if row else GENESIS_HASH

    def __iter__(self) -> Iterator[Event]:
        yield from self.all()

    def all(self) -> list[Event]:
        return [self._row(r) for r in self.conn.execute("SELECT * FROM events ORDER BY seq")]

    def for_work(self, work_id: str) -> list[Event]:
        rows = self.conn.execute(
            "SELECT * FROM events WHERE work_id = ? ORDER BY seq", (work_id,)
        )
        return [self._row(r) for r in rows]

    def work_ids(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT work_id FROM events WHERE work_id IS NOT NULL ORDER BY work_id"
        )
        return [r["work_id"] for r in rows]

    def last(self) -> Event | None:
        row = self.conn.execute("SELECT * FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return self._row(row) if row else None

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"])

    @staticmethod
    def _row(r: sqlite3.Row) -> Event:
        return Event(
            seq=r["seq"],
            event_id=r["event_id"],
            ts=r["ts"],
            type=r["type"],
            work_id=r["work_id"],
            actor=r["actor"],
            payload=json.loads(r["payload"]),
            prev_hash=r["prev_hash"],
            hash=r["hash"],
        )

    # -- integrity ------------------------------------------------------------

    def verify_chain(self) -> tuple[bool, str]:
        prev = GENESIS_HASH
        for e in self.all():
            body = {
                "event_id": e.event_id,
                "ts": e.ts,
                "type": e.type,
                "work_id": e.work_id,
                "actor": e.actor,
                "payload": e.payload,
                "prev_hash": prev,
            }
            expected = _hash_event(prev, body)
            if e.prev_hash != prev:
                return False, f"event {e.seq} prev_hash mismatch"
            if e.hash != expected:
                return False, f"event {e.seq} hash mismatch"
            prev = e.hash
        return True, "ok"

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "EventLog":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
