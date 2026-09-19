# ADR-001: LangGraph 集成架构设计

**状态**：提议中（Proposed）  
**日期**：2026-09-19  
**决策者**：开发团队  
**标签**：架构、LangGraph、多会话、状态管理

---

## 背景（Context）

### 当前问题

1. **多会话并行冲突**：
   - 单一 `loading` 状态导致会话 A 流式生成时，会话 B 被阻塞
   - 切换会话时没有中断正在进行的请求
   - 无法支持"切走后回来看到结果"的 UX

2. **状态管理混乱**：
   - 前端 `messages` 数组在切换时直接替换，丢失运行时状态
   - 后端 SessionStore 只存最终结果，无法恢复中间态

3. **扩展性受限**：
   - Phase 4 需要多 Agent 协作、条件路由、Human-in-the-loop
   - 当前手动管理状态的方式无法支持复杂编排

### 业务目标

- **用户体验**：支持多会话并行流式生成，切换无卡顿
- **技术债务**：避免 Phase 4 推倒重来
- **可维护性**：清晰的状态流转、易于调试和测试

---

## 决策（Decision）

**采用 LangGraph 作为 RAG 系统的状态管理和编排引擎。**

### 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Session A   │  │  Session B   │  │  Session C   │     │
│  │  (streaming) │  │  (idle)      │  │  (streaming) │     │
│  └──────┬───────┘  └──────────────┘  └──────┬───────┘     │
│         │  AbortController per session       │             │
└─────────┼────────────────────────────────────┼─────────────┘
          │ SSE stream                         │ SSE stream
          ↓                                    ↓
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  /api/v1/stream  ←  Feature Flag: USE_LANGGRAPH            │
│         │                                                    │
│    ┌────▼────────────────────────────────────┐             │
│    │         LangGraph RAG App               │             │
│    │  ┌────────┐    ┌──────────┐            │             │
│    │  │Retrieve│───▶│ Generate │───▶ END    │             │
│    │  └────────┘    └──────────┘            │             │
│    └─────────────────┬──────────────────────┘             │
│                      │                                      │
│         ┌────────────▼──────────────┐                      │
│         │  AsyncSqliteSaver         │                      │
│         │  (gameguide.db)           │                      │
│         │  - thread_id = session_id │                      │
│         │  - checkpoint 自动持久化   │                      │
│         └───────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 关键设计

#### 1. State 定义

```python
class RAGState(TypedDict):
    # 输入
    query: str
    game: str | None
    session_id: str
    
    # 检索
    retrieved_docs: list[dict]
    retrieval_scores: list[float]
    
    # 生成
    thinking: str
    answer: str
    
    # 历史（由 LangGraph 管理）
    messages: Annotated[list[BaseMessage], add_messages]
```

#### 2. 双层持久化

| 层级 | 职责 | 技术 | 数据 |
|------|------|------|------|
| **业务层** | Session 元数据 | SessionStore (SQLite) | title, created_at, message_count |
| **执行层** | 运行时状态 | LangGraph Checkpointer | messages, thinking, retrieved_docs, 中间态 |

**原因**：
- Checkpointer 专注执行状态，不管业务逻辑（如标题生成）
- SessionStore 继续负责用户可见的元数据
- 两者通过 `session_id = thread_id` 关联

#### 3. 流式输出策略

```python
stream_mode = "updates"  # 只返回节点更新，减少流量

async for event in rag_graph.astream(input, config, stream_mode="updates"):
    if "retrieve" in event:
        yield sse("retrieval", {"count": len(event["retrieve"]["retrieved_docs"])})
    elif "generate" in event:
        # 支持 token-level streaming
        yield sse("thinking", {"delta": event["generate"]["thinking"]})
        yield sse("generation", {"delta": event["generate"]["answer"]})
```

#### 4. Feature Flag 灰度

```python
# src/config.py
class Settings(BaseSettings):
    use_langgraph: bool = Field(default=False, description="启用 LangGraph 实现")

# src/api/main.py
@app.post("/api/v1/stream")
async def stream_endpoint(req: StreamRequest):
    if settings.use_langgraph:
        return await stream_with_langgraph(req)  # 新实现
    else:
        return await stream_legacy(req)  # 旧实现（兜底）
```

**灰度策略**：
1. 本地开发：`USE_LANGGRAPH=true` 测试新实现
2. 单元测试：两种实现都跑，确保行为一致
3. 生产部署：先 `false`（旧），观察稳定后切 `true`
4. 遇到问题立即回滚：改环境变量即可

---

## 实施计划（Implementation Plan）

### 阶段 1：POC 验证（今天，2-3 小时）

**目标**：独立脚本验证可行性，不改现有代码。

```bash
# scripts/langgraph_poc.py
# 验证点：
# 1. AsyncSqliteSaver 能否正常工作
# 2. 流式输出是否符合预期
# 3. checkpoint 恢复是否正确
```

**验收**：
- ✅ 单会话流式生成成功
- ✅ 中断后从 checkpoint 恢复
- ✅ 多次运行状态累积正确

---

### 阶段 2：核心 Graph 实现（明天，4-5 小时）

#### 2.1 创建模块结构

```
src/graphs/
├── __init__.py
├── rag_state.py      # State 定义
├── rag_graph.py      # Graph 构建
├── nodes.py          # 节点实现
└── utils.py          # 辅助函数
```

#### 2.2 测试先行（TDD）

```python
# tests/unit/test_rag_graph.py
@pytest.mark.asyncio
async def test_rag_graph_single_turn():
    """单轮对话测试"""
    result = await rag_graph.ainvoke(
        {"query": "妖刀姬怎么连招？", "game": "", "session_id": "test-1"},
        config={"configurable": {"thread_id": "test-1"}}
    )
    assert result["answer"]
    assert result["retrieved_docs"]

@pytest.mark.asyncio
async def test_rag_graph_checkpoint_resume():
    """断点恢复测试"""
    thread_id = "test-resume"
    
    # 第一次执行
    result1 = await rag_graph.ainvoke(
        {"query": "妖刀姬技能？", "session_id": thread_id},
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # 第二次从 checkpoint 恢复
    result2 = await rag_graph.ainvoke(
        {"query": "伤害是多少？", "session_id": thread_id},
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # 验证历史被加载
    state = await rag_graph.aget_state({"configurable": {"thread_id": thread_id}})
    assert len(state.values["messages"]) == 4  # 2 轮 * 2 消息
```

#### 2.3 实现节点（复用现有逻辑）

```python
# src/graphs/nodes.py
async def retrieve_node(state: RAGState) -> dict:
    """检索节点 - 包装现有 retrieve()"""
    from ..retrieval import retrieve
    results = retrieve(state["query"], top_k=10, game=state.get("game"))
    return {
        "retrieved_docs": [
            {
                "id": r.chunk.chunk_id,
                "content": r.chunk.content,
                "score": r.score,
                "metadata": r.chunk.metadata,
            }
            for r in results
        ],
        "retrieval_scores": [r.score for r in results],
    }

async def generate_node(state: RAGState) -> dict:
    """生成节点 - 支持流式输出"""
    from ..pipeline import build_context
    from ..llm import get_streaming_llm, message_text, reasoning_text
    from ..prompts.templates import SYSTEM_PROMPT, build_user_prompt
    from langchain_core.messages import SystemMessage, HumanMessage
    
    # 构造 context
    results = [RetrievalResult(**d) for d in state["retrieved_docs"]]
    context_chunks, _ = build_context(results, top_n=5)
    
    # 构造 messages（LangGraph 会自动管理历史）
    user_prompt = build_user_prompt(state["query"], context_chunks, state.get("game", ""))
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state.get("messages", []),  # 历史
        HumanMessage(content=user_prompt),
    ]
    
    # 流式生成
    llm = get_streaming_llm()
    full_thinking = ""
    full_answer = ""
    
    async for chunk in llm.astream(messages):
        thinking = reasoning_text(chunk)
        content = message_text(chunk)
        
        if thinking:
            full_thinking += thinking
            # 通过 yield 实现流式输出（需要配合 astream_events）
        if content:
            full_answer += content
    
    return {
        "thinking": full_thinking,
        "answer": full_answer,
    }
```

---

### 阶段 3：API 集成与 Feature Flag（后天上午，3 小时）

```python
# src/api/main.py
async def stream_with_langgraph(req: StreamRequest):
    """LangGraph 实现"""
    from ..graphs.rag_graph import rag_graph
    
    session_id = req.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    async def event_stream():
        yield sse("start", {"session_id": session_id})
        
        try:
            async for event in rag_graph.astream(
                {
                    "query": req.query,
                    "game": req.game or "",
                    "session_id": session_id,
                },
                config=config,
                stream_mode="updates",
            ):
                # 转换为前端期望的格式
                if "retrieve" in event:
                    yield sse("retrieval", {"chunks_retrieved": len(event["retrieve"]["retrieved_docs"])})
                elif "generate" in event:
                    if event["generate"].get("thinking"):
                        yield sse("thinking", {"delta": event["generate"]["thinking"]})
                    if event["generate"].get("answer"):
                        yield sse("generation", {"delta": event["generate"]["answer"]})
            
            # 最终状态
            final_state = await rag_graph.aget_state(config)
            yield sse("done", {
                "answer": final_state.values["answer"],
                "thinking": final_state.values["thinking"],
                "retrieved_docs": final_state.values["retrieved_docs"],
            })
        
        except Exception as e:
            yield sse("error", {"error": str(e)})
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

async def stream_legacy(req: StreamRequest):
    """旧实现（保持不变，兜底）"""
    # 当前的 stream_query_endpoint 逻辑
    ...

@app.post("/api/v1/stream")
async def stream_endpoint(req: StreamRequest):
    if settings.use_langgraph:
        return await stream_with_langgraph(req)
    return await stream_legacy(req)
```

---

### 阶段 4：前端多会话状态管理（后天下午，3-4 小时）

```typescript
// web/src/hooks/useMultiSession.ts
import { useState, useRef, useCallback } from 'react';

interface SessionState {
  messages: Message[];
  loading: boolean;
}

export function useMultiSession() {
  const [sessionStates, setSessionStates] = useState<Map<string, SessionState>>(new Map());
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const abortControllers = useRef<Map<string, AbortController>>(new Map());
  
  const sendMessage = useCallback(async (sessionId: string, query: string) => {
    // 创建独立的 AbortController
    const controller = new AbortController();
    abortControllers.current.set(sessionId, controller);
    
    // 更新该会话的 loading 状态
    setSessionStates(prev => {
      const state = prev.get(sessionId) || { messages: [], loading: false };
      return new Map(prev).set(sessionId, { ...state, loading: true });
    });
    
    try {
      for await (const event of streamQuery({
        query,
        session_id: sessionId,
        signal: controller.signal,
      })) {
        // 只更新对应 sessionId 的状态
        setSessionStates(prev => {
          const state = prev.get(sessionId)!;
          return new Map(prev).set(sessionId, {
            ...state,
            messages: applyEvent(state.messages, event),
          });
        });
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log(`Session ${sessionId} request aborted`);
      } else {
        throw err;
      }
    } finally {
      abortControllers.current.delete(sessionId);
      setSessionStates(prev => {
        const state = prev.get(sessionId)!;
        return new Map(prev).set(sessionId, { ...state, loading: false });
      });
    }
  }, []);
  
  const switchSession = useCallback((newSessionId: string) => {
    setActiveSessionId(newSessionId);
    // 不中断其他会话的请求
  }, []);
  
  return {
    sessionStates,
    activeSessionId,
    sendMessage,
    switchSession,
  };
}
```

---

### 阶段 5：集成测试与性能基准（第 4 天，半天）

```python
# tests/integration/test_multi_session.py
@pytest.mark.asyncio
async def test_parallel_sessions():
    """测试多会话并行"""
    async with httpx.AsyncClient(...) as client:
        # 会话 A 开始流式生成
        task_a = asyncio.create_task(stream_session(client, "session-a", "妖刀姬连招？"))
        await asyncio.sleep(0.5)  # 模拟延迟
        
        # 会话 B 立即开始（不应被阻塞）
        task_b = asyncio.create_task(stream_session(client, "session-b", "红蝶技能？"))
        
        results = await asyncio.gather(task_a, task_b)
        assert results[0]["answer"]
        assert results[1]["answer"]

@pytest.mark.asyncio
async def test_checkpoint_recovery():
    """测试断点恢复"""
    # 第一轮对话
    await stream_session(client, "session-x", "妖刀姬 1 技能？")
    
    # 模拟崩溃重启
    # ...
    
    # 第二轮应该能访问历史
    result = await stream_session(client, "session-x", "伤害是多少？")
    # 后端应该从 checkpoint 加载历史，正确理解"伤害"指代
    assert "妖刀姬" in result["answer"] or "刃返" in result["answer"]
```

**性能基准**：

| 指标 | 旧实现 | LangGraph 实现 | 目标 |
|------|--------|---------------|------|
| 首字延迟 | ~1.2s | ≤ 1.5s | < 2s |
| Token 吞吐 | ~45 token/s | ≥ 40 token/s | > 35 token/s |
| 内存占用 | ~150MB | ≤ 200MB | < 250MB |
| Checkpoint 开销 | N/A | ≤ 50ms | < 100ms |

---

## 结果（Consequences）

### 正面影响

1. **多会话并行**：彻底解决切换卡顿问题
2. **状态可恢复**：刷新、崩溃后能恢复中间态
3. **架构清晰**：Node-based 编排易于理解和扩展
4. **测试友好**：每个 Node 可独立测试
5. **可观测性**：LangSmith 自动追踪
6. **为 Phase 4 铺路**：Multi-Agent 无需重构

### 负面影响与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| **学习曲线** | 开发速度短期下降 | POC 先验证，文档同步 |
| **依赖增加** | LangGraph 版本兼容 | 锁定版本 `langgraph==0.2.55` |
| **性能开销** | Checkpoint 写入延迟 | 异步写入，监控 P99 |
| **兼容性** | 旧数据迁移 | Feature Flag 长期共存 |
| **调试复杂度** | Graph 状态难追踪 | 接入 LangSmith，本地开启 verbose |

### 不做的后果

- Phase 4 必须推倒重来（预计 5-7 天工作量浪费）
- 多会话问题靠前端 hack 解决，技术债累积
- 无法支持 HITL、条件路由等高级特性

---

## 监控与回滚

### 关键指标

```python
# 监控埋点
import time
from prometheus_client import Histogram, Counter

langgraph_latency = Histogram('langgraph_node_duration_seconds', 'Node执行耗时', ['node_name'])
langgraph_errors = Counter('langgraph_errors_total', '执行错误', ['error_type'])

@node_wrapper
async def retrieve_node(state):
    start = time.time()
    try:
        result = await _retrieve(state)
        langgraph_latency.labels(node_name='retrieve').observe(time.time() - start)
        return result
    except Exception as e:
        langgraph_errors.labels(error_type=type(e).__name__).inc()
        raise
```

### 回滚预案

```bash
# 方案 1：环境变量回滚
export USE_LANGGRAPH=false
docker compose restart api

# 方案 2：代码回滚
git revert <commit-hash>
git push

# 方案 3：数据回滚
# Checkpointer 与 SessionStore 独立，互不影响
# 关闭 LangGraph 后 SessionStore 仍正常工作
```

---

## 附录

### 依赖版本

```toml
# pyproject.toml
[tool.poetry.dependencies]
langgraph = "^0.2.55"
langchain-core = "^0.3.0"
langchain-ollama = "^0.3.0"
aiosqlite = "^0.20.0"
```

### 参考文档

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Persistence Guide](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- [Streaming Tokens](https://langchain-ai.github.io/langgraph/how-tos/streaming-tokens/)
- [Human-in-the-Loop](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/)

### 后续优化（Phase 2-4）

- [ ] 条件路由：低分自动 Query Rewrite
- [ ] Rerank 节点
- [ ] Multi-Agent Supervisor
- [ ] Tool Calling 集成
- [ ] 可视化 Graph 执行流程

---

**决策状态更新历史**：
- 2026-09-19：提议中，待技术验证
- 预计 2026-09-21：通过，开始实施
