"""JSONL → 单文件 Markdown 转换器。

输入：data/raw/jsonl/{source}/{YYYY-MM-DD}.jsonl
输出：data/raw/md/{source}/{doc_id}_{title_slug}.md

为什么需要单文件 .md：
- 人读友好（项目维护 / 调试 / 数据审阅）
- RAG 切片更准（按 Markdown 章节切，保留上下文）
- 备份存档（与 JSONL 互为冗余）

设计要点：
- 不重新做 HTML→MD（clean_text 已经是 trafilatura 的 markdown 输出）
- 头部加 YAML frontmatter（doc_id / source / url / title）便于后续按 frontmatter 检索
- 文件名稳定：doc_id 是 16 字符 hash，重跑不冲突
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator

from loguru import logger

from src.config import settings


# ===== 路径 =====
DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
RAW_JSONL_DIR = DATA_ROOT / "raw" / "jsonl"
RAW_MD_DIR = DATA_ROOT / "raw" / "md"


# ===== 标题 slugify =====
def slugify_title(title: str, max_len: int = 50) -> str:
    """标题 → 文件名安全字符串。

    - 保留中文（UTF-8）
    - 空格 → _
    - 移除 / \\ : * ? " < > | 等文件系统非法字符
    - 限制长度
    - 空标题用 'untitled' 兜底
    """
    if not title or not title.strip():
        return "untitled"

    # 替换非法字符
    safe = re.sub(r'[\\/:\*\?"<>|]', "_", title)
    # 合并多个空格/下划线
    safe = re.sub(r"[\s_]+", "_", safe)
    # 移除前后下划线
    safe = safe.strip("_")
    # 长度限制
    if len(safe) > max_len:
        safe = safe[:max_len].rstrip("_")
    return safe or "untitled"


def make_md_filename(doc_id: str, title: str) -> str:
    """doc_id + 标题 → 稳定文件名。"""
    slug = slugify_title(title)
    return f"{doc_id}_{slug}.md"


def jsonl_to_markdown(record: dict[str, Any]) -> str:
    """单条 JSONL 记录 → Markdown 字符串（带 frontmatter）。"""
    # 必需字段
    doc_id = record.get("doc_id", "unknown")
    source = record.get("source", "unknown")
    url = record.get("url", "")
    title = record.get("title", "") or "Untitled"
    clean_text = record.get("clean_text", "")

    # 可选字段
    game = record.get("game", "")
    author = record.get("author", "")
    publish_date = record.get("publish_date", "")
    language = record.get("language", "zh")
    word_count = record.get("word_count", len(clean_text))
    quality_score = record.get("quality_score", 0.0)
    crawl_ts = record.get("crawl_ts", "")

    # frontmatter：标准 YAML
    fm_lines = [
        "---",
        f"doc_id: {doc_id}",
        f"source: {source}",
        f"game: {game}" if game else "",
        f"url: {url}",
        f"title: {json.dumps(title, ensure_ascii=False)}",  # 中文安全
        f"author: {json.dumps(author, ensure_ascii=False)}" if author else "",
        f"publish_date: {publish_date}" if publish_date else "",
        f"language: {language}",
        f"word_count: {word_count}",
        f"quality_score: {quality_score}",
        f"crawl_ts: {crawl_ts}",
        "---",
    ]
    # 去掉空行
    fm_lines = [line for line in fm_lines if line]
    frontmatter = "\n".join(fm_lines)

    # 正文：保留 clean_text（已是 markdown）+ 末尾来源标注
    body = f"\n{clean_text.strip()}\n\n---\n\n**来源**: [{source}]({url})  \n"
    if author:
        body += f"**作者**: {author}  \n"
    if publish_date:
        body += f"**发布日期**: {publish_date}  \n"
    body += f"**爬取时间**: {crawl_ts}\n"

    return frontmatter + body


def iter_jsonl(jsonl_path: Path) -> Iterator[dict[str, Any]]:
    """逐行读 JSONL。"""
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning(f"Invalid JSON in {jsonl_path}:{line_no}: {exc}")
                continue


def transform_file(jsonl_path: Path, md_dir: Path = RAW_MD_DIR, overwrite: bool = False) -> int:
    """单文件 JSONL → 多文件 .md。

    Args:
        jsonl_path: 输入 JSONL 路径（.../jsonl/{source}/{date}.jsonl）
        md_dir: 输出根目录
        overwrite: 已存在是否覆盖（默认跳过）

    Returns:
        写入成功的文件数
    """
    # source = jsonl_path.parent.name
    source = jsonl_path.parent.name
    out_dir = md_dir / source
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for record in iter_jsonl(jsonl_path):
        doc_id = record.get("doc_id", "unknown")
        title = record.get("title", "")
        clean_text = record.get("clean_text", "")
        if not clean_text or len(clean_text.strip()) < 50:
            logger.debug(f"Skip {doc_id} (text too short)")
            continue

        filename = make_md_filename(doc_id, title)
        out_path = out_dir / filename

        if out_path.exists() and not overwrite:
            logger.debug(f"Skip {out_path} (exists, overwrite=False)")
            continue

        md_content = jsonl_to_markdown(record)
        out_path.write_text(md_content, encoding="utf-8")
        count += 1

    logger.info(f"[{source}] {jsonl_path.name} → {count} .md files")
    return count


def transform_all(
    jsonl_dir: Path = RAW_JSONL_DIR,
    md_dir: Path = RAW_MD_DIR,
    overwrite: bool = False,
) -> dict[str, int]:
    """批量转换：递归扫描所有 JSONL 文件。

    Returns:
        {source: count}
    """
    if not jsonl_dir.exists():
        logger.warning(f"JSONL dir not found: {jsonl_dir}")
        return {}

    stats: dict[str, int] = {}
    for jsonl_path in sorted(jsonl_dir.rglob("*.jsonl")):
        if jsonl_path.name.startswith("_"):
            # 跳过 _seen_ids.json 这类元数据
            continue
        count = transform_file(jsonl_path, md_dir=md_dir, overwrite=overwrite)
        source = jsonl_path.parent.name
        stats[source] = stats.get(source, 0) + count

    return stats


if __name__ == "__main__":
    # CLI: python -m src.etl.to_markdown
    import sys
    overwrite = "--overwrite" in sys.argv
    stats = transform_all(overwrite=overwrite)
    print(f"\n转换结果：{stats}")
    print(f"输出目录：{RAW_MD_DIR.absolute()}")
