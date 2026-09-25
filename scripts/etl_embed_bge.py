"""BGE GPU 跑 embedding 脚本（替代 Ollama CPU 路径）。

与 scripts/etl_embed_only_resume 同接口，但走 FlagEmbedding GPU。

用法：
    # 1/10 采样（demo 推荐）
    python -m scripts.etl_embed_bge --use-sampled --batch-size 32

    # 全量
    python -m scripts.etl_embed_bge --batch-size 32

    # 自定义 batch（显存吃紧时调小到 16）
    python -m scripts.etl_embed_bge --batch-size 16

性能：
    RTX 5070 8GB + bge-m3 fp16 + batch=32：~300-500 chunks/s
    100k chunks：~3-5 分钟（vs Ollama CPU 的 131.8 分钟）
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from loguru import logger

from src.config import settings
from src.etl.embed_bge import embed_chunks, load_chunks_parquet


CLEAN_DIR = Path(settings.data_dir) / "clean"


def main(batch_size: int, use_sampled: bool, workers_unused: int = 0):
    """workers 参数被忽略（GPU 单设备，不需要 ThreadPool）。

    保留这个参数是为了和 etl_embed_only_resume 的 CLI 兼容。
    """
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
        batch_size=batch_size,
        checkpoint_dir=embeddings_chunks_dir,
        final_path=embeddings_parquet,
        resume=True,
    )
    elapsed = time.time() - t0
    logger.info(
        f"✅ BGE GPU Embedding 完成: {len(embeddings_df)} chunks in {elapsed/60:.1f} min "
        f"({len(embeddings_df)/elapsed:.1f} chunks/s)"
    )

    total = time.time() - started
    logger.info(f"总耗时 {total/60:.1f} min")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BGE GPU embedding 脚本（替代 Ollama CPU）")
    parser.add_argument("--batch-size", type=int, default=32, help="GPU batch size（RTX 5070 8GB 起步 32）")
    parser.add_argument("--use-sampled", action="store_true", default=True, help="使用 1/10 采样（默认 True）")
    parser.add_argument("--workers", type=int, default=0, help="已忽略（GPU 不需要 ThreadPool）")
    args = parser.parse_args()
    main(args.batch_size, args.use_sampled, args.workers)