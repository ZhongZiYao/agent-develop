"""重排模块

使用 Cross-Encoder 模型对检索结果进行精准重排。

推荐模型：
1. BAAI/bge-reranker-v2-m3 (中文优势，多语言)
2. BAAI/bge-reranker-v2-minicpm-layerwise (轻量级)
3. sentence-transformers/ms-marco-MiniLM-L-12-v2 (英文)

原理：
- Bi-Encoder (Embedding): query 和 doc 分别编码，计算相似度（快，不精准）
- Cross-Encoder (Reranker): query + doc 一起输入，直接预测相关性（慢，精准）

工作流：
1. Bi-Encoder 召回 top_k=100
2. Cross-Encoder 重排到 top_n=10
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from ..schemas import RetrievalResult


class Reranker:
    """重排器（Cross-Encoder）"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", device: str = "cpu"):
        """
        Args:
            model_name: HuggingFace 模型名称或本地路径
                - HuggingFace: "BAAI/bge-reranker-v2-m3"
                - 本地路径: "./models/bge-reranker-v2-m3"
            device: 运行设备 (cpu/cuda)
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None
        logger.info(f"Initializing Reranker with model: {model_name}")

    def _load_model(self):
        """延迟加载模型（避免启动时加载）"""
        if self._model is not None:
            return

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            import torch

            logger.info(f"Loading reranker model: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
            logger.info("Reranker model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            logger.warning("Reranker will be disabled, falling back to original ranking")
            self._model = None

    def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        top_n: int = 10,
    ) -> list[RetrievalResult]:
        """重排检索结果

        Args:
            query: 查询文本
            results: 检索结果列表
            top_n: 返回前 N 个

        Returns:
            重排后的结果（按相关性降序）
        """
        if not results:
            return []

        # 如果结果数量已经 <= top_n，且模型未加载，直接返回
        if len(results) <= top_n and self._model is None:
            return results[:top_n]

        # 延迟加载模型
        self._load_model()

        # 如果模型加载失败，降级为原始排序
        if self._model is None:
            logger.warning("Reranker model not available, returning original ranking")
            return results[:top_n]

        # 执行重排
        try:
            reranked = self._compute_scores(query, results)
            return reranked[:top_n]
        except Exception as e:
            logger.error(f"Reranking failed: {e}, falling back to original ranking")
            return results[:top_n]

    def _compute_scores(
        self,
        query: str,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """计算重排分数

        Args:
            query: 查询
            results: 检索结果

        Returns:
            重排后的结果（附带新的 score）
        """
        import torch

        # 准备输入 pairs: [(query, doc1), (query, doc2), ...]
        pairs = [(query, result.chunk.content) for result in results]

        # Tokenize
        inputs = self._tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 推理
        with torch.no_grad():
            outputs = self._model(**inputs)
            # BGE reranker 输出 logits，取第一列作为相关性分数
            scores = outputs.logits[:, 0].cpu().numpy()

        # 将新分数附加到结果上
        reranked_results = []
        for i, result in enumerate(results):
            reranked_result = RetrievalResult(
                chunk=result.chunk,
                score=float(scores[i]),  # 替换为 reranker 分数
            )
            reranked_results.append(reranked_result)

        # 按新分数降序排序
        reranked_results.sort(key=lambda x: x.score, reverse=True)

        logger.debug(f"Reranked {len(results)} results, top score: {reranked_results[0].score:.4f}")
        return reranked_results

    def batch_rerank(
        self,
        queries: list[str],
        results_list: list[list[RetrievalResult]],
        top_n: int = 10,
    ) -> list[list[RetrievalResult]]:
        """批量重排（适用于多个查询）

        Args:
            queries: 查询列表
            results_list: 每个查询的检索结果
            top_n: 每个查询返回前 N 个

        Returns:
            重排后的结果列表
        """
        return [self.rerank(q, r, top_n) for q, r in zip(queries, results_list)]


# 全局单例（延迟初始化）
_global_reranker: Optional[Reranker] = None


def get_reranker(
    model_name: str = "BAAI/bge-reranker-v2-m3",
    device: str = "cpu",
) -> Reranker:
    """获取全局 Reranker 实例

    Args:
        model_name: 模型名称
        device: 运行设备

    Returns:
        Reranker 实例
    """
    global _global_reranker
    if _global_reranker is None:
        _global_reranker = Reranker(model_name=model_name, device=device)
    return _global_reranker
