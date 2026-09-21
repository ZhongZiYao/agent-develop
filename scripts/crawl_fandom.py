"""Run Fandom spider with proper settings — production driver.

Usage:
    cd /path/to/RAG_system
    CRAWLER_PROXY=http://127.0.0.1:7890 python scripts/crawl_fandom.py --max-pages 50
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# 把 src 加入 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from src.crawlers import settings as cs
from src.crawlers.spiders.fandom_spider import FandomSpider


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--start-url", type=str, default="https://onmyoji.fandom.com/wiki/Onmyoji_Wiki")
    args = parser.parse_args()

    # 完整加载 src.crawlers.settings 里的所有配置（包括 ITEM_PIPELINES）
    settings = Settings()
    for attr in dir(cs):
        if attr.isupper() and not attr.startswith("_"):
            val = getattr(cs, attr)
            if not callable(val):
                settings.set(attr, val, priority="project")

    # CLI 覆盖
    settings.set("CLOSESPIDER_PAGECOUNT", args.max_pages, priority="cmdline")
    settings.set("CONCURRENT_REQUESTS_PER_DOMAIN", 1, priority="cmdline")
    settings.set("DOWNLOAD_DELAY", 1.5, priority="cmdline")
    settings.set("ROBOTSTXT_OBEY", False, priority="cmdline")  # POC

    # 关 httpcompression（playwright 拿到的已经是最终渲染后的 DOM）
    mw = dict(settings.get("DOWNLOADER_MIDDLEWARES", {}))
    mw["scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware"] = None
    settings.set("DOWNLOADER_MIDDLEWARES", mw, priority="cmdline")

    print("=== Settings summary ===")
    print(f"DOWNLOAD_HANDLERS: {settings.get('DOWNLOAD_HANDLERS')}")
    print(f"ITEM_PIPELINES: {settings.get('ITEM_PIPELINES')}")
    print(f"USER_AGENT: {settings.get('USER_AGENT')}")
    print(f"CRAWLER_PROXY: {os.getenv('CRAWLER_PROXY')}")
    print()

    process = CrawlerProcess(settings)
    process.crawl(
        FandomSpider,
        start_urls=[args.start_url],
        max_pages=args.max_pages,
    )
    process.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())