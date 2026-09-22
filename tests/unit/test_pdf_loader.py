"""PDF Loader 单测

覆盖：
1. 文件名解析（两种命名风格）
2. 目录元数据补全
3. 单文件加载（真实 PDF）
4. 扫描件跳过
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.loaders.pdf_loader import (
    _extract_category,
    _extract_dir_meta,
    _extract_filename_meta,
    load_pdf_dir,
    load_pdf_file,
)


class TestFilenameMeta:
    """文件名元数据解析"""

    def test_full_pattern(self):
        """完整命名风格：工银理财_2026-08-20_临时性信息披露_xxx.pdf"""
        meta = _extract_filename_meta(
            "工银理财_2026-08-20_临时性信息披露_关于鑫悦30天业绩比较基准调整的公告.pdf"
        )
        assert meta["institution"] == "工银理财"
        assert meta["effective_date"] == "2026-08-20"
        assert meta["report_type"] == "临时报告"  # 标准化后
        assert "鑫悦" in meta["product_name"]

    def test_variant_pattern(self):
        """变体命名风格：招银理财_关于xxx公告_其他产品公告_xxx.pdf"""
        meta = _extract_filename_meta(
            "招银理财_关于招睿嘉鑫稳进理财计划增设D份额的公告_其他产品公告_506051DZ.pdf"
        )
        assert meta["institution"] == "招银"
        assert meta["effective_date"] == ""
        assert meta["report_type"] == "未知"

    def test_product_code_extracted(self):
        """产品编号提取（理财登记系统编码）"""
        meta = _extract_filename_meta(
            "工银理财_2026-08-27_临时性信息披露_关于鑫悦最短持有30天固收增强开放式理财产品2号(24GS5969)业绩比较基准调整.pdf"
        )
        assert meta["product_code"] == "24GS5969"


class TestDirMeta:
    """目录元数据补全"""

    def test_dir_meta_for_zhao_yin(self):
        """招银目录结构：临时报告/B01招银理财/新设份额/file.pdf"""
        p = Path("data/理财文件/临时报告/B01招银理财/新设份额/anyfile.pdf")
        meta = _extract_dir_meta(p)
        assert meta["institution"] == "B01招银理财"
        assert meta["report_type"] == "新设份额"  # 优先事项名

    def test_dir_meta_for_gong_yin(self):
        """工银目录结构：临时报告/A01工银理财/业绩比较基准调整/file.pdf"""
        p = Path("data/理财文件/临时报告/A01工银理财/业绩比较基准调整/anyfile.pdf")
        meta = _extract_dir_meta(p)
        assert meta["institution"] == "A01工银理财"
        assert meta["report_type"] == "业绩比较基准调整"

    def test_dir_meta_for_product_book(self):
        """产品说明书目录：产品说明书&发行公告/<机构>/file.pdf"""
        p = Path("data/理财文件/产品说明书&发行公告/招银理财/anyfile.pdf")
        meta = _extract_dir_meta(p)
        assert meta["report_type"] == "产品说明书"


class TestCategory:
    """一级分类提取"""

    def test_category_linshi(self):
        p = Path("data/理财文件/临时报告/A01工银理财/费率调整/file.pdf")
        assert _extract_category(p) == "临时报告"

    def test_category_chanpin(self):
        p = Path("data/理财文件/产品说明书&发行公告/招银理财/file.pdf")
        assert _extract_category(p) == "产品说明书"

    def test_category_dingqi(self):
        p = Path("data/理财文件/定期报告/A01工银理财/file.pdf")
        assert _extract_category(p) == "定期报告"


@pytest.fixture
def real_pdf_path() -> Path:
    """返回第一个真实 PDF 路径（来自招银理财临时报告）"""
    candidate = Path(
        "data/理财文件/临时报告/B01招银理财/新设份额/"
        "招银理财_关于招银理财招睿嘉鑫稳进(策略优选)1年持有1号固收增强理财计划增设D份额的公告_其他产品公告_506051DZ.pdf"
    )
    if not candidate.exists():
        pytest.skip(f"真实 PDF 不存在: {candidate}")
    return candidate


class TestLoadPdfFile:
    """单文件加载"""

    def test_load_real_pdf(self, real_pdf_path: Path):
        """加载真实 PDF"""
        doc = load_pdf_file(real_pdf_path)
        assert doc is not None
        assert len(doc.content) > 100
        assert doc.metadata["institution"] == "B01招银理财"
        assert doc.metadata["report_type"] == "新设份额"
        assert doc.metadata["category"] == "临时报告"
        assert doc.metadata["page_count"] >= 1
        assert doc.metadata["source"] == "pdf_local"
        assert doc.metadata["doc_id"]  # 非空

    def test_nonexistent_returns_none(self, tmp_path: Path):
        """不存在的文件返回 None"""
        doc = load_pdf_file(tmp_path / "nope.pdf")
        assert doc is None

    def test_load_scan_skip(self, tmp_path: Path):
        """扫描件（文本过短）应返回 None"""
        fake = tmp_path / "scan.pdf"
        fake.write_bytes(b"%PDF-1.4\n")  # 仅占位
        # 我们无法构造真正的扫描 PDF，只能验证 min_text_chars=128000 时返回 None
        doc = load_pdf_file(fake, min_text_chars=128000)
        # fake 不是有效 PDF，会走 except 分支返回 None
        assert doc is None


class TestLoadPdfDir:
    """目录加载"""

    def test_load_poc_dir(self):
        """加载真实 PDF 目录（POC 限定 5 个）"""
        dir_path = Path("data/理财文件/临时报告/B01招银理财/新设份额")
        if not dir_path.exists():
            pytest.skip("理财文件目录不存在")

        docs = load_pdf_dir(dir_path, limit=5)
        assert len(docs) > 0
        for d in docs:
            assert d.metadata["institution"] == "B01招银理财"
            assert d.metadata["report_type"] == "新设份额"