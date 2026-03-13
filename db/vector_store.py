"""PostgreSQL + pgvector operations for document storage and vector search."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings

engine = create_async_engine(settings.database_url, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_schema() -> None:
    """Create pgvector extension and tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                ticker VARCHAR(10) NOT NULL,
                title TEXT NOT NULL,
                document_type VARCHAR(50) NOT NULL,
                filing_type VARCHAR(10),
                filed_date TIMESTAMPTZ,
                fiscal_year INTEGER,
                fiscal_quarter INTEGER,
                source_url TEXT,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        )
        await conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding vector({settings.embedding_dimensions}),
                metadata JSONB DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """)
        )
        # HNSW index for fast approximate nearest neighbor search
        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding
            ON document_chunks
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)
        )
        # BM25 support: tsvector column + GIN index
        await conn.execute(
            text("""
            ALTER TABLE document_chunks
            ADD COLUMN IF NOT EXISTS tsv tsvector
            GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
        """)
        )
        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_tsv
            ON document_chunks USING gin(tsv)
        """)
        )
        # Index for filtering by ticker
        await conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_documents_ticker
            ON documents(ticker)
        """)
        )


async def store_document(
    session: AsyncSession,
    ticker: str,
    title: str,
    document_type: str,
    filing_type: str | None = None,
    filed_date: str | None = None,
    fiscal_year: int | None = None,
    fiscal_quarter: int | None = None,
    source_url: str | None = None,
) -> str:
    """Insert a document record and return its ID."""
    result = await session.execute(
        text("""
        INSERT INTO documents (ticker, title, document_type, filing_type, filed_date,
                               fiscal_year, fiscal_quarter, source_url)
        VALUES (:ticker, :title, :document_type, :filing_type, :filed_date,
                :fiscal_year, :fiscal_quarter, :source_url)
        RETURNING id
    """),
        {
            "ticker": ticker.upper(),
            "title": title,
            "document_type": document_type,
            "filing_type": filing_type,
            "filed_date": filed_date,
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fiscal_quarter,
            "source_url": source_url,
        },
    )
    row = result.fetchone()
    return str(row[0])


async def store_chunks(
    session: AsyncSession,
    document_id: str,
    chunks: list[dict],
) -> int:
    """Batch insert chunks with embeddings. Returns count inserted."""
    for chunk in chunks:
        await session.execute(
            text("""
            INSERT INTO document_chunks (document_id, content, chunk_index, embedding, metadata)
            VALUES (:document_id, :content, :chunk_index, :embedding::vector, :metadata::jsonb)
        """),
            {
                "document_id": document_id,
                "content": chunk["content"],
                "chunk_index": chunk["chunk_index"],
                "embedding": str(chunk["embedding"]),
                "metadata": chunk.get("metadata", "{}"),
            },
        )
    return len(chunks)


async def vector_search(
    session: AsyncSession,
    query_embedding: list[float],
    top_k: int = 5,
    ticker: str | None = None,
    filing_type: str | None = None,
) -> list[dict]:
    """Approximate nearest neighbor search using pgvector HNSW index."""
    filters = []
    params: dict = {"embedding": str(query_embedding), "top_k": top_k}

    if ticker:
        filters.append("d.ticker = :ticker")
        params["ticker"] = ticker.upper()
    if filing_type:
        filters.append("d.filing_type = :filing_type")
        params["filing_type"] = filing_type

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    result = await session.execute(
        text(f"""
        SELECT c.id, c.content, c.chunk_index, c.metadata,
               d.title, d.ticker, d.filing_type, d.fiscal_year,
               1 - (c.embedding <=> :embedding::vector) AS similarity
        FROM document_chunks c
        JOIN documents d ON c.document_id = d.id
        {where_clause}
        ORDER BY c.embedding <=> :embedding::vector
        LIMIT :top_k
    """),
        params,
    )
    return [dict(row._mapping) for row in result.fetchall()]


async def bm25_search(
    session: AsyncSession,
    query: str,
    top_k: int = 5,
    ticker: str | None = None,
    filing_type: str | None = None,
) -> list[dict]:
    """Full-text search using PostgreSQL tsvector + ts_rank."""
    filters = ["c.tsv @@ plainto_tsquery('english', :query)"]
    params: dict = {"query": query, "top_k": top_k}

    if ticker:
        filters.append("d.ticker = :ticker")
        params["ticker"] = ticker.upper()
    if filing_type:
        filters.append("d.filing_type = :filing_type")
        params["filing_type"] = filing_type

    where_clause = f"WHERE {' AND '.join(filters)}"

    result = await session.execute(
        text(f"""
        SELECT c.id, c.content, c.chunk_index, c.metadata,
               d.title, d.ticker, d.filing_type, d.fiscal_year,
               ts_rank(c.tsv, plainto_tsquery('english', :query)) AS bm25_score
        FROM document_chunks c
        JOIN documents d ON c.document_id = d.id
        {where_clause}
        ORDER BY bm25_score DESC
        LIMIT :top_k
    """),
        params,
    )
    return [dict(row._mapping) for row in result.fetchall()]
