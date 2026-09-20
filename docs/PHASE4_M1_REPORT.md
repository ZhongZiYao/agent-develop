# Phase 4 M1 完成报告：Agentic RAG 基础框架

## 🎯 **M1 目标**

实现 **ReAct (Reasoning + Acting)** 架构的 Agent 基础框架。

---

## ✅ **完成的组件**

### 1. **AgentState** (`src/graphs/agent_state.py`)

扩展 RAGState，新增 Agent 特有字段：

```python
class AgentState(TypedDict):
    # 继承 RAGState 的基础字段
    query: str
    retrieved_docs: list[dict]
    answer: str
    
    # Agent 特有字段
    agent_scratchpad: list[dict]  # [{thought, action, observation}]
    iterations: int
    max_iterations: int
    tools_used: list[str]
    
    # Reflexion 相关（M2 使用）
    reflection: str
    evaluation_score: float
    need_replan: bool
```

---

### 2. **Tools** (`src/agents/tools.py`)

**3 个基础工具**：

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `rag_search` | 从知识库检索信息 | query, top_k | list[dict] |
| `compare` | 对比两个实体 | entity_a, entity_b, aspect | comparison dict |
| `finish` | 结束并返回答案 | answer | finish signal |

**Tool 类封装**：
```python
class Tool:
    name: str
    description: str  # 供 LLM 理解的工具描述
    func: callable    # 实际执行函数
    
    async def run(**kwargs) -> Any
```

**注册表**：
- `AGENT_TOOLS`: 全局工具列表
- `get_tool_by_name(name)`: 按名字获取工具
- `get_tools_description()`: 生成 LLM Prompt

---

### 3. **ReAct Agent** (`src/agents/react_agent.py`)

**ReAct 循环核心逻辑**：

```
while iterations < max_iterations:
    1. Thought: 思考下一步（调用 LLM）
       "我需要先检索妖刀姬的信息..."
       
    2. Action: 选择工具（LLM 输出 JSON）
       {"tool": "rag_search", "args": {"query": "妖刀姬"}}
       
    3. Observation: 执行工具，记录结果
       [doc1, doc2, doc3]
       
    4. 记录到 scratchpad
       append({thought, action, observation})
       
    5. 检查是否结束
       if action.tool == "finish": break
```

**关键方法**：
- `_think(query, scratchpad)`: 思考下一步
- `_select_action(thought, scratchpad)`: 选择工具（JSON 解析）
- `_execute_action(action)`: 执行工具
- `_format_scratchpad(scratchpad)`: 格式化历史

**LangGraph 包装**：
- `react_agent_node(state)`: 节点函数
- `should_continue(state)`: 循环终止判断

---

### 4. **Router** (`src/agents/router.py`)

**查询分类 + 路由决策**：

| 查询类型 | 特征 | 路由目标 |
|---------|------|---------|
| `simple_factual` | 简单事实查询 | Direct RAG |
| `comparison` | 包含"哪个""对比""vs" | Agentic RAG |
| `complex_analytical` | 包含"为什么""分析" | Agentic RAG |
| `multi_hop` | 包含"然后""之后" | Agentic RAG |
| `ambiguous` | 查询太短或太泛 | Direct RAG |

**实现方式**：
- `_heuristic_classify(query)`: 启发式分类（关键词匹配，快速）
- `llm_classify_query(query)`: LLM 分类（可选，准确但慢）

**测试结果**：
```
妖刀姬的连招是什么？ → simple_factual
妖刀姬和红蝶哪个更好？ → comparison
为什么 S13 削弱妖刀姬？ → complex_analytical
```

---

### 5. **Agentic RAG Graph** (`src/agents/agentic_rag_graph.py`)

**完整流程编排**：

```
┌─────────────────────────────────────────┐
│  Router: 查询分类                        │
└─────────────────────────────────────────┘
            ↓
    ┌───────┴───────┐
    ↓               ↓
┌─────────┐   ┌─────────────────────┐
│ Direct  │   │  Agentic RAG Loop   │
│  RAG    │   │  ┌───────────────┐  │
│         │   │  │ ReAct Agent   │  │
│ (Phase3)│   │  │ Iteration 1   │←─┤
└─────────┘   │  └───────────────┘  │
    ↓         │  ┌───────────────┐  │
   END        │  │ Iteration 2   │←─┤
              │  └───────────────┘  │
              │         ...         │
              └─────────────────────┘
                       ↓
                      END
```

**Graph 结构**：
- 入口：`router`
- 条件路由：`router → {direct_rag | agentic_rag}`
- 循环边：`agentic_rag → continue → agentic_rag`
- 终止：`agentic_rag → end → END`

**便捷函数**：
```python
result = await run_agentic_rag(
    query="妖刀姬和红蝶哪个更好？",
    max_iterations=5
)
```

---

## 🧪 **集成测试** (`tests/integration/test_agentic_rag.py`)

### 测试用例

| 测试 | 目的 | 验证点 |
|------|------|--------|
| `test_simple_query_routes_to_direct_rag` | 简单查询路由 | route == "direct_rag" |
| `test_comparison_query_routes_to_agentic_rag` | 对比查询路由 | route == "agentic_rag" |
| `test_react_loop_with_rag_search` | ReAct 循环 | scratchpad 不为空 |
| `test_max_iterations_limit` | 迭代次数限制 | iterations <= max_iterations |
| `test_agent_scratchpad_format` | Scratchpad 格式 | 包含 thought/action/observation |

---

## 📐 **架构设计亮点**

### 1. **ReAct 范式**
- 学术界 2022 年提出，已成为主流 Agent 架构
- Thought + Action + Observation 循环
- 可解释性强（能看到推理过程）

### 2. **双路由设计**
- 简单问题 → Direct RAG（高效，低 Token）
- 复杂问题 → Agentic RAG（智能，多步推理）
- 最优性能/成本平衡

### 3. **工具可扩展**
- Tool 基类 + 注册表模式
- 添加新工具只需 3 步：
  1. 实现 `async def tool_func(**kwargs)`
  2. 创建 `Tool(name, desc, func)`
  3. 添加到 `AGENT_TOOLS`

### 4. **循环可控**
- `max_iterations`: 防止死循环
- `should_continue()`: 灵活终止条件
- `finish` 工具：Agent 主动结束

### 5. **可解释性**
- `agent_scratchpad`: 记录完整推理过程
- 每步包含：thought, action, observation
- 便于调试和展示给用户

---

## 📊 **与 Phase 3 的对比**

| 维度 | Phase 3 (Modular RAG) | Phase 4 M1 (Agentic RAG) |
|------|----------------------|-------------------------|
| **架构** | 固定流水线 | 动态循环 |
| **路由** | 静态配置 | 动态分类 |
| **工具** | 仅向量检索 | 多工具（search, compare, finish） |
| **推理** | 单步 | 多步 ReAct 循环 |
| **复杂问题** | 不支持 | 支持对比、分析、多跳 |
| **可解释性** | 低 | 高（scratchpad 记录） |
| **Token 消耗** | 低 | 中等（需权衡） |

---

## 🎯 **使用示例**

### 简单查询（走 Direct RAG）

```python
result = await run_agentic_rag("妖刀姬的连招是什么？")

# 输出
{
    "route": "direct_rag",
    "query_type": "simple_factual",
    "answer": "妖刀姬的连招是...",
    "retrieved_docs": [...]
}
```

### 复杂查询（走 Agentic RAG）

```python
result = await run_agentic_rag("妖刀姬和红蝶哪个更适合新手？")

# 输出
{
    "route": "agentic_rag",
    "query_type": "comparison",
    "answer": "从新手友好度来看...",
    "agent_scratchpad": [
        {
            "iteration": 1,
            "thought": "我需要先检索妖刀姬的信息",
            "action": {"tool": "rag_search", "args": {"query": "妖刀姬"}},
            "observation": [doc1, doc2, ...]
        },
        {
            "iteration": 2,
            "thought": "接下来检索红蝶的信息",
            "action": {"tool": "rag_search", "args": {"query": "红蝶"}},
            "observation": [doc3, doc4, ...]
        },
        {
            "iteration": 3,
            "thought": "现在可以对比了",
            "action": {"tool": "finish", "args": {"answer": "..."}},
            "observation": {"type": "finish"}
        }
    ],
    "iterations": 3
}
```

---

## 🚀 **下一步：M2 Reflexion 自我纠错**

**待实现**：
1. ✅ Reflection 节点：评估当前步骤质量
2. ✅ Evaluator 节点：评估最终答案质量
3. ✅ Replan 机制：质量不佳时重新规划
4. ✅ Memory 机制：记录失败经验

---

## 📚 **参考文献**

1. **ReAct**: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022)
2. **LangGraph**: State Machines for LLM Applications (LangChain, 2024)
3. **Reflexion**: Language Agents with Verbal Reinforcement Learning (Shinn et al., 2023)

---

**M1 完成度：100% ✅**

Commit: `066127d`
Files: 7 个新文件，784 行代码
