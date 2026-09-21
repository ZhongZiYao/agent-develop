"""Curl-cffi Download Handler - 绕过 Cloudflare 的真实浏览器 TLS 指纹。

为什么需要：
- 默认 Twisted/HTTP11 handler 用 Python OpenSSL，TLS 指纹 (JA3) 是爬虫标志
- Fandom/Cloudflare 看 JA3 直接弹 403
- curl-cffi 模拟 Chrome 124 的 libcurl TLS 指纹，Python 里能拿到 200

使用：
- settings.py 把 "https" 指向本 handler
- 保留 http 走默认 Twisted（http 不需要 TLS 指纹）

Scrapy 2.19 download handler 接口约定：
- download_request(self, request, spider) -> Deferred (返回 Twisted Deferred)
- close() -> coroutine (注意是 async coroutine)
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse, Request as ScrapyRequest
from scrapy.utils.defer import deferred_from_coro, deferred_to_future

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from scrapy.crawler import Crawler


class CurlCffiDownloadHandler:
    """用 curl_cffi 处理 HTTPS 请求，绕过 Cloudflare Turnstile。

    启用条件：
    1. 安装了 curl_cffi
    2. settings 里 DOWNLOAD_HANDLERS["https"] = "src.crawlers.downloaders.curl_cffi_handler.CurlCffiDownloadHandler"
    3. 环境变量 CRAWLER_PROXY 可选配置代理
    """

    DEFAULT_IMPERSONATE = os.getenv("CRAWLER_IMPERSONATE", "chrome124")
    DEFAULT_PROXY = os.getenv("CRAWLER_PROXY")  # e.g. "http://127.0.0.1:7890"

    def __init__(self, crawler: "Crawler") -> None:
        try:
            from curl_cffi import requests as cc_requests  # noqa: F401
        except ImportError:
            raise NotConfigured("curl_cffi is not installed; pip install curl-cffi")

        self._crawler = crawler
        self._impersonate = self.DEFAULT_IMPERSONATE
        self._proxy = self.DEFAULT_PROXY
        logger.info(
            f"CurlCffiDownloadHandler initialized (impersonate={self._impersonate}, proxy={self._proxy})"
        )

    @classmethod
    def from_crawler(cls, crawler: "Crawler") -> "CurlCffiDownloadHandler":
        return cls(crawler)

    def download_request(self, request: ScrapyRequest, spider: Any):
        """Scrapy 2.19 download_request 接口：返回 Deferred。"""
        from twisted.internet import threads

        return threads.deferToThread(self._sync_download, request)

    def _sync_download(self, request: ScrapyRequest) -> HtmlResponse:
        from curl_cffi import requests as cc_requests

        # 构造 curl_cffi session
        session_kwargs: dict[str, Any] = {
            "impersonate": self._impersonate,
            "timeout": request.meta.get("download_timeout", 30),
            "allow_redirects": True,
        }
        # proxy 优先级：request.meta > 环境变量
        proxy_meta = request.meta.get("proxy")
        if proxy_meta:
            session_kwargs["proxy"] = proxy_meta
        elif self._proxy:
            session_kwargs["proxy"] = self._proxy

        session = cc_requests.Session(**session_kwargs)

        # 合并 headers
        merged_headers: dict[str, str] = {}
        for k, v in request.headers.items():
            key = k.decode("latin1") if isinstance(k, bytes) else k
            if isinstance(v, list):
                merged_headers[key] = v[0].decode("latin1") if isinstance(v[0], bytes) else v[0]
            else:
                merged_headers[key] = v.decode("latin1") if isinstance(v, bytes) else v

        # 关键：去掉 Accept-Encoding，让 curl_cffi 返回原始字节（避免 brotli 编码）
        # Scrapy 的 httpcompression 中间件会再用 brotli 解一次，但版本不一致就崩
        merged_headers.pop("Accept-Encoding", None)

        try:
            response = session.request(
                method=request.method,
                url=request.url,
                headers=merged_headers,
                data=request.body if request.body else None,
            )
            # curl_cffi 已自动解码压缩响应 — 必须从 headers 中移除 Content-Encoding，
            # 否则 Scrapy 的 HttpCompressionMiddleware 会再次解压 → 报错
            headers_dict = dict(response.headers)
            headers_dict.pop("Content-Encoding", None)
            headers_dict.pop("content-encoding", None)
            headers_dict.pop("Content-Length", None)  # 解压后长度变了

            return HtmlResponse(
                url=response.url,
                status=response.status_code,
                headers=headers_dict,
                body=response.content,
                request=request,
                encoding=response.encoding or "utf-8",
            )
        except Exception as exc:
            logger.warning(f"curl_cffi request failed: {request.url} -> {exc}")
            raise
        finally:
            session.close()

    async def close(self) -> None:
        """清理（Scrapy 2.19 要求是 coroutine）。"""
        pass