"""理财 PDF POC ETL 编排脚本

Pipeline:
1. transform_pdfs_to_chunks (PDF → parquet)
2. embed_chunks (Ollama bge-m3)
3. load_chunks_to_duckdb
4. load_embeddings_to_duckdb
5. load_to_chroma (向量库同步)

用法:
    python -m scripts.etl_financial_poc
"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

from src.config import settings
from src.etl.embed_ollama import embed_chunks, save_embeddings
from src.etl.load_chroma import load_to_chroma
from src.etl.load_duckdb_financial import load_chunks_to_duckdb, load_embeddings_to_duckdb
from src.etl.transform_pdf import transform_pdfs_to_chunks


CLEAN_DIR = Path(settings.data_dir) / "clean"
POC_JSON = CLEAN_DIR / "poc_files.json"


def run_poc_pipeline():
    """跑完整 POC ETL pipeline。"""
    if not POC_JSON.exists():
        logger.error(f"POC 列表不存在: {POC_JSON}（先跑 python -m scripts.scan_pdfs）")
        return

    poc_list = json.loads(POC_JSON.read_text(encoding="utf-8"))
    pdf_paths = [Path(settings.pdf_data_dir) / item["path"] for item in poc_list]
    logger.info(f"POC 文件: {len(pdf_paths)} 个 PDF")

    # Step 1: Transform
    logger.info("=" * 60)
    logger.info("Step 1/4: Transform PDF → chunks.parquet")
    logger.info("=" * 60)
    chunks_parquet = transform_pdfs_to_chunks(
        pdf_dir=pdf_paths,  # 传路径列表而非目录
        output_parquet=CLEAN_DIR / "chunks.parquet",
    )

    # Step 2: Embed
    logger.info("=" * 60)
    logger.info("Step 2/4: Embedding (Ollama bge-m3)")
    logger.info("=" * 60)
    import pandas as pd
    chunks_df = pd.read_parquet(chunks_parquet)
    embeddings_df = embed_chunks(chunks_df)
    embeddings_parquet = save_embeddings(embeddings_df, out_path=CLEAN_DIR / "embeddings.parquet")

    # Step 3: DuckDB
    logger.info("=" * 60)
    logger.info("Step 3/4: DuckDB 数仓加载")
    logger.info("=" * 60)
    load_chunks_to_duckdb(chunks_parquet)
    load_embeddings_to_duckdb(embeddings_parquet)

    # Step 4: Chroma
    logger.info("=" * 60)
    logger.info("Step 4/4: Chroma 向量库同步")
    logger.info("=" * 60)
    load_to_chroma(
        chunks_parquet=chunks_parquet,
        embeddings_parquet=embeddings_parquet,
    )

    logger.info("=" * 60)
    logger.info("✅ POC ETL 全链路完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_poc_pipeline()