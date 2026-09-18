"""递归文本切分器 — 按 Markdown 标题 + 长度切分

策略：
1. 先按 Markdown 标题（# / ## / ###）切分
2. 单个块超过 chunk_size 时按段落切
3. 单段超过 chunk_size 时按句子切
4. 相邻块保留 overlap 字符重叠

面试可讲的点：
- 为什么不简单按字符数切？→ Markdown 有结构，标题切分能保留语义
- 为什么需要 overlap？→ 防止关键信息被切到边界
"""

from __future__ import annotations

import re
import uuid
from typing import List

from ..config import settings
from ..schemas import Chunk, Document


# 匹配 Markdown 标题（# ## ###）
HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _split_by_headers(content: str) -> list[dict]:
    """按 Markdown 标题切分，保留标题作为段落前缀"""
    matches = list(HEADER_RE.finditer(content))
    if not matches:
        return [{"header": "", "body": content.strip()}]

    sections = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        header = match.group(0).strip()
        body = content[start:end].strip()

        if body:
            sections.append({"header": header, "body": body})

    # 处理头部（第一个标题前的内容）
    if matches[0].start() > 0:
        prefix = content[:matches[0].start()].strip()
        if prefix:
            sections.insert(0, {"header": "", "body": prefix})

    return sections


def _split_long_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """把超长文本切成多块（保留 overlap）"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        chunks.append(chunk_text)
        if end >= len(text):
            break
        # 下次起点向前回退 overlap
        start = end - overlap
    return chunks


def split_document(
    doc: Document,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    doc_id: str = "",
) -> List[Chunk]:
    """
    切分单个 Document 为 Chunk 列表

    Args:
        doc: 输入文档
        chunk_size: 每块最大字符数（默认从 settings 读）
        chunk_overlap: 块间重叠字符数
        doc_id: 文档 ID（用于关联 chunk）

    Returns:
        Chunk 列表
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    # 1. 按标题切
    sections = _split_by_headers(doc.content)

    chunks: list[Chunk] = []
    chunk_index = 0

    for section in sections:
        body = section["body"]

        # 2. 处理超长 section
        sub_texts = _split_long_text(body, chunk_size, chunk_overlap)

        for sub_text in sub_texts:
            chunk_id = f"{doc_id}#{chunk_index:04d}" if doc_id else str(uuid.uuid4())[:12]
            chunks.append(
                Chunk(
                    content=sub_text.strip(),
                    metadata={
                        **doc.metadata,
                        "header": section["header"],
                    },
                    source=doc.source,
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1

    return chunks


def split_documents(
    docs: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Chunk]:
    """批量切分"""
    all_chunks = []
    for doc in docs:
        from ..loaders.markdown_loader import make_doc_id

        doc_id = make_doc_id(doc.content, doc.source)
        chunks = split_document(doc, chunk_size, chunk_overlap, doc_id)
        all_chunks.extend(chunks)
    return all_chunks