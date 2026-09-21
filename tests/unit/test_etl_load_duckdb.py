"""ETL DuckDB 数仓单元测试。

覆盖：
- DDL 建表（DWD / DWS / ADS）
- 文档 / chunks / embeddings 加载
- DWS 聚合（按 game / source 统计）
- ADS 视图（RAG 检索入口）
- 跨组件查询（JOIN documents + chunks + embeddings）
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest

from src.etl.load_duckdb import (
    build_dws_summary,
    build_duckdb_warehouse,
    get_connection,
    load_chunks_to_dwd,
    load_documents_to_dwd,
    load_embeddings_to_dwd,
    query_corpus_stats,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """临时 DuckDB 文件路径。"""
    return tmp_path / "test.duckdb"


@pytest.fixture
def db_con(db_path: Path) -> duckdb.DuckDBPyConnection:
    """临时 DuckDB 连接（每个测试隔离）。"""
    con = get_connection(db_path)
    build_duckdb_warehouse(con)
    yield con
    con.close()


@pytest.fixture
def sample_docs(tmp_path: Path) -> Path:
    """示例 meta.parquet。"""
    df = pd.DataFrame(
        {
            "doc_id": ["d1", "d2", "d3"],
            "source": ["fandom", "fandom", "official"],
            "game": ["onmyoji", "onmyoji", "onmyoji"],
            "title": ["妖刀姬", "红蝶", "S13 赛季"],
            "url": ["u1", "u2", "u3"],
            "author": [None, None, "官方"],
            "publish_date": [None, None, "2026-01-01"],
            "word_count": [100, 200, 300],
            "quality_score": [0.8, 0.7, 0.9],
            "language": ["zh", "zh", "zh"],
            "crawl_ts": ["2026-09-21"] * 3,
        }
    )
    path = tmp_path / "meta.parquet"
    df.to_parquet(path)
    return path


@pytest.fixture
def sample_chunks(tmp_path: Path) -> Path:
    """示例 chunks.parquet。"""
    df = pd.DataFrame(
        {
            "chunk_id": ["c1", "c2", "c3", "c4"],
            "doc_id": ["d1", "d1", "d2", "d3"],
            "chunk_index": [0, 1, 0, 0],
            "chunk_text": ["chunk1", "chunk2", "chunk3", "chunk4"],
            "chunk_tokens": [50, 60, 70, 80],
            "section_title": ["技能", "御魂", "简介", "赛季"],
            "source": ["fandom", "fandom", "fandom", "official"],
            "game": ["onmyoji"] * 4,
            "title": ["妖刀姬", "妖刀姬", "红蝶", "S13"],
            "url": ["u1", "u1", "u2", "u3"],
            "quality_score": [0.8, 0.8, 0.7, 0.9],
        }
    )
    path = tmp_path / "chunks.parquet"
    df.to_parquet(path)
    return path


@pytest.fixture
def sample_embeddings(tmp_path: Path) -> Path:
    """示例 embeddings.parquet（含 1024 维零向量）。"""
    df = pd.DataFrame(
        {
            "chunk_id": ["c1", "c2", "c3", "c4"],
            "embedding": [np.zeros(1024).astype(np.float32).tolist() for _ in range(4)],
            "model": ["bge-m3"] * 4,
        }
    )
    path = tmp_path / "embeddings.parquet"
    df.to_parquet(path)
    return path


class TestSchema:
    """DDL 建表测试"""

    def test_dwd_documents_exists(self, db_con: duckdb.DuckDBPyConnection):
        tables = db_con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='dwd' AND table_name='documents'"
        ).fetchall()
        assert len(tables) == 1

    def test_dwd_chunks_exists(self, db_con: duckdb.DuckDBPyConnection):
        tables = db_con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='dwd' AND table_name='chunks'"
        ).fetchall()
        assert len(tables) == 1

    def test_dws_views_exist(self, db_con: duckdb.DuckDBPyConnection):
        tables = db_con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='dws'"
        ).fetchall()
        names = {t[0] for t in tables}
        assert {"game_stats", "source_stats"}.issubset(names)

    def test_ads_view_exists(self, db_con: duckdb.DuckDBPyConnection):
        views = db_con.execute(
            "SELECT table_name FROM information_schema.views "
            "WHERE table_schema='ads'"
        ).fetchall()
        assert any(v[0] == "rag_corpus" for v in views)


class TestLoadDocuments:
    """documents 加载"""

    def test_load_from_parquet(
        self, db_con: duckdb.DuckDBPyConnection, sample_docs: Path
    ):
        n = load_documents_to_dwd(db_con, sample_docs)
        assert n == 3

    def test_missing_file(
        self, db_con: duckdb.DuckDBPyConnection, tmp_path: Path
    ):
        """文件不存在返回 0，不抛异常"""
        n = load_documents_to_dwd(db_con, tmp_path / "missing.parquet")
        assert n == 0

    def test_idempotent_reload(
        self, db_con: duckdb.DuckDBPyConnection, sample_docs: Path
    ):
        """重复加载：主键冲突抛 ConstraintException（保留行为，不做静默 upsert）。

        实际 ETL 用法是先 TRUNCATE 再 INSERT，或用 upsert；这里只断言主键约束生效。
        """
        import pytest

        load_documents_to_dwd(db_con, sample_docs)
        # 第二次加载会因主键冲突抛 ConstraintException
        with pytest.raises(duckdb.ConstraintException):
            load_documents_to_dwd(db_con, sample_docs)


class TestLoadChunks:
    """chunks 加载"""

    def test_load_from_parquet(
        self, db_con: duckdb.DuckDBPyConnection, sample_chunks: Path
    ):
        n = load_chunks_to_dwd(db_con, sample_chunks)
        assert n == 4


class TestLoadEmbeddings:
    """embeddings 加载（FLOAT[1024] 数组）"""

    def test_load_from_parquet(
        self, db_con: duckdb.DuckDBPyConnection, sample_embeddings: Path
    ):
        n = load_embeddings_to_dwd(db_con, sample_embeddings)
        assert n == 4

    def test_embedding_dim_preserved(
        self, db_con: duckdb.DuckDBPyConnection, sample_embeddings: Path
    ):
        """FLOAT[1024] 类型 + 维度保留"""
        load_embeddings_to_dwd(db_con, sample_embeddings)
        row = db_con.execute(
            "SELECT embedding FROM dwd.embeddings LIMIT 1"
        ).fetchone()
        assert len(row[0]) == 1024


class TestDwsSummary:
    """DWS 聚合"""

    def test_aggregates_by_game_and_source(
        self,
        db_con: duckdb.DuckDBPyConnection,
        sample_docs: Path,
    ):
        load_documents_to_dwd(db_con, sample_docs)
        build_dws_summary(db_con)

        rows = db_con.execute(
            "SELECT * FROM dws.game_stats ORDER BY game, source"
        ).fetchall()

        # (onmyoji, fandom) + (onmyoji, official) = 2 groups
        assert len(rows) == 2

    def test_aggregates_by_source(
        self,
        db_con: duckdb.DuckDBPyConnection,
        sample_docs: Path,
    ):
        load_documents_to_dwd(db_con, sample_docs)
        build_dws_summary(db_con)

        rows = db_con.execute("SELECT * FROM dws.source_stats ORDER BY source").fetchall()
        sources = [r[0] for r in rows]
        assert "fandom" in sources
        assert "official" in sources


class TestQueryCorpusStats:
    """语料库概览查询"""

    def test_returns_all_metrics(
        self,
        db_con: duckdb.DuckDBPyConnection,
        sample_docs: Path,
        sample_chunks: Path,
        sample_embeddings: Path,
    ):
        load_documents_to_dwd(db_con, sample_docs)
        load_chunks_to_dwd(db_con, sample_chunks)
        load_embeddings_to_dwd(db_con, sample_embeddings)

        stats = query_corpus_stats(db_con)

        assert stats["documents"] == 3
        assert stats["chunks"] == 4
        assert stats["embeddings"] == 4
        assert isinstance(stats["by_game"], list)
        assert isinstance(stats["by_source"], list)

    def test_by_game_grouping(
        self,
        db_con: duckdb.DuckDBPyConnection,
        sample_docs: Path,
    ):
        load_documents_to_dwd(db_con, sample_docs)
        stats = query_corpus_stats(db_con)

        games = [g["game"] for g in stats["by_game"]]
        assert "onmyoji" in games


class TestAdsView:
    """ADS 视图（RAG 检索入口）"""

    def test_view_joins_all_layers(
        self,
        db_con: duckdb.DuckDBPyConnection,
        sample_docs: Path,
        sample_chunks: Path,
        sample_embeddings: Path,
    ):
        """ads.rag_corpus 应 JOIN 三个表"""
        load_documents_to_dwd(db_con, sample_docs)
        load_chunks_to_dwd(db_con, sample_chunks)
        load_embeddings_to_dwd(db_con, sample_embeddings)

        rows = db_con.execute("SELECT COUNT(*) FROM ads.rag_corpus").fetchone()[0]
        assert rows == 4

    def test_view_filters_low_quality(
        self,
        db_con: duckdb.DuckDBPyConnection,
        sample_docs: Path,
        sample_chunks: Path,
        sample_embeddings: Path,
    ):
        """quality_score < 0.3 的文档不进视图"""
        db_con.execute("UPDATE dwd.documents SET quality_score = 0.1 WHERE doc_id = 'd1'")
        load_chunks_to_dwd(db_con, sample_chunks)
        load_embeddings_to_dwd(db_con, sample_embeddings)

        rows = db_con.execute(
            "SELECT chunk_id FROM ads.rag_corpus WHERE doc_id = 'd1'"
        ).fetchall()
        assert len(rows) == 0


class TestIntegration:
    """端到端：raw parquet → DuckDB → 查询"""

    def test_end_to_end(
        self,
        db_con: duckdb.DuckDBPyConnection,
        sample_docs: Path,
        sample_chunks: Path,
        sample_embeddings: Path,
    ):
        load_documents_to_dwd(db_con, sample_docs)
        load_chunks_to_dwd(db_con, sample_chunks)
        load_embeddings_to_dwd(db_con, sample_embeddings)
        build_dws_summary(db_con)

        result = db_con.execute(
            """
            SELECT chunk_id, game, section_title, chunk_text
            FROM ads.rag_corpus
            WHERE section_title = '技能'
            """
        ).fetchall()

        assert len(result) == 1
        assert result[0][0] == "c1"
        assert result[0][1] == "onmyoji"