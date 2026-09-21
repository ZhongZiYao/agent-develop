"""Phase 7 ETL 包 - Extract / Transform / Embed / Load 流水线。

模块结构：
    extract.py    从源数据（Scrapy 落盘 / API / 文件）读入 Document 列表
    transform.py  清洗 + 切分 + NER + 元数据提取
    embed.py      GPU 加速 batched embedding
    load_chroma.py    Chroma 写入
    load_qdrant.py    Qdrant sidecar 写入
    load_duckdb.py    DuckDB 数仓写入（ODS/DWD/DWS 分层）
"""