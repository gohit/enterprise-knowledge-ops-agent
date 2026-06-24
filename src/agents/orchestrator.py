"""Orchestrator agent — plans the work.

Decomposes the user's question into the minimal set of self-contained sub-questions
needed to answer it across multiple policy documents. Emits a structured plan (a list
of SubTasks) so routing is explicit and inspectable, not hidden inside a prompt.

The LLM is asked for JSON and parsed tolerantly here (rather than relying on a
provider-specific structured-output API), which keeps the agent testable with a
simple fake LLM.
"""
from __future__ import annotations

from src.graph.state import GraphState, SubTask
from src.jsonparse import parse_json_object

ORCHESTRATOR_PROMPT = """You are the ORCHESTRATOR in a multi-agent system that answers \
questions about enterprise HR policies. Decompose the user's question into the minimal set \
of self-contained sub-questions needed to answer it. Use multiple sub-questions only when \
the answer genuinely requires reasoning across more than one topic or document; otherwise \
return a single sub-question.

Return ONLY a JSON object of the form:
{{"subtasks": ["first sub-question", "second sub-question"]}}

User question: {query}
"""


def parse_subtasks(text: str, fallback_query: str) -> list[SubTask]:
    """Parse the LLM's JSON plan into SubTasks, falling back to a single task."""
    data = parse_json_object(text)
    raw = data.get("subtasks", [])
    questions = [q.strip() for q in raw if isinstance(q, str) and q.strip()] if isinstance(raw, list) else []

    if not questions:
        # Robust fallback: treat the whole query as one subtask rather than crashing.
        questions = [fallback_query]

    return [SubTask(id=f"s{i + 1}", question=q) for i, q in enumerate(questions)]


def plan_query(query: str, llm) -> list[SubTask]:
    response = llm.invoke(ORCHESTRATOR_PROMPT.format(query=query))
    text = getattr(response, "content", str(response))
    return parse_subtasks(text, query)


def make_orchestrator_node(llm):
    """Build the orchestrator graph node bound to a given LLM client."""

    def orchestrator_node(state: GraphState) -> dict:
        plan = plan_query(state["query"], llm)
        attempts = state.get("attempts", 0) + 1
        return {
            "plan": plan,
            "attempts": attempts,
            "trace": [
                {
                    "agent": "orchestrator",
                    "action": "plan",
                    "attempt": attempts,
                    "subtasks": [s.question for s in plan],
                }
            ],
        }

    return orchestrator_node
