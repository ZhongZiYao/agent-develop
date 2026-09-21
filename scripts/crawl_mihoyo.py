"""Driver: 跑米游社 spider。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from src.crawlers import settings as cs
from src.crawlers.spiders.mihoyo_spider import MihoyoSpider


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", default="genshin",
                        choices=["genshin", "honkai_star_rail", "honkai3", "zenless"])
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--max-articles", type=int, default=100)
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    settings = Settings()
    for attr in dir(cs):
        if attr.isupper() and not attr.startswith("_"):
            val = getattr(cs, attr)
            if not callable(val):
                settings.set(attr, val, priority="project")

    settings.set("CLOSESPIDER_PAGECOUNT", args.max_articles + 20, priority="cmdline")
    settings.set("ROBOTSTXT_OBEY", False, priority="cmdline")
    settings.set("DOWNLOAD_HANDLERS", {
        "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
    }, priority="cmdline")

    mw = dict(settings.get("DOWNLOADER_MIDDLEWARES", {}))
    mw["scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware"] = None
    settings.set("DOWNLOADER_MIDDLEWARES", mw, priority="cmdline")

    print(f"=== 米游社爬虫 ===")
    print(f"游戏: {args.game}")
    print(f"最大页数: {args.max_pages}")
    print(f"最大文章: {args.max_articles}")
    print()

    process = CrawlerProcess(settings)
    process.crawl(
        MihoyoSpider,
        game=args.game,
        max_pages=args.max_pages,
        max_articles=args.max_articles,
    )
    process.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
