"""ETL Transform 层 - 清洗后 JSONL → DWD chunks + meta。

输入：data/raw/jsonl/{source}/{date}.jsonl
输出：
    data/clean/chunks.parquet     切分后的 chunks（含 doc_id / game / section_title）
    data/clean/meta.parquet       文档级元数据（标题 / 来源 / 字数 / 质量分）

实现：
    - 用 LangChain RecursiveCharacterTextSplitter 切分（沿用 Phase 1）
    - 元数据保留：source / game / url / title / word_count / quality_score
    - 跳过 quality_score 太低的文档（疑似爬取失败）
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterator

import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from tqdm import tqdm

from src.config import settings


# ===== 路径配置 =====
DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
RAW_JSONL_DIR = DATA_ROOT / "raw" / "jsonl"
CLEAN_DIR = DATA_ROOT / "clean"

# ===== 切分参数（与 Phase 1 一致）=====
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MIN_QUALITY_SCORE = 0.3  # 低于此丢弃

# ===== 章节切分正则（Markdown 标题）=====
SECTION_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def make_chunk_id(doc_id: str, chunk_index: int) -> str:
    """生成稳定 chunk_id。"""
    raw = f"{doc_id}::{chunk_index}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def detect_sections(markdown_text: str) -> list[tuple[int, str, int]]:
    """检测 Markdown 章节，返回 [(start_pos, title, level), ...]。

    用于把 chunk 关联到所属章节标题。
    """
    sections = []
    for match in SECTION_PATTERN.finditer(markdown_text):
        level = len(match.group(1))
        title = match.group(2).strip()
        sections.append((match.start(), title, level))
    return sections


def find_section_for_pos(
    pos: int, sections: list[tuple[int, str, int]]
) -> str:
    """给定字符位置，返回所属章节标题。"""
    current = "(无章节)"
    for sec_pos, sec_title, _level in sections:
        if sec_pos <= pos:
            current = sec_title
        else:
            break
    return current


def iter_raw_jsonl(raw_dir: Path | None = None) -> Iterator[dict]:
    """流式遍历所有原始 JSONL 文件。

    Args:
        raw_dir: 自定义 raw 根目录（含 jsonl/{source}/*.jsonl），
                 None 时用模块默认路径

    Yields: 单文档 dict
    """
    base = raw_dir if raw_dir is not None else RAW_JSONL_DIR
    if not base.exists():
        logger.warning(f"raw 目录不存在: {base}")
        return

    for jsonl_path in sorted(base.rglob("*.jsonl")):
        if jsonl_path.name.startswith("_"):
            continue
        logger.info(f"读取 {jsonl_path}")
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    logger.warning(f"JSON 解析失败 {jsonl_path}:{line_no}: {exc}")


def transform_documents(
    raw_dir: Path | None = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    min_quality: float = MIN_QUALITY_SCORE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """主入口：清洗 + 切分 → 返回 (chunks_df, meta_df)。

    Args:
        raw_dir: 自定义 raw 根目录（测试用），None 时用模块默认
        chunk_size: chunk 字符数上限
        chunk_overlap: 相邻 chunk 重叠字符数
        min_quality: 低于此 quality_score 的文档丢弃

    Returns:
        chunks_df: 列 = [chunk_id, doc_id, chunk_text, chunk_tokens, section_title,
                        source, game, title, url, quality_score]
        meta_df:   列 = [doc_id, source, game, title, url, author, publish_date,
                        word_count, quality_score, language, crawl_ts]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
    )

    chunks_rows: list[dict] = []
    meta_rows: list[dict] = []

    n_total = 0
    n_dropped = 0

    for doc in tqdm(iter_raw_jsonl(raw_dir), desc="Transform documents"):
        n_total += 1

        # 质量过滤
        quality = doc.get("quality_score", 0)
        if quality < min_quality:
            n_dropped += 1
            continue

        text = doc.get("clean_text", "")
        if not text or len(text) < 50:
            n_dropped += 1
            continue

        doc_id = doc["doc_id"]
        source = doc.get("source", "unknown")
        game = doc.get("game", "unknown")
        title = doc.get("title", "")
        url = doc.get("url", "")

        # 章节检测
        sections = detect_sections(text)

        # 切分
        text_chunks = splitter.split_text(text)
        for chunk_idx, chunk_text in enumerate(text_chunks):
            # 找 chunk 在原文中位置（简单启发：substring index）
            # 实际 LangChain 不返回位置，这里重新 locate
            char_pos = text.find(chunk_text[:50])
            if char_pos < 0:
                char_pos = 0
            section_title = find_section_for_pos(char_pos, sections)

            chunk_id = make_chunk_id(doc_id, chunk_idx)
            chunks_rows.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "chunk_index": chunk_idx,
                    "chunk_text": chunk_text,
                    "chunk_tokens": len(chunk_text),  # 简化：字符数
                    "section_title": section_title,
                    "source": source,
                    "game": game,
                    "title": title,
                    "url": url,
                    "quality_score": quality,
                }
            )

        meta_rows.append(
            {
                "doc_id": doc_id,
                "source": source,
                "game": game,
                "title": title,
                "url": url,
                "author": doc.get("author"),
                "publish_date": doc.get("publish_date"),
                "word_count": doc.get("word_count", len(text)),
                "quality_score": quality,
                "language": doc.get("language", "zh"),
                "crawl_ts": doc.get("crawl_ts"),
            }
        )

    logger.info(
        f"Transform 完成: total={n_total}, dropped={n_dropped}, "
        f"chunks={len(chunks_rows)}, docs={len(meta_rows)}"
    )

    chunks_df = pd.DataFrame(chunks_rows)
    meta_df = pd.DataFrame(meta_rows)
    return chunks_df, meta_df


def save_parquet(
    chunks_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    out_dir: Path = CLEAN_DIR,
) -> tuple[Path, Path]:
    """保存为 Parquet（列存压缩）。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks_path = out_dir / "chunks.parquet"
    meta_path = out_dir / "meta.parquet"

    chunks_df.to_parquet(chunks_path, engine="pyarrow", index=False)
    meta_df.to_parquet(meta_path, engine="pyarrow", index=False)

    logger.info(f"写入 {chunks_path} ({chunks_path.stat().st_size / 1e6:.1f} MB)")
    logger.info(f"写入 {meta_path} ({meta_path.stat().st_size / 1e6:.1f} MB)")
    return chunks_path, meta_path


def run() -> tuple[Path, Path]:
    """CLI 入口。"""
    chunks_df, meta_df = transform_documents()
    return save_parquet(chunks_df, meta_df)


if __name__ == "__main__":
    run()