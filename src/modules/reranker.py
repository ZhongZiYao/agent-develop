"""Reranker Module

重排模块：使用 Cross-Encoder 对初排结果进行精排
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from ..config import settings
from ..retrieval.reranker import get_reranker
from .base import ModuleRegistry, RAGModule


@ModuleRegistry.register
class RerankerModule(RAGModule):
    """重排模块

    输入 state:
        - query: str
        - retrieved_docs: list[dict] (初排文档)

    输出 state 更新:
        - retrieved_docs: list[dict] (重排后文档)
    """

    name = "reranker"

    def __init__(self, config: dict | None = None):
        super().__init__(config)

        self.model_name = self.config.get("model", settings.rerank_model)
        self.device = self.config.get("device", settings.rerank_device)
        self.top_n = self.config.get("top_n", settings.rerank_top_n)
        self.enabled = self.config.get("enabled", settings.rerank_enabled)

        # 延迟加载模型（首次调用时加载）
        self._reranker = None

    async def __call__(self, state: dict) -> dict:
        """执行重排"""
        if not self.enabled:
            logger.debug(f"[{self.name}] Reranker disabled, skipping")
            return {}

        query = state.get("query", "")
        retrieved_docs = state.get("retrieved_docs", [])

        if not query or not retrieved_docs:
            logger.warning(f"[{self.name}] Empty query or no docs, skipping rerank")
            return {}

        # 懒加载模型
        if self._reranker is None:
            logger.info(f"[{self.name}] Loading reranker model: {self.model_name}")
            self._reranker = get_reranker(self.model_name, self.device)

        # 转换为 SearchResult 格式（reranker 需要）
        from ..vectorstore.models import SearchResult, Chunk

        search_results = [
            SearchResult(
                chunk=Chunk(
                    id=doc["id"],
                    content=doc["content"],
                    metadata=doc["metadata"],
                ),
                score=doc["score"],
            )
            for doc in retrieved_docs
        ]

        # 重排
        logger.debug(f"[{self.name}] Reranking {len(search_results)} docs → top {self.top_n}")
        reranked = self._reranker.rerank(query, search_results, top_n=self.top_n)

        # 转回标准格式
        reranked_docs = [
            {
                "id": r.chunk.id,
                "content": r.chunk.content,
                "metadata": r.chunk.metadata,
                "score": r.score,
                "title": r.chunk.metadata.get("title", "未知"),
                "source": r.chunk.metadata.get("filename", ""),
            }
            for r in reranked
        ]

        logger.debug(
            f"[{self.name}] Reranked: top score={reranked_docs[0]['score']:.4f}"
            if reranked_docs else "[{self.name}] No results after reranking"
        )

        return {"retrieved_docs": reranked_docs}

    def get_config(self):
        """导出配置"""
        config = super().get_config()
        config.params.update({
            "model": self.model_name,
            "device": self.device,
            "top_n": self.top_n,
            "enabled": self.enabled,
        })
        return config
