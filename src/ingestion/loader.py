"""Load enterprise PDF documents and split them into citable chunks.

Each chunk carries metadata used downstream for retrieval and source attribution:
- ``source``    : the PDF filename (e.g. "Global Rehire Policy.pdf")
- ``page``      : 1-indexed page number
- ``chunk_id``  : stable id like "Global Rehire Policy.pdf::p3::12"

This module needs no Azure credentials — it is pure document processing, so it can
be unit-tested offline.
"""
from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from src.config import settings


def load_documents(source_dir: str | Path | None = None) -> list[Document]:
    """Load every PDF in ``source_dir`` as one Document per page.

    Uses pypdf directly (rather than the sunset langchain-community loader) so the
    ingestion path has no deprecated dependencies. Blank pages are skipped.
    """
    source_dir = Path(source_dir or settings.source_docs_dir)
    if not source_dir.exists():
        raise FileNotFoundError(f"Source documents directory not found: {source_dir}")

    pdfs = sorted(source_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in {source_dir}")

    docs: list[Document] = []
    for pdf in pdfs:
        reader = PdfReader(str(pdf))
        for page_index, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if not text:
                continue  # skip image-only / empty pages
            docs.append(
                Document(
                    page_content=text,
                    # filename as source, 1-indexed page for human-readable citations.
                    metadata={"source": pdf.name, "page": page_index + 1},
                )
            )
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    """Split page-level documents into overlapping, citable chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "doc")
        page = chunk.metadata.get("page", "?")
        chunk.metadata["chunk_id"] = f"{source}::p{page}::{i}"
    return chunks


def load_and_split(source_dir: str | Path | None = None) -> list[Document]:
    """Convenience: load all PDFs and return ready-to-index chunks."""
    return split_documents(load_documents(source_dir))
