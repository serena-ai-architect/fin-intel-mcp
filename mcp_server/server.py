"""MCP Server definition — registers all 6 financial intelligence tools."""

import json

from mcp.server.fastmcp import FastMCP

from db.models import (
    AnalyzeSentimentInput,
    GetTechnicalSignalsInput,
    IngestDocumentInput,
    QueryKnowledgeBaseInput,
    SearchEarningsInput,
    SearchFilingsInput,
)

mcp_server = FastMCP(
    "fin-intel-mcp",
    instructions="Financial Intelligence MCP Server — RAG over SEC filings, sentiment analysis, and technical indicators",
)


@mcp_server.tool()
async def search_sec_filings(
    ticker: str,
    query: str,
    filing_type: str | None = None,
    top_k: int = 5,
) -> str:
    """Search SEC filings (10-K, 10-Q, 8-K) using hybrid RAG retrieval.

    Args:
        ticker: Stock ticker symbol (e.g., NVDA, AAPL)
        query: Natural language query about the filing content
        filing_type: Optional filter: "10-K", "10-Q", or "8-K"
        top_k: Number of results (1-20, default 5)
    """
    from observability.langfuse_setup import trace_tool
    from rag.generator import generate_answer
    from rag.reranker import rerank
    from rag.retriever import hybrid_retrieve

    chunks = await hybrid_retrieve(query, top_k=top_k * 2, ticker=ticker, filing_type=filing_type)
    reranked = rerank(query, chunks, top_k=top_k)
    result = await generate_answer(query, reranked)
    return result.model_dump_json()


@mcp_server.tool()
async def search_earnings_calls(
    ticker: str,
    query: str,
    top_k: int = 5,
) -> str:
    """Search earnings call transcripts using RAG.

    Args:
        ticker: Stock ticker symbol
        query: Natural language query about earnings discussions
        top_k: Number of results (1-20, default 5)
    """
    from rag.generator import generate_answer
    from rag.reranker import rerank
    from rag.retriever import hybrid_retrieve

    chunks = await hybrid_retrieve(query, top_k=top_k * 2, ticker=ticker, filing_type=None)
    # Filter to earnings_call document_type if metadata available
    earnings_chunks = [c for c in chunks if c.get("metadata", {}).get("document_type") == "earnings_call"]
    if not earnings_chunks:
        earnings_chunks = chunks  # Fall back to all results
    reranked = rerank(query, earnings_chunks, top_k=top_k)
    result = await generate_answer(query, reranked)
    return result.model_dump_json()


@mcp_server.tool()
async def analyze_sentiment(
    ticker: str,
    texts: list[str],
) -> str:
    """Analyze financial sentiment of texts using FinBERT.

    Args:
        ticker: Stock ticker for context
        texts: List of financial texts to analyze (max 20)
    """
    from engines.sentiment import analyze_sentiment as _analyze

    result = await _analyze(ticker, texts[:20])
    return result.model_dump_json()


@mcp_server.tool()
async def get_technical_signals(
    ticker: str,
    period: str = "6mo",
) -> str:
    """Get technical analysis signals: RSI, MACD, Bollinger Bands, Moving Averages.

    Args:
        ticker: Stock ticker symbol
        period: Time period: 1mo, 3mo, 6mo, 1y, 2y
    """
    from engines.technical import get_technical_signals as _get_signals

    result = await _get_signals(ticker, period)
    return result.model_dump_json()


@mcp_server.tool()
async def ingest_document(
    ticker: str,
    filing_type: str = "10-K",
    fiscal_year: int | None = None,
) -> str:
    """Ingest a SEC filing into the RAG knowledge base.

    Fetches from SEC EDGAR, parses, chunks, embeds, and stores in pgvector.

    Args:
        ticker: Stock ticker symbol
        filing_type: "10-K", "10-Q", or "8-K"
        fiscal_year: Specific year, or None for latest
    """
    import json as json_mod

    from db.models import FilingType
    from db.vector_store import get_session, store_chunks, store_document
    from ingestion.parser import clean_filing_text, parse_html_to_text
    from ingestion.sec_edgar import fetch_filing_content, search_filings
    from rag.chunker import chunk_text
    from rag.embedder import embed_texts

    # 1. Find filing on EDGAR
    ft = FilingType(filing_type)
    filings = await search_filings(ticker, ft, count=5)
    if not filings:
        return json_mod.dumps({"error": f"No {filing_type} filings found for {ticker}"})

    filing = filings[0]  # Latest filing

    # 2. Fetch and parse
    raw_content = await fetch_filing_content(filing["document_url"])
    text = clean_filing_text(parse_html_to_text(raw_content))

    if len(text) < 100:
        return json_mod.dumps({"error": "Filing content too short after parsing — may be an index page"})

    # 3. Chunk
    chunks = chunk_text(text)

    # 4. Embed (batch)
    embeddings = await embed_texts(chunks)

    # 5. Store
    async with get_session() as session:
        doc_id = await store_document(
            session,
            ticker=ticker.upper(),
            title=f"{ticker.upper()} {filing_type} {filing.get('filed_date', '')}",
            document_type="sec_filing",
            filing_type=filing_type,
            filed_date=filing.get("filed_date"),
            fiscal_year=fiscal_year,
            source_url=filing["document_url"],
        )
        chunk_records = [
            {
                "content": content,
                "chunk_index": i,
                "embedding": emb,
                "metadata": json_mod.dumps(
                    {"ticker": ticker.upper(), "document_type": "sec_filing", "filing_type": filing_type}
                ),
            }
            for i, (content, emb) in enumerate(zip(chunks, embeddings))
        ]
        count = await store_chunks(session, doc_id, chunk_records)

    return json_mod.dumps(
        {
            "status": "success",
            "document_id": doc_id,
            "ticker": ticker.upper(),
            "filing_type": filing_type,
            "chunks_stored": count,
            "source_url": filing["document_url"],
        }
    )


@mcp_server.tool()
async def query_knowledge_base(
    query: str,
    ticker: str | None = None,
    top_k: int = 5,
) -> str:
    """General-purpose RAG query across all ingested financial documents.

    Args:
        query: Natural language question
        ticker: Optional ticker filter
        top_k: Number of results (1-20, default 5)
    """
    from rag.generator import generate_answer
    from rag.reranker import rerank
    from rag.retriever import hybrid_retrieve

    chunks = await hybrid_retrieve(query, top_k=top_k * 2, ticker=ticker)
    reranked = rerank(query, chunks, top_k=top_k)
    result = await generate_answer(query, reranked)
    return result.model_dump_json()
