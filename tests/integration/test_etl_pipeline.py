"""ETL 端到端集成测试。

模拟真实 ETL 流水线：raw JSONL → transform → embed → load_duckdb。
GPU / Chroma 全部 mock 掉，只验证流水线编排正确。

注：实际部署时此测试作为 CI smoke test；不走真实模型权重。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pytest


# ===== Mock SentenceTransformer =====


class _FakeEncoder:
    """bge-m3 替代品：返回零向量，维度 1024。"""

    def __init__(self, *args, **kwargs):
        self.dim = 1024

    def half(self):
        return self

    def encode(self, sentences, batch_size=32, **kwargs):
        n = len(sentences)
        return np.ones((n, self.dim), dtype=np.float32) / np.sqrt(self.dim)


@pytest.fixture
def fake_st(monkeypatch: pytest.MonkeyPatch):
    """monkeypatch sentence_transformers。"""
    mod = type(sys)("fake_st")
    mod.SentenceTransformer = _FakeEncoder
    monkeypatch.setitem(sys.modules, "sentence_transformers", mod)
    return mod


# ===== Sample raw data =====


@pytest.fixture
def raw_jsonl(tmp_path: Path) -> Path:
    """5 篇示例文档，覆盖不同游戏 / 来源。"""
    raw_dir = tmp_path / "raw" / "jsonl"
    sources = ["fandom", "official"]
    samples = [
        {
            "doc_id": "d1", "source": "fandom", "game": "onmyoji",
            "title": "妖刀姬",
            "clean_text": (
                "# 妖刀姬\n\n"
                "## 技能\n\n"
                "妖刀姬是强力单体输出式神，能斩首刀，造成大量单体伤害。"
                "她的技能机制依赖连击次数，最大化暴击收益。\n\n"
                "## 御魂\n\n"
                "推荐破势四件套，暴击两件套。"
                "副属性优先暴击、暴伤、攻击加成。\n\n"
                "## 阵容搭配\n\n"
                "常见搭配：妖刀姬 + 鬼切 + 大天狗 + 茨木 + 八岐大蛇。"
            ),
            "quality_score": 0.85, "word_count": 200, "language": "zh",
            "crawl_ts": "2026-09-21",
        },
        {
            "doc_id": "d2", "source": "fandom", "game": "genshin",
            "title": "原神角色图鉴",
            "clean_text": (
                "# 原神\n\n"
                "## 角色\n\n"
                "包含旅行者、派蒙等核心 NPC，覆盖七元素体系。"
                "每位角色都有独特的元素爆发和元素战技机制。\n\n"
                "## 元素\n\n"
                "火、水、雷、风、冰、岩、草 七大元素。"
                "元素反应是战斗核心。"
            ),
            "quality_score": 0.9, "word_count": 150, "language": "zh",
            "crawl_ts": "2026-09-21",
        },
        {
            "doc_id": "d3", "source": "official", "game": "onmyoji",
            "title": "S13 赛季更新公告",
            "clean_text": (
                "# S13 赛季\n\n"
                "## 改动\n\n"
                "新角色上线，新副本开放，"
                "原有式神数值平衡性调整。\n\n"
                "## 平衡性\n\n"
                "调整部分式神的技能机制，优化游戏体验。"
                "本次更新涵盖 20+ 式神的数值变化。"
            ),
            "quality_score": 0.95, "word_count": 150, "language": "zh",
            "crawl_ts": "2026-09-21",
        },
        {
            "doc_id": "d4", "source": "fandom", "game": "onmyoji",
            "title": "低质量文档",
            "clean_text": "abc",  # 会被丢弃（太短）
            "quality_score": 0.1, "word_count": 3, "language": "zh",
            "crawl_ts": "2026-09-21",
        },
        {
            "doc_id": "d5", "source": "official", "game": "genshin",
            "title": "原神 v4.0 公告",
            "clean_text": (
                "# v4.0\n\n"
                "## 新角色\n\n"
                "枫丹新增 5 个角色，包含水元素主C与辅助。"
                "新角色带来全新的元素反应机制。\n\n"
                "## 系统\n\n"
                "圣遗物系统优化，副属性洗炼更便捷。"
            ),
            "quality_score": 0.9, "word_count": 180, "language": "zh",
            "crawl_ts": "2026-09-21",
        },
    ]

    for src in set(s["source"] for s in samples):
        (raw_dir / src).mkdir(parents=True, exist_ok=True)
        with (raw_dir / src / "2026-09-21.jsonl").open("w", encoding="utf-8") as f:
            for s in samples:
                if s["source"] == src:
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")
    return raw_dir


# ===== 测试 =====


class TestPipelineEndToEnd:
    """完整流水线：raw → transform → embed → load_duckdb"""

    def test_transform_embeds_loads_to_duckdb(
        self,
        raw_jsonl: Path,
        fake_st,
        tmp_path: Path,
        monkeypatch,
    ):
        """3 阶段全跑通（GPU/Chroma mock 掉）"""
        from src.etl import embed as embed_mod
        from src.etl.load_duckdb import (
            build_dws_summary,
            build_duckdb_warehouse,
            load_chunks_to_dwd,
            load_documents_to_dwd,
            load_embeddings_to_dwd,
        )
        from src.etl.transform import transform_documents, save_parquet

        # ===== Stage 1: Transform =====
        chunks_df, meta_df = transform_documents(raw_dir=raw_jsonl)
        # 5 篇输入，1 篇低质量被丢 → 4 篇 meta
        assert len(meta_df) == 4
        assert "d4" not in meta_df["doc_id"].values

        # 切分产出 chunks
        assert len(chunks_df) >= 4  # 每篇至少 1 个 chunk

        # 落盘到 clean/
        monkeypatch.setattr("src.etl.transform.CLEAN_DIR", tmp_path)
        save_parquet(chunks_df, meta_df, out_dir=tmp_path)

        # ===== Stage 2: Embed (mock GPU) =====
        monkeypatch.setattr(embed_mod, "CLEAN_DIR", tmp_path)
        # monkeypatch 函数默认参数
        embed_mod.load_chunks_parquet.__defaults__ = (tmp_path / "chunks.parquet",)
        embed_mod.save_embeddings.__defaults__ = (tmp_path / "embeddings.parquet",)

        # 不用 run()，手动调用避免 GPU 检测
        chunks_for_embed = embed_mod.load_chunks_parquet()
        embeddings_df = embed_mod.embed_chunks(chunks_for_embed)
        embed_mod.save_embeddings(embeddings_df)

        assert (tmp_path / "embeddings.parquet").exists()
        assert len(embeddings_df) == len(chunks_df)

        # ===== Stage 3: Load DuckDB =====
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        build_duckdb_warehouse(con)
        load_documents_to_dwd(con, tmp_path / "meta.parquet")
        load_chunks_to_dwd(con, tmp_path / "chunks.parquet")
        load_embeddings_to_dwd(con, tmp_path / "embeddings.parquet")
        build_dws_summary(con)

        # 验证：docs / chunks / embeddings 行数一致
        n_docs = con.execute("SELECT COUNT(*) FROM dwd.documents").fetchone()[0]
        n_chunks = con.execute("SELECT COUNT(*) FROM dwd.chunks").fetchone()[0]
        n_emb = con.execute("SELECT COUNT(*) FROM dwd.embeddings").fetchone()[0]

        assert n_docs == 4
        assert n_chunks == len(chunks_df)
        assert n_emb == len(chunks_df)

        # 验证：DWS 聚合按 game / source 都有
        games = con.execute(
            "SELECT DISTINCT game FROM dws.game_stats"
        ).fetchall()
        assert {g[0] for g in games} == {"onmyoji", "genshin"}

        sources = con.execute(
            "SELECT DISTINCT source FROM dws.source_stats"
        ).fetchall()
        assert {s[0] for s in sources} == {"fandom", "official"}

        # 验证：ADS 视图可查询（按 game 过滤）
        onmyoji_chunks = con.execute(
            "SELECT COUNT(*) FROM ads.rag_corpus WHERE game = 'onmyoji'"
        ).fetchone()[0]
        assert onmyoji_chunks > 0

        con.close()


class TestDataLineage:
    """数据血缘：从 raw → DWD → ADS 全链路可追溯"""

    def test_ads_view_traces_back_to_raw(
        self,
        raw_jsonl: Path,
        fake_st,
        tmp_path: Path,
        monkeypatch,
    ):
        """ADS 视图的每行都能追溯到 raw JSONL 中的原始文档"""
        from src.etl import embed as embed_mod
        from src.etl.load_duckdb import (
            build_duckdb_warehouse,
            load_chunks_to_dwd,
            load_documents_to_dwd,
            load_embeddings_to_dwd,
        )
        from src.etl.transform import transform_documents, save_parquet

        # ETL 全跑
        chunks_df, meta_df = transform_documents(raw_dir=raw_jsonl)
        monkeypatch.setattr("src.etl.transform.CLEAN_DIR", tmp_path)
        save_parquet(chunks_df, meta_df, out_dir=tmp_path)

        monkeypatch.setattr(embed_mod, "CLEAN_DIR", tmp_path)
        embed_mod.load_chunks_parquet.__defaults__ = (tmp_path / "chunks.parquet",)
        embed_mod.save_embeddings.__defaults__ = (tmp_path / "embeddings.parquet",)
        chunks_for_embed = embed_mod.load_chunks_parquet()
        embeddings_df = embed_mod.embed_chunks(chunks_for_embed)
        embed_mod.save_embeddings(embeddings_df)

        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        build_duckdb_warehouse(con)
        load_documents_to_dwd(con, tmp_path / "meta.parquet")
        load_chunks_to_dwd(con, tmp_path / "chunks.parquet")
        load_embeddings_to_dwd(con, tmp_path / "embeddings.parquet")

        # 血缘追溯：找一篇 onmyoji + official 的文档（如 S13 公告 d3）
        rows = con.execute(
            """
            SELECT c.chunk_id, c.doc_id, d.title, d.source, c.chunk_text
            FROM ads.rag_corpus c
            JOIN dwd.documents d ON c.doc_id = d.doc_id
            WHERE d.doc_id = 'd3'
            """
        ).fetchall()

        assert len(rows) > 0
        for chunk_id, doc_id, title, source, chunk_text in rows:
            assert doc_id == "d3"
            assert title == "S13 赛季更新公告"
            assert source == "official"
            assert len(chunk_text) > 0

        con.close()


class TestScaleBehavior:
    """大规模数据下的行为"""

    def test_1000_docs_handled(self, tmp_path: Path, fake_st, monkeypatch):
        """1000 篇文档可正常处理（性能不测，只验证跑通）"""
        from src.etl import embed as embed_mod
        from src.etl.load_duckdb import (
            build_duckdb_warehouse,
            load_chunks_to_dwd,
            load_documents_to_dwd,
            load_embeddings_to_dwd,
            build_dws_summary,
            query_corpus_stats,
        )
        from src.etl.transform import transform_documents, save_parquet

        # 生成 1000 篇
        raw_dir = tmp_path / "raw" / "jsonl" / "fandom"
        raw_dir.mkdir(parents=True)
        with (raw_dir / "test.jsonl").open("w", encoding="utf-8") as f:
            for i in range(1000):
                f.write(json.dumps({
                    "doc_id": f"d{i}",
                    "source": "fandom",
                    "game": "onmyoji",
                    "title": f"Title {i}",
                    "clean_text": f"# Title {i}\n\n## Section\n\n" + ("内容 " * 30),
                    "quality_score": 0.8,
                    "word_count": 100,
                    "language": "zh",
                    "crawl_ts": "2026-09-21",
                }, ensure_ascii=False) + "\n")

        chunks_df, meta_df = transform_documents(raw_dir=tmp_path / "raw")
        assert len(meta_df) == 1000

        # 不实际保存 parquet / embed，节省测试时间
        # 只验证查询接口
        monkeypatch.setattr("src.etl.transform.CLEAN_DIR", tmp_path)
        save_parquet(chunks_df, meta_df, out_dir=tmp_path)

        # embed（mock GPU）
        monkeypatch.setattr(embed_mod, "CLEAN_DIR", tmp_path)
        embed_mod.load_chunks_parquet.__defaults__ = (tmp_path / "chunks.parquet",)
        embed_mod.save_embeddings.__defaults__ = (tmp_path / "embeddings.parquet",)
        chunks_for_embed = embed_mod.load_chunks_parquet()
        # batch=64 提速
        embeddings_df = embed_mod.embed_chunks(chunks_for_embed, batch_size=128)
        assert len(embeddings_df) == len(chunks_df)
        embed_mod.save_embeddings(embeddings_df)

        # 加载数仓
        db_path = tmp_path / "test.duckdb"
        con = duckdb.connect(str(db_path))
        build_duckdb_warehouse(con)
        load_documents_to_dwd(con, tmp_path / "meta.parquet")
        load_chunks_to_dwd(con, tmp_path / "chunks.parquet")
        load_embeddings_to_dwd(con, tmp_path / "embeddings.parquet")
        build_dws_summary(con)

        stats = query_corpus_stats(con)
        assert stats["documents"] == 1000
        assert stats["chunks"] >= 1000  # 每篇 1+ 个 chunk（短文可能不切分）

        con.close()