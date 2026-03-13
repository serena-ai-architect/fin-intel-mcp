"""fin-intel-mcp — FastAPI app + MCP Server entry point.

Run with: uvicorn main:app --reload
MCP mode: python main.py mcp
"""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database schema and observability on startup."""
    from db.vector_store import init_schema
    from observability.langfuse_setup import get_langfuse

    await init_schema()
    get_langfuse()  # Warm up Langfuse client
    print(f"✓ {settings.app_name} started — pgvector schema ready")
    yield
    print(f"✓ {settings.app_name} shutting down")


app = FastAPI(
    title="fin-intel-mcp",
    description="Financial Intelligence MCP Server — RAG over SEC filings, sentiment analysis, and technical indicators",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST API Routes ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/v1/query/rag")
async def query_rag(query: str, ticker: str | None = None, top_k: int = 5):
    """General RAG query endpoint."""
    from rag.generator import generate_answer
    from rag.reranker import rerank
    from rag.retriever import hybrid_retrieve

    chunks = await hybrid_retrieve(query, top_k=top_k * 2, ticker=ticker)
    reranked = rerank(query, chunks, top_k=top_k)
    result = await generate_answer(query, reranked)
    return result.model_dump()


@app.post("/api/v1/ingest/sec-filing")
async def ingest_sec_filing(ticker: str, filing_type: str = "10-K", fiscal_year: int | None = None):
    """Ingest a SEC filing into the knowledge base."""
    import json

    from mcp_server.server import ingest_document

    result = await ingest_document(ticker, filing_type, fiscal_year)
    return json.loads(result)


@app.post("/api/v1/analyze/sentiment")
async def analyze_sentiment_endpoint(ticker: str, texts: list[str]):
    """Analyze sentiment of financial texts."""
    from engines.sentiment import analyze_sentiment

    result = await analyze_sentiment(ticker, texts)
    return result.model_dump()


@app.post("/api/v1/analyze/technical")
async def analyze_technical(ticker: str, period: str = "6mo"):
    """Get technical analysis signals."""
    from engines.technical import get_technical_signals

    result = await get_technical_signals(ticker, period)
    return result.model_dump()


@app.get("/api/v1/signals/stream")
async def signals_stream(ticker: str):
    """SSE endpoint for streaming analysis results."""
    from sse_starlette.sse import EventSourceResponse

    from streaming.sse import analysis_stream

    return EventSourceResponse(analysis_stream(ticker))


# ── MCP Mode ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        # Run as MCP Server (stdio transport)
        from mcp_server.server import mcp_server

        mcp_server.run()
    else:
        import uvicorn

        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
