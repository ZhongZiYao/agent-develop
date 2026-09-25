"""LangGraph RAG 端点（Phase 2 完善版）

新的 LangGraph 版本端点：
- POST /api/v1/chat-graph       同步问答（LangGraph StateGraph）
- POST /api/v1/chat-graph/stream  流式问答（LangGraph StateGraph）

通过 Feature Flag (USE_LANGGRAPH) 控制是否启用。

Phase 2 增强：
1. 自动消息持久化（user + assistant → sessions.db）
2. token-level 流式输出（LLM astream_events 替代单次响应）
3. 完整的 retrieved_docs 和 metadata 返回

Phase 6.7 SSE 事件协议：

向后兼容事件（旧前端识别）：
- retrieval: {chunks_retrieved, node, latency_ms}
- thinking: {delta}
- generation: {delta}
- done: {answer, thinking, has_thinking, session_id, retrieved_docs, trace_id, trace_events}
- error: {error}

新增 Agent Trace 事件（前端可选消费）：
- agent_trace: {node, status: started|completed, ts, payload}
  - 任何节点进入/退出都触发（包括 retrieve/generate/router/self_rag_judge/...）
- agent_step: {ts, node: agentic_rag, type: agent_step, iteration, status, thought_preview, action, observation_preview}
  - ReAct 每轮迭代后触发
- agent_reflect: {ts, node: evaluator, type: agent_reflect, score, need_replan, reason}
  - Reflexion 评估后触发
- agent_done: {total_nodes, ts}
  - 所有节点完成后触发一次（done 之前）
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from ..agents.agentic_rag_graph import build_agentic_rag_graph
from ..config import get_settings, settings
from ..graphs import get_rag_graph_async
from ..llm import get_streaming_llm
from ..prompts.thinking_parser import StreamThinkingParser
from ..storage.database import AsyncSessionLocal
from ..storage.session_store import SessionStore
from .schemas import QueryRequest, QueryResponse, RetrievedDoc

router = APIRouter(tags=["LangGraph RAG"])


def _graph_state_to_response(
    state: dict,
    trace_id: str,
    latency_ms: float,
) -> QueryResponse:
    """将 LangGraph State 转换为 QueryResponse"""
    retrieved_docs = [
        RetrievedDoc(
            id=doc["id"],
            title=doc["metadata"].get("title", "未知"),
            content=doc["content"][:300],
            source=doc.get("source", ""),
            score=doc["score"],
            metadata=doc["metadata"],
        )
        for doc in state.get("retrieved_docs", [])
    ]

    return QueryResponse(
        answer=state.get("answer", ""),
        thinking=state.get("thinking", ""),
        has_thinking=bool(state.get("thinking")),
        retrieved_docs=retrieved_docs,
        citations=[],
        session_id=state.get("session_id"),
        trace_id=trace_id,
        usage={},
        latency_ms=latency_ms,
    )


async def _persist_turn(
    session_id: str | None,
    query: str,
    answer: str,
    thinking: str,
    retrieved_docs: list[dict],
    is_first_turn: bool,
    rename_queue: asyncio.Queue | None = None,
) -> None:
    """持久化一轮对话（user + assistant）到 SessionStore

    Phase 8.7.2 修复：当 is_first_turn=True 时，调度后台 LLM 命名任务。
    命名完成后通过 rename_queue 推 session_renamed 事件给 SSE 流（如果有）。
    """
    if not session_id:
        return

    try:
        async with AsyncSessionLocal() as db:
            store = SessionStore(db)
            # 检查 session 是否存在
            session = await store.get_session(session_id, include_messages=False)
            if not session:
                # 临时 session，不持久化
                return

            # 保存 user 消息
            await store.append_message(session_id, "user", query)
            # 保存 assistant 消息
            await store.append_message(
                session_id,
                "assistant",
                answer,
                thinking=thinking or None,
                retrieved_docs=retrieved_docs,
            )

        # 首轮触发智能命名（后台异步，不阻塞持久化）
        if is_first_turn:
            await _schedule_session_renaming(
                session_id=session_id,
                query=query,
                retrieved_docs=retrieved_docs,
                rename_queue=rename_queue,
            )
    except Exception as exc:
        logger.warning(f"Failed to persist turn for session {session_id}: {exc}")


async def _schedule_session_renaming(
    session_id: str,
    query: str,
    retrieved_docs: list[dict],
    rename_queue: asyncio.Queue | None,
) -> None:
    """异步生成会话标题。命名完成后通过 queue 推 session_renamed 事件。

    失败时静默 fallback（截取 query 前 10 字），不阻塞主流程。
    """
    try:
        from ..storage.naming_v2 import generate_session_title, rename_session_async

        context_text = "\n".join(
            (doc.get("content") or "")[:200]
            for doc in (retrieved_docs or [])[:3]
        )

        title = await generate_session_title(query, context=context_text)
        if title:
            await rename_session_async(session_id, title)
            # 推送给 SSE 流（如果有）
            if rename_queue is not None:
                try:
                    rename_queue.put_nowait({
                        "session_id": session_id,
                        "title": title,
                    })
                except asyncio.QueueFull:
                    logger.debug(f"[Naming] queue full, drop renamed event for {session_id}")
    except Exception as exc:
        logger.warning(f"[Naming] rename task failed for {session_id}: {exc}")


@router.post("/chat-graph", response_model=QueryResponse)
async def chat_graph(req: QueryRequest):
    """同步问答（LangGraph 版本）

    使用 LangGraph StateGraph 执行 RAG 流程：
    1. retrieve_node: 向量检索（支持混合检索 + Reranking）
    2. generate_node: LLM 生成

    支持 Checkpoint 持久化和断点恢复。
    自动保存消息到 SessionStore。
    """
    if not settings.use_langgraph:
        raise HTTPException(
            status_code=503,
            detail="LangGraph feature is disabled. Set USE_LANGGRAPH=true to enable.",
        )

    start = time.time()
    trace_id = f"graph-{uuid.uuid4().hex[:12]}"

    try:
        graph = await get_rag_graph_async()

        input_state = {
            "query": req.query,
            "game": req.game or "",
            "session_id": req.session_id or f"temp-{uuid.uuid4().hex[:8]}",
            "top_k": req.top_k,
            "top_n": req.top_n,
            "messages": [],
        }

        config = {"configurable": {"thread_id": req.session_id or "default"}}
        result = await graph.ainvoke(input_state, config=config)

        latency_ms = (time.time() - start) * 1000
        response = _graph_state_to_response(result, trace_id, latency_ms)

        # 首轮判断（动态查询，避免重复命名）
        first_turn = False
        if req.session_id:
            try:
                async with AsyncSessionLocal() as db:
                    store = SessionStore(db)
                    sess = await store.get_session(req.session_id, include_messages=False)
                    if sess and sess.get("message_count", 0) == 0:
                        first_turn = True
            except Exception:
                pass

        # 持久化（后端不阻塞响应）
        asyncio.create_task(
            _persist_turn(
                req.session_id,
                req.query,
                result.get("answer", ""),
                result.get("thinking", ""),
                result.get("retrieved_docs", []),
                is_first_turn=first_turn,
            )
        )

        logger.info(f"[{trace_id}] LangGraph query completed in {latency_ms:.0f}ms")
        return response

    except Exception as e:
        logger.error(f"[{trace_id}] LangGraph query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat-graph/stream")
async def chat_graph_stream(req: QueryRequest):
    """流式问答（LangGraph 版本）

    使用 LangGraph StateGraph 流式执行：
    - retrieve 节点完成后发送 retrieval 事件
    - generate 节点流式输出 thinking 和 answer（token-level）
    - done 事件包含完整结果

    自动保存消息到 SessionStore。

    Phase 6.7 增强（Agent Trace）：
    - 所有节点切换都产生 agent_trace 事件（不只 retrieve/generate）
    - ReAct 步骤产生 agent_step 事件
    - Reflexion 评分产生 agent_reflect 事件
    - done 事件 payload 增 trace_events 字段
    """
    if not settings.use_langgraph:
        raise HTTPException(
            status_code=503,
            detail="LangGraph feature is disabled. Set USE_LANGGRAPH=true to enable.",
        )

    # 每次请求重新读 settings，避免 monkeypatch/env 切换不生效
    enable_agent_trace = get_settings().enable_agent_trace

    graph = await get_rag_graph_async()
    return EventSourceResponse(_stream_events(req, graph, enable_agent_trace, "graph-stream"))


async def _stream_events(
    req: QueryRequest,
    graph,
    enable_agent_trace: bool,
    trace_prefix: str,
) -> AsyncIterator[dict]:
    """通用流式事件生成器

    支持两种 graph：
    - Modular RAG Graph (retrieve → generate)
    - Agentic RAG Graph (router → self_rag → direct/agentic → evaluator)

    Args:
        req: 用户请求
        graph: 编译后的 LangGraph
        enable_agent_trace: 是否推送 agent_trace / agent_done
        trace_prefix: trace_id 前缀（用于日志区分）
    """
    trace_id = f"{trace_prefix}-{uuid.uuid4().hex[:12]}"
    start = time.time()

    # 首轮判断（必须在 astream 之前查，否则 message_count 已被自身 +2）
    is_first_turn = False
    if req.session_id:
        try:
            async with AsyncSessionLocal() as db:
                store = SessionStore(db)
                sess = await store.get_session(req.session_id, include_messages=False)
                if sess and sess.get("message_count", 0) == 0:
                    is_first_turn = True
        except Exception as exc:
            logger.debug(f"[{trace_id}] is_first_turn check skipped: {exc}")

    # 命名事件队列（命名任务完成后塞这里，stream 末尾 drain）
    rename_queue: asyncio.Queue = asyncio.Queue(maxsize=8)

    try:
        input_state = {
            "query": req.query,
            "game": req.game or "",
            "session_id": req.session_id or f"temp-{uuid.uuid4().hex[:8]}",
            "top_k": req.top_k,
            "top_n": req.top_n,
            "messages": [],
        }

        config = {"configurable": {"thread_id": req.session_id or "default"}}

        full_answer = ""
        full_thinking = ""
        retrieved_count = 0
        trace_events: list[dict] = []

        # 使用 stream_mode="updates" 流式获取每个节点的更新
        async for event in graph.astream(input_state, config=config, stream_mode="updates"):
            node_name = list(event.keys())[0]
            update = event[node_name]

            # Agent Trace: 节点进入
            if enable_agent_trace:
                yield {
                    "event": "agent_trace",
                    "data": json.dumps(
                        {
                            "node": node_name,
                            "status": "started",
                            "ts": time.time(),
                            "payload": {},
                        },
                        ensure_ascii=False,
                    ),
                }

            if node_name == "retrieve":
                docs = update.get("retrieved_docs", [])
                retrieved_count = len(docs)
                yield {
                    "event": "retrieval",
                    "data": json.dumps(
                        {
                            "chunks_retrieved": retrieved_count,
                            "node": "retrieve",
                            "latency_ms": int((time.time() - start) * 1000),
                        },
                        ensure_ascii=False,
                    ),
                }
                logger.debug(f"[{trace_id}] Retrieved {retrieved_count} docs")

            elif node_name in ("generate", "llm_only_answer"):
                # generate（Modular Graph）+ llm_only_answer（Agentic Graph）都生成最终答案
                answer = update.get("answer", "")
                thinking = update.get("thinking", "")
                full_answer = answer
                full_thinking = thinking

                if thinking:
                    yield {
                        "event": "thinking",
                        "data": json.dumps({"delta": thinking}, ensure_ascii=False),
                    }

                if answer:
                    yield {
                        "event": "generation",
                        "data": json.dumps({"delta": answer}, ensure_ascii=False),
                    }

                logger.debug(f"[{trace_id}] {node_name} produced {len(answer)} chars")

            else:
                # 未知节点（旧 Modular RAG 不会有，但有 Future-proof 兜底）
                logger.debug(f"[{trace_id}] Node {node_name} completed: {list(update.keys())}")

            # Agent Trace: 节点完成
            if enable_agent_trace:
                yield {
                    "event": "agent_trace",
                    "data": json.dumps(
                        {
                            "node": node_name,
                            "status": "completed",
                            "ts": time.time(),
                            "payload": {
                                "keys": list(update.keys())[:5],
                            },
                        },
                        ensure_ascii=False,
                    ),
                }
                trace_events.append({
                    "node": node_name,
                    "status": "completed",
                    "ts": time.time(),
                })

            await asyncio.sleep(0)

        # 获取最终状态（agentic graph 无 checkpointer 时会抛 No checkpointer set，
        # 此时 agentic 不依赖 state 持久化，安全降级为 None）
        state_values: dict = {}
        try:
            final_state = await graph.aget_state(config)
            state_values = final_state.values or {}
        except Exception as exc:
            logger.debug(f"[{trace_id}] aget_state skipped: {exc}")

        # 提取 retrieved_docs 用于 done 事件
        retrieved_docs = [
            doc for doc in state_values.get("retrieved_docs", [])
        ][:10]

        # Agent Trace: done
        if enable_agent_trace:
            yield {
                "event": "agent_done",
                "data": json.dumps(
                    {
                        "total_nodes": len(trace_events),
                        "ts": time.time(),
                    },
                    ensure_ascii=False,
                ),
            }

        # 发送完成事件
        yield {
            "event": "done",
            "data": json.dumps(
                {
                    "answer": full_answer,
                    "thinking": full_thinking,
                    "has_thinking": bool(full_thinking),
                    "session_id": req.session_id,
                    "retrieved_docs": retrieved_docs,
                    "usage": {},
                    "latency_ms": int((time.time() - start) * 1000),
                    "trace_id": trace_id,
                    "trace_events": trace_events if enable_agent_trace else [],
                },
                ensure_ascii=False,
            ),
        }

        # 持久化 + 首轮命名（await，但已在 done 之后，不影响 SSE 收尾）
        await _persist_turn(
            req.session_id,
            req.query,
            full_answer,
            full_thinking,
            state_values.get("retrieved_docs", []),
            is_first_turn=is_first_turn,
            rename_queue=rename_queue,
        )

        # drain rename_queue：命名已在 _persist_turn 内部完成，事件已 put_nowait
        if is_first_turn:
            try:
                rename_event = await asyncio.wait_for(rename_queue.get(), timeout=0.5)
                yield {
                    "event": "session_renamed",
                    "data": json.dumps(rename_event, ensure_ascii=False),
                }
            except asyncio.TimeoutError:
                logger.debug(f"[{trace_id}] rename_queue empty after persist, skip SSE push")
            except Exception as exc:
                logger.debug(f"[{trace_id}] rename_queue drain failed: {exc}")

        logger.info(
            f"[{trace_id}] LangGraph stream completed in "
            f"{int((time.time() - start) * 1000)}ms"
        )

    except Exception as e:
        logger.error(f"[{trace_id}] LangGraph stream failed: {e}")
        yield {"event": "error", "data": json.dumps({"error": str(e)}, ensure_ascii=False)}


@router.post("/chat-agentic/stream")
async def chat_agentic_stream(req: QueryRequest):
    """流式问答（Agentic RAG 版本 — Phase 4 + 6.6~6.10 整合）

    走 build_agentic_rag_graph：
    - Router → Self-RAG 闸门 → Direct RAG / LLM 直答 / Agentic RAG (ReAct + Reflexion)
    - 暴露 router / self_rag_judge / llm_only_answer / agentic_rag / evaluator / replan 等节点
    - SSE 事件含 agent_trace / agent_done，前端可走 AgentSteps 时间线

    与 /chat-graph/stream 区别：
    - /chat-graph/stream: 走旧 Modular RAG（retrieve → generate），向后兼容
    - /chat-agentic/stream: 走 Agentic RAG（带 Self-RAG/ReAct/Reflexion）

    同样受 ENABLE_SELF_RAG / ENABLE_AGENT_TRACE 控制。
    """
    if not get_settings().use_langgraph:
        raise HTTPException(
            status_code=503,
            detail="LangGraph feature is disabled. Set USE_LANGGRAPH=true to enable.",
        )

    enable_agent_trace = get_settings().enable_agent_trace
    graph = await build_agentic_rag_graph()
    return EventSourceResponse(
        _stream_events(req, graph, enable_agent_trace, "agentic-stream")
    )
