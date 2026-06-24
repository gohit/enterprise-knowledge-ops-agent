"""Verifier agent — grounding and validation.

Checks each factual claim in the Analyst's draft answer against the retrieved
evidence and produces a GroundingReport (score + list of unsupported claims). The
verdict (pass/fail) is derived from the configured grounding threshold. This is the
core anti-hallucination control.
"""
from __future__ import annotations

from src.graph.state import GraphState, GroundingReport, RetrievedChunk
from src.guardrails.grounding import verdict_for
from src.jsonparse import parse_json_object

VERIFIER_PROMPT = """You are the VERIFIER in a multi-agent system. Check whether each \
factual claim in the ANSWER is supported by the EVIDENCE below. Do not use outside \
knowledge — only the evidence counts.

Return ONLY a JSON object:
{{"grounding_score": <number between 0 and 1>, "unsupported_claims": ["claim text", ...]}}

where grounding_score is the fraction of the answer's claims that are supported by the \
evidence (1.0 = fully grounded, 0.0 = not grounded at all).

ANSWER:
{answer}

EVIDENCE:
{evidence}
"""


def _evidence_text(retrieved: dict[str, list[RetrievedChunk]]) -> str:
    lines: list[str] = []
    for chunks in retrieved.values():
        for c in chunks:
            lines.append(f"[{c.source}, p.{c.page}] {c.text}")
    return "\n".join(lines)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def verify_grounding(answer: str, retrieved, llm) -> GroundingReport:
    response = llm.invoke(
        VERIFIER_PROMPT.format(answer=answer, evidence=_evidence_text(retrieved))
    )
    text = getattr(response, "content", str(response))
    data = parse_json_object(text, default={"grounding_score": 0.0, "unsupported_claims": []})

    try:
        score = _clamp(float(data.get("grounding_score", 0.0)))
    except (TypeError, ValueError):
        score = 0.0  # unparseable score is treated as ungrounded (fail-safe)

    unsupported = [c for c in data.get("unsupported_claims", []) if isinstance(c, str)]
    return GroundingReport(score=score, verdict=verdict_for(score), unsupported=unsupported)


def make_verifier_node(llm):
    """Build the verifier node bound to a given LLM client."""

    def verifier_node(state: GraphState) -> dict:
        report = verify_grounding(state.get("draft_answer", ""), state.get("retrieved", {}), llm)
        return {
            "grounding": report,
            "trace": [
                {
                    "agent": "verifier",
                    "action": "ground_check",
                    "score": round(report.score, 3),
                    "verdict": report.verdict,
                    "unsupported_claims": report.unsupported,
                }
            ],
        }

    return verifier_node
