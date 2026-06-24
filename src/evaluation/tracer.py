"""Persist each run's decision trace and evaluation report to a JSON log file.

Writes ``logs/trace_<timestamp>.json`` containing the query, final answer, the full
ordered decision trace, and the structured evaluation report — the inspectable,
structured observability output the rubric asks for.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.config import settings
from src.evaluation.metrics import build_report
from src.graph.state import GraphState


def save_run(state: GraphState, report: dict | None = None, logs_dir: str | Path | None = None) -> Path:
    """Write the run's trace + evaluation report to a timestamped JSON file."""
    report = report if report is not None else build_report(state)
    logs_dir = Path(logs_dir or settings.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    path = logs_dir / f"trace_{now.strftime('%Y%m%d_%H%M%S_%f')}.json"
    payload = {
        "timestamp": now.isoformat(timespec="seconds"),
        "query": state.get("query", ""),
        "final_answer": state.get("final_answer", ""),
        "evaluation": report,
        "trace": state.get("trace", []),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
