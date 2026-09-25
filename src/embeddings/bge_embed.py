"""BGE FlagEmbedding 本地 Embedding 封装（统一替换 OllamaEmbeddings）。

设计目标：
    - 与 langchain OllamaEmbeddings 同接口（embed_query / aembed_query /
      embed_documents / aembed_documents），可平滑替换 src.vectorstore.chroma_store
    - 单例懒加载 FlagEmbedding FlagModel（GPU 推理）
    - 异步接口内部用 thread pool 包装 sync encode（langchain 接口习惯）

背景：Phase 8.7 把 ETL embedding 切到 FlagEmbedding GPU 后，API query 端
还走 OllamaEmbeddings，导致 corpus (BGE) vs query (Ollama) 余弦 ~0.95 不严格一致。
统一到 FlagEmbedding 后两者完全一致。

依赖：FlagEmbedding + torch (已通过 uv extra gpu 装上)
环境变量：
    HF_ENDPOINT  HF 镜像（如 https://hf-mirror.com）
    BGE_MODEL_NAME  默认 BAAI/bge-m3
"""
from __future__ import annotations

import asyncio
import os
import threading

from langchain_core.embeddings import Embeddings

from ..config import settings
from ..etl.embed_bge import _get_model, truncate_for_embed, EMBEDDING_DIM, MAX_EMBED_CHARS


# ===== 单例 async lock（langchain 期望并发安全） =====
_async_lock = threading.Lock()


def _encode_sync(texts: list[str]) -> list[list[float]]:
    """同步编码多条文本（GPU batch）。"""
    model = _get_model()
    truncated = [truncate_for_embed(t) for t in texts]
    out = model.encode(
        truncated,
        batch_size=len(truncated),
        max_length=MAX_EMBED_CHARS,  # 与 embed_ollama 对齐
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )
    return out["dense_vecs"].tolist()


class BGEFlagEmbeddings(Embeddings):
    """LangChain Embeddings 接口实现 — 包装 FlagEmbedding FlagModel。

    接口对齐 OllamaEmbeddings:
        - embed_query(text) -> list[float]
        - embed_documents(texts: list[str]) -> list[list[float]]
        - aembed_query / aembed_documents 异步版（asyncio.to_thread 包装）
    """

    def embed_query(self, text: str) -> list[float]:
        with _async_lock:
            vecs = _encode_sync([text])
        return vecs[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        with _async_lock:
            return _encode_sync(list(texts))

    async def aembed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query, text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents, texts)


_singleton: BGEFlagEmbeddings | None = None


def get_embeddings() -> BGEFlagEmbeddings:
    """获取 BGE Embeddings 单例（与 ollama_embed.get_embeddings 同名同位置）。"""
    global _singleton
    if _singleton is None:
        with _async_lock:
            if _singleton is None:
                _singleton = BGEFlagEmbeddings()
    return _singleton


# ===== 兼容旧 ollama_embed 接口 =====
async def aembed_query(text: str) -> list[float]:
    """异步编码单条 query（保留兼容）"""
    return await get_embeddings().aembed_query(text)


async def aembed_documents(texts: list[str]) -> list[list[float]]:
    """异步编码多条文档（保留兼容）"""
    return await get_embeddings().aembed_documents(texts)
