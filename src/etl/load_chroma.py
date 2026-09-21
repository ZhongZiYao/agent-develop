"""Chroma 向量库 Load - 把 embeddings.parquet 写入 Chroma 持久化。

沿用 Phase 1 的 Chroma 封装。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from src.config import settings


DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
CLEAN_DIR = DATA_ROOT / "clean"
CHROMA_PERSIST_DIR = Path(getattr(settings, "chroma_persist_dir", DATA_ROOT / "chroma"))


def load_to_chroma(
    chunks_parquet: Path = CLEAN_DIR / "chunks.parquet",
    embeddings_parquet: Path = CLEAN_DIR / "embeddings.parquet",
    collection_name: str = "gameguide_phase7",
    batch_size: int = 5000,
) -> int:
    """把 chunks + embeddings 写入 Chroma。

    Returns:
        写入的 chunk 总数
    """
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    if not chunks_parquet.exists() or not embeddings_parquet.exists():
        logger.warning("chunks.parquet 或 embeddings.parquet 不存在，跳过")
        return 0

    chunks_df = pd.read_parquet(chunks_parquet)
    embeddings_df = pd.read_parquet(embeddings_parquet)
    df = chunks_df.merge(embeddings_df, on="chunk_id", how="inner")

    logger.info(f"准备写入 Chroma: {len(df)} chunks")

    # 创建客户端
    client = chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # 删除旧 collection（幂等）
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine", "description": "Phase 7 ETL corpus"},
    )

    # 分批写入
    total = 0
    for start in range(0, len(df), batch_size):
        batch = df.iloc[start : start + batch_size]
        collection.add(
            ids=batch["chunk_id"].tolist(),
            documents=batch["chunk_text"].tolist(),
            embeddings=batch["embedding"].tolist(),
            metadatas=[
                {
                    "doc_id": row.doc_id,
                    "source": row.source,
                    "game": row.game,
                    "title": row.title or "",
                    "section_title": row.section_title or "",
                    "url": row.url or "",
                }
                for row in batch.itertuples()
            ],
        )
        total += len(batch)
        logger.info(f"Chroma 进度: {total}/{len(df)}")

    logger.info(f"Chroma 写入完成: {total} chunks @ {CHROMA_PERSIST_DIR}")
    return total


if __name__ == "__main__":
    load_to_chroma()