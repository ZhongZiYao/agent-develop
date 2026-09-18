# GameGuide AI

> 基于 LangChain + LangGraph 的游戏攻略问答 RAG 系统
> 学习项目，对标网易互娱 AI Agent 实习生岗位面试要求

## 🎯 项目目标

从 0 构建一个生产级 RAG 系统，覆盖：

- **Phase 1**：Naive RAG MVP（当前阶段 ✅）
- **Phase 2**：Advanced RAG + 评测
- **Phase 3**：Modular RAG 化重构
- **Phase 4**：Agentic RAG + 多 Agent
- **Phase 5**：Memory / MCP / Harness 加分项
- **Phase 6**：技术博客 + 面试 STAR

## 🛠 技术栈

| 组件 | 选型 |
|------|------|
| **LLM** | MiniMax（OpenAI 兼容 API） |
| **Embedding** | Ollama 本地 bge-m3（中文 SOTA） |
| **Vector Store** | Chroma（本地持久化） |
| **框架** | LangChain + LangGraph |
| **后端** | FastAPI + SSE |
| **前端** | Next.js 14 + TypeScript + Tailwind |
| **评测** | RAGAS（Phase 2） |
| **追踪** | LangSmith（可选） |

## 📁 项目结构

```
gameguide-ai/
├── docs/                # 文档（PRD、架构、API、路线）
├── data/                # 数据
│   ├── raw/             # 原始攻略语料
│   ├── chroma/          # Chroma 持久化（git ignore）
│   └── eval/            # RAGAS 测试集
├── src/                 # Python 后端
│   ├── loaders/         # 文档加载
│   ├── splitters/       # 文本切分
│   ├── embeddings/      # Ollama Embedding
│   ├── vectorstore/     # Chroma 封装
│   ├── retrievers/      # 召回
│   ├── rerankers/       # 重排（Phase 2）
│   ├── prompts/         # Prompt 模板
│   ├── pipeline.py      # RAG Pipeline
│   ├── llm.py           # LLM 客户端
│   ├── config.py        # 配置
│   ├── api/             # FastAPI
│   └── __main__.py      # CLI 入口
├── web/                 # Next.js 前端
│   ├── src/app/         # App Router
│   ├── src/components/  # React 组件
│   └── src/lib/         # API 客户端
├── scripts/             # 工具脚本
│   ├── rebuild_index.py # 重建索引
│   └── cli_query.py     # 命令行问答
├── tests/               # 测试
├── docker/              # Docker 文件
├── docker-compose.yml   # 一键启动
├── docs/                # 文档
└── CLAUDE.md            # Claude Code 项目记忆
```

## 🚀 快速开始

### 方式 1：本地开发（推荐新手）

#### 1. 准备 Ollama

```bash
# 安装 Ollama（Windows/Mac/Linux 各自下载）
# https://ollama.com/download

# 拉取 embedding 模型
ollama serve                # 启动服务
ollama pull bge-m3          # 拉取 bge-m3（中文 SOTA，1024 维）
```

#### 2. 启动后端

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY

# 构建索引
python scripts/rebuild_index.py

# 启动 API
uvicorn src.api.main:app --reload --port 8000

# 验证
curl http://localhost:8000/api/v1/health
```

#### 3. 启动前端

```bash
cd web
npm install
npm run dev
# 打开 http://localhost:3000
```

#### 4. 命令行体验

```bash
# 同步问答
python scripts/cli_query.py "妖刀姬 S13 怎么连招？"

# 流式输出
python scripts/cli_query.py "E-4048 错误码" --stream
```

### 方式 2：Docker Compose（一键启动）

```bash
# 启动所有服务（含 Ollama）
docker-compose up -d

# 拉取 bge-m3
docker exec -it gameguide-ollama ollama pull bge-m3

# 重建索引（首次）
docker exec -it gameguide-api python scripts/rebuild_index.py

# 查看日志
docker-compose logs -f
```

打开 http://localhost:3000

## 📚 文档索引

- [PRD（产品需求文档）](docs/00-PRD.md)
- [架构设计文档](docs/01-架构设计.md)
- [学习路线（10 周）](docs/02-学习路线.md)
- [API 设计文档](docs/03-API 设计.md)
- [调研笔记](docs/04-调研笔记.md)
- [Claude Code 项目记忆](CLAUDE.md)

## 📊 Phase 1 MVP 验收

- [x] 加载 10 篇游戏攻略文档
- [x] 端到端 demo：query → 答案（含引用）
- [x] FastAPI + SSE 流式
- [x] Next.js 前端 UI
- [x] Chroma 持久化
- [x] Ollama 本地 Embedding
- [x] 命令行工具
- [ ] RAGAS 评测（Phase 2）

## 🎮 示例问题

试试这些问题：

- `妖刀姬 S13 怎么连招？`
- `E-4048 错误码怎么解决？`
- `红蝶怎么玩？`
- `素问在副本里站什么位置？`
- `长剑和太刀哪个更适合新手？`

## 🔧 配置说明

完整配置见 `.env.example`。关键项：

```bash
# LLM
LLM_API_KEY=sk-xxx                    # MiniMax key
LLM_BASE_URL=https://api.minimaxi.chat/v1
LLM_MODEL=MiniMax-Text-01

# Embedding（Ollama）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=bge-m3

# 检索参数
TOP_K=10
TOP_N=5
```

## 🧪 测试

```bash
# 跑单测
pytest tests/unit/ -v

# 跑集成测试（需要 Ollama + LLM）
INTEGRATION_TESTS=1 pytest tests/integration/ -v
```

## 📈 学习路径

详细路线见 [docs/02-学习路线.md](docs/02-学习路线.md)，每周一个 Phase。

## 📝 License

MIT — 仅用于学习目的