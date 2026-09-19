"""Classifier layer — Jev (TypeSafe) as an ADVISORY judgment source.

The factory asks narrow, typed questions about a bounded *state* and gets typed
answers (probabilities / choices / scores). Answers are signals the controller
acts on; they are never authority.

Providers:
- ``MockClassifier`` — deterministic, offline (all evals use this).
- ``JevClassifier``   — TypeSafe System One model (opt-in; TYPESAFE_API_KEY).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


# --- questions --------------------------------------------------------------

@dataclass
class Noul:
    instructions: str
    criteria: str | None = None


@dataclass
class Choice:
    instructions: str
    criteria: dict[str, str]


@dataclass
class Score:
    instructions: str
    criteria: list[str]


Question = Noul | Choice | Score


@dataclass
class Answer:
    kind: str                 # noul | choice | score
    value: float | str        # probability, chosen option, or score
    probabilities: dict[str, float] | None = None
    confidence: float | None = None

    @property
    def noul(self) -> float:
        assert self.kind == "noul"
        return float(self.value)

    @property
    def choice(self) -> str:
        assert self.kind == "choice"
        return str(self.value)

    @property
    def score(self) -> float:
        assert self.kind == "score"
        return float(self.value)


class Classifier(Protocol):
    def ask(self, state: dict[str, Any], questions: dict[str, Question]) -> dict[str, Answer]:
        ...

    def calls(self) -> int:
        ...


# --- mock -------------------------------------------------------------------

class MockClassifier:
    """Deterministic classifier driven by ``state['signals']``.

    For a Noul question with id ``x`` it returns ``signals[x]`` (default 0.0);
    for a Choice it returns ``signals[x]`` (default first option, confidence 1);
    for a Score it returns ``signals[x]`` (default 0).
    """

    def __init__(self, signals: dict[str, Any] | None = None):
        self.signals = signals or {}
        self._calls = 0

    def ask(self, state: dict[str, Any], questions: dict[str, Question]) -> dict[str, Answer]:
        self._calls += 1
        sig = {**self.signals, **(state.get("signals") or {})}
        out: dict[str, Answer] = {}
        for qid, q in questions.items():
            if isinstance(q, Noul):
                out[qid] = Answer("noul", float(sig.get(qid, 0.0)))
            elif isinstance(q, Choice):
                pick = sig.get(qid) or next(iter(q.criteria))
                out[qid] = Answer("choice", pick, {pick: 1.0}, 1.0)
            else:  # Score
                out[qid] = Answer("score", float(sig.get(qid, 0)), None, 1.0)
        return out

    def calls(self) -> int:
        return self._calls


class ErrorClassifier:
    """Always raises — used to prove fail-closed behaviour."""

    def ask(self, state, questions):
        raise RuntimeError("classifier unavailable")

    def calls(self) -> int:
        return 0


class CountingClassifier:
    """Wraps a classifier and counts asks (for cost-bound evals)."""

    def __init__(self, inner: Classifier):
        self.inner = inner
        self._calls = 0

    def ask(self, state, questions):
        self._calls += 1
        return self.inner.ask(state, questions)

    def calls(self) -> int:
        return self._calls


# --- Jev (TypeSafe) ---------------------------------------------------------

class JevClassifier:
    """TypeSafe System One model. Opt-in; requires ``typesafe-sdk`` + API key."""

    def __init__(self, model: str = "jev-latest", timeout: float = 10.0, api_key: str | None = None):
        self.model = model
        self.timeout = timeout
        self.api_key = api_key
        self._calls = 0

    def _client(self):
        import os
        try:
            from typesafe_sdk import TypeSafeClient
        except ImportError as e:  # pragma: no cover - optional dep
            raise RuntimeError("typesafe-sdk not installed (pip install typesafe-sdk)") from e
        key = self.api_key or os.environ.get("TYPESAFE_API_KEY")
        if not key:
            raise RuntimeError("TYPESAFE_API_KEY is not set")
        return TypeSafeClient(api_key=key)

    @staticmethod
    def _to_sdk(q: Question):
        from typesafe_sdk import Choice as JChoice, Noul as JNoul, Score as JScore
        if isinstance(q, Noul):
            return JNoul(instructions=q.instructions) if not q.criteria else JNoul(
                instructions=q.instructions, criteria=q.criteria)
        if isinstance(q, Choice):
            return JChoice(instructions=q.instructions, criteria=q.criteria)
        return JScore(instructions=q.instructions, criteria=q.criteria)

    def ask(self, state: dict[str, Any], questions: dict[str, Question]) -> dict[str, Answer]:
        self._calls += 1
        client = self._client()
        payload = {qid: self._to_sdk(q) for qid, q in questions.items()}
        with client as c:
            resp = c.system_one(state=state, questions=payload)
        out: dict[str, Answer] = {}
        for qid, q in questions.items():
            a = resp.answers[qid]
            if isinstance(q, Noul):
                out[qid] = Answer("noul", float(a.noul))
            elif isinstance(q, Choice):
                out[qid] = Answer("choice", a.choice, dict(getattr(a, "probabilities", {}) or {}),
                                  float(getattr(a, "confidence", 0.0)))
            else:
                out[qid] = Answer("score", float(a.score), dict(getattr(a, "probabilities", {}) or {}),
                                  float(getattr(a, "confidence", 0.0)))
        return out

    def calls(self) -> int:
        return self._calls


def build_classifier(cfg: dict | None = None) -> Classifier:
    cfg = cfg or {}
    provider = cfg.get("provider", "mock")
    if provider == "mock":
        return MockClassifier()
    if provider == "jev":
        return JevClassifier(model=cfg.get("model", "jev-latest"),
                             timeout=float(cfg.get("timeout_s", 10)))
    raise ValueError(f"unknown classifier provider: {provider}")
