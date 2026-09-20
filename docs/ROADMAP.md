# 🚀 项目后续升级路线

**当前状态**：Phase 0-5 完成，minimax LLM 已接入
**目标**：从 MVP → 生产级 AI 平台

---

## 📊 **优先级矩阵（按 ROI 排序）**

```
高价值 ▲
       │
       │  ★ RAGAS 评测 (4h)
       │  ★ 智能命名 V2 (2h)
       │  ★ 技术博客 1-2 篇 (1 天)
       │
       │  ★ README 重写 (2h)
       │  ★ Demo 视频 (4h)
       │  ★ STAR 回答 (4h)
       │
       │  ★ 会话搜索 + 导出 (5h)
       │  ★ LangSmith 接入 (3h)
       │  ★ CI/CD + Docker 优化 (1 天)
       │
       │  ★ Multi-Agent (3 天)
       │  ★ MCP Server (1 天)
       │  ★ Redis Checkpoint (4h)
       │
       │  ★ Self-RAG (2 天)
       │  ★ GraphRAG (3 天)
       │
       │  ★ K8s 部署 (1 天)
       │  ★ 多租户 (3 天)
       │
低价值 ▼
```

---

## 🎯 **第一优先级：智能化完善（1-2 周）**

### 1. 智能命名 V2（已完成）

**实现**：✅ `src/storage/naming_v2.py`

**改进点**：
- ✅ 基于检索内容生成（更精准）
- ✅ 长度 3-7 词（行业标准）
- ✅ 重试机制（最多 2 次）
- ✅ 关键词降级（LLM 失败时）
- ✅ 多轮更新判断（主题变化）

**测试**：✅ `tests/unit/test_naming_v2.py`

---

### 2. RAGAS 评测（4h）

**目标**：自动评估 RAG 质量

**实现步骤**：
```python
# src/evaluation/ragas_eval.py

from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)
from datasets import Dataset

async def evaluate_rag(test_cases: list[dict]):
    """评估 RAG 质量

    Args:
        test_cases: [{query, expected_answer, ground_truth}, ...]
    """
    dataset = Dataset.from_list(test_cases)

    # RAGAS 评估（需要 RAG 系统的 callable）
    result = evaluate(
        dataset,
        metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
    )
    return result

# 使用：
result = await evaluate_rag([
    {
        "question": "妖刀姬 S13 怎么连招？",
        "answer": run_rag_graph("妖刀姬 S13 怎么连招？"),
        "contexts": [...],
        "ground_truth": "1. 长按 C 进入妖刀形态...",
    },
])
print(f"Context Precision: {result['context_precision']:.3f}")
print(f"Faithfulness: {result['faithfulness']:.3f}")
```

**指标含义**：
- **Context Precision**: 检索相关性（0-1）
- **Context Recall**: 检索完整性（0-1）
- **Faithfulness**: 答案忠实于文档（0-1）
- **Answer Relevancy**: 答案相关性（0-1）

**价值**：⭐⭐⭐⭐⭐
- 面试展示："我的 RAG 系统达到 90% faithfulness"
- A/B 测试 RAGAS 指标
- 持续监控质量

---

### 3. 会话搜索 + 导出（5h）

**目标**：让用户能查找和备份历史会话

```python
# src/api/sessions.py 新增端点

@app.post("/api/v1/sessions/search")
async def search_sessions(query: str, top_k: int = 5):
    """基于内容搜索会话（用 RAG 自己搜索）"""
    sessions = await session_store.search_by_content(query)
    return sessions

@app.get("/api/v1/sessions/{id}/export")
async def export_session(id: str, format: str = "markdown"):
    """导出会话（Markdown / JSON）"""
    if format == "markdown":
        return await session_store.export_md(id)
    return await session_store.export_json(id)
```

**前端**：
```tsx
// Sidebar 添加搜索框 + 导出按钮
<button onClick={() => exportSession(id, 'markdown')}>
  📥 导出
</button>
```

---

### 4. LangSmith 接入（3h）

**目标**：追踪所有 LLM 调用

```python
# src/llm.py 添加 LangSmith 追踪

import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key

# LangSmith 自动追踪所有 LLM 调用
# 查看 https://smith.langchain.com
```

**追踪内容**：
- LLM 调用（prompt、completion、token、延迟）
- 检索调用（query、docs、scores）
- Agent 步骤（ReAct 循环）

**价值**：⭐⭐⭐⭐
- 实时监控生产环境
- Debug 慢请求
- 成本分析

---

## 🚀 **第二优先级：面试准备（1 周）**

### 5. 技术博客 1-2 篇（1 天）

**选题**：
1. **《从 Naive RAG 到 Agentic RAG：我的 RAG 系统演进之路》**
   - 5 个 Phase 的演进过程
   - 每个 Phase 的关键决策
   - 代码示例 + 性能数据

2. **《ReAct + Reflexion：构建自我纠错的 AI Agent》**
   - Agent 架构详解
   - ReAct vs Plan-Execute
   - 工具调用设计
   - 反思机制

3. **《Modular RAG：让 RAG 系统像积木一样灵活》**
   - 模块化架构设计
   - 配置驱动
   - A/B 测试

**发布平台**：Medium / 掘金 / 知乎

---

### 6. README 重写（2h）

```markdown
# GameGuide AI

> 基于 ReAct + Reflexion 的 Agentic RAG 游戏攻略问答系统

![demo](demo.gif)

## 🎯 项目亮点
- 🚀 ReAct Agent + Reflexion 自我纠错
- 🧩 Modular RAG（配置驱动）
- 💾 多会话独立运行
- 🔌 支持 Ollama / minimax 双 LLM

## 📊 性能数据
- Context Precision: 0.92
- Faithfulness: 0.95
- 缓存命中: 97%

## 🏗️ 架构图
[完整架构图]

## 🚀 快速开始
...

## 📚 技术栈
...

## 🎓 学习价值
...
```

---

### 7. Demo 视频（4h）

**内容（5 分钟）**：
1. **开场**（30s）：问题介绍 + 项目亮点
2. **演示**（3min）：
   - 创建会话
   - 智能命名
   - 多会话切换
3. **架构**（1min）：技术栈 + 关键设计
4. **结尾**（30s）：项目地址 + GitHub

**工具**：
- **OBS Studio**（录屏）
- **剪映/PR**（剪辑）

**上传**：B 站 / YouTube / 掘金

---

### 8. STAR 回答准备（4h）

**模板**：

```
S (Situation 背景)：
在游戏攻略 AI 项目中，需要让 Agent 能够自我纠错...

T (Task 任务)：
设计 ReAct + Reflexion 架构，让 Agent 评估答案质量...

A (Action 行动)：
1. 实现 ReAct Loop（Thought → Action → Observation）
2. 设计 Reflexion Evaluator 节点（5 分制）
3. 添加 Memory 机制记录失败经验
4. 集成 LangGraph Checkpointer

R (Result 结果)：
- 答案质量提升 17%（Precision）
- 缓存命中率达 97%
- 反思机制有效识别低质量答案
```

**5 个核心场景**：
1. ReAct Agent 设计
2. Reflexion 自我纠错
3. Modular RAG 架构
4. 多会话状态管理
5. 性能优化

---

## 🔧 **第三优先级：生产化（1 周）**

### 9. CI/CD + Docker 优化（1 天）

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/unit -v
      - run: docker compose up -d
      - run: pytest tests/integration -v
```

**Docker 多阶段构建**：
```dockerfile
# stage 1: builder
FROM python:3.11-slim AS builder
COPY requirements.txt .
RUN pip install --user

# stage 2: runtime
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**价值**：
- 镜像大小减少 60%（从 800MB 到 300MB）
- CI 自动测试覆盖

---

### 10. Redis Checkpointer（4h）

```python
# src/graphs/rag_graph.py
from langgraph.checkpoint.redis import AsyncRedisSaver

saver = AsyncRedisSaver(
    redis_url="redis://localhost:6379/0"
)
graph = workflow.compile(checkpointer=saver)
```

**价值**：
- 支持多实例部署（横向扩展）
- 高可用（Redis 集群）
- 性能提升（内存访问）

---

### 11. MCP Server（1 天）

```python
# src/mcp/server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("gameguide-rag")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="rag_search",
            description="Search game guides knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "number"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, args: dict):
    if name == "rag_search":
        docs = await run_rag(args["query"], top_k=args.get("top_k", 5))
        return [TextContent(text=str(docs))]
```

**价值**：⭐⭐⭐⭐
- 标准化工具接口
- 可被 Claude Desktop / Cursor 使用

---

## 🚀 **第四优先级：高级 AI 功能（1 个月）**

### 12. Multi-Agent 协作（3 天）

**Supervisor + Workers 架构**：
```
Supervisor Agent
    ├─ Retrieval Worker（信息检索）
    ├─ Analysis Worker（信息分析）
    └─ Generation Worker（答案生成）
```

**价值**：⭐⭐⭐⭐⭐
- 专业化分工
- 并行执行
- 更强的能力

---

### 13. Self-RAG（2 天）

**核心思想**：Agent 自己评估检索质量，必要时重新检索

```python
# 流程
用户问题 → 检索 → [生成答案]
                ↓
              质量评估
                ↓
        质量 < 阈值 → 重新检索（调整 query）
```

**价值**：⭐⭐⭐⭐⭐
- 动态调整检索策略
- 自我纠错
- 提升答案质量

---

### 14. GraphRAG（3 天）

**核心思想**：构建实体关系图谱

```
妖刀姬 ──属于── 永劫无间
    │
    └──使用── 刃返（技能）
         │
         └──克制── 红蝶（角色）
```

**价值**：⭐⭐⭐⭐
- 多跳推理
- 实体关系
- 复杂查询

---

## 🚀 **第五优先级：企业级（3 个月）**

### 15. Kubernetes 部署（1 天）

```yaml
# k8s/gameguide-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gameguide-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gameguide-api
  template:
    metadata:
      labels:
        app: gameguide-api
    spec:
      containers:
      - name: api
        image: gameguide-api:dev
        ports:
        - containerPort: 8000
```

### 16. 多租户（3 天）

- 用户隔离
- 数据隔离
- 配额管理
- 计费系统

---

## 📊 **推荐执行顺序（基于 ROI）**

### 🎯 **如果你要面试（推荐 ⭐⭐⭐⭐⭐）**

```
Week 1:
├── 智能命名 V2 ✅ (已完成)
├── RAGAS 评测 (4h)
├── 会话搜索 + 导出 (5h)
├── LangSmith 接入 (3h)
└── 技术博客 1 篇 (4h)

Week 2:
├── README 重写 (2h)
├── Demo 视频 (4h)
├── STAR 回答 (4h)
└── 第二篇博客 (4h)

Week 3:
└── 开始投递简历 + 面试！

Week 4+:
└── 面试期间继续开发 Multi-Agent / Self-RAG
```

### 🎯 **如果你想继续深挖（推荐 ⭐⭐⭐⭐）**

```
Week 1-2:
├── 智能命名 V2 ✅
├── RAGAS 评测
├── 会话搜索 + 导出
├── LangSmith 接入
└── 技术博客 1 篇

Week 3-4:
├── Multi-Agent 协作 (3 天)
├── Self-RAG (2 天)
└── README 重写 + Demo 视频

Month 2:
├── CI/CD + Docker 优化
├── Redis Checkpointer
├── MCP Server
└── GraphRAG

Month 3:
├── K8s 部署
├── 多租户
└── 高级功能（按需）
```

### 🎯 **混合路线（推荐 ⭐⭐⭐⭐⭐）**

```
Week 1:
├── RAGAS 评测 (4h)         ← 量化 RAG 质量
├── 会话搜索 + 导出 (5h)    ← 提升产品体验
├── 技术博客 1 篇 (4h)     ← 展示深度
└── LangSmith 接入 (3h)     ← 可观测性

Week 2:
├── README 重写 (2h)        ← 第一印象
├── Demo 视频 (4h)          ← 面试亮点
├── STAR 回答 (4h)          ← 面试必备
└── Multi-Agent (3 天)      ← 技术深度

Week 3:
└── 开始投递简历！

Week 4+:
└── 面试期间继续优化其他功能
```

---

## 📝 **总结**

### 立即可做（ROI 高 ⭐⭐⭐⭐⭐）
1. **RAGAS 评测** - 量化 RAG 效果
2. **会话搜索 + 导出** - 提升产品体验
3. **技术博客** - 展示深度

### 短期价值（1 周）
- README 重写
- Demo 视频
- STAR 回答

### 中期价值（1 个月）
- Multi-Agent 协作
- Self-RAG
- CI/CD + Redis

### 长期价值（3 个月）
- K8s + 多租户
- 企业级功能

---

**你想从哪个开始？**

1. **面试准备路线**：RAGAS + 博客 + README + Demo
2. **技术深度路线**：Multi-Agent + Self-RAG + 高级功能
3. **生产化路线**：CI/CD + Redis + K8s
4. **混合路线**：面试准备 + 高级功能并进