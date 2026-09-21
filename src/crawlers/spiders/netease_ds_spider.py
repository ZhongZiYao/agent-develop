"""网易大神 Spider - 爬取网易自家游戏攻略（阴阳师/永劫无间/第五人格/荒野行动）。

数据源：https://ds.163.com/
URL 模式：
  - 游戏专题: /game/{game_id}/
  - 攻略列表: /game/{game_id}/strategy/  (HTML 静态)
  - 攻略详情: /article/{id}.html

游戏映射（game_id 从页面提取，常见值）：
  - 阴阳师: 'yys' / 'onmyoji' / 'yys2'
  - 永劫无间: 'yjwj'
  - 第五人格: 'dwrg'
  - 荒野行动: 'hyxd'
  - 明日之后: 'mrz'
  - 倩女幽魂: 'qnyh'

反爬策略（采用降级方案，避开登录态）：
  - 走游戏专题页 HTML（公开），从中抓攻略链接
  - 不走 /api/ 加密接口
  - UA 必备 Chrome 标识
  - 频率限制：< 20 req/min
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import scrapy

from src.crawlers.items import GameDocumentItem


# 游戏 → game_id（来自 ds.163.com 页面路径）
NETEASE_DS_GAMES = {
    "onmyoji": "yys",
    "yjwj": "yjwj",          # 永劫无间
    "dwrg": "dwrg",          # 第五人格
    "hyxd": "hyxd",          # 荒野行动
    "mrz": "mrz",            # 明日之后
    "qnyh": "qnyh",          # 倩女幽魂
}


class NeteaseDsSpider(scrapy.Spider):
    """网易大神攻略爬虫（HTML 静态降级方案，无需登录态）。

    Args:
        game: 游戏 ID（onmyoji / yjwj / dwrg / hyxd / mrz / qnyh）
        max_pages: 翻页上限
        max_articles: 文章上限
    """

    name = "netease_ds"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": False,  # POC
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
            "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        },
    }

    BASE_URL = "https://ds.163.com"

    def __init__(
        self,
        game: str = "onmyoji",
        max_pages: int = 5,
        max_articles: int = 100,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        if game not in NETEASE_DS_GAMES:
            raise ValueError(
                f"Unknown game '{game}'. "
                f"Available: {list(NETEASE_DS_GAMES.keys())}"
            )
        self.game = game
        self.game_id = NETEASE_DS_GAMES[game]
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
            "Referer": referer or f"{self.BASE_URL}/",
        }

    def start_requests(self):
        """攻略列表入口。"""
        url = f"{self.BASE_URL}/game/{self.game_id}/strategy/"
        yield scrapy.Request(
            url,
            headers=self._headers(),
            callback=self.parse_list,
            meta={"page": 1},
        )

    def parse_list(self, response: Any) -> Any:
        """列表页：解析 article 链接 + 翻页。

        网易大神攻略链接模式：
          - /article/{id}.html
          - /game/{game_id}/article/{id}.html
        """
        # 抓所有 article 链接
        article_links = response.css(
            'a[href*="/article/"]::attr(href)'
        ).getall()
        article_ids = set()
        for href in article_links:
            m = re.search(r"/article/(\d+)", href)
            if m:
                article_ids.add(m.group(1))

        self.logger.info(
            f"netease_ds game={self.game} page={response.meta['page']} "
            f"found {len(article_ids)} articles"
        )

        for aid in article_ids:
            if self.article_count >= self.max_articles:
                self.logger.info(f"Hit max_articles={self.max_articles}")
                return
            self.article_count += 1
            article_url = (
                f"{self.BASE_URL}/article/{aid}.html"
            )
            yield scrapy.Request(
                article_url,
                headers=self._headers(referer=response.url),
                callback=self.parse_article,
                meta={"aid": aid},
            )

        # 翻页：网易大神常见 ?page=N 或 ?p=N
        next_page = response.meta["page"] + 1
        if next_page <= self.max_pages and len(article_ids) >= 5:
            # 尝试 page=N 模式
            next_url = f"{response.url.rstrip('/')}/?page={next_page}"
            yield scrapy.Request(
                next_url,
                headers=self._headers(),
                callback=self.parse_list,
                meta={"page": next_page},
            )

    def parse_article(self, response: Any) -> Any:
        """详情页：解析正文。

        网易大神文章页结构：
        - 标题：h1.article-title / .article-title / og:title
        - 作者：.author-name / .user-name
        - 时间：.article-time / .publish-time
        - 正文：.article-content / .article-body / #article-content
        """
        # 标题
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css(".article-title::text").get(default="").strip()
        if not title:
            title = response.css('meta[property="og:title"]::attr(content)').get(default="").strip()

        # 作者
        author = response.css(".author-name::text").get(default="").strip()
        if not author:
            author = response.css(".user-name::text").get(default="").strip()

        # 发布时间
        publish_date = response.css(".article-time::text").get(default="").strip()
        if not publish_date:
            publish_date = response.css(".publish-time::text").get(default="").strip()
        if not publish_date:
            publish_date = response.css('meta[property="article:published_time"]::attr(content)').get(default="").strip()

        # 正文容器（多选择器兜底）
        content_html = (
            response.css(".article-content").get()
            or response.css(".article-body").get()
            or response.css("#article-content").get()
            or response.css('[class*="content"]').get()
        )
        if not content_html:
            content_html = response.text

        if not content_html or len(content_html.strip()) < 50:
            self.logger.warning(f"Content too short aid={response.meta['aid']}")
            return

        yield GameDocumentItem(
            source="netease_ds",
            game=self.game,
            url=response.url,
            title=title,
            raw_html=content_html,
            author=author or None,
            publish_date=publish_date or None,
            language="zh",
        )
