# GameGuide AI

> 基于 LangChain + LangGraph 的游戏攻略问答 RAG 系统
> 学习项目，对标网易互娱 AI Agent 实习生岗位面试要求

## 🎯 项目目标

从 0 构建一个生产级 RAG 系统，覆盖：
- **Phase 1**：Naive RAG MVP
- **Phase 2**：Advanced RAG + 评测
- **Phase 3**：Modular RAG 化重构
- **Phase 4**：Agentic RAG + 多 Agent
- **Phase 5**：Memory / MCP / Harness 加分项
- **Phase 6**：技术博客 + 面试 STAR

## 🛠 技术栈

| 组件 | 选型 |
|------|------|
| LLM | Qwen-Long / Claude 3.5 |
| Embedding | BGE-M3 |
| Reranker | bge-reranker-large |
| Vector Store | Chroma |
| BM25 | rank_bm25 |
| 框架 | LangChain + LangGraph |
| 后端 | FastAPI + SSE |
| 前端 | Streamlit |
| 评测 | RAGAS |
| 追踪 | LangSmith |

## 📁 目录结构

```
gameguide-ai/
├── docs/                # 文档（PRD、架构、API、路线）
├── data/                # 原始语料 + 评测集
├── src/
│   ├── loaders/         # 文档加载
│   ├── splitters/       # 文本切分
│   ├── embeddings/      # Embedding 封装
│   ├── vectorstore/     # 向量库封装
│   ├── retrievers/      # 召回
│   ├── rerankers/       # 重排
│   ├── prompts/         # Prompt 模板
│   ├── agents/          # LangGraph Agent
│   ├── api/             # FastAPI
│   └── ui/              # Streamlit
├── tests/               # 测试
├── eval/                # RAGAS 评测
├── notebooks/           # 实验
├── configs/             # 配置
└── scripts/              # 工具脚本
```

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API keys

# 3. 准备数据
# 把游戏攻略 .md 文件放到 data/raw/ 下

# 4. 构建索引
python scripts/rebuild_index.py

# 5. 启动服务
uvicorn src.api.main:app --reload --port 8000

# 6. 启动 UI
streamlit run src/ui/app.py
```

## 📚 文档索引

- [PRD（产品需求文档）](docs/00-PRD.md)
- [架构设计文档](docs/01-架构设计.md)
- [学习路线（10 周）](docs/02-学习路线.md)
- [API 设计文档](docs/03-API 设计.md)
- [Claude Code 项目记忆](CLAUDE.md)

## 📈 学习路径

详细路线见 [docs/02-学习路线.md](docs/02-学习路线.md)，每周一个 Phase。

## 📝 License

MIT — 仅用于学习目的