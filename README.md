# GameGuide AI

> 基于 RAG 的游戏攻略智能问答系统

一个完整的检索增强生成（RAG）应用，支持从游戏攻略文档中智能检索并生成回答。采用 LangChain 框架、向量数据库检索、LLM 生成，提供 Web 界面和流式响应。

## ✨ 核心特性

- **智能检索**：基于语义向量的相似度检索，自动定位相关文档片段
- **流式生成**：Server-Sent Events (SSE) 实时流式返回，提升用户体验
- **引用溯源**：每个回答标注原始文档来源，可追溯验证
- **多 LLM 支持**：支持 Ollama 本地模型和 MiniMax 云端 API
- **会话管理**：SQLite 持久化会话历史，支持多轮对话上下文
- **前后端分离**：FastAPI 后端 + Next.js 前端，Docker Compose 一键部署

## 🛠 技术栈

### 后端
- **框架**：FastAPI + Pydantic
- **RAG 引擎**：LangChain + LangGraph（实验中）
- **向量数据库**：Chroma（本地持久化）
- **Embedding**：Ollama bge-m3 (1024 维)
- **LLM**：Ollama qwen3:8b / MiniMax API
- **会话存储**：SQLite + SQLAlchemy
- **流式响应**：SSE (Server-Sent Events)

### 前端
- **框架**：Next.js 14 (App Router) + TypeScript
- **UI 库**：Tailwind CSS + shadcn/ui
- **状态管理**：React Hooks
- **流式渲染**：EventSource API

### 部署
- **容器化**：Docker + Docker Compose
- **反向代理**：内置健康检查和热重载

## 📁 项目结构

```
RAG_system/
├── src/                     # Python 后端源码
│   ├── api/                 # FastAPI 路由和端点
│   ├── loaders/             # 文档加载器（Markdown/HTML）
│   ├── splitters/           # 文本切分策略
│   ├── embeddings/          # Embedding 封装
│   ├── vectorstore/         # Chroma 向量库
│   ├── retrievers/          # 检索器
│   ├── rerankers/           # 重排序（规划中）
│   ├── prompts/             # Prompt 模板
│   ├── storage/             # 会话存储
│   ├── graphs/              # LangGraph 工作流（开发中）
│   ├── pipeline.py          # RAG 主流程
│   ├── llm.py               # LLM 客户端
│   └── config.py            # 配置管理
├── web/                     # Next.js 前端
│   ├── src/app/             # 页面路由
│   ├── src/components/      # React 组件
│   └── src/lib/             # API 客户端
├── data/
│   ├── raw/                 # 原始攻略文档
│   ├── chroma/              # 向量库持久化
│   └── gameguide.db         # 会话数据库
├── scripts/                 # 工具脚本
│   ├── rebuild_index.py     # 重建索引
│   └── cli_query.py         # 命令行测试
├── tests/                   # 单元测试和集成测试
├── docs/                    # 架构文档和 ADR
├── docker-compose.yml       # 容器编排
└── README.md
```

## 🚀 快速开始

### 方式 1：Docker Compose（推荐）

**前置要求**：宿主机已安装 Ollama 并拉取模型

```bash
# 1. 准备 Ollama 模型（Windows/Mac 宿主机）
ollama pull bge-m3          # Embedding 模型
ollama pull qwen3:8b        # 生成模型

# 2. 启动服务
docker compose up -d --build

# 3. 构建索引（首次运行）
docker exec -it gameguide-api python scripts/rebuild_index.py

# 4. 访问应用
# Web UI: http://localhost:3000
# API 文档: http://localhost:8000/docs
```

### 方式 2：本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt
cd web && npm install && cd ..

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 配置 Ollama 或 MiniMax

# 3. 构建索引
python scripts/rebuild_index.py

# 4. 启动后端
uvicorn src.api.main:app --reload --port 8000

# 5. 启动前端（新终端）
cd web && npm run dev
```

## 📖 使用示例

### Web 界面

访问 http://localhost:3000，输入问题即可获得实时流式回答：

```
Q: 妖刀姬怎么连招？
A: 妖刀姬的基础连招为：长按 C 键进入妖刀形态 → 1 技能「刃返」突进 → 
   2 段普攻 → 大招「妖刀斩」。完整连招需配合 0.5 秒窗口取消...
   
   [引用来源：阴阳师妖刀姬攻略.md]
```

### 命令行测试

```bash
# 同步查询
python scripts/cli_query.py "红蝶怎么玩？"

# 流式输出
python scripts/cli_query.py "E-4048 错误码" --stream
```

### API 调用

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 同步查询
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "妖刀姬连招", "session_id": "test"}'

# 流式查询（SSE）
curl -N http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "红蝶技能", "session_id": "test"}'
```

## 🏗 架构设计

### RAG 流程

```
用户查询
   ↓
1. Embedding（bge-m3）
   ↓
2. 向量检索（Chroma top_k=10）
   ↓
3. 上下文构建（top_n=5）
   ↓
4. Prompt 组装（System + User + Context）
   ↓
5. LLM 生成（qwen3:8b / MiniMax）
   ↓
6. 流式返回 + 引用溯源
```

### 会话管理

- **SessionStore**：SQLite 存储会话元数据和历史消息
- **多轮对话**：自动加载最近 N 轮历史作为上下文
- **并发安全**：异步 SQLAlchemy 引擎

### 进阶特性（开发中）

- **LangGraph 集成**：状态图工作流，支持 Checkpoint 断点续传
- **Reranker**：计划引入重排序提升召回精度
- **多 Agent**：计划实现工具调用和多 Agent 协作

## 🧪 测试

```bash
# 单元测试
pytest tests/unit/ -v

# 集成测试（需要 Ollama 运行）
INTEGRATION_TESTS=1 pytest tests/integration/ -v

# 覆盖率报告
pytest --cov=src --cov-report=html
```

## 📊 配置说明

关键环境变量（`.env`）：

```bash
# LLM 配置
LLM_PROVIDER=ollama              # ollama / minimax
LLM_MODEL=qwen3:8b
LLM_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.1
LLM_REASONING=true               # 启用思维链

# Embedding 配置
OLLAMA_EMBED_MODEL=bge-m3
OLLAMA_EMBED_DIM=1024

# 检索参数
TOP_K=10                         # 召回候选数
TOP_N=5                          # 实际使用文档数

# 向量库
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=gameguide
```

## 📝 开发进度

### 已完成 ✅

- [x] 文档加载和切分（Markdown/HTML）
- [x] 向量索引构建和持久化
- [x] 语义检索和上下文构建
- [x] LLM 生成和流式响应
- [x] FastAPI 后端（同步 + 流式端点）
- [x] Next.js 前端 UI
- [x] 会话管理和历史记录
- [x] Docker 容器化部署
- [x] 健康检查和索引状态监控

### 进行中 🚧

- [ ] LangGraph StateGraph 集成（Checkpoint 持久化）
- [ ] 前端多会话状态管理
- [ ] Feature Flag 灰度发布机制

### 规划中 📅

- [ ] Reranker 重排序（BM25 / Cross-Encoder）
- [ ] RAGAS 评测框架
- [ ] LangSmith 追踪和调试
- [ ] Multi-Agent 工具调用
- [ ] 缓存优化和性能调优

## 🤝 贡献

欢迎提 Issue 和 PR！

## 📄 License

MIT License - 仅供学习和个人项目使用
