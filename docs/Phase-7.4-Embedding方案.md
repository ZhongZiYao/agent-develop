# Phase 7.4 Embedding 实现方案

**时间**: 2026-09-21  
**目标**: 为 2575 chunks 生成 bge-m3 embeddings 并入库

---

## 方案选择

### Option 1: sentence-transformers (原方案)
- **优点**: GPU 加速，batch 推理高效
- **缺点**: 需要下载 HuggingFace 模型（~2GB），依赖 torch
- **文件**: `src/etl/embed.py`
- **状态**: ❌ ModuleNotFoundError: sentence_transformers

### Option 2: Ollama HTTP API (推荐)
- **优点**: 
  - 无需下载模型（Ollama 已有 bge-m3）
  - 零依赖（只需 requests）
  - 与现有技术栈一致（Ollama 已用于 LLM）
- **缺点**: 串行请求，速度较慢（2575 chunks 预计 10-15 分钟）
- **文件**: `src/etl/embed_ollama.py` ✅ 已创建
- **API**: `POST http://localhost:11434/api/embeddings`

---

## 实现细节

### embed_ollama.py 核心逻辑

```python
def embed_text_ollama(text: str, model: str = "bge-m3") -> list[float]:
    """调用 Ollama API 生成 embedding。"""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": model, "prompt": text}
    resp = requests.post(url, json=payload, timeout=30)
    return resp.json().get("embedding", [])

def embed_chunks(chunks_df: pd.DataFrame) -> pd.DataFrame:
    """批量 embedding（串行）。"""
    embeddings = []
    for text in tqdm(chunks_df["chunk_text"]):
        emb = embed_text_ollama(text)
        embeddings.append(emb)
    return pd.DataFrame({
        "chunk_id": chunks_df["chunk_id"],
        "embedding": embeddings,
        "model": "bge-m3"
    })
```

### 执行命令

```bash
# 1. 确保 Ollama 运行中，且 bge-m3 已拉取
ollama list | grep bge-m3

# 2. 运行 embedding 生成
python -c "from src.etl.embed_ollama import run; run()"
# 输出: data/clean/embeddings.parquet (2575 rows × 1024 dim)

# 3. 重新加载到 DuckDB
python -c "from src.etl.load_duckdb import run; run()"
```

---

## 性能预估

| 阶段 | 规模 | 耗时 | 备注 |
|------|------|------|------|
| Ollama embedding | 2575 chunks | ~15 min | 串行请求，~0.35s/chunk |
| Parquet 写入 | 2575 × 1024 | <1s | 列存压缩 |
| DuckDB 加载 | 2575 embeddings | <2s | DELETE+INSERT |

**瓶颈**: Ollama API 串行调用

**优化方向**:
1. 并发请求（asyncio + aiohttp）
2. 本地 GPU 推理（回到 sentence-transformers）
3. 分批加载到 Chroma（边 embed 边入库）

---

## 下一步操作

```bash
# Step 1: 生成 embeddings
python src/etl/embed_ollama.py

# Step 2: 加载到 DuckDB
python -c "from src.etl.load_duckdb import load_embeddings_to_dwd; load_embeddings_to_dwd()"

# Step 3: 验证
python -c "
import duckdb
con = duckdb.connect('data/warehouse/gameguide.duckdb')
print(con.execute('SELECT COUNT(*) FROM dwd.embeddings').fetchone())
con.close()
"
# 预期输出: (2575,)
```

---

## 后续集成：向量库加载

### Chroma (主库)
```python
from src.etl.load_chroma import load_all_to_chroma

load_all_to_chroma(
    chunks_parquet="data/clean/chunks.parquet",
    embeddings_parquet="data/clean/embeddings.parquet",
    collection_name="gameguide-corpus"
)
```

### Qdrant (可选 sidecar)
```python
from src.etl.load_qdrant import load_all_to_qdrant

load_all_to_qdrant(
    chunks_parquet="data/clean/chunks.parquet",
    embeddings_parquet="data/clean/embeddings.parquet",
    collection_name="gameguide-corpus"
)
```

---

## 文件清单

- ✅ `src/etl/embed.py` - 原 sentence-transformers 实现（保留）
- ✅ `src/etl/embed_ollama.py` - 新 Ollama API 实现
- ⏳ `src/etl/load_chroma.py` - Chroma 向量库加载
- ⏳ `src/etl/load_qdrant.py` - Qdrant 向量库加载

---

## 技术债务

1. **Task #101**: embed.py 改用 Ollama（本次已用 embed_ollama.py 新建）
2. **并发优化**: embed_ollama.py 改造为 async + 批量并发
3. **断点续跑**: 支持部分 chunks 已 embed 场景
