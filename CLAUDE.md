# CLAUDE.md — FinGuide AI 项目记忆

> 给 Claude Code 用的项目上下文。读完这段它就知道这个项目是什么、怎么做、用什么约定。

---

## 项目一句话

**FinGuide AI** 是一个面向银行理财领域的 RAG 问答系统——基于 LangChain + LangGraph 构建，场景是基于 22 家银行（招银/工银/中银/浦银/民生/交银/中信 等）发布的 2 万+ 理财产品 PDF 公告，进行产品说明书/业绩基准/费率/定期报告的智能问答。

项目继续面向 AI Agent 实习面试，叙事从"游戏攻略问答"转为"金融合规问答"，更强调：
- 真实 PDF 文档的处理（PyMuPDF + 表格感知切分）
- 多机构元数据（institution / report_type / effective_date / product_code）
- 风险提示与时效性披露（理财非存款）

## 当前进度

| Phase | 状态 | 备注 |
|-------|------|------|
| Phase 0–6：核心 RAG + Agent | ✅ 已完成 | Naive → Advanced → Modular → Agentic → Multi-Agent → Self-RAG/Trace |
| Phase 7：ETL 流水线（游戏源）| ✅ 已完成 | 已被 Phase 8 替代 |
| **Phase 8：金融域改造** | ⏳ 进行中 | 业务域从游戏切到银行理财；100 PDF POC 已跑通 |
| Phase 9：技术博客 + 面试 STAR | ⏳ 下一步 | |

## 技术栈速查

| 层级 | 选型 |
|------|------|
| LLM | Ollama 本地 qwen3:8b 或 minimax 云端（reasoning=True） |
| Embedding | Ollama 本地 bge-m3（1024 维） |
| Reranker | bge-reranker-large |
| Vector Store | Chroma（本地 PersistentClient） |
| 数仓 | DuckDB（文档/分块/向量元数据） |
| BM25 | rank_bm25 |
| PDF 解析 | PyMuPDF（fitz） |
| 框架 | LangChain + LangGraph |
| 后端 | FastAPI + SSE |
| 前端 | Next.js 14 (App Router) + TypeScript + Tailwind（indigo 配色） |
| 评测 | RAGAS |
| 追踪 | LangSmith |

## 目录结构

```
finguide-ai/
├── docs/                # 文档（PRD、架构、API、路线、Phase 报告）
├── data/
│   ├── 理财文件/         # 原始 PDF 语料（22 家机构，2万+ 文件）
│   ├── clean/            # ETL 中间产物（gitignore）
│   ├── chroma/           # 向量库持久化（gitignore）
│   └── warehouse/        # DuckDB 数据库（gitignore）
├── src/
│   ├── loaders/          # 文档加载（pdf_loader 支持双引擎）
│   ├── splitters/        # 文本切分（pdf_table_splitter 按页/段切）
│   ├── embeddings/       # Embedding 封装（Ollama bge-m3）
│   ├── vectorstore/      # 向量库封装
│   ├── retrievers/       # 召回（向量/BM25/Hybrid）
│   ├── rerankers/        # 重排
│   ├── prompts/          # Prompt 模板（金融域：必带风险提示）
│   ├── agents/           # LangGraph Agent（Self-RAG / ReAct / Reflexion）
│   ├── graphs/           # StateGraph 定义
│   ├── etl/              # ETL 流水线（transform_pdf / load_duckdb / load_chroma）
│   ├── api/              # FastAPI（含 graph_routes SSE）
│   └── storage/          # SQLite Session / Memory
├── scripts/              # 数据处理脚本（含 etl_financial_poc / scan_pdfs）
├── tests/                # pytest 单测 + 集成测试
├── web/                  # Next.js 14 前端（MetadataBadge 等）
├── eval/                 # RAGAS 评测脚本
├── notebooks/            # 实验性 Jupyter
└── configs/              # YAML 配置
```

## 关键约定

### Python 代码风格
- Python 3.11+，类型注解全开
- Pydantic v2 做数据 schema
- 用 `pathlib.Path` 处理路径，不用 `os.path`
- 单测用 pytest，async 用 pytest-asyncio
- 函数 ≤ 50 行，模块 ≤ 300 行

### 命名规范
- 文件名：小写下划线（`pdf_table_splitter.py`）
- 类名：PascalCase（`PdfTableSplitter`）
- 函数/变量：小写下划线（`transform_pdfs_to_chunks`）
- 常量：大写下划线（`DEFAULT_TOP_K = 50`）

### 接口约定
- Loader 输入路径，输出 `List[Document]`
- Splitter 输入 `List[Document]`，输出 `List[Chunk]`
- Retriever 输入 query 字符串，输出 `List[Chunk]`
- Pipeline 输入 `QueryRequest`，输出 `QueryResponse`
- 所有 IO 函数都 async

### 金融域特有约定
- **金融元数据**：`institution / report_type / effective_date / product_name / product_code / category / page_num`
- **产品编号识别**：理财登记系统编码，regex `\b\d{2}[A-Z]{2}\d{4,6}\b`（如 `24GS5969`）
- **报告类型**：产品说明书 / 临时报告 / 定期报告；子类含"业绩比较基准调整/新设份额/费率调整及优惠"
- **风险提示**：每条回答必须附"理财非存款，产品过往业绩不预示未来表现"
- **专有名词**：机构名、产品名、产品编号、业绩基准、费率 原文保留，不翻译简化

### Git 约定
- 分支：`main` / `feat/xxx` / `fix/xxx`
- Commit：`<scope>: <subject>`（`feat(etl): add pdf loader`）
- 不 commit `.env`、模型权重、`data/clean/`、`data/warehouse/`、`*.parquet`

## 常用命令

```bash
# 后端
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000

# 金融 ETL 一键跑通（100 PDF POC）
python scripts/etl_financial_poc.py

# CLI 问答
python scripts/cli_query.py "招银理财 24GS5969 的业绩基准是多少？"
python scripts/cli_query.py "工银理财最新产品说明书" --stream

# PDF 扫描 + POC 选取
python scripts/scan_pdfs.py --limit 100

# 前端
cd web && npm install && npm run dev   # http://localhost:3000
cd web && npm run build && npm start   # 生产模式

# Docker
docker-compose up -d                    # 一键启动全部
docker exec -it finguide-api python scripts/etl_financial_poc.py

# 测试
pytest tests/unit/ -v
INTEGRATION_TESTS=1 pytest tests/integration/ -v
```

## 环境变量

```bash
# .env（不要 commit）
LLM_PROVIDER=ollama              # ollama | minimax
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=qwen3:8b
LLM_CONTEXT_WINDOW=8192
LLM_REASONING=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=bge-m3
PDF_DATA_DIR=./data/理财文件
PDF_MIN_TEXT_CHARS=100
PDF_MAX_PAGES=80
PDF_CHUNK_SIZE=500
PDF_CHUNK_OVERLAP=50
LANGSMITH_API_KEY=
LANGSMITH_TRACING=false
LANGSMITH_PROJECT=finguide-ai
CHROMA_PERSIST_DIR=./data/chroma
DUCKDB_PATH=./data/warehouse/finguide.duckdb
CHROMA_COLLECTION_NAME=finguide_pdf_v1
```

## 面试相关

- **核心叙事**：Naive RAG → Advanced (Hybrid + Rerank) → Modular → Agentic RAG → Multi-Agent → Self-RAG + Trace → **金融域落地**
- **关键数据**：Anthropic Contextual Retrieval 49% 失败率下降；DuckDB 列存 100 PDF POC 端到端 < 5min
- **重点 Demo**：LangGraph 多 Agent 协作 + 金融 PDF ETL 真实数据 + RAGAS 评测对比

## 注意事项

1. **默认生成模型用本地 Ollama qwen3:8b**；`bge-m3` 只用于 Embedding
2. **本地地址与 Docker 地址不同**：本地用 `localhost`，容器用 `host.docker.internal`
3. **向量库先 Chroma**——本地零成本；DuckDB 存元数据/审计
4. **每写完一个模块**——立刻写单测（PDF Loader/Splitter/ETL 都有对应单测）
5. **每个 Phase 结束**——跑通 + 截图 + 写 Phase 报告
6. **不要写 .env**——用 `.env.example` 做模板
7. **金融域 prompt 必带风险提示**——所有 prompt 模板结尾必须包含"理财非存款..."
8. **PDF 文件名即元数据**——通过 regex 解析，目录兜底

## 当前任务清单

参见 TaskList（项目级 TaskCreate 任务列表）：
1. Phase 0–6：核心 RAG + Agent ✅
2. Phase 7：游戏 ETL 流水线 ✅（已废弃）
3. Phase 8：金融域改造 ⏳（8.1 ETL 清理 ✅ / 8.2 PDF POC ✅ / 8.3 前端 + Prompt ✅ / 8.4 文档 / 8.5 验证）
4. Phase 9：技术博客 + 面试 STAR ⏳

## 相关文件

- 业务调研：`E:/Program Files/vibe_coding/RAG_system/agent-developer-interview-2026-09.md`
- 技术调研：`E:/Program Files/vibe_coding/RAG_system/rag-retrieval-rerank-deepdive-2026-09.md`
- PRD：`docs/00-PRD.md`
- 架构：`docs/01-架构设计.md`
- API：`docs/03-API 设计.md`
- 学习路线：`docs/02-学习路线.md`
- Phase 报告：`docs/phase-XX-*.md`
