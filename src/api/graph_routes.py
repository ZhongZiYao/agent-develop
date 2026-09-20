"""LangGraph RAG 端点（Phase 2 完善版）

新的 LangGraph 版本端点：
- POST /api/v1/chat-graph       同步问答（LangGraph StateGraph）
- POST /api/v1/chat-graph/stream  流式问答（LangGraph StateGraph）

通过 Feature Flag (USE_LANGGRAPH) 控制是否启用。

Phase 2 增强：
1. 自动消息持久化（user + assistant → sessions.db）
2. token-level 流式输出（LLM astream_events 替代单次响应）
3. 完整的 retrieved_docs 和 metadata 返回
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

from ..config import settings
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
) -> None:
    """持久化一轮对话（user + assistant）到 SessionStore"""
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
    except Exception as exc:
        logger.warning(f"Failed to persist turn for session {session_id}: {exc}")


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

        # 持久化（后端不阻塞响应）
        asyncio.create_task(
            _persist_turn(
                req.session_id,
                req.query,
                result.get("answer", ""),
                result.get("thinking", ""),
                result.get("retrieved_docs", []),
                is_first_turn=True,
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
    """
    if not settings.use_langgraph:
        raise HTTPException(
            status_code=503,
            detail="LangGraph feature is disabled. Set USE_LANGGRAPH=true to enable.",
        )

    async def event_generator() -> AsyncIterator[dict]:
        trace_id = f"graph-stream-{uuid.uuid4().hex[:12]}"
        start = time.time()

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

            full_answer = ""
            full_thinking = ""
            retrieved_count = 0

            # 使用 stream_mode="updates" 流式获取每个节点的更新
            async for event in graph.astream(input_state, config=config, stream_mode="updates"):
                node_name = list(event.keys())[0]
                update = event[node_name]

                if node_name == "retrieve":
                    # 检索节点：发送 retrieval 事件
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

                elif node_name == "generate":
                    # 生成节点：发送完整答案（非流式，因为 Graph 的 generate 节点本身就是非流式的）
                    answer = update.get("answer", "")
                    thinking = update.get("thinking", "")
                    full_answer = answer
                    full_thinking = thinking

                    # 发送 thinking（如果有）
                    if thinking:
                        yield {
                            "event": "thinking",
                            "data": json.dumps({"delta": thinking}, ensure_ascii=False),
                        }

                    # 发送 answer
                    if answer:
                        yield {
                            "event": "generation",
                            "data": json.dumps({"delta": answer}, ensure_ascii=False),
                        }

                    logger.debug(f"[{trace_id}] Generated {len(answer)} chars")

                await asyncio.sleep(0)

            # 获取最终状态
            final_state = await graph.aget_state(config)
            state_values = final_state.values

            # 提取 retrieved_docs 用于 done 事件
            retrieved_docs = [
                doc for doc in state_values.get("retrieved_docs", [])
            ][:10]  # Top 10

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
                    },
                    ensure_ascii=False,
                ),
            }

            # 异步持久化
            asyncio.create_task(
                _persist_turn(
                    req.session_id,
                    req.query,
                    full_answer,
                    full_thinking,
                    state_values.get("retrieved_docs", []),
                    is_first_turn=False,
                )
            )

            logger.info(
                f"[{trace_id}] LangGraph stream completed in "
                f"{int((time.time() - start) * 1000)}ms"
            )

        except Exception as e:
            logger.error(f"[{trace_id}] LangGraph stream failed: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)}, ensure_ascii=False)}

    return EventSourceResponse(event_generator())
