"""Qdrant sidecar 向量库 Load - 用于演示 Chroma vs Qdrant 性能对比。

Qdrant 跑在 Docker（qdrant/qdrant:latest），端口 6333。
本模块仅作 client 端写入。

启动 Qdrant：
    docker run -d -p 6333:6333 -p 6334:6334 \
        -v $(pwd)/data/qdrant:/qdrant/storage \
        --name gameguide-qdrant qdrant/qdrant:latest
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from src.config import settings


DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
CLEAN_DIR = DATA_ROOT / "clean"

QDRANT_HOST = getattr(settings, "qdrant_host", "localhost")
QDRANT_PORT = getattr(settings, "qdrant_port", 6333)
COLLECTION_NAME = "gameguide_phase7"


def load_to_qdrant(
    chunks_parquet: Path = CLEAN_DIR / "chunks.parquet",
    embeddings_parquet: Path = CLEAN_DIR / "embeddings.parquet",
    collection_name: str = COLLECTION_NAME,
    batch_size: int = 1000,
) -> int:
    """把 chunks + embeddings 写入 Qdrant sidecar。

    Returns:
        写入的 chunk 总数
    """
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        PointStruct,
        VectorParams,
    )

    if not chunks_parquet.exists() or not embeddings_parquet.exists():
        logger.warning("chunks.parquet 或 embeddings.parquet 不存在，跳过")
        return 0

    chunks_df = pd.read_parquet(chunks_parquet)
    embeddings_df = pd.read_parquet(embeddings_parquet)
    df = chunks_df.merge(embeddings_df, on="chunk_id", how="inner")
    logger.info(f"准备写入 Qdrant: {len(df)} chunks")

    # 连接 Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # 创建 / 重建 collection（1024 维 + cosine）
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

    # 分批写入
    total = 0
    for start in range(0, len(df), batch_size):
        batch = df.iloc[start : start + batch_size]
        points = [
            PointStruct(
                id=hash(row.chunk_id) & 0x7FFFFFFFFFFFFFFF,  # Qdrant 要正整数 ID
                vector=row.embedding,
                payload={
                    "chunk_id": row.chunk_id,
                    "doc_id": row.doc_id,
                    "chunk_text": row.chunk_text,
                    "source": row.source,
                    "game": row.game,
                    "title": row.title or "",
                    "section_title": row.section_title or "",
                    "url": row.url or "",
                },
            )
            for row in batch.itertuples()
        ]
        client.upsert(collection_name=collection_name, points=points, wait=True)
        total += len(batch)
        logger.info(f"Qdrant 进度: {total}/{len(df)}")

    logger.info(f"Qdrant 写入完成: {total} chunks")
    return total


if __name__ == "__main__":
    load_to_qdrant()