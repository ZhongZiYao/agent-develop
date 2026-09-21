"""米游社 BBS Spider - 爬取米游社玩家攻略 + 官方公告。

数据源：https://www.miyoushe.com/  （原 bbs.mihoyo.com 已迁移）

公开 API（无需登录态，无需 DS 签名）：
  - 列表: https://bbs-api.miyoushe.com/post/api/getForumPostList?forum_id={fid}
  - 详情: https://bbs-api.miyoushe.com/post/api/getPostFull?post_id={id}
  - webHome 推荐: https://bbs-api-static.miyoushe.com/apihub/wapi/webHome?gids={gid}

游戏 fid 配置（原 bbs.mihoyo.com 旧 fid 已失效，新接口 forum_id 不同）：
  - 原神: gid=2, forum_id=26
  - 崩坏:星穹铁道: gid=6, forum_id=56
  - 崩坏 3: gid=1, forum_id=58
  - 绝区零: gid=8, forum_id=57

反爬：
  - 公开 API 无需登录态，无需 DS 签名
  - 必须带 Referer: https://www.miyoushe.com/{prefix}/
  - 频率限制：< 30 req/min
  - structured_content 是富文本 JSON（quill delta 风格），需转 Markdown
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import scrapy

from src.crawlers.items import GameDocumentItem


# 游戏 → gid + forum_id + URL prefix
MIHOYO_GAMES = {
    "genshin": {"gid": 2, "forum_id": 26, "name": "原神", "url_prefix": "ys"},
    "honkai_star_rail": {"gid": 6, "forum_id": 56, "name": "崩坏:星穹铁道", "url_prefix": "sr"},
    "honkai3": {"gid": 1, "forum_id": 58, "name": "崩坏3", "url_prefix": "bh3"},
    "zenless": {"gid": 8, "forum_id": 57, "name": "绝区零", "url_prefix": "nap"},
}


def _structured_to_markdown(structured: str | list[Any] | None) -> str:
    """把米游社 structured_content（quill delta JSON 字符串）转 Markdown。

    structured_content 形如:
        '[{"insert":"文本\\n"},{"insert":{"image":"url"}},{"insert":"更多文本"}]'
    """
    if not structured:
        return ""
    if isinstance(structured, str):
        try:
            ops = json.loads(structured)
        except (json.JSONDecodeError, TypeError):
            return structured
    else:
        ops = structured

    parts: list[str] = []
    for op in ops:
        ins = op.get("insert")
        if isinstance(ins, str):
            parts.append(ins)
        elif isinstance(ins, dict):
            # 图片
            if "image" in ins:
                parts.append(f"\n![image]({ins['image']})\n")
            # 链接
            elif "link" in ins:
                link_text = ins.get("text", ins["link"])
                parts.append(f"[{link_text}]({ins['link']})")
            else:
                # 其他富文本块（视频/分割线等），忽略
                pass
        # attributes（如 header）忽略——非结构化文本损失可控
    md = "".join(parts)
    # 多余空行合并
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md


def _ts_to_iso(ts: int | None) -> str | None:
    """Unix 秒 → ISO 8601（UTC）。"""
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (ValueError, OSError, TypeError):
        return None


class MihoyoSpider(scrapy.Spider):
    """米游社 BBS 通用爬虫（公开 API 方案）。

    Args:
        game: 游戏 ID（genshin / honkai_star_rail / honkai3 / zenless）
        max_pages: 翻页上限
        max_articles: 抓取文章上限
        sort_type: 排序方式（1=最新 / 2=最热）
    """

    name = "mihoyo"

    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
            "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        },
    }

    BASE_API = "https://bbs-api.miyoushe.com"
    BASE_WEB = "https://www.miyoushe.com"

    def __init__(
        self,
        game: str = "genshin",
        max_pages: int = 5,
        max_articles: int = 100,
        sort_type: int = 1,
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
        self.fid = cfg["forum_id"]
        self.game_name = cfg["name"]
        self.url_prefix = cfg["url_prefix"]
        self.max_pages = max_pages
        self.max_articles = max_articles
        self.sort_type = sort_type
        self.article_count = 0

    def _headers(self, referer: str | None = None) -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": referer or f"{self.BASE_WEB}/{self.url_prefix}/",
            "x-rpc-client_type": "4",
            "x-rpc-app_version": "2.40.0",
        }

    def start_requests(self):
        """第 1 页版块列表（API）。"""
        url = (
            f"{self.BASE_API}/post/api/getForumPostList"
            f"?forum_id={self.fid}&page_size=20&sort_type={self.sort_type}"
        )
        yield scrapy.Request(
            url,
            headers=self._headers(),
            callback=self.parse_list,
            meta={"page": 1},
        )

    def parse_list(self, response: Any) -> Any:
        """列表 API：提取 post_id + 翻页。

        Response shape:
            {"retcode": 0, "data": {"list": [{"post": {...}, "user": {...}, "stat": {...}}]}}
        """
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as exc:
            self.logger.error(f"List API parse failed: {exc}")
            return

        if data.get("retcode") != 0:
            self.logger.warning(
                f"List API non-zero retcode={data.get('retcode')} "
                f"msg={data.get('message')}"
            )
            return

        items = data.get("data", {}).get("list", [])
        if not items:
            self.logger.info(f"No posts fid={self.fid} page={response.meta['page']}")
            return

        for it in items:
            if self.article_count >= self.max_articles:
                self.logger.info(f"Hit max_articles={self.max_articles}")
                return
            post = it.get("post") or {}
            pid = post.get("post_id")
            if not pid:
                continue
            # 跳过纯视频帖（view_type=2 或 4）
            if post.get("view_type") in (2, 4):
                continue
            self.article_count += 1
            detail_url = f"{self.BASE_API}/post/api/getPostFull?post_id={pid}"
            yield scrapy.Request(
                detail_url,
                headers=self._headers(referer=response.url),
                callback=self.parse_article,
                meta={
                    "pid": pid,
                    "list_subject": post.get("subject", ""),
                    "list_reply": post.get("reply_num") or it.get("stat", {}).get("reply_num", 0),
                    "list_view": post.get("view_num") or it.get("stat", {}).get("view_num", 0),
                },
            )

        # 翻页：cursor 用最后一个 post 的 created_at（米游社分页机制）
        if response.meta["page"] < self.max_pages and len(items) >= 20:
            last_post = items[-1].get("post") or {}
            last_id = last_post.get("post_id", "")
            next_page = response.meta["page"] + 1
            next_url = (
                f"{self.BASE_API}/post/api/getForumPostList"
                f"?forum_id={self.fid}&page_size=20&sort_type={self.sort_type}"
                f"&last_id={last_id}"
            )
            yield scrapy.Request(
                next_url,
                headers=self._headers(),
                callback=self.parse_list,
                meta={"page": next_page},
            )

    def parse_article(self, response: Any) -> Any:
        """详情 API：解析标题 + 富文本 + 元数据。

        Response shape:
            {"retcode": 0, "data": {"post": {"post": {...}, "user": {...}, "stat": {...}}}}
        """
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as exc:
            self.logger.warning(f"Detail API parse failed pid={response.meta['pid']}: {exc}")
            return

        if data.get("retcode") != 0:
            self.logger.warning(
                f"Detail API non-zero pid={response.meta['pid']}: "
                f"{data.get('message')}"
            )
            return

        inner = data.get("data", {}).get("post") or {}
        post = inner.get("post") or {}
        user = inner.get("user") or {}
        stat = inner.get("stat") or {}

        pid = post.get("post_id") or response.meta["pid"]
        title = (post.get("subject") or "").strip()
        author = (user.get("nickname") or "").strip()
        publish_date = (
            post.get("reply_time")  # ISO-like 字符串，如 "2026-09-21 17:48:13"
            or _ts_to_iso(post.get("created_at"))
        )
        structured = post.get("structured_content")
        # 兜底：旧接口还有 content 字段
        if not structured:
            structured = post.get("content")

        content_md = _structured_to_markdown(structured)
        if len(content_md) < 50:
            self.logger.warning(f"Content too short pid={pid} (len={len(content_md)})")
            return

        # 真实 URL：https://www.miyoushe.com/{prefix}/article/{id}
        article_url = f"{self.BASE_WEB}/{self.url_prefix}/article/{pid}"

        yield GameDocumentItem(
            source="mihoyo",
            game=self.game,
            url=article_url,
            title=title or response.meta.get("list_subject", ""),
            raw_html=content_md,  # 已是 Markdown，直接放 raw_html 字段（pipeline 会再清洗）
            author=author or None,
            publish_date=publish_date or None,
            language="zh",
            raw_json=json.dumps(
                {
                    "view_num": stat.get("view_num", 0),
                    "reply_num": stat.get("reply_num", 0),
                    "like_num": stat.get("like_num", 0),
                    "is_official": bool(post.get("post_status", {}).get("is_official")),
                    "is_good": bool(post.get("post_status", {}).get("is_good")),
                },
                ensure_ascii=False,
            )[:1000],
        )
