"""一次性跑 Embedding + DuckDB + Chroma（基于已有 chunks parquet）。

本次基于采样的 1/10 数据（chunks_sampled.parquet）— 之前全量跑了 16 min
还没写出 transform 进度就中断，所以 chunks.parquet 是上上次的 101万 chunks 全量产物。

本次选择：
    - 用 scripts/sample_chunks.py 生成 1/10 采样 → chunks_sampled.parquet
    - 跑 embed（8 workers + checkpoint 2000 + 限长 512 字符）
    - 写 DuckDB（幂等 DELETE+INSERT）
    - 同步 Chroma

支持 checkpoint 续跑：embeddings.parquet 已存在的 chunk_id 自动跳过。

Usage:
    python -m scripts.etl_financial_skip_transform --workers 8 --use-sampled
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from loguru import logger

from src.config import settings
from src.etl.embed_ollama import embed_chunks, load_chunks_parquet
from src.etl.load_chroma import load_to_chroma
from src.etl.load_duckdb_financial import load_chunks_to_duckdb, load_embeddings_to_duckdb


CLEAN_DIR = Path(settings.data_dir) / "clean"


def main(workers: int, use_sampled: bool):
    started = time.time()

    chunks_parquet = CLEAN_DIR / ("chunks_sampled.parquet" if use_sampled else "chunks.parquet")
    embeddings_parquet = CLEAN_DIR / "embeddings.parquet"
    embeddings_chunks_dir = CLEAN_DIR / "embeddings_chunks"
    if not chunks_parquet.exists():
        logger.error(f"{chunks_parquet} 不存在")
        return

    # Step 1: Embedding（自动 resume，append 模式 checkpoint）
    logger.info("=" * 60)
    logger.info(f"Step 2/4: Embedding (workers={workers}, source={chunks_parquet.name})")
    logger.info("=" * 60)
    chunks_df = load_chunks_parquet(chunks_parquet)
    t0 = time.time()
    embeddings_df = embed_chunks(
        chunks_df,
        max_workers=workers,
        checkpoint_dir=embeddings_chunks_dir,
        final_path=embeddings_parquet,
    )
    elapsed = time.time() - t0
    logger.info(f"Embedding 完成: {elapsed/60:.1f} min ({len(chunks_df)/elapsed:.1f} chunks/s)")

    # Step 2: DuckDB
    logger.info("=" * 60)
    logger.info("Step 3/4: DuckDB 数仓")
    logger.info("=" * 60)
    load_chunks_to_duckdb(chunks_parquet)
    load_embeddings_to_duckdb(embeddings_parquet)

    # Step 3: Chroma
    logger.info("=" * 60)
    logger.info("Step 4/4: Chroma 向量库")
    logger.info("=" * 60)
    load_to_chroma(
        chunks_parquet=chunks_parquet,
        embeddings_parquet=embeddings_parquet,
    )

    total = time.time() - started
    logger.info("=" * 60)
    logger.info(f"✅ ETL 完成 — {total/60:.1f} min")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--use-sampled", action="store_true", help="使用 1/10 采样（推荐 demo）")
    args = parser.parse_args()
    main(args.workers, args.use_sampled)