"""Unit tests for the Verifier agent (VER-* cases)."""
from __future__ import annotations

from src.agents.verifier import verify_grounding
from src.graph.state import RetrievedChunk


def _evidence(sample_chunks):
    return {
        "s1": [
            RetrievedChunk(
                d.metadata["chunk_id"], d.metadata["source"], d.metadata["page"], score, d.page_content
            )
            for d, score in sample_chunks
        ]
    }


def test_ver1_fully_supported_answer_passes(fake_llm, sample_chunks):
    llm = fake_llm('{"grounding_score": 0.95, "unsupported_claims": []}')
    report = verify_grounding("grounded answer", _evidence(sample_chunks), llm)
    assert report.verdict == "pass"
    assert report.score == 0.95
    assert report.unsupported == []


def test_ver2_unsupported_claim_lowers_score(fake_llm, sample_chunks):
    llm = fake_llm('{"grounding_score": 0.4, "unsupported_claims": ["made-up fact"]}')
    report = verify_grounding("partly invented answer", _evidence(sample_chunks), llm)
    assert report.verdict == "fail"
    assert "made-up fact" in report.unsupported


def test_ver3_threshold_boundary(fake_llm, sample_chunks):
    # Just below the 0.75 default threshold -> fail.
    below = verify_grounding("x", _evidence(sample_chunks), fake_llm('{"grounding_score": 0.74}'))
    assert below.verdict == "fail"
    # At the threshold -> pass.
    at = verify_grounding("x", _evidence(sample_chunks), fake_llm('{"grounding_score": 0.75}'))
    assert at.verdict == "pass"


def test_ver_unparseable_output_is_failsafe(fake_llm, sample_chunks):
    # Garbage from the LLM must be treated as ungrounded, never silently "pass".
    report = verify_grounding("x", _evidence(sample_chunks), fake_llm("not json"))
    assert report.score == 0.0
    assert report.verdict == "fail"


def test_ver_score_is_clamped(fake_llm, sample_chunks):
    report = verify_grounding("x", _evidence(sample_chunks), fake_llm('{"grounding_score": 1.7}'))
    assert report.score == 1.0
