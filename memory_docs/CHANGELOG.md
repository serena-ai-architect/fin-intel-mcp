# CHANGELOG.md

> 按时间倒序排列，最新变更在最上面。
> 每个 Claude Code session 结束前必须更新此文件。
> 超过 500 行时，将旧内容移至 docs/changelog-archive/YYYY-MM.md

---

### 2026-03-20 Session via Claude Code

**Summary**: 项目重命名 fin-intel-mcp → hk-regtech-mcp，突出 HK 合规定位

**Changes**:
- 项目名改为 `hk-regtech-mcp`，pyproject.toml 更新 (`pyproject.toml`)
- 所有文档引用更新 (`README.md`, `README_CN.md`)

**Why**: 与 agentic-analyst 一起重命名，强调 compliance-as-infrastructure 差异化

**Next TODO**:
- [ ] AWS 部署 (EC2 + Docker)
- [ ] PyPI 发布
- [ ] Claude Desktop MCP 配置教程

**Decisions Made**: 无

---

### 2026-03-18 Session via Claude Code

**Summary**: HK 合规工具实现 — compliance-as-infrastructure pattern

**Changes**:
- 3 个 HK compliance tools: check_hk_compliance, search_hkex_filings, assess_cross_border_risk (`engines/hk_regulatory.py`)
- 结构化规则数据库: 15 rules (HKMA/SFC/PDPO/HKEX) + 6 cross-border factors (`engines/hk_rules_data.py`)
- MCP server 注册 3 个新工具 (`mcp_server/server.py`)
- 6 个新 Pydantic models: ComplianceRule, ComplianceCheckResult, HKEXFiling, HKEXFilingResult, CrossBorderRiskFactor, CrossBorderRiskResult (`db/models.py`)

**Why**: 面试差异化核心 — 将 HK 监管规则编码为可组合工具

**Decisions Made**: ADR-004 (structured rules over LLM-generated compliance)

---

### 2026-03-10 Session via Claude Code

**Summary**: 测试 + SEC EDGAR 修复 + parser 改进 + README

**Changes**:
- 3 个测试文件: test_rag_pipeline.py (10 tests), test_technical.py (4 tests), test_ingestion.py (6 tests) (`tests/`)
- SEC EDGAR client 修复: CIK 解析、filing URL 构建 (`ingestion/sec_edgar.py`)
- HTML parser 改进: XBRL 清理、SEC boilerplate 移除 (`ingestion/parser.py`)
- README 完整文档 (`README.md`, `README_CN.md`)

**Why**: 测试覆盖 + 文档完善

---

### 2026-02 Initial Build

**Summary**: 项目初始架构 — Python/FastAPI MCP Server for financial intelligence

**Changes**:
- FastAPI + MCP dual-mode 入口 (`main.py`)
- Hybrid RAG pipeline: chunker, embedder, retriever (BM25+vector+RRF), reranker, generator (`rag/`)
- 6 个 MCP 工具定义 (`mcp_server/server.py`)
- Sentiment engine: FinBERT + DeepSeek fallback (`engines/sentiment.py`)
- Technical engine: yfinance + pandas-ta (`engines/technical.py`)
- SEC EDGAR ingestion pipeline (`ingestion/`)
- PostgreSQL + pgvector schema (`db/vector_store.py`)
- 13 Pydantic models (`db/models.py`)
- Langfuse observability (`observability/langfuse_setup.py`)
- SSE streaming (`streaming/sse.py`)
- Pydantic settings (`config.py`)

**Decisions Made**: ADR-001 through ADR-003, ADR-005, ADR-006

---

### 2026-03-24 Current TODO

- [ ] AWS 部署 (EC2 + Docker Compose)
- [ ] PyPI 发布 (`pip install hk-regtech-mcp`)
- [ ] Claude Desktop MCP 配置教程（README 加一段）
- [ ] HKEX ESS API 接入（替代 demo data）
- [ ] HKMA RSS feed 自动更新规则
- [ ] 更多测试覆盖（HK compliance tools unit tests）

---

<!-- Add new entries above this line -->
