# Getting Started

Step-by-step guide to run the **Enterprise Knowledge Ops Agent** on your machine — whether you
cloned the repo, downloaded a zip, or are setting it up again after some time away.

The system runs **locally** (agents, vector database, UI). Chat and embedding calls go to your
configured cloud provider (**AWS Bedrock** by default, or **Azure OpenAI**).

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Python 3.10+** | 3.11 or 3.12 recommended; 3.13 works if your dependencies install cleanly |
| **Git** (optional) | Only needed if you clone instead of downloading a zip |
| **Model access** | AWS Bedrock or Azure OpenAI account with chat + embedding models enabled |
| **Source documents** | Your own PDFs (policies, SOPs, contracts, etc.) — **not included in the repo** |

---

## 1. Get the code

```bash
git clone https://github.com/gohit/enterprise-knowledge-ops-agent.git
cd enterprise-knowledge-ops-agent
```

If you downloaded a zip, extract it and `cd` into the project folder.

---

## 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> Always activate the virtual environment before running project commands. Your prompt will
> usually show `(.venv)` when it is active.

---

## 3. Configure credentials

Copy the example environment file and edit it:

**Windows:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Open `.env` and set `LLM_PROVIDER` to `bedrock` (default) or `azure`.

### AWS Bedrock (default)

```env
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=          # optional — leave blank to use ~/.aws/credentials or SSO
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=          # only for temporary credentials
BEDROCK_CHAT_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
BEDROCK_EMBED_MODEL_ID=amazon.titan-embed-text-v2:0
```

- Enable model access in the [Bedrock console](https://console.aws.amazon.com/bedrock/) for your region.
- Ensure your IAM principal has `bedrock:InvokeModel`.
- List models available in your account: `python tools/list_bedrock_models.py`
- See the root [README.md](README.md#credentials-aws-bedrock) for detailed credential options.

### Azure OpenAI (alternative)

```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small
```

Never commit `.env` — it is listed in `.gitignore`.

---

## 4. Add your source documents

Place **text-based PDF files** in the `Policies/` folder at the project root:

```
Policies/
├── your-policy-one.pdf
├── your-policy-two.pdf
└── ...
```

**Important:**

- PDFs are **not stored in the repository** (they are excluded by `.gitignore`). You must supply your own files.
- Use **text PDFs** (normal policy documents). Scanned image-only PDFs need OCR first; this project uses `pypdf` text extraction.
- Any enterprise documents work — HR policies, SOPs, internal guides, contracts. For richer multi-document demos, use a set of documents that overlap in topic (see [docs/06_corpus_guide.md](docs/06_corpus_guide.md) for examples and sample queries).
- To use a different folder, set `SOURCE_DOCS_DIR` in `.env` (path relative to the project root or absolute).

---

## 5. Verify model access

Before building the index, confirm chat and embedding models respond:

```bash
python tools/check_model.py
```

Fix any errors reported here (wrong region, model not enabled, expired credentials) before
continuing.

---

## 6. Build the vector index (process your documents)

Ingestion loads every PDF in `Policies/`, splits them into chunks, embeds them, and stores the
result in a local **Chroma** database at `data/vectorstore/`.

```bash
python -m src.ingestion.index --rebuild
```

You should see output like:

```
Indexed 495 chunks into .../data/vectorstore
```

(Your chunk count depends on how many PDFs you added and their length.)

### What ingestion does

| Step | What happens |
|------|----------------|
| **Load** | Each `*.pdf` in `Policies/` is read with `pypdf` |
| **Split** | Text is chunked (~800 characters, 120 overlap by default) |
| **Metadata** | Each chunk keeps `source` (filename), `page` (1-based), and `chunk_id` for citations |
| **Embed** | Chunks are embedded via your configured provider (Bedrock Titan or Azure embeddings) |
| **Store** | Vectors are persisted in `data/vectorstore/` (also git-ignored) |

### When to re-run

Run `python -m src.ingestion.index --rebuild` again whenever you:

- Add, remove, or replace PDFs in `Policies/`
- Change `SOURCE_DOCS_DIR`, `CHUNK_SIZE`, or `CHUNK_OVERLAP` in `.env`
- Switch embedding provider or model (Bedrock ↔ Azure, or a different embed model)

The `--rebuild` flag deletes the old index and recreates it from scratch.

---

## 7. Ask questions

### CLI (multi-agent graph)

```bash
python -m src.app "What is the rehire policy for former employees?"
```

Show the agent decision trace:

```bash
python -m src.app "Your question here" --trace
```

Compare against a simple single-step RAG baseline:

```bash
python -m src.app "Your question here" --baseline
```

### Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

Opens a browser at `http://localhost:8501` with the answer, sources, decision trace, and
evaluation panel. Press `Ctrl+C` in the terminal to stop.

Use a different port if needed:

```bash
streamlit run ui/streamlit_app.py --server.port 8502
```

Each run also writes a JSON trace to `logs/trace_<timestamp>.json`.

---

## 8. Run tests (optional)

Unit tests use mocked LLMs and do **not** require live model credentials or a built index:

```bash
python -m pytest -q
```

With coverage:

```bash
python -m pytest --cov=src --cov-report=term-missing
```

See [docs/05_unit_test_plan.md](docs/05_unit_test_plan.md) for the full test catalogue.

---

## Quick reference

| Task | Command |
|------|---------|
| Activate venv (Windows) | `.\.venv\Scripts\Activate.ps1` |
| Activate venv (macOS/Linux) | `source .venv/bin/activate` |
| Install dependencies | `python -m pip install -r requirements.txt` |
| Verify models | `python tools/check_model.py` |
| List Bedrock models | `python tools/list_bedrock_models.py` |
| Build / rebuild index | `python -m src.ingestion.index --rebuild` |
| Ask via CLI | `python -m src.app "your question" --trace` |
| Launch UI | `streamlit run ui/streamlit_app.py` |
| Run tests | `python -m pytest -q` |

---

## Optional configuration

Set these in `.env` (defaults shown in `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SOURCE_DOCS_DIR` | `Policies` | Folder containing source PDFs |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `CHUNK_OVERLAP` | `120` | Overlap between consecutive chunks |
| `TOP_K` | `4` | Chunks retrieved per sub-question |
| `MIN_RELEVANCE` | `0.2` | Below this score, retrieval is treated as insufficient |
| `GROUNDING_THRESHOLD` | `0.75` | Minimum grounding score to accept an answer |
| `MAX_RETRIES` | `2` | Re-plan / re-retrieve attempts before abstaining |

---

## Troubleshooting

| Problem | Likely fix |
|---------|------------|
| `Indexed 0 chunks` | No PDFs in `Policies/` (or wrong `SOURCE_DOCS_DIR`) |
| `Embeddings are not configured` | Check `.env` — provider, region, and model IDs |
| `AccessDenied` / `ExpiredToken` (AWS) | Refresh credentials; update `AWS_*` in `.env` |
| Model not found | Run `python tools/list_bedrock_models.py`; use an ACTIVE model id for your region |
| Empty or garbled PDF text | PDF may be scanned images — use a text-based PDF or OCR first |
| Port 8501 already in use | `streamlit run ... --server.port 8502` |
| Index seems stale after adding PDFs | Re-run with `--rebuild` |

---

## Next steps

- **Architecture & agent flow:** [docs/README.md](docs/README.md)
- **Demo queries & corpus design:** [docs/06_corpus_guide.md](docs/06_corpus_guide.md)
- **Evaluation & guardrails:** [docs/04_evaluation_and_guardrails.md](docs/04_evaluation_and_guardrails.md)
- **Project overview:** [README.md](README.md)
