"""Scrapy 爬虫项目包。

子模块：
    spiders/   各类爬虫（Fandom / Official / NGA / B站）
    pipelines  数据清洗、去重、HTML→MD、落盘 JSONL
    items.py   Item 定义
    settings.py Scrapy 配置（并发 / 限速 / User-Agent）

启动方式：
    scrapy crawl fandom
    scrapy crawl official
    scrapy crawl nga
    scrapy crawl bili
"""