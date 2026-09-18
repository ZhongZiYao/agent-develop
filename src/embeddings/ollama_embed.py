"""Ollama 本地 Embedding 封装

基于 langchain-ollama（langchain 官方支持的 Ollama 集成）。
默认模型 bge-m3（中文 SOTA，1024 维）。
"""

from __future__ import annotations

from functools import lru_cache

from langchain_ollama import OllamaEmbeddings

from ..config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddings:
    """
    获取 Ollama Embeddings 单例

    用前请确保：
    1. Ollama 服务已启动（ollama serve）
    2. 已 pull 模型（ollama pull bge-m3）
    """
    return OllamaEmbeddings(
        model=settings.ollama_embed_model,
        base_url=settings.ollama_base_url,
    )


async def aembed_query(text: str) -> list[float]:
    """异步编码单条 query"""
    return await get_embeddings().aembed_query(text)


async def aembed_documents(texts: list[str]) -> list[list[float]]:
    """异步编码多条文档"""
    return await get_embeddings().aembed_documents(texts)