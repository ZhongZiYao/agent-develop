"""全量理财 PDF ETL — 把 23,229 份 PDF 跑 transform → embed → DuckDB → Chroma。

特点：
- 分批处理（默认每批 1000 个 PDF），避免内存溢出
- 增量更新：扫描已处理的 doc_id 跳过（基于 DuckDB）
- 失败隔离：单文件失败不影响整批
- 资源监控：每 100 文件报告一次吞吐
- **Embedding 并发**：默认 16 个并发请求（替代串行）

用法：
    python -m scripts.etl_financial_full                 # 全量
    python -m scripts.etl_financial_full --batch 2000    # 自定义批大小
    python -m scripts.etl_financial_full --limit 5000    # 只跑前 N 个
    python -m scripts.etl_financial_full --workers 32    # 自定义 embedding 并发
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
from loguru import logger

from src.config import settings
from src.etl.embed_ollama import embed_chunks, save_embeddings
from src.etl.load_chroma import load_to_chroma
from src.etl.load_duckdb_financial import load_chunks_to_duckdb, load_embeddings_to_duckdb
from src.etl.transform_pdf import transform_pdfs_to_chunks


CLEAN_DIR = Path(settings.data_dir) / "clean"


def discover_all_pdfs() -> list[Path]:
    """扫描 data/理财文件 下所有 PDF。"""
    pdf_root = Path(settings.pdf_data_dir)
    pdfs = sorted(pdf_root.rglob("*.pdf"))
    return pdfs


def get_processed_doc_ids() -> set[str]:
    """从 DuckDB 读取已处理的 doc_id 列表（用于增量）。"""
    try:
        import duckdb
        con = duckdb.connect(settings.duckdb_path, read_only=True)
        rows = con.execute("SELECT doc_id FROM dwd.documents WHERE source='pdf_local'").fetchall()
        con.close()
        return {r[0] for r in rows}
    except Exception:
        return set()


def doc_id_from_path(pdf_path: Path) -> str:
    """用文件路径 sha1 前 12 位作为 doc_id（与 pdf_loader 一致：使用 resolve()）。"""
    import hashlib
    return hashlib.sha1(str(pdf_path.resolve()).encode("utf-8")).hexdigest()[:12]


def run_full_pipeline(
    batch_size: int = 1000,
    limit: int | None = None,
    incremental: bool = True,
    skip_embed: bool = False,
    skip_chroma: bool = False,
    workers: int = 16,
):
    """跑全量 ETL。"""
    started = time.time()

    # 1. 发现 PDF
    logger.info("=" * 60)
    logger.info("Step 0/4: 发现 PDF 文件")
    logger.info("=" * 60)
    all_pdfs = discover_all_pdfs()
    logger.info(f"发现 {len(all_pdfs)} 个 PDF")
    if limit:
        all_pdfs = all_pdfs[:limit]
        logger.info(f"限制为前 {limit} 个")

    if not all_pdfs:
        logger.warning("没有找到 PDF，退出")
        return

    # 2. 增量：过滤已处理
    if incremental:
        processed = get_processed_doc_ids()
        before = len(all_pdfs)
        all_pdfs = [p for p in all_pdfs if doc_id_from_path(p) not in processed]
        logger.info(f"增量过滤: {before} → {len(all_pdfs)}（已处理 {before - len(all_pdfs)}）")

    if not all_pdfs:
        logger.info("所有 PDF 已处理，无需重跑")
        return

    # 3. 分批 transform
    logger.info("=" * 60)
    logger.info(f"Step 1/4: Transform PDF → chunks (batch_size={batch_size})")
    logger.info("=" * 60)
    all_chunks = []
    total_failed = 0

    for batch_idx in range(0, len(all_pdfs), batch_size):
        batch = all_pdfs[batch_idx : batch_idx + batch_size]
        batch_no = batch_idx // batch_size + 1
        total_batches = (len(all_pdfs) + batch_size - 1) // batch_size
        t0 = time.time()

        try:
            tmp_parquet = CLEAN_DIR / f"_chunks_batch_{batch_no:04d}.parquet"
            transform_pdfs_to_chunks(
                pdf_dir=batch,
                output_parquet=tmp_parquet,
            )
            if tmp_parquet.exists():
                df = pd.read_parquet(tmp_parquet)
                all_chunks.append(df)
                tmp_parquet.unlink()
                elapsed = time.time() - t0
                logger.info(
                    f"Batch {batch_no}/{total_batches}: "
                    f"{len(batch)} PDFs → {len(df)} chunks ({elapsed:.1f}s, "
                    f"{len(batch)/elapsed:.1f} PDFs/s)"
                )
        except Exception as e:
            total_failed += len(batch)
            logger.error(f"Batch {batch_no} 失败: {e}")

    if not all_chunks:
        logger.error("没有产出任何 chunks，退出")
        return

    chunks_df = pd.concat(all_chunks, ignore_index=True)
    logger.info(f"Transform 汇总: {len(chunks_df)} chunks from {len(all_pdfs) - total_failed} docs")

    chunks_parquet = CLEAN_DIR / "chunks.parquet"
    chunks_parquet.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = chunks_parquet.with_suffix(".parquet.tmp")
    if tmp_path.exists():
        tmp_path.unlink()
    chunks_df.to_parquet(tmp_path, engine="pyarrow", index=False)
    if chunks_parquet.exists():
        chunks_parquet.unlink()
    tmp_path.rename(chunks_parquet)
    logger.info(f"写入 {chunks_parquet} ({len(chunks_df)} rows, {chunks_parquet.stat().st_size/1e6:.1f} MB)")

    # 4. Embed
    if skip_embed:
        logger.info("Step 2/4: 跳过 embedding（使用现有 embeddings.parquet）")
        embeddings_parquet = CLEAN_DIR / "embeddings.parquet"
        if not embeddings_parquet.exists():
            logger.error("没有现有 embeddings.parquet，无法 skip")
            return
    else:
        logger.info("=" * 60)
        logger.info(f"Step 2/4: Embedding (Ollama bge-m3) — {len(chunks_df)} chunks, workers={workers}")
        logger.info("=" * 60)
        t0 = time.time()
        embeddings_df = embed_chunks(chunks_df, max_workers=workers)
        embeddings_parquet = save_embeddings(embeddings_df, out_path=CLEAN_DIR / "embeddings.parquet")
        elapsed = time.time() - t0
        logger.info(f"Embedding 耗时: {elapsed:.1f}s ({len(chunks_df)/elapsed:.1f} chunks/s)")

    # 5. DuckDB
    logger.info("=" * 60)
    logger.info("Step 3/4: DuckDB 数仓加载")
    logger.info("=" * 60)
    load_chunks_to_duckdb(chunks_parquet)
    load_embeddings_to_duckdb(embeddings_parquet)

    # 6. Chroma
    if skip_chroma:
        logger.info("Step 4/4: 跳过 Chroma 同步")
    else:
        logger.info("=" * 60)
        logger.info("Step 4/4: Chroma 向量库同步")
        logger.info("=" * 60)
        load_to_chroma(
            chunks_parquet=chunks_parquet,
            embeddings_parquet=embeddings_parquet,
        )

    total_elapsed = time.time() - started
    logger.info("=" * 60)
    logger.info(f"✅ 全量 ETL 完成 — 耗时 {total_elapsed/60:.1f} min")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="全量理财 PDF ETL")
    parser.add_argument("--batch", type=int, default=1000, help="每批 PDF 数（默认 1000）")
    parser.add_argument("--limit", type=int, default=None, help="只跑前 N 个")
    parser.add_argument("--no-incremental", action="store_true", help="关闭增量（重新跑所有）")
    parser.add_argument("--skip-embed", action="store_true", help="跳过 embedding")
    parser.add_argument("--skip-chroma", action="store_true", help="跳过 Chroma 同步")
    parser.add_argument("--workers", type=int, default=16, help="embedding 并发线程数（默认 16）")
    args = parser.parse_args()

    run_full_pipeline(
        batch_size=args.batch,
        limit=args.limit,
        incremental=not args.no_incremental,
        skip_embed=args.skip_embed,
        skip_chroma=args.skip_chroma,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
