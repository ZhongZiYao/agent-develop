# Phase 7.4 完成 - 前端集成验证指南

**时间**: 2026-09-21  
**状态**: ✅ ETL 完成，⚠️ 需重启后端

---

## 已完成工作

### 1. ETL 全流程
- ✅ **爬取**: 80 docs (fandom 44 + 米游社 36)
- ✅ **切分**: 2575 chunks
- ✅ **Embedding**: 2575 × 1024 维 (bge-m3)
- ✅ **DuckDB**: 数仓完整加载
- ✅ **Chroma**: 向量库已更新

### 2. 数据验证
```python
# Chroma 向量库验证
from src.vectorstore.chroma_store import get_vector_store_instance
vs = get_vector_store_instance()
print(vs.count())  # 输出: 2575 ✅

# 检索测试
results = vs.search('原神攻略', top_k=5)
# 能够检索到米游社和 fandom 混合结果 ✅
```

---

## ⚠️ 需要操作：重启后端

### 问题原因
Chroma collection 被重新创建，旧的 collection ID 失效：
```
{"detail":"Internal error: Collection [e277df41-a69f-4919-98cc-b0119504063f] does not exist."}
```

### 解决方案
重启后端服务，让它重新连接到新的 Chroma collection。

#### 方法 1: Docker Compose（推荐）
```bash
# 停止并重启后端容器
cd /path/to/RAG_system
docker-compose restart backend

# 或完全重启
docker-compose down
docker-compose up -d
```

#### 方法 2: 本地开发模式
```bash
# 找到运行中的后端进程并停止
# Windows:
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*"

# Linux/Mac:
pkill -f "uvicorn.*main:app"

# 重新启动
cd src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 验证步骤

### 1. 后端 API 测试
```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 查询测试（应该返回答案 + retrieved_docs）
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"原神攻略"}' | python -m json.tool
```

**预期结果**:
- `retrieved_docs`: 包含米游社和 fandom 来源的文档
- `answer`: LLM 根据新数据生成的回答
- `metadata.source`: 应该看到 `mihoyo` 和 `fandom`

### 2. 前端界面测试
```bash
# 启动前端（如果未运行）
cd frontend
npm run dev
```

访问 `http://localhost:3000`，测试查询：
- **测试 1**: "原神攻略" → 应该看到米游社来源的文档
- **测试 2**: "妖刀姬出装" → 应该看到 fandom 阴阳师攻略
- **测试 3**: "崩坏3攻略" → 应该看到米游社崩3内容

**检查点**:
- [ ] 检索到的文档包含 `source: mihoyo` 和 `source: fandom`
- [ ] 文档内容与爬取的数据一致
- [ ] LLM 回答基于新数据生成
- [ ] 引用标注正确（[1][2] 等）

### 3. 数据源分布验证
```python
# 检查检索结果的来源分布
from src.modules.retriever import HybridRetrieverModule

retriever = HybridRetrieverModule()
state = {"query": "原神攻略"}
result = await retriever(state)

# 统计来源
sources = [doc['source'] for doc in result['retrieved_docs']]
from collections import Counter
print(Counter(sources))
# 预期: {'mihoyo': X, 'fandom': Y}
```

---

## 数据源覆盖

### 当前已入库游戏
| 游戏 | 来源 | 文档数 | Chunks | 备注 |
|------|------|--------|--------|------|
| onmyoji (阴阳师) | Fandom | 44 | 2492 | 英文 Wiki |
| genshin (原神) | 米游社 | 10 | ~30 | 玩家讨论 |
| honkai3 (绝区零) | 米游社 | 19 | ~40 | 官方公告 |
| zenless (绝区零) | 米游社 | 7 | ~13 | 玩家讨论 |

### 检索测试用例
```
✅ "阴阳师妖刀姬" → Fandom 详细攻略
✅ "原神攻略" → 米游社玩家分享
✅ "崩坏3版本更新" → 米游社官方公告
✅ "绝区零" → 米游社最新讨论
```

---

## 性能指标

### ETL 性能
- Crawl: 26s (4 游戏)
- Transform: 110ms (80 docs → 2575 chunks)
- Embed: 9min (Ollama API 串行)
- Load DuckDB: 630ms
- Load Chroma: 2.5s

### 检索性能（预估）
- 向量检索: ~50ms (top_k=50)
- Rerank: ~100ms (top_n=5)
- LLM 生成: ~2-5s (streaming)
- **总延迟**: ~3-5s

---

## 下一步

### Phase 7.5: Airflow 调度（Task #92）
自动化 ETL 流程：
```python
# DAG 定义
crawl_task >> transform_task >> embed_task >> load_duckdb_task >> load_chroma_task
```

### 优化方向
1. **并发 embedding**: asyncio 改造 embed_ollama.py（提速 5-10x）
2. **增量更新**: 只 embed 新 chunks
3. **数据源扩展**: B站专栏、NGA、网易大神
4. **Rerank 优化**: bge-reranker-v2-m3

---

## 文件清单

- ✅ `src/etl/embed_ollama.py` - Ollama API embedding
- ✅ `src/etl/load_chroma.py` - Chroma 加载脚本（已修复 collection_name）
- ✅ `data/clean/embeddings.parquet` - 16 MB，2575 embeddings
- ✅ `data/warehouse/gameguide.duckdb` - 数仓完整
- ✅ `data/chroma/` - 向量库已更新（collection: gameguide）

---

## 故障排查

### 问题 1: 后端报错 "Collection does not exist"
**原因**: Chroma collection ID 变更  
**解决**: 重启后端服务

### 问题 2: 检索不到米游社数据
**检查**:
```python
from src.vectorstore.chroma_store import get_vector_store_instance
vs = get_vector_store_instance()
print(vs.count())  # 应该是 2575
```
**解决**: 如果 < 2575，重新运行 `python -c "from src.etl.load_chroma import load_to_chroma; load_to_chroma()"`

### 问题 3: 检索结果质量差
**可能原因**:
- Embedding 模型不匹配（检查是否都用 bge-m3）
- 数据质量问题（米游社文本较短）
- Rerank 未启用

**解决**: 检查 `settings.use_reranker` 配置
