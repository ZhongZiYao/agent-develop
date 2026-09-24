"""独立 resume 脚本：只跑 Embedding（跳过 DuckDB/Chroma）。

用法：
    python -m scripts.etl_embed_only_resume --workers 8

背景：之前 56,000 chunks 已经从老 embeddings.parquet 被当作 done 跳过，
      但落盘的 embeddings.parquet 只含新跑的 45,279。
      这次只跑 embedding 剩下的 56,000，不触发 DuckDB/Chroma，
      便于先验证 resume 逻辑 + 减少单次跑失败的代价。
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from loguru import logger

from src.config import settings
from src.etl.embed_ollama import embed_chunks, load_chunks_parquet


CLEAN_DIR = Path(settings.data_dir) / "clean"


def main(workers: int, use_sampled: bool):
    started = time.time()

    chunks_parquet = CLEAN_DIR / ("chunks_sampled.parquet" if use_sampled else "chunks.parquet")
    embeddings_parquet = CLEAN_DIR / "embeddings.parquet"
    embeddings_chunks_dir = CLEAN_DIR / "embeddings_chunks"

    if not chunks_parquet.exists():
        logger.error(f"{chunks_parquet} 不存在")
        return

    chunks_df = load_chunks_parquet(chunks_parquet)
    logger.info(f"目标 chunks: {len(chunks_df)} ({chunks_parquet.name})")

    t0 = time.time()
    embeddings_df = embed_chunks(
        chunks_df,
        max_workers=workers,
        checkpoint_dir=embeddings_chunks_dir,
        final_path=embeddings_parquet,
        resume=True,
    )
    elapsed = time.time() - t0
    logger.info(
        f"✅ Embedding 完成: {len(embeddings_df)} chunks in {elapsed/60:.1f} min "
        f"({len(embeddings_df)/elapsed:.1f} chunks/s)"
    )

    total = time.time() - started
    logger.info(f"总耗时 {total/60:.1f} min")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--use-sampled", action="store_true", default=True)
    args = parser.parse_args()
    main(args.workers, args.use_sampled)
