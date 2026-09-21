"""Unit tests for src.crawlers.spiders.mihoyo_spider."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.crawlers.spiders.mihoyo_spider import (
    MIHOYO_GAMES,
    MihoyoSpider,
    _structured_to_markdown,
)


class TestStructuredToMarkdown:
    def test_empty(self):
        assert _structured_to_markdown("") == ""
        assert _structured_to_markdown(None) == ""

    def test_plain_text(self):
        sc = json.dumps([{"insert": "Hello world\n"}], ensure_ascii=False)
        assert _structured_to_markdown(sc) == "Hello world"

    def test_multi_inserts(self):
        sc = json.dumps(
            [
                {"insert": "第一段文字。"},
                {"insert": "\n第二段。"},
            ],
            ensure_ascii=False,
        )
        out = _structured_to_markdown(sc)
        assert "第一段文字" in out
        assert "第二段" in out

    def test_image_insert(self):
        sc = json.dumps(
            [
                {"insert": "看图："},
                {"insert": {"image": "https://example.com/x.jpg"}},
                {"insert": "\n完成。"},
            ],
            ensure_ascii=False,
        )
        out = _structured_to_markdown(sc)
        assert "![image]" in out
        assert "https://example.com/x.jpg" in out

    def test_extra_newlines_collapsed(self):
        sc = json.dumps([{"insert": "a\n\n\n\n\nb"}], ensure_ascii=False)
        out = _structured_to_markdown(sc)
        assert "\n\n\n" not in out

    def test_invalid_json_returns_raw(self):
        # 失败时不抛异常，原样返回
        assert _structured_to_markdown("not json") == "not json"


class TestGamesConfig:
    def test_required_games(self):
        for k in ("genshin", "honkai_star_rail", "honkai3", "zenless"):
            assert k in MIHOYO_GAMES

    def test_config_fields(self):
        for info in MIHOYO_GAMES.values():
            assert {"gid", "forum_id", "name", "url_prefix"}.issubset(info)

    def test_genshin_fid_is_new(self):
        # 新接口 forum_id=26（原神），不是旧 bbs.mihoyo.com 的 43
        assert MIHOYO_GAMES["genshin"]["forum_id"] == 26


class TestInit:
    def test_unknown_game(self):
        with pytest.raises(ValueError, match="Unknown game"):
            MihoyoSpider(game="not_real")

    def test_genshin(self):
        sp = MihoyoSpider(game="genshin")
        assert sp.gid == 2
        assert sp.fid == 26
        assert sp.url_prefix == "ys"


class TestHeaders:
    def test_default_referer(self):
        sp = MihoyoSpider(game="genshin")
        h = sp._headers()
        assert "miyoushe.com/ys/" in h["Referer"]
        assert "Chrome" in h["User-Agent"]
        assert h["Accept"].startswith("application/json")

    def test_custom_referer(self):
        sp = MihoyoSpider(game="genshin")
        h = sp._headers(referer="https://www.miyoushe.com/ys/article/123")
        assert "article/123" in h["Referer"]


class TestParseList:
    def _list_resp(self, post_ids, last_post_id=""):
        body = {
            "retcode": 0,
            "message": "OK",
            "data": {
                "list": [
                    {
                        "post": {
                            "post_id": pid,
                            "subject": f"title-{pid}",
                            "view_type": 1,
                        },
                        "user": {"nickname": "u"},
                        "stat": {"view_num": 1, "reply_num": 0, "like_num": 0},
                    }
                    for pid in post_ids
                ],
            },
        }
        resp = MagicMock()
        resp.text = json.dumps(body, ensure_ascii=False)
        resp.url = "https://bbs-api.miyoushe.com/post/api/getForumPostList?forum_id=26"
        resp.meta = {"page": 1}
        return resp

    def test_yields_detail_per_post(self):
        sp = MihoyoSpider(game="genshin", max_pages=1, max_articles=10)
        resp = self._list_resp(["1001", "1002", "1003"])
        results = list(sp.parse_list(resp))
        detail = [r for r in results if "getPostFull" in r.url]
        assert len(detail) == 3
        assert detail[0].url.endswith("post_id=1001")
        assert detail[0].meta["pid"] == "1001"

    def test_max_articles_stops(self):
        sp = MihoyoSpider(game="genshin", max_pages=1, max_articles=2)
        resp = self._list_resp(["1", "2", "3", "4"])
        results = list(sp.parse_list(resp))
        detail = [r for r in results if "getPostFull" in r.url]
        assert len(detail) == 2

    def test_video_posts_skipped(self):
        sp = MihoyoSpider(game="genshin", max_pages=1, max_articles=10)
        body = {
            "retcode": 0,
            "message": "OK",
            "data": {
                "list": [
                    {"post": {"post_id": "1", "subject": "normal", "view_type": 1}, "user": {}, "stat": {}},
                    {"post": {"post_id": "2", "subject": "video", "view_type": 2}, "user": {}, "stat": {}},
                    {"post": {"post_id": "3", "subject": "image", "view_type": 4}, "user": {}, "stat": {}},
                ],
            },
        }
        resp = MagicMock()
        resp.text = json.dumps(body)
        resp.url = "https://bbs-api.miyoushe.com/post/api/getForumPostList"
        resp.meta = {"page": 1}
        results = list(sp.parse_list(resp))
        pids = [r.meta["pid"] for r in results if "getPostFull" in r.url]
        # 视频类(view_type=2/4)被跳过
        assert pids == ["1"]

    def test_non_zero_retcode_logs_noop(self):
        sp = MihoyoSpider(game="genshin")
        resp = MagicMock()
        resp.text = json.dumps({"retcode": -1, "message": "error"})
        resp.meta = {"page": 1}
        assert list(sp.parse_list(resp)) == []

    def test_invalid_json_logs_noop(self):
        sp = MihoyoSpider(game="genshin")
        resp = MagicMock()
        resp.text = "not json"
        resp.meta = {"page": 1}
        assert list(sp.parse_list(resp)) == []


class TestParseArticle:
    def _detail_resp(self, pid="12345", subject="攻略", structured=None, user=None, stat=None):
        body = {
            "retcode": 0,
            "message": "OK",
            "data": {
                "post": {
                    "post": {
                        "post_id": pid,
                        "subject": subject,
                        "created_at": 1789982404,
                        "reply_time": "2026-09-21 17:48:13",
                        "structured_content": structured or json.dumps(
                            [{"insert": "A" * 200}], ensure_ascii=False
                        ),
                        "view_type": 1,
                    },
                    "user": user or {"nickname": "作者"},
                    "stat": stat or {"view_num": 100, "reply_num": 5, "like_num": 10},
                },
            },
        }
        resp = MagicMock()
        resp.text = json.dumps(body, ensure_ascii=False)
        resp.url = "https://bbs-api.miyoushe.com/post/api/getPostFull?post_id=" + pid
        resp.meta = {"pid": pid, "list_subject": subject}
        return resp

    def test_success(self):
        sp = MihoyoSpider(game="genshin")
        resp = self._detail_resp(pid="777", subject="原神 4.0 攻略")
        items = list(sp.parse_article(resp))
        assert len(items) == 1
        item = items[0]
        assert item["source"] == "mihoyo"
        assert item["game"] == "genshin"
        assert item["url"].endswith("/ys/article/777")
        assert item["title"] == "原神 4.0 攻略"
        assert item["author"] == "作者"
        assert item["publish_date"] == "2026-09-21 17:48:13"

    def test_structured_to_markdown(self):
        sp = MihoyoSpider(game="genshin")
        # 内容需 > 50 字符才不被过滤
        sc = json.dumps(
            [
                {"insert": "看图："},
                {"insert": {"image": "https://example.com/x.jpg"}},
                {"insert": " 这里是详细的正文段落，包含足够多的字符以通过长度阈值过滤。"},
            ],
            ensure_ascii=False,
        )
        resp = self._detail_resp(structured=sc)
        items = list(sp.parse_article(resp))
        assert "![image]" in items[0]["raw_html"]
        assert "这里是详细" in items[0]["raw_html"]

    def test_short_content_dropped(self):
        sp = MihoyoSpider(game="genshin")
        resp = self._detail_resp(structured=json.dumps([{"insert": "hi"}]))
        items = list(sp.parse_article(resp))
        assert items == []

    def test_non_zero_retcode_logs_noop(self):
        sp = MihoyoSpider(game="genshin")
        resp = MagicMock()
        resp.text = json.dumps({"retcode": -1, "message": "err"})
        resp.meta = {"pid": "1"}
        assert list(sp.parse_article(resp)) == []

    def test_invalid_json_logs_noop(self):
        sp = MihoyoSpider(game="genshin")
        resp = MagicMock()
        resp.text = "broken"
        resp.meta = {"pid": "1"}
        assert list(sp.parse_article(resp)) == []
