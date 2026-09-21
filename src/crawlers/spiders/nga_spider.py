"""NGA 玩家社区 Spider - 爬取 NGA 精华攻略帖。

数据源：https://bbs.nga.cn/
URL 模式：
  - 版块列表: /thread.php?fid={fid}&order_by=postdatedesc
  - 精华: /thread.php?fid={fid}&order_by=postdatedesc&filter=type&type=4
  - 帖子详情: /read.php?tid={tid}

游戏版块 fid：
  - 阴阳师: fid=601
  - 原神: fid=619
  - 永劫无间: fid=672
  - 明日方舟: fid=741

反爬：
  - 公开浏览无登录态可看
  - IP 频率限制：< 60 req/min
  - 带 UA + 必要 Referer
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import scrapy

from src.crawlers.items import GameDocumentItem


# 游戏 → 版块 fid 配置
NGA_GAMES = {
    "onmyoji": {"fid": 601, "name": "阴阳师"},
    "genshin": {"fid": 619, "name": "原神"},
    "yjwj": {"fid": 672, "name": "永劫无间"},
    "arknights": {"fid": 741, "name": "明日方舟"},
}


class NgaSpider(scrapy.Spider):
    """NGA 论坛通用爬虫。

    Args:
        game: 游戏 ID（onmyoji / genshin / yjwj / arknights）
        mode: 'latest' (最新) / 'essence' (精华, type=4)
        max_pages: 翻页上限
        max_articles: 文章上限
    """

    name = "nga"

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": False,  # POC
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
            "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        },
    }

    BASE_URL = "https://bbs.nga.cn"

    def __init__(
        self,
        game: str = "onmyoji",
        mode: str = "essence",
        max_pages: int = 5,
        max_articles: int = 100,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        cfg = NGA_GAMES.get(game)
        if cfg is None:
            raise ValueError(
                f"Unknown game '{game}'. "
                f"Available: {list(NGA_GAMES.keys())}"
            )
        if mode not in ("latest", "essence"):
            raise ValueError(f"mode must be 'latest' or 'essence', got {mode!r}")
        self.game = game
        self.fid = cfg["fid"]
        self.game_name = cfg["name"]
        self.mode = mode
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
            "Referer": referer or f"{self.BASE_URL}/thread.php?fid={self.fid}",
        }

    def _list_url(self, page: int) -> str:
        """构造列表 URL。"""
        base = f"{self.BASE_URL}/thread.php?fid={self.fid}&order_by=postdatedesc"
        if self.mode == "essence":
            base += "&filter=type&type=4"
        if page > 1:
            base += f"&page={page}"
        return base

    def start_requests(self):
        yield scrapy.Request(
            self._list_url(1),
            headers=self._headers(),
            callback=self.parse_list,
            meta={"page": 1},
        )

    def parse_list(self, response: Any) -> Any:
        """列表页：提取 tid 列表 + 翻页。"""
        # NGA 帖子链接：/read.php?tid={tid} 或 /read.php?{tid}
        hrefs = response.css('a[href*="read.php"]::attr(href)').getall()
        tids = set()
        for href in hrefs:
            m = re.search(r"(?:read\.php\?)?(?:tid=|)(\d+)", href)
            if m:
                tids.add(m.group(1))

        self.logger.info(
            f"NGA fid={self.fid} page={response.meta['page']} "
            f"found {len(tids)} tids"
        )

        for tid in tids:
            if self.article_count >= self.max_articles:
                self.logger.info(f"Hit max_articles={self.max_articles}")
                return
            self.article_count += 1
            detail_url = f"{self.BASE_URL}/read.php?tid={tid}"
            yield scrapy.Request(
                detail_url,
                headers=self._headers(referer=response.url),
                callback=self.parse_post,
                meta={"tid": tid},
            )

        # 翻页
        next_page = response.meta["page"] + 1
        if next_page <= self.max_pages and len(tids) >= 5:
            yield scrapy.Request(
                self._list_url(next_page),
                headers=self._headers(),
                callback=self.parse_list,
                meta={"page": next_page},
            )

    def parse_post(self, response: Any) -> Any:
        """详情页：NGA 帖子解析。

        NGA 页面结构：
        - 标题：h1 / .thread-title / .topic-title
        - 作者：.author / .postauthor / a[href*="space.php?uid"]
        - 时间：.postDate / .post-date / span[data-role="postDate"]
        - 正文：#postcontent0 / .postcontent / [id^=postcontent]
        """
        # 标题
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css(".thread-title::text").get(default="").strip()
        if not title:
            title = response.css(".topic-title::text").get(default="").strip()
        if not title:
            title = response.css('meta[property="og:title"]::attr(content)').get(default="").strip()

        # 作者
        author = ""
        # 找第一个 .postauthor 内的 username
        author_node = response.css(".postauthor .author-name, .postauthor a, .author a")
        if author_node:
            author = author_node.css("::text").get(default="").strip()
        if not author:
            author = response.css('a[href*="space.php?uid"]::text').get(default="").strip()

        # 发布时间
        publish_date = response.css(".postDate::text").get(default="").strip()
        if not publish_date:
            publish_date = response.css('span[data-role="postDate"]::text').get(default="").strip()

        # 正文：第一个 postcontent（楼主）
        # 多种结构兼容
        content_html = (
            response.css("#postcontent0").get()
            or response.css('[id^="postcontent"]').get()  # 楼主第一个
            or response.css(".postcontent").get()
        )
        if not content_html:
            content_html = response.text

        if not content_html or len(content_html.strip()) < 50:
            self.logger.warning(f"Content too short tid={response.meta['tid']}")
            return

        yield GameDocumentItem(
            source="nga",
            game=self.game,
            url=response.url,
            title=title,
            raw_html=content_html,
            author=author or None,
            publish_date=publish_date or None,
            language="zh",
        )
