# DECISIONS.md — Architecture Decision Records

> 按时间倒序排列，最新决策在最上面。
> 每条记录回答一个核心问题：为什么选 A 而不选 B？

---

### ADR-006: Optional ML dependencies via [ml] extra

**Date**: 2026-03
**Status**: Accepted

**Context**
FinBERT 和 CrossEncoder reranker 依赖 transformers + torch（~2GB），在轻量部署场景（Docker, CI）不需要。

**Decision**
将 transformers, torch, sentence-transformers 放入 `[ml]` optional extra。安装 `pip install hk-regtech-mcp` 只装核心依赖，`pip install hk-regtech-mcp[ml]` 才装 ML 模型。

**Alternatives Considered**
- 全部作为必需依赖: 简单但安装重 → Rejected：Docker image 从 ~200MB 膨胀到 ~2.5GB
- 完全移除本地 ML，全用 LLM API: 无本地依赖 → Rejected：FinBERT 情绪分析质量高于 LLM prompt，且离线可用

**Consequences**
- Sentiment engine 自动 fallback：FinBERT 不可用 → DeepSeek LLM
- Reranker 自动 fallback：CrossEncoder 不可用 → RRF scores
- `pyproject.toml` 的 `[project.optional-dependencies]` 管理

---

### ADR-005: FastAPI dual-mode (REST + MCP stdio)

**Date**: 2026-03
**Status**: Accepted

**Context**
需要同时支持：(1) Claude Desktop / MCP 客户端通过 stdio 调用；(2) Web 应用通过 HTTP API 调用。

**Decision**
`main.py` 根据命令行参数切换：`python main.py mcp` 启动 MCP stdio server，否则启动 FastAPI HTTP server。两者共享相同的 engine 和 db 层。

**Alternatives Considered**
- 分离为两个独立服务: 解耦但重复代码 → Rejected：engine/db/config 完全相同，分离后维护成本翻倍
- 只做 MCP，不做 REST: MCP 专注 → Rejected：上层 agentic-analyst 的 Next.js 前端需要 HTTP 端点做 SSE streaming

**Consequences**
- 单一 codebase 服务两种协议
- MCP server 使用 stdio transport（Claude Desktop 原生支持）
- REST server 暴露 5 个端点 + SSE streaming

---

### ADR-004: Structured HK rules database over LLM-generated compliance

**Date**: 2026-03
**Status**: Accepted

**Context**
HK 合规检查核心问题：规则是让 LLM 临时生成，还是预编码为结构化数据？

**Decision**
在 `hk_rules_data.py` 中编码 15 条结构化规则（4 个监管机构 + 6 个跨境风险因子），每条附法规编号和引用来源。Compliance tools 查询这个数据库，不依赖 LLM 生成规则。

**Alternatives Considered**
- LLM 动态生成合规规则: 灵活 → Rejected：不可审计，输出不稳定，面试官会问"数据从哪来"
- 外部 RegTech API (Compliance.ai, Ascent): 专业 → Rejected：没有 HK 市场覆盖，且价格昂贵

**Consequences**
- 可审计：每条规则有 rule_id, citation, applies_to
- 可测试：规则是 pure data，不需要 LLM 就能验证
- 需要手动维护规则更新（未来可接入 HKMA RSS feed 自动更新）
- 面试叙事："rules-as-data, compliance-as-skills"

---

### ADR-003: FinBERT with DeepSeek fallback for sentiment

**Date**: 2026-02
**Status**: Accepted

**Context**
金融情绪分析需要准确的 positive/negative/neutral 分类。选项：通用 LLM prompt vs 专业金融模型。

**Decision**
优先使用 FinBERT (ProsusAI/finbert)，transformers 不可用时 fallback 到 DeepSeek LLM prompt。

**Alternatives Considered**
- 纯 LLM prompt: 简单但准确度低 → Rejected：通用 LLM 对金融语言的情绪判断不如 FinBERT
- VADER: 轻量但非金融特化 → Rejected：不区分"revenue declined"（negative）vs"risk declined"（positive）

**Consequences**
- FinBERT 需要 transformers + torch（放入 [ml] optional extra）
- Lazy loading：首次调用时才加载模型
- 每条文本 max 512 tokens（FinBERT 限制）

---

### ADR-002: Hybrid BM25 + vector over pure vector search

**Date**: 2026-02
**Status**: Accepted

**Context**
RAG 检索质量直接影响 SEC filing Q&A 和 earnings call 分析的准确度。Pure vector search 对精确术语（ticker, 法规编号）召回差。

**Decision**
Hybrid retrieval：pgvector HNSW（语义相似度）+ PostgreSQL tsvector（BM25 精确匹配），通过 Reciprocal Rank Fusion (k=60) 合并。

**Alternatives Considered**
- Pure vector search: 简单 → Rejected：对 "NVDA 10-K FY2024" 这类精确查询，纯语义搜索不如 BM25
- Elasticsearch: 成熟但重 → Rejected：增加一个独立服务，PostgreSQL 的 tsvector 已够用
- Cohere Rerank API: 好但贵 → Rejected：改用本地 CrossEncoder（ms-marco-MiniLM），可选

**Consequences**
- 两种搜索并行执行，RRF fusion 合并结果
- 需要 PostgreSQL tsvector GIN index + pgvector HNSW index
- 检索质量显著好于纯 vector（especially for financial terms）

---

### ADR-001: PostgreSQL + pgvector over ChromaDB / Pinecone

**Date**: 2026-01
**Status**: Accepted

**Context**
需要向量数据库存储 SEC filing embeddings。选项：托管服务 vs 嵌入式 vs 与关系型 DB 集成。

**Decision**
使用 PostgreSQL + pgvector extension，部署在 Supabase（与 agentic-analyst 共享同一实例）。

**Alternatives Considered**
- ChromaDB: 嵌入式，简单 → Rejected：不支持 BM25 full-text search（需要 hybrid retrieval）
- Pinecone: 托管，高性能 → Rejected：增加外部依赖和成本，Supabase 已经在用
- Weaviate: Hybrid search 原生支持 → Rejected：需要额外服务，PostgreSQL + tsvector 已经实现了 BM25

**Consequences**
- 单一数据库：pgvector (HNSW) + tsvector (BM25) + 关系数据，all in PostgreSQL
- 与 agentic-analyst 共享 Supabase 实例，零额外成本
- HNSW index 参数 (m=16, ef_construction=64) 适合中小规模数据

---

<!-- Add new ADRs above this line -->
