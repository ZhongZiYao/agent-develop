"""Unit tests for src.crawlers.spiders.netease_ds_spider."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.crawlers.spiders.netease_ds_spider import NETEASE_DS_GAMES, NeteaseDsSpider


class TestGamesConfig:
    def test_required_games(self):
        assert "onmyoji" in NETEASE_DS_GAMES
        assert "yjwj" in NETEASE_DS_GAMES
        assert "dwrg" in NETEASE_DS_GAMES

    def test_onmyoji_id(self):
        assert NETEASE_DS_GAMES["onmyoji"] == "yys"


class TestInit:
    def test_unknown_game(self):
        with pytest.raises(ValueError, match="Unknown game"):
            NeteaseDsSpider(game="not_real")

    def test_valid(self):
        sp = NeteaseDsSpider(game="onmyoji", max_pages=3, max_articles=50)
        assert sp.game == "onmyoji"
        assert sp.game_id == "yys"
        assert sp.max_pages == 3


class TestHeaders:
    def test_default_referer(self):
        sp = NeteaseDsSpider(game="onmyoji")
        h = sp._headers()
        assert "ds.163.com" in h["Referer"]
        assert "Chrome" in h["User-Agent"]

    def test_custom_referer(self):
        sp = NeteaseDsSpider(game="onmyoji")
        h = sp._headers(referer="https://ds.163.com/article/123.html")
        assert "article/123" in h["Referer"]


class TestParseList:
    def _make_sp(self, **kwargs):
        return NeteaseDsSpider(game="onmyoji", **kwargs)

    def _list_resp(self, hrefs):
        resp = MagicMock()
        resp.url = "https://ds.163.com/game/yys/strategy/"
        resp.meta = {"page": 1}

        def css_se(sel):
            node = MagicMock()
            if "/article/" in sel:
                node.getall.return_value = hrefs
            else:
                node.getall.return_value = []
            return node

        resp.css.side_effect = css_se
        return resp

    def test_extract_articles(self):
        sp = self._make_sp()
        resp = self._list_resp([
            "/article/12345.html",
            "/game/yys/article/67890.html",  # 同模式
            "/article/12345.html",  # dup
        ])
        results = list(sp.parse_list(resp))
        # 2 个 unique → 2 个详情请求
        assert sum(1 for r in results if "/article/" in r.url and ".html" in r.url) == 2

    def test_max_articles_stops(self):
        sp = self._make_sp(max_articles=3, max_pages=1)
        resp = self._list_resp([f"/article/{i}.html" for i in range(10)])
        results = list(sp.parse_list(resp))
        assert sum(1 for r in results if ".html" in r.url and "strategy" not in r.url) == 3


class TestParseArticle:
    def _make_sp(self):
        return NeteaseDsSpider(game="onmyoji")

    def _detail_resp(self, title="x", author="y", publish="2026-09-21", content="<p>x</p>" * 30):
        resp = MagicMock()
        resp.url = "https://ds.163.com/article/12345.html"
        resp.meta = {"aid": "12345"}

        def css_se(sel):
            node = MagicMock()
            if "h1::text" in sel or "article-title" in sel:
                node.get.return_value = title
            elif "author-name" in sel or "user-name" in sel:
                node.get.return_value = author
            elif "article-time" in sel or "publish-time" in sel:
                node.get.return_value = publish
            elif "content" in sel or "article-body" in sel:
                node.get.return_value = content
            else:
                node.get.return_value = None
            return node

        resp.css.side_effect = css_se
        return resp

    def test_success(self):
        sp = self._make_sp()
        resp = self._detail_resp()
        items = list(sp.parse_article(resp))
        assert len(items) == 1
        item = items[0]
        assert item["source"] == "netease_ds"
        assert item["game"] == "onmyoji"

    def test_short_content_dropped(self):
        sp = self._make_sp()
        resp = self._detail_resp(content="too short")
        items = list(sp.parse_article(resp))
        assert items == []
