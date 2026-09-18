"""核心数据结构：Document / Chunk / RetrievalResult"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """原始文档（loader 输出）"""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""  # 文件路径或 URL

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
        }


@dataclass
class Chunk:
    """切分后的文本块（splitter 输出，最终入库的单位）"""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    chunk_id: str = ""  # 全局唯一 ID
    doc_id: str = ""  # 所属文档 ID
    chunk_index: int = 0  # 在所属文档中的顺序

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "chunk_index": self.chunk_index,
        }


@dataclass
class RetrievalResult:
    """召回结果（含分数）"""
    chunk: Chunk
    score: float = 0.0
    rank: int = 0
    retrieval_method: str = "vector"  # vector / bm25 / hybrid

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "rank": self.rank,
            "retrieval_method": self.retrieval_method,
        }