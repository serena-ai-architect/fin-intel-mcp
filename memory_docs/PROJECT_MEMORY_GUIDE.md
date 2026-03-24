# hk-regtech-mcp — 项目记忆文件体系

## 设计原则

每个新的 Claude Code session 启动时，只需读取这几个文件就能完全接上上下文。
文件按 **更新频率** 分层，避免高频小改动污染低频战略文档。

---

## 文件清单（共 4 个）

```
hk-regtech-mcp/memory_docs/
├── CLAUDE.md              ← Claude Code 会话入口
├── ARCHITECTURE.md        ← 当前架构全景（低频更新，架构变了才动）
├── DECISIONS.md           ← 架构决策记录 ADR（中频更新，选 A 不选 B 的理由）
└── CHANGELOG.md           ← 变更日志 + 下一步 TODO（高频更新，session 接力棒）
```

---

## 1. CLAUDE.md — Claude Code 会话入口（最重要）

**作用**：提供项目定位、技术栈、当前重点的快照。

**内容包含**：
- 项目一句话定位（HK RegTech MCP Server — compliance-as-infrastructure）
- 技术栈摘要（Python 3.12, FastAPI, MCP SDK, 9 tools, Hybrid RAG）
- 当前开发阶段和重点
- 编码规范和偏好

**更新时机**：每当开发阶段/重点发生变化时更新。

---

## 2. ARCHITECTURE.md — 架构全景

**作用**：描述系统"现在长什么样"。

**内容包含**：
- 9 个 MCP tool 清单（6 financial + 3 HK compliance）
- Hybrid RAG pipeline（BM25 + pgvector + RRF fusion）
- 分析引擎（sentiment, technical, HK regulatory）
- 数据库 schema（PostgreSQL + pgvector）
- 目录结构

**更新时机**：架构实际发生变化后更新。

---

## 3. DECISIONS.md — 架构决策记录 (ADR)

**作用**：记录"为什么选 A 不选 B"。**防止下一个 session 重新讨论已否决方案。**

**更新时机**：每次做出技术方案选择时追加。

---

## 4. CHANGELOG.md — 变更日志

**作用**：记录每次 session 的变更 + TODO 接力棒。

**更新时机**：每个 Claude Code session 结束前。

---

## 使用工作流

### Session 开始时

```
> 请先读取 memory_docs/CLAUDE.md, memory_docs/ARCHITECTURE.md, memory_docs/DECISIONS.md, memory_docs/CHANGELOG.md
```

### Session 结束前

```
> 请将本次 session 的变更更新到 memory_docs/CHANGELOG.md，
> 如果有架构决策请更新 memory_docs/DECISIONS.md，
> 如果架构发生了变化请更新 memory_docs/ARCHITECTURE.md
```

---

## 注意事项

- CHANGELOG.md 超过 500 行时归档
- DECISIONS.md 中的"替代方案"字段是最有价值的部分
- 中英文混合均可
