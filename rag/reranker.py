"""Cross-encoder reranker for improving retrieval precision.

Falls back to RRF/similarity scores if sentence-transformers is not installed.
"""

from config import settings

_reranker = None
_HAS_CROSS_ENCODER = False

try:
    from sentence_transformers import CrossEncoder

    _HAS_CROSS_ENCODER = True
except ImportError:
    pass


def _get_reranker():
    global _reranker
    if _reranker is None and _HAS_CROSS_ENCODER:
        _reranker = CrossEncoder(settings.reranker_model)
    return _reranker


def rerank(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank retrieved chunks using a cross-encoder model.

    Falls back to existing scores (rrf_score / similarity) if cross-encoder is unavailable.
    """
    if not chunks:
        return []

    reranker = _get_reranker()
    if reranker is None:
        # Fallback: sort by existing scores
        chunks.sort(
            key=lambda x: x.get("rrf_score", x.get("similarity", 0)),
            reverse=True,
        )
        return chunks[:top_k]

    pairs = [[query, chunk["content"]] for chunk in chunks]
    scores = reranker.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    chunks.sort(key=lambda x: x["rerank_score"], reverse=True)
    return chunks[:top_k]
