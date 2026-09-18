"""LLM 客户端封装（基于 langchain-openai，与 MiniMax 兼容）"""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from .config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """
    获取 LLM 客户端单例

    MiniMax 提供 OpenAI 兼容 API，所以可以用 ChatOpenAI。
    切换其他 provider 时改这里即可。
    """
    if not settings.llm_api_key:
        raise ValueError(
            "LLM_API_KEY 未配置，请在 .env 中设置 LLM_API_KEY=你的key"
        )

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout,
    )


def get_streaming_llm() -> ChatOpenAI:
    """获取流式 LLM 客户端（用于 SSE）"""
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY 未配置")

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout,
        streaming=True,
    )