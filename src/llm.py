"""LLM provider 封装。

支持：
- ollama：本地 ChatOllama，reasoning 使用结构化 reasoning_content
- minimax/openai：OpenAI 兼容 ChatOpenAI

上层只依赖 get_llm()/get_streaming_llm()，不感知具体供应商。
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from .config import settings


def _ollama_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        reasoning=settings.llm_reasoning,
        temperature=settings.llm_temperature,
        num_ctx=settings.llm_context_window,
        num_predict=settings.llm_max_tokens,
        keep_alive=settings.llm_keep_alive,
        validate_model_on_init=True,
        sync_client_kwargs={"timeout": settings.llm_timeout},
        async_client_kwargs={"timeout": settings.llm_timeout},
    )


def _openai_compatible_llm(*, streaming: bool) -> ChatOpenAI:
    if not settings.llm_api_key:
        raise ValueError(
            f"{settings.llm_provider} 需要 LLM_API_KEY，请在 .env 中配置"
        )

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout,
        streaming=streaming,
    )


def _create_llm(*, streaming: bool) -> BaseChatModel:
    provider = settings.llm_provider.lower().strip()
    if provider == "ollama":
        return _ollama_llm()
    if provider in {"minimax", "openai"}:
        return _openai_compatible_llm(streaming=streaming)
    raise ValueError(
        f"不支持的 LLM_PROVIDER={settings.llm_provider!r}，"
        "可选：ollama/minimax/openai"
    )


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """获取同步/异步调用共用的 LLM 单例。"""
    return _create_llm(streaming=False)


@lru_cache(maxsize=1)
def get_streaming_llm() -> BaseChatModel:
    """获取流式 LLM 单例。"""
    return _create_llm(streaming=True)


def message_text(message: Any) -> str:
    """把 LangChain message/chunk 的 content 统一转换为文本。"""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "".join(parts)
    return str(content or "")


def reasoning_text(message: Any) -> str:
    """读取 ChatOllama 等模型返回的结构化 reasoning 内容。"""
    additional = getattr(message, "additional_kwargs", {}) or {}
    reasoning = additional.get("reasoning_content", "")
    return reasoning if isinstance(reasoning, str) else str(reasoning or "")


def clear_llm_cache() -> None:
    """测试或运行时切换 provider 后清理客户端缓存。"""
    get_llm.cache_clear()
    get_streaming_llm.cache_clear()
