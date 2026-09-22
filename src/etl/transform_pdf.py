"""PDF Transform — 把加载的 PDF Document 切成 Chunk 并落 parquet。

输入：data/理财文件/*.pdf (经 pdf_loader 加载)
输出：data/clean/chunks.parquet (chunk_id / doc_id / chunk_text / metadata)

列结构：
- chunk_id (str): 全局唯一 (doc_id#0000)
- doc_id (str): 文档 ID
- chunk_index (int): 文档内序号
- chunk_text (str): chunk 文本
- institution (str): 机构
- report_type (str): 报告类型
- effective_date (str): 生效日期
- product_name (str): 产品名
- product_code (str): 产品编号
- title (str): 标题
- filename (str): 文件名
- page_num (int): 页码
- category (str): 一级分类
- page_count (int): 总页数
- file_path (str): 文件路径
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from src.config import settings
from src.loaders.pdf_loader import load_pdf_dir, load_pdf_files
from src.splitters.pdf_table_splitter import split_pdf_documents


CLEAN_DIR = Path(settings.data_dir) / "clean"


def transform_pdfs_to_chunks(
    pdf_dir: Path | str | list[Path | str] | None = None,
    output_parquet: Path | str | None = None,
    limit: int | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> Path:
    """完整 transform: PDF → Documents → Chunks → parquet。

    Args:
        pdf_dir: PDF 目录 OR 显式 PDF 路径列表 (POC 用)
        output_parquet: 输出 parquet 路径 (默认 data/clean/chunks.parquet)
        limit: 限制加载文件数（POC 用）
        chunk_size / chunk_overlap: 覆盖 settings

    Returns:
        输出 parquet 路径
    """
    output_parquet = Path(output_parquet) if output_parquet else CLEAN_DIR / "chunks.parquet"

    logger.info(f"=== Transform 开始 ===")
    logger.info(f"PDF 源: {pdf_dir}")
    logger.info(f"限制文件数: {limit or '全部'}")

    # 1. 加载 PDF（支持目录或显式路径列表）
    if isinstance(pdf_dir, list):
        docs = load_pdf_files(
            pdf_dir,
            min_text_chars=settings.pdf_min_text_chars,
            max_pages=settings.pdf_max_pages,
        )
    else:
        pdf_dir = Path(pdf_dir)
        docs = load_pdf_dir(
            pdf_dir,
            limit=limit,
            min_text_chars=settings.pdf_min_text_chars,
            max_pages=settings.pdf_max_pages,
        )
    if not docs:
        logger.warning("未加载到任何 PDF")
        return output_parquet

    # 2. 切分
    chunk_size = chunk_size or settings.pdf_chunk_size
    chunk_overlap = chunk_overlap or settings.pdf_chunk_overlap
    chunks = split_pdf_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    logger.info(f"切分完成: {len(docs)} 文档 → {len(chunks)} chunks")

    # 3. 转 DataFrame
    rows = []
    for c in chunks:
        meta = c.metadata
        rows.append({
            "chunk_id": c.chunk_id,
            "doc_id": c.doc_id,
            "chunk_index": c.chunk_index,
            "chunk_text": c.content,
            # 业务字段（金融域）
            "institution": meta.get("institution", ""),
            "report_type": meta.get("report_type", ""),
            "effective_date": meta.get("effective_date", ""),
            "product_name": meta.get("product_name", ""),
            "product_code": meta.get("product_code", ""),
            # 来源
            "title": meta.get("title", ""),
            "filename": meta.get("filename", ""),
            "file_path": meta.get("file_path", ""),
            "category": meta.get("category", ""),
            "page_num": meta.get("page_num", 0),
            "page_count": meta.get("page_count", 0),
            # ETL 标记
            "source": meta.get("source", "pdf_local"),
            "chunk_type": meta.get("chunk_type", "pdf_segment"),
        })

    df = pd.DataFrame(rows)

    # 4. 落 parquet
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_parquet.with_suffix(".parquet.tmp")
    # 清理旧 tmp 文件（如果上次中断）
    if tmp_path.exists():
        tmp_path.unlink()
    df.to_parquet(tmp_path, engine="pyarrow", index=False)
    tmp_path.rename(output_parquet)

    size_mb = output_parquet.stat().st_size / 1e6
    logger.info(f"=== Transform 完成 ===")
    logger.info(f"输出: {output_parquet} ({size_mb:.2f} MB, {len(df)} rows)")
    logger.info(f"机构分布: {df['institution'].value_counts().head(5).to_dict()}")
    logger.info(f"报告类型分布: {df['report_type'].value_counts().to_dict()}")
    return output_parquet


def run() -> Path:
    """CLI 入口：扫描全量理财文件目录"""
    pdf_dir = Path(settings.pdf_data_dir)
    return transform_pdfs_to_chunks(pdf_dir=pdf_dir)


if __name__ == "__main__":
    run()