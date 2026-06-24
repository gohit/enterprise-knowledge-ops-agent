# Study Guide — Enterprise Knowledge Ops Agent

A plain-language guide to understand this project for an evaluation. Read top to bottom once,
then use the **Q&A** at the end to self-test. Everything here reflects the actual code.

---

## 1. What is this project, in one paragraph?

It's an **Enterprise Knowledge Operations Agent** — a local, **multi-agent AI system** that
answers complex questions about company policy documents by *reasoning across several documents
at once*. Instead of one model doing a single "search-then-answer" (basic RAG), a **team of five
specialized agents** plans the work, retrieves evidence, reasons over it, verifies the answer is
grounded in the sources, and explains how it got there. It is built with **LangGraph** and runs
on **AWS Bedrock** (Claude + Titan).

## 2. Why not just a normal chatbot?

A basic RAG chatbot has three weaknesses the case study calls out:
1. It reacts in one pass — no planning for multi-step questions.
2. It has no specialized roles (retrieval, reasoning, validation are all mashed together).
3. It can't explain *how* or *why* it produced an answer, and it happily hallucinates when
   retrieval is poor.

This system fixes all three: it **plans**, it has **distinct agent roles**, and every answer
comes with **citations, a decision trace, and an evaluation report**. When it isn't confident,
it **says so** instead of making things up.

## 3. The technology (quick facts)

| Concern | Choice |
|---------|--------|
| Orchestration framework | **LangGraph** (a stateful graph of agent "nodes" with conditional routing) |
| Supporting libraries | **LangChain** (loaders, splitters, model wrappers) |
| Chat LLM | **Anthropic Claude Sonnet 4.5** on **AWS Bedrock** (`us.anthropic.claude-sonnet-4-5-...`) |
| Embeddings | **Amazon Titan Text Embeddings V2** on Bedrock (1024-dim vectors) |
| Vector database | **Chroma** (local, persisted in `data/vectorstore/`) |
| Documents | 13 Cognizant **HR policy PDFs** in `Policies/` → 128 pages → **495 chunks** |
| UI | **Streamlit** (chat-style, with explainability panels) |
| Provider switch | `LLM_PROVIDER` in `.env` → `bedrock` (default) or `azure` |
| Tests | **pytest** — 47 tests, all run offline with a mocked LLM |

> Note on "local": the *system* runs locally (vector DB, agents, UI). The *models* are called
> via AWS Bedrock (a cloud API). The model layer is swappable, so the provider can change without
> touching the agents.

## 4. The five agents (the heart of it)

| Agent | One-line job | File |
|-------|--------------|------|
| **Orchestrator** | Plans: breaks the question into sub-questions | `src/agents/orchestrator.py` |
| **Retriever** | RAG: fetches the most relevant chunks per sub-question | `src/agents/retriever.py` |
| **Analyst** | Reasons across the retrieved evidence and writes the answer | `src/agents/analyst.py` |
| **Verifier** | Checks every claim is supported by the sources (grounding) | `src/agents/verifier.py` |
| **Memory** | Records the run (query, plan, answer) for context | `src/agents/memory.py` |

Each agent has **one job** and doesn't do the others' work — that clean separation is what makes
it a *true* multi-agent system (and what the rubric rewards most).

## 5. How a question flows through the system

This is the most important thing to understand. The flow is a **LangGraph state machine**
(`src/graph/build_graph.py`):

```
START
  → validate        (guardrail: empty? too long? injection attempt?)
  → orchestrator    (plan: split the question into sub-questions)
  → retriever       (fetch top-k chunks per sub-question, with relevance scores)
  → [retrieval gate]  relevant? → continue : re-plan (bounded) : abstain
  → analyst         (reason across all evidence → draft answer with citations)
  → verifier        (score how well the draft is grounded in sources)
  → [grounding gate]  grounded? → finalize : re-plan (bounded) : return limited answer
  → finalize / limited
  → memory          (record the run)
  → END
```

A worked example — *"Can a resigned employee be rehired, and what separation conditions apply?"*:
1. **validate** → passes.
2. **orchestrator** → 2 sub-questions: (a) rehire eligibility, (b) surviving separation conditions.
3. **retriever** → pulls chunks from the Rehire Policy for (a) and the Separation Policy for (b).
4. **analyst** → writes one coherent answer combining both, citing `[source, p.X]`.
5. **verifier** → grounding score (e.g. 1.0) → pass.
6. **finalize → memory → END** → answer + sources + evaluation report returned.

## 6. The feedback loops (what makes it "agentic", not linear)

There are **two bounded re-plan loops**. A basic pipeline goes straight through; this system can
*loop back and try again*:

- **Retrieval gate** — if no sub-question found relevant evidence (top score below
  `MIN_RELEVANCE`, default 0.2), it loops back to the Orchestrator to re-plan. After
  `MAX_RETRIES` (default 2), it **abstains** with an `insufficient_retrieval` flag.
- **Grounding gate** — if the Verifier says the answer isn't well supported (grounding score
  below `GROUNDING_THRESHOLD`, default 0.75), it loops back to re-plan. After retries, it returns
  a **limited answer with a disclaimer** and a `low_grounding` flag.

Both loops are **bounded** by a shared `attempts` counter so the system can never loop forever.

## 7. Guardrails and trust (anti-hallucination)

| Where | What it does |
|-------|--------------|
| **Input** (`guardrails/input_validation.py`) | Rejects empty/over-long input; detects prompt-injection ("ignore previous instructions", "reveal your system prompt") before any LLM call |
| **Retrieval** | The relevance gate stops the system answering from irrelevant/empty evidence |
| **Output** (`agents/verifier.py` + `guardrails/grounding.py`) | Grounding score gates the answer; low confidence → disclaimer + flag, never a confident fabrication |
| **Citations** | Every fact is cited `[source, p.X]` so any claim can be checked |

## 8. Evaluation & observability (how it shows its work)

Every run produces a structured **evaluation report** and is logged to
`logs/trace_<timestamp>.json` (`src/evaluation/metrics.py` + `tracer.py`). The report contains:
- **Retrieval relevance** — top & mean similarity score per sub-question
- **Grounding score** + verdict (pass/fail) + any unsupported claims
- **Failure flags** — `invalid_input`, `insufficient_retrieval`, `low_grounding`
- **Decision trace** — the full ordered list of agent actions
- **Step count** and agent invocation order

The Streamlit UI shows the same three things as expandable panels: **Sources**, **Decision
Trace**, **Evaluation**.

## 9. How AWS Bedrock is wired in

Only **two files** know about the model provider:
- `src/llm.py` → `get_chat_llm()` returns a Claude client on Bedrock (or Azure).
- `src/ingestion/index.py` → `get_embeddings()` returns Titan embeddings (or Azure).

Both read `LLM_PROVIDER` from config and build a shared boto3 client (`src/aws.py`). Everything
else — agents, graph, guardrails, evaluation — is provider-agnostic. That's why the system was
fully built and tested with a **mocked LLM** before any cloud key existed.

## 10. Project structure (where to find things)

```
Policies/            the 13 source PDFs
data/vectorstore/    the Chroma index (generated)
src/
  config.py          all settings (.env-driven)
  llm.py             chat model factory (provider switch)
  aws.py             shared Bedrock client
  ingestion/         loader.py (PDF→chunks), index.py (embed + retrieve)
  agents/            orchestrator, retriever, analyst, verifier, memory
  graph/             state.py (shared state), build_graph.py (the state machine)
  guardrails/        input_validation.py, grounding.py
  evaluation/        metrics.py (report), tracer.py (logging)
  baseline.py        the simple single-agent RAG (for comparison)
  app.py             CLI entry point
ui/streamlit_app.py  the web UI
tests/               47 unit tests (offline, mocked LLM)
docs/                all design documentation + diagrams
```

## 11. How to run it (commands)

```powershell
# build the document index (once, or after changing docs/provider)
& ".\.venv\Scripts\python.exe" -m src.ingestion.index --rebuild
# ask from the CLI, showing the decision trace
& ".\.venv\Scripts\python.exe" -m src.app "your question" --trace
# launch the UI
& ".\.venv\Scripts\streamlit.exe" run ui\streamlit_app.py
# run the tests
& ".\.venv\Scripts\python.exe" -m pytest -q
```

## 12. How it maps to the rubric (100 points)

| Rubric criterion | Pts | Where it's earned |
|------------------|:---:|-------------------|
| Agentic Architecture & Design | 20 | 5 distinct agents + explicit LangGraph |
| Query Planning & Orchestration | 15 | Orchestrator decomposes; conditional routing + re-plan loops |
| Retrieval & RAG Effectiveness | 15 | Per-subtask retrieval with scores + source/page metadata |
| Reasoning & Synthesis | 15 | Analyst combines evidence across documents |
| Validation, Grounding & Guardrails | 15 | Verifier grounding score + input guardrail + abstention |
| Evaluation & Observability | 10 | Trace + report logged to JSON; failure detection |
| Documentation & Explainability | 10 | These docs, diagrams, UI panels |

---

# Q&A — practise for the evaluation

## Easy / definition questions

**Q: What is this case study about?**
Building an *agentic* AI system — the Enterprise Knowledge Ops Agent — that answers complex
questions across multiple enterprise policy documents using a coordinated team of specialized
agents, with grounding, guardrails, and explainability. It goes beyond a basic RAG chatbot.

**Q: What problem does it solve?**
Business users need accurate, explainable answers that require reasoning across *several*
documents. Basic RAG chatbots react in one pass, lack specialized roles, and can't explain or
verify their answers. This system plans, reasons across documents, validates, and explains.

**Q: How many agents are there, and what are they?**
Five: **Orchestrator** (planning), **Retriever** (RAG), **Analyst** (reasoning/synthesis),
**Verifier** (grounding/validation), and **Memory** (context).

**Q: What LLM does it use?**
**Anthropic Claude Sonnet 4.5** via **AWS Bedrock** for the chat/reasoning, and **Amazon Titan
Text Embeddings V2** for embeddings. The provider is switchable to Azure OpenAI via one config
value.

**Q: What is the vector database?**
**Chroma**, stored locally in `data/vectorstore/`.

**Q: What framework ties the agents together?**
**LangGraph** — it models the agents as nodes in a stateful graph with conditional edges (so it
can branch and loop), built on top of **LangChain**.

**Q: What documents does it answer over?**
13 Cognizant global HR policy PDFs (rehire, separation, referral, work model, harassment,
performance, etc.), split into 495 searchable chunks.

**Q: Is it cloud or local?**
The system runs locally (vector DB, agents, UI). Only the model calls go to AWS Bedrock (cloud).

**Q: What is RAG?**
Retrieval-Augmented Generation — fetch relevant document chunks and give them to the LLM so its
answer is grounded in real sources rather than only its training data.

**Q: What is an embedding?**
A numeric vector representing the meaning of text, so similar texts are near each other. We embed
both the documents and the question, then find the closest chunks (similarity search).

## How-it-works questions

**Q: Walk me through what happens when I ask a question.**
Input validation → Orchestrator plans sub-questions → Retriever fetches chunks per sub-question →
(retrieval gate) → Analyst synthesizes a cited answer → Verifier scores grounding → (grounding
gate) → finalize (or limited answer) → Memory records → return answer + sources + evaluation.

**Q: What makes it "agentic" rather than a simple pipeline?**
Explicit planning (the Orchestrator emits a structured plan), distinct agent roles, and **two
feedback loops** that route control *back* to re-plan when retrieval or grounding is weak — plus
bounded retries and abstention. A linear pipeline can't loop or self-correct.

**Q: How does it avoid hallucination?**
Four ways: (1) the Analyst answers only from retrieved context, (2) the Verifier checks each
claim against sources and produces a grounding score, (3) a confidence threshold gates the
answer, and (4) on low confidence it abstains/adds a disclaimer instead of guessing. Plus
citations let users verify everything.

**Q: What is the grounding score?**
A 0–1 number from the Verifier = the fraction of the answer's claims supported by the retrieved
evidence. Below the threshold (0.75) the answer is flagged/limited. Unparseable verifier output
fails safe to 0.0.

**Q: What is the retrieval relevance score for?**
It measures how well retrieved chunks match a sub-question. It (a) drives the retrieval gate
(too low → re-plan/abstain) and (b) is logged in the evaluation report as a quality signal.

**Q: What happens if the answer isn't in the documents?**
The retrieval gate detects no relevant evidence, re-plans up to the retry limit, then **abstains**
with a clear "not enough information" message and an `insufficient_retrieval` flag — it does not
fabricate.

**Q: What failures can the system detect?**
`invalid_input` (guardrail), `insufficient_retrieval` (no relevant evidence), and `low_grounding`
(answer not supported). All are logged in the evaluation report.

**Q: How can I see how it reached an answer?**
The **decision trace** — an ordered log of every agent action (validate, plan, retrieve,
synthesize, ground-check, finalize, record). It's shown in the UI and saved to
`logs/trace_<timestamp>.json`.

**Q: What does the Memory agent do?**
Records each run (query, plan, final answer) into an accumulating memory channel — the basis for
multi-turn context. (Single questions work today; the design supports follow-ups.)

**Q: How do the agents share data?**
Through one shared `GraphState` object that LangGraph threads through every node. Some fields
(trace, failures, memory) *accumulate* across nodes; others are overwritten by the producing
agent.

**Q: How does the Orchestrator decompose a question?**
It prompts the LLM to return JSON listing sub-questions, then parses it tolerantly (with a
single-subtask fallback if parsing fails), producing a structured, inspectable plan.

**Q: Could you swap the LLM?**
Yes — change `LLM_PROVIDER` in `.env` (bedrock ↔ azure) and the model IDs. Only `src/llm.py` and
`src/ingestion/index.py` change behavior; nothing else. (Rebuild the index after switching, since
embedding dimensions differ.)

**Q: How was it tested without a real model key?**
The model layer is injectable, so tests pass a **fake LLM** that returns scripted responses. All
47 tests run offline, deterministically — that's how the whole engine was built before AWS access.

**Q: Why LangGraph and not a plain LangChain chain?**
Because the flow isn't linear — it branches (valid vs reject), loops (re-plan on weak
retrieval/grounding), and shares evolving state across agents. LangGraph models exactly that with
nodes, conditional edges, and a typed state object.

## Likely "explain a design choice" questions

**Q: Why separate the Analyst and the Verifier?**
So generation and checking are independent. The Verifier critiques the Analyst's draft against the
sources — separation of duties is what lets the system catch its own ungrounded claims.

**Q: Why bound the retry loops?**
To guarantee termination and predictable cost — without a cap, a hard question could loop forever.
After the cap, the system degrades gracefully (abstain or disclaimer) rather than spinning.

**Q: What would you improve with more time?**
Examples: tune `MIN_RELEVANCE`/chunking for sharper retrieval, add multi-turn follow-ups through
Memory, add per-subtask sub-answers, detect conflicting sources explicitly, and add Phase 7 AWS
deployment.

Back to the [docs index](README.md).
