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

# User-Agent（必须礼貌）
USER_AGENT = (
    "Mozilla/5.0 (compatible; GameGuide-AI-Bot/1.0; "
    "+https://github.com/ziyao/gameguide-ai)"
)

# 默认请求头
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
}

# 爬取深度（避免无限递归）
DEPTH_LIMIT = 5
DEPTH_STATS = True

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