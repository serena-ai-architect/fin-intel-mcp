# ARCHITECTURE.md — hk-regtech-mcp

> Last updated: 2026-03-24
> Update this file when the system architecture actually changes, not for every code commit.

## System Overview

```
MCP Client (any AI system)
  ↓ MCP Protocol (stdio or HTTP)
hk-regtech-mcp Server
  ├── Financial Intelligence (6 tools)
  │   ├── RAG Pipeline (BM25 + pgvector + RRF)
  │   ├── Sentiment Engine (FinBERT / DeepSeek)
  │   └── Technical Engine (yfinance + pandas-ta)
  └── HK Compliance (3 tools)
      └── Structured Rules Database (15 rules, 6 cross-border factors)
```

Also exposes REST API (FastAPI) for non-MCP consumers.

## MCP Tool Inventory (9 tools)

### Financial Intelligence Tools (6)

| Tool | Parameters | Description |
|------|-----------|-------------|
| **search_sec_filings** | ticker, query, filing_type?, top_k? | Hybrid RAG over SEC 10-K/10-Q/8-K filings |
| **search_earnings_calls** | ticker, query, top_k? | RAG search over earnings call transcripts |
| **analyze_sentiment** | ticker, texts[] | FinBERT (preferred) or DeepSeek LLM fallback |
| **get_technical_signals** | ticker, period? | RSI(14), MACD(12,26,9), Bollinger(20,2), MA(50/200) |
| **ingest_document** | ticker, filing_type?, fiscal_year? | SEC EDGAR → parse → chunk → embed → store |
| **query_knowledge_base** | query, ticker?, top_k? | General RAG Q&A across all ingested documents |

### HK Regulatory Compliance Tools (3)

| Tool | Parameters | Description |
|------|-----------|-------------|
| **check_hk_compliance** | ticker, activity_type, jurisdiction? | Matching HKMA/SFC/PDPO/HKEX rules with citations |
| **search_hkex_filings** | ticker, filing_type?, period? | HKEX announcements (demo data, future: ESS API) |
| **assess_cross_border_risk** | ticker, source_jurisdiction?, target_jurisdiction? | HK↔CN↔International risk factors, weighted score 0-10 |

## Hybrid RAG Pipeline

```
Document → Chunk → Embed → Store (pgvector)
                                    ↓
Query → Embed ──→ Vector Search (HNSW, cosine) ─┐
     └──────→ BM25 Search (tsvector, ts_rank) ──┤
                                                  ↓
                                        RRF Fusion (k=60)
                                                  ↓
                                        Rerank (CrossEncoder, optional)
                                                  ↓
                                        Generate (DeepSeek + citations)
```

### Components

| Component | File | Tech |
|-----------|------|------|
| Chunking | `rag/chunker.py` | LangChain RecursiveCharacterTextSplitter (500 chars, 50 overlap) |
| Embedding | `rag/embedder.py` | OpenAI text-embedding-3-small (1536-dim) |
| Retrieval | `rag/retriever.py` | Dual: pgvector HNSW + PostgreSQL tsvector, fused via RRF |
| Reranking | `rag/reranker.py` | cross-encoder/ms-marco-MiniLM-L-6-v2 (optional, graceful fallback) |
| Generation | `rag/generator.py` | DeepSeek-V3 with citation extraction |

## Analysis Engines

### Sentiment Engine (`engines/sentiment.py`)
- **Primary**: FinBERT (ProsusAI/finbert) — lazy-loaded, max 512 tokens/text
- **Fallback**: DeepSeek LLM (if transformers not installed)
- **Output**: SentimentAnalysis (per-text scores + overall sentiment + overall score)

### Technical Engine (`engines/technical.py`)
- **Data**: yfinance (1mo/3mo/6mo/1y/2y candles)
- **Indicators**: RSI(14), MACD(12,26,9), Bollinger Bands(20,2), SMA(50), SMA(200)
- **Signal logic**: Per-indicator thresholds → STRONG_BUY/BUY/NEUTRAL/SELL/STRONG_SELL → weighted majority vote
- **Output**: TechnicalAnalysis (price, indicators[], overall_signal)

### HK Regulatory Engine (`engines/hk_regulatory.py` + `engines/hk_rules_data.py`)
- **Rules database**: 15 structured rules across 4 regulators
  - HKMA (5): TM-G-1, GenAI Sandbox, Virtual Assets, Open Banking, Stablecoin
  - SFC (3): Virtual Asset Trading Platform, Type 9 Asset Management, AI in licensed activities
  - PDPO (3): Six Data Protection Principles, Cross-border transfer, AI/Big Data guidance
  - HKEX (4): Biotech Listing (Ch.18A), Secondary Listing (Ch.19C), ESG Reporting, Stock Connect
- **Cross-border factors**: 6 factors (data_localization, capital_flow, dual_listing, sanctions, VIE, regulatory_divergence)
- Each rule has: rule_id, title, summary, applies_to, citation, relevance keywords

## Database Schema (PostgreSQL + pgvector)

### `documents` table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| ticker | VARCHAR(10) | Company ticker |
| title | TEXT | Document title |
| document_type | VARCHAR(50) | SEC_FILING, EARNINGS_CALL, CUSTOM |
| filing_type | VARCHAR(10) | 10-K, 10-Q, 8-K |
| filed_date | TIMESTAMPTZ | Filing date |
| fiscal_year / fiscal_quarter | INTEGER | Fiscal period |
| source_url | TEXT | Original document URL |

### `document_chunks` table
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| document_id | UUID FK | Parent document |
| content | TEXT | Chunk text |
| chunk_index | INTEGER | Position in document |
| embedding | vector[1536] | pgvector column |
| metadata | JSONB | ticker, document_type, filing_type |
| tsv | tsvector (GENERATED) | BM25 full-text index |

### Indexes
- **HNSW** on embedding (m=16, ef_construction=64, cosine distance)
- **GIN** on tsv (full-text search)
- **B-tree** on documents.ticker

## Ingestion Pipeline

```
SEC EDGAR API → search_filings(ticker, filing_type) → fetch_filing_content(url)
    ↓
HTML Parser (unstructured or regex fallback) → clean_filing_text()
    ↓
RecursiveCharacterTextSplitter (500 chars, 50 overlap)
    ↓
OpenAI embed_texts() → pgvector store_chunks()
```

## REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/v1/query/rag | RAG Q&A (query, ticker?, top_k?) |
| POST | /api/v1/ingest/sec-filing | Ingest SEC filing |
| POST | /api/v1/analyze/sentiment | Sentiment analysis |
| POST | /api/v1/analyze/technical | Technical signals |
| GET | /api/v1/signals/stream | SSE streaming (technical + sentiment) |

## Run Modes

- **FastAPI**: `uvicorn main:app --reload` (REST + SSE)
- **MCP Server**: `python main.py mcp` (stdio transport for Claude Desktop / MCP clients)

## Directory Structure

```
hk-regtech-mcp/
├── main.py                     # FastAPI + MCP entry point (dual mode)
├── config.py                   # Pydantic settings (env-based)
├── pyproject.toml              # Dependencies, Python 3.12
├── mcp_server/
│   └── server.py               # 9 MCP tool definitions
├── rag/
│   ├── chunker.py              # Text chunking
│   ├── embedder.py             # OpenAI embeddings
│   ├── retriever.py            # Hybrid BM25 + vector + RRF
│   ├── reranker.py             # CrossEncoder reranking (optional)
│   └── generator.py            # DeepSeek RAG with citations
├── engines/
│   ├── sentiment.py            # FinBERT + DeepSeek fallback
│   ├── technical.py            # yfinance + pandas-ta indicators
│   ├── hk_regulatory.py        # 3 HK compliance tool implementations
│   └── hk_rules_data.py        # Structured rules database (15 rules)
├── ingestion/
│   ├── sec_edgar.py            # SEC EDGAR API client
│   └── parser.py               # HTML → clean text
├── db/
│   ├── models.py               # 13 Pydantic models (4 enums)
│   └── vector_store.py         # pgvector operations
├── streaming/
│   └── sse.py                  # Server-Sent Events
├── observability/
│   └── langfuse_setup.py       # Langfuse trace decorator
├── tests/
│   ├── test_rag_pipeline.py    # RAG: chunker, reranker, RRF fusion (10 tests)
│   ├── test_technical.py       # Technical signals (4 tests)
│   └── test_ingestion.py       # SEC EDGAR + parser (6 tests)
└── memory_docs/                # Project memory (this file system)
```

## Pydantic Data Models (13)

- **Document**: DocumentMetadata, DocumentChunk, Document, Citation
- **RAG**: RAGResult
- **Sentiment**: SentimentResult, SentimentAnalysis
- **Technical**: TechnicalIndicator, TechnicalAnalysis
- **HK Compliance**: ComplianceRule, ComplianceCheckResult, HKEXFiling, HKEXFilingResult, CrossBorderRiskFactor, CrossBorderRiskResult

## Observability

All tool calls traced via Langfuse `@trace_tool()` decorator:
- Execution time (duration_ms)
- Input/output as span data
- Error status tracking
- Lazy initialization (graceful if credentials not configured)
