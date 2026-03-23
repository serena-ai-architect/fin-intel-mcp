# hk-regtech-mcp — Skill Infrastructure Layer

HK RegTech MCP Server — the composable skill layer for AI agent systems. Encapsulates **Hong Kong regulatory compliance** (HKMA, SFC, PDPO, HKEX), financial data analysis (SEC filing RAG, sentiment analysis, technical indicators) as MCP tools that any agent can consume.

> **Compliance-as-Infrastructure**: Regulatory rules (HKMA, SFC, PDPO, HKEX) are encoded as data and exposed as pluggable skills — not hardcoded into agent prompts. This pattern means compliance scales across any MCP-compatible agent system, addressing the industry shift from scattered agents to composable skill registries.

## Architecture

```
┌──────────────────────────────────────────────┐
│  hk-regtech-mcp (Python 3.12 / FastAPI)       │
│                                              │
│  MCP Tools:                                  │
│  ├── search_sec_filings    (RAG 10-K/10-Q)  │
│  ├── search_earnings_calls (RAG transcripts) │
│  ├── analyze_sentiment     (FinBERT/LLM)    │
│  ├── get_technical_signals (RSI/MACD/BB/MA) │
│  ├── ingest_document       (SEC → pgvector) │
│  └── query_knowledge_base  (general RAG)    │
│                                              │
│  RAG Pipeline:                               │
│  chunk → embed → BM25+vector → RRF → rerank │
│         → DeepSeek generate w/ citations     │
│                                              │
│  REST endpoints (debug):                     │
│  POST /api/v1/query/rag                      │
│  POST /api/v1/ingest/sec-filing              │
│  POST /api/v1/analyze/sentiment              │
│  POST /api/v1/analyze/technical              │
│  GET  /api/v1/signals/stream (SSE)           │
└──────────────┬───────────────────────────────┘
               │ MCP Protocol + REST
               ▼
     Agentic Analyst (first consumer)
     or any MCP-compatible agent
```

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/serenahappyhacking/hk-regtech-mcp.git
cd hk-regtech-mcp

# 2. Create virtual environment (requires Python 3.12+)
uv venv --python python3.12
source .venv/bin/activate

# 3. Install dependencies
uv pip install -e ".[dev]"

# 4. Optional: install ML models (FinBERT + cross-encoder reranker)
uv pip install -e ".[ml]"

# 5. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 6. Run FastAPI server
uvicorn main:app --reload

# 7. Or run as MCP Server (stdio)
python main.py mcp
```

## MCP Tools

| Tool | Description | Input |
|------|-------------|-------|
| `search_sec_filings` | Hybrid RAG search over SEC 10-K/10-Q/8-K filings | `ticker`, `query`, `filing_type?`, `top_k?` |
| `search_earnings_calls` | RAG search over earnings call transcripts | `ticker`, `query`, `top_k?` |
| `analyze_sentiment` | Financial sentiment analysis (FinBERT or DeepSeek fallback) | `ticker`, `texts[]` |
| `get_technical_signals` | RSI, MACD, Bollinger Bands, Moving Averages | `ticker`, `period?` |
| `ingest_document` | Fetch SEC filing → parse → chunk → embed → store in pgvector | `ticker`, `filing_type?`, `fiscal_year?` |
| `query_knowledge_base` | General RAG Q&A across all ingested documents | `query`, `ticker?`, `top_k?` |

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| API | FastAPI (Python 3.12) | Pydantic validation, async, auto-docs |
| MCP | mcp Python SDK | Standard MCP protocol |
| LLM | DeepSeek-V3 | Cost-effective, consistent with Analyst |
| Embedding | OpenAI text-embedding-3-small | $0.02/M tokens |
| Vector Store | pgvector (Supabase) | Shared with Analyst |
| Retrieval | BM25 + vector + RRF fusion | Hybrid for precision + recall |
| Reranker | cross-encoder/ms-marco-MiniLM | Optional, improves RAG accuracy |
| Sentiment | FinBERT (local) / DeepSeek (fallback) | Domain-specific financial NLP |
| Technical | yfinance + pandas-ta | Live market data + indicators |
| Observability | Langfuse | Trace every tool call |
| SEC Data | SEC EDGAR API | Official 10-K/10-Q/8-K source |

## Project Structure

```
hk-regtech-mcp/
├── main.py                      # FastAPI + MCP entry point
├── config.py                    # Pydantic Settings
├── db/
│   ├── models.py                # Pydantic models (13 models)
│   └── vector_store.py          # pgvector operations + schema
├── rag/
│   ├── chunker.py               # RecursiveCharacterTextSplitter
│   ├── embedder.py              # OpenAI embeddings
│   ├── retriever.py             # Hybrid BM25 + vector + RRF
│   ├── reranker.py              # Cross-encoder (optional)
│   └── generator.py             # DeepSeek RAG with citations
├── engines/
│   ├── sentiment.py             # FinBERT + LLM fallback
│   └── technical.py             # yfinance + pandas-ta
├── ingestion/
│   ├── sec_edgar.py             # SEC EDGAR submissions API
│   └── parser.py                # HTML → clean text (XBRL-aware)
├── mcp_server/
│   └── server.py                # MCP Server + 6 tool definitions
├── streaming/
│   └── sse.py                   # SSE event streaming
├── observability/
│   └── langfuse_setup.py        # Trace decorator
└── tests/                       # 19 tests (all passing)
```

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# By module
python -m pytest tests/test_technical.py -v      # Live market data
python -m pytest tests/test_rag_pipeline.py -v    # RAG components
python -m pytest tests/test_ingestion.py -v       # SEC EDGAR + parser
```

## Compliance-as-Infrastructure (HK Regulatory)

Three MCP tools demonstrate the compliance-as-infrastructure pattern for Hong Kong financial markets:

| Tool | Description | Regulators |
|------|-------------|------------|
| `check_hk_compliance` | Applicable regulatory requirements for a company/activity in HK | HKMA, SFC, PDPO, HKEX |
| `search_hkex_filings` | HKEX announcements and disclosure filings | HKEX |
| `assess_cross_border_risk` | Cross-border regulatory risk (HK↔Mainland↔International) | PIPL, PDPO, Stock Connect |

Rules are structured data in `engines/hk_rules_data.py`, not agent prompts — making them auditable, version-controlled, and consumable by any MCP-compatible system.

## Part of a Skill-Composition Ecosystem

This is the Skill Infrastructure Layer in a three-product AI portfolio:

1. **[AdWing](https://github.com/serenahappyhacking/AdWing.ai)** — D2C ad copy generation (TypeScript/LangGraph.js/Claude)
2. **[Agentic Analyst](https://github.com/serenahappyhacking/agentic-analyst)** — Skill-composition investment intelligence (TypeScript/LangGraph.js/DeepSeek)
3. **hk-regtech-mcp** — Skill Infrastructure Layer (Python/FastAPI/MCP) ← *this repo*

The narrative: *"I build composable agent infrastructure — not isolated projects, but an ecosystem where financial intelligence and compliance rules are pluggable skills that any agent can consume via MCP."*
