"""Download handlers - 绕 Cloudflare TLS / Turnstile 的方案。

- playwright_handler: 真 Chromium 浏览器，能跑 JS Challenge（推荐）
- curl_cffi_handler: 备选方案，已知不稳（Cloudflare 频繁 ban IP）
"""
from .playwright_handler import PlaywrightDownloadHandler

__all__ = ["PlaywrightDownloadHandler"]