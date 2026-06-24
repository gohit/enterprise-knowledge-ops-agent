"""Unit tests for document loading and chunking (ING-* cases).

These run fully offline against the real Policies/ PDFs — no Azure needed.
"""
from __future__ import annotations

import pytest

from src.config import settings
from src.ingestion.loader import load_and_split, load_documents, split_documents


@pytest.fixture(scope="module")
def pages():
    return load_documents()


def test_ing1_load_returns_pages_with_metadata(pages):
    """ING-1: loading yields non-empty pages with source + page metadata."""
    assert len(pages) > 0
    first = pages[0]
    assert first.page_content.strip()
    assert first.metadata["source"].endswith(".pdf")
    assert isinstance(first.metadata["page"], int)
    assert first.metadata["page"] >= 1  # 1-indexed for citations


def test_ing2_split_produces_citable_chunks(pages):
    """ING-2: chunks respect size and carry source, page, chunk_id."""
    chunks = split_documents(pages)
    assert len(chunks) >= len(pages)
    for chunk in chunks[:50]:
        assert {"source", "page", "chunk_id"} <= set(chunk.metadata)
        assert chunk.metadata["chunk_id"].count("::") == 2
        # allow some overshoot for separators, but chunks shouldn't be huge
        assert len(chunk.page_content) <= settings.chunk_size * 2


def test_ing2_chunk_ids_are_unique(pages):
    chunks = split_documents(pages)
    ids = [c.metadata["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))


def test_ing3_missing_directory_raises():
    """ING-3: a missing source directory raises a clear error."""
    with pytest.raises(FileNotFoundError):
        load_documents("does-not-exist-dir")


def test_load_and_split_covers_multiple_policies(pages):
    """Corpus sanity: chunks should span several distinct policy files."""
    chunks = load_and_split()
    sources = {c.metadata["source"] for c in chunks}
    assert len(sources) >= 5  # we have 13 policies; expect many distinct sources
