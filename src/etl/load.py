"""ETL Load 层 - DuckDB 数仓 + Chroma / Qdrant 向量库。

三个 Load 目标：
    1. DuckDB  数仓（ODS/DWD/DWS/ADS 分层）
    2. Chroma  主向量库（沿用 Phase 1）
    3. Qdrant  sidecar 向量库（演示对比）
"""
from src.etl.load_duckdb import (
    build_duckdb_warehouse,
    load_chunks_to_dwd,
    load_documents_to_dwd,
    load_embeddings_to_dwd,
    build_dws_summary,
    query_corpus_stats,
)
from src.etl.load_chroma import load_to_chroma
from src.etl.load_qdrant import load_to_qdrant

__all__ = [
    "build_duckdb_warehouse",
    "load_documents_to_dwd",
    "load_chunks_to_dwd",
    "load_embeddings_to_dwd",
    "build_dws_summary",
    "query_corpus_stats",
    "load_to_chroma",
    "load_to_qdrant",
]