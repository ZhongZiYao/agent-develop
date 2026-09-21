"""米游社 BBS Spider - 爬取米游社玩家攻略 + 官方公告。

数据源：https://bbs.mihoyo.com/
URL 模式：
  - 版块列表: /{game}/forum.php?forum_id={fid}
  - 帖子详情: /{game}/article/{id}
  - API 详情: /{game}/api/getPostFull?post_id={id}

游戏 fid 配置：
  - 原神: gid=2, fid=43
  - 崩坏:星穹铁道: gid=6, fid=49
  - 崩坏 3: gid=1, fid=44
  - 绝区零: gid=8, fid=58

反爬：
  - 公开浏览无登录态可看，但需带 Cookie: _ga / _gid / 18nfirst / 18nsecond
  - 频率限制：< 30 req/min
  - 用静态 HTML + 解析，避开 API 加密
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import scrapy

from src.crawlers.items import GameDocumentItem


# 游戏 → URL 前缀 + 版块 fid
MIHOYO_GAMES = {
    "genshin": {"gid": 2, "fid": 43, "name": "原神", "url_prefix": "ys"},
    "honkai_star_rail": {"gid": 6, "fid": 49, "name": "崩坏:星穹铁道", "url_prefix": "sr"},
    "honkai3": {"gid": 1, "fid": 44, "name": "崩坏3", "url_prefix": "bh3"},
    "zenless": {"gid": 8, "fid": 58, "name": "绝区零", "url_prefix": "nap"},
}


class MihoyoSpider(scrapy.Spider):
    """米游社 BBS 通用爬虫。

    Args:
        game: 游戏 ID（genshin / honkai_star_rail / honkai3 / zenless）
        max_pages: 翻页上限
        max_articles: 抓取文章上限
    """

    name = "mihoyo"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": False,  # POC
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
            "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        },
    }

    BASE_URL = "https://bbs.mihoyo.com"

    def __init__(
        self,
        game: str = "genshin",
        max_pages: int = 5,
        max_articles: int = 100,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        cfg = MIHOYO_GAMES.get(game)
        if cfg is None:
            raise ValueError(
                f"Unknown game '{game}'. "
                f"Available: {list(MIHOYO_GAMES.keys())}"
            )
        self.game = game
        self.gid = cfg["gid"]
        self.fid = cfg["fid"]
        self.game_name = cfg["name"]
        self.url_prefix = cfg["url_prefix"]
        self.max_pages = max_pages
        self.max_articles = max_articles
        self.article_count = 0

    def _headers(self, referer: str | None = None) -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": referer or f"{self.BASE_URL}/{self.url_prefix}/",
        }

    def start_requests(self):
        """第 1 页版块列表。"""
        url = f"{self.BASE_URL}/{self.url_prefix}/forum.php?forum_id={self.fid}"
        yield scrapy.Request(
            url,
            headers=self._headers(),
            callback=self.parse_list,
            meta={"page": 1},
        )

    def parse_list(self, response: Any) -> Any:
        """列表页：解析帖子链接 + 翻页。"""
        # 米游社帖子链接：/ys/article/{id}
        article_links = response.css(
            'a[href*="/article/"]::attr(href)'
        ).getall()
        article_ids = set()
        for href in article_links:
            m = re.search(r"/article/(\d+)", href)
            if m:
                article_ids.add(m.group(1))

        self.logger.info(f"Found {len(article_ids)} unique article ids on page {response.meta['page']}")

        for aid in article_ids:
            if self.article_count >= self.max_articles:
                self.logger.info(f"Hit max_articles={self.max_articles}")
                return
            self.article_count += 1
            article_url = f"{self.BASE_URL}/{self.url_prefix}/article/{aid}"
            yield scrapy.Request(
                article_url,
                headers=self._headers(referer=response.url),
                callback=self.parse_article,
                meta={"aid": aid},
            )

        # 翻页
        next_page = response.meta["page"] + 1
        if next_page <= self.max_pages and len(article_ids) >= 5:
            next_url = (
                f"{self.BASE_URL}/{self.url_prefix}/forum.php"
                f"?forum_id={self.fid}&page={next_page}"
            )
            yield scrapy.Request(
                next_url,
                headers=self._headers(),
                callback=self.parse_list,
                meta={"page": next_page},
            )

    def parse_article(self, response: Any) -> Any:
        """详情页：解析标题 + 正文 + 元数据。"""
        # 米游社标题：h1 或 og:title
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css('meta[property="og:title"]::attr(content)').get(default="").strip()

        # 作者
        author = response.css(".author-name::text").get(default="").strip()
        if not author:
            author = response.css(".user-name::text").get(default="").strip()

        # 发布时间
        publish_date = response.css(".post-time::text").get(default="").strip()
        if not publish_date:
            publish_date = response.css('meta[property="article:published_time"]::attr(content)').get(default="").strip()

        # 正文：米游社正文容器 .post-content 或 #ContentCn
        content_html = response.css("div.post-content").get()
        if not content_html:
            content_html = response.css("#ContentCn").get()
        if not content_html:
            content_html = response.css(".article-content").get()
        if not content_html:
            content_html = response.text

        if not content_html or len(content_html.strip()) < 50:
            self.logger.warning(f"Content too short aid={response.meta['aid']}")
            return

        yield GameDocumentItem(
            source="mihoyo",
            game=self.game,
            url=response.url,
            title=title,
            raw_html=content_html,
            author=author or None,
            publish_date=publish_date or None,
            language="zh",
        )
