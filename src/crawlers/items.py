"""Scrapy Items - 定义爬取的数据结构。"""

import scrapy


class GameDocumentItem(scrapy.Item):
    """统一的游戏文档 Item，跨数据源复用。

    所有爬虫（Fandom / Official / NGA / B站）都 yield 这个 Item，
    pipeline 统一处理。
    """

    # 必填字段
    doc_id = scrapy.Field()          # 文档唯一 ID（URL hash）
    source = scrapy.Field()          # 数据源: 'fandom' / 'official' / 'nga' / 'bili'
    game = scrapy.Field()            # 游戏: 'onmyoji' / 'genshin' / 'arknights' / ...
    url = scrapy.Field()             # 原始 URL
    title = scrapy.Field()           # 标题
    raw_html = scrapy.Field()        # 原始 HTML（pipeline 处理）
    crawl_ts = scrapy.Field()        # 爬取时间戳

    # 可选字段
    author = scrapy.Field()          # 作者
    publish_date = scrapy.Field()    # 发布日期（ISO 8601 字符串）
    language = scrapy.Field()        # 'zh' / 'en'，默认 'zh'
    raw_json = scrapy.Field()        # 原始 JSON / API 响应（调试用）

    # 清洗后字段（pipeline 写入）
    clean_text = scrapy.Field()      # 清洗后正文（Markdown）
    word_count = scrapy.Field()      # 字符数
    quality_score = scrapy.Field()   # 质量分 0-1