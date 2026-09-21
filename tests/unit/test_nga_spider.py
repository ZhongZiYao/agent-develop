"""Unit tests for src.crawlers.spiders.nga_spider."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.crawlers.spiders.nga_spider import NGA_GAMES, NgaSpider


class TestGamesConfig:
    def test_required_games(self):
        assert "onmyoji" in NGA_GAMES
        assert "genshin" in NGA_GAMES
        assert "yjwj" in NGA_GAMES
        assert "arknights" in NGA_GAMES

    def test_config_fields(self):
        for game, info in NGA_GAMES.items():
            assert "fid" in info
            assert "name" in info
            assert isinstance(info["fid"], int)


class TestInit:
    def test_unknown_game(self):
        with pytest.raises(ValueError, match="Unknown game"):
            NgaSpider(game="not_real")

    def test_invalid_mode(self):
        with pytest.raises(ValueError, match="mode must be"):
            NgaSpider(game="onmyoji", mode="invalid")

    def test_valid(self):
        sp = NgaSpider(game="onmyoji", mode="essence", max_pages=3, max_articles=50)
        assert sp.fid == 601
        assert sp.mode == "essence"


class TestListUrl:
    def test_essence_page_1(self):
        sp = NgaSpider(game="onmyoji", mode="essence")
        url = sp._list_url(1)
        assert "fid=601" in url
        assert "type=4" in url
        assert "page=" not in url

    def test_essence_page_2(self):
        sp = NgaSpider(game="onmyoji", mode="essence")
        url = sp._list_url(2)
        assert "page=2" in url

    def test_latest_no_filter(self):
        sp = NgaSpider(game="onmyoji", mode="latest")
        url = sp._list_url(1)
        assert "type=4" not in url


class TestHeaders:
    def test_default_referer(self):
        sp = NgaSpider(game="onmyoji")
        h = sp._headers()
        assert "bbs.nga.cn" in h["Referer"]
        assert "Chrome" in h["User-Agent"]


class TestParseList:
    def _make_sp(self, **kwargs):
        return NgaSpider(game="onmyoji", **kwargs)

    def _list_resp(self, tids):
        resp = MagicMock()
        resp.url = "https://bbs.nga.cn/thread.php?fid=601"
        resp.meta = {"page": 1}

        def css_side_effect(selector):
            node = MagicMock()
            if "read.php" in selector:
                node.getall.return_value = [f"/read.php?tid={t}" for t in tids]
            else:
                node.getall.return_value = []
            return node

        resp.css.side_effect = css_side_effect
        return resp

    def test_extract_tids(self):
        sp = self._make_sp()
        resp = self._list_resp([123456, 789012, 333444, 123456])
        results = list(sp.parse_list(resp))
        # 3 个 unique tids → 3 个详情请求
        assert sum(1 for r in results if "read.php" in r.url) == 3

    def test_max_articles_stops(self):
        sp = self._make_sp(max_articles=2, max_pages=1)
        resp = self._list_resp(list(range(10)))
        results = list(sp.parse_list(resp))
        assert sum(1 for r in results if "read.php" in r.url) == 2


class TestParsePost:
    def _make_sp(self):
        return NgaSpider(game="onmyoji")

    def _detail_resp(self, title="x", author="y", publish="2026-09-21", content="<p>x</p>" * 30):
        resp = MagicMock()
        resp.url = "https://bbs.nga.cn/read.php?tid=123456"
        resp.meta = {"tid": "123456"}

        # 用 side_effect 链式模拟 css().css()/.get() 调用
        def css_side_effect(selector):
            node = MagicMock()
            if "h1::text" in selector or "thread-title" in selector or "topic-title" in selector or "og:title" in selector:
                node.get.return_value = title
            elif "postauthor" in selector or "author a" in selector:
                # 多层 css：.postauthor .author-name ::text
                node.css.return_value.get.return_value = author
            elif "space.php?uid" in selector:
                node.get.return_value = author
            elif "postDate" in selector:
                node.get.return_value = publish
            elif "postcontent" in selector:
                node.get.return_value = content
            else:
                node.get.return_value = None
            return node

        resp.css.side_effect = css_side_effect
        return resp

    def test_success(self):
        sp = self._make_sp()
        resp = self._detail_resp()
        items = list(sp.parse_post(resp))
        assert len(items) == 1
        assert items[0]["source"] == "nga"
        assert items[0]["game"] == "onmyoji"

    def test_short_content_dropped(self):
        sp = self._make_sp()
        resp = self._detail_resp(content="too short")
        items = list(sp.parse_post(resp))
        assert items == []
