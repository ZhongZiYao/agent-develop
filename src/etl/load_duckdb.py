"""DuckDB 数仓 Load - ODS/DWD/DWS 分层建模。

输入：
    data/clean/chunks.parquet   chunks 切分结果
    data/clean/meta.parquet     文档元数据
    data/clean/embeddings.parquet  bge-m3 向量

输出：
    data/warehouse/gameguide.duckdb
        ods.raw_documents       原始文档（落盘）
        dwd.documents           清洗后文档
        dwd.chunks              切分后 chunks
        dwd.entities            NER 实体（可选，Phase 7.3+）
        dws.game_stats          按游戏统计
        dws.source_stats        按来源统计
        ads.rag_corpus          RAG 检索入口视图

DuckDB 优势：
- pip install 即用，单文件 30MB
- 列存 + 向量化执行
- 直接读 Parquet，无需导入
- 适合 100w-10亿行分析
"""
from __future__ import annotations

from pathlib import Path

import duckdb
from loguru import logger

from src.config import settings


# ===== 路径配置 =====
DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
CLEAN_DIR = DATA_ROOT / "clean"
WAREHOUSE_DIR = DATA_ROOT / "warehouse"
DUCKDB_PATH = WAREHOUSE_DIR / "gameguide.duckdb"


# ===== 建表 SQL =====

_DDL_DWD = """
CREATE SCHEMA IF NOT EXISTS dwd;
CREATE SCHEMA IF NOT EXISTS dws;
CREATE SCHEMA IF NOT EXISTS ads;

CREATE TABLE IF NOT EXISTS dwd.documents (
    doc_id          VARCHAR(64) PRIMARY KEY,
    source          VARCHAR(32) NOT NULL,
    game            VARCHAR(32) NOT NULL,
    title           TEXT,
    url             TEXT,
    author          TEXT,
    publish_date    VARCHAR(32),
    word_count      INT,
    quality_score   FLOAT,
    language        VARCHAR(8) DEFAULT 'zh',
    crawl_ts        VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS dwd.chunks (
    chunk_id        VARCHAR(64) PRIMARY KEY,
    doc_id          VARCHAR(64) NOT NULL,
    chunk_index     INT,
    chunk_text      TEXT,
    chunk_tokens    INT,
    section_title   TEXT,
    source          VARCHAR(32),
    game            VARCHAR(32),
    title           TEXT,
    url             TEXT,
    quality_score   FLOAT
);

CREATE TABLE IF NOT EXISTS dwd.embeddings (
    chunk_id        VARCHAR(64) PRIMARY KEY,
    embedding       FLOAT[1024],
    model           VARCHAR(64)
);
"""

_DDL_DWS = """
CREATE TABLE IF NOT EXISTS dws.game_stats AS
SELECT
    game,
    source,
    COUNT(DISTINCT doc_id)   AS doc_count,
    COUNT(*)                 AS chunk_count,
    AVG(quality_score)       AS avg_quality,
    SUM(word_count)          AS total_words,
    MAX(crawl_ts)            AS last_crawl
FROM dwd.documents
GROUP BY game, source;

CREATE TABLE IF NOT EXISTS dws.source_stats AS
SELECT
    source,
    COUNT(DISTINCT doc_id)   AS doc_count,
    COUNT(*)                 AS chunk_count,
    AVG(word_count)          AS avg_word_count,
    SUM(word_count)          AS total_words
FROM dwd.documents
GROUP BY source;
"""

_DDL_ADS = """
CREATE OR REPLACE VIEW ads.rag_corpus AS
SELECT
    c.chunk_id,
    c.doc_id,
    d.game,
    d.source,
    d.title,
    d.url,
    c.section_title,
    c.chunk_text,
    e.embedding
FROM dwd.chunks c
JOIN dwd.documents d ON c.doc_id = d.doc_id
LEFT JOIN dwd.embeddings e ON c.chunk_id = e.chunk_id
WHERE d.quality_score >= 0.3;
"""


def get_connection(db_path: Path = DUCKDB_PATH) -> duckdb.DuckDBPyConnection:
    """获取 DuckDB 连接（自动创建父目录）。"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def build_duckdb_warehouse(con: duckdb.DuckDBPyConnection | None = None) -> None:
    """建表（DWD / DWS / ADS）。"""
    if con is None:
        con = get_connection()
    con.execute(_DDL_DWD)
    con.execute(_DDL_DWS)
    con.execute(_DDL_ADS)
    logger.info("DuckDB schema 创建完成")


def load_documents_to_dwd(
    con: duckdb.DuckDBPyConnection | None = None,
    parquet_path: Path = CLEAN_DIR / "meta.parquet",
) -> int:
    """把 meta.parquet 写入 dwd.documents。"""
    if con is None:
        con = get_connection()
    if not parquet_path.exists():
        logger.warning(f"{parquet_path} 不存在，跳过 documents 加载")
        return 0
    # DELETE then INSERT 以支持增量（按 doc_id 去重）
    con.execute(
        "DELETE FROM dwd.documents WHERE doc_id IN (SELECT doc_id FROM read_parquet(?))",
        [str(parquet_path)],
    )
    con.execute(
        "INSERT INTO dwd.documents SELECT * FROM read_parquet(?)",
        [str(parquet_path)],
    )
    n = con.execute("SELECT COUNT(*) FROM dwd.documents").fetchone()[0]
    logger.info(f"dwd.documents: {n} rows")
    return n


def load_chunks_to_dwd(
    con: duckdb.DuckDBPyConnection | None = None,
    parquet_path: Path = CLEAN_DIR / "chunks.parquet",
) -> int:
    """把 chunks.parquet 写入 dwd.chunks。"""
    if con is None:
        con = get_connection()
    if not parquet_path.exists():
        logger.warning(f"{parquet_path} 不存在，跳过 chunks 加载")
        return 0
    # 增量：先删同 doc_id 旧 chunks，再 INSERT
    con.execute(
        "DELETE FROM dwd.chunks WHERE doc_id IN (SELECT doc_id FROM read_parquet(?))",
        [str(parquet_path)],
    )
    con.execute(
        "INSERT INTO dwd.chunks SELECT * FROM read_parquet(?)",
        [str(parquet_path)],
    )
    n = con.execute("SELECT COUNT(*) FROM dwd.chunks").fetchone()[0]
    logger.info(f"dwd.chunks: {n} rows")
    return n


def load_embeddings_to_dwd(
    con: duckdb.DuckDBPyConnection | None = None,
    parquet_path: Path = CLEAN_DIR / "embeddings.parquet",
) -> int:
    """把 embeddings.parquet 写入 dwd.embeddings。

    DuckDB 直接支持 FLOAT[N] 数组类型。
    """
    if con is None:
        con = get_connection()
    if not parquet_path.exists():
        logger.warning(f"{parquet_path} 不存在，跳过 embeddings 加载")
        return 0
    # DuckDB 会自动把 list[float] 解析为 FLOAT[1024]
    # 增量：先删同 chunk_id 旧 embeddings，再 INSERT
    con.execute(
        "DELETE FROM dwd.embeddings WHERE chunk_id IN (SELECT chunk_id FROM read_parquet(?))",
        [str(parquet_path)],
    )
    con.execute(
        "INSERT INTO dwd.embeddings SELECT chunk_id, embedding::FLOAT[1024], model "
        "FROM read_parquet(?)",
        [str(parquet_path)],
    )
    n = con.execute("SELECT COUNT(*) FROM dwd.embeddings").fetchone()[0]
    logger.info(f"dwd.embeddings: {n} rows")
    return n


def build_dws_summary(con: duckdb.DuckDBPyConnection | None = None) -> None:
    """重建 DWS 汇总表。"""
    if con is None:
        con = get_connection()
    con.execute("DROP TABLE IF EXISTS dws.game_stats")
    con.execute("DROP TABLE IF EXISTS dws.source_stats")
    con.execute(_DDL_DWS)
    logger.info("DWS 汇总表已重建")


def query_corpus_stats(con: duckdb.DuckDBPyConnection | None = None) -> dict:
    """查询语料库概览（演示用）。"""
    if con is None:
        con = get_connection()
    stats = {
        "documents": con.execute("SELECT COUNT(*) FROM dwd.documents").fetchone()[0],
        "chunks": con.execute("SELECT COUNT(*) FROM dwd.chunks").fetchone()[0],
        "embeddings": con.execute("SELECT COUNT(*) FROM dwd.embeddings").fetchone()[0],
        "by_game": con.execute(
            "SELECT game, COUNT(*) AS n FROM dwd.documents GROUP BY game ORDER BY n DESC"
        ).fetchdf().to_dict("records"),
        "by_source": con.execute(
            "SELECT source, COUNT(*) AS n FROM dwd.documents GROUP BY source ORDER BY n DESC"
        ).fetchdf().to_dict("records"),
    }
    return stats


def run() -> None:
    """CLI 入口：全流程跑一遍。"""
    con = get_connection()
    build_duckdb_warehouse(con)
    load_documents_to_dwd(con)
    load_chunks_to_dwd(con)
    load_embeddings_to_dwd(con)
    build_dws_summary(con)
    stats = query_corpus_stats(con)
    logger.info(f"语料库概览: {stats}")


if __name__ == "__main__":
    run()