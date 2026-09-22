"""PDF 切分器 — 按页 + 段落切分（理财公告/说明书专用）

特点：
1. PyMuPDF 已经按 `[Page N]` 分好页边界
2. 每个页面按段落切（双换行）
3. 超长段落按字符长度递归切
4. 保留产品/事项上下文（从 metadata 复制到每个 chunk）
5. 表格行不被强行切开（按行边界对齐）

面试可讲：
- 为什么按页切？→ 金融公告每页通常是一个独立事项
- 为什么不过度切？→ LLM 上下文窗口有限，但金融术语上下文强
"""

from __future__ import annotations

import re
import uuid
from typing import List

from ..config import settings
from ..schemas import Chunk, Document


# 页边界标记（PyMuPDF 在 _extract_text_pymupdf 中已加）
PAGE_BOUNDARY_RE = re.compile(r"\[Page (\d+)\]")


def _split_by_pages(content: str) -> list[dict]:
    """按 [Page N] 切分"""
    matches = list(PAGE_BOUNDARY_RE.finditer(content))
    if not matches:
        return [{"page": 0, "text": content.strip()}]

    pages = []
    for i, m in enumerate(matches):
        start = m.end()  # 跳过 [Page N] 标记本身
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        page_num = int(m.group(1))
        text = content[start:end].strip()
        if text:
            pages.append({"page": page_num, "text": text})
    return pages


def _split_by_paragraphs(page_text: str) -> list[str]:
    """按段落切（双换行）"""
    paras = re.split(r"\n\s*\n", page_text)
    return [p.strip() for p in paras if p.strip()]


def _split_long_paragraph(text: str, chunk_size: int, overlap: int) -> list[str]:
    """超长段落按句子边界切"""
    if len(text) <= chunk_size:
        return [text]

    # 优先按中文句末标点切
    sentence_pattern = re.compile(r"([。！？；\n])")
    sentences = sentence_pattern.split(text)
    # split 带捕获组: [sent, delim, sent, delim, ...]
    pairs = []
    for i in range(0, len(sentences) - 1, 2):
        s = sentences[i]
        d = sentences[i + 1] if i + 1 < len(sentences) else ""
        pairs.append(s + d)

    # 拼装到不超过 chunk_size
    chunks = []
    current = ""
    for s in pairs:
        if len(current) + len(s) <= chunk_size:
            current += s
        else:
            if current:
                chunks.append(current)
            # 当前句超长则硬切
            if len(s) > chunk_size:
                for j in range(0, len(s), chunk_size - overlap):
                    chunks.append(s[j : j + chunk_size])
                current = ""
            else:
                current = s
    if current:
        chunks.append(current)

    return chunks


def split_pdf_document(
    doc: Document,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    doc_id: str = "",
) -> List[Chunk]:
    """切分 PDF Document 为 Chunk 列表。

    Args:
        doc: 输入 PDF 文档（content 含 [Page N] 标记）
        chunk_size: 每块最大字符数
        chunk_overlap: 块间重叠字符数
        doc_id: 文档 ID

    Returns:
        Chunk 列表
    """
    chunk_size = chunk_size or settings.pdf_chunk_size
    chunk_overlap = chunk_overlap or settings.pdf_chunk_overlap

    pages = _split_by_pages(doc.content)
    chunks: list[Chunk] = []
    chunk_index = 0

    for page_info in pages:
        page_num = page_info["page"]
        page_text = page_info["text"]

        # 按段落切
        paragraphs = _split_by_paragraphs(page_text)

        # 拼装段落直到 chunk_size
        buffer = ""
        for para in paragraphs:
            # 单段超长则递归切
            if len(para) > chunk_size:
                # 先 flush buffer
                if buffer:
                    chunk_id = f"{doc_id}#{chunk_index:04d}" if doc_id else str(uuid.uuid4())[:12]
                    chunks.append(_make_chunk(buffer, doc, doc_id, chunk_id, chunk_index, page_num))
                    chunk_index += 1
                    buffer = ""
                # 切长段
                for sub in _split_long_paragraph(para, chunk_size, chunk_overlap):
                    chunk_id = f"{doc_id}#{chunk_index:04d}" if doc_id else str(uuid.uuid4())[:12]
                    chunks.append(_make_chunk(sub, doc, doc_id, chunk_id, chunk_index, page_num))
                    chunk_index += 1
                continue

            # buffer 拼装
            if not buffer:
                buffer = para
            elif len(buffer) + len(para) + 2 <= chunk_size:
                buffer = buffer + "\n\n" + para
            else:
                # flush
                chunk_id = f"{doc_id}#{chunk_index:04d}" if doc_id else str(uuid.uuid4())[:12]
                chunks.append(_make_chunk(buffer, doc, doc_id, chunk_id, chunk_index, page_num))
                chunk_index += 1
                buffer = para

        # flush 剩余 buffer
        if buffer:
            chunk_id = f"{doc_id}#{chunk_index:04d}" if doc_id else str(uuid.uuid4())[:12]
            chunks.append(_make_chunk(buffer, doc, doc_id, chunk_id, chunk_index, page_num))
            chunk_index += 1

    return chunks


def _make_chunk(
    text: str,
    doc: Document,
    doc_id: str,
    chunk_id: str,
    chunk_index: int,
    page_num: int,
) -> Chunk:
    """构造 Chunk，附加 PDF 特定 metadata"""
    return Chunk(
        content=text.strip(),
        metadata={
            **doc.metadata,
            "page_num": page_num,
            "chunk_type": "pdf_segment",
        },
        source=doc.source,
        chunk_id=chunk_id,
        doc_id=doc_id,
        chunk_index=chunk_index,
    )


def split_pdf_documents(
    docs: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Chunk]:
    """批量切分"""
    all_chunks = []
    for doc in docs:
        # PDF 文档以文件路径 hash 作为 doc_id（幂等）
        import hashlib
        doc_id = doc.metadata.get("doc_id") or hashlib.sha1(
            str(doc.source).encode("utf-8")
        ).hexdigest()[:12]
        chunks = split_pdf_document(doc, chunk_size, chunk_overlap, doc_id)
        all_chunks.extend(chunks)
    return all_chunks