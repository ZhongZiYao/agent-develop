"""Unit tests for src.crawlers.spiders.mihoyo_spider."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.crawlers.spiders.mihoyo_spider import MIHOYO_GAMES, MihoyoSpider


class TestGamesConfig:
    def test_required_games(self):
        assert "genshin" in MIHOYO_GAMES
        assert "honkai_star_rail" in MIHOYO_GAMES
        assert "honkai3" in MIHOYO_GAMES
        assert "zenless" in MIHOYO_GAMES

    def test_config_fields(self):
        for game, info in MIHOYO_GAMES.items():
            assert "gid" in info
            assert "fid" in info
            assert "name" in info
            assert "url_prefix" in info


class TestInit:
    def test_unknown_game(self):
        with pytest.raises(ValueError, match="Unknown game"):
            MihoyoSpider(game="not_real")

    def test_genshin(self):
        sp = MihoyoSpider(game="genshin")
        assert sp.gid == 2
        assert sp.fid == 43
        assert sp.url_prefix == "ys"

    def test_star_rail(self):
        sp = MihoyoSpider(game="honkai_star_rail")
        assert sp.gid == 6
        assert sp.fid == 49
        assert sp.url_prefix == "sr"


class TestHeaders:
    def test_default_referer(self):
        sp = MihoyoSpider(game="genshin")
        h = sp._headers()
        assert "bbs.mihoyo.com/ys/" in h["Referer"]
        assert "Chrome" in h["User-Agent"]

    def test_custom_referer(self):
        sp = MihoyoSpider(game="genshin")
        h = sp._headers(referer="https://bbs.mihoyo.com/ys/article/123")
        assert "article/123" in h["Referer"]


class TestParseList:
    def _make_sp(self, game="genshin", max_articles=100):
        return MihoyoSpider(game=game, max_articles=max_articles)

    def test_extract_article_ids(self):
        sp = self._make_sp()
        resp = MagicMock()
        resp.url = "https://bbs.mihoyo.com/ys/forum.php?forum_id=43"
        resp.meta = {"page": 1}
        # 模拟页面：3 个不同 ID + 1 个重复
        resp.css.return_value.getall.return_value = [
            "/ys/article/12345",
            "/ys/article/67890",
            "/ys/article/12345",  # dup
            "/ys/article/99999",
        ]
        results = list(sp.parse_list(resp))
        # 详情请求 3 个（unique）
        assert sum(1 for r in results if "/article/" in r.url and "forum" not in r.url) == 3

    def test_max_articles_stops(self):
        sp = MihoyoSpider(game="genshin", max_articles=2, max_pages=1)
        resp = MagicMock()
        resp.url = "https://bbs.mihoyo.com/ys/forum.php?forum_id=43"
        resp.meta = {"page": 1}
        resp.css.return_value.getall.return_value = [
            f"/ys/article/{i}" for i in range(10)
        ]
        results = list(sp.parse_list(resp))
        # 只 yield 2 个详情
        assert sum(1 for r in results if "/article/" in r.url and "forum" not in r.url) == 2


class TestParseArticle:
    def _make_sp(self):
        return MihoyoSpider(game="genshin")

    def _detail_resp(self, title="x", author="y", publish="2026-09-21", content="<p>content</p>" * 20):
        resp = MagicMock()
        resp.url = "https://bbs.mihoyo.com/ys/article/12345"
        resp.meta = {"aid": "12345"}

        def css_side_effect(selector):
            ret = MagicMock()
            if "h1::text" in selector:
                ret.get.return_value = title
            elif "author-name" in selector or "user-name" in selector:
                ret.get.return_value = author
            elif "post-time" in selector or "published_time" in selector:
                ret.get.return_value = publish
            elif "post-content" in selector or "#ContentCn" in selector or "article-content" in selector:
                ret.get.return_value = content
            else:
                ret.get.return_value = None
            return ret

        resp.css.side_effect = css_side_effect
        return resp

    def test_success(self):
        sp = self._make_sp()
        resp = self._detail_resp()
        items = list(sp.parse_article(resp))
        assert len(items) == 1
        item = items[0]
        assert item["source"] == "mihoyo"
        assert item["game"] == "genshin"
        assert item["url"] == "https://bbs.mihoyo.com/ys/article/12345"

    def test_short_content_dropped(self):
        sp = self._make_sp()
        resp = self._detail_resp(content="too short")
        items = list(sp.parse_article(resp))
        assert items == []
