"""RAG Pipeline — Phase 1.5

当前 Memory 边界：
- SessionStore + SQLite：业务会话、刷新恢复、最近 N 条消息窗口。
- LangGraph Checkpointer：本阶段尚未进入执行路径。Phase 4 建立真实 StateGraph 后，
  使用 thread_id=session_id 保存 Graph checkpoint、断点恢复和 HITL 状态。

Pipeline:
  user query + session_id
    ↓
  从 SessionStore 加载历史最近 N 轮（WindowMemory）
    ↓
  向量检索 top_k
    ↓
  top_n + 短路判断（Phase 1.x）
    ↓
  context = 检索结果 + 最近消息窗口
    ↓
  LLM 生成
    ↓
  返回 PipelineResult（answer + retrieved_docs + history_used）

Phase 4 会包成 LangGraph StateGraph 节点：
  - StateGraph + SqliteSaver checkpointer（thread_id = session_id）
  - 节点 = 当前 run_rag 流程
  - 状态字段：messages / context / retrieved_docs / generation
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .config import settings
from .llm import get_llm, message_text
from .prompts.templates import (
    REJECT_MESSAGE,
    REJECT_SCORE_THRESHOLD,
    SYSTEM_PROMPT,
    build_user_prompt,
    format_context_chunk,
)
from .schemas import Chunk, RetrievalResult
from .vectorstore.chroma_store import get_vector_store_instance


# WindowMemory 配置：最近 N 轮对话作为 context。
# 一轮通常含 user + assistant 两条消息，因此 10 轮 = 20 条消息。
HISTORY_WINDOW = 20


@dataclass
class PipelineResult:
    """RAG 问答结果"""
    answer: str
    retrieved_docs: list[RetrievalResult]
    usage: dict
    latency_ms: float
    history_used: int = 0  # 实际注入到 prompt 的历史消息数


def retrieve(query: str, top_k: int | None = None, game: str | None = None) -> list[RetrievalResult]:
    """向量召回"""
    top_k = top_k or settings.top_k
    vs = get_vector_store_instance()
    return vs.search(query, top_k=top_k)


def build_context(results: list[RetrievalResult], top_n: int | None = None) -> tuple[list[str], list[Chunk]]:
    """从检索结果构造 context"""
    top_n = top_n or settings.top_n
    top_results = results[:top_n]
    formatted = [format_context_chunk(i + 1, r.chunk) for i, r in enumerate(top_results)]
    raw_chunks = [r.chunk for r in top_results]
    return formatted, raw_chunks


async def load_history(session_id: str | None, window: int = HISTORY_WINDOW) -> list[dict]:
    """
    从 SessionStore 加载最近 N 轮对话历史

    Args:
        session_id: 会话 ID（None 表示无 session，不加载）
        window: 最多取多少条消息

    Returns:
        [{"role": "user"|"assistant", "content": "..."}, ...]
    """
    if not session_id:
        return []

    from .storage.database import AsyncSessionLocal
    from .storage.session_store import SessionStore

    async with AsyncSessionLocal() as db:
        store = SessionStore(db)
        msgs = await store.get_messages(session_id, limit=window, from_the_end=True)
        return [{"role": m["role"], "content": m["content"]} for m in msgs]


def format_history(history: list[dict]) -> str:
    """把历史对话格式化成 prompt 片段"""
    if not history:
        return ""

    lines = ["【对话历史】"]
    for m in history:
        role_zh = "用户" if m["role"] == "user" else "助手"
        # 截断过长的单条消息
        content = m["content"]
        if len(content) > 300:
            content = content[:300] + "..."
        lines.append(f"{role_zh}: {content}")
    return "\n".join(lines) + "\n\n"


def generate(
    query: str,
    context_chunks: list[str],
    game: str = "",
    history: list[dict] | None = None,
) -> tuple[str, dict]:
    """调 LLM 生成答案（支持 history）"""
    llm = get_llm()

    history_text = format_history(history or [])

    user_prompt = build_user_prompt(query, context_chunks, game)
    if history_text:
        # 把 history 插到参考资料之前
        user_prompt = history_text + user_prompt

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)

    usage = {}
    if hasattr(response, "response_metadata") and response.response_metadata:
        token_usage = response.response_metadata.get("token_usage", {})
        usage = {
            "prompt_tokens": token_usage.get("prompt_tokens", 0),
            "completion_tokens": token_usage.get("completion_tokens", 0),
            "total_tokens": token_usage.get("total_tokens", 0),
        }

    return message_text(response), usage


async def run_rag_async(query: str, game: str = "", session_id: str | None = None) -> PipelineResult:
    """
    异步端到端 RAG（支持 session history）

    Pipeline:
      query → load_history → retrieve → 短路判断 → context + history → LLM → answer
    """
    start = time.time()

    # 1. 加载历史（Phase 1.5 WindowMemory）
    history = await load_history(session_id) if session_id else []
    history_count = len(history)

    # 2. 召回
    results = retrieve(query, top_k=settings.top_k, game=game)

    # 3. 短路判断
    if not results or results[0].score < REJECT_SCORE_THRESHOLD:
        preview_chunks, _ = build_context(results, top_n=min(3, len(results)))
        preview_text = "\n\n".join(preview_chunks) if preview_chunks else "（无）"
        reject_answer = REJECT_MESSAGE.format(context=preview_text)
        latency_ms = (time.time() - start) * 1000
        return PipelineResult(
            answer=reject_answer,
            retrieved_docs=results,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            latency_ms=latency_ms,
            history_used=history_count,
        )

    # 4. 构造 context
    context_chunks, raw_chunks = build_context(results, top_n=settings.top_n)

    # 5. 生成（带 history）
    answer, usage = generate(query, context_chunks, game, history=history)

    latency_ms = (time.time() - start) * 1000

    return PipelineResult(
        answer=answer,
        retrieved_docs=results,
        usage=usage,
        latency_ms=latency_ms,
        history_used=history_count,
    )


def run_rag(query: str, game: str = "") -> PipelineResult:
    """
    同步端到端 RAG（不带 session 上下文，用于兼容旧调用）

    内部用 asyncio.run 跑异步版本
    """
    import asyncio

    return asyncio.run(run_rag_async(query, game=game, session_id=None))