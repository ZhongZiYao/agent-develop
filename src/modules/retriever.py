"""Retriever Module

混合检索模块：
1. 向量检索（Vector Search）
2. BM25 关键词检索（可选）
3. RRF 融合（Reciprocal Rank Fusion）
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from ..vectorstore.chroma_store import get_vector_store_instance
from .base import ModuleRegistry, RAGModule


@ModuleRegistry.register
class HybridRetrieverModule(RAGModule):
    """混合检索模块

    输入 state:
        - query: str (主查询)
        - expanded_queries: list[str] (扩展查询，可选)

    输出 state 更新:
        - retrieved_docs: list[dict] (检索到的文档)
    """

    name = "hybrid_retriever"

    def __init__(self, config: dict | None = None):
        super().__init__(config)

        # 向量库
        self.vector_store = get_vector_store_instance()

        # BM25 索引（当前未实现，预留接口）
        self.bm25_index = None

        # 检索参数
        self.vector_top_k = self.config.get("vector_top_k", 50)
        self.bm25_top_k = self.config.get("bm25_top_k", 30)
        self.use_expanded = self.config.get("use_expanded", True)
        self.fusion_method = self.config.get("fusion", "rrf")  # rrf 或 linear
        self.rrf_k = self.config.get("rrf_k", 60)

    async def __call__(self, state: dict) -> dict:
        """执行混合检索"""
        query = state.get("query", "")
        expanded_queries = state.get("expanded_queries", [])

        if not query:
            logger.warning(f"[{self.name}] Empty query, returning no results")
            return {"retrieved_docs": []}

        # 构建查询列表
        queries = [query]
        if self.use_expanded and expanded_queries:
            queries.extend(expanded_queries[:3])  # 最多用前 3 个扩展

        logger.debug(f"[{self.name}] Retrieving with {len(queries)} queries")

        # 1. 向量检索
        vector_results = self._vector_search(queries)
        logger.debug(f"[{self.name}] Vector search: {len(vector_results)} results")

        # 2. BM25 检索（暂未实现）
        bm25_results = []
        if self.bm25_index:
            bm25_results = self._bm25_search(queries)
            logger.debug(f"[{self.name}] BM25 search: {len(bm25_results)} results")

        # 3. 融合
        if bm25_results:
            fused = self._fuse(vector_results, bm25_results)
            logger.debug(f"[{self.name}] Fused: {len(fused)} results")
        else:
            fused = vector_results

        # 转换为标准格式
        retrieved_docs = self._format_results(fused)

        return {"retrieved_docs": retrieved_docs}

    def _vector_search(self, queries: list[str]) -> list[Any]:
        """向量检索（多查询 RRF 融合）"""
        all_results = []

        for query in queries:
            results = self.vector_store.search(query, top_k=self.vector_top_k)
            all_results.append(results)

        # RRF 融合多个查询的结果
        if len(all_results) == 1:
            return all_results[0]

        return self._rrf_fuse(all_results)

    def _bm25_search(self, queries: list[str]) -> list[Any]:
        """BM25 关键词检索（预留接口）"""
        # TODO: 实现 BM25 索引
        return []

    def _fuse(self, vector_results: list, bm25_results: list) -> list:
        """融合向量和 BM25 结果"""
        if self.fusion_method == "rrf":
            return self._rrf_fuse([vector_results, bm25_results])
        elif self.fusion_method == "linear":
            return self._linear_fuse(vector_results, bm25_results)
        else:
            return vector_results

    def _rrf_fuse(self, result_lists: list[list]) -> list:
        """Reciprocal Rank Fusion

        RRF(d) = Σ 1 / (k + rank_i(d))
        其中 k 是常数（默认 60），rank_i 是文档在第 i 个结果列表中的排名
        """
        doc_scores: dict[str, float] = {}

        for results in result_lists:
            for rank, result in enumerate(results, start=1):
                doc_id = result.chunk.chunk_id
                score = 1.0 / (self.rrf_k + rank)
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + score

        # 按 RRF 分数排序
        sorted_ids = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # 返回重排后的文档（取第一个列表的对象）
        id_to_result = {r.chunk.chunk_id: r for results in result_lists for r in results}
        return [id_to_result[doc_id] for doc_id, _ in sorted_ids if doc_id in id_to_result]

    def _linear_fuse(self, vector_results: list, bm25_results: list, alpha: float = 0.7) -> list:
        """线性加权融合（预留）"""
        # TODO: 实现线性融合
        return vector_results

    def _format_results(self, results: list) -> list[dict]:
        """转换为标准格式"""
        formatted = []
        for result in results:
            formatted.append({
                "id": result.chunk.chunk_id,
                "content": result.chunk.content,
                "metadata": result.chunk.metadata,
                "score": result.score,
                "title": result.chunk.metadata.get("title", "未知"),
                "source": result.chunk.metadata.get("filename", ""),
            })
        return formatted

    def get_config(self):
        """导出配置"""
        config = super().get_config()
        config.params.update({
            "vector_top_k": self.vector_top_k,
            "bm25_top_k": self.bm25_top_k,
            "use_expanded": self.use_expanded,
            "fusion": self.fusion_method,
            "rrf_k": self.rrf_k,
        })
        return config
