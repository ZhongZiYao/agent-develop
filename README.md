# FinGuide AI · 银行理财 RAG 问答系统

> 基于 LangChain + LangGraph 的银行理财产品智能问答系统，覆盖 22 家银行 2 万+ 公告 PDF 的真实金融场景。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-28_passed-brightgreen.svg)](tests/)
[![POC](https://img.shields.io/badge/POC-100_PDF-success.svg)](docs/phase8-5-端到端验证.md)

---

## 🎯 项目亮点

| 维度 | 能力 |
|------|------|
| **真实场景** | 22 家银行 23,229 份理财 PDF（产品说明书 / 业绩基准调整 / 定期报告 / 费率公告）|
| **RAG 全链路** | PDF ETL → 表格感知切分 → Hybrid 召回（向量 + BM25 + Rerank）→ LLM 生成 |
| **多 Agent 协作** | LangGraph Router / ReAct / Reflexion / Self-RAG 闸门 / Supervisor 多 Agent |
| **可观测** | SSE 实时 Trace 推送 + 前端 AgentSteps 时间线 + DuckDB 数仓审计 |
| **合规** | Prompt 100% 必带风险提示，专有名词原文保留，业绩基准附带生效日期 |
| **PDF 工程** | PyMuPDF 双引擎 + 双命名 regex + 目录 fallback + DuckDB 三表存储 |

---

## 🛠 技术栈

| 层级 | 选型 |
|------|------|
| **LLM** | Ollama 本地 qwen3:8b / 国产云端 MiniMax（reasoning=True） |
| **Embedding** | Ollama 本地 bge-m3（1024 维） |
| **Reranker** | bge-reranker-large |
| **向量库** | Chroma（PersistentClient） |
| **数仓** | DuckDB（dwd.documents / dwd.chunks / dwd.embeddings 三表） |
| **BM25** | rank_bm25 |
| **PDF 解析** | PyMuPDF（fitz）+ 表格感知切分 |
| **框架** | LangChain + LangGraph（StateGraph 多 Agent） |
| **后端** | FastAPI + SSE 流式 |
| **前端** | Next.js 14 (App Router) + TypeScript + Tailwind（indigo 配色） |
| **评测** | RAGAS |
| **追踪** | LangSmith + SSE Trace |

---

## 🏗 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                   用户 → Next.js 14 (Tailwind)                 │
│                  ┌─────────────────────────────┐               │
│                  │   MetadataBadge 五色标签      │  ← 机构/类型/日期/编号/产品
│                  │   AgentSteps 时间线           │  ← Self-RAG / Router / ReAct
│                  └─────────────────────────────┘               │
└─────────────────────────────┬───────────────────────────────────┘
                              │ SSE 流式
┌─────────────────────────────▼───────────────────────────────────┐
│                FastAPI + LangGraph StateGraph                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Router  │─▶│ ReAct    │─▶│ Reflexion│─▶│ Generate │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│        │             │             │             │              │
│        ▼             ▼             ▼             ▼              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Self-RAG  │  │ Hybrid   │  │ Rerank   │  │ qwen3:8b │        │
│  │ 闸门     │  │ 召回     │  │ 重排     │  │ 生成     │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                   PDF ETL 流水线（金融域特化）                   │
│                                                                  │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐             │
│  │  PyMuPDF   │──▶│ 表格感知    │──▶│ Embedding  │             │
│  │  双引擎    │    │ 切分器     │    │ 16 并发     │             │
│  └────────────┘    └────────────┘    └────────────┘             │
│         │                  │                │                    │
│         ▼                  ▼                ▼                    │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐             │
│  │ DuckDB     │    │ Chroma     │    │ BM25       │             │
│  │ dwd 3表    │    │ 向量索引   │    │ 关键词索引 │             │
│  └────────────┘    └────────────┘    └────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### RAG 演进路径

```
Naive RAG (Phase 1)
   └─▶ Advanced RAG + Hybrid + Rerank + RAGAS (Phase 2)
       └─▶ Modular 抽象 + 配置化 (Phase 3)
           └─▶ Agentic RAG + Router + ReAct + Reflexion (Phase 4)
               └─▶ Multi-Agent + Memory + 工具扩展 + 并行 (Phase 5)
                   └─▶ Self-RAG + SSE Trace + AgentSteps 可视化 (Phase 6)
                       └─▶ ETL 流水线（金融域 PDF） (Phase 8) ⭐
```

---

## 📁 目录结构

```
finguide-ai/
├── docs/                       # 项目文档（PRD / 架构 / Phase 报告）
├── data/
│   ├── 理财文件/                 # 23,229 PDF（22 家银行）
│   ├── clean/                   # ETL 中间产物（gitignore）
│   ├── chroma/                  # 向量库（gitignore）
│   └── warehouse/               # DuckDB（gitignore）
├── src/
│   ├── loaders/                 # pdf_loader 双引擎（PyMuPDF + 双 regex + 目录 fallback）
│   ├── splitters/               # pdf_table_splitter（页面 + 段落 + 长段分句）
│   ├── embeddings/              # Ollama bge-m3
│   ├── vectorstore/             # Chroma 封装
│   ├── retrievers/              # 向量 + BM25 + Hybrid (RRF)
│   ├── rerankers/               # bge-reranker-large
│   ├── prompts/                 # 金融 Prompt（强制风险提示）
│   ├── agents/                  # LangGraph Agent（Self-RAG / ReAct / Reflexion）
│   ├── graphs/                  # StateGraph 多 Agent
│   ├── etl/                     # transform_pdf / load_duckdb_financial / load_chroma
│   ├── api/                     # FastAPI（含 graph_routes SSE）
│   └── storage/                 # SQLite Session / Memory
├── scripts/
│   ├── etl_financial_poc.py     # 100 PDF POC 一键跑通
│   ├── etl_financial_full.py    # 全量 ETL（分批 + 增量 + 并发）
│   ├── scan_pdfs.py             # PDF 扫描 + POC 选取
│   └── cli_query.py             # CLI 问答
├── tests/                       # pytest 单测（28+ passed）
│   ├── unit/                    # test_pdf_loader / test_pdf_splitter / test_pdf_etl
│   └── integration/             # 端到端集成测试
├── web/                         # Next.js 14 前端
│   └── src/components/
│       ├── MetadataBadge.tsx    # 5 类金融元数据标签
│       ├── AgentSteps.tsx       # SSE Trace 时间线
│       └── Markdown.tsx         # GFM Markdown 渲染
├── eval/                        # RAGAS 评测脚本
├── configs/                     # YAML 配置
├── docker-compose.yml
└── CLAUDE.md                    # Claude Code 项目记忆
```

---

## 🚀 快速开始

### 方式 1：Docker Compose（推荐）

```bash
# 1. 准备 Ollama 模型
ollama pull bge-m3          # Embedding
ollama pull qwen3:8b        # 生成

# 2. 启动
docker compose up -d --build

# 3. 构建索引（首次）
docker exec -it finguide-api python scripts/etl_financial_poc.py

# 4. 访问
# Web UI: http://localhost:3000
# API:    http://localhost:8000/docs
```

### 方式 2：本地开发

```bash
# 1. 安装
pip install -r requirements.txt
cd web && npm install && cd ..

# 2. 配置
cp .env.example .env
# 编辑 .env 配置 Ollama / 国产云端 LLM / PDF_DATA_DIR

# 3. ETL 一键跑通
python scripts/etl_financial_poc.py     # 100 PDF POC
# 或全量
python -m scripts.etl_financial_full --workers 32

# 4. 启动
uvicorn src.api.main:app --reload --port 8000  # 后端
cd web && npm run dev                          # 前端
```

---

## 💡 使用示例

### Web 界面（indigo 配色 + Metadata Badge）

```
Q: 招银理财 24GS5969 当前业绩基准是多少？

A: ## 业绩基准
| 项目 | 数值 |
|------|------|
| 业绩比较基准 | 2.30% - 3.50% |
| 生效日期 | 2026-08-20 |
| 来源 | 工银理财业绩比较基准调整公告 |

> 理财非存款，产品过往业绩不预示未来表现。投资有风险，决策需谨慎。

[参考资料]
[1] 标题：工银理财·鑫悦最短持有30天...     [Badge: 🏛 A01工银理财 · 📄 业绩比较基准调整 · 📅 2026-08-20 · #️⃣ 24GS5969]
```

### CLI 问答

```bash
python scripts/cli_query.py "招银理财 24GS5969 的业绩基准是多少？"
python scripts/cli_query.py "工银理财最新产品说明书" --stream
```

### API（SSE 流式 + Trace 推送）

```bash
curl -N -X POST http://localhost:8000/api/v1/chat-graph/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "中银理财业绩比较基准调整公告", "top_k": 10, "top_n": 5}'

# 响应（SSE）：
# event: agent_trace     → {node: "router", status: "started"}
# event: agent_trace     → {node: "self_rag_judge", status: "completed", payload: {need_retrieval: true}}
# event: retrieval       → {docs: [...]}
# event: agent_step      → {iteration: 1, thought_preview: "...", action: {tool: "rag_search"}}
# event: agent_reflect   → {score: 4.2, need_replan: false}
# event: generation      → token-by-token 流式回答
# event: done            → {total_steps: 5, trace_events: [...]}
```

---

## 🧪 测试

```bash
# 单元测试（28+ 测试，PDF Loader / Splitter / ETL 全覆盖）
pytest tests/unit/ -v

# 集成测试（需要 Ollama + Chroma 运行）
INTEGRATION_TESTS=1 pytest tests/integration/ -v
```

测试覆盖：
- ✅ PDF Loader 双 regex + 目录 fallback + 真实 PDF 加载
- ✅ 表格感知切分器（页面 / 段落 / 长段分句）
- ✅ ETL 幂等 DELETE+INSERT
- ✅ DuckDB schema 完整性
- ✅ Chroma 写入 + metadata 字段

---

## 📊 量化成果（Phase 8 POC）

| 指标 | 数值 |
|------|------|
| 真实 PDF 数据 | 23,229 份 / 8.1 GB / 22 家银行 |
| POC 端到端 | 100 PDF → 48 docs / 662 chunks / 662 vectors < 5min |
| Chunk 平均大小 | 500 字符（chunk_size=500, overlap=50） |
| Embedding 吞吐 | 16-32 并发，bge-m3 1024 维 |
| 召回策略 | 向量 + BM25 + Rerank 三路混合 |
| 单测覆盖 | 28 passed（PDF/Splitter/ETL 全模块） |
| 风险提示 | Prompt 硬约束 100% 必带 |

---

## 🎓 关键技术亮点

### 1. PDF 元数据抽取（双 regex + 目录 fallback）

```python
# 文件名标准 regex
INSTITUTION_DATE_TYPE_PRODUCT.pdf
例：工银理财_2026-08-20_临时性信息披露_关于工银理财·鑫悦最短持有30天...pdf

# 文件名变体 regex（招银理财等）
INSTITUTION_REPORT_TYPE_(DATE)_DESCRIPTION.pdf
例：招银理财_2026-08-18_重大事项公告_关于...（2026年8月18日）.pdf

# 目录 fallback（最权威）
data/理财文件/A01工银理财/产品说明书/*.pdf
data/理财文件/招银理财/临时报告/新设份额/*.pdf
```

### 2. LangGraph 多 Agent + Self-RAG

```python
StateGraph:
  START → Router → SelfRAGJudge
                       │
                       ├─ need_retrieval=true ─▶ RouteDecision
                       │                              │
                       │                              ├─ 闲聊 / 简单 → DirectRAG → Generate
                       │                              └─ 复杂 / 多跳 → AgenticRAG
                       │                                                  │
                       │                                                  ├─ ReActLoop → ToolCall → Reflect
                       │                                                  ├─ Reflexion (Evaluator → Replan)
                       │                                                  └─ Generate (LLM)
                       │
                       └─ need_retrieval=false ─▶ LLMOnlyAnswer
```

### 3. DuckDB 数仓三表

```sql
dwd.documents:   doc_id, institution, report_type, effective_date,
                 product_name, product_code, title, filename, ...
dwd.chunks:      chunk_id, doc_id, chunk_text, page_num, chunk_index
dwd.embeddings:  chunk_id, embedding (1024 维 float32), model
```

幂等模式：`DELETE WHERE source='pdf_local' + INSERT`，可重复跑。

### 4. SSE Trace 时间线（前端 AgentSteps）

```
🔀 Router → 🔍 Self-RAG 判断需要检索 → 🔎 召回 5 篇 →
💭 第1轮思考 → 🛠 rag_search → 👁 观察 →
⭐ 反思 4.2 分无需重规划 → ✅ 生成完成
```

---

## 📝 开发进度

### ✅ Phase 0–6：核心 RAG + Agent
Naive → Advanced (Hybrid + Rerank + RAGAS) → Modular → Agentic → Multi-Agent → Self-RAG + SSE Trace

### ✅ Phase 7–8：金融域改造 ⭐
- ✅ 清理游戏 ETL 残留 / 改名 finguide
- ✅ PDF Loader 双引擎 + 表格感知 Splitter
- ✅ 100 PDF POC 端到端跑通（5 min）
- ✅ Prompt 金融化（风险提示 100%）
- ✅ 前端 Metadata Badge 5 色标签
- ✅ CLAUDE.md / PRD / Phase 报告 重写
- ✅ 28 个单测全绿

### 📅 Phase 9：技术博客 + 面试 STAR
- [ ] RAGAS 金融评测集 50 题
- [ ] 全量 23,229 PDF ETL 跑通（embedding 并发优化后）
- [ ] 技术博客 6000 字
- [ ] 面试 STAR 准备

详见 [`docs/phase8-完成报告.md`](docs/phase8-完成报告.md) 与 [`docs/phase8-5-端到端验证.md`](docs/phase8-5-端到端验证.md)。

---

## 📄 License

MIT License — 仅供学习和个人项目使用

## 🤝 贡献

欢迎提 Issue 和 PR！