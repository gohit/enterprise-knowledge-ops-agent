"""Memory agent — context management.

Records a compact summary of each completed run (query, plan, answer) into the
``memory`` channel. Because ``memory`` uses the ``add`` reducer, entries accumulate
across turns, enabling multi-turn follow-up questions later (the UI can seed prior
context back into the graph).
"""
from __future__ import annotations

from src.graph.state import GraphState


def make_memory_node():
    def memory_node(state: GraphState) -> dict:
        entry = {
            "query": state.get("query", ""),
            "plan": [s.question for s in state.get("plan", [])],
            "answer": state.get("final_answer", ""),
        }
        return {
            "memory": [entry],
            "trace": [{"agent": "memory", "action": "record"}],
        }

    return memory_node
