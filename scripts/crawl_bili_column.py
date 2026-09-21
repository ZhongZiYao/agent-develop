"""Driver: 跑 B 站专栏 spider。

用法:
    BILI_SESSDATA=xxx python scripts/crawl_bili_column.py --game onmyoji --max-pages 5
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from src.crawlers import settings as cs
from src.crawlers.spiders.bili_column_spider import BiliColumnSpider


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", default="onmyoji", choices=["onmyoji", "genshin", "arknights", "honkai_star_rail"])
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--max-articles", type=int, default=100)
    parser.add_argument("--sessdata", default=os.getenv("BILI_SESSDATA", ""))
    args = parser.parse_args()

    # stdout 编码
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # 加载 src.crawlers.settings 配置
    settings = Settings()
    for attr in dir(cs):
        if attr.isupper() and not attr.startswith("_"):
            val = getattr(cs, attr)
            if not callable(val):
                settings.set(attr, val, priority="project")

    # CLI 覆盖
    settings.set("CLOSESPIDER_PAGECOUNT", args.max_articles + 50, priority="cmdline")
    settings.set("ROBOTSTXT_OBEY", False, priority="cmdline")
    # B 站不走 Playwright，用默认 handler
    settings.set("DOWNLOAD_HANDLERS", {
        "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
    }, priority="cmdline")
    # 关 httpcompression（避免 brotli 冲突）
    mw = dict(settings.get("DOWNLOADER_MIDDLEWARES", {}))
    mw["scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware"] = None
    settings.set("DOWNLOADER_MIDDLEWARES", mw, priority="cmdline")

    print(f"=== B 站专栏爬虫 ===")
    print(f"游戏: {args.game}")
    print(f"最大页数: {args.max_pages}")
    print(f"最大文章: {args.max_articles}")
    print(f"SESSDATA: {'已设置' if args.sessdata else '[未设置 - 仅能爬公开内容]'}")
    print()

    process = CrawlerProcess(settings)
    process.crawl(
        BiliColumnSpider,
        game=args.game,
        max_pages=args.max_pages,
        max_articles=args.max_articles,
        sessdata=args.sessdata,
    )
    process.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
