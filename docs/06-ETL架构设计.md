# Phase 7 ETL 架构设计

> 日期：2026-09-21
> 状态：Phase 7 启动文档
> 目标：从 50-100 篇样本数据 → 40-50w chunks（8-10w 篇文档）真实语料库

---

## 1. 目标与范围

### 1.1 业务目标

把 GameGuide AI 从「演示级 RAG」（50-100 篇样本）升级到「生产级数据层」（8-10w 篇文档 / 40-50w chunks），支撑：

1. **RAG 检索质量**：覆盖多游戏 + 多源，避免单源偏见
2. **数据可分析**：DuckDB 数仓支撑指标统计 / 数据血缘 / 质量监控
3. **流水线可调度**：Airflow DAG 让"重跑 / 增量 / 失败重试"全自动
4. **可演示对比**：Chroma vs Qdrant sidecar 性能对比

### 1.2 范围

✅ **In Scope**：
- 4 个数据源爬虫（Fandom Wiki / 官方公告 / NGA 精华 / B站字幕）
- 完整 ETL 流水线（Extract → Transform → Embed → Load）
- GPU 加速 Embedding（RTX 5070）
- DuckDB 数仓 + PostgreSQL 元数据
- Airflow 调度
- 监控 + 增量 + 重试

❌ **Out of Scope**（不在本阶段做）：
- Spark / Iceberg / Kafka（单机无意义）
- 流式 ETL（数据量小，批处理足够）
- 自动化数据质量报告（先做手动巡检）

---

## 2. 数据源清单

| ID | 数据源 | 类型 | 估算页数 | 估算 chunks | 爬取难度 | 合规风险 |
|----|--------|------|---------|------------|---------|---------|
| **S1** | Fandom Wiki（多游戏）| 半结构化 | 3-5w | 15-25w | 🟢 低 | 🟢 CC-BY-SA |
| **S2** | 官方公告 / 版本日志 | 半结构化 | 5k | 2-3w | 🟢 低 | 🟢 公开 |
| **S3** | NGA / TapTap 精华帖 | UGC | 1-2w | 5-10w | 🟡 中（要登录态）| 🟡 需尊重 robots.txt |
| **S4** | B站攻略专栏 + 视频字幕 ASR | 半结构化 | 5k | 2-5w | 🟡 中（要 ASR）| 🟢 公开 |
| **总计** | | | **~7-8w** | **~30-45w** | | |

### 2.1 POC 优先级

| 阶段 | 数据源 | 目标 |
|----|----|----|
| **Phase 7.2（POC）** | S1 阴阳师 Fandom Wiki | 1000 页 / 5000 chunks |
| **Phase 7.3（扩展）** | S1（多游戏）+ S2 | 5w 页 / 20w chunks |
| **Phase 7.4（全量）** | S1+S2+S3+S4 | 8w 页 / 40w chunks |

### 2.2 合规与礼仪

- ✅ **Fandom Wiki**：CC-BY-SA 协议，注明来源 + 作者（`attribution`）
- ✅ **官方公告**：公开内容，合理引用即可
- ⚠️ **NGA / TapTap**：遵守 robots.txt，仅爬公开精华区，不爬用户隐私
- ⚠️ **B站**：公开专栏 + ASR 后注明来源，**不爬登录态内容**
- ✅ **统一 User-Agent**：`GameGuide-AI-Bot/1.0 (+https://github.com/xxx)` 礼貌爬取
- ✅ **限速**：单域名 ≤ 1 req/sec，并发 ≤ 4
- ✅ **失败重试**：最多 3 次，失败入死信队列，不阻塞

---

## 3. 技术栈（最终版）

### 3.1 已锁定选型

| 层 | 选型 | 替代方案 | 选择理由 |
|----|------|---------|---------|
| **爬虫** | Scrapy 2.11 | requests / Playwright | 内置 Pipeline / Item / 并发 / 去重 / 调度 |
| **正文提取** | trafilatura 1.6 | BeautifulSoup | SOTA 正文提取，准确率高 |
| **HTML→MD** | markdownify 0.11 | html2text | 保留结构 + 中文友好 |
| **中文 NLP** | jieba 0.42 + HanLP 2.1 | 纯正则 | 实体抽取（妖刀姬 / S13）|
| **数据建模** | pandas 2.2 + pyarrow 15 | polars | DuckDB 兼容 + 通用 |
| **OLAP 数仓** | DuckDB 0.10 | ClickHouse / Spark | 单机神器，列存 + 向量化 |
| **OLTP 元数据** | PostgreSQL 16（Docker）| MySQL / SQLite | ACID + JSONB 灵活 |
| **调度** | Airflow 2.8（Docker standalone）| Prefect / Dagster | 字节面试加分，业内标配 |
| **主向量库** | Chroma 0.5（沿用）| FAISS / Milvus | 已集成，迁移成本高 |
| **向量库演示** | Qdrant 1.7（Docker sidecar）| Weaviate | 多库对比测试，面试亮点 |
| **Embedding** | bge-m3（1024 维）| OpenAI text-embedding-3 | 已沿用，本地 GPU 加速 |
| **Reranker** | bge-reranker-large | Cohere | 已沿用 |
| **存储格式** | JSONL（原始）+ Parquet（清洗）| CSV / Pickle | Parquet 列存压缩好 |

### 3.2 显式不引入

| 技术 | 不引入的理由 |
|----|----|
| **Spark / Iceberg** | 单机 10w 行 = 杀鸡用牛刀，DuckDB 秒杀 |
| **Hadoop / HDFS** | 同上，本地盘 = 你的 HDFS |
| **Kafka / Flink** | 不是流数据，Airflow 批调度足够 |
| **StarRocks / Doris** | 需要多节点，单机跑不起来 |
| **ClickHouse** | Docker 镜像 1GB+，DuckDB 在此量级更轻 |
| **MongoDB** | DuckDB + Parquet 已覆盖 JSON / 半结构化需求 |

### 3.3 硬件适配（RTX 5070 Laptop + E 盘 280GB）

| 用途 | 预算 | 备注 |
|----|----|----|
| 模型权重（bge-m3 + reranker）| 3 GB | 一次性下载 |
| 原始 HTML / JSONL | 5-8 GB | 清洗后可删 HTML |
| DWD 清洗后（Parquet）| 2 GB | 列存压缩 60-70% |
| Chroma 向量库 | 8-10 GB | 40w chunks × 1024 维 × 4B × 3 |
| Qdrant sidecar | 5-8 GB | 同等规模 |
| DuckDB + PostgreSQL | 2 GB | |
| Airflow logs + DAG | 1 GB | |
| Docker volumes | 10-15 GB | Qdrant + PG 持久化 |
| **uv venv** | 5 GB | Python 包 |
| **代码 + 文档** | 2 GB | |
| **Buffer** | **50-60 GB** | 重跑 / 调试 / 模型扩展 |
| **合计** | **~100 GB** | |

GPU 利用：RTX 5070（Blackwell，8GB VRAM）跑 bge-m3 embedding 提速 5-10x。

---

## 4. ETL 流水线架构

```
┌─────────────────────────────────────────────────────────────┐
│              GameGuide AI ETL 流水线 (Phase 7)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────── EXTRACT ───────────────┐                  │
│  │                                         │                  │
│  │  [S1 Fandom]    [S2 Official]           │                  │
│  │       │              │                   │                  │
│  │  [S3 NGA]      [S4 B站]                 │                  │
│  │       │              │                   │                  │
│  │  Scrapy Spiders (并发=4, 限速=1rps)     │                  │
│  │       │                                  │                  │
│  │       ▼                                  │                  │
│  │  data/raw/html/{source}/{date}/...html  │  ← 可删除        │
│  │  data/raw/jsonl/{source}/{date}.jsonl  │  ← 保留          │
│  └─────────────────────────────────────────┘                  │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────── TRANSFORM ──────────────┐                  │
│  │                                         │                  │
│  │  ① Trafilatura 提取正文                 │                  │
│  │  ② markdownify HTML→MD                   │                  │
│  │  ③ 章节检测 + 切分 (chunk_size=500)     │                  │
│  │  ④ jieba + HanLP 实体抽取               │                  │
│  │  ⑤ 元数据提取（标题/作者/时间/游戏）    │                  │
│  │  ⑥ 去重（SimHash / URL hash）           │                  │
│  │       │                                  │                  │
│  │       ▼                                  │                  │
│  │  data/clean/chunks.parquet  (DWD)        │                  │
│  │  data/clean/meta.parquet    (维度表)     │                  │
│  │  data/clean/sources.parquet (来源映射)   │                  │
│  └─────────────────────────────────────────┘                  │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────── EMBED ──────────────────┐                  │
│  │                                         │                  │
│  │  BAAI/bge-m3 (CUDA)                     │                  │
│  │  batch_size=32, fp16, normalize=True   │                  │
│  │  预计：40w chunks @ 300 句/秒           │                  │
│  │  ≈ 20-30 分钟                           │                  │
│  │       │                                  │                  │
│  │       ▼                                  │                  │
│  │  data/clean/embeddings.parquet (1024 维) │                  │
│  └─────────────────────────────────────────┘                  │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────── LOAD ───────────────────┐                  │
│  │                                         │                  │
│  │  ┌──────────────┐  ┌──────────────┐    │                  │
│  │  │ Chroma       │  │ Qdrant       │    │                  │
│  │  │ (主库)       │  │ (sidecar)    │    │                  │
│  │  └──────────────┘  └──────────────┘    │                  │
│  │                                         │                  │
│  │  ┌──────────────┐  ┌──────────────┐    │                  │
│  │  │ DuckDB       │  │ PostgreSQL   │    │                  │
│  │  │ (OLAP 数仓)  │  │ (OLTP 元数据)│    │                  │
│  │  └──────────────┘  └──────────────┘    │                  │
│  │                                         │                  │
│  │  - DuckDB: 文档 / chunks / 嵌入向量     │                  │
│  │  - PG: 任务运行日志 / 数据血缘 / 监控   │                  │
│  └─────────────────────────────────────────┘                  │
│                                                              │
│  ┌─────────────── ORCHESTRATION ───────────┐                  │
│  │                                         │                  │
│  │  Airflow standalone (Docker)            │                  │
│  │  DAGs:                                  │                  │
│  │   - crawl_fandom      (每日)            │                  │
│  │   - crawl_official    (每周)            │                  │
│  │   - crawl_nga         (每周)            │                  │
│  │   - crawl_bili        (每周)            │                  │
│  │   - transform_chunks  (依赖 crawl)     │                  │
│  │   - embed_chunks      (依赖 transform)  │                  │
│  │   - load_vector_db    (依赖 embed)      │                  │
│  │   - load_warehouse    (依赖 embed)      │                  │
│  └─────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 数据模型（数仓分层）

### 5.1 ODS 层（Operational Data Store）

源数据原始落地，**不做任何清洗**，只做格式统一：

```sql
-- ODS：原始爬取数据
CREATE TABLE ods.raw_documents (
    doc_id          VARCHAR(64) PRIMARY KEY,   -- URL hash
    source          VARCHAR(32),               -- 'fandom' / 'official' / 'nga' / 'bili'
    game            VARCHAR(32),               -- 'onmyoji' / 'genshin' / ...
    url             TEXT,
    title           TEXT,
    author          TEXT,
    publish_date    DATE,
    crawl_date      TIMESTAMP,
    raw_html_path   TEXT,                      -- 原始 HTML 文件路径
    raw_text_path   TEXT,                      -- 提取后文本路径
    language        VARCHAR(8),                -- 'zh' / 'en'
    http_status     INT,
    content_length  INT,                       -- 字节数
    error_message   TEXT
);
```

### 5.2 DWD 层（Data Warehouse Detail）

清洗 + 切分 + 标准化：

```sql
-- DWD：清洗后文档
CREATE TABLE dwd.documents (
    doc_id          VARCHAR(64) PRIMARY KEY,
    source          VARCHAR(32),
    game            VARCHAR(32),
    title           TEXT,
    author          TEXT,
    publish_date    DATE,
    crawl_date      TIMESTAMP,
    markdown        TEXT,                      -- 清洗后 Markdown
    word_count      INT,
    section_count   INT,
    quality_score   FLOAT                      -- 0-1 质量分
);

-- DWD：切分后 chunks
CREATE TABLE dwd.chunks (
    chunk_id        VARCHAR(64) PRIMARY KEY,   -- doc_id + chunk_index
    doc_id          VARCHAR(64),
    chunk_index     INT,
    chunk_text      TEXT,
    chunk_tokens    INT,
    section_title   TEXT,                      -- 所属章节
    embedding       FLOAT[1024]                -- bge-m3 向量
);
```

### 5.3 DWS 层（Data Warehouse Summary）

按主题聚合：

```sql
-- DWS：按游戏统计
CREATE TABLE dws.game_stats AS
SELECT
    game,
    COUNT(DISTINCT doc_id) AS doc_count,
    COUNT(chunk_id) AS chunk_count,
    AVG(quality_score) AS avg_quality,
    MAX(crawl_date) AS last_crawl
FROM dwd.documents
GROUP BY game;

-- DWS：按来源统计
CREATE TABLE dws.source_stats AS
SELECT
    source,
    COUNT(DISTINCT doc_id) AS doc_count,
    AVG(word_count) AS avg_word_count,
    SUM(word_count) AS total_words
FROM dwd.documents
GROUP BY source;

-- DWS：按实体统计（NER 结果）
CREATE TABLE dws.entity_stats AS
SELECT
    entity_name,
    entity_type,                              -- 'character' / 'skill' / 'item'
    COUNT(*) AS mention_count,
    COUNT(DISTINCT doc_id) AS doc_count
FROM dwd.entities
GROUP BY entity_name, entity_type;
```

### 5.4 ADS 层（Application Data Store）

给应用 / 报表用的最终视图：

```sql
-- ADS：RAG 检索入口视图（已与向量库对齐）
CREATE VIEW ads.rag_corpus AS
SELECT
    c.chunk_id,
    c.doc_id,
    d.game,
    d.source,
    c.section_title,
    c.chunk_text,
    c.embedding
FROM dwd.chunks c
JOIN dwd.documents d ON c.doc_id = d.doc_id
WHERE d.quality_score >= 0.5;
```

---

## 6. 流水线接口契约

### 6.1 Scrapy → 文件系统

```python
# data/raw/jsonl/fandom/2026-09-21.jsonl
{"doc_id": "abc123", "url": "...", "title": "...", "html": "...", "crawl_ts": 1234567890}
{"doc_id": "def456", "url": "...", "title": "...", "html": "...", "crawl_ts": 1234567891}
```

### 6.2 Transform 输出

```python
# data/clean/chunks.parquet (Arrow 表)
schema:
  chunk_id: string
  doc_id: string
  chunk_index: int32
  chunk_text: string
  chunk_tokens: int32
  section_title: string
  source: string
  game: string
```

### 6.3 Embedding 输出

```python
# data/clean/embeddings.parquet
schema:
  chunk_id: string
  embedding: list<float32>[1024]
  model: string          # 'bge-m3'
  model_version: string  # 'v1.0'
  embed_ts: timestamp
```

---

## 7. 监控与质量

### 7.1 关键指标

| 指标 | 公式 | 告警阈值 |
|----|----|----|
| 爬取成功率 | 成功数 / 总请求数 | < 80% 告警 |
| 平均文档长度 | AVG(word_count) | < 100 告警（疑似爬失败）|
| 重复率 | 重复文档 / 总文档 | > 30% 告警 |
| Chunk 长度分布 | P50 / P95 | P95 > 1000 切分异常 |
| Embedding 失败率 | 失败数 / 总数 | > 1% 告警 |
| 端到端耗时 | ETL 总耗时 | > 30min 告警 |

### 7.2 监控实现

- **轻量**：PostgreSQL 记录 `etl_runs` 表，每次跑批写入
- **可选**：Streamlit 简单 dashboard（Phase 7.5+ 视情况）

---

## 8. 风险与回退

| 风险 | 影响 | 回退方案 |
|----|----|----|
| **IP 被封** | 爬虫中断 | 限速 1rps + 随机 UA + 代理池（可选）|
| **磁盘爆**（>100GB）| ETL 中断 | 每阶段检查 + 自动跳过 + 删原始 HTML |
| **GPU 显存不够** | Embedding 失败 | 降级到 CPU（速度 -80% 但能跑）|
| **Qdrant Docker 起不来** | sidecar 缺失 | Chroma 单独跑，Qdrant 可选 |
| **Airflow Docker 卡** | 调度失败 | 切到独立 venv 跑 `airflow standalone` |
| **数据合规投诉** | 法律责任 | 提供 `robots.txt` 遵守证明 + 来源标注 |
| **DuckDB 大数据慢** | ETL 瓶颈 | 升级到 ClickHouse 或 PostgreSQL（极小概率）|

---

## 9. 实施路线

| 阶段 | 内容 | 周期 | 里程碑 |
|----|----|----|----|
| **7.1** | 调研 + 架构文档 | 1 天 | 本文档 |
| **7.2** | uv 环境 + POC 爬虫 | 2 天 | 阴阳师 1000 页成功 |
| **7.3** | 多源爬虫 + Transform | 3 天 | 5w 页入库 |
| **7.4** | Embedding + 向量库 + DuckDB | 4 天 | 40w chunks 可检索 |
| **7.5** | Airflow + 文档 + 报告 | 2 天 | 全流程跑通 |

---

## 10. 面试叙事模板

> "GameGuide AI 数据层从零搭起 ETL 流水线：Scrapy 爬 4 个数据源，trafilatura 做正文提取，pandas + DuckDB 做数仓建模（ODS/DWD/DWS/ADS），Airflow 跑 DAG 调度，bge-m3 GPU 加速 embed 40w chunks。单机 RTX 5070 + 16GB 内存 + 100GB SSD 撑住，**不上 Spark 是因为单机跑 Spark 集群是过度工程，DuckDB 列存在此量级已秒杀**。我能在面试里讲清 trade-off：什么时候该上 Spark（数据 > 1 亿行 + 真正集群），什么时候 DuckDB 够了。"

✅ **展示 trade-off 思考 + ETL 完整链路 + 数仓分层**，比"用过 Spark"加分。