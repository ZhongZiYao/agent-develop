# GameGuide AI — API 设计文档

> 版本：v0.1 (2026-09)
> 配套：`docs/00-PRD.md`、`docs/01-架构设计.md`

---

## 1. 设计原则

1. **RESTful**：路径表示资源，HTTP 方法表示动作
2. **流式优先**：所有 LLM 调用默认 SSE 流式
3. **版本化**：所有接口在 `/api/v1/` 前缀下
4. **可观测**：每个请求带 `trace_id`、LangSmith 集成
5. **类型安全**：用 Pydantic 严格定义请求/响应

---

## 2. 接口列表

| 路径 | 方法 | 说明 | 优先级 |
|------|------|------|--------|
| `/api/v1/query` | POST | 同步问答 | P0 |
| `/api/v1/stream` | POST | SSE 流式问答 | P0 |
| `/api/v1/index` | POST | 触发索引重建 | P0 |
| `/api/v1/index/status` | GET | 查询索引状态 | P0 |
| `/api/v1/health` | GET | 健康检查 | P0 |
| `/api/v1/eval` | POST | 触发评测 | P1 |
| `/api/v1/feedback` | POST | 用户反馈 | P1 |
| `/api/v1/agent/stream` | POST | 多 Agent 流式（Phase 4）| P1 |

---

## 3. Pydantic Schema

### 3.1 QueryRequest

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class QueryRequest(BaseModel):
    query: str = Field(..., description="用户问题", min_length=1, max_length=2000)
    game: Optional[str] = Field(None, description="游戏名过滤，如'永劫无间'")
    top_k: int = Field(50, ge=1, le=200, description="召回数量")
    top_n: int = Field(5, ge=1, le=20, description="精排后保留数量")
    use_rerank: bool = Field(True, description="是否使用 Reranker")
    use_query_rewrite: bool = Field(False, description="是否启用 Query Rewrite")
    use_hyde: bool = Field(False, description="是否启用 HyDE")
    use_agent: bool = Field(False, description="是否使用多 Agent 模式")
    thread_id: Optional[str] = Field(None, description="会话 ID（用于 Checkpointing）")
    metadata: Optional[dict] = Field(None, description="额外元数据")
```

### 3.2 RetrievedDoc

```python
class RetrievedDoc(BaseModel):
    id: str
    title: str
    content: str
    source: str
    url: Optional[str]
    score: float
    metadata: dict = {}
```

### 3.3 QueryResponse

```python
class QueryResponse(BaseModel):
    answer: str = Field(..., description="生成的最终答案")
    retrieved_docs: List[RetrievedDoc] = Field(default_factory=list)
    citations: List[int] = Field(default_factory=list, description="引用的 doc 编号")
    trace_id: str
    usage: dict = Field(default_factory=dict, description="token 用量")
    latency_ms: float
    metadata: dict = {}
```

### 3.4 IndexRequest

```python
class IndexRequest(BaseModel):
    source_dir: str = Field("data/raw/", description="原始文档目录")
    force_rebuild: bool = Field(False, description="是否强制重建")
    chunk_size: int = Field(500, ge=100, le=2000)
    chunk_overlap: int = Field(50, ge=0, le=500)
    embedding_model: str = Field("BAAI/bge-m3")
```

### 3.5 IndexResponse

```python
class IndexResponse(BaseModel):
    job_id: str
    status: str  # "pending" | "running" | "completed" | "failed"
    total_docs: int = 0
    processed_docs: int = 0
    total_chunks: int = 0
    started_at: str
    finished_at: Optional[str] = None
    error: Optional[str] = None
```

---

## 4. 接口详细定义

### 4.1 POST /api/v1/query — 同步问答

**请求示例**：
```json
{
  "query": "妖刀姬 S13 怎么连招？",
  "game": "永劫无间",
  "top_k": 50,
  "top_n": 5,
  "use_rerank": true,
  "use_query_rewrite": false
}
```

**响应示例**：
```json
{
  "answer": "妖刀姬 S13 的核心连招是 [1]：(1) 长按 C 进入妖刀形态 → (2) 释放 1 技能「刃返」 → (3) 接 2 段普攻 → (4) 接大招「妖刀斩」。完整连招需配合 0.5 秒窗口取消。",
  "retrieved_docs": [
    {
      "id": "doc-yjwj-001",
      "title": "永劫无间妖刀姬攻略",
      "content": "妖刀姬 S13 是当前版本强势角色...",
      "source": "data/raw/yjwj/yjwj_yaodaoji.md",
      "url": null,
      "score": 0.92,
      "metadata": {"game": "永劫无间", "character": "妖刀姬", "version": "S13"}
    }
  ],
  "citations": [1],
  "trace_id": "langsmith-trace-xxx",
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 234,
    "total_tokens": 1468
  },
  "latency_ms": 3421.5,
  "metadata": {"retrieval_count": 50, "reranked_count": 5}
}
```

**错误码**：
| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 知识库为空 |
| 429 | LLM API 限速 |
| 500 | 服务器内部错误 |
| 503 | LLM 服务不可用 |

### 4.2 POST /api/v1/stream — SSE 流式问答

**请求**：同 `/query`

**响应**：Server-Sent Events 流
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

**事件流**：
```
event: start
data: {"trace_id": "langsmith-xxx", "query": "妖刀姬..."}

event: retrieval
data: {"chunks_retrieved": 50, "took_ms": 245}

event: rerank
data: {"top_n": 5, "took_ms": 156}

event: generation
data: {"delta": "妖刀姬", "index": 0}

event: generation
data: {"delta": "S13", "index": 1}

event: generation
data: {"delta": "的", "index": 2}

...

event: citations
data: {"citations": [1, 3]}

event: done
data: {"usage": {"total_tokens": 1468}, "latency_ms": 3421}
```

**客户端示例（JavaScript）**：
```javascript
const eventSource = new EventSource('/api/v1/stream?...', {
  // 注意：EventSource 不支持 POST，需要用 fetch + ReadableStream
});

async function streamQuery(query) {
  const response = await fetch('/api/v1/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query})
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    const lines = decoder.decode(value).split('\n');
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        // 处理 data
      }
    }
  }
}
```

### 4.3 POST /api/v1/index — 触发索引

**请求**：
```json
{
  "source_dir": "data/raw/yjwj/",
  "force_rebuild": false,
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

**响应**：
```json
{
  "job_id": "idx-20260918-001",
  "status": "running",
  "total_docs": 0,
  "processed_docs": 0,
  "total_chunks": 0,
  "started_at": "2026-09-18T10:00:00Z"
}
```

**异步处理**：用 BackgroundTasks，返回 job_id，前端轮询 `/index/status`

### 4.4 GET /api/v1/index/status

**Query 参数**：`?job_id=xxx`

**响应**：
```json
{
  "job_id": "idx-20260918-001",
  "status": "completed",
  "total_docs": 87,
  "processed_docs": 87,
  "total_chunks": 1234,
  "started_at": "2026-09-18T10:00:00Z",
  "finished_at": "2026-09-18T10:05:23Z"
}
```

### 4.5 GET /api/v1/health

**响应**：
```json
{
  "status": "ok",
  "components": {
    "vector_store": "ok",
    "bm25_index": "ok",
    "llm_api": "ok",
    "embedding_model": "ok"
  },
  "version": "0.1.0",
  "uptime_seconds": 3600
}
```

### 4.6 POST /api/v1/eval — 触发评测（Phase 2）

**请求**：
```json
{
  "test_set_path": "data/eval/test_set.jsonl",
  "pipeline": "advanced",
  "metrics": ["faithfulness", "context_recall", "answer_relevance"]
}
```

**响应**：
```json
{
  "eval_id": "eval-20260918-001",
  "status": "running",
  "total_cases": 30,
  "metrics": ["faithfulness", "context_recall", "answer_relevance"]
}
```

---

## 5. FastAPI 实现骨架

```python
# src/api/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from .schemas import QueryRequest, QueryResponse, IndexRequest, IndexResponse
from ..pipeline import run_rag, run_rag_stream

app = FastAPI(
    title="GameGuide AI",
    description="游戏攻略问答 RAG 系统",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """同步问答"""
    try:
        result = await run_rag(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/stream")
async def stream(req: QueryRequest):
    """SSE 流式问答"""
    async def event_generator():
        async for event in run_rag_stream(req):
            yield f"event: {event.type}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/v1/index", response_model=IndexResponse)
async def index(req: IndexRequest, background_tasks: BackgroundTasks):
    """触发索引"""
    job_id = generate_job_id()
    background_tasks.add_task(rebuild_index, req, job_id)
    return IndexResponse(
        job_id=job_id,
        status="pending",
        started_at=now_iso()
    )


@app.get("/api/v1/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "components": check_components(),
        "version": "0.1.0"
    }
```

---

## 6. 错误处理

### 6.1 全局错误格式

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "LLM API 调用频率超限，请稍后重试",
    "details": {"retry_after": 60},
    "trace_id": "xxx"
  }
}
```

### 6.2 错误码定义

| 错误码 | HTTP | 含义 |
|--------|------|------|
| `INVALID_REQUEST` | 400 | 请求参数错误 |
| `EMPTY_QUERY` | 400 | 查询为空 |
| `KNOWLEDGE_BASE_EMPTY` | 404 | 知识库为空（请先索引）|
| `RATE_LIMIT_EXCEEDED` | 429 | LLM API 限速 |
| `LLM_SERVICE_UNAVAILABLE` | 503 | LLM 服务不可用 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

### 6.3 重试策略
- 客户端：指数退避（1s, 2s, 4s, 8s, max 30s）
- 服务端：限流熔断，连续失败 5 次熔断 60s

---

## 7. 安全设计

### 7.1 输入校验
- `query` 长度 ≤ 2000 字
- 黑名单关键词过滤（"忽略以上指令"等 prompt injection）
- 单 IP QPS 限制（默认 10 QPS）

### 7.2 输出过滤
- 敏感词过滤（政治/暴力/色情）
- LLM 输出长度限制（避免滥用）
- 答案必须包含 citations（否则降级处理）

### 7.3 审计日志
- 所有请求入 audit log（含 user_id、query、answer、trace_id）
- 保留 90 天
- 可回放

---

## 8. 性能指标

| 接口 | P50 延迟 | P95 延迟 | QPS |
|------|---------|---------|-----|
| /query | < 3s | < 6s | 10 |
| /stream | TTFT < 1s | < 6s | 10 |
| /index | - | - | 1 |
| /health | < 50ms | < 100ms | 100 |

---

## 9. 版本演进

| 版本 | 变化 |
|------|------|
| v0.1 | 同步 query + 流式 stream（Phase 1-2）|
| v0.2 | + /eval 评测接口（Phase 2）|
| v0.3 | + /agent/stream 多 Agent（Phase 4）|
| v0.4 | + /memory 记忆管理（Phase 5）|
| v1.0 | + 鉴权 + 多租户（生产级）|

---

## 10. 接口测试

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient
from src.api.main import app

@pytest.mark.asyncio
async def test_query_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/query", json={
            "query": "妖刀姬怎么连招？",
            "game": "永劫无间"
        })
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["retrieved_docs"]) > 0
        assert "trace_id" in data


@pytest.mark.asyncio
async def test_stream_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream("POST", "/api/v1/stream", json={
            "query": "测试"
        }) as response:
            assert response.status_code == 200
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    events.append(json.loads(line[5:].strip()))
            assert len(events) > 0
            assert events[-1].get("type") == "done"
```