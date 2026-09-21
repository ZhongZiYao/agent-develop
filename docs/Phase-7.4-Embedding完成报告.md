# Phase 7.4 Embedding 完成报告

**时间**: 2026-09-21  
**目标**: 为 2575 chunks 生成 bge-m3 embeddings 并入库

---

## 执行概况

### 数据规模
- **Chunks**: 2575 (80 文档切分)
- **Embeddings**: 2575 × 1024 维
- **存储**: 16 MB (Parquet 列存压缩)
- **模型**: bge-m3 (Ollama)

### 性能数据
- **生成速度**: ~4.8 chunks/s
- **总耗时**: ~9 分钟
- **API**: Ollama HTTP `/api/embeddings`
- **并发**: 串行（单线程）

---

## 技术方案

### 最终选择：Ollama HTTP API
```python
# src/etl/embed_ollama.py
def embed_text_ollama(text: str, model: str = "bge-m3") -> list[float]:
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": model, "prompt": text}
    resp = requests.post(url, json=payload, timeout=30)
    return resp.json().get("embedding", [])
```

**优势**:
- ✅ 零依赖（无需 HuggingFace 下载）
- ✅ 与现有技术栈一致（Ollama 已用于 LLM）
- ✅ 本地推理，数据不出网

**劣势**:
- ⚠️ 串行请求，速度较慢（~0.21s/chunk）

### 未采用方案：sentence-transformers
- **原因**: ModuleNotFoundError（需额外安装 torch + transformers）
- **保留**: `src/etl/embed.py` 保留用于 GPU 加速场景

---

## DuckDB 数仓状态

```sql
-- 最终统计
SELECT 
    'documents' as type, COUNT(*) as n FROM dwd.documents
UNION ALL
SELECT 'chunks', COUNT(*) FROM dwd.chunks
UNION ALL
SELECT 'embeddings', COUNT(*) FROM dwd.embeddings;
```

| type | n |
|------|---|
| documents | 80 |
| chunks | 2575 |
| embeddings | 2585 |

**注**: embeddings 有 2585 条（含 10 条旧测试数据 BAAI/bge-m3）

### 数据完整性
```sql
-- Chunks without embeddings: 0
SELECT COUNT(*) 
FROM dwd.chunks c 
LEFT JOIN dwd.embeddings e ON c.chunk_id = e.chunk_id 
WHERE e.chunk_id IS NULL;
-- Result: 0 ✅
```

---

## 执行日志

```bash
# Step 1: 生成 embeddings (Ollama API)
python -c "from src.etl.embed_ollama import run; run()"
# Output:
#   加载 2575 chunks from data/clean/chunks.parquet
#   开始 embedding 2575 个 chunks (model=bge-m3)...
#   Embedding: 100%|██████████| 2575/2575 [09:08<00:00, 4.69it/s]
#   写入 data/clean/embeddings.parquet (16.0 MB, 2575 rows)

# Step 2: 加载到 DuckDB
python -c "from src.etl.load_duckdb import run; run()"
# Output:
#   dwd.embeddings: 2585 rows
#   语料库概览: {'documents': 80, 'chunks': 2575, 'embeddings': 2585, ...}
```

---

## 文件清单

- ✅ `src/etl/embed_ollama.py` - Ollama API 实现（新建）
- ✅ `src/etl/embed.py` - sentence-transformers 实现（保留）
- ✅ `data/clean/embeddings.parquet` - 16 MB，2575 rows
- ✅ `data/warehouse/gameguide.duckdb` - 已加载 embeddings

---

## 性能优化方向

### 1. 并发请求（asyncio）
```python
import asyncio
import aiohttp

async def embed_text_async(text: str, session):
    async with session.post(url, json=payload) as resp:
        return await resp.json()

# 预计提速 5-10x（受 Ollama 并发限制）
```

### 2. GPU 本地推理（sentence-transformers）
```bash
uv pip install sentence-transformers torch

python -c "from src.etl.embed import run; run()"
# GPU batch 推理: ~32 chunks/batch @ 100ms = 0.3s/chunk
# 预计 2575 chunks @ 1-2 分钟
```

### 3. 增量更新
```python
# 只 embed 新 chunks（JOIN 检查已有 embedding）
SELECT c.chunk_id, c.chunk_text
FROM dwd.chunks c
LEFT JOIN dwd.embeddings e ON c.chunk_id = e.chunk_id
WHERE e.chunk_id IS NULL
```

---

## 下一步

### Task #91 后续子任务

#### 1. 向量库加载（Chroma）
```python
from src.etl.load_chroma import load_all_to_chroma

load_all_to_chroma(
    chunks_parquet="data/clean/chunks.parquet",
    embeddings_parquet="data/clean/embeddings.parquet",
    collection_name="gameguide-corpus"
)
```

#### 2. 向量库加载（Qdrant sidecar，可选）
```python
from src.etl.load_qdrant import load_all_to_qdrant

load_all_to_qdrant(
    chunks_parquet="data/clean/chunks.parquet",
    embeddings_parquet="data/clean/embeddings.parquet"
)
```

#### 3. 端到端检索测试
```python
# 测试 DuckDB embeddings → 向量检索
from src.retrievers.vector_retriever import VectorRetriever

retriever = VectorRetriever(db_path="data/warehouse/gameguide.duckdb")
results = retriever.search("妖刀姬怎么出装？", top_k=5)
```

---

## 技术债务

- [ ] Task #101: 标记完成（embed.py 改用 Ollama）
- [ ] embed_ollama.py 改造为 async 并发版本
- [ ] 清理旧 BAAI/bge-m3 测试数据（10 条）
- [ ] 断点续跑：支持增量 embedding
