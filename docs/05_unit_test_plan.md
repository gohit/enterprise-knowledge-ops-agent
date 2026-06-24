# 5. Unit Test Case Documentation

A required deliverable. This maps each component to concrete unit tests so behavior is
verifiable and regressions are caught. Tests live in `tests/` and run with `pytest`. LLM and
embedding calls are **mocked** so tests are fast, deterministic, and offline.

## 5.1 Testing strategy

| Layer | Approach |
|-------|----------|
| Pure logic (chunking, scoring, thresholds, guardrail regex) | Direct unit tests, no mocks. |
| Agents (Orchestrator, Analyst, Verifier) | Mock the LLM client; assert on parsing, routing, and state writes. |
| Retriever | Use a tiny in-memory/temp Chroma index with 3–4 known chunks. |
| Graph | Mock agent nodes; assert routing/conditional edges fire correctly. |
| End-to-end | One integration test with mocked LLM returning canned plan/answer. |

Fixtures: `conftest.py` provides a fake LLM (returns scripted responses), a temp vector store,
and sample documents.

## 5.2 Test cases by component

### Ingestion / chunking (`tests/test_loader.py`)
| ID | Test | Expected |
|----|------|----------|
| ING-1 | Load a sample PDF | returns non-empty text + page metadata |
| ING-2 | Split a long doc | chunks respect size/overlap; each has `source`, `page`, `chunk_id` |
| ING-3 | Unsupported file type | raises a clear, handled error |

### Retriever (`tests/test_retriever.py`)
| ID | Test | Expected |
|----|------|----------|
| RET-1 | Query matching a known chunk | that chunk ranks #1; score returned |
| RET-2 | Each result carries metadata | `source`, `page`, `chunk_id`, `score` present |
| RET-3 | Off-topic query | top score < `min_relevance` (drives the retrieval gate) |

### Orchestrator (`tests/test_orchestrator.py`)
| ID | Test | Expected |
|----|------|----------|
| ORCH-1 | Multi-part query | plan contains > 1 subtask |
| ORCH-2 | Simple query | plan contains exactly 1 subtask |
| ORCH-3 | Plan parsing | malformed LLM output handled gracefully (no crash) |
| ORCH-4 | Re-plan on feedback | given a "low grounding" signal, produces a revised plan |

### Analyst (`tests/test_analyst.py`)
| ID | Test | Expected |
|----|------|----------|
| ANA-1 | Synthesis cites chunks | draft answer references provided chunk IDs |
| ANA-2 | Cross-document reasoning | given chunks from 2 docs, answer references both |
| ANA-3 | No context | returns an "insufficient evidence" style draft, not invented facts |

### Verifier / grounding (`tests/test_verifier.py`)
| ID | Test | Expected |
|----|------|----------|
| VER-1 | Fully supported answer | grounding score high; verdict `pass`; no unsupported claims |
| VER-2 | Unsupported claim present | claim listed in `unsupported_claims`; score drops |
| VER-3 | Threshold boundary | score just below threshold → verdict triggers retry/flag |

### Guardrails (`tests/test_guardrails.py`)
| ID | Test | Expected |
|----|------|----------|
| GRD-1 | Empty input | rejected |
| GRD-2 | Over-length input | rejected/truncated per policy |
| GRD-3 | Injection phrase ("ignore previous instructions") | detected and stripped/rejected |
| GRD-4 | Normal question | passes unchanged |

### Evaluation / tracer (`tests/test_evaluation.py`)
| ID | Test | Expected |
|----|------|----------|
| EVAL-1 | Trace populated | every executed node appends a `TraceEvent` |
| EVAL-2 | Report schema | report has retrieval, grounding, failures, steps fields |
| EVAL-3 | Failure flag | irrelevant retrieval sets the `insufficient_retrieval` flag |

### Graph routing (`tests/test_graph.py`)
| ID | Test | Expected |
|----|------|----------|
| GR-1 | Happy path | invalid→reject skipped; reaches `synthesize` |
| GR-2 | Retrieval gate | no relevant docs routes back to `plan` |
| GR-3 | Grounding loop | low score with retries left routes to `plan`; exhausted routes to `flag` |
| GR-4 | Invalid input | routes straight to `reject` |

### End-to-end (`tests/test_e2e.py`)
| ID | Test | Expected |
|----|------|----------|
| E2E-1 | Cross-document question (mocked LLM) | returns final answer + citations + eval report; trace has ≥ 5 steps |
| E2E-2 | Unanswerable question | returns flagged/limited answer with disclaimer |

## 5.3 Coverage goals & commands

- Target: **≥ 80%** line coverage on `src/` (excluding the optional UI).
- Run: `pytest -q`
- Coverage: `pytest --cov=src --cov-report=term-missing`

## 5.4 Traceability — tests ↔ rubric / user stories

| Rubric area | Covering tests |
|-------------|----------------|
| Retrieval & RAG | ING-*, RET-* |
| Planning & Orchestration | ORCH-*, GR-1/2/3 |
| Reasoning & Synthesis | ANA-* |
| Validation & Guardrails | VER-*, GRD-* |
| Evaluation & Observability | EVAL-*, E2E-* |

This closes the documentation set. Return to the [index](README.md).
