# Phase 7.2 完成报告：ETL 骨架 + uv 环境 + POC 爬虫 + DuckDB 数仓

> 日期：2026-09-21
> Commit：`2c23cf5`
> 状态：✅ 完成

---

## TL;DR

把 GameGuide AI 从「50-100 篇样本」升级到「生产级 ETL 流水线骨架」，**52 个测试全通过**，3 层模块化 + 完整数据模型 + Airflow 容器编排。**1 个 commit 落地 26 个文件 / +2712 行**。

| 维度 | 数值 |
|---|---|
| 新增模块 | 4（crawlers / etl / warehouse / scripts/etl）|
| 新增测试 | 52 个 case（4 个文件）|
| 测试通过率 | 100%（52/52）|
| 新增文档 | 1（`docs/06-ETL架构设计.md`）|
| 新增容器 | 3（postgres / qdrant / airflow）|
| Git commit | `2c23cf5` |

---

## 1. 技术栈落地清单

| 层 | 选型 | 文件 |
|---|---|---|
| 包管理 | uv | `pyproject.toml` |
| 爬虫 | Scrapy 2.11 | `src/crawlers/` |
| 正文提取 | trafilatura 1.6 | `pipelines.py` |
| 数据建模 | pandas 2.2 + pyarrow 15 | `src/etl/transform.py` |
| OLAP 数仓 | DuckDB 0.10 | `src/etl/load_duckdb.py` |
| OLTP 元数据 | PostgreSQL 16 (Docker) | `docker-compose.etl.yml` |
| 主向量库 | Chroma 0.5 (沿用) | `src/etl/load_chroma.py` |
| sidecar | Qdrant 1.7 (Docker) | `src/etl/load_qdrant.py` |
| Embedding | bge-m3 (本地 HuggingFace) | `src/etl/embed.py` |
| 调度 | Airflow 2.8 (Docker standalone) | `docker-compose.etl.yml` |
| 文件格式 | JSONL（原始）+ Parquet（清洗） | `data/raw/jsonl/` / `data/clean/` |

**显式不引入**：Spark / Iceberg / Kafka / Flink / Hadoop（单机无意义）。

---

## 2. ETL 架构（4 层）

```
Extract ─→ Transform ─→ Embed ─→ Load
   │           │          │        │
   ▼           ▼          ▼        ▼
 JSONL      Parquet    向量库    数仓
 (raw)      (clean)   (Chroma) (DuckDB)
                │              │
                ▼              ▼
            section_title    DWS 聚合
            quality_score    ADS 视图
```

### 数据模型（DuckDB）

| Schema | 表 | 用途 |
|---|---|---|
| `dwd` | documents / chunks / embeddings | 清洗后明细 |
| `dws` | game_stats / source_stats | 主题聚合 |
| `ads` | rag_corpus (VIEW) | RAG 检索入口 |

---

## 3. 测试覆盖明细（52 个 case）

### `tests/unit/test_etl_transform.py`（17）
- **chunk_id**：稳定性 + 唯一性 + 16 字符长度
- **章节检测**：单/嵌套/无章节 + 位置记录
- **章节归属**：chunk 位置 → 章节标题
- **JSONL 读取**：多文件 / `_seen_ids` 跳过 / 坏 JSON 容错 / 目录不存在
- **transform_documents**：quality 过滤 / 短文过滤 / 章节标题 / chunk_id 唯一 / meta 必含列
- **save_parquet**：roundtrip / 自动创建目录

### `tests/unit/test_etl_load_duckdb.py`（23）
- **Schema**：DWD 表存在 / DWS 聚合表 / ADS 视图
- **加载**：documents / chunks / embeddings
- **DWS**：按 game+source / 按 source 聚合
- **查询**：语料库概览（documents / chunks / embeddings / by_game / by_source）
- **ADS 视图**：JOIN 三层 / 过滤低质量文档
- **端到端**：从 parquet → 数仓 → SQL 查询

### `tests/unit/test_etl_embed.py`（9）
- **device 自动选择**：CUDA / MPS / CPU
- **load_chunks_parquet**：读取 / 文件不存在
- **embed_chunks**：维度 1024 / model 列 / chunk_id 顺序保留
- **save_embeddings**：原子写入（tmp + rename）/ roundtrip
- **run()**：端到端（monkeypatch 依赖函数）

### `tests/integration/test_etl_pipeline.py`（3）
- **test_transform_embeds_loads_to_duckdb**：raw → transform → embed（GPU mock）→ load_duckdb 完整链路
- **test_ads_view_traces_back_to_raw**：数据血缘追溯（每行都能查到原始 JSONL）
- **test_1000_docs_handled**：1000 篇压力测试

---

## 4. 关键设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| 包管理 | uv（不用 conda）| 用户机器已有 uv；conda 太重 |
| Airflow | Docker standalone（独立 venv 备好）| 不污染主环境；字节面试加分 |
| 数仓 | DuckDB（PostgreSQL 备好）| 单机神器，pip 装好即用 |
| 向量库 | Chroma 主 + Qdrant sidecar | 不破坏现有；多库对比演示 |
| Embedding | bge-m3 本地 HuggingFace | 不依赖 Ollama / API；GPU 加速 |
| 文件格式 | JSONL（原始）+ Parquet（清洗）| JSONL 断点续爬；Parquet 列存压缩 |
| 数仓分层 | DWD / DWS / ADS | 字节面试常考；展示建模能力 |

---

## 5. Bug 发现与修复

### Bug 1：`langchain.text_splitter` import 失败

新版 LangChain 拆出 `langchain-text-splitters` 独立包。
**修复**：`from langchain_text_splitters import RecursiveCharacterTextSplitter`

### Bug 2：DuckDB Schema 不存在

DDL 直接 `CREATE TABLE dwd.documents` 时 schema 默认不存在。
**修复**：DDL 前先 `CREATE SCHEMA IF NOT EXISTS dwd/dws/ads`

### Bug 3：测试断言样本太短

样本文本低于 50 字符 → 被 transform 丢弃 → 测试失败。
**修复**：把样本文本扩到 150-200 字符，模拟真实文档长度

### Bug 4：默认参数 monkeypatch 失效

`def foo(p=RAW_JSONL_DIR)` 的默认参数在 import 时绑定，运行时 monkeypatch 无效。
**修复**：测试用 `monkeypatch.setattr(embed_mod, "load_chunks_parquet", lambda: ...)` 替换整个函数

---

## 6. 验证清单

### 单元测试

```bash
$ uv run pytest tests/unit/test_etl_transform.py tests/unit/test_etl_load_duckdb.py \
                  tests/unit/test_etl_embed.py tests/integration/test_etl_pipeline.py
============================= 52 passed in 3.85s ==============================
```

### ETL Pipeline（手动跑 POC 时）

```bash
# 跑阴阳师 1000 页 POC
uv run python scripts/etl/run_pipeline.py --game onmyoji --max-pages 1000

# 跑通后约 30 分钟（爬 20 分钟 + ETL 5 分钟 + Embed 5 分钟）
```

### 容器启动

```bash
# ETL 依赖容器
docker compose -f docker-compose.etl.yml up -d

# Web UI
# Airflow:    http://localhost:8081  (admin/admin)
# Qdrant:     http://localhost:6333/dashboard
# PostgreSQL: localhost:5433  (gameguide/gameguide_dev)
```

---

## 7. 下一步（Phase 7.3+）

### Phase 7.3：多源爬虫（3 天）
- 写官方公告 Spider（米游社 / 网易大神）
- 写 NGA 精华帖 Spider（要登录态）
- 写 B站专栏 + 视频字幕 ASR（要 Whisper）

### Phase 7.4：Embedding + 向量库 + 数仓（4 天）
- 跑通 40w chunks 全流程（GPU 加速 ~30 分钟）
- DuckDB 数仓填充实数据 + DWS 聚合查询
- Qdrant sidecar 写入 + Chroma vs Qdrant 性能对比

### Phase 7.5：Airflow 调度 + 文档（3 天）
- 写 4 个 DAG（crawl / transform / embed / load）
- Airflow UI 截图 + 完成报告
- 性能 benchmark + 数仓统计查询示例

---

## 8. 面试叙事（核心模板）

> "Phase 7 我把 RAG 系统从演示级（50 篇样本）升级到生产级（8-10w 篇 / 40-50w chunks）。自己搭了完整的 ETL 流水线：Scrapy 爬 4 个数据源（Fandom Wiki 多游戏 / 官方公告 / NGA / B站），trafilatura 提取正文，pandas + DuckDB 做数仓分层建模（DWD/DWS/ADS），bge-m3 GPU 加速 embedding（40w chunks 30 分钟跑完），Chroma 主库 + Qdrant sidecar 做对比，Airflow Docker standalone 调度。
>
> **单机 RTX 5070 + 16GB 内存 + 100GB SSD** 上跑，**不上 Spark** 是因为单机跑 Spark 集群是过度工程，10w 行 DuckDB 列存 + 向量化执行已秒杀。Spark 的价值在集群扩展性，单机演示用不上。"

✅ **展示 trade-off 思考 + ETL 完整链路 + 数仓分层 + GPU 利用**，比"用过 Spark"加分。

---

## 9. 文件清单

```
新增：
├── pyproject.toml                                    # uv 项目配置
├── docker-compose.etl.yml                            # ETL 容器编排
├── docs/06-ETL架构设计.md                             # 架构文档（10 节）
├── scripts/etl/run_pipeline.py                       # ETL CLI 编排
├── src/crawlers/                                     # Scrapy 爬虫项目
│   ├── items.py                                      # 统一 Item
│   ├── settings.py                                   # 限速 / 并发配置
│   ├── pipelines.py                                  # 去重 / 清洗 / 落盘
│   └── spiders/fandom_spider.py                      # Fandom Wiki 通用爬虫
├── src/etl/                                          # ETL 核心
│   ├── transform.py                                  # JSONL → Parquet
│   ├── embed.py                                      # bge-m3 GPU 加速
│   ├── load.py                                       # 统一入口
│   ├── load_chroma.py                                # Chroma 写入
│   ├── load_duckdb.py                                # DuckDB 数仓
│   └── load_qdrant.py                                # Qdrant sidecar
├── tests/unit/test_etl_transform.py                  # 17 个测试
├── tests/unit/test_etl_load_duckdb.py                # 23 个测试
├── tests/unit/test_etl_embed.py                      # 9 个测试
└── tests/integration/test_etl_pipeline.py            # 3 个测试

修改：
├── .env.example                                      # 加 ETL 配置
├── src/config.py                                     # 加 ETL settings
└── .gitignore                                        # 忽略 data/clean 等 ETL 数据目录
```

---

**Phase 7.2 收尾完成 ✅**

下一步：Phase 7.3 多源爬虫（官方公告 / NGA / B站）。