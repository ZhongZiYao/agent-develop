"""Scrapy Pipelines - 数据清洗、转换、落盘。

Pipeline 顺序（settings.py 定义）：
1. DuplicateFilterPipeline (100)   内存去重 + 持久化去重
2. HtmlCleaningPipeline (200)       HTML 标准化、提取正文
3. JsonlDumpPipeline (300)          落盘到 data/raw/jsonl/{source}/{date}.jsonl
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import trafilatura
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from src.config import settings  # 复用项目配置


# ===== 全局路径配置 =====
DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
RAW_JSONL_DIR = DATA_ROOT / "raw" / "jsonl"


def _make_doc_id(url: str) -> str:
    """URL → 16 字符 doc_id（SHA1 前缀）。"""
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


class DuplicateFilterPipeline:
    """去重 Pipeline - 基于 doc_id 内存级去重。

    设计：
    - 用 set 存已见过的 doc_id
    - 跨爬虫批次持久化（写 _seen_ids.json，下次启动读）
    - 简单可靠，10w 文档内存占用 < 10MB
    """

    def __init__(self) -> None:
        self.seen_ids: set[str] = set()
        self.seen_file = RAW_JSONL_DIR / "_seen_ids.json"
        self._load_seen()

    def _load_seen(self) -> None:
        """启动时加载历史已见 ID。"""
        if self.seen_file.exists():
            try:
                self.seen_ids = set(json.loads(self.seen_file.read_text()))
            except Exception:
                self.seen_ids = set()

    def _save_seen(self) -> None:
        """爬虫关闭时持久化。"""
        self.seen_file.parent.mkdir(parents=True, exist_ok=True)
        self.seen_file.write_text(json.dumps(list(self.seen_ids), ensure_ascii=False))

    def close_spider(self, spider: Any) -> None:
        """Scrapy 关闭钩子。"""
        self._save_seen()

    def process_item(self, item: Any, spider: Any) -> Any:
        adapter = ItemAdapter(item)
        url = adapter.get("url")
        if not url:
            raise DropItem("Missing url")

        doc_id = adapter.get("doc_id") or _make_doc_id(url)
        adapter["doc_id"] = doc_id

        if doc_id in self.seen_ids:
            raise DropItem(f"Duplicate doc_id={doc_id}")

        self.seen_ids.add(doc_id)
        return item


class HtmlCleaningPipeline:
    """HTML 清洗 Pipeline - 提取正文 + 标准化字段。

    处理：
    - trafilatura 提取正文（HTML → 纯文本）
    - 编码统一（UTF-8）
    - 字段标准化（language / crawl_ts）
    - 计算 quality_score（长度 + 链接密度）
    """

    def __init__(self) -> None:
        self.min_text_length = 50  # 低于此长度视为爬取失败

    def process_item(self, item: Any, spider: Any) -> Any:
        adapter = ItemAdapter(item)
        raw_html = adapter.get("raw_html")

        if not raw_html:
            raise DropItem(f"Missing raw_html doc_id={adapter.get('doc_id')}")

        # trafilatura 提取正文（返回 Markdown）
        try:
            extracted = trafilatura.extract(
                raw_html,
                output_format="markdown",
                include_links=False,
                include_images=False,
                include_tables=True,
                favor_recall=True,
            )
        except Exception as exc:
            raise DropItem(f"trafilatura failed doc_id={adapter.get('doc_id')}: {exc}")

        if not extracted or len(extracted.strip()) < self.min_text_length:
            raise DropItem(
                f"Text too short doc_id={adapter.get('doc_id')} "
                f"len={len(extracted.strip()) if extracted else 0}"
            )

        # 写入清洗后字段
        adapter["clean_text"] = extracted.strip()
        adapter["language"] = adapter.get("language") or "zh"
        adapter["crawl_ts"] = adapter.get("crawl_ts") or datetime.now(
            tz=timezone.utc
        ).isoformat()

        # 简单质量分：基于文本长度（避免过短 / 过长）
        word_count = len(extracted)
        if word_count < 200:
            quality = 0.3
        elif word_count > 50000:
            quality = 0.5  # 可能含很多模板内容
        else:
            quality = min(1.0, 0.5 + word_count / 5000)
        adapter["quality_score"] = round(quality, 3)

        # 元数据
        adapter["word_count"] = word_count

        return item


class JsonlDumpPipeline:
    """JSONL 落盘 Pipeline - 按 source/date 分文件。

    输出路径：data/raw/jsonl/{source}/{YYYY-MM-DD}.jsonl
    每行一个 JSON 对象，方便断点续爬与流式处理。
    """

    def __init__(self) -> None:
        self.date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._buffers: dict[str, list[str]] = {}
        self._flush_threshold = 100  # 每攒够 100 行刷一次盘

    def _get_path(self, source: str) -> Path:
        path = RAW_JSONL_DIR / source / f"{self.date_str}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def process_item(self, item: Any, spider: Any) -> Any:
        adapter = ItemAdapter(item)
        source = adapter.get("source", "unknown")

        # 构建输出 dict（剔除大字段 raw_html，节省空间）
        record = {
            "doc_id": adapter.get("doc_id"),
            "source": source,
            "game": adapter.get("game"),
            "url": adapter.get("url"),
            "title": adapter.get("title"),
            "author": adapter.get("author"),
            "publish_date": adapter.get("publish_date"),
            "language": adapter.get("language"),
            "clean_text": adapter.get("clean_text"),
            "word_count": adapter.get("word_count"),
            "quality_score": adapter.get("quality_score"),
            "crawl_ts": adapter.get("crawl_ts"),
        }
        # 去掉 None 值
        record = {k: v for k, v in record.items() if v is not None}

        line = json.dumps(record, ensure_ascii=False)
        self._buffers.setdefault(source, []).append(line)

        # 攒够阈值刷盘
        if len(self._buffers[source]) >= self._flush_threshold:
            self._flush(source)

        return item

    def _flush(self, source: str) -> None:
        path = self._get_path(source)
        with path.open("a", encoding="utf-8") as f:
            f.write("\n".join(self._buffers[source]) + "\n")
        self._buffers[source] = []

    def close_spider(self, spider: Any) -> None:
        """爬虫关闭时刷盘残余。"""
        for source in self._buffers:
            if self._buffers[source]:
                self._flush(source)