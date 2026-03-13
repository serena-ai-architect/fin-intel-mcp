"""Hybrid retrieval: vector search + BM25 fused via Reciprocal Rank Fusion (RRF)."""

from db.vector_store import bm25_search, get_session, vector_search
from rag.embedder import embed_query


def _rrf_fuse(
    vector_results: list[dict],
    bm25_results: list[dict],
    k: int = 60,
    top_k: int = 5,
) -> list[dict]:
    """Reciprocal Rank Fusion: combine two ranked lists into one.

    RRF score = sum( 1 / (k + rank_i) ) for each list the doc appears in.
    k=60 is the standard constant from the original paper.
    """
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for rank, doc in enumerate(vector_results):
        doc_id = str(doc["id"])
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        docs[doc_id] = doc

    for rank, doc in enumerate(bm25_results):
        doc_id = str(doc["id"])
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        docs[doc_id] = doc

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]
    results = []
    for doc_id in sorted_ids:
        doc = docs[doc_id]
        doc["rrf_score"] = scores[doc_id]
        results.append(doc)
    return results


async def hybrid_retrieve(
    query: str,
    top_k: int = 5,
    ticker: str | None = None,
    filing_type: str | None = None,
) -> list[dict]:
    """Run vector + BM25 search in parallel, fuse with RRF.

    Returns top_k chunks ranked by combined relevance.
    """
    query_embedding = await embed_query(query)

    # Fetch more candidates from each source for better fusion
    fetch_k = top_k * 3

    async with get_session() as session:
        vec_results = await vector_search(
            session, query_embedding, top_k=fetch_k, ticker=ticker, filing_type=filing_type
        )
        bm25_results = await bm25_search(
            session, query, top_k=fetch_k, ticker=ticker, filing_type=filing_type
        )

    return _rrf_fuse(vec_results, bm25_results, top_k=top_k)
