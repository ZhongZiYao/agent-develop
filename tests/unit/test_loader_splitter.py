"""Loader + Splitter 单测"""

import tempfile
from pathlib import Path

import pytest

from src.loaders.markdown_loader import load_markdown_dir, load_markdown_file, make_doc_id
from src.schemas import Document
from src.splitters.recursive_splitter import split_document, split_documents


def test_load_markdown_file():
    """测试加载单个 md 文件"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# 测试标题\n\n这是正文内容。")
        tmp_path = Path(f.name)

    try:
        doc = load_markdown_file(tmp_path)
        assert "测试标题" in doc.content
        assert doc.metadata["title"] == "测试标题"
        assert doc.metadata["filename"] == tmp_path.name
    finally:
        tmp_path.unlink()


def test_load_markdown_dir(tmp_path: Path):
    """测试递归加载目录"""
    (tmp_path / "game1").mkdir()
    (tmp_path / "game1" / "doc1.md").write_text("# Doc1\n", encoding="utf-8")
    (tmp_path / "game1" / "doc2.md").write_text("# Doc2\n", encoding="utf-8")

    docs = load_markdown_dir(tmp_path)
    assert len(docs) == 2
    games = {d.metadata["game"] for d in docs}
    assert games == {"game1"}


def test_split_document_short():
    """测试短文档切分（不切）"""
    doc = Document(content="# 标题\n\n这是正文。", source="test.md", metadata={})
    chunks = split_document(doc, chunk_size=500, chunk_overlap=50, doc_id="d1")
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "d1#0000"
    assert chunks[0].doc_id == "d1"


def test_split_document_long():
    """测试长文档切分（按长度切）"""
    long_text = "这是一段测试文本。" * 100  # ~900 字符
    doc = Document(content=f"# 标题\n\n{long_text}", source="test.md", metadata={})
    chunks = split_document(doc, chunk_size=200, chunk_overlap=20, doc_id="d1")
    assert len(chunks) > 1
    # 每块不超过 chunk_size
    for c in chunks:
        assert len(c.content) <= 250  # 允许少量超出


def test_split_documents_batch():
    """批量切分"""
    docs = [
        Document(content="# A\n\nA 内容", source="a.md", metadata={}),
        Document(content="# B\n\nB 内容", source="b.md", metadata={}),
    ]
    chunks = split_documents(docs, chunk_size=500, chunk_overlap=50)
    assert len(chunks) == 2
    doc_ids = {c.doc_id for c in chunks}
    assert len(doc_ids) == 2  # 不同文档 ID


def test_make_doc_id_deterministic():
    """doc_id 由 source + 内容哈希确定"""
    id1 = make_doc_id("hello", "a.md")
    id2 = make_doc_id("hello", "a.md")
    id3 = make_doc_id("hello", "b.md")
    assert id1 == id2
    assert id1 != id3