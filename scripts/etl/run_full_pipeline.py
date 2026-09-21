"""Phase 7.3 多源 ETL 全链路 Pipeline。

用法：
    # 全链路：crawl → transform → embed → load（多源）
    uv run python scripts/etl/run_full_pipeline.py

    # 单源
    uv run python scripts/etl/run_full_pipeline.py --sources bili

    # 跳过爬虫，只跑 ETL 后半段
    uv run python scripts/etl/run_full_pipeline.py --skip-crawl

    # 只跑某阶段
    uv run python scripts/etl/run_full_pipeline.py --stage embed

支持数据源（独立 CLI 子命令）：
    fandom / bili / mihoyo / nga / netease_ds
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


# 各源 → 爬虫 driver 脚本 + 默认 game
SPIDER_DRIVERS = {
    "fandom": {
        "script": "crawl_fandom.py",
        "args": ["--max-pages", "100"],
        "env": {},  # Fandom 需要 CRAWLER_PROXY
    },
    "bili": {
        "script": "crawl_bili_column.py",
        "args": ["--game", "onmyoji", "--max-pages", "5", "--max-articles", "100"],
        "env": {},  # 可选 BILI_SESSDATA
    },
    "mihoyo": {
        "script": "crawl_mihoyo.py",
        "args": ["--game", "genshin", "--max-pages", "5", "--max-articles", "100"],
        "env": {},
    },
    "nga": {
        "script": "crawl_nga.py",
        "args": ["--game", "onmyoji", "--mode", "essence", "--max-pages", "5", "--max-articles", "100"],
        "env": {},
    },
    "netease_ds": {
        "script": "crawl_netease_ds.py",
        "args": ["--game", "onmyoji", "--max-pages", "5", "--max-articles", "100"],
        "env": {},
    },
}


def run_crawl_source(source: str) -> None:
    """跑单个源的爬虫（subprocess）。"""
    cfg = SPIDER_DRIVERS.get(source)
    if cfg is None:
        raise ValueError(f"Unknown source: {source}. Available: {list(SPIDER_DRIVERS.keys())}")

    script_path = SCRIPTS_DIR / cfg["script"]
    if not script_path.exists():
        raise FileNotFoundError(f"Driver script not found: {script_path}")

    cmd = [sys.executable, str(script_path)] + cfg["args"]
    env = os.environ.copy()
    env.update(cfg["env"])

    logger.info(f"=== EXTRACT: {source} ({cfg['script']}) ===")
    logger.info(f"CMD: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        logger.warning(f"{source} crawler exited {result.returncode}")
        if result.stderr:
            logger.debug(f"stderr (last 500 chars):\n{result.stderr[-500:]}")
    else:
        logger.info(f"{source} crawler OK ({len(result.stdout.splitlines())} log lines)")


def run_crawl(sources: list[str]) -> None:
    """跑多个源的爬虫。"""
    for src in sources:
        try:
            run_crawl_source(src)
        except Exception as exc:
            logger.warning(f"Source {src} failed: {exc}")


def run_transform_to_md() -> None:
    """JSONL → 单文件 .md（人工读 + 备份）。"""
    logger.info("=== TRANSFORM STEP 1: JSONL → Markdown ===")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.etl.to_markdown import transform_all

    stats = transform_all()
    logger.info(f"Markdown 转换: {stats} (total {sum(stats.values())} files)")


def run_transform_to_parquet() -> None:
    """JSONL → chunks.parquet + meta.parquet（供 embed 用）。"""
    logger.info("=== TRANSFORM STEP 2: JSONL → Parquet ===")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.etl.transform import run

    run()


def run_embed() -> None:
    """bge-m3 GPU 批量 embedding。"""
    logger.info("=== EMBED: bge-m3 GPU 批量 embedding ===")
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
    logger.info("=== LOAD: Chroma 向量库 ===")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.etl.load_chroma import load_to_chroma

    load_to_chroma()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 7.3 多源 ETL Pipeline")
    parser.add_argument(
        "--stage",
        choices=["all", "crawl", "transform", "embed", "load"],
        default="all",
        help="执行阶段",
    )
    parser.add_argument(
        "--sources",
        default="fandom",
        help="逗号分隔数据源（fandom/bili/mihoyo/nga/netease_ds）。例: --sources bili,mihoyo,nga",
    )
    parser.add_argument("--skip-crawl", action="store_true", help="跳过爬虫阶段")
    parser.add_argument("--skip-md", action="store_true", help="跳过 JSONL → Markdown 转换")
    parser.add_argument("--skip-chroma", action="store_true", help="跳过 Chroma 写入")
    parser.add_argument("--skip-qdrant", action="store_true", help="跳过 Qdrant 写入")
    parser.add_argument("--skip-duckdb", action="store_true", help="跳过 DuckDB 数仓写入")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    t0 = time.time()
    stages = []

    # 阶段 1: EXTRACT
    if args.stage in ("all", "crawl") and not args.skip_crawl:
        run_crawl(sources)
        stages.append("crawl")

    # 阶段 2: TRANSFORM（两步）
    if args.stage in ("all", "transform"):
        if not args.skip_md:
            run_transform_to_md()
            stages.append("transform_md")
        run_transform_to_parquet()
        stages.append("transform_parquet")

    # 阶段 3: EMBED
    if args.stage in ("all", "embed"):
        run_embed()
        stages.append("embed")

    # 阶段 4: LOAD
    if args.stage in ("all", "load"):
        if not args.skip_duckdb:
            run_load_duckdb()
            stages.append("load_duckdb")
        if not args.skip_chroma:
            try:
                run_load_chroma()
                stages.append("load_chroma")
            except Exception as exc:
                logger.warning(f"Chroma 加载失败: {exc}")

    elapsed = time.time() - t0
    logger.info(f"=== Pipeline 完成: {stages}, 耗时 {elapsed:.1f}s ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
