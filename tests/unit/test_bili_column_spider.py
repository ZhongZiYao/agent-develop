"""Unit tests for src.crawlers.spiders.bili_column_spider.

覆盖：
- 初始化校验（未知 game 抛错）
- _headers 含必要字段
- 列表 API 响应解析（成功 / 失败 / 空）
- 详情 API 响应解析
- 时间戳转换
- BILI_CATEGORIES 配置完整性
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.crawlers.spiders.bili_column_spider import BILI_CATEGORIES, BiliColumnSpider


# ===== BILI_CATEGORIES =====
class TestCategories:
    def test_required_games(self):
        assert "onmyoji" in BILI_CATEGORIES
        assert "genshin" in BILI_CATEGORIES
        assert "arknights" in BILI_CATEGORIES
        assert "honkai_star_rail" in BILI_CATEGORIES

    def test_cid_is_int(self):
        for game, info in BILI_CATEGORIES.items():
            assert isinstance(info["cid"], int), f"{game} cid not int"
            assert "name" in info


# ===== Init =====
class TestInit:
    def test_unknown_game_raises(self):
        with pytest.raises(ValueError, match="Unknown game"):
            BiliColumnSpider(game="not_a_real_game")

    def test_valid_game(self):
        sp = BiliColumnSpider(game="onmyoji", max_pages=2, max_articles=10)
        assert sp.game == "onmyoji"
        assert sp.cid == 181
        assert sp.max_pages == 2
        assert sp.max_articles == 10
        assert sp.article_count == 0


# ===== Headers =====
class TestHeaders:
    def test_user_agent_present(self):
        sp = BiliColumnSpider(game="onmyoji")
        h = sp._headers()
        assert "Mozilla" in h["User-Agent"]
        assert "Chrome" in h["User-Agent"]

    def test_accept_json(self):
        sp = BiliColumnSpider(game="onmyoji")
        h = sp._headers()
        assert "application/json" in h["Accept"]

    def test_referer_added(self):
        sp = BiliColumnSpider(game="onmyoji")
        h = sp._headers(referer="https://www.bilibili.com/read/cv123")
        assert h["Referer"] == "https://www.bilibili.com/read/cv123"

    def test_no_referer_when_not_specified(self):
        sp = BiliColumnSpider(game="onmyoji")
        h = sp._headers()
        assert "Referer" not in h


# ===== Time conversion =====
class TestTsToIso:
    def test_valid_timestamp(self):
        iso = BiliColumnSpider._ts_to_iso(1700000000)
        assert iso is not None
        assert "T" in iso

    def test_zero_returns_1970_epoch(self):
        # 0 → 1970-01-01T00:00:00+00:00（合法的 Unix epoch）
        iso = BiliColumnSpider._ts_to_iso(0)
        assert iso is not None
        assert iso.startswith("1970-01-01")


# ===== List API parsing =====
class TestParseList:
    def _make_sp(self):
        return BiliColumnSpider(game="onmyoji", max_pages=2, max_articles=10)

    def _list_response(self, code=0, articles=None):
        resp = MagicMock()
        resp.text = json.dumps({
            "code": code,
            "message": "0" if code == 0 else "error",
            "data": {"articles": articles or []},
        })
        resp.meta = {"page": 1}
        return resp

    def test_empty_list_stops(self):
        sp = self._make_sp()
        resp = self._list_response(articles=[])
        results = list(sp.parse_list(resp))
        assert results == []  # 没有 yield 任何 Request

    def test_non_zero_code(self):
        sp = self._make_sp()
        resp = self._list_response(code=-101, articles=[{"id": 1}])
        results = list(sp.parse_list(resp))
        assert results == []

    def test_yields_detail_request(self):
        sp = self._make_sp()
        resp = self._list_response(articles=[{
            "id": 12345,
            "stats": {"view": 100, "like": 5, "reply": 2},
        }])
        results = list(sp.parse_list(resp))
        assert len(results) == 1
        # 第一个是详情请求
        assert "view?id=12345" in results[0].url
        assert results[0].callback == sp.parse_detail
        assert results[0].meta["aid"] == 12345

    def test_max_articles_stops(self):
        sp = BiliColumnSpider(game="onmyoji", max_articles=2, max_pages=5)
        # 5 篇 → 只 yield 2 个详情
        resp = self._list_response(articles=[{"id": i} for i in range(5)])
        results = list(sp.parse_list(resp))
        # 详情请求 2 个（max_articles=2），最后一个会跳出循环，page=1 不翻下一页
        assert sum(1 for r in results if "view?" in r.url) == 2


# ===== Detail API parsing =====
class TestParseDetail:
    def _make_sp(self):
        return BiliColumnSpider(game="onmyoji")

    def _detail_response(self, code=0, art=None):
        resp = MagicMock()
        resp.text = json.dumps({
            "code": code,
            "message": "0",
            "data": art or {},
        })
        resp.meta = {"aid": 12345}
        return resp

    def test_success(self):
        sp = self._make_sp()
        resp = self._detail_response(art={
            "title": "妖刀姬连招攻略",
            "author": {"name": "UP主老王"},
            "publish_time": 1700000000,
            "content": {
                "html": "<p>妖刀姬的连招核心是...</p>",
            },
            "stats": {"view": 1000, "like": 50},
        })
        items = list(sp.parse_detail(resp))
        assert len(items) == 1
        item = items[0]
        assert item["source"] == "bili"
        assert item["game"] == "onmyoji"
        assert item["title"] == "妖刀姬连招攻略"
        assert item["author"] == "UP主老王"
        assert "https://www.bilibili.com/read/cv12345" == item["url"]
        assert "妖刀姬的连招" in item["raw_html"]

    def test_non_zero_code(self):
        sp = self._make_sp()
        resp = self._detail_response(code=-101, art={"title": "x", "content": {"html": "<p>x</p>"}})
        assert list(sp.parse_detail(resp)) == []

    def test_empty_content(self):
        sp = self._make_sp()
        resp = self._detail_response(art={"title": "x", "content": {"html": ""}})
        assert list(sp.parse_detail(resp)) == []

    def test_markdown_fallback(self):
        """如果 html 字段为空，markdown 字段兜底。"""
        sp = self._make_sp()
        resp = self._detail_response(art={
            "title": "MD only",
            "content": {"html": "", "markdown": "# 标题\n内容"},
        })
        items = list(sp.parse_detail(resp))
        assert len(items) == 1
        assert items[0]["raw_html"] == "# 标题\n内容"
