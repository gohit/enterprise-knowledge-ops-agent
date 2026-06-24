"""Assemble the multi-agent LangGraph.

Flow (Phase 4):

    START -> validate -> orchestrator -> retriever -> [gate] -> analyst -> verifier -> [ground] -> finalize -> memory -> END
                  |                          ^   |                              |   |                              ^
               (reject)                      |  (re-plan)                       |  (re-plan)                       |
                  v                          +---+                              +---+                         (limited)
                 END                                                                                              |
                                                                  insufficient ----------------------------> memory -> END

Two bounded feedback loops route control back to the Orchestrator:
- retrieval gate  : no relevant evidence -> re-plan (then abstain via `insufficient`)
- grounding gate  : answer not grounded  -> re-plan (then return a `limited` answer)
Both are bounded by `settings.max_retries` via the shared `attempts` counter.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.agents.analyst import insufficient_node, make_analyst_node
from src.agents.memory import make_memory_node
from src.agents.orchestrator import make_orchestrator_node
from src.agents.retriever import make_retriever_node
from src.agents.verifier import make_verifier_node
from src.config import settings
from src.graph.state import GraphState
from src.guardrails.grounding import with_disclaimer
from src.guardrails.input_validation import validate_input


def validate_node(state: GraphState) -> dict:
    check = validate_input(state.get("query", ""), settings.max_query_chars)
    return {
        "is_valid": check.valid,
        "trace": [
            {
                "agent": "guardrail",
                "action": "validate_input",
                "result": "pass" if check.valid else "fail",
                "reason": check.reason,
            }
        ],
    }


def reject_node(state: GraphState) -> dict:
    message = "Your question could not be processed (it was empty, too long, or unsafe)."
    return {
        "final_answer": message,
        "failures": ["invalid_input"],
        "trace": [{"agent": "guardrail", "action": "reject"}],
    }


def finalize_node(state: GraphState) -> dict:
    """Accept the grounded draft as the final answer."""
    return {
        "final_answer": state.get("draft_answer", ""),
        "trace": [{"agent": "system", "action": "finalize"}],
    }


def limited_node(state: GraphState) -> dict:
    """Grounding stayed low after retries: return a disclaimed, limited answer."""
    return {
        "final_answer": with_disclaimer(state.get("draft_answer", "")),
        "failures": ["low_grounding"],
        "trace": [{"agent": "system", "action": "limit_answer", "reason": "low_grounding"}],
    }


def route_after_validate(state: GraphState) -> str:
    return "orchestrator" if state.get("is_valid") else "reject"


def route_after_retrieval(state: GraphState) -> str:
    """Retrieval gate: proceed, re-plan, or abstain (bounded by max_retries)."""
    if state.get("retrieval_ok"):
        return "analyst"
    if state.get("attempts", 0) < settings.max_retries:
        return "orchestrator"
    return "insufficient"


def route_after_verify(state: GraphState) -> str:
    """Grounding gate: accept, re-plan, or return a limited answer (bounded)."""
    report = state.get("grounding")
    if report is not None and report.verdict == "pass":
        return "finalize"
    if state.get("attempts", 0) < settings.max_retries:
        return "orchestrator"
    return "limited"


def build_graph(llm=None, retriever=None):
    """Compile the multi-agent graph.

    ``llm`` and ``retriever`` are injectable for offline testing; when omitted the
    real Azure chat client and Chroma retriever are created lazily (needs creds).
    """
    if llm is None:
        from src.llm import get_chat_llm

        llm = get_chat_llm()
    if retriever is None:
        from src.ingestion.index import retrieve as retriever

    graph = StateGraph(GraphState)
    graph.add_node("validate", validate_node)
    graph.add_node("reject", reject_node)
    graph.add_node("orchestrator", make_orchestrator_node(llm))
    graph.add_node("retriever", make_retriever_node(retriever))
    graph.add_node("analyst", make_analyst_node(llm))
    graph.add_node("verifier", make_verifier_node(llm))
    graph.add_node("finalize", finalize_node)
    graph.add_node("limited", limited_node)
    graph.add_node("insufficient", insufficient_node)
    graph.add_node("memory", make_memory_node())

    graph.add_edge(START, "validate")
    graph.add_conditional_edges(
        "validate", route_after_validate, {"orchestrator": "orchestrator", "reject": "reject"}
    )
    graph.add_edge("reject", END)
    graph.add_edge("orchestrator", "retriever")
    graph.add_conditional_edges(
        "retriever",
        route_after_retrieval,
        {"analyst": "analyst", "orchestrator": "orchestrator", "insufficient": "insufficient"},
    )
    graph.add_edge("analyst", "verifier")
    graph.add_conditional_edges(
        "verifier",
        route_after_verify,
        {"finalize": "finalize", "orchestrator": "orchestrator", "limited": "limited"},
    )
    graph.add_edge("finalize", "memory")
    graph.add_edge("limited", "memory")
    graph.add_edge("insufficient", "memory")
    graph.add_edge("memory", END)

    return graph.compile()


def run_query(query: str, llm=None, retriever=None) -> GraphState:
    """Run a question through the graph and return the final state."""
    graph = build_graph(llm=llm, retriever=retriever)
    initial: GraphState = {
        "query": query,
        "attempts": 0,
        "trace": [],
        "failures": [],
        "memory": [],
    }
    return graph.invoke(initial)
