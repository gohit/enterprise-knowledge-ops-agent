"""CLI entry point for the Enterprise Knowledge Ops Agent.

Usage:
    python -m src.app "your question"            # full multi-agent graph
    python -m src.app "your question" --baseline # the single-agent RAG baseline
    python -m src.app "your question" --trace    # also print the decision trace

Both modes need Azure credentials + a built index to run live.
"""
from __future__ import annotations

import argparse


def _print_sources(sources: list[tuple[str, int]]) -> None:
    print("\nSOURCES\n-------")
    for i, (source, page) in enumerate(sources, start=1):
        print(f"[{i}] {source}  (p.{page})")


def _run_baseline(question: str, k: int | None) -> None:
    from src.baseline import answer_baseline

    result = answer_baseline(question, k=k)
    print("ANSWER (baseline)\n-----------------")
    print(result.answer)
    _print_sources(result.sources)


def _run_graph(question: str, show_trace: bool, save_log: bool) -> None:
    from src.evaluation.metrics import build_report, format_report
    from src.evaluation.tracer import save_run
    from src.graph.build_graph import run_query

    state = run_query(question)
    print("ANSWER\n------")
    print(state.get("final_answer", ""))

    sources = sorted(
        {(c.source, c.page) for chunks in state.get("retrieved", {}).values() for c in chunks}
    )
    if sources:
        _print_sources(sources)

    report = build_report(state)
    print("\n" + format_report(report))

    if show_trace:
        print("\nDECISION TRACE\n--------------")
        for i, event in enumerate(state.get("trace", []), start=1):
            detail = {k: v for k, v in event.items() if k not in ("agent", "action")}
            print(f"{i:>2}. [{event['agent']}] {event['action']}  {detail or ''}")

    if save_log:
        path = save_run(state, report=report)
        print(f"\nTrace + evaluation logged to: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the Knowledge Ops Agent a question.")
    parser.add_argument("question", help="The question to ask.")
    parser.add_argument("-k", type=int, default=None, help="Chunks to retrieve (baseline only).")
    parser.add_argument("--baseline", action="store_true", help="Use the single-agent baseline.")
    parser.add_argument("--trace", action="store_true", help="Print the agent decision trace.")
    parser.add_argument("--no-log", action="store_true", help="Do not write a trace log file.")
    args = parser.parse_args()

    if args.baseline:
        _run_baseline(args.question, args.k)
    else:
        _run_graph(args.question, args.trace, save_log=not args.no_log)


if __name__ == "__main__":
    main()
