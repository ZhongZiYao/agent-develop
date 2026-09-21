"""Playwright Download Handler - 用真浏览器绕过 Cloudflare Turnstile。

为什么用 Playwright 而不是 curl_cffi：
- Cloudflare Turnstile 是 JS Challenge，需要跑 JS 才能拿到 cf_clearance cookie
- curl_cffi 只能模拟 TLS 指纹，无法执行 JS
- Playwright = 真 Chromium = 通过 Turnstile 的「我是人」验证
- 后续请求复用同一个 Browser context（cf_clearance cookie 自动维持）

Windows 兼容性：
- Playwright 在 Windows 必须 ProactorEventLoop
- Scrapy 默认 SelectorEventLoop 不支持 subprocess
- 我们跑独立线程 + ProactorEventLoop，handler 用 sync Deferred 接口与 Scrapy reactor 通信
"""
from __future__ import annotations

import asyncio
import logging
import os
import queue
import threading
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any, Optional as Opt

from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse

logger = logging.getLogger(__name__)


@dataclass
class _DownloadJob:
    url: str
    timeout: float
    job_id: int
    meta: dict


@dataclass
class _DownloadResult:
    url: str
    status: int
    body: bytes
    encoding: str
    error: Optional[str] = None


class PlaywrightDownloadHandler:
    """用 Playwright 真浏览器处理 HTTPS 请求，绕过 Cloudflare Turnstile。

    启用条件：
    1. pip install playwright && playwright install chromium
    2. settings DOWNLOAD_HANDLERS["https"] = 本类
    3. 环境变量 CRAWLER_PROXY 可选配置代理
    """

    DEFAULT_PROXY = os.getenv("CRAWLER_PROXY")

    def __init__(self, crawler) -> None:
        try:
            from playwright.async_api import async_playwright  # noqa: F401
        except ImportError:
            raise NotConfigured(
                "playwright not installed; uv pip install playwright && playwright install chromium"
            )

        self._proxy = self.DEFAULT_PROXY
        self._jobs: queue.Queue = queue.Queue()
        self._results: dict[int, Future] = {}
        self._job_counter = 0
        self._worker_thread: Opt[threading.Thread] = None
        self._loop: Opt[asyncio.AbstractEventLoop] = None
        self._ready_evt = threading.Event()

        logger.info(f"PlaywrightDownloadHandler initialized (proxy={self._proxy})")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def _ensure_worker(self) -> None:
        if self._worker_thread is not None:
            return
        self._worker_thread = threading.Thread(
            target=self._run_loop, name="PlaywrightWorker", daemon=True
        )
        self._worker_thread.start()
        # 等 worker ready（最多 60s — 含启动 Chromium）
        if not self._ready_evt.wait(timeout=60):
            raise RuntimeError("Playwright worker not ready in 60s")

    def _run_loop(self) -> None:
        if os.name == "nt":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._worker_main())
        except Exception as exc:
            logger.error(f"Playwright worker crashed: {exc}")
        finally:
            loop.close()

    async def _worker_main(self) -> None:
        from playwright.async_api import async_playwright

        playwright_ctx = await async_playwright().start()
        browser = None
        try:
            launch_kwargs: dict = {"headless": True}
            if self._proxy:
                launch_kwargs["proxy"] = {"server": self._proxy}

            browser = await playwright_ctx.chromium.launch(**launch_kwargs)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
            )
            logger.info("Playwright browser started")
            self._ready_evt.set()

            while True:
                job = await self._loop.run_in_executor(None, self._jobs.get)
                if job is None:
                    break
                try:
                    result = await self._do_download(context, job)
                except Exception as exc:
                    result = _DownloadResult(
                        url=job.url, status=500, body=b"", encoding="utf-8",
                        error=str(exc),
                    )
                fut = self._results.pop(job.job_id, None)
                if fut and not fut.done():
                    fut.set_result(result)

            await context.close()
        finally:
            if browser:
                await browser.close()
            await playwright_ctx.stop()

    async def _do_download(self, context, job: _DownloadJob) -> _DownloadResult:
        page = await context.new_page()
        try:
            response = await page.goto(
                job.url,
                wait_until="domcontentloaded",
                timeout=job.timeout * 1000,
            )
            # 等 Cloudflare Turnstile 完成（页面 title 不再是 "Just a moment..."）
            try:
                await page.wait_for_function(
                    "() => !document.title.includes('Just a moment')",
                    timeout=15000,
                )
            except Exception:
                logger.warning(
                    f"Challenge timeout: {job.url} title={await page.title()!r}"
                )

            body = await page.content()
            status = response.status if response else 200
            return _DownloadResult(
                url=page.url, status=status, body=body.encode("utf-8"), encoding="utf-8",
            )
        finally:
            await page.close()

    # ===== Scrapy handler 接口 =====
    # Scrapy 2.19 检测到 download_request 是普通函数（非 coroutine）就调
    # download_request_async(request, spider) — 但传的是 (request, spider)
    # 我们走 sync 风格：返回 Deferred

    def download_request(self, request, spider):
        from twisted.internet import threads

        self._ensure_worker()

        self._job_counter += 1
        job_id = self._job_counter
        fut: Future = Future()
        self._results[job_id] = fut

        job = _DownloadJob(
            url=request.url,
            timeout=request.meta.get("download_timeout", 60),
            job_id=job_id,
            meta=dict(request.meta),
        )
        self._jobs.put_nowait(job)

        # 转 Deferred
        d = threads.deferToThread(fut.result, timeout=job.timeout + 30)
        d.addCallback(self._build_response, request)
        return d

    def _build_response(self, result: _DownloadResult, request) -> HtmlResponse:
        if result.error:
            logger.warning(f"Download failed {request.url} -> {result.error}")
        return HtmlResponse(
            url=result.url,
            status=result.status,
            headers={"Content-Type": "text/html; charset=utf-8"},
            body=result.body,
            request=request,
            encoding=result.encoding,
        )

    async def close(self) -> None:
        if not self._ready_evt.is_set():
            return
        try:
            self._jobs.put_nowait(None)
        except Exception:
            pass
        if self._worker_thread:
            self._worker_thread.join(timeout=10)