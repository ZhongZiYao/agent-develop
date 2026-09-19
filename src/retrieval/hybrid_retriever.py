"""混合检索模块

结合向量检索和关键词检索，使用 RRF (Reciprocal Rank Fusion) 融合结果。

向量检索：语义相似度（召回泛化能力强）
关键词检索：精确匹配（召回准确性高）
RRF 融合：平衡两种策略的优势
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from loguru import logger

from ..schemas import Chunk, RetrievalResult


class HybridRetriever:
    """混合检索器（向量 + BM25）"""

    def __init__(self, vector_store, bm25_index: Optional[object] = None):
        """
        Args:
            vector_store: 向量存储实例（ChromaVectorStore）
            bm25_index: BM25 索引（可选，未实现时退化为仅向量检索）
        """
        self.vector_store = vector_store
        self.bm25_index = bm25_index

    def search(
        self,
        query: str,
        top_k: int = 50,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        game: Optional[str] = None,
    ) -> list[RetrievalResult]:
        """混合检索

        Args:
            query: 查询文本
            top_k: 最终返回数量
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            game: 游戏过滤（可选）

        Returns:
            融合后的检索结果列表
        """
        # 1. 向量检索
        vector_results = self._vector_search(query, top_k=top_k, game=game)
        logger.debug(f"Vector search returned {len(vector_results)} results")

        # 2. BM25 检索（如果可用）
        if self.bm25_index:
            bm25_results = self._bm25_search(query, top_k=top_k, game=game)
            logger.debug(f"BM25 search returned {len(bm25_results)} results")

            # 3. RRF 融合
            fused = self._rrf_fusion(
                vector_results,
                bm25_results,
                k=60,  # RRF 常数
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
            )
            logger.debug(f"RRF fusion produced {len(fused)} results")
            return fused[:top_k]
        else:
            # 退化为仅向量检索
            logger.warning("BM25 index not available, falling back to vector-only search")
            return vector_results

    def _vector_search(
        self,
        query: str,
        top_k: int,
        game: Optional[str] = None,
    ) -> list[RetrievalResult]:
        """向量检索"""
        return self.vector_store.search(query, top_k=top_k)

    def _bm25_search(
        self,
        query: str,
        top_k: int,
        game: Optional[str] = None,
    ) -> list[RetrievalResult]:
        """BM25 关键词检索

        TODO: 实现 BM25 索引
        当前占位实现，返回空列表
        """
        if not self.bm25_index:
            return []

        # 调用 BM25 索引的 search 方法
        # bm25_scores = self.bm25_index.get_scores(tokenize(query))
        # ... 构造 RetrievalResult
        return []

    def _rrf_fusion(
        self,
        vector_results: list[RetrievalResult],
        bm25_results: list[RetrievalResult],
        k: int = 60,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ) -> list[RetrievalResult]:
        """RRF (Reciprocal Rank Fusion) 算法融合结果

        公式：
        RRF_score(doc) = Σ (weight / (k + rank))

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25 检索结果
            k: RRF 常数（通常取 60）
            vector_weight: 向量权重
            bm25_weight: BM25 权重

        Returns:
            融合后的结果，按 RRF 分数降序排列
        """
        rrf_scores = defaultdict(float)
        doc_map = {}  # chunk_id -> RetrievalResult

        # 累加向量检索的 RRF 分数
        for rank, result in enumerate(vector_results, start=1):
            chunk_id = result.chunk.chunk_id
            rrf_scores[chunk_id] += vector_weight / (k + rank)
            doc_map[chunk_id] = result

        # 累加 BM25 检索的 RRF 分数
        for rank, result in enumerate(bm25_results, start=1):
            chunk_id = result.chunk.chunk_id
            rrf_scores[chunk_id] += bm25_weight / (k + rank)
            if chunk_id not in doc_map:
                doc_map[chunk_id] = result

        # 按 RRF 分数排序
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # 构造最终结果（更新 score 为 RRF 分数）
        fused_results = []
        for chunk_id in sorted_ids:
            result = doc_map[chunk_id]
            # 创建新的 RetrievalResult，score 替换为 RRF 分数
            fused_result = RetrievalResult(
                chunk=result.chunk,
                score=rrf_scores[chunk_id],  # RRF 分数
            )
            fused_results.append(fused_result)

        return fused_results

    def multi_query_search(
        self,
        queries: list[str],
        top_k: int = 50,
        game: Optional[str] = None,
    ) -> list[RetrievalResult]:
        """多查询检索（支持查询扩展）

        对每个查询分别检索，然后用 RRF 融合

        Args:
            queries: 多个查询（原始 + 扩展）
            top_k: 最终返回数量
            game: 游戏过滤

        Returns:
            融合后的检索结果
        """
        all_results = []

        for query in queries:
            results = self.search(query, top_k=top_k, game=game)
            all_results.append(results)

        # 使用 RRF 融合多个查询的结果
        return self._multi_rrf_fusion(all_results, top_k=top_k)

    def _multi_rrf_fusion(
        self,
        results_list: list[list[RetrievalResult]],
        k: int = 60,
        top_k: int = 50,
    ) -> list[RetrievalResult]:
        """多查询 RRF 融合"""
        rrf_scores = defaultdict(float)
        doc_map = {}

        # 每个查询的结果权重相同
        weight = 1.0 / len(results_list)

        for results in results_list:
            for rank, result in enumerate(results, start=1):
                chunk_id = result.chunk.chunk_id
                rrf_scores[chunk_id] += weight / (k + rank)
                if chunk_id not in doc_map:
                    doc_map[chunk_id] = result

        # 排序并返回
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        fused_results = []
        for chunk_id in sorted_ids[:top_k]:
            result = doc_map[chunk_id]
            fused_result = RetrievalResult(
                chunk=result.chunk,
                score=rrf_scores[chunk_id],
            )
            fused_results.append(fused_result)

        return fused_results
