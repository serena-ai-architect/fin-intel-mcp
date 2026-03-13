"""RAG generation with citations using DeepSeek-V3."""

from datetime import datetime, timezone

from openai import AsyncOpenAI

from config import settings
from db.models import Citation, RAGResult

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    return _client


RAG_SYSTEM_PROMPT = """You are a financial analyst assistant. Answer the user's question based ONLY on the provided context chunks.

Rules:
1. If the context doesn't contain enough information, say so explicitly — never hallucinate.
2. Cite your sources using [1], [2], etc. matching the chunk numbers provided.
3. Be specific with numbers, dates, and financial figures when available.
4. Keep answers concise but thorough.
"""


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into numbered context for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        title = chunk.get("title", "Unknown")
        ticker = chunk.get("ticker", "")
        fiscal_year = chunk.get("fiscal_year", "")
        header = f"[{i}] {title} ({ticker} FY{fiscal_year})" if fiscal_year else f"[{i}] {title} ({ticker})"
        parts.append(f"{header}\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


async def generate_answer(query: str, chunks: list[dict]) -> RAGResult:
    """Generate a cited answer from retrieved chunks using DeepSeek-V3."""
    if not chunks:
        return RAGResult(
            answer="No relevant documents found for your query.",
            citations=[],
            query=query,
        )

    client = _get_client()
    context = _build_context(chunks)

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
        temperature=0.3,
        max_tokens=2048,
    )

    answer = response.choices[0].message.content or ""

    # Build citations from the chunks that were provided to the LLM
    citations = [
        Citation(
            chunk_id=str(chunk.get("id", "")),
            document_title=chunk.get("title", "Unknown"),
            content_snippet=chunk["content"][:200],
            relevance_score=chunk.get("rerank_score", chunk.get("rrf_score", 0.0)),
        )
        for chunk in chunks
    ]

    return RAGResult(
        answer=answer,
        citations=citations,
        query=query,
        retrieval_method="hybrid",
    )
