"""米游社真实数据 driver（requests 实现，绕开 Scrapy 调度问题）。

用法：
    python scripts/crawl_mihoyo_requests.py --game genshin --max-pages 2

输出：data/raw/jsonl/{source}/{game}.jsonl
  - 复用 src.crawlers.spiders.mihoyo_spider 的 structured_content → Markdown 转换
  - 写到数据湖统一 schema（doc_id/source/game/title/.../clean_text）

为什么不用 Scrapy：
- Scrapy 2.19 + scrapy-fingerprint 插件在 Windows 下异步 reactor 调度有问题
- 直接 requests 同步拉数据更稳定，适合 API 简单场景
- 后续如果想恢复 Scrapy 版本，可以从 src.crawlers.spiders.mihoyo_spider 启用
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.crawlers.spiders.mihoyo_spider import MIHOYO_GAMES, _structured_to_markdown

BASE_API = "https://bbs-api.miyoushe.com"
BASE_WEB = "https://www.miyoushe.com"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "x-rpc-client_type": "4",
    "x-rpc-app_version": "2.40.0",
}


def _make_doc_id(source: str, game: str, post_id: str) -> str:
    """生成稳定的 doc_id。"""
    raw = f"{source}_{game}_{post_id}"
    h = hashlib.sha1(raw.encode()).hexdigest()[:10]
    return f"{source}_{game}_{post_id}_{h}"


def fetch_list_page(game: str, page: int, last_id: str = "") -> list[dict]:
    """拉一页论坛列表（20 条/页）。

    Args:
        game: 游戏 ID（genshin / honkai_star_rail / honkai3 / zenless）
        page: 页码（仅用于日志，不参与 cursor）
        last_id: 上一页最后一条 post_id，用于翻页 cursor
    """
    cfg = MIHOYO_GAMES[game]
    headers = {**DEFAULT_HEADERS, "Referer": f"{BASE_WEB}/{cfg['url_prefix']}/"}
    url = (
        f"{BASE_API}/post/api/getForumPostList"
        f"?forum_id={cfg['forum_id']}&page_size=20&sort_type=1"
    )
    if last_id:
        url += f"&last_id={last_id}"
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("retcode") != 0:
        print(f"[WARN] list retcode={data.get('retcode')} msg={data.get('message')}")
        return []
    return data.get("data", {}).get("list", [])


def fetch_post_detail(post_id: str, game: str) -> dict | None:
    """拉单帖详情 + 解析成数据湖 schema。"""
    cfg = MIHOYO_GAMES[game]
    headers = {**DEFAULT_HEADERS, "Referer": f"{BASE_WEB}/{cfg['url_prefix']}/"}
    url = f"{BASE_API}/post/api/getPostFull?post_id={post_id}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        print(f"  [ERR] detail {post_id}: {type(exc).__name__}: {exc}")
        return None

    if data.get("retcode") != 0:
        print(f"  [SKIP] detail {post_id} retcode={data.get('retcode')}")
        return None

    inner = data.get("data", {}).get("post") or {}
    post = inner.get("post") or {}
    user = inner.get("user") or {}
    stat = inner.get("stat") or {}

    structured = post.get("structured_content") or post.get("content") or ""
    body_md = _structured_to_markdown(structured)
    if len(body_md) < 50:
        return None

    pid = post.get("post_id") or post_id
    title = (post.get("subject") or "").strip()
    publish_ts = post.get("created_at")
    publish_date = (
        post.get("reply_time")
        or (datetime.fromtimestamp(int(publish_ts), tz=timezone.utc).isoformat() if publish_ts else None)
    )

    # 计算质量分（与 HtmlCleaningPipeline 一致）
    word_count = len(body_md)
    if word_count < 200:
        quality = 0.3
    elif word_count > 50000:
        quality = 0.5
    else:
        quality = min(1.0, 0.5 + word_count / 5000)
    quality_score = round(quality, 3)

    return {
        "doc_id": _make_doc_id("mihoyo", game, pid),
        "source": "mihoyo",
        "game": game,
        "url": f"{BASE_WEB}/{cfg['url_prefix']}/article/{pid}",
        "title": title,
        "author": user.get("nickname") if user else None,
        "publish_date": publish_date,
        "language": "zh",
        "clean_text": body_md,
        "word_count": word_count,
        "quality_score": quality_score,
        "metadata": {
            "post_id": pid,
            "view_num": stat.get("view_num", 0),
            "reply_num": stat.get("reply_num", 0),
            "like_num": stat.get("like_num", 0),
            "is_official": bool(post.get("post_status", {}).get("is_official")),
            "is_good": bool(post.get("post_status", {}).get("is_good")),
        },
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="米游社真实数据 driver (requests 实现)")
    parser.add_argument("--game", default="genshin", choices=list(MIHOYO_GAMES.keys()))
    parser.add_argument("--max-pages", type=int, default=3, help="翻页上限")
    parser.add_argument("--max-articles", type=int, default=30, help="抓取文章上限")
    args = parser.parse_args()

    print(f"=== 米游社 requests driver ===")
    print(f"游戏: {args.game} (forum_id={MIHOYO_GAMES[args.game]['forum_id']})")
    print(f"最大页: {args.max_pages}, 最大文章: {args.max_articles}")
    print()

    out_dir = PROJECT_ROOT / "data" / "raw" / "jsonl" / "mihoyo"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.game}.jsonl"

    seen: set[str] = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                seen.add(rec.get("doc_id", ""))
            except Exception:
                pass

    saved = 0
    scanned = 0
    last_post_id = ""
    for page in range(1, args.max_pages + 1):
        items = fetch_list_page(args.game, page, last_id=last_post_id)
        if not items:
            print(f"page {page}: 0 items, stop")
            break
        print(f"page {page}: got {len(items)} items")

        for it in items:
            if saved >= args.max_articles:
                break
            scanned += 1
            post = it.get("post") or {}
            pid = post.get("post_id")
            if not pid:
                continue
            if post.get("view_type") in (2, 4):
                continue  # 跳过纯视频帖

            doc = fetch_post_detail(pid, args.game)
            if not doc:
                continue
            if doc["doc_id"] in seen:
                continue
            seen.add(doc["doc_id"])

            with open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            saved += 1
            print(f"  [OK] {doc['doc_id'][:30]} title={doc['title'][:30]}")

        if items:
            last_post_id = items[-1].get("post", {}).get("post_id", "")
        time.sleep(1.5)

    print(f"\n扫描 {scanned} 篇 / 入库 {saved} 篇 → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
