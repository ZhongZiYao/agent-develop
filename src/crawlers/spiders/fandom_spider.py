"""Fandom Wiki Spider - 爬取 Fandom Wiki 上的游戏攻略页面。

目标游戏：阴阳师（onmyoji），可扩展到原神 / 明日方舟 / 王者荣耀。
URL 模式：https://{game}. fandom.com/wiki/{PageName}
"""
import os
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import scrapy

from src.crawlers.items import GameDocumentItem


class FandomSpider(scrapy.Spider):
    """Fandom Wiki 通用爬虫。

    Args:
        game: 游戏 ID（如 'onmyoji' / 'genshin' / 'arknights'）
        start_urls: 起始 URL 列表，None 时用默认入口页
        allowed_page_pattern: 允许的页面 URL 正则（过滤非攻略页）
        max_pages: 爬取页面上限（防止失控）
    """

    name = "fandom"

    # 默认配置：爬阴阳师 Wiki
    DEFAULT_GAME = "onmyoji"
    DEFAULT_BASE_URL = "https://onmyoji.fandom.com"
    DEFAULT_START_PATHS = [
        "/wiki/Onmyoji_Wiki",          # Wiki 首页
        "/wiki/Category:Characters",   # 角色列表
        "/wiki/Category:Shikigami",    # 式神列表
        "/wiki/Category:Skins",        # 皮肤列表
        "/wiki/Category:Events",       # 活动列表
        "/wiki/Category:Items",        # 道具列表
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,          # Fandom 限速更严 + Cloudflare 友好
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,  # 串行最稳（避免被 Cloudflare 弹）
    }

    def __init__(
        self,
        game: str | None = None,
        start_urls: list[str] | None = None,
        allowed_pattern: str | None = None,
        max_pages: int = 10000,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.game = game or self.DEFAULT_GAME
        self.base_url = f"https://{self.game}.fandom.com"
        self.max_pages = max_pages
        self.page_count = 0

        # 代理：Fandom 在国内被 Cloudflare 拦截，必须经过代理才能拿到 200
        self.proxy_url = os.getenv("CRAWLER_PROXY")  # e.g. "http://127.0.0.1:7890"

        # 起始 URL
        if start_urls:
            self.start_urls = start_urls
        else:
            self.start_urls = [
                urljoin(self.base_url, path)
                for path in self.DEFAULT_START_PATHS
            ]

        # 允许的页面 URL 正则（默认排除特殊页）
        self.allowed_pattern = allowed_pattern or self._build_default_pattern()

    def _build_default_pattern(self) -> str:
        """默认排除：讨论页 / 编辑页 / 用户页 / 文件页。"""
        return r"^/wiki/[^:]+$"  # 不含冒号的页面（即非特殊命名空间）

    @property
    def allowed_domains(self) -> list[str]:
        return [urlparse(self.base_url).netloc]

    def _proxy_kwargs(self) -> dict[str, Any]:
        """每个请求都带的 meta（注入代理）。"""
        if self.proxy_url:
            return {"proxy": self.proxy_url}
        return {}

    def parse(self, response: Any) -> Any:
        """入口页 / 列表页：解析出详情页 URL 继续跟进。"""
        if self.page_count >= self.max_pages:
            return

        # 提取详情页链接
        page_links = response.css("a[href*='/wiki/']::attr(href)").getall()

        for href in set(page_links):
            if self.page_count >= self.max_pages:
                break
            # 过滤非 Wiki 内容
            if not re.match(self.allowed_pattern, href.split("#")[0]):
                continue
            # 跳过 main page / 主页（一般无攻略价值）
            if "Main_Page" in href or "Special:" in href:
                continue
            # 带 Referer 头（Fandom/CDN 会校验）+ 代理 meta（爬虫注入到 download handler）
            yield response.follow(
                href,
                self.parse_page,
                priority=1,
                dont_filter=False,
                meta=self._proxy_kwargs(),
            )

    def parse_page(self, response: Any) -> Any:
        """详情页：解析正文 + 元数据。"""
        self.page_count += 1

        # 提取标题
        title = response.css("h1.page-header__title::text").get()
        if not title:
            title = response.css("title::text").get(default="").split(" - ")[0]

        # 提取正文 HTML
        content_html = response.css("div.mw-parser-output").get()
        if not content_html:
            content_html = response.css("div#mw-content-text").get()
        if not content_html:
            # 兜底：整页 body
            content_html = response.text

        # 作者 / 发布日期（Fandom 通常没明确显示，用 og:meta）
        author = response.css(
            'meta[property="article:author"]::attr(content)'
        ).get(default="")
        publish_date = response.css(
            'meta[property="article:published_time"]::attr(content)'
        ).get(default="")

        yield GameDocumentItem(
            source="fandom",
            game=self.game,
            url=response.url,
            title=(title or "").strip(),
            raw_html=content_html,
            author=author or None,
            publish_date=publish_date or None,
        )