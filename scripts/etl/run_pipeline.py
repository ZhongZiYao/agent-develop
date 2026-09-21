"""Phase 7 ETL 全流程 Pipeline - 一键跑通 Extract → Transform → Embed → Load。

用法：
    # 跑全流程（推荐先用 POC 数据）
    uv run python scripts/etl/run_pipeline.py --max-pages 1000 --game onmyoji

    # 分阶段跑
    uv run python scripts/etl/run_pipeline.py --stage transform
    uv run python scripts/etl/run_pipeline.py --stage embed
    uv run python scripts/etl/run_pipeline.py --stage load

    # 只跑 DuckDB 数仓（向量库跳过）
    uv run python scripts/etl/run_pipeline.py --stage load --skip-chroma --skip-qdrant

    # 只跑 Qdrant sidecar（演示对比）
    uv run python scripts/etl/run_pipeline.py --stage load --skip-chroma
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from loguru import logger


PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_crawl(game: str, max_pages: int, source: str = "fandom") -> None:
    """跑 Scrapy 爬虫。"""
    logger.info(f"=== EXTRACT: 爬取 {source} {game} 上限 {max_pages} 页 ===")
    cmd = [
        "scrapy",
        "crawl",
        source,
        "-a",
        f"game={game}",
        "-a",
        f"max_pages={max_pages}",
        "-s",
        "LOG_LEVEL=INFO",
    ]
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def run_transform() -> None:
    """跑 Transform：JSONL → chunks.parquet + meta.parquet。"""
    logger.info("=== TRANSFORM: JSONL → Parquet ===")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.etl.transform import run

    run()


def run_embed() -> None:
    """跑 Embedding：bge-m3 GPU 批量。"""
    logger.info("=== EMBED: bge-m3 批量 embedding ===")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.etl.embed import run

    run()


def run_load_duckdb() -> None:
    """DuckDB 数仓加载。"""
    logger.info("=== LOAD: DuckDB 数仓 ===")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.etl.load_duckdb import run

    run()


def run_load_chroma() -> None:
    """Chroma 向量库加载。"""
    logger.info("=== LOAD: Chroma ===")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.etl.load_chroma import load_to_chroma

    load_to_chroma()


def run_load_qdrant() -> None:
    """Qdrant sidecar 加载。"""
    logger.info("=== LOAD: Qdrant ===")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.etl.load_qdrant import load_to_qdrant

    load_to_qdrant()


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 7 ETL Pipeline")
    parser.add_argument(
        "--stage",
        choices=["all", "crawl", "transform", "embed", "load"],
        default="all",
        help="执行阶段",
    )
    parser.add_argument("--game", default="onmyoji", help="目标游戏")
    parser.add_argument("--max-pages", type=int, default=1000, help="爬取页面上限")
    parser.add_argument("--source", default="fandom", choices=["fandom"], help="数据源")
    parser.add_argument("--skip-chroma", action="store_true", help="跳过 Chroma 写入")
    parser.add_argument("--skip-qdrant", action="store_true", help="跳过 Qdrant 写入")
    parser.add_argument(
        "--skip-duckdb", action="store_true", help="跳过 DuckDB 数仓写入"
    )
    args = parser.parse_args()

    t0 = time.time()
    stages = []

    if args.stage in ("all", "crawl"):
        run_crawl(args.game, args.max_pages, args.source)
        stages.append("crawl")

    if args.stage in ("all", "transform"):
        run_transform()
        stages.append("transform")

    if args.stage in ("all", "embed"):
        run_embed()
        stages.append("embed")

    if args.stage in ("all", "load"):
        if not args.skip_duckdb:
            run_load_duckdb()
            stages.append("load_duckdb")
        if not args.skip_chroma:
            run_load_chroma()
            stages.append("load_chroma")
        if not args.skip_qdrant:
            try:
                run_load_qdrant()
                stages.append("load_qdrant")
            except Exception as exc:
                logger.warning(f"Qdrant 写入失败（Docker 没起？跳过）: {exc}")

    elapsed = time.time() - t0
    logger.info(f"✅ ETL Pipeline 完成: {stages}, 耗时 {elapsed:.1f}s")


if __name__ == "__main__":
    main()