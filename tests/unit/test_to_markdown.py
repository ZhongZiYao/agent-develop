"""Unit tests for src.etl.to_markdown.

覆盖：
- slugify_title 边界条件（空 / 中文 / 非法字符 / 超长）
- make_md_filename 稳定性
- jsonl_to_markdown frontmatter + 正文结构
- iter_jsonl 容错（坏行不崩）
- transform_file / transform_all 真实数据路径
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.etl.to_markdown import (
    iter_jsonl,
    jsonl_to_markdown,
    make_md_filename,
    slugify_title,
    transform_all,
    transform_file,
)


# ===== slugify_title =====
class TestSlugifyTitle:
    def test_empty_string(self):
        assert slugify_title("") == "untitled"

    def test_whitespace_only(self):
        assert slugify_title("   ") == "untitled"

    def test_chinese(self):
        # 中文保留
        assert slugify_title("妖刀姬连招攻略") == "妖刀姬连招攻略"

    def test_english(self):
        assert slugify_title("Bishamonten Guide") == "Bishamonten_Guide"

    def test_illegal_chars(self):
        # / \\ : * ? " < > | 都替换成 _
        result = slugify_title("a/b\\c:d*e?f\"g<h>i|j")
        assert "/" not in result
        assert "\\" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result

    def test_multiple_spaces_collapsed(self):
        assert slugify_title("foo    bar   baz") == "foo_bar_baz"

    def test_max_length(self):
        long = "a" * 100
        result = slugify_title(long, max_len=20)
        assert len(result) <= 20

    def test_strip_underscores(self):
        assert slugify_title("___foo___") == "foo"


# ===== make_md_filename =====
class TestMakeMdFilename:
    def test_basic(self):
        fname = make_md_filename("abc123", "测试标题")
        assert fname.startswith("abc123_")
        assert fname.endswith(".md")

    def test_stable(self):
        # 同样输入同样输出（幂等）
        f1 = make_md_filename("xyz", "Title 1")
        f2 = make_md_filename("xyz", "Title 1")
        assert f1 == f2


# ===== jsonl_to_markdown =====
class TestJsonlToMarkdown:
    def _sample(self, **overrides) -> dict:
        base = {
            "doc_id": "abc123",
            "source": "fandom",
            "game": "onmyoji",
            "url": "https://example.com/wiki/Bishamonten",
            "title": "Bishamonten",
            "author": "WikiUser",
            "publish_date": "2026-09-21",
            "language": "en",
            "clean_text": "# Bishamonten\n\nA shikigami.\n\n## Stats\n\n| HP | ATK |\n|---|---|\n| 1000 | 500 |",
            "word_count": 100,
            "quality_score": 0.85,
            "crawl_ts": "2026-09-21T09:00:00+00:00",
        }
        base.update(overrides)
        return base

    def test_has_frontmatter(self):
        md = jsonl_to_markdown(self._sample())
        assert md.startswith("---\n")
        assert "doc_id: abc123" in md
        assert "source: fandom" in md

    def test_chinese_title_in_frontmatter(self):
        # 中文标题要正确转义（用 json.dumps 加引号）
        md = jsonl_to_markdown(self._sample(title="妖刀姬"))
        # 标题里包含中文
        assert "妖刀姬" in md

    def test_optional_fields_skipped_when_empty(self):
        md = jsonl_to_markdown(self._sample(author="", publish_date=""))
        assert "author:" not in md
        assert "publish_date:" not in md

    def test_body_preserves_markdown(self):
        md = jsonl_to_markdown(self._sample())
        assert "## Stats" in md
        assert "| HP | ATK |" in md

    def test_source_attribution_at_bottom(self):
        md = jsonl_to_markdown(self._sample())
        assert "**来源**" in md
        assert "https://example.com/wiki/Bishamonten" in md


# ===== iter_jsonl =====
class TestIterJsonl:
    def test_skip_invalid_json(self, tmp_path: Path):
        bad = tmp_path / "bad.jsonl"
        bad.write_text(
            '{"valid": 1}\n'
            "this is not json\n"
            '{"also_valid": 2}\n',
            encoding="utf-8",
        )
        records = list(iter_jsonl(bad))
        assert len(records) == 2
        assert records[0]["valid"] == 1
        assert records[1]["also_valid"] == 2

    def test_skip_blank_lines(self, tmp_path: Path):
        p = tmp_path / "blank.jsonl"
        p.write_text('{"a": 1}\n\n{"a": 2}\n\n\n', encoding="utf-8")
        records = list(iter_jsonl(p))
        assert len(records) == 2


# ===== transform_file 真实数据 =====
class TestTransformFile:
    def test_transform_fandom_sample(self, tmp_path: Path):
        # 模拟真实 JSONL 输入
        jsonl_dir = tmp_path / "jsonl" / "fandom"
        jsonl_dir.mkdir(parents=True)
        record = {
            "doc_id": "8799c352be3f4312",
            "source": "fandom",
            "game": "onmyoji",
            "url": "https://onmyoji.fandom.com/wiki/Bishamonten",
            "title": "Bishamonten",
            "language": "zh",
            "clean_text": (
                "# Bishamonten\n\n"
                "Bishamonten is a SP shikigami in Onmyoji. "
                "She excels at dealing AoE damage with her skill "
                "Hyakki Yagyou and ultimate gohudou.\n\n"
                "## Stats\n\n"
                "| HP | ATK | DEF | SPD |\n"
                "|---|---|---|---|\n"
                "| 1200 | 850 | 410 | 115 |\n"
            ),
            "word_count": 100,
            "quality_score": 0.85,
            "crawl_ts": "2026-09-21T09:00:00+00:00",
        }
        jsonl_path = jsonl_dir / "2026-09-21.jsonl"
        jsonl_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

        md_dir = tmp_path / "md"
        count = transform_file(jsonl_path, md_dir=md_dir)
        assert count == 1

        # 验证产物
        out_files = list((md_dir / "fandom").glob("*.md"))
        assert len(out_files) == 1
        content = out_files[0].read_text(encoding="utf-8")
        assert "Bishamonten" in content
        assert "doc_id: 8799c352be3f4312" in content

    def test_skip_short_text(self, tmp_path: Path):
        jsonl_dir = tmp_path / "jsonl" / "fandom"
        jsonl_dir.mkdir(parents=True)
        record = {
            "doc_id": "short1",
            "source": "fandom",
            "title": "Short",
            "clean_text": "hi",  # 不到 50 字
            "word_count": 2,
        }
        jsonl_path = jsonl_dir / "2026-09-21.jsonl"
        jsonl_path.write_text(json.dumps(record), encoding="utf-8")

        count = transform_file(jsonl_path, md_dir=tmp_path / "md")
        assert count == 0

    def test_skip_existing_without_overwrite(self, tmp_path: Path):
        jsonl_dir = tmp_path / "jsonl" / "fandom"
        jsonl_dir.mkdir(parents=True)
        record = {
            "doc_id": "dup1",
            "source": "fandom",
            "title": "Dup",
            "clean_text": "x" * 100,
        }
        jsonl_path = jsonl_dir / "2026-09-21.jsonl"
        jsonl_path.write_text(json.dumps(record), encoding="utf-8")

        md_dir = tmp_path / "md"
        # 第一次
        count1 = transform_file(jsonl_path, md_dir=md_dir)
        assert count1 == 1
        # 第二次不 overwrite
        count2 = transform_file(jsonl_path, md_dir=md_dir, overwrite=False)
        assert count2 == 0
        # 第三次 overwrite
        count3 = transform_file(jsonl_path, md_dir=md_dir, overwrite=True)
        assert count3 == 1


class TestTransformAll:
    def test_recursive_scan(self, tmp_path: Path):
        # 模拟 data/raw/jsonl 结构
        (tmp_path / "jsonl" / "fandom").mkdir(parents=True)
        (tmp_path / "jsonl" / "bili").mkdir(parents=True)
        # _seen_ids.json 应被跳过
        (tmp_path / "jsonl" / "_seen_ids.json").write_text('["x","y"]')

        rec_fandom = {"doc_id": "f1", "source": "fandom", "title": "F1", "clean_text": "x" * 100}
        (tmp_path / "jsonl" / "fandom" / "2026-09-21.jsonl").write_text(
            json.dumps(rec_fandom), encoding="utf-8"
        )
        rec_bili = {"doc_id": "b1", "source": "bili", "title": "B1", "clean_text": "y" * 100}
        (tmp_path / "jsonl" / "bili" / "2026-09-21.jsonl").write_text(
            json.dumps(rec_bili), encoding="utf-8"
        )

        stats = transform_all(jsonl_dir=tmp_path / "jsonl", md_dir=tmp_path / "md")
        assert stats.get("fandom") == 1
        assert stats.get("bili") == 1
        # _seen_ids.json 不会出现在统计里
        assert "_seen_ids" not in stats
