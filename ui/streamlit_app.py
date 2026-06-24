"""Streamlit UI for the Enterprise Knowledge Ops Agent.

A chat-style interface that surfaces not just the answer, but *how* it was produced:
sources, the full agent decision trace, and the evaluation report. This is the
explainability/observability surface for the case study.

Run:  streamlit run ui/streamlit_app.py
(Needs Azure credentials in .env and a built index: python -m src.ingestion.index --rebuild)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when launched via `streamlit run`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from src.config import settings  # noqa: E402
from src.evaluation.metrics import build_report  # noqa: E402
from src.evaluation.tracer import save_run  # noqa: E402
from src.llm import chat_configured  # noqa: E402

st.set_page_config(page_title="Enterprise Knowledge Ops Agent", page_icon="📚", layout="wide")


# --------------------------------------------------------------------------- helpers
def _index_exists() -> bool:
    return settings.vectorstore_dir.exists() and any(settings.vectorstore_dir.iterdir())


def _render_turn(turn: dict) -> None:
    """Render one assistant turn: answer + Sources / Trace / Evaluation expanders."""
    st.markdown(turn["answer"])

    if turn.get("failures"):
        st.warning("Flags: " + ", ".join(turn["failures"]))

    report = turn.get("report", {})
    grounding = report.get("grounding")

    cols = st.columns(3)
    cols[0].metric("Grounding", f"{grounding['score']:.2f}" if grounding else "—",
                   grounding["verdict"] if grounding else None)
    cols[1].metric("Sub-questions", report.get("subtasks", "—"))
    cols[2].metric("Steps", report.get("steps", "—"))

    with st.expander(f"📚 Sources ({len(turn.get('sources', []))})"):
        if turn.get("sources"):
            for i, (src, page) in enumerate(turn["sources"], 1):
                st.markdown(f"**[{i}]** {src} — p.{page}")
        else:
            st.caption("No sources retrieved.")

    with st.expander("🧭 Decision Trace"):
        for i, event in enumerate(turn.get("trace", []), 1):
            detail = {k: v for k, v in event.items() if k not in ("agent", "action")}
            st.markdown(f"`{i:>2}.` **{event['agent']}** · {event['action']}")
            if detail:
                st.json(detail, expanded=False)

    with st.expander("📊 Evaluation report"):
        st.json(report, expanded=False)


def _answer(question: str) -> dict:
    """Run the graph for one question and package the result for rendering."""
    from src.graph.build_graph import run_query  # lazy: triggers creds check on use

    state = run_query(question)
    report = build_report(state)
    sources = sorted(
        {(c.source, c.page) for chunks in state.get("retrieved", {}).values() for c in chunks}
    )
    try:
        save_run(state, report=report)
    except Exception:  # logging must never break the UI
        pass
    return {
        "answer": state.get("final_answer", ""),
        "sources": sources,
        "trace": state.get("trace", []),
        "failures": state.get("failures", []),
        "report": report,
    }


# --------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Enterprise Knowledge Ops Agent")
    st.caption("Multi-agent RAG over enterprise policies — LangGraph")

    st.subheader("System status")
    st.write("⚙️ Provider:", f"`{settings.llm_provider}`")
    st.write("🔑 Model:", "✅ configured" if chat_configured() else "❌ not configured")
    st.write("🗂️ Index:", "✅ built" if _index_exists() else "❌ not built")

    if not chat_configured():
        st.info("Add Azure credentials to `.env` to enable answering.", icon="ℹ️")
    if not _index_exists():
        st.info("Build the index: `python -m src.ingestion.index --rebuild`", icon="ℹ️")

    st.divider()
    st.subheader("Try asking")
    st.markdown(
        "- Can a resigned employee be rehired, and what separation conditions apply?\n"
        "- How does the work model policy affect returnship eligibility?\n"
        "- What should an employee do and avoid after referring a candidate?"
    )
    if st.button("Clear conversation"):
        st.session_state.history = []
        st.rerun()


# --------------------------------------------------------------------------- main chat
st.title("📚 Enterprise Knowledge Ops Agent")
st.caption("Ask complex questions across company policies. Answers are grounded, cited, and explainable.")

if "history" not in st.session_state:
    st.session_state.history = []  # list of {"question", "result"}

# Replay prior turns.
for turn in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(turn["question"])
    with st.chat_message("assistant"):
        _render_turn(turn["result"])

question = st.chat_input("Ask a question about company policies…")
if question:
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        if not chat_configured():
            st.error("The model is not configured. Add Azure credentials to `.env` and rebuild the index.")
        elif not _index_exists():
            st.error("No document index found. Run `python -m src.ingestion.index --rebuild` first.")
        else:
            with st.spinner("Planning, retrieving, reasoning, verifying…"):
                try:
                    result = _answer(question)
                    _render_turn(result)
                    st.session_state.history.append({"question": question, "result": result})
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Something went wrong: {exc}")
