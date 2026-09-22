"""金融 DuckDB 数仓 — 把 chunks.parquet 写入 DuckDB 列存数仓。

表结构（dwd schema）:
- dwd.documents: 文档元数据
- dwd.chunks: chunk 文本
- dwd.embeddings: chunk embedding 向量

理财域字段: institution / report_type / effective_date / product_name / product_code
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
from loguru import logger

from src.config import settings


DATA_ROOT = Path(settings.data_dir)
CLEAN_DIR = DATA_ROOT / "clean"
WAREHOUSE_DIR = Path(settings.warehouse_dir)
WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
DUCKDB_PATH = Path(settings.duckdb_path)


def init_warehouse(db_path: Path = DUCKDB_PATH) -> duckdb.DuckDBPyConnection:
    """初始化数仓 schema（幂等）。"""
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS dwd")
    # documents: 文档级元数据（去重 doc_id）
    con.execute("""
        CREATE TABLE IF NOT EXISTS dwd.documents (
            doc_id           VARCHAR PRIMARY KEY,
            institution      VARCHAR,
            report_type      VARCHAR,
            effective_date   VARCHAR,
            product_name     VARCHAR,
            product_code     VARCHAR,
            category         VARCHAR,
            title            VARCHAR,
            filename         VARCHAR,
            file_path        VARCHAR,
            page_count       INTEGER,
            source           VARCHAR,
            loaded_at        TIMESTAMP DEFAULT current_timestamp
        )
    """)
    # chunks: chunk 级数据
    con.execute("""
        CREATE TABLE IF NOT EXISTS dwd.chunks (
            chunk_id         VARCHAR PRIMARY KEY,
            doc_id           VARCHAR,
            chunk_index      INTEGER,
            chunk_text       VARCHAR,
            institution      VARCHAR,
            report_type      VARCHAR,
            effective_date   VARCHAR,
            product_name     VARCHAR,
            product_code     VARCHAR,
            category         VARCHAR,
            title            VARCHAR,
            filename         VARCHAR,
            file_path        VARCHAR,
            page_num         INTEGER,
            page_count       INTEGER,
            source           VARCHAR,
            chunk_type       VARCHAR,
            loaded_at        TIMESTAMP DEFAULT current_timestamp
        )
    """)
    # embeddings: 向量数据
    con.execute("""
        CREATE TABLE IF NOT EXISTS dwd.embeddings (
            chunk_id         VARCHAR PRIMARY KEY,
            embedding        DOUBLE[],
            model            VARCHAR,
            created_at       TIMESTAMP DEFAULT current_timestamp
        )
    """)
    logger.info(f"DuckDB schema 初始化: {db_path}")
    return con


def load_chunks_to_duckdb(
    chunks_parquet: Path = CLEAN_DIR / "chunks.parquet",
    db_path: Path = DUCKDB_PATH,
) -> int:
    """加载 chunks 到 dwd.chunks / dwd.documents (幂等：DELETE+INSERT)。

    Returns:
        写入的 chunks 数量
    """
    if not chunks_parquet.exists():
        logger.warning(f"{chunks_parquet} 不存在，跳过")
        return 0

    df = pd.read_parquet(chunks_parquet)
    logger.info(f"加载 {len(df)} chunks from {chunks_parquet}")

    con = init_warehouse(db_path)

    # documents: 按 doc_id 去重
    docs_df = df[[
        "doc_id", "institution", "report_type", "effective_date",
        "product_name", "product_code", "category", "title",
        "filename", "file_path", "page_count", "source",
    ]].drop_duplicates(subset=["doc_id"])

    # 幂等：先 delete by source，再 insert
    con.execute("DELETE FROM dwd.documents WHERE source = ?", ["pdf_local"])
    con.execute(
        """
        INSERT INTO dwd.documents
        (doc_id, institution, report_type, effective_date, product_name,
         product_code, category, title, filename, file_path,
         page_count, source)
        SELECT
            doc_id, institution, report_type, effective_date, product_name,
            product_code, category, title, filename, file_path,
            page_count, source
        FROM docs_df
        """
    )

    # chunks: 全量替换
    con.execute("DELETE FROM dwd.chunks WHERE source = ?", ["pdf_local"])
    con.execute(
        """
        INSERT INTO dwd.chunks
        SELECT
            chunk_id, doc_id, chunk_index, chunk_text,
            institution, report_type, effective_date, product_name,
            product_code, category, title, filename, file_path,
            page_num, page_count, source, chunk_type,
            current_timestamp
        FROM df
        """
    )

    n_chunks = len(df)
    n_docs = len(docs_df)
    logger.info(f"dwd.documents: {n_docs} 行, dwd.chunks: {n_chunks} 行")

    # 概览
    overview = con.execute("""
        SELECT
            (SELECT COUNT(*) FROM dwd.documents) AS docs,
            (SELECT COUNT(*) FROM dwd.chunks) AS chunks,
            (SELECT COUNT(*) FROM dwd.embeddings) AS embeddings,
            (SELECT COUNT(DISTINCT institution) FROM dwd.chunks) AS institutions,
            (SELECT COUNT(DISTINCT report_type) FROM dwd.chunks) AS report_types
    """).fetchone()
    logger.info(f"语料库概览: {dict(zip(['docs','chunks','embeddings','institutions','report_types'], overview))}")

    con.close()
    return n_chunks


def load_embeddings_to_duckdb(
    embeddings_parquet: Path = CLEAN_DIR / "embeddings.parquet",
    db_path: Path = DUCKDB_PATH,
) -> int:
    """加载 embeddings 到 dwd.embeddings (幂等)。"""
    if not embeddings_parquet.exists():
        logger.warning(f"{embeddings_parquet} 不存在，跳过")
        return 0

    df = pd.read_parquet(embeddings_parquet)
    logger.info(f"加载 {len(df)} embeddings from {embeddings_parquet}")

    con = init_warehouse(db_path)
    # 幂等
    con.execute(f"DELETE FROM dwd.embeddings WHERE model = '{settings.ollama_embed_model}'")
    con.execute(
        """
        INSERT INTO dwd.embeddings (chunk_id, embedding, model)
        SELECT chunk_id, embedding, model FROM df
        """
    )
    logger.info(f"dwd.embeddings: {len(df)} 行")
    con.close()
    return len(df)


def run() -> int:
    """CLI 入口：加载 chunks + embeddings 到 DuckDB"""
    n_chunks = load_chunks_to_duckdb()
    n_embs = load_embeddings_to_duckdb()
    return n_chunks + n_embs


if __name__ == "__main__":
    run()