"""Scrapy 配置 - 限速 / 并发 / User-Agent / Pipeline 启用。

设计原则：
- 礼貌爬取：单域名 ≤ 4 并发，1 req/sec 限速
- robots.txt 遵守
- 失败自动重试 3 次
- 启用 Pipeline：去重 → HTML 清洗 → JSONL 落盘
"""

# 项目名
BOT_NAME = "gameguide_crawler"

# 并发与限速（核心礼仪）
CONCURRENT_REQUESTS_PER_DOMAIN = 4    # 单域名最大并发
DOWNLOAD_DELAY = 1.0                 # 单请求间隔（秒）
RANDOMIZE_DOWNLOAD_DELAY = True      # 随机 0.5-1.5x 抖动

# 重试
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# robots.txt
ROBOTSTXT_OBEY = True

# 反爬绕过：模拟真实 Chrome 浏览器，避免被 Cloudflare Turnstile 拦截
import logging  # noqa: E402  (放在前面以免 DOWNLOAD_HANDLERS 块的引用报错)
import os  # noqa: E402
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 完整浏览器请求头（缺一个 Cloudflare 都可能拒绝）
DEFAULT_REQUEST_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Chromium";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# 启用浏览器级 TLS 指纹（scrapy-fingerprint 插件，非必需但显著降低识别率）
# 如果未安装 scrapy-fingerprint，下面的 settings 会被忽略
try:
    import scrapy_fingerprint  # noqa: F401

    SCRAPY_FINGERPRINT = {
        "tls": True,            # TLS 指纹 = Chrome
        "http2": True,          # HTTP/2 指纹 = Chrome
        "user_agent": USER_AGENT,
    }
except ImportError:
    pass

# 爬取深度（避免无限递归）
DEPTH_LIMIT = 5
DEPTH_STATS = True

# HTTPS 用 curl_cffi 模拟 Chrome TLS 指纹（绕 Cloudflare）
# HTTP 保留默认 Twisted handler（不需要 TLS 指纹）
DOWNLOAD_HANDLERS = {
    "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
    "https": "src.crawlers.downloaders.playwright_handler.PlaywrightDownloadHandler",
}

# 代理：Fandom 在国内被 Cloudflare 拦截，必须经过代理才能拿到 200
# 走环境变量 CRAWLER_PROXY 配置（避免代码硬编码）
if os.getenv("CRAWLER_PROXY"):
    logger = logging.getLogger("scrapy")
    logger.info(f"CRAWLER_PROXY detected: {os.getenv('CRAWLER_PROXY')}")

# Pipeline 顺序：去重 → 编码统一 → HTML→MD → JSONL 落盘
ITEM_PIPELINES = {
    "src.crawlers.pipelines.DuplicateFilterPipeline": 100,
    "src.crawlers.pipelines.HtmlCleaningPipeline": 200,
    "src.crawlers.pipelines.JsonlDumpPipeline": 300,
}

# 日志
LOG_LEVEL = "INFO"
LOG_ENCODING = "utf-8"

# 内存 / 磁盘
MEMUSAGE_LIMIT_MB = 2048             # 2GB 内存上限（Win11 笔记本）
FEED_EXPORT_ENCODING = "utf-8"

# Telnet（开发用，关闭）
TELNETCONSOLE_ENABLED = False