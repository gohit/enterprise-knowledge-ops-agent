# Policies — source documents

This folder is where the system reads its source documents from (configured as
`SOURCE_DOCS_DIR` in `src/config.py`, defaulting to `Policies/`).

> **PDF files are not included in the repository.** They are excluded via `.gitignore`
> (`*.pdf`). You must add your own documents before building the index.

## Quick steps

See **[GETTING_STARTED.md](../GETTING_STARTED.md)** for the full setup guide. In short:

1. Place your policy / SOP / contract **PDFs** into this `Policies/` folder.
2. Configure `.env` and verify model access (`python tools/check_model.py`).
3. Build the index:
   ```bash
   python -m src.ingestion.index --rebuild
   ```
4. Ask questions via the CLI or Streamlit UI (see [GETTING_STARTED.md](../GETTING_STARTED.md) §7).

Use **text-based PDFs** (not scanned images). For richer cross-document demos, use a set of
documents that overlap in subject matter — see [docs/06_corpus_guide.md](../docs/06_corpus_guide.md).

To point at a different folder, set `SOURCE_DOCS_DIR` in `.env`.
