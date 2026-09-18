# AI Agent 开发工程师面经（2026.09 整理）

> 适用岗位：网易互娱·AI 工具应用实习生 / AI Agent 工程师 / LLM 应用工程师
> 涵盖：Agent 基础、Prompt Engineering、RAG、Context Engineering、MCP、Skill、Harness Engineering、LangChain、LangGraph、Memory、AI Agent Eval、多 Agent 协作

---

## 目录

1. [AI Agent 基础概念](#1-ai-agent-基础概念)
2. [Prompt Engineering 进阶](#2-prompt-engineering-进阶)
3. [RAG 检索增强生成](#3-rag-检索增强生成)
4. [Context Engineering 上下文工程](#4-context-engineering-上下文工程)
5. [MCP（Model Context Protocol）](#5-mcpmodel-context-protocol)
6. [Skill 与 Claude Code 工具链](#6-skill-与-claude-code-工具链)
7. [Harness Engineering](#7-harness-engineering)
8. [LangChain](#8-langchain)
9. [LangGraph](#9-langgraph)
10. [Memory 记忆系统](#10-memory-记忆系统)
11. [AI Agent Eval 评估体系](#11-ai-agent-eval-评估体系)
12. [多 Agent 协作 / ReAct / Plan-and-Execute](#12-多-agent-协作--react--plan-and-execute)
13. [场景设计题（高频）](#13-场景设计题高频)
14. [项目深挖准备](#14-项目深挖准备)
15. [反问环节 / 加分项](#15-反问环节--加分项)

---

## 1. AI Agent 基础概念

### Q1.1 什么是 AI Agent？和 LLM / Copilot 有什么区别？

**答**：
- **LLM**：单次推理，给 prompt 出 response，没有行动能力
- **Copilot**：人主导、AI 辅助（每次动作需要人确认）
- **Agent**：AI 主导，**自主感知→规划→调用工具→执行→反思**，可以闭环完成多步任务

Agent 的核心三要素：
1. **感知（Perception）**：能读 LLM/工具/环境的输入
2. **决策（Planning + Reasoning）**：能拆解目标、选下一步行动
3. **行动（Action）**：能调用工具影响外部世界

### Q1.2 Agent 的标准循环是什么？

**答（ReAct 范式）**：
```
Thought → Action → Observation → Thought → Action → ... → Final Answer
```
- Thought：当前进度 + 下一步计划
- Action：调工具或生成回答
- Observation：工具返回结果

### Q1.3 主流 Agent 范式有哪些？

| 范式 | 特点 | 适用场景 |
|------|------|---------|
| **ReAct** | 边想边干，每步都推理 | 通用任务、工具调用 |
| **Plan-and-Execute** | 先全规划、再逐步执行 | 长流程、确定性高 |
| **Reflexion** | 反思 + 自我批评 + 二次尝试 | 容错、复杂推理 |
| **CodeAct** | Agent 直接生成代码执行 | 数学、数据分析 |
| **Multi-Agent** | 多 Agent 分工 + 协作 | 复杂流水线、角色扮演 |

### Q1.4 Agent 失败的常见原因有哪些？

**答**（面试常问）：
1. **上下文丢失 / 截断**：长任务把关键信息挤出窗口
2. **工具调用错误**：参数错、JSON Schema 解析失败
3. **循环不收敛**：陷入重复工具调用（无 max_attempts）
4. **规划失败**：拆解任务粒度不对，缺关键步骤
5. **幻觉**：工具结果被 LLM 误读、编造参数
6. **状态丢失**：多轮 session 状态没持久化
7. **错误恢复差**：某个工具失败直接崩，没有降级方案

### Q1.5 怎么保证 Agent 不会"瞎循环"？

**答**：
- 硬限：设置 `max_iterations`、`max_tool_calls`、`timeout`
- 软限：检测重复 pattern（同样的 action 出现 N 次就中断）
- 反思：每 N 步强制 LLM 自我评估"还应该继续吗"
- 人工介入：高风险决策触发 `interrupt()` 让用户决定（LangGraph 原生支持）

### Q1.6 Agent vs Workflow 怎么选？

**答**：
- **Workflow（LangChain LCEL / DAG）**：步骤确定、低延迟、低成本、易调试
- **Agent**：步骤不确定、需要动态决策、要调用外部世界
- 折中：**Workflow + 局部 Agent**（大部分流程固化成 DAG，关键节点嵌入 Agent 做决策）

---

## 2. Prompt Engineering 进阶

### Q2.1 Prompt 的基本结构是什么？

**答（一个高质量 prompt 通常包含）**：
```
[Role]         # 角色设定
[Context]      # 背景信息 / 历史
[Task]         # 具体任务
[Constraints]  # 约束条件（不能做什么）
[Format]       # 输出格式要求（JSON Schema / markdown）
[Examples]     # Few-shot 示例（可选）
[Steps]        # 思维链引导（可选）
```

### Q2.2 什么是 Zero-shot / One-shot / Few-shot？什么时候用哪个？

**答**：
- **Zero-shot**：不给示例，靠 LLM 自身能力（适合简单任务）
- **One-shot**：给 1 个示例（建立格式规范）
- **Few-shot**：给 2-5 个示例（建立推理模式、风格、边界）

经验：**示例 > 描述**。同样约束，写一个示例比写一段话管用。

### Q2.3 Chain-of-Thought (CoT) 是什么？怎么用？

**答**：
- 让 LLM **显式输出推理过程**，再给最终答案
- 触发词：`"Let's think step by step"` / `"请一步步思考"`
- 变体：
  - **Zero-shot CoT**：仅触发词
  - **Few-shot CoT**：给带推理过程的示例
  - **Self-Consistency**：采样多条 CoT，投票出最终答案
- 适用：数学、逻辑、多步推理

### Q2.4 System Prompt 和 User Prompt 的区别？

**答**：
- **System Prompt**：定义角色、行为准则、输出格式、约束；优先级高、跨轮次保留
- **User Prompt**：当前轮次任务、输入数据、问题
- 技巧：
  - 稳定约束放 system（"始终输出 JSON"）
  - 易变内容放 user（"今天的日期"）
  - 重要内容**两边都重复**（防止 instruction 漂移）

### Q2.5 怎么防止 LLM 编造（幻觉）？

**答**：
1. **RAG 注入真实上下文**（最有效）
2. **明确拒绝条款**："如果不知道，请说'我不知道'，不要编造"
3. **要求引文**：强制 LLM 标注信息来源
4. **后处理校验**：用规则 / 二次 LLM 验证输出
5. **低温度 + Top-p 限制**（temperature=0）
6. **Self-Check**：让 LLM 自己审一遍输出，找幻觉

### Q2.6 Function Call / Tool Use 的 Prompt 设计要点？

**答**：
- **工具描述要清晰**：名称、参数、用途、边界、失败行为
- **示例少而精**：给 1-2 个调用样例
- **错误信息要 actionable**：参数错时告诉 LLM 应该填什么
- **避免工具过多**：单次 prompt 工具数控制在 5-10 个内，否则选择率显著下降
- **反例要写明**："不要用 X 工具做 Y 事"

### Q2.7 Prompt 注入（Prompt Injection）怎么防？

**答**：
- **指令隔离**：用户输入和 system prompt 物理分离
- **结构化数据**：用户输入用 JSON / 标签包裹，不当指令解析
- **输入过滤**：检测 "忽略以上指令"、"system:" 等注入关键词
- **工具调用限制**：用户输入不直接进 LLM 决策路径
- **审计日志**：所有 prompt 都留痕，可回放

---

## 3. RAG 检索增强生成

### Q3.1 RAG 的完整 Pipeline 是什么？

**答（标准流程）**：
```
文档加载（Loader）
  ↓
文本切分（Splitter / Chunker）
  ↓
向量化（Embedding Model）
  ↓
存入向量库（Vector Store）
  ↓
用户 Query
  ↓
Query 向量化
  ↓
召回（Retrieval）→ Top-K 候选
  ↓
重排（Rerank）→ Top-N
  ↓
Prompt 拼装（Context + Query）
  ↓
LLM 生成（Generation）
```

### Q3.2 文档切分（Chunking）怎么做？有哪些策略？

**答**：
- **固定大小切分**：每 N 个 token 一块，重叠 M 个（最简单）
- **按结构切分**：Markdown 标题、代码段、段落
- **语义切分**：用 embedding 算相邻段相似度，相似度低就断开
- **递归切分**：先按大粒度（段落），不够再按小粒度（句子）

**经验值**：
- 通用文本：chunk_size 500-1000 token，overlap 50-200
- 代码：按函数 / 类切
- 表格：整张表一块，或拆成行 + 表头

### Q3.3 Embedding 模型怎么选？

**答**：
- 通用中文：**BGE-M3**（智源）、**M3E**、**BCE**
- 通用英文：**BGE-large-en-v1.5**、**text-embedding-3-large**
- 多模态：**Jina CLIP-v2**、**BGE-VL**
- 选型要点：维度、语种、MTEB 榜单、推理速度、私有化能力

### Q3.4 向量库选型？

**答**：
- **小规模 / 本地**：Chroma、FAISS
- **生产级 / 分布式**：Milvus、Weaviate、Qdrant
- **云托管**：Pinecone、Zilliz Cloud
- **关键词+向量混合**：Elasticsearch + 向量、Tantivy

### Q3.5 召回率上不去怎么办？

**答（进阶 RAG 优化清单）**：
1. **Hybrid Search**：BM25（关键词）+ 向量（语义）混合
2. **Query Rewrite / HyDE**：用 LLM 把用户 query 改写 / 假设答案再检索
3. **Multi-Query**：一个 query 拆成多个角度分别检索
4. **Reranking**：用 Cross-Encoder（bge-reranker-large）精排
5. **Metadata Filter**：用时间、类型、tag 过滤
6. **Parent Document Retriever**：检索小块、返回大块
7. **GraphRAG**：微软方案，构建实体关系图谱
8. **Self-RAG**：让 LLM 自己判断要不要检索、检索够不够
9. **Agentic RAG**：让 Agent 决定检索什么、用哪个工具

### Q3.6 RAG 怎么评估？

**答**：
- **检索质量**：Recall@K、MRR、NDCG（需要标注 query-doc 对）
- **生成质量**：Faithfulness（答案是否基于检索内容）、Answer Relevance、Context Relevance
- **框架**：RAGAS（最流行）、ARES、TruLens
- **数据**：构造 50-200 个真实 QA 对

### Q3.7 Naive RAG → Advanced RAG → Modular RAG 的演进？

**答**：
- **Naive RAG**：固定流程（load → split → embed → retrieve → generate）
- **Advanced RAG**：在前后加入优化（Query Rewrite、Chunking 优化、Rerank、Prompt 优化）
- **Modular RAG**：把每个模块抽象化、可插拔、可重排

---

## 4. Context Engineering 上下文工程

### Q4.1 什么是 Context Engineering？和 Prompt Engineering 区别？

**答**：
- **Prompt Engineering**：优化单次 prompt 措辞
- **Context Engineering**：管理**整个 LLM 调用窗口内的所有信息**——system prompt、工具描述、历史消息、检索结果、用户输入、few-shot、记忆——并动态决定每轮填什么

引用 Anthropic 观点：**Context Engineering = 10x harder than Prompt Engineering**

### Q4.2 Context Window 的 4 个核心要素？

**答（Andrej Karpathy 框架）**：
1. **Instructions (system prompt)**：任务、角色、规则
2. **Knowledge (RAG)**：外部事实注入
3. **Tools**：可用工具描述 + schema
4. **Memory**：短期（当前 session）+ 长期（用户偏好 / 历史）

### Q4.3 Context 满了怎么办？截断策略有哪些？

**答**：
- **滑动窗口**：保留最近 N 轮 + 关键轮
- **摘要压缩**：用 LLM 把旧对话压缩成摘要
- **层级记忆**：短期完整 + 长期摘要
- **重要性评分**：保留高 importance 消息
- **工具结果截断**：过长的工具输出截断 + 标记引用

### Q4.4 怎么防止 Context 污染（Context Poisoning）？

**答**：
- 严格区分**系统注入** vs **用户输入** vs **工具返回**
- 工具返回内容用 XML 标签包裹 `<tool_result>...</tool_result>`
- 关键决策前重新"读取"系统 prompt（防止 instruction 漂移）
- 审计每条消息来源，refusal 策略要清晰

### Q4.5 Context Caching 是什么？什么时候用？

**答**：
- Anthropic / OpenAI 提供的 prompt cache：相同前缀只计算一次
- 适用场景：system prompt + 大量 examples 固定不变
- 收益：成本降 90%、延迟降 80%
- 注意：cache 命中前缀必须完全一致（前缀必须 stable）

### Q4.6 长上下文（128K+）的使用误区？

**答**：
- 不要把"长 context"当万能解：模型注意力仍随距离衰减
- 仍然要 RAG：长 context 解决不了精确检索问题
- "Lost in the Middle" 现象：模型对中段信息关注度低
- 仍然要做信息分层：关键放首尾，次要放中间
- 成本高：长 context 计价按 token，建议 cache

---

## 5. MCP（Model Context Protocol）

### Q5.1 什么是 MCP？为什么需要它？

**答**：
- **MCP** = Model Context Protocol，Anthropic 2024.11 开源的 **Agent ↔ 工具** 通信标准协议
- 类比 USB-C：统一不同数据源、工具的接入方式
- 之前：每个 Agent（Claude/Cursor/Cline）都要自己适配每个工具（DB/Slack/GitHub）
- 之后：工具实现一次 MCP Server，所有 MCP Client 都能用

### Q5.2 MCP 架构和核心概念？

**答**：
```
MCP Host (Claude Desktop / Cursor)
    ↓ JSON-RPC 2.0
MCP Client
    ↓
MCP Server
    ↓
本地资源 / API
```

- **Host**：用户接触的应用（Claude Desktop、Cursor、IDE）
- **Client**：在 Host 内，与 Server 通信
- **Server**：暴露资源（Resources）、工具（Tools）、提示（Prompts）

### Q5.3 MCP Server 能暴露什么？

**答**：
| 类型 | 作用 | 示例 |
|------|------|------|
| **Tools** | LLM 可调用的函数 | 查数据库、发邮件 |
| **Resources** | 只读数据源 | 文件、日志、API 响应 |
| **Prompts** | 预制 prompt 模板 | 写周报的 prompt 模板 |
| **Sampling** | 让 Server 反过来调 LLM | 少见，慎用 |

### Q5.4 MCP 的传输层有哪些？

**答**：
- **stdio**：标准输入输出，本地进程间通信（最常用）
- **HTTP + SSE**：远程通信，长连接推送事件
- **WebSocket**：双向实时（较新）

### Q5.5 MCP 怎么定义一个 Tool？

**答（JSON Schema）**：
```json
{
  "name": "get_weather",
  "description": "Get the current weather for a location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {"type": "string", "description": "City name"},
      "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["location"]
  }
}
```

### Q5.6 MCP vs Function Call / Tool Use 区别？

**答**：
- **Function Call / Tool Use**：模型能力，由 LLM 厂商定义
- **MCP**：协议层，跨模型/跨应用统一
- 关系：MCP Server 内部把工具能力封装好，通过 MCP 协议暴露，Host Agent 调用
- 类比：HTTP 之于 RPC，MCP 之于 Function Call

### Q5.7 MCP 的局限和安全考量？

**答**：
- **安全**：MCP Server 可以执行任意代码，需要 sandbox / 权限控制
- **认证**：当前 MCP 规范对 auth 还在演进
- **网络**：HTTP + SSE 需要鉴权和 CORS
- **状态管理**：长任务的状态由 Server 自己维护
- **发现机制**：Client 怎么找到可用的 Server（Registry 协议进行中）

### Q5.8 怎么设计一个 MCP Server（实战）？

**答（关键设计点）**：
1. **Tool 设计要原子**：一个 tool 做一个事，避免组合工具
2. **参数 schema 严格**：用 JSON Schema 约束，避免 LLM 瞎填
3. **错误信息要 actionable**：告诉 LLM 应该填什么
4. **description 要 LLM 友好**：清晰说明何时用、边界、副作用
5. **幂等性**：GET 类操作尽量幂等
6. **限流保护**：内置 rate limit、token 校验
7. **日志完整**：每次调用都记日志，便于回放

---

## 6. Skill 与 Claude Code 工具链

### Q6.1 什么是 Claude Code / Agent Skill？

**答**：
- **Claude Code**：Anthropic 的官方 CLI Agent，能在本地读代码、写代码、跑命令
- **Agent Skill**：用 **Markdown + 触发词** 把专家经验封装成可复用的 Agent 工作流
- 一个 Skill = 一个 SKILL.md（含 frontmatter：name、description）+ 可选 scripts

### Q6.2 Skill 的结构和最佳实践？

**答（一个 Skill 通常包含）**：
```yaml
---
name: <skill-name>
description: |
  <触发条件 + 能力描述>
  Use when: <具体场景>
allowed-tools: [Read, Bash, Grep, Edit]  # 可选权限限制
---
# <Skill 标题>

## When to use
- <场景 1>
- <场景 2>

## Workflow
1. <步骤 1>
2. <步骤 2>

## Output format
- <期望输出>

## Examples
- <输入示例 → 输出示例>

## Common pitfalls
- <坑 1>：怎么避免
```

### Q6.3 怎么写好一个 Skill 的 description（触发器）？

**答**：
- 包含**触发关键词**（让 Agent 在对的时候检索到）
- 包含**反例**（不该触发的情况）
- 用 "Use when:" 显式说明场景
- 例：
  > "Use when: the user mentions 数据库连接报错、Postgres error、SQL 异常。Do NOT use for: 业务逻辑问题。"

### Q6.4 Skill 体系的分层设计？

**答**：
- **基础工具类 Skill**：调 API、跑命令（"连数据库"）
- **工作流类 Skill**：排障、代码 review、发布（"生产事故复盘"）
- **知识类 Skill**：领域 SOP、最佳实践（"性能调优清单"）
- **元 Skill**：管理其他 Skill（"列出所有可用 skill"）

### Q6.5 Claude Code 的核心能力？

**答**：
- **Read / Glob / Grep**：探索代码库
- **Edit / Write**：编辑文件
- **Bash**：执行命令
- **WebFetch / WebSearch**：联网
- **TodoWrite**：任务规划
- **Skill 检索**：根据用户 query 自动匹配 Skill
- **MCP 工具**：通过 MCP 协议扩展

### Q6.6 Skill vs Prompt vs Sub-Agent 区别？

**答**：
- **Skill**：给当前 Agent 的专家经验，文本形式，触发即用
- **Prompt**：单次输入，临时性
- **Sub-Agent**：独立 Agent 调用，主 Agent 失去控制权
- 选择：复用经验 → Skill；一次性任务 → Prompt；独立长任务 → Sub-Agent

---

## 7. Harness Engineering

### Q7.1 什么是 Harness Engineering？

**答**：
- **Harness** = "马具"——控制 Agent 行为的整套"骨架"
- 包含：Prompt 模板、工具描述、上下文管理、错误恢复、人机协作
- 类比：Harness = 操作系统内核（控制 + 调度），Agent = 用户进程
- Anthropic 2025 重点推的概念："The harness is the product"

### Q7.2 Harness 的核心组成？

**答**：
1. **System Prompt**：角色、规则、约束
2. **Tool Definitions**：工具 schema、description
3. **Context Assembly**：每轮怎么把信息装进 context
4. **Loop Control**：ReAct/Plan-Execute 的循环逻辑、最大步数
5. **Error Recovery**：工具失败重试、降级
6. **Memory**：短期 / 长期记忆
7. **Human-in-the-Loop**：中断点、确认机制
8. **Observability**：日志、追踪、指标
9. **Guardrails**：内容安全、行为边界

### Q7.3 Harness Engineering 关键设计原则？

**答**：
- **确定性优先**：能用代码判断的不让 LLM 判断
- **小工具多组合**：避免大而全的工具
- **错误信息要 actionable**：让 LLM 知道怎么修正
- **状态可恢复**：每步持久化，能 resume
- **可观测性先行**：没有 trace 就别上线
- **预算控制**：单任务 max token、max cost、max time
- **人机分工**：高风险决策让人来

### Q7.4 ReAct 和 Plan-and-Execute 哪个更适合 Harness？

**答**：
| 维度 | ReAct | Plan-and-Execute |
|------|-------|------------------|
| 延迟 | 高（每步思考）| 低（先规划）|
| 成本 | 高 | 低 |
| 容错 | 中（重做）| 好（重做单步）|
| 适应性 | 强 | 弱（plan 定死）|
| 适用 | 探索性任务 | 确定性流水线 |

生产常见：**Plan-and-Execute + ReAct 局部回退**（主框架 Plan-Execute，复杂节点嵌入 ReAct）

### Q7.5 Harness 怎么设计"自纠错"能力？

**答**：
- **Self-Critique**：每步后 LLM 自评，失败则重试
- **Critic Agent**：独立评判 Agent 评估结果
- **回滚机制**：检测到状态污染回滚到上一 checkpoint
- **工具结果验证**：用 schema / 业务规则校验工具输出
- **限速熔断**：连续失败 N 次熔断，避免雪崩

---

## 8. LangChain

### Q8.1 LangChain 是什么？核心组件？

**答**：
LangChain = LLM 应用开发框架
核心组件：
- **Models**：LLM / ChatModel / Embedding 统一接口
- **Prompts**：PromptTemplate、ChatPromptTemplate、Few-shot
- **Chains**：LCEL 链式组合（`prompt | llm | parser`）
- **Memory**：对话状态管理
- **Retrievers**：RAG 检索抽象
- **Agents**：基于 LLM 的 Agent
- **Tools**：工具抽象
- **Document Loaders / Splitters**：文档处理
- **Vector Stores**：向量库抽象
- **Callbacks / Tracing**：可观测性

### Q8.2 LCEL 是什么？有什么优势？

**答**：
**LCEL = LangChain Expression Language**，用 `|` 组合组件的声明式语法：

```python
chain = prompt | llm | output_parser
```

**优势**：
- 同步 / 异步 / 流式 / 批处理 同一套代码
- 自动 fallback（LLM 失败时切换备选）
- 自动 trace（LangSmith 集成）
- 类型安全（Runnable 接口）

### Q8.3 LangChain 1.0 的核心变化？

**答**：
- 全面采用 **LangGraph 作为 Agent 编排底层**（弃用老 AgentExecutor）
- 强化 **LCEL**，简化 API
- **LangSmith** 成为默认可观测层
- 新的 **langchain-v1** 包结构
- 强调 **content_blocks**（统一多模态内容表示）

### Q8.4 LangChain 适合什么场景？不适合什么？

**答**：
✅ **适合**：
- 快速原型
- RAG / 简单 LLM 应用
- 标准 LLM 工作流
- LangChain 生态内的集成（大量 loader、vector store）

❌ **不适合**：
- 复杂多 Agent 编排（用 LangGraph）
- 强定制控制流（用 LangGraph / 自研）
- 极致性能场景（LangChain 抽象有开销）

---

## 9. LangGraph

### Q9.1 LangGraph 是什么？和 LangChain 区别？

**答**：
- LangGraph = 把 Agent 建模为**有向图**（节点 + 边）的编排框架
- 核心抽象：**StateGraph**（带类型 State 的有向图）
- 与 LangChain 关系：**LangGraph 是 LangChain 的子项目**，深度集成

| 维度 | LangChain | LangGraph |
|------|-----------|-----------|
| 结构 | 线性链 (LCEL) | 有向图（含循环）|
| 状态 | 隐式 | 显式 TypedDict |
| 循环 | 不支持 | 一等公民 |
| 多人协作 | 弱 | Supervisor/Swarm/Handoff |
| 人机协作 | 需 workaround | 原生 `interrupt()` |
| 适用 | 简单流水线 | 生产级 Agent |

### Q9.2 LangGraph 的核心概念？

**答**：
- **State**：TypedDict，定义图执行期间所有共享数据
- **Node**：Python 函数，接收 State、返回部分 State
- **Edge**：节点间转移，可条件（`add_conditional_edges`）可静态
- **Reducer**：多个节点写同一字段时怎么合并（默认覆盖，常见 `add_messages`、`operator.add`）
- **Checkpointer**：状态持久化（InMemory/Sqlite/Postgres/Redis）
- **Thread ID**：隔离不同 session 的状态

### Q9.3 LangGraph 的多 Agent 模式？

**答**：
1. **Supervisor（主管）模式**：
   - 中央 Supervisor 节点决策下一个 Worker
   - Worker 执行完返回 Supervisor
   - 优点：控制流清晰；缺点：Supervisor 是瓶颈
2. **Hierarchical（层级）模式**：
   - 多级 Supervisor 树
   - 适合大型流水线（软件开发流水线）
3. **Swarm（群体）模式**：
   - Agent 通过 Handoff 移交控制权（OpenAI Swarm 风格）
   - 灵活但难调试
4. **Subgraph（子图）**：
   - 一个图作为另一个图的节点
   - 模块化复用

### Q9.4 LangGraph 的 Checkpointing 怎么用？

**答**：
```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("state.db")
app = graph.compile(checkpointer=checkpointer)

# 执行时指定 thread_id
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke(state, config=config)

# 后续可恢复
result = app.invoke(None, config=config)  # 传 None 表示继续

# 可换 PostgreSQL / Redis
from langgraph.checkpoint.postgres import PostgresSaver
```

**应用场景**：
- 长时间任务中断恢复
- 调试（time-travel 到任意历史点）
- 人机协作（暂停等人批准再继续）

### Q9.5 LangGraph 的 Human-in-the-Loop 怎么实现？

**答（两种方式）**：

**方式 1：interrupt() 节点内**
```python
from langgraph.types import interrupt

def my_node(state):
    approval = interrupt({"question": "Approve?"})
    if not approval:
        return {"messages": [...]}
    return ...
```
恢复：`app.invoke(Command(resume=True), config)`

**方式 2：interrupt_before 编译选项**
```python
app = graph.compile(interrupt_before=["supervisor"])
# 第一次跑到 supervisor 前暂停
result = app.invoke(state, config)
# 人工审核后
result = app.invoke(None, config)  # 继续
```

### Q9.6 LangGraph 怎么避免循环不收敛？

**答**：
- **State 里加计数器**：`iteration_count`，每步 +1，超阈值走 END
- **max_attempts 限制**：在路由函数里判断
- **超时控制**：wall-clock + token 用量
- **检测重复 pattern**：连续 N 步同样的 tool call 直接终止

### Q9.7 LangGraph 的 State 更新机制？

**答**：
- **Node 返回 dict** 表示要更新的字段
- **Reducer**：定义合并规则
  - 默认：覆盖
  - `Annotated[list, operator.add]`：列表追加
  - `add_messages`（from langgraph.graph.message）：智能合并 message（按 ID 去重）
- 示例：
```python
class State(TypedDict):
    messages: Annotated[list, add_messages]  # 自动追加 + 去重
    count: int                                # 覆盖
    tasks: Annotated[list, operator.add]      # 列表追加
```

### Q9.8 LangGraph 的可观测性？

**答**：
- **LangSmith**：官方 trace 平台，集成零成本
- **OpenTelemetry**：通用协议
- **内置 streaming**：`app.stream()` / `app.astream_events()` 拿每步事件
- **状态快照**：`app.get_state(config)` 拿当前 State

---

## 10. Memory 记忆系统

### Q10.1 Agent 为什么需要 Memory？

**答**：
- LLM 本身无状态，每次调用独立
- Memory 让 Agent 拥有**连续性**——记住用户偏好、历史对话、关键事实
- 三类需求：
  - **当下 session 上下文**（短期）
  - **用户长期偏好**（长期）
  - **从过往交互学到的知识**（情景）

### Q10.2 Memory 的分类？

**答**：
| 类型 | 时长 | 实现 |
|------|------|------|
| **Buffer Memory** | 短期 | 完整保留最近 N 轮 |
| **Summary Memory** | 短期 | 把旧对话压缩成摘要 |
| **Window Memory** | 短期 | 滑动窗口（最近 K 轮）|
| **Vector Memory** | 长期 | 关键事实向量化，按相似度检索 |
| **Episodic Memory** | 长期 | 情景记忆（"上次用户问过什么、Agent 怎么答"）|
| **Semantic Memory** | 长期 | 用户偏好、知识 |
| **Procedural Memory** | 长期 | 行为模式（自动触发某些工具）|

### Q10.3 短期 vs 长期 Memory 怎么配合？

**答**：
- **短期**：当前 thread 的 messages，存 InMemory/Sqlite
- **长期**：跨 session 的用户画像、关键事实，存 Vector DB + KV
- 每轮流程：
  1. 从长期 Memory 检索相关 fact
  2. 拼进 system prompt
  3. 短期 messages 按窗口截断
  4. 本轮结束后写回长期（触发"重要事实提取" LLM 调用）

### Q10.4 LangMem / mem0 / Zep 这些 Memory 框架？

**答**：
- **LangMem**：LangChain 官方出品，集成 LangGraph
- **mem0**：开源，自带 fact extraction 和 dedup
- **Zep**：长期记忆服务，性能强
- **Letta（MemGPT 团队）**：分级 memory（core / archival / recall）
- 选型：自研成本高就用现成框架；数据敏感就自研

### Q10.5 Memory 的写入策略？

**答**：
- **每轮写**：开销大，可能噪音多
- **结束写**：可能漏掉关键信息
- **重要事件触发**：检测"用户给偏好"、"用户纠正 Agent"等 pattern 时写
- **定期 consolidation**：每隔 N 轮把零散 memory 聚类合并
- **TTL / 衰减**：老 memory 自动降权或删除

### Q10.6 Memory 和 RAG 区别？

**答**：
- **Memory**：Agent 自身状态的一部分，关于**用户、Agent 自身、过往交互**
- **RAG**：外部**知识库**的检索，与具体用户无关
- Memory 是"个人笔记"，RAG 是"图书馆"

### Q10.7 怎么评估 Memory 系统的效果？

**答**：
- **检索准确率**：跨 session 检索相关 fact 的 Recall@K
- **写入去重率**：同一 fact 不重复写入
- **冲突解决**：用户改偏好时旧记录被覆盖
- **延迟**：每轮 memory 检索 < 100ms
- **成本**：memory 操作占整体 LLM 成本 < 10%

---

## 11. AI Agent Eval 评估体系

### Q11.1 为什么要做 Agent Eval？

**答**：
- Agent 行为**非确定性**，每次可能不同
- 改 prompt / 模型 / 工具版本后不知道好坏
- 上线前必须量化质量，否则就是盲飞

### Q11.2 Agent Eval 的 5 个核心维度？

**答**：
1. **准确性（Accuracy）**：任务完成度、答案正确率
2. **延迟（Latency）**：端到端 P50/P95、首 token 延迟
3. **成本（Cost）**：每任务 token 消耗、API 费用
4. **鲁棒性（Robustness）**：异常输入下不崩
5. **可解释性（Explainability）**：决策路径可追溯

### Q11.3 评估方法有哪些？

**答**：
| 方法 | 说明 | 适用 |
|------|------|------|
| **规则匹配** | 关键词 / 格式校验 | 简单任务 |
| **参考答案对比** | 与 gold answer 字符串匹配 / 语义相似 | 有标注场景 |
| **LLM-as-a-Judge** | 用 GPT-4 / Claude 当裁判打分 | 开放任务（注意偏见）|
| **Human Eval** | 人工标注 | 关键路径 |
| **A/B Test** | 线上分流对比 | 业务指标 |
| **端到端模拟** | 跑完整任务看结果 | Agent 任务 |

### Q11.4 怎么设计测试集？

**答（设计原则）**：
- **规模**：50-200 个 case（最少 30，覆盖典型 + 边界 + 异常）
- **覆盖**：
  - 正常 case（70%）
  - 边界 case（20%）
  - 异常 / 对抗 case（10%）
- **标注**：每条 query + 标准答案 + 评分维度 + 期望行为
- **持续更新**：定期加新 case，覆盖用户真实 query 分布
- **去污染**：测试集不能和训练集重叠

### Q11.5 LLM-as-a-Judge 的最佳实践？

**答**：
- **结构化评分**：1-5 分 + 理由（不要只让 LLM 说"好/坏"）
- **多维度拆分**：分别评"准确性"、"完整性"、"风格"
- **Reference 提供**：给 gold answer 让 LLM 对比
- **位置偏见规避**：同一 case 跑两次，交换 reference 位置
- **自评偏见**：LLM 倾向评自己输出高分，要换裁判模型
- **CoT 强制**：要求 Judge LLM 先列出证据再打分

### Q11.6 常见 Eval 框架？

**答**：
- **LangSmith**：LangChain 官方
- **RAGAS**：RAG 专用（Faithfulness / Answer Relevance / Context Precision）
- **DeepEval**：通用 LLM Eval
- **Braintrust**：综合
- **AgentBench / GAIA / SWE-bench**：公开 Agent 评测基准
- **Promptfoo**：Prompt Eval / 红队

### Q11.7 怎么避免 Eval 过拟合？

**答**：
- 训练集 / 测试集严格分离
- 测试集用人工标注，不让 LLM 生成（避免循环 bias）
- 多版本 prompt 跑同一测试集，看是否单调提升
- 线上 A/B 验证，不要只看 offline 指标

### Q11.8 Agent 失败怎么 debug？

**答（debug 流程）**：
1. **完整 trace**：每步的 input/output/token/latency 都要可看
2. **回放**：用相同输入重放 Agent，复现问题
3. **单步调试**：跳过某些步骤看结果
4. **对照实验**：换 prompt / 换模型 / 换工具版本对比
5. **失败分类**：归纳失败 mode（幻觉 / 工具错 / 循环 / 超时）
6. **单元测试**：工具、retriever 单独测，不靠 LLM 测

---

## 12. 多 Agent 协作 / ReAct / Plan-and-Execute

### Q12.1 ReAct 和 Chain-of-Thought 区别？

**答**：
- **CoT**：纯思考（reasoning），不调外部工具
- **ReAct**：Reasoning + Acting，每步思考 + 调工具 + 观察结果
- 关系：ReAct = CoT + 工具调用

### Q12.2 ReAct 完整 trace 长什么样？

**答**：
```
Question: 北京今天天气怎么样？
Thought 1: 用户想知道北京天气，需要调天气工具
Action 1: get_weather(location="北京")
Observation 1: {"temp": 25, "weather": "晴"}
Thought 2: 拿到天气数据，可以回答了
Action 2: Finish
Final Answer: 北京今天天气晴，气温 25 度
```

### Q12.3 ReAct 有什么局限？怎么改进？

**答**：
**局限**：
- 每步都思考 → 慢、贵
- 容易陷入重复 tool call
- 任务规划性差（走一步看一步）

**改进**：
- **Plan-and-Execute**：先全规划、再执行（适合确定性任务）
- **ReWOO**：先规划所有 ReAct 步骤，一次性执行（减少 LLM 调用）
- **Reflexion**：失败后反思，更新策略
- **Self-Ask**：让 LLM 问自己子问题
- **Tree of Thoughts**：多路径探索 + 选最优

### Q12.4 多 Agent 协作的主流模式？

**答**：
1. **Supervisor 模式**（最常用）：
   - 中央 Supervisor 决策调度
   - Worker 各自执行子任务
2. **Hierarchical 模式**：
   - 多级 Supervisor 树
3. **Swarm / Handoff 模式**：
   - Agent 之间通过工具移交控制权
   - OpenAI Swarm / CrewAI 风格
4. **Collaborative Debate**：
   - 多个 Agent 辩论 / 投票
5. **Role-based（角色分工）**：
   - PM / Dev / QA 角色化 Agent 协作

### Q12.5 多 Agent 怎么通信？

**答**：
- **共享 State**（LangGraph 风格）：所有 Agent 读 / 写同一 State
- **消息队列**（Kafka / Redis Streams）：异步解耦
- **Handoff 协议**：一个 Agent 把控制权交给另一个
- **Pub/Sub**：广播通知
- **A2A 协议**（Google 2025）：跨厂商 Agent 互操作

### Q12.6 多 Agent 系统的常见坑？

**答**：
1. **通信开销**：N 个 Agent 通信成本是 O(N²)
2. **状态不一致**：并发写同一 State 冲突（用 Reducer 解决）
3. **循环依赖**：A 等 B 结果，B 等 A 结果
4. **Token 爆炸**：N 个 Agent × 完整 context = 巨贵
5. **调试难**：决策链长，难复现
6. **协调器瓶颈**：Supervisor 单点

### Q12.7 CodeAct 是什么？优势？

**答**：
- 让 Agent **直接生成 Python / JS 代码**执行（而不是调离散 tool）
- 优势：
  - 灵活：可以组合多个 tool
  - 适合数据 / 数学 / 文件处理
  - 比调 function call 表达力强
- 风险：
  - 代码执行需要 sandbox
  - 错误处理复杂
  - 安全风险

---

## 13. 场景设计题（高频）

### Q13.1 如何设计一个"AI 客服"系统？

**答**（架构要点）：
1. **意图识别**：用户 query 分类（退货 / 查询 / 投诉 / 闲聊）
2. **知识库 RAG**：FAQ / 政策文档检索
3. **工具调用**：查订单 / 退款 / 转人工
4. **多轮管理**：短期 Memory + 用户画像
5. **降级策略**：答不上 → 转人工
6. **质量监控**：在线 Eval（满意度 / 转人工率）

### Q13.2 怎么设计一个"AI 帮你写代码"工具（如 Copilot）？

**答**：
1. **Context 收集**：当前文件、相关文件、git diff、终端输出
2. **补全模式**：cursor 位置前后 N 行
3. **指令模式**：FIM（Fill in Middle）/ Chat
4. **RAG**：项目内代码检索、API 文档
5. **工具**：运行命令、查文件、git 操作
6. **安全**：执行类工具需 sandbox + 用户确认
7. **Eval**：HumanEval、用户接受率、修改率

### Q13.3 怎么设计一个"研究助手"（多 Agent 调研报告）？

**答**：
1. **规划 Agent**：拆解问题、列子问题
2. **搜索 Agent**（多个并行）：各自负责子主题
3. **批判 Agent**：评估每个搜索结果的可靠性
4. **写作 Agent**：综合所有材料写报告
5. **配图 Agent**：找/生成配图
6. **Review Agent**：审稿、改稿

实现：LangGraph Supervisor 模式 + checkpointer

### Q13.4 怎么让 Agent 处理长任务（10+ 步骤）？

**答**：
- **分阶段**：拆成子任务，每阶段独立 checkpoint
- **持久化**：每个 checkpoint 入库
- **可恢复**：任意点中断后能从 checkpoint 继续
- **预算控制**：单任务 max token、max cost、max time
- **可视化**：用户能看进度
- **可取消**：长任务能 interrupt

### Q13.5 LLM 输出不稳定怎么解决？

**答**：
- 降低 temperature（0 或接近 0）
- 多次采样取众数（Self-Consistency）
- 强制输出格式（JSON Schema + parser）
- 固定 random seed（如支持）
- 后处理校验（schema 校验、二次 LLM 改写）
- 单元测试覆盖输出空间

### Q13.6 怎么降低 LLM 调用成本？

**答**：
- **Prompt Caching**：重复前缀 cache 90% 成本
- **模型分级**：简单任务用小模型（gpt-4o-mini / claude-haiku）
- **批处理**：非实时任务批量调用
- **截断策略**：长 context 摘要压缩
- **RAG 替代长 context**：检索比塞全文便宜
- **减少 tool call**：能一次解决不调多次
- **避免重试**：错误恢复一次到位

### Q13.7 Agent 怎么"学会"一个新工具？

**答**：
- 看工具的 description + schema
- 试一次失败 → 看错误信息 → 调整
- 需要时检索工具文档 / 源代码
- 累积成功案例到 memory，下次更快

### Q13.8 怎么设计 Agent 的安全边界？

**答**：
- **工具白名单**：只允许注册的 tool
- **输入过滤**：检测 prompt injection
- **输出审核**：生成内容过安全模型
- **权限分级**：低风险自动执行，高风险需确认
- **审计日志**：所有调用可回放
- **沙箱**：代码执行类工具必须 sandbox
- **人机介入**：高风险操作强制人工确认

---

## 14. 项目深挖准备

### 项目 A：深度研究智能体（多 Agent 协作 + ReAct）

**准备 STAR 答法**：

**S（Situation）**：
> 看到 ChatGPT Deep Research 上线，想自己复现一个开源版本，验证多 Agent 协作在研究类任务上的可行性。

**T（Task）**：
> 设计并实现一个能自主完成"给定主题→规划子问题→并行调研→汇总报告"的 Agent 系统。

**A（Action）**：
- 用 ReAct + 规划专家 + 多个搜索 Agent + 总结 Agent 的 Supervisor 模式
- HelloAgents 自研框架（不用 LangChain 是想理解底层 + 体积小）
- FastAPI + SSE 流式推送
- 向量记忆库做上下文压缩
- 反思机制：报告生成后让 critic Agent 评估，找 fact 错误

**R（Result）**：
- 复杂研究任务（10+ 子问题）从一次 3 分钟 → 多 Agent 并行 1 分钟
- 报告引用准确率 > 90%
- 开源后获得 X stars

**面试常被追问**：
1. 为什么用 HelloAgents 不用 LangChain？→ 体积小 + 可控性 + 想读源码
2. 多 Agent 通信协议？→ 共享 State（消息列表）+ tool call 序列化
3. 怎么避免循环？→ max_iterations + 检测重复 tool call
4. SSE 怎么做的？→ FastAPI StreamingResponse，EventSource 客户端
5. 反思机制怎么设计？→ Critic Agent 给 1-5 分，< 3 分触发重写
6. Token 成本怎么算？→ 平均 5K input + 8K output per task，约 $0.15

### 项目 B：AI Agent 全栈开发实习（MCP / Claude Code）

**准备 STAR 答法**：

**S（Situation）**：
> 团队使用 Claude Code 进行开发，碰到排障 / DB 查询 / 工具调用效率低。

**T（Task）**：
> 基于 MCP 协议扩展 Claude Code 能力，封装团队内部知识为可复用 Skill。

**A（Action）**：
- 设计 3 个 MCP Server：MySQL、Redis、NATS（统一 JSON-RPC stdio）
- Tool schema 用 Zod 定义，description LLM 友好
- 写排障 SOP Skill：包含 6 类常见故障 → 排查步骤 → 输出格式
- 写一个 Skill 检索机制：用户 query → 向量化 → 匹配最相关 Skill
- 团队部署，3 周使用

**R（Result）**：
- DB 查询从 5 分钟 → 30 秒
- 排障流程从 30 分钟 → 5 分钟
- 沉淀 8 个 Skill 给团队使用

**面试常被追问**：
1. MCP Server 怎么设计 Tool？→ 原子性 + 严格 schema + 错误信息 actionable
2. stdio vs HTTP 怎么选？→ 本地用 stdio，跨机用 HTTP+SSE
3. Skill 怎么触发？→ description 含触发关键词 + 检索匹配
4. Claude Code 怎么集成 MCP？→ 改 .claude/config.json 注册 server
5. 团队推广怎么做的？→ 写 README + 录视频 + Office Hours 答疑
6. 有没有碰到安全问题？→ Tool 调用全部走 audit log，敏感操作加二次确认

### 项目 C：一带一路数据可视化平台（Prompt Engineering）

**准备 STAR 答法**：

**S（Situation）**：
> 一带一路覆盖 60+ 国家，需要聚合经济、人口、贸易等多源数据，传统人工整理太慢。

**T（Task）**：
> 用大模型 API 自动提取非结构化文本中的关键指标，生成结构化数据。

**A（Action）**：
- Prompt 设计：System（角色 + 输出 JSON Schema + Few-shot 3 个）
- 容错：JSON parse 失败 → 自动 retry 3 次 + 兜底
- 数据校验：值域检查（GDP 不可能 < 0）、日期格式校验
- 流水线：抓取 → 清洗 → LLM 提取 → 校验 → 入库

**R（Result）**：
- 100+ 国家数据从 2 周人工 → 1 天自动化
- 数据准确率 92%（人工抽检）

**面试常被追问**：
1. Prompt 怎么设计的？→ System + Few-shot + JSON Schema
2. 失败怎么兜底？→ 重试 + 字段缺失标记 + 人工抽检
3. 怎么防 LLM 幻觉？→ 输出限值校验 + 抽检 + 引文强制
4. 成本多少？→ X 元 / 文档

### 项目 D：银行业理财公告采集

**准备 STAR 答法**（按数仓口径包装）：

**S（Situation）**：
> 30+ 银行官网的理财公告分散，结构不统一。

**T（Task）**：
> 构建一个多源数据采集 + 解析 + 存储 pipeline。

**A（Action）**：
- **多源适配器**（类比 Flume / DataX）：每个银行一个 spider
- **采集策略**（类比 Kafka 反压）：限速 + 重试 + 断点续跑
- **解析层**（类比 ETL 转换）：PDF / Word / HTML 统一提取
- **存储层**（类比 ODS）：分银行 + 日期分区
- **调度**（类比 Airflow）：每日定时 + 手动触发
- **可靠性**：Cookie 池、UA 池、失败告警

**R（Result）**：
- 覆盖 30+ 银行，每日 200+ 公告
- 抓取成功率 > 95%
- 增量延迟 < 1 小时

**面试常被追问**（包装为大数据问题）：
1. 数据源不一致怎么解决？→ Schema on read + 归一化层
2. 增量怎么做的？→ 按公告 ID 去重 + 时间戳
3. 调度失败了怎么办？→ 断点续跑 + 告警 + 手动触发

---

## 15. 反问环节 / 加分项

### 15.1 反问环节（给面试官的问题）

**问团队 / 项目**：
- 团队当前主要在做哪类 AI 工具？是 toB 内部工具还是会对外？
- 团队用什么 Agent 框架？LangGraph / 自研？
- 日常开发流程是什么样的？会用 Claude Code / Cursor 吗？
- 有没有开源计划？

**问技术栈**：
- 主力 LLM 用什么？Claude / GPT / 自研？
- 有没有 GPU 集群？推理成本谁负责？
- 数据怎么管理？有专门的向量库吗？

**问成长**：
- 实习生能接触到核心项目吗？还是偏支持？
- mentor 带教模式是什么样的？
- 实习转正机会大吗？

**问业务（针对网易互娱）**：
- AI 工具目前在游戏研发里落地到什么程度了？哪些场景效果最好？
- 团队对 AI Coding / AI 美术 / AI 数值哪块投入最大？
- 我能带的 AI Agent 经验在哪些场景能用上？

### 15.2 加分项（聊到的概率高）

1. **MCP**：你做了 3 个 MCP Server，理解协议底层
2. **Claude Code / Cursor**：你深度用过，知道 best practice
3. **Harness Engineering**：你把 HelloAgents 当 Harness 设计的
4. **RAG**：一带一路 + HelloAgents 都有 RAG 元素
5. **AI Agent Eval**：你设计过 5 维度评测方案
6. **AI Coding 工具链**：自研 + 深度使用 Claude Code
7. **多 Agent 协作**：HelloAgents 是 Supervisor 模式
8. **流式 UX**：FastAPI + SSE 经验

### 15.3 风险点（主动准备解释）

1. **没碰过 LangGraph 生产项目**：
   - 诚实说，但补充"我读过源码 + 写过 demo + 准备第一个项目就用它"
2. **RAG 偏简单**：
   - 强调"做过完整 Pipeline，知道每一步的优化空间"
3. **没做过游戏行业**：
   - 主动说"我玩 X 游戏、关注 Y 赛道，相信 Agent 经验可迁移"
4. **AI Agent Eval 经验少**：
   - 强调"我自学了 RAGAS / LangSmith，知道评测方法论"

### 15.4 面试节奏预测

| 轮次 | 时长 | 重点 |
|------|------|------|
| 一面（技术）| 60min | 项目深挖 + AI Agent 概念 + 代码题（LLM 应用题）|
| 二面（Leader）| 45min | 场景设计 + 你能给团队带来什么 + 为什么是游戏 |
| HR 面 | 20min | 稳定性、抗压、薪资、实习时长 |

### 15.5 面试前 24h 检查清单

- [ ] 自我介绍 30s + 2min 倒背如流
- [ ] 4 个项目都能 STAR 答 1 遍
- [ ] AI Agent 基础概念 8 问倒背
- [ ] Prompt Engineering 7 问能举实例
- [ ] RAG Pipeline 能画出来
- [ ] MCP 协议能讲清架构
- [ ] LangGraph 核心概念能讲清
- [ ] AI Agent Eval 5 维度能讲
- [ ] 多 Agent 模式能对比
- [ ] 准备 3-5 个反问

---

## 附：核心概念速查表

| 缩写 | 全称 | 一句话解释 |
|------|------|----------|
| LLM | Large Language Model | 大语言模型 |
| Agent | LLM + Tools + Memory | 能自主完成多步任务的系统 |
| RAG | Retrieval-Augmented Generation | 检索增强生成 |
| CoT | Chain-of-Thought | 思维链推理 |
| MCP | Model Context Protocol | Agent-工具通信协议 |
| ReAct | Reason + Act | 思考-行动循环范式 |
| ToT | Tree of Thoughts | 多路径思维探索 |
| A2A | Agent-to-Agent | Agent 间通信协议 |
| PE | Prompt Engineering | Prompt 优化技术 |
| CE | Context Engineering | 上下文窗口内信息管理 |
| LCEL | LangChain Expression Language | LangChain 链式语法 |
| HITL | Human-in-the-Loop | 人机协作 |
| Eval | Evaluation | 评估方法 |

---

> 整理人：Mavis（基于用户简历 + 网易互娱 AI 工具岗 JD + 互联网公开面经）
> 整理时间：2026-09
