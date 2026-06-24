# Enterprise Knowledge Ops Agent — Documentation

This folder contains the design and planning documentation for the **Enterprise Knowledge
Operations Agent**, a local, multi-agent Agentic AI system built with **LangGraph** that
answers complex enterprise questions by reasoning across multiple documents.

> Tech tower: **Open Source / LangGraph + AWS**
> Stack: Python · LangChain · LangGraph · Embeddings · RAG · Azure OpenAI · Chroma (vector DB) · Guardrails · Streamlit (optional UI) · AWS (deploy)

## How to read these docs

**Running the project locally?** Start with [GETTING_STARTED.md](../GETTING_STARTED.md) (setup,
documents, ingestion, and run commands).

Read the design docs below in order — each builds on the previous one.

| # | Document | What it covers | Maps to deliverable |
|---|----------|----------------|---------------------|
| 🚀 | [GETTING_STARTED.md](../GETTING_STARTED.md) | Local setup, PDFs, index build, CLI & UI | (run guide) |
| ⭐ | [STUDY_GUIDE.md](STUDY_GUIDE.md) | Plain-language walkthrough + evaluation Q&A (read this to learn the project) | (learning / eval prep) |
| 0 | [00_submission_summary.md](00_submission_summary.md) | Rubric + user-story mapping, deliverables checklist (read first) | (evaluator orientation) |
| 1 | [01_architecture.md](01_architecture.md) | System architecture, the 5 agents, component diagram | Architecture diagram |
| 2 | [02_agent_flow.md](02_agent_flow.md) | How a single query flows through the LangGraph state machine | Agent flow diagram |
| 3 | [03_implementation_plan.md](03_implementation_plan.md) | Phased, step-by-step build plan with a checklist | (build guide) |
| 4 | [04_evaluation_and_guardrails.md](04_evaluation_and_guardrails.md) | Grounding checks, guardrails, failure detection, observability | Evaluation & guardrail documentation |
| 5 | [05_unit_test_plan.md](05_unit_test_plan.md) | Unit test cases per component | Unit test case documentation |
| 6 | [06_corpus_guide.md](06_corpus_guide.md) | The 13-policy document set, overlap clusters, demo query catalogue | (corpus + demo guide) |

## The 30-second summary

A user asks a complex question. Instead of one model doing a single retrieval + answer, a
**team of specialized agents** coordinates:

1. **Orchestrator** plans the work — breaks the question into sub-questions.
2. **Retriever** pulls relevant chunks from a vector database for each sub-question.
3. **Analyst** reasons across the retrieved chunks and synthesizes an answer.
4. **Verifier** checks that every claim is grounded in the sources; flags low confidence.
5. **Memory** carries context (prior turns, intermediate findings) across the whole run.

Every step is **logged and traceable**, every answer carries **source citations**, and an
**evaluation report** (grounding score, retrieval relevance, failure flags) accompanies the
response. This is what separates an "agentic" system from a plain RAG chatbot — and it is
exactly what the rubric rewards.

## Scoring alignment (why each doc matters)

| Rubric criterion | Points | Covered in |
|------------------|:------:|------------|
| Agentic Architecture & Design | 20 | Docs 1, 2 |
| Query Planning & Orchestration | 15 | Docs 1, 2 |
| Retrieval & RAG Effectiveness | 15 | Docs 1, 3 |
| Reasoning & Synthesis | 15 | Docs 1, 2 |
| Validation, Grounding & Guardrails | 15 | Doc 4 |
| Evaluation & Observability | 10 | Doc 4 |
| Documentation & Explainability | 10 | All docs |
