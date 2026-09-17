"""
Integration tests for the Moss semantic recall layer.

WHAT THESE COVER
----------------
The wiring between TexMed and the Moss SDK: index build, query dispatch,
nearest-neighbour classification, flag construction, confidence scoring, the
approval learning loop, and graceful degradation.

The `_StubClient` replaces only the Moss *transport*. It is constructed with and
returns the genuine `moss` SDK types (`DocumentInfo`, `QueryOptions`,
`MutationOptions`), so a drift in those signatures fails these tests.

WHAT THESE DO NOT COVER
-----------------------
Retrieval quality. The stub scores by token overlap, not by Moss's embeddings.
These tests prove the integration is correct, not that semantic recall is good —
that is what `eval_semantic.py` measures against the live service.

Run with a Python >= 3.10 interpreter that has `moss` installed:
    python -m pytest tests/test_semantic_matcher.py -v
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

moss = pytest.importorskip("moss", reason="moss requires Python >= 3.10")
from moss import DocumentInfo, MutationOptions, QueryOptions  # noqa: E402

from agents.semantic_matcher import SemanticMatcher  # noqa: E402


# ── stub transport ────────────────────────────────────────────────────────────


class _Hit:
    def __init__(self, doc, score):
        self.id = doc.id
        self.text = doc.text
        self.metadata = doc.metadata
        self.score = score
        self.payload = None


class _Result:
    def __init__(self, docs, query):
        self.docs = docs
        self.query = query
        self.time_taken_ms = 1.2


def _tokens(text):
    return {t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if len(t) > 2}


class _StubClient:
    """Mimics the MossClient surface the matcher uses. No network."""

    def __init__(self):
        self.docs = {}
        self.created = []
        self.loaded = []
        self.load_should_fail = True   # simulate "index does not exist yet"

    async def create_index(self, name, docs, model_id=None, *, wait=True):
        assert all(isinstance(d, DocumentInfo) for d in docs), "must pass real DocumentInfo"
        self.created.append((name, model_id, len(docs)))
        for d in docs:
            self.docs[d.id] = d
        self.load_should_fail = False
        return {"ok": True}

    async def load_index(self, name, auto_refresh=False,
                         polling_interval_in_seconds=600, cache_path=None):
        if self.load_should_fail:
            raise RuntimeError(f"index '{name}' not found")
        self.loaded.append(name)
        return name

    async def add_docs(self, name, docs, options=None):
        assert all(isinstance(d, DocumentInfo) for d in docs)
        assert options is None or isinstance(options, MutationOptions)
        for d in docs:
            self.docs[d.id] = d
        return {"added": len(docs)}

    async def query(self, name, query, options=None):
        assert isinstance(options, QueryOptions), "must pass real QueryOptions"
        q = _tokens(query)
        scored = []
        for d in self.docs.values():
            dt = _tokens(d.text)
            overlap = len(q & dt) / len(q | dt) if (q | dt) else 0.0
            scored.append(_Hit(d, overlap))
        scored.sort(key=lambda h: h.score, reverse=True)
        top_k = getattr(options, "top_k", 3) or 3
        return _Result(scored[:top_k], query)


@pytest.fixture
def matcher():
    m = SemanticMatcher(client=_StubClient(), threshold=0.05)
    assert m.warm(timeout=30)
    return m


# ── tests ─────────────────────────────────────────────────────────────────────


def test_warm_creates_then_loads_index(matcher):
    """First warm builds the index from the corpus, then loads it."""
    stub = matcher._client
    assert len(stub.created) == 1
    name, model_id, count = stub.created[0]
    assert model_id == "moss-minilm"      # read from the corpus file
    assert count == 70                    # 40 recoupment + 30 benign
    assert stub.loaded == [name]
    assert matcher.ready


def test_warm_is_idempotent(matcher):
    matcher.warm()
    matcher.warm()
    assert len(matcher._client.created) == 1


def test_recoupment_line_matches(matcher):
    hit = matcher.match("Amount recouped from this payment          940.55")
    assert hit is not None
    assert hit.label == "recoupment"
    assert hit.score >= matcher.threshold
    assert hit.query_ms > 0


def test_benign_nearest_neighbour_is_not_flagged(matcher):
    """
    The load-bearing case: a benign line whose top hit is a benign doc returns
    None even though the similarity score is high. Without the benign half of
    the corpus this line would be flagged.
    """
    hit = matcher.match("Contractual adjustment per provider agreement   1,240.00")
    assert hit is None


def test_flag_fields_are_well_formed(matcher):
    hit = matcher.match("Offset applied to prior outstanding balance    500.00")
    assert hit is not None
    fields = hit.to_flag_fields()
    assert fields["source"] == "semantic"
    assert fields["payer_tag"]
    assert 0.0 <= fields["semantic_score"] <= 1.0
    assert fields["semantic_doc_id"]
    assert fields["semantic_learned"] is False


def test_short_lines_are_not_queried(matcher):
    before = matcher.stats()["queries"]
    assert matcher.match("$12.00") is None
    assert matcher.match("") is None
    assert matcher.stats()["queries"] == before, "pre-filter should skip the query"


def test_learn_adds_confirmed_phrase_and_marks_it(matcher):
    novel = "Vendor chargeback netted against this disbursement per audit"
    assert matcher.learn(novel, payer_tag="anthem") is True
    assert matcher.stats()["learned_phrases"] == 1

    hit = matcher.match(novel)
    assert hit is not None
    assert hit.learned is True
    assert hit.payer_tag == "anthem"
    assert hit.to_flag_fields()["semantic_learned"] is True


def test_stats_reports_latency_percentiles(matcher):
    for _ in range(5):
        matcher.match("Amount recouped from this payment    940.55")
    stats = matcher.stats()
    assert stats["ready"] is True
    assert stats["queries"] >= 5
    assert stats["latency_ms_p50"] is not None
    assert stats["latency_ms_p95"] is not None
    assert stats["corpus_size"] == 70


def test_query_failure_degrades_to_none(matcher):
    async def boom(*a, **k):
        raise RuntimeError("moss service unreachable")

    matcher._client.query = boom
    assert matcher.match("Amount recouped from this payment    940.55") is None
    assert "unreachable" in matcher.stats()["last_error"]


def test_disabled_without_credentials(monkeypatch):
    for var in ("MOSS_PROJECT_ID", "MOSS_PROJECT_KEY"):
        monkeypatch.delenv(var, raising=False)
    m = SemanticMatcher()
    assert m.enabled is False
    assert m.ready is False
    assert m.match("Amount recouped from this payment  940.55") is None
    assert m.warm() is False
    assert "MOSS_PROJECT_ID" in m.disabled_reason


def test_force_disabled_env(monkeypatch):
    monkeypatch.setenv("MOSS_PROJECT_ID", "x")
    monkeypatch.setenv("MOSS_PROJECT_KEY", "y")
    monkeypatch.setenv("MOSS_DISABLED", "1")
    m = SemanticMatcher()
    assert m.enabled is False
    assert "MOSS_DISABLED" in m.disabled_reason


# ── agent-level integration ───────────────────────────────────────────────────


def test_agent_adds_semantic_flag_regex_misses(matcher):
    from agents.recoupment_agent import RecoupmentAgent

    line = "Payment reduced to satisfy an earlier excess disbursement   1,204.00"

    baseline = RecoupmentAgent(use_semantic=False).run(line, "t.pdf")
    assert baseline.flags == [], "regex should miss this rewording"

    result = RecoupmentAgent(matcher=matcher).run(line, "t.pdf")
    assert len(result.flags) == 1
    flag = result.flags[0]
    assert flag["source"] == "semantic"
    assert flag["amounts_found"] == [1204.00]
    assert flag["confidence"] > 0


def test_semantic_flag_reduces_net_received(matcher):
    """A semantically detected clawback must move net_received, not just log."""
    from agents.recoupment_agent import RecoupmentAgent

    text = (
        "Total amount paid to provider                 5,000.00\n"
        "Payment reduced to satisfy an earlier excess disbursement   1,204.00\n"
    )
    result = RecoupmentAgent(matcher=matcher).run(text, "t.pdf")
    assert result.paid_amount == 5000.00
    assert result.net_received == 3796.00


def test_regex_verdict_wins_over_semantic(matcher):
    """A line regex already claimed is never re-queried or double-flagged."""
    from agents.recoupment_agent import RecoupmentAgent

    line = "OUTSTANDING NEG BAL WITH DIFFER    18,020.11"
    result = RecoupmentAgent(matcher=matcher).run(line, "t.pdf")
    assert len(result.flags) == 1
    assert result.flags[0]["source"] == "pattern"


def test_learned_phrase_scores_higher_than_plain_semantic(matcher):
    """The +0.05 human-confirmed bonus must actually reach the flag."""
    from agents.recoupment_agent import _flag_confidence

    base = {"source": "semantic", "amounts_found": [900.0], "line": "x"}
    learned = dict(base, semantic_learned=True)
    assert _flag_confidence(learned, None, {}) > _flag_confidence(base, None, {})


def test_money_gate_suppresses_amountless_lines(matcher):
    """
    Lines without a dollar figure are never sent to Moss. A clawback the
    practice can act on always states an amount; prose and footers do not.
    This is both a precision guard and a query-volume reduction.
    """
    from agents.recoupment_agent import _detect_flags, _load_compiled_patterns

    compiled = _load_compiled_patterns()
    text = (
        "Settlement of an outstanding accounts receivable      3,240.00\n"
        "balance against this payment cycle.\n"
        "Questions: provider.services@meridianregional.example\n"
    )
    before = matcher.stats()["queries"]
    flags = _detect_flags(text, compiled, matcher=matcher)

    assert len(flags) == 1, "only the money-bearing line should flag"
    assert flags[0]["amounts_found"] == [3240.00]
    assert matcher.stats()["queries"] - before == 1, "amountless lines must not be queried"

    # Opting out restores querying of every regex-missed line.
    before = matcher.stats()["queries"]
    _detect_flags(text, compiled, matcher=matcher, semantic_requires_amount=False)
    assert matcher.stats()["queries"] - before == 3
