"""RAG Pipeline — 把 load → split → embed → retrieve → generate 串起来

Phase 1 实现 Naive RAG（最简版）：
  1. 已有 VectorStore（数据已入库）
  2. 用户 query → 向量检索 top_k
  3. 取 top_n 个 chunk 拼 context
  4. LLM 生成答案

Phase 2 会替换为 Advanced RAG（Hybrid + Rerank + Query Rewrite）。
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from .config import settings
from .llm import get_llm
from .prompts.templates import (
    SYSTEM_PROMPT,
    build_user_prompt,
    format_context_chunk,
)
from .schemas import Chunk, RetrievalResult
from .vectorstore.chroma_store import get_vector_store_instance


@dataclass
class PipelineResult:
    """RAG 问答结果"""
    answer: str
    retrieved_docs: list[RetrievalResult]
    usage: dict
    latency_ms: float


def retrieve(query: str, top_k: int | None = None, game: str | None = None) -> list[RetrievalResult]:
    """
    向量召回（Phase 1 Naive 版本）

    Args:
        query: 用户问题
        top_k: 召回数量
        game: 游戏过滤（Phase 1 暂未启用，Phase 2 加 metadata filter）

    Returns:
        RetrievalResult 列表（按 score 降序）
    """
    top_k = top_k or settings.top_k
    vs = get_vector_store_instance()
    results = vs.search(query, top_k=top_k)

    # Phase 1 没启用 rerank，直接取 top_n
    # Phase 2 会在这里插入 rerank
    return results


def build_context(results: list[RetrievalResult], top_n: int | None = None) -> tuple[list[str], list[Chunk]]:
    """
    从检索结果构造 context（取 top_n 个）

    Returns:
        (formatted_chunks, raw_chunks)
    """
    top_n = top_n or settings.top_n
    top_results = results[:top_n]

    formatted = [format_context_chunk(i + 1, r.chunk) for i, r in enumerate(top_results)]
    raw_chunks = [r.chunk for r in top_results]
    return formatted, raw_chunks


def generate(query: str, context_chunks: list[str], game: str = "") -> tuple[str, dict]:
    """调 LLM 生成答案"""
    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=build_user_prompt(query, context_chunks, game)),
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

    return response.content, usage


def run_rag(query: str, game: str = "") -> PipelineResult:
    """
    端到端 RAG 流程

    Pipeline:
      query → retrieve(top_k) → top_n → context → LLM → answer
    """
    start = time.time()

    # 1. 召回
    results = retrieve(query, top_k=settings.top_k, game=game)

    # 2. 构造 context
    context_chunks, raw_chunks = build_context(results, top_n=settings.top_n)

    # 3. 生成
    answer, usage = generate(query, context_chunks, game)

    latency_ms = (time.time() - start) * 1000

    return PipelineResult(
        answer=answer,
        retrieved_docs=results,
        usage=usage,
        latency_ms=latency_ms,
    )


async def run_rag_stream(query: str, game: str = ""):
    """
    流式 RAG（Phase 2 实现，Phase 1 先放占位）
    """
    raise NotImplementedError("流式响应将在 Phase 1.5 API 层实现")