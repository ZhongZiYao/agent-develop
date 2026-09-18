# CLAUDE.md — GameGuide AI 项目记忆

> 给 Claude Code 用的项目上下文。读完这段它就知道这个项目是什么、怎么做、用什么约定。

---

## 项目一句话

**GameGuide AI** 是一个面向网易互娱 AI Agent 实习面试的学习型项目——基于 LangChain + LangGraph 构建生产级 RAG 系统，场景是游戏攻略问答。

## 当前进度

| Phase | 状态 | 备注 |
|-------|------|------|
| Phase 0：准备 | ✅ 已完成 | PRD、架构、API、路线文档已写 |
| Phase 1：Naive RAG MVP | ⏳ 下一步 | 准备创建项目骨架 + 写代码 |

## 技术栈速查

| 层级 | 选型 |
|------|------|
| LLM | 通义千问 Qwen-Long / Claude 3.5 |
| Embedding | BGE-M3（智源）|
| Reranker | bge-reranker-large |
| Vector Store | Chroma（本地）|
| BM25 | rank_bm25 |
| 框架 | LangChain + LangGraph |
| 后端 | FastAPI + SSE |
| 前端 | Streamlit |
| 评测 | RAGAS |
| 追踪 | LangSmith |

## 目录结构

```
gameguide-ai/
├── docs/                # 文档（PRD、架构、API、路线）
├── data/                # 原始语料 + 评测集
├── src/
│   ├── loaders/         # 文档加载
│   ├── splitters/       # 文本切分
│   ├── embeddings/      # Embedding 封装
│   ├── vectorstore/     # 向量库封装
│   ├── retrievers/      # 召回（向量/BM25/Hybrid）
│   ├── rerankers/       # 重排
│   ├── prompts/         # Prompt 模板
│   ├── agents/          # LangGraph Agent
│   ├── api/             # FastAPI
│   └── ui/              # Streamlit
├── tests/               # 单测 + 集成测试
├── eval/                # RAGAS 评测脚本
├── notebooks/           # 实验性 Jupyter
├── configs/             # YAML 配置
└── scripts/              # 数据处理脚本
```

## 关键约定

### Python 代码风格
- Python 3.11+，类型注解全开
- Pydantic v2 做数据 schema
- 用 `pathlib.Path` 处理路径，不用 `os.path`
- 单测用 pytest，async 用 pytest-asyncio
- 函数 ≤ 50 行，模块 ≤ 300 行

### 命名规范
- 文件名：小写下划线（`hybrid_retriever.py`）
- 类名：PascalCase（`HybridRetriever`）
- 函数/变量：小写下划线（`retrieve_chunks`）
- 常量：大写下划线（`DEFAULT_TOP_K = 50`）

### 接口约定
- Loader 输入路径，输出 `List[Document]`
- Retriever 输入 query 字符串，输出 `List[Chunk]`
- Pipeline 输入 `QueryRequest`，输出 `QueryResponse`
- 所有 IO 函数都 async

### Git 约定
- 分支：`main` / `feat/xxx` / `fix/xxx`
- Commit：`<scope>: <subject>`（`feat(retriever): add hybrid search`）
- 不 commit `.env`、模型权重

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 API
uvicorn src.api.main:app --reload --port 8000

# 启动 Streamlit
streamlit run src/ui/app.py

# 跑单测
pytest tests/ -v

# 跑 RAGAS 评测
python eval/ragas_eval.py --pipeline advanced

# 重建索引
python scripts/rebuild_index.py
```

## 环境变量

```bash
# .env（不要 commit）
QWEN_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
LANGSMITH_API_KEY=xxx
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=gameguide-ai
CHROMA_PERSIST_DIR=./data/chroma
```

## 面试相关

- **核心叙事**：从 Naive → Advanced → Modular → Agentic RAG 的渐进式演进
- **关键数据**：Anthropic Contextual Retrieval 49% 失败率下降
- **重点 Demo**：LangGraph 多 Agent 协作 + RAGAS 评测对比

## 注意事项

1. **不要默认用 OpenAI**——优先 Qwen-Long（中文强 + 便宜）
2. **向量库先 Chroma**——本地零成本，Phase 5+ 再升级 Milvus
3. **每写完一个模块**——立刻写单测
4. **每个 Phase 结束**——跑通 + 截图 + 写博客
5. **不要写 .env**——用 `.env.example` 做模板

## 当前任务清单

参见 TaskList（项目级 TaskCreate 任务列表）：
1. Phase 0：编写 PRD + 架构设计 + 准备数据 ✅
2. Phase 1：实现 Naive RAG MVP（进行中）
3. Phase 2：Advanced RAG + 评测
4. Phase 3：Modular 化重构
5. Phase 4：Agentic RAG + 多 Agent
6. Phase 5：Memory/MCP/Harness
7. Phase 6：技术博客 + 面试 STAR

## 相关文件

- 业务调研：`E:/Program Files/vibe_coding/RAG_system/agent-developer-interview-2026-09.md`
- 技术调研：`E:/Program Files/vibe_coding/RAG_system/rag-retrieval-rerank-deepdive-2026-09.md`
- PRD：`docs/00-PRD.md`
- 架构：`docs/01-架构设计.md`
- API：`docs/03-API 设计.md`
- 学习路线：`docs/02-学习路线.md`