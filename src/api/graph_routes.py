"""LangGraph RAG 端点

新的 LangGraph 版本端点：
- POST /api/v1/chat-graph       同步问答（LangGraph StateGraph）
- POST /api/v1/chat-graph/stream  流式问答（LangGraph StateGraph）

通过 Feature Flag (USE_LANGGRAPH) 控制是否启用。
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
from .schemas import QueryRequest, QueryResponse, RetrievedDoc

router = APIRouter(tags=["LangGraph RAG"])


def _graph_state_to_response(
    state: dict,
    trace_id: str,
    latency_ms: float,
) -> QueryResponse:
    """将 LangGraph State 转换为 QueryResponse"""
    # 提取 retrieved_docs
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


@router.post("/chat-graph", response_model=QueryResponse)
async def chat_graph(req: QueryRequest):
    """同步问答（LangGraph 版本）

    使用 LangGraph StateGraph 执行 RAG 流程：
    1. retrieve_node: 向量检索
    2. generate_node: LLM 生成

    支持 Checkpoint 持久化和断点恢复。
    """
    if not settings.use_langgraph:
        raise HTTPException(
            status_code=503,
            detail="LangGraph feature is disabled. Set USE_LANGGRAPH=true to enable.",
        )

    start = time.time()
    trace_id = f"graph-{uuid.uuid4().hex[:12]}"

    try:
        # 获取编译好的 Graph
        graph = await get_rag_graph_async()

        # 构造输入状态
        input_state = {
            "query": req.query,
            "game": req.game or "",
            "session_id": req.session_id or f"temp-{uuid.uuid4().hex[:8]}",
            "top_k": req.top_k,
            "top_n": req.top_n,
            "messages": [],  # LangGraph 会自动管理历史
        }

        # 执行 Graph（thread_id = session_id）
        config = {"configurable": {"thread_id": req.session_id or "default"}}
        result = await graph.ainvoke(input_state, config=config)

        # 转换为响应
        latency_ms = (time.time() - start) * 1000
        response = _graph_state_to_response(result, trace_id, latency_ms)

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
    - generate 节点流式输出 thinking 和 answer
    """
    if not settings.use_langgraph:
        raise HTTPException(
            status_code=503,
            detail="LangGraph feature is disabled. Set USE_LANGGRAPH=true to enable.",
        )

    async def event_generator() -> AsyncIterator[dict]:
        trace_id = f"graph-stream-{uuid.uuid4().hex[:12]}"

        try:
            # 获取编译好的 Graph
            graph = await get_rag_graph_async()

            # 构造输入状态
            input_state = {
                "query": req.query,
                "game": req.game or "",
                "session_id": req.session_id or f"temp-{uuid.uuid4().hex[:8]}",
                "top_k": req.top_k,
                "top_n": req.top_n,
                "messages": [],
            }

            # 流式执行 Graph
            config = {"configurable": {"thread_id": req.session_id or "default"}}

            async for event in graph.astream(input_state, config=config, stream_mode="updates"):
                # event 格式: {"node_name": {partial_state_update}}
                node_name = list(event.keys())[0]
                update = event[node_name]

                if node_name == "retrieve":
                    # 检索完成
                    retrieved_count = len(update.get("retrieved_docs", []))
                    yield {
                        "event": "retrieval",
                        "data": json.dumps(
                            {"chunks_retrieved": retrieved_count, "node": "retrieve"},
                            ensure_ascii=False,
                        ),
                    }

                elif node_name == "generate":
                    # 生成完成（非流式，暂时一次返回）
                    # TODO: 实现真正的 token-level streaming
                    answer = update.get("answer", "")
                    thinking = update.get("thinking", "")

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

                await asyncio.sleep(0)

            # 获取最终状态
            final_state = await graph.aget_state(config)
            state_values = final_state.values

            # 发送完成事件
            retrieved_docs = [
                RetrievedDoc(
                    id=doc["id"],
                    title=doc["metadata"].get("title", "未知"),
                    content=doc["content"][:300],
                    source=doc.get("source", ""),
                    score=doc["score"],
                    metadata=doc["metadata"],
                ).model_dump()
                for doc in state_values.get("retrieved_docs", [])
            ]

            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "answer": state_values.get("answer", ""),
                        "thinking": state_values.get("thinking", ""),
                        "has_thinking": bool(state_values.get("thinking")),
                        "session_id": state_values.get("session_id"),
                        "retrieved_docs": retrieved_docs,
                        "usage": {},
                    },
                    ensure_ascii=False,
                ),
            }

        except Exception as e:
            logger.error(f"[{trace_id}] LangGraph stream failed: {e}")
            yield {"event": "error", "data": json.dumps({"error": str(e)}, ensure_ascii=False)}

    return EventSourceResponse(event_generator())
