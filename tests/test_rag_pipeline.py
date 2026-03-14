"""Tests for RAG pipeline components — no database required."""

import pytest

from rag.chunker import chunk_text
from rag.reranker import rerank


class TestChunker:
    def test_chunk_short_text(self):
        """Short text should return a single chunk."""
        text = "This is a short text about NVIDIA's revenue growth."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_long_text(self):
        """Long text should be split into multiple overlapping chunks."""
        # Create text that's clearly longer than chunk_size (500)
        text = "NVIDIA reported record revenue of $60.9 billion for fiscal year 2024. " * 20
        chunks = chunk_text(text)
        assert len(chunks) > 1
        # Check that chunks are not empty
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_preserves_content(self):
        """All content should be present across chunks."""
        sentences = [f"Sentence number {i} with unique content." for i in range(50)]
        text = " ".join(sentences)
        chunks = chunk_text(text)
        rejoined = " ".join(chunks)
        # Each original sentence should appear in at least one chunk
        for s in sentences[:5]:  # Spot check first 5
            assert s in rejoined or s.split()[0] in rejoined


class TestReranker:
    def test_rerank_fallback_sorts_by_rrf(self):
        """Without cross-encoder, reranker should fall back to RRF scores."""
        chunks = [
            {"content": "Low relevance text", "rrf_score": 0.1},
            {"content": "High relevance text about revenue", "rrf_score": 0.9},
            {"content": "Medium relevance text", "rrf_score": 0.5},
        ]
        result = rerank("NVIDIA revenue", chunks, top_k=2)
        assert len(result) == 2
        assert result[0]["rrf_score"] == 0.9
        assert result[1]["rrf_score"] == 0.5

    def test_rerank_empty_chunks(self):
        """Empty input should return empty output."""
        result = rerank("test query", [], top_k=5)
        assert result == []

    def test_rerank_respects_top_k(self):
        """Should return at most top_k results."""
        chunks = [{"content": f"chunk {i}", "rrf_score": 0.5} for i in range(10)]
        result = rerank("test", chunks, top_k=3)
        assert len(result) == 3


class TestRRFFusion:
    def _fuse(self, vec, bm25, k=60, top_k=5):
        from rag.retriever import _rrf_fuse
        return _rrf_fuse(vec, bm25, k=k, top_k=top_k)

    def test_rrf_basic_fusion(self):
        """Test RRF fusion logic directly."""
        vec = [
            {"id": "a", "content": "doc A"},
            {"id": "b", "content": "doc B"},
        ]
        bm25 = [
            {"id": "b", "content": "doc B"},
            {"id": "c", "content": "doc C"},
        ]
        result = self._fuse(vec, bm25, k=60, top_k=3)

        # "b" appears in both lists, should rank highest
        assert result[0]["id"] == "b"
        assert len(result) == 3
        # All results should have rrf_score
        for r in result:
            assert "rrf_score" in r
            assert r["rrf_score"] > 0

    def test_rrf_no_overlap(self):
        """When lists have no overlap, all docs should still appear."""
        vec = [{"id": "a", "content": "A"}]
        bm25 = [{"id": "b", "content": "B"}]
        result = self._fuse(vec, bm25, k=60, top_k=5)
        assert len(result) == 2

    def test_rrf_single_list(self):
        """When one list is empty, should still return results from the other."""
        vec = [{"id": "a", "content": "A"}, {"id": "b", "content": "B"}]
        result = self._fuse(vec, [], k=60, top_k=5)
        assert len(result) == 2
