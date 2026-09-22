"""PDF Transform + DuckDB loader 单测"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from src.etl.load_duckdb_financial import (
    DUCKDB_PATH,
    init_warehouse,
    load_chunks_to_duckdb,
)
from src.etl.transform_pdf import transform_pdfs_to_chunks


@pytest.fixture(scope="module")
def poc_chunks_parquet(tmp_path_factory):
    """跑 5 个 PDF 的 POC transform，返回 parquet 路径"""
    pdf_dir = Path("data/理财文件/临时报告/B01招银理财/新设份额")
    if not pdf_dir.exists():
        pytest.skip("理财文件目录不存在")

    out_dir = tmp_path_factory.mktemp("poc")
    out_path = out_dir / "chunks.parquet"

    transform_pdfs_to_chunks(
        pdf_dir=pdf_dir,
        output_parquet=out_path,
        limit=5,
    )
    return out_path


class TestTransform:
    """PDF Transform 测试"""

    def test_chunks_parquet_exists(self, poc_chunks_parquet):
        assert poc_chunks_parquet.exists()

    def test_chunks_parquet_columns(self, poc_chunks_parquet):
        """验证 parquet 列结构"""
        import pandas as pd
        df = pd.read_parquet(poc_chunks_parquet)
        required = [
            "chunk_id", "doc_id", "chunk_index", "chunk_text",
            "institution", "report_type", "effective_date", "product_name",
            "product_code", "title", "filename", "file_path",
            "category", "page_num", "page_count",
        ]
        for col in required:
            assert col in df.columns, f"缺少列: {col}"

    def test_chunks_have_finance_metadata(self, poc_chunks_parquet):
        """每个 chunk 应携带金融 metadata"""
        import pandas as pd
        df = pd.read_parquet(poc_chunks_parquet)
        for col in ["institution", "report_type", "category"]:
            assert df[col].notna().all(), f"{col} 不能为空"
            assert (df[col] != "").all(), f"{col} 不能为空字符串"
        # 招银文件 institution 应一致
        assert df["institution"].unique().tolist() == ["B01招银理财"]

    def test_chunk_id_unique(self, poc_chunks_parquet):
        """chunk_id 应全局唯一"""
        import pandas as pd
        df = pd.read_parquet(poc_chunks_parquet)
        assert df["chunk_id"].is_unique


class TestDuckDBLoad:
    """DuckDB 数仓加载测试"""

    def test_init_schema(self, tmp_path):
        """schema 初始化幂等"""
        db_path = tmp_path / "test.duckdb"
        con1 = init_warehouse(db_path)
        con1.close()
        con2 = init_warehouse(db_path)
        # 表应存在
        tables = con2.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='dwd'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        assert {"documents", "chunks", "embeddings"}.issubset(table_names)
        con2.close()

    def test_load_chunks_idempotent(self, poc_chunks_parquet, tmp_path):
        """两次加载应幂等（不重复）"""
        db_path = tmp_path / "test_load.duckdb"
        n1 = load_chunks_to_duckdb(poc_chunks_parquet, db_path=db_path)
        n2 = load_chunks_to_duckdb(poc_chunks_parquet, db_path=db_path)
        # 两次数量应一致（幂等）
        assert n1 == n2
        con = duckdb.connect(str(db_path), read_only=True)
        n_actual = con.execute("SELECT COUNT(*) FROM dwd.chunks").fetchone()[0]
        assert n_actual == n1
        con.close()

    def test_load_chunks_to_default_db(self, poc_chunks_parquet):
        """加载到默认 finguide.duckdb（CI 跳过）"""
        import os
        if not os.environ.get("INTEGRATION_TESTS"):
            pytest.skip("需要 INTEGRATION_TESTS=1")

        n = load_chunks_to_duckdb(poc_chunks_parquet)
        assert n > 0
        con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        assert con.execute("SELECT COUNT(*) FROM dwd.chunks").fetchone()[0] > 0
        con.close()