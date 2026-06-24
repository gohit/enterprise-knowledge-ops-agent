# 0. Submission Summary & Rubric Mapping

A one-page orientation for the evaluator. It maps every **rubric criterion**, **user story**,
and **required deliverable** to exactly where it is satisfied — so the submission can be scored
quickly and nothing is missed.

> **Project:** Enterprise Knowledge Ops Agent — a local, multi-agent Agentic AI system
> (LangGraph) that answers complex enterprise questions by reasoning across 13 Cognizant
> global HR policy documents.

---

## A. One-paragraph overview

A user asks a complex, possibly cross-document question. An **Orchestrator** agent plans the
work by decomposing it into ordered subtasks. A **Retriever** agent runs RAG over a Chroma
vector store for each subtask, preserving relevance scores and source metadata. An **Analyst**
agent reasons across the retrieved evidence and synthesizes a cited answer. A **Verifier**
agent checks every claim against its sources, computes a grounding score, and — if confidence
is low — sends control back to re-plan or returns a limited, flagged answer rather than
hallucinating. A **Memory** agent threads context throughout. Every step is logged to an
inspectable decision trace, and each answer ships with citations and a structured evaluation
report. This is implemented as a stateful **LangGraph** with explicit nodes, conditional
routing, and feedback loops.

---

## B. Rubric mapping (100 points)

| # | Rubric criterion | Pts | How this submission targets the top band | Evidence |
|---|------------------|:---:|------------------------------------------|----------|
| 1 | **Agentic Architecture & Design** | 20 | Five clearly-bounded agents (Orchestrator, Retriever, Analyst, Verifier, Memory); orchestration is an explicit LangGraph, not implicit prompt chaining | [01_architecture](01_architecture.md), [diagram](diagrams/01_architecture_1.png) |
| 2 | **Query Planning & Orchestration** | 15 | Orchestrator emits a structured multi-subtask plan; conditional edges route and re-plan | [02_agent_flow](02_agent_flow.md), [diagram](diagrams/02_agent_flow_1.png) |
| 3 | **Retrieval & RAG Effectiveness** | 15 | Per-subtask retrieval with relevance scores; source + page metadata preserved for citation | [01 §1.5](01_architecture.md), [03 Phase 1](03_implementation_plan.md) |
| 4 | **Reasoning & Synthesis** | 15 | Analyst reasons *across* documents (overlapping policy clusters force real synthesis) | [02_agent_flow](02_agent_flow.md), [06 clusters](06_corpus_guide.md) |
| 5 | **Validation, Grounding & Guardrails** | 15 | Verifier enforces claim-level grounding; input/retrieval/output guardrails; abstains on low confidence | [04_evaluation_and_guardrails](04_evaluation_and_guardrails.md) |
| 6 | **Evaluation & Observability** | 10 | Retrieval scores, grounding checks, decision traces, and 3 failure detectors — all logged in structured form | [04 §4.3](04_evaluation_and_guardrails.md) |
| 7 | **Documentation & Explainability** | 10 | Architecture + flow diagrams, agent-role docs, exported images, this mapping | all of [docs/](README.md) |

---

## C. User-story coverage

| User Story | Acceptance criteria met by | Where |
|------------|----------------------------|-------|
| **US1** Complex query handling | decompose → multi-subtask retrieve → cross-doc synthesis | [02 §2.2](02_agent_flow.md) |
| **US2** Planning & orchestration | Orchestrator node + conditional edges + logged trace | [02 §2.1, §2.5](02_agent_flow.md) |
| **US3** Grounded & validated responses | Verifier + grounding score + low-confidence flagging + citations | [04 §4.1.3](04_evaluation_and_guardrails.md) |
| **US4** Explainability & transparency | decision-trace events + reasoning summaries surfaced in UI | [02 §2.5](02_agent_flow.md) |
| **US5** Governance & guardrails | input validation + hallucination control + source attribution | [04 §4.1–4.2](04_evaluation_and_guardrails.md) |
| **US6** Evaluation, observability & failure detection | relevance scores + grounding + traces + 3 failure detectors + structured logs | [04 §4.3](04_evaluation_and_guardrails.md) |

---

## D. Deliverables checklist (case study §6)

| Deliverable | Status | Location |
|-------------|:------:|----------|
| Application code base | Planned (Phases 0–6) | `src/`, `ui/` |
| Fully functional, running application | Planned | CLI `src.app` + Streamlit UI |
| Architecture and agent flow diagram | **Done** | [docs/diagrams/](diagrams/) (SVG + PNG) |
| Evaluation and guardrail documentation | **Done** | [04_evaluation_and_guardrails](04_evaluation_and_guardrails.md) |
| Unit test case documentation | **Done** (plan); suite in Phase 6 | [05_unit_test_plan](05_unit_test_plan.md) |

> **Current state:** Design, documentation, and diagrams are complete. Application code is the
> next phase per the [implementation plan](03_implementation_plan.md). This summary will be
> updated to "Done" as each phase lands.

---

## E. What distinguishes this from a basic RAG submission

1. **Explicit orchestration** — the plan is a structured object emitted by a real node, logged
   and inspectable; not a hidden instruction inside one prompt.
2. **A genuine feedback loop** — the Verifier can route control *back* to the Orchestrator
   (re-plan / re-retrieve), which is agentic control flow, not a linear pipeline.
3. **Responsible uncertainty handling** — bounded retries, then **abstention with a
   disclaimer** instead of a confident hallucination.
4. **Self-evaluation** — every answer carries a structured evaluation report (retrieval
   relevance, grounding score, failure flags) that an evaluator can inspect directly.
5. **Cross-document corpus** — the 13 policies deliberately overlap, so answers require real
   multi-document synthesis rather than single-passage lookup.

---

## F. How to evaluate quickly

1. Read this page (you're here) and the [architecture diagram](diagrams/01_architecture_1.png).
2. Skim [02_agent_flow](02_agent_flow.md) §2.2 for a concrete worked query.
3. Run a **Tier 2/3** demo query from the [corpus guide](06_corpus_guide.md#64-demo-query-catalogue)
   and inspect the decision trace + evaluation panel.
4. Run a **Tier 4** guardrail query to see abstention / injection defense.
5. Run `pytest -q` against the [test plan](05_unit_test_plan.md).
