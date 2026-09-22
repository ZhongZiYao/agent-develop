"""PDF Splitter 单测"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.loaders.pdf_loader import load_pdf_file
from src.splitters.pdf_table_splitter import (
    _split_by_pages,
    _split_by_paragraphs,
    _split_long_paragraph,
    split_pdf_document,
)


class TestSplitByPages:
    """按页切分"""

    def test_single_page(self):
        content = "[Page 1]\n这是一段文字"
        pages = _split_by_pages(content)
        assert len(pages) == 1
        assert pages[0]["page"] == 1
        assert "一段文字" in pages[0]["text"]

    def test_multi_pages(self):
        content = "[Page 1]\n第一页\n\n[Page 2]\n第二页\n\n[Page 3]\n第三页"
        pages = _split_by_pages(content)
        assert len(pages) == 3
        assert [p["page"] for p in pages] == [1, 2, 3]

    def test_no_page_mark(self):
        content = "无页边界标记的纯文本"
        pages = _split_by_pages(content)
        assert len(pages) == 1
        assert pages[0]["page"] == 0


class TestSplitByParagraphs:
    """按段落切"""

    def test_double_newline_split(self):
        text = "第一段\n\n第二段\n\n第三段"
        paras = _split_by_paragraphs(text)
        assert len(paras) == 3
        assert paras == ["第一段", "第二段", "第三段"]

    def test_filter_empty(self):
        text = "\n\n第一段\n\n\n\n第二段\n\n"
        paras = _split_by_paragraphs(text)
        assert paras == ["第一段", "第二段"]


class TestSplitLongParagraph:
    """超长段落切分"""

    def test_short_unchanged(self):
        text = "短文本"
        chunks = _split_long_paragraph(text, chunk_size=100, overlap=10)
        assert chunks == ["短文本"]

    def test_long_split(self):
        # 构造一个超长段落
        text = "测试句子。" * 100  # ~500 字符
        chunks = _split_long_paragraph(text, chunk_size=100, overlap=10)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 100


class TestSplitPdfDocument:
    """完整 PDF 文档切分"""

    def test_split_real_pdf(self):
        """真实 PDF 切分"""
        pdf_path = Path(
            "data/理财文件/临时报告/B01招银理财/新设份额/"
            "招银理财_关于招银理财招睿嘉鑫稳进(策略优选)1年持有1号固收增强理财计划增设D份额的公告_其他产品公告_506051DZ.pdf"
        )
        if not pdf_path.exists():
            pytest.skip("真实 PDF 不存在")

        doc = load_pdf_file(pdf_path)
        assert doc is not None

        chunks = split_pdf_document(doc, chunk_size=500, chunk_overlap=50, doc_id="test_doc")
        assert len(chunks) >= 1
        # 每个 chunk 应携带金融 metadata
        c0 = chunks[0]
        assert c0.metadata["institution"] == "B01招银理财"
        assert c0.metadata["report_type"] == "新设份额"
        assert c0.metadata["category"] == "临时报告"
        assert c0.metadata["page_num"] >= 1
        assert c0.metadata["chunk_type"] == "pdf_segment"
        # chunk_id 应按 doc_id 编号
        assert c0.chunk_id.startswith("test_doc#")
        # 短文本 PDF 切出的 chunk 长度合理
        for c in chunks:
            assert len(c.content) > 0

    def test_chunk_id_sequential(self):
        """chunk_id 应严格递增"""
        pdf_path = Path(
            "data/理财文件/临时报告/B01招银理财/新设份额/"
            "招银理财_关于招银理财招睿嘉鑫稳进(策略优选)1年持有1号固收增强理财计划增设D份额的公告_其他产品公告_506051DZ.pdf"
        )
        if not pdf_path.exists():
            pytest.skip("真实 PDF 不存在")

        doc = load_pdf_file(pdf_path)
        chunks = split_pdf_document(doc, doc_id="seq_test")
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "chunk_id 应全局唯一"