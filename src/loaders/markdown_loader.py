"""Markdown Loader — 递归加载 data/raw/ 下所有 .md 文件

输出 Document 列表，metadata 含 source / game / title。
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ..schemas import Document


def _extract_title(content: str, fallback: str) -> str:
    """从 Markdown 内容提取第一个 H1 标题"""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def _extract_game(source_path: Path) -> str:
    """从文件路径推断游戏名（倒数第二级目录）"""
    # data/raw/yongjiewujian/yaodaoji_guide.md → yongjiewujian
    parts = source_path.parts
    if len(parts) >= 2:
        return parts[-2]
    return "通用"


def load_markdown_file(path: Path) -> Document:
    """加载单个 Markdown 文件"""
    content = path.read_text(encoding="utf-8")
    title = _extract_title(content, fallback=path.stem)
    game = _extract_game(path)

    return Document(
        content=content,
        metadata={
            "title": title,
            "game": game,
            "filename": path.name,
            "file_extension": path.suffix,
        },
        source=str(path.resolve()),
    )


def load_markdown_dir(dir_path: Path | str, recursive: bool = True) -> list[Document]:
    """递归加载目录下所有 .md 文件"""
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {dir_path}")

    pattern = "**/*.md" if recursive else "*.md"
    files = sorted(dir_path.glob(pattern))

    if not files:
        return []

    docs = [load_markdown_file(f) for f in files]
    return docs


def make_doc_id(content: str, source: str) -> str:
    """用 content + source 哈希生成 doc_id（用于去重和关联 chunk）"""
    raw = f"{source}::{content[:200]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]