"""Canonical bytes and content digests.

Every durable record is hashed over its canonical JSON form so the same logical
object always produces the same digest. Foundation of the ledger, spec/approval
binding, and artifact addressing.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

GENESIS_HASH = "sha256:genesis"


def canonical_bytes(obj: Any) -> bytes:
    """Deterministic JSON bytes: sorted keys, no insignificant whitespace."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def digest(obj: Any) -> str:
    """Return a prefixed SHA-256 digest of the canonical form of ``obj``."""
    return "sha256:" + hashlib.sha256(canonical_bytes(obj)).hexdigest()


def digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()
