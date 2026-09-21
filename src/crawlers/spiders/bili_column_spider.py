"""B 站专栏 Spider - 爬取 UP 主攻略长文。

数据源：https://www.bilibili.com/read
接口：
  - 列表 API: https://api.bilibili.com/x/article/encyclopedias?cid={cid}&pn={page}
  - 详情 API: https://api.bilibili.com/x/article/view?id={aid}
  - Web 详情（fallback）: https://www.bilibili.com/read/cv{aid}

反爬：
  - 必带 Cookie: SESSDATA=xxx（任何有效 SESSDATA 都可看公开内容）
  - UA 必带 Chrome 标识
  - Referer 必带 read/cv{aid}
  - 无登录态可读公开内容（无需登录）

游戏分类 cid（来自 B 站专栏页面）：
  - 原神: cid=145
  - 崩坏:星穹铁道: cid=171
  - 明日方舟: cid=149
  - 阴阳师: cid=181
"""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

import scrapy

from src.crawlers.items import GameDocumentItem


# 游戏分类 cid 配置
BILI_CATEGORIES = {
    "genshin": {"cid": 145, "name": "原神"},
    "honkai_star_rail": {"cid": 171, "name": "崩坏:星穹铁道"},
    "arknights": {"cid": 149, "name": "明日方舟"},
    "onmyoji": {"cid": 181, "name": "阴阳师"},
}


class BiliColumnSpider(scrapy.Spider):
    """B 站专栏通用爬虫。

    Args:
        game: 游戏 ID（genshin / honkai_star_rail / arknights / onmyoji）
        cid: 专栏分类 ID（可从 BILI_CATEGORIES 自动查）
        max_pages: 翻页上限（每页 ~20 篇）
        max_articles: 抓取文章上限（防止失控）
        sessdata: B 站 SESSDATA Cookie（必填，演示用可设 .env）
    """

    name = "bili_column"

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "ROBOTSTXT_OBEY": False,  # POC
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
            "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        },  # B 站无 Cloudflare，用默认即可
    }

    BASE_API = "https://api.bilibili.com"
    BASE_WEB = "https://www.bilibili.com"

    def __init__(
        self,
        game: str = "onmyoji",
        cid: int | None = None,
        max_pages: int = 10,
        max_articles: int = 200,
        sessdata: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.game = game
        cat = BILI_CATEGORIES.get(game)
        if cat is None:
            raise ValueError(
                f"Unknown game '{game}'. "
                f"Available: {list(BILI_CATEGORIES.keys())}"
            )
        self.cid = cid if cid is not None else cat["cid"]
        self.game_name = cat["name"]
        self.max_pages = max_pages
        self.max_articles = max_articles
        self.article_count = 0

        # SESSDATA Cookie（公开内容必须带）
        self.sessdata = sessdata or ""
        self.cookies = {"SESSDATA": self.sessdata} if self.sessdata else {}

    def _headers(self, referer: str | None = None) -> dict[str, str]:
        """统一请求头。"""
        h = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        if referer:
            h["Referer"] = referer
        return h

    def start_requests(self):
        """第 1 页列表请求。"""
        url = f"{self.BASE_API}/x/article/encyclopedias?cid={self.cid}&pn=1&ps=20"
        yield scrapy.Request(
            url,
            headers=self._headers(referer=f"{self.BASE_WEB}/read"),
            cookies=self.cookies,
            callback=self.parse_list,
            meta={"page": 1},
        )

    def parse_list(self, response: Any) -> Any:
        """列表页：解析出 article_id 列表，继续翻页 + 请求详情。"""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as exc:
            self.logger.error(f"List API parse failed: {exc}")
            return

        if data.get("code") != 0:
            self.logger.warning(f"List API non-zero code: {data.get('code')} msg={data.get('message')}")
            return

        articles = data.get("data", {}).get("articles", [])
        if not articles:
            self.logger.info(f"No articles in cid={self.cid} page={response.meta['page']}")
            return

        for art in articles:
            if self.article_count >= self.max_articles:
                self.logger.info(f"Hit max_articles={self.max_articles}, stopping")
                return
            aid = art.get("id")
            if not aid:
                continue
            self.article_count += 1
            detail_url = f"{self.BASE_API}/x/article/view?id={aid}"
            yield scrapy.Request(
                detail_url,
                headers=self._headers(referer=f"{self.BASE_WEB}/read/cv{aid}"),
                cookies=self.cookies,
                callback=self.parse_detail,
                meta={
                    "aid": aid,
                    "list_view": art.get("stats", {}).get("view", 0),
                    "list_like": art.get("stats", {}).get("like", 0),
                    "list_reply": art.get("stats", {}).get("reply", 0),
                },
            )

        # 翻下一页
        next_page = response.meta["page"] + 1
        if next_page <= self.max_pages and len(articles) >= 20:
            url = f"{self.BASE_API}/x/article/encyclopedias?cid={self.cid}&pn={next_page}&ps=20"
            yield scrapy.Request(
                url,
                headers=self._headers(referer=f"{self.BASE_WEB}/read"),
                cookies=self.cookies,
                callback=self.parse_list,
                meta={"page": next_page},
            )

    def parse_detail(self, response: Any) -> Any:
        """详情 API：JSON 返回，content.body 是 HTML 片段。"""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as exc:
            self.logger.warning(f"Detail API parse failed aid={response.meta['aid']}: {exc}")
            return

        if data.get("code") != 0:
            self.logger.warning(
                f"Detail API non-zero aid={response.meta['aid']}: "
                f"code={data.get('code')} msg={data.get('message')}"
            )
            return

        art = data.get("data", {})
        title = art.get("title", "")
        author = art.get("author", {}).get("name", "")
        publish_ts = art.get("publish_time", 0)  # Unix 秒
        publish_date = (
            self._ts_to_iso(publish_ts) if publish_ts else None
        )
        # content 是 dict 含 markdown / html 字段
        content_html = art.get("content", {}).get("html", "") or art.get("content", {}).get("markdown", "")
        if not content_html:
            self.logger.warning(f"Empty content aid={response.meta['aid']}")
            return

        # B 站 article_id → 真实 URL（cv{id}）
        aid = response.meta["aid"]
        url = f"https://www.bilibili.com/read/cv{aid}"

        yield GameDocumentItem(
            source="bili",
            game=self.game,
            url=url,
            title=title.strip(),
            raw_html=content_html,
            author=author or None,
            publish_date=publish_date,
            language="zh",
            raw_json=json.dumps({"aid": aid, **art.get("stats", {})}, ensure_ascii=False)[:1000],
        )

    @staticmethod
    def _ts_to_iso(ts: int) -> str | None:
        """Unix 秒 → ISO 8601。"""
        try:
            from datetime import datetime, timezone
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            return None
