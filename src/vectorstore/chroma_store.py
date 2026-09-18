"""Chroma 向量库封装

特性：
- 持久化到本地磁盘
- 自动管理 embeddings 客户端（Ollama）
- 支持 add / search / count / reset
- 返回带 score 的 RetrievalResult
"""

from __future__ import annotations

from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import settings
from ..embeddings.ollama_embed import get_embeddings
from ..schemas import Chunk, RetrievalResult


@lru_cache(maxsize=1)
def get_chroma_client():
    """获取 Chroma 客户端单例（持久化模式）"""
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


@lru_cache(maxsize=1)
def get_vector_store():
    """获取 Collection 单例"""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},  # 余弦相似度
    )


class VectorStore:
    """向量库封装（不依赖 LangChain，直接用 chromadb）"""

    def __init__(self):
        self._collection = None
        self._embeddings = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = get_vector_store()
        return self._collection

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = get_embeddings()
        return self._embeddings

    # ===== 写入 =====
    def add(self, chunks: list[Chunk]) -> int:
        """添加 chunks 到向量库，返回写入数量"""
        if not chunks:
            return 0

        contents = [c.content for c in chunks]
        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {**c.metadata, "source": c.source, "doc_id": c.doc_id, "chunk_index": c.chunk_index}
            for c in chunks
        ]

        # 用 Ollama 编码
        embeddings = self.embeddings.embed_documents(contents)

        # Chroma 写入（batched）
        BATCH_SIZE = 64
        total = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            self.collection.add(
                ids=ids[i : i + BATCH_SIZE],
                documents=contents[i : i + BATCH_SIZE],
                embeddings=embeddings[i : i + BATCH_SIZE],
                metadatas=metadatas[i : i + BATCH_SIZE],
            )
            total += len(ids[i : i + BATCH_SIZE])

        return total

    # ===== 检索 =====
    def search(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        """向量检索"""
        if self.count() == 0:
            return []

        query_emb = self.embeddings.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        return self._parse_results(results, retrieval_method="vector")

    # ===== 元操作 =====
    def count(self) -> int:
        """获取当前 collection 的文档数"""
        return self.collection.count()

    def reset(self) -> None:
        """清空 collection（慎用）"""
        client = get_chroma_client()
        client.delete_collection(settings.chroma_collection_name)
        # 清两个缓存：
        # 1) get_vector_store 函数的 lru_cache
        # 2) VectorStore 实例的 _collection 属性
        get_vector_store.cache_clear()
        self._collection = None

    # ===== 内部 =====
    def _parse_results(
        self,
        results: dict,
        retrieval_method: str,
    ) -> list[RetrievalResult]:
        """把 Chroma 返回的 dict 转成 RetrievalResult 列表"""
        parsed: list[RetrievalResult] = []

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        # Chroma 返回的是 distance（越小越相似），转换为 similarity score
        distances = results.get("distances", [[]])[0]

        for rank, (chunk_id, doc_text, meta, dist) in enumerate(
            zip(ids, docs, metadatas, distances, strict=False)
        ):
            # 余弦距离 [0, 2]，转成相似度 [0, 1]
            score = max(0.0, 1.0 - dist)

            meta = meta or {}
            chunk = Chunk(
                content=doc_text,
                metadata={k: v for k, v in meta.items() if k not in ("source", "doc_id", "chunk_index")},
                source=meta.get("source", ""),
                chunk_id=chunk_id,
                doc_id=meta.get("doc_id", ""),
                chunk_index=int(meta.get("chunk_index", 0)),
            )

            parsed.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    rank=rank,
                    retrieval_method=retrieval_method,
                )
            )

        return parsed


# 单例
_vector_store_instance: VectorStore | None = None


def get_vector_store_instance() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance