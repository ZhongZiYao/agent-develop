"""ETL Transform 层单元测试。

覆盖：
- chunk_id 稳定性（同 doc_id + index → 同 hash）
- 章节检测（Markdown 标题识别）
- 章节归属（chunk 位置 → 章节标题）
- JSONL 流式读取
- 质量过滤（低 quality 丢弃）
- Parquet 落盘 + 读回（数据完整性）
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.etl import transform as transform_mod
from src.etl.transform import (
    detect_sections,
    find_section_for_pos,
    iter_raw_jsonl,
    make_chunk_id,
    save_parquet,
    transform_documents,
)


# ===== Fixtures =====


@pytest.fixture
def sample_raw_jsonl(tmp_path: Path) -> Path:
    """构造示例 raw jsonl（写入到 raw/jsonl/fandom/test.jsonl）。

    返回 raw 根目录，调用方传 iter_raw_jsonl / transform_documents。
    """
    raw_dir = tmp_path / "raw"
    fandom_dir = raw_dir / "jsonl" / "fandom"
    fandom_dir.mkdir(parents=True)

    samples = [
        {
            "doc_id": "aaaa1111",
            "source": "fandom",
            "game": "onmyoji",
            "url": "https://onmyoji.fandom.com/wiki/YaoDaoJi",
            "title": "妖刀姬",
            "clean_text": "# 妖刀姬\n\n## 技能\n\n妖刀姬是强力输出式神，能造成大量单体伤害。\n\n## 御魂\n\n推荐破势，暴击收益高。",
            "word_count": 100,
            "quality_score": 0.8,
            "language": "zh",
            "crawl_ts": "2026-09-21T00:00:00Z",
        },
        {
            "doc_id": "bbbb2222",
            "source": "fandom",
            "game": "onmyoji",
            "url": "https://onmyoji.fandom.com/wiki/HongDie",
            "title": "红蝶",
            "clean_text": "太短了",  # < 50 字符，会被丢弃
            "word_count": 4,
            "quality_score": 0.2,  # 低分
            "language": "zh",
            "crawl_ts": "2026-09-21T00:00:00Z",
        },
        {
            "doc_id": "cccc3333",
            "source": "fandom",
            "game": "onmyoji",
            "url": "https://onmyoji.fandom.com/wiki/S13",
            "title": "S13 赛季",
            "clean_text": "# S13 赛季\n\n## 上分攻略\n\n强势英雄：妖刀姬、不知火舞。\n\n## ban 位\n\nban 阎王避免被针对。",
            "word_count": 80,
            "quality_score": 0.7,
            "language": "zh",
            "crawl_ts": "2026-09-21T00:00:00Z",
        },
    ]
    path = fandom_dir / "test.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    return raw_dir


# ===== Tests =====


class TestMakeChunkId:
    """chunk_id 稳定性 + 唯一性"""

    def test_same_input_same_id(self):
        id1 = make_chunk_id("doc1", 0)
        id2 = make_chunk_id("doc1", 0)
        assert id1 == id2

    def test_different_index_different_id(self):
        assert make_chunk_id("doc1", 0) != make_chunk_id("doc1", 1)

    def test_different_doc_different_id(self):
        assert make_chunk_id("doc1", 0) != make_chunk_id("doc2", 0)

    def test_id_length(self):
        assert len(make_chunk_id("doc", 0)) == 16


class TestDetectSections:
    """Markdown 章节检测"""

    def test_single_section(self):
        text = "# 标题\n\n内容"
        sections = detect_sections(text)
        assert len(sections) == 1
        assert sections[0][1] == "标题"
        assert sections[0][2] == 1

    def test_nested_sections(self):
        text = "# 一级\n\n内容\n\n## 二级\n\n内容\n\n### 三级\n\n内容"
        sections = detect_sections(text)
        assert len(sections) == 3
        assert [s[2] for s in sections] == [1, 2, 3]

    def test_no_section(self):
        assert detect_sections("没有标题的内容") == []

    def test_section_positions(self):
        text = "前置\n# 标题\n后置"
        sections = detect_sections(text)
        assert len(sections) == 1
        assert sections[0][0] < text.find("# 标题") + 10


class TestFindSectionForPos:
    """位置 → 章节归属"""

    def test_in_first_section(self):
        sections = [(0, "章节A", 1), (100, "章节B", 1)]
        assert find_section_for_pos(50, sections) == "章节A"

    def test_in_second_section(self):
        sections = [(0, "章节A", 1), (100, "章节B", 1)]
        assert find_section_for_pos(150, sections) == "章节B"

    def test_before_any_section(self):
        sections = [(50, "章节A", 1)]
        assert find_section_for_pos(10, sections) == "(无章节)"

    def test_empty_sections(self):
        assert find_section_for_pos(50, []) == "(无章节)"


class TestIterRawJsonl:
    """JSONL 流式读取"""

    def test_iterates_all_docs(self, sample_raw_jsonl: Path):
        docs = list(iter_raw_jsonl(sample_raw_jsonl))
        assert len(docs) == 3

    def test_skips_seen_file(self, tmp_path: Path):
        """以 _ 开头的 jsonl 跳过（_seen_ids.json 之类）"""
        raw_dir = tmp_path / "raw"
        (raw_dir / "jsonl" / "fandom").mkdir(parents=True)
        (raw_dir / "jsonl" / "fandom" / "_seen_ids.json").write_text("[]")
        (raw_dir / "jsonl" / "fandom" / "data.jsonl").write_text(
            json.dumps({"doc_id": "x", "clean_text": "x" * 100, "quality_score": 0.5}) + "\n"
        )
        docs = list(iter_raw_jsonl(raw_dir))
        assert len(docs) == 1

    def test_skips_invalid_json(self, tmp_path: Path):
        """JSON 解析失败的行被跳过，不抛异常"""
        raw_dir = tmp_path / "raw"
        (raw_dir / "jsonl" / "fandom").mkdir(parents=True)
        (raw_dir / "jsonl" / "fandom" / "data.jsonl").write_text(
            "not valid json\n"
            + json.dumps({"doc_id": "x", "clean_text": "x" * 100, "quality_score": 0.5})
            + "\n"
        )
        docs = list(iter_raw_jsonl(raw_dir))
        assert len(docs) == 1

    def test_missing_dir(self, tmp_path: Path):
        docs = list(iter_raw_jsonl(tmp_path / "nonexistent"))
        assert docs == []


class TestTransformDocuments:
    """主流程：清洗 + 切分"""

    def test_quality_filter_drops_low_quality(self, sample_raw_jsonl: Path):
        """quality_score < 0.3 的文档被丢弃"""
        chunks_df, meta_df = transform_documents(
            raw_dir=sample_raw_jsonl, min_quality=0.3
        )
        assert len(meta_df) == 2  # 1 篇低质量被丢
        assert "bbbb2222" not in meta_df["doc_id"].values

    def test_short_text_filter(self, sample_raw_jsonl: Path):
        """clean_text 太短被丢"""
        chunks_df, meta_df = transform_documents(raw_dir=sample_raw_jsonl)
        # 妖刀姬 + S13 = 2 篇
        assert len(meta_df) == 2

    def test_chunks_have_section_title(self, sample_raw_jsonl: Path):
        """每个 chunk 都有 section_title 字段"""
        chunks_df, _ = transform_documents(raw_dir=sample_raw_jsonl)
        assert "section_title" in chunks_df.columns
        assert len(chunks_df) > 0
        # 至少有非空 section_title
        non_empty = chunks_df["section_title"].fillna("").astype(str)
        assert non_empty.str.len().gt(0).any(), (
            f"应有非空 section_title，实际: {chunks_df['section_title'].tolist()}"
        )

    def test_chunk_id_format(self, sample_raw_jsonl: Path):
        """chunk_id 唯一 + 16 字符"""
        chunks_df, _ = transform_documents(raw_dir=sample_raw_jsonl)
        assert all(len(c) == 16 for c in chunks_df["chunk_id"])
        assert chunks_df["chunk_id"].is_unique

    def test_metadata_columns(self, sample_raw_jsonl: Path):
        """meta df 必含列"""
        _, meta_df = transform_documents(raw_dir=sample_raw_jsonl)
        expected = {
            "doc_id",
            "source",
            "game",
            "title",
            "url",
            "word_count",
            "quality_score",
            "language",
            "crawl_ts",
        }
        assert expected.issubset(set(meta_df.columns))


class TestSaveParquet:
    """Parquet 落盘"""

    def test_roundtrip(self, tmp_path: Path):
        """写入 + 读回 数据一致"""
        chunks_df = pd.DataFrame(
            {
                "chunk_id": ["abc", "def"],
                "doc_id": ["d1", "d1"],
                "chunk_text": ["文本1", "文本2"],
            }
        )
        meta_df = pd.DataFrame(
            {
                "doc_id": ["d1"],
                "title": ["标题"],
                "source": ["fandom"],
            }
        )
        chunks_path, meta_path = save_parquet(chunks_df, meta_df, out_dir=tmp_path)

        chunks_back = pd.read_parquet(chunks_path)
        meta_back = pd.read_parquet(meta_path)

        assert len(chunks_back) == 2
        assert chunks_back["chunk_id"].tolist() == ["abc", "def"]
        assert meta_back["title"].iloc[0] == "标题"

    def test_creates_dir(self, tmp_path: Path):
        target_dir = tmp_path / "deep" / "nested" / "dir"
        chunks_df = pd.DataFrame({"chunk_id": ["x"]})
        meta_df = pd.DataFrame({"doc_id": ["d"]})
        save_parquet(chunks_df, meta_df, out_dir=target_dir)
        assert target_dir.exists()