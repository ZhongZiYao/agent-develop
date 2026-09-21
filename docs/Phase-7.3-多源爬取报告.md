# Phase 7.3 多源爬取完成报告

**时间**: 2026-09-21  
**目标**: 批量爬取多个游戏数据源，验证 ETL 全链路支持多源数据

---

## 执行概况

### 爬取统计

| 数据源 | 游戏 | 爬取条数 | 状态 |
|--------|------|----------|------|
| Fandom | onmyoji | 44 | ✅ 已有数据 |
| 米游社 | genshin (原神) | 10 | ✅ 成功 |
| 米游社 | honkai3 (绝区零) | 19 | ✅ 成功 |
| 米游社 | zenless (绝区零) | 7 | ✅ 成功 |
| 米游社 | honkai_star_rail (崩坏星穹铁道) | 0 | ⚠️ 内容过短被过滤 |

**总计**: 80 文档，2575 chunks

### 数据仓库统计

```
数据源分布:
  fandom:  44 docs,  936,365 字, 2492 chunks
  mihoyo:  36 docs,   25,463 字,   83 chunks

游戏分布:
  onmyoji:  44 docs
  honkai3:  19 docs
  genshin:  10 docs
  zenless:   7 docs
```

---

## 关键修复

### 问题：米游社数据被过滤

**现象**: transform 阶段 `dropped` 计数增加，米游社数据未入库

**根因**: `crawl_mihoyo_requests.py` 返回的文档缺少 `quality_score` 字段，导致 transform 默认值为 0，低于阈值 0.3 被过滤

**修复**: 添加质量分计算逻辑（与 Scrapy Pipeline 一致）
```python
word_count = len(body_md)
if word_count < 200:
    quality = 0.3
elif word_count > 50000:
    quality = 0.5
else:
    quality = min(1.0, 0.5 + word_count / 5000)
quality_score = round(quality, 3)
```

---

## 技术亮点

### 1. 多源 JSONL 自动合并
- `transform.py` 使用 `rglob("*.jsonl")` 递归扫描
- 自动处理 `data/raw/jsonl/{source}/*.jsonl` 目录结构
- 单次 transform 合并所有源数据

### 2. 幂等加载机制
- `load_duckdb.py` 实现 DELETE+INSERT 模式
- 支持增量更新，避免主键冲突
- 多次运行结果一致

### 3. 批量爬取脚本
- `scripts/crawl_all_sources.sh` 自动化爬取多游戏
- 容错设计：单个游戏失败不影响后续
- 统计报告：自动汇总各文件行数

---

## 数据质量观察

### 米游社内容特点
- **文本量小**: 平均 707 字/篇（fandom 平均 21,281 字/篇）
- **内容类型**: 玩家社区讨论为主，缺少系统性攻略
- **视频过滤**: `view_type=2/4` 纯视频帖被跳过
- **短文过滤**: <50 字内容被过滤

### 改进方向
1. **降低质量阈值**: 考虑将 `MIN_QUALITY_SCORE` 从 0.3 降至 0.2，保留更多社区讨论
2. **游戏百科补充**: Fandom 质量高但覆盖少，需增加游戏维基百科源
3. **深度爬取**: 当前只爬首页，后续可按标签/精华帖深度爬取

---

## 性能表现

**ETL 全流程耗时**: 
- Crawl: ~26 秒（4 游戏 × 1-5 页）
- Transform: 110 ms（80 docs → 2575 chunks）
- Load: 630 ms（写入 DuckDB）

**资源占用**:
- Parquet 文件: 0.6 MB（chunks）+ 0.01 MB（meta）
- DuckDB 数据库: ~1.5 MB

---

## 下一步

- [ ] Task #91: Embedding 批量生成（2575 chunks）
- [ ] Task #92: Airflow 调度（每日定时爬取）
- [ ] 探索其他数据源：B站专栏（API 已变更，需进一步调研）
- [ ] 前端集成：多源数据混合检索展示

---

## 文件清单

- ✅ `scripts/crawl_mihoyo_requests.py` - 米游社爬虫（requests 实现）
- ✅ `scripts/crawl_all_sources.sh` - 批量爬取脚本
- ✅ `src/etl/transform.py` - 多源 JSONL 合并转换
- ✅ `src/etl/load_duckdb.py` - 幂等加载逻辑
- ✅ `data/raw/jsonl/mihoyo/{game}.jsonl` - 原始数据（不提交）
- ✅ `data/warehouse/gameguide.duckdb` - 数仓（不提交）
