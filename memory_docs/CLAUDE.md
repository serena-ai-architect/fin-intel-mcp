# CLAUDE.md — hk-regtech-mcp

## Project Identity

**hk-regtech-mcp**: HK RegTech MCP Server — compliance-as-infrastructure for Hong Kong financial regulation. 9 个可组合 MCP 工具（6 金融智能 + 3 HK 合规），任何 MCP 兼容 AI 系统即插即用。

**定位**：独立 Skill Layer，不绑定特定 orchestrator。上层 [agentic-analyst](../../agentic-analyst/) 是参考实现之一。

## Tech Stack

- **Language**: Python 3.12
- **Framework**: FastAPI + MCP SDK (mcp[cli] v1.6.0)
- **Database**: PostgreSQL + pgvector (Supabase)
- **RAG**: Hybrid retrieval (BM25 + vector + RRF fusion)
- **Embeddings**: OpenAI text-embedding-3-small (1536-dim)
- **LLM (RAG generation)**: DeepSeek-V3
- **Sentiment**: FinBERT (local, via transformers) / DeepSeek fallback
- **Technical Analysis**: yfinance + pandas-ta (RSI, MACD, Bollinger, MA)
- **Ingestion**: SEC EDGAR API + HTML parser
- **Observability**: Langfuse (all tool calls traced)
- **Streaming**: Server-Sent Events (SSE)
- **Testing**: pytest + pytest-asyncio
- **Linting**: Ruff (Python 3.12, line-length 100)

## MCP Tools (9 total)

| Tool | Category |
|------|----------|
| search_sec_filings | Financial (RAG) |
| search_earnings_calls | Financial (RAG) |
| analyze_sentiment | Financial (FinBERT) |
| get_technical_signals | Financial (yfinance) |
| ingest_document | Financial (SEC EDGAR) |
| query_knowledge_base | Financial (RAG) |
| check_hk_compliance | HK Compliance |
| search_hkex_filings | HK Compliance |
| assess_cross_border_risk | HK Compliance |

## Current Focus (as of 2026-03-24)

- HK compliance tools 已实现（structured rules database, 15 rules, 6 cross-border factors）
- **Next**: AWS 部署 (EC2 + Docker)
- **Next**: PyPI 发布 (`pip install hk-regtech-mcp`)
- **Next**: Claude Desktop MCP 配置教程
- **Future**: HKEX RSS feed 接入（真实数据替代 demo data）

## Session Protocol

1. **Session start**: Read `memory_docs/ARCHITECTURE.md`, `memory_docs/DECISIONS.md`, latest `memory_docs/CHANGELOG.md`
2. **During work**: For architectural decisions, document in `memory_docs/DECISIONS.md`
3. **Session end (MANDATORY)**: Update `memory_docs/CHANGELOG.md`

## Coding Preferences

- Type hints on all functions
- Pydantic models for all data structures
- Async-first (asyncpg, httpx, FastAPI)
- Google-style docstrings
- Error handling: raise descriptive exceptions, don't swallow errors silently
- Tests: pytest with `@pytest.mark.asyncio` for async functions
