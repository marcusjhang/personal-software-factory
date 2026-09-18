import random

import pytest

from psf.durability import (
    CORRECTABLE, POLICY, TERMINAL, TRANSIENT,
    DuplicateEffect, Durability, TerminalError, backoff_seconds, classify, retryable,
)


def test_lease_single_winner_and_reclaim(tmp_path):
    clock = [0.0]
    d = Durability(tmp_path / "d.db", clock=lambda: clock[0])
    assert d.claim("W1", "worker-a", ttl=10, now=0.0) == 1
    # held, so a second claimer loses
    assert d.claim("W1", "worker-b", ttl=10, now=5.0) is None
    # after expiry, a new claimer takes over with a higher epoch (fence)
    assert d.claim("W1", "worker-b", ttl=10, now=11.0) == 2


def test_stale_epoch_renew_and_release_rejected(tmp_path):
    d = Durability(tmp_path / "d.db", clock=lambda: 0.0)
    epoch = d.claim("W1", "a", ttl=10, now=0.0)
    assert d.renew("W1", "a", epoch, ttl=10, now=1.0) is True
    # stale epoch fails (fenced)
    assert d.renew("W1", "a", epoch - 1, ttl=10, now=2.0) is False
    assert d.release("W1", "a", epoch - 1) is False
    assert d.release("W1", "a", epoch) is True


def test_outbox_intent_then_confirm(tmp_path):
    d = Durability(tmp_path / "d.db")
    item = d.record_effect("W1", "github.create_pr", {"title": "x"})
    assert item.status == "INTENT"
    sent = d.send(item.key, sender=lambda: {"pr": 1})
    assert sent.status == "CONFIRMED"
    # replay does not resend
    calls = []
    again = d.send(item.key, sender=lambda: calls.append(1) or {"pr": 1})
    assert again.status == "CONFIRMED" and calls == []


def test_unknown_is_reconciled_not_blind_retried(tmp_path):
    d = Durability(tmp_path / "d.db")
    item = d.record_effect("W1", "github.merge", {"pr": 1})
    applied = {}

    def crashing_sender():
        applied[item.key] = {"merged": True}  # the effect DID happen
        raise TimeoutError("no ack")

    sent = d.send(item.key, sender=crashing_sender)
    assert sent.status == "UNKNOWN"
    # blind resend is refused
    with pytest.raises(RuntimeError):
        d.send(item.key, sender=crashing_sender)
    # reconcile observes the target and confirms without re-sending
    rec = d.reconcile(item.key, checker=lambda: applied.get(item.key))
    assert rec.status == "CONFIRMED"


def test_reconcile_absent_allows_resend(tmp_path):
    d = Durability(tmp_path / "d.db")
    item = d.record_effect("W1", "email.send", {"to": "a"})
    d.send(item.key, sender=lambda: (_ for _ in ()).throw(TimeoutError()))
    assert d.outbox(item.key).status == "UNKNOWN"
    rec = d.reconcile(item.key, checker=lambda: None)
    assert rec.status == "INTENT"  # proven absent -> safe to resend
    done = d.send(item.key, sender=lambda: {"ok": True})
    assert done.status == "CONFIRMED"


def test_same_key_different_bytes_rejected(tmp_path):
    d = Durability(tmp_path / "d.db")
    d.record_effect("W1", "effect", {"a": 1}, key="k")
    with pytest.raises(DuplicateEffect):
        d.record_effect("W1", "effect", {"a": 2}, key="k")


def test_idempotent_resource_applies_once(tmp_path):
    d = Durability(tmp_path / "d.db")
    resource = {}
    item = d.record_effect("W1", "charge", {"amount": 10})
    send = lambda: resource.setdefault(item.key, {"charged": True})  # noqa: E731
    d.send(item.key, sender=send)
    d.send(item.key, sender=send)  # duplicate delivery
    assert len(resource) == 1


def test_retry_classification_and_backoff():
    assert classify(TimeoutError()) == TRANSIENT and retryable(TimeoutError())
    assert classify(ConnectionError()) == TRANSIENT
    assert classify(ValueError()) == CORRECTABLE and not retryable(ValueError())
    assert classify(TerminalError("nope")) == TERMINAL
    assert classify(PermissionError()) == POLICY
    rng = random.Random(0)
    for attempt in range(6):
        assert 0.0 <= backoff_seconds(attempt, rng=rng) <= 100.0
