"""Build a structured evaluation report from a finished graph run.

Packages the signals the agents already produced (retrieval relevance per subtask,
grounding score/verdict, failure flags, decision-trace length) into one inspectable
report. Pure functions over the final state — no LLM, fully testable.
"""
from __future__ import annotations

from src.graph.state import GraphState


def build_report(state: GraphState) -> dict:
    """Summarize a run into a JSON-serializable evaluation report."""
    plan = state.get("plan", [])
    retrieved = state.get("retrieved", {})
    question_of = {s.id: s.question for s in plan}

    retrieval: list[dict] = []
    for subtask_id, chunks in retrieved.items():
        scores = [c.score for c in chunks]
        retrieval.append(
            {
                "subtask": subtask_id,
                "question": question_of.get(subtask_id, ""),
                "top_score": round(max(scores), 3) if scores else 0.0,
                "mean_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
                "chunks": len(chunks),
                "sources": sorted({c.source for c in chunks}),
            }
        )

    grounding = state.get("grounding")
    grounding_d = (
        {
            "score": round(grounding.score, 3),
            "verdict": grounding.verdict,
            "unsupported_claims": grounding.unsupported,
        }
        if grounding is not None
        else None
    )

    trace = state.get("trace", [])
    return {
        "query": state.get("query", ""),
        "subtasks": len(plan),
        "retrieval": retrieval,
        "grounding": grounding_d,
        "failures": state.get("failures", []),
        "steps": len(trace),
        "agents_invoked": [e.get("agent") for e in trace],
    }


def format_report(report: dict) -> str:
    """Render the report as a compact console block."""
    lines = ["EVALUATION", "----------"]
    grounding = report.get("grounding")
    if grounding:
        lines.append(f"Grounding score : {grounding['score']:.2f}  ({grounding['verdict']})")
        if grounding["unsupported_claims"]:
            lines.append(f"Unsupported     : {grounding['unsupported_claims']}")
    lines.append(f"Subtasks        : {report['subtasks']}   Steps: {report['steps']}")
    for r in report["retrieval"]:
        lines.append(
            f"  [{r['subtask']}] top={r['top_score']:.2f} mean={r['mean_score']:.2f} "
            f"chunks={r['chunks']} sources={r['sources']}"
        )
    lines.append(f"Failures        : {report['failures'] or 'none'}")
    return "\n".join(lines)
