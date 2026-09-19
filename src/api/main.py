"""FastAPI 应用入口

接口：
- POST /api/v1/query      同步问答（原实现）
- POST /api/v1/stream     SSE 流式问答（原实现）
- POST /api/v1/chat-graph      同步问答（LangGraph 版本，需 USE_LANGGRAPH=true）
- POST /api/v1/chat-graph/stream  SSE 流式问答（LangGraph 版本，需 USE_LANGGRAPH=true）
- POST /api/v1/index      触发索引
- GET  /api/v1/index/{id} 查询索引状态
- GET  /api/v1/health     健康检查
- /api/v1/sessions/*     会话管理（Phase 1.5）
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from ..config import settings
from ..llm import get_streaming_llm, message_text, reasoning_text
from ..pipeline import build_context, retrieve
from ..prompts.templates import SYSTEM_PROMPT, build_user_prompt
from ..schemas import Chunk
from ..splitters.recursive_splitter import split_documents
from ..storage.database import init_db
from ..vectorstore.chroma_store import get_vector_store_instance
from ..loaders.markdown_loader import load_markdown_dir
from .schemas import (
    HealthResponse,
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
    RetrievedDoc,
)
from .sessions import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期：启动时初始化数据库"""
    await init_db()
    yield


app = FastAPI(
    title="GameGuide AI",
    description="游戏攻略问答 RAG 系统 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 内存索引任务存储（Phase 5 替换为 Redis/Celery）=====
_index_jobs: dict[str, IndexResponse] = {}


def _retrieve_to_response(results, top_n: int) -> tuple[list[RetrievedDoc], list[Chunk]]:
    """把 RetrievalResult 转成 RetrievedDoc + Chunk"""
    docs = []
    for r in results[:top_n]:
        docs.append(
            RetrievedDoc(
                id=r.chunk.chunk_id,
                title=r.chunk.metadata.get("title", "未知"),
                content=r.chunk.content[:300],
                source=r.chunk.source,
                score=r.score,
                metadata=r.chunk.metadata,
            )
        )
    return docs, [r.chunk for r in results[:top_n]]


async def _persist_turn(
    session_id: str | None,
    query_text: str,
    answer: str,
    thinking: str,
    retrieved_docs: list[RetrievedDoc],
    history_count: int,
) -> None:
    """持久化一轮对话；首轮在后台生成标题。失败不影响问答主流程。"""
    if not session_id:
        return

    try:
        from ..storage.database import AsyncSessionLocal
        from ..storage.session_store import SessionStore

        async with AsyncSessionLocal() as db:
            store = SessionStore(db)
            if not await store.get_session(session_id):
                logger.warning(f"Skip persistence: session {session_id} does not exist")
                return
            await store.append_message(session_id, "user", query_text)
            await store.append_message(
                session_id,
                "assistant",
                answer,
                thinking=thinking or None,
                retrieved_docs=[doc.model_dump() for doc in retrieved_docs],
            )

        if history_count == 0:
            from ..storage.naming import generate_session_title, rename_session_async

            async def _rename_first_turn() -> None:
                title = await generate_session_title(query_text)
                await rename_session_async(session_id, title)

            asyncio.create_task(_rename_first_turn())
    except Exception as exc:
        logger.warning(f"Failed to persist session turn: {exc}")


@app.post("/api/v1/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """同步问答（支持 session 历史）"""
    start = time.time()
    trace_id = f"trace-{uuid.uuid4().hex[:12]}"

    try:
        # 加载历史（如果提供了 session_id）
        from ..pipeline import load_history
        history = await load_history(req.session_id) if req.session_id else []

        # 1. 检索
        results = retrieve(req.query, top_k=req.top_k, game=req.game)

        if not results:
            return QueryResponse(
                answer="知识库为空，请先调用 /api/v1/index 构建索引",
                retrieved_docs=[],
                citations=[],
                trace_id=trace_id,
                latency_ms=(time.time() - start) * 1000,
            )

        # 2. 短路判断：top1 score 太低直接拒答
        from ..prompts.templates import REJECT_MESSAGE, REJECT_SCORE_THRESHOLD

        if results[0].score < REJECT_SCORE_THRESHOLD:
            preview_chunks, _ = build_context(results, top_n=min(3, len(results)))
            preview_text = "\n\n".join(preview_chunks) if preview_chunks else "（无）"
            reject_answer = REJECT_MESSAGE.format(context=preview_text)
            reject_docs = _retrieve_to_response(results, min(3, len(results)))[0]
            await _persist_turn(
                req.session_id,
                req.query,
                reject_answer,
                "",
                reject_docs,
                len(history),
            )
            return QueryResponse(
                answer=reject_answer,
                retrieved_docs=reject_docs,
                citations=[],
                trace_id=trace_id,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                latency_ms=(time.time() - start) * 1000,
            )

        # 3. 构造 context
        context_chunks, _ = build_context(results, top_n=req.top_n)

        # 3. 生成（带 history）
        from ..llm import get_llm
        from ..pipeline import format_history
        from ..prompts.thinking_parser import parse_thinking

        llm = get_llm()
        user_prompt = build_user_prompt(req.query, context_chunks, req.game or "")
        if history:
            user_prompt = format_history(history) + user_prompt

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)

        # 剥离 <think>...</think> 块
        raw_content = message_text(response)
        clean_answer, tagged_thinking = parse_thinking(raw_content)
        thinking_content = reasoning_text(response) or tagged_thinking

        usage = {}
        if hasattr(response, "response_metadata") and response.response_metadata:
            token_usage = response.response_metadata.get("token_usage", {})
            usage = {
                "prompt_tokens": token_usage.get("prompt_tokens", 0),
                "completion_tokens": token_usage.get("completion_tokens", 0),
                "total_tokens": token_usage.get("total_tokens", 0),
            }

        # 4. 构造响应
        retrieved_docs, _ = _retrieve_to_response(results, req.top_n)

        # 5. 自动持久化到 session（如果提供了 session_id）
        await _persist_turn(
            req.session_id,
            req.query,
            clean_answer or raw_content,
            thinking_content,
            retrieved_docs,
            len(history),
        )

        return QueryResponse(
            answer=clean_answer or raw_content,  # 兜底：剥离失败就用原文
            thinking=thinking_content,
            has_thinking=bool(thinking_content),
            retrieved_docs=retrieved_docs,
            citations=[],  # Phase 2 解析 [1]、[2] 标注
            trace_id=trace_id,
            usage=usage,
            latency_ms=(time.time() - start) * 1000,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/v1/stream")
async def stream(req: QueryRequest):
    """SSE 流式问答"""

    async def event_generator():
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        yield {"event": "start", "data": json.dumps({"trace_id": trace_id, "query": req.query}, ensure_ascii=False)}

        try:
            # 1. 加载会话历史并检索
            from ..pipeline import format_history, load_history

            history = await load_history(req.session_id) if req.session_id else []
            retrieve_start = time.time()
            results = retrieve(req.query, top_k=req.top_k, game=req.game)
            retrieve_took = (time.time() - retrieve_start) * 1000

            if not results:
                yield {"event": "error", "data": json.dumps({"error": "知识库为空"}, ensure_ascii=False)}
                return

            from ..prompts.templates import REJECT_MESSAGE, REJECT_SCORE_THRESHOLD

            if results[0].score < REJECT_SCORE_THRESHOLD:
                preview_chunks, _ = build_context(results, top_n=min(3, len(results)))
                preview_text = "\n\n".join(preview_chunks) if preview_chunks else "（无）"
                reject_answer = REJECT_MESSAGE.format(context=preview_text)
                retrieved_docs, _ = _retrieve_to_response(results, min(3, len(results)))
                await _persist_turn(
                    req.session_id,
                    req.query,
                    reject_answer,
                    "",
                    retrieved_docs,
                    len(history),
                )
                yield {
                    "event": "generation",
                    "data": json.dumps({"delta": reject_answer}, ensure_ascii=False),
                }
                yield {
                    "event": "done",
                    "data": json.dumps(
                        {
                            "answer": reject_answer,
                            "thinking": "",
                            "has_thinking": False,
                            "session_id": req.session_id,
                            "retrieved_docs": [doc.model_dump() for doc in retrieved_docs],
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        },
                        ensure_ascii=False,
                    ),
                }
                return

            yield {
                "event": "retrieval",
                "data": json.dumps({"chunks_retrieved": len(results), "took_ms": retrieve_took}, ensure_ascii=False),
            }

            # 2. 构造 context
            context_chunks, _ = build_context(results, top_n=req.top_n)

            # 3. 流式生成（带 thinking 解析）
            from ..prompts.thinking_parser import StreamThinkingParser

            llm = get_streaming_llm()
            user_prompt = build_user_prompt(req.query, context_chunks, req.game or "")
            if history:
                user_prompt = format_history(history) + user_prompt
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            parser = StreamThinkingParser()
            full_answer = ""
            full_thinking = ""

            async for chunk in llm.astream(messages):
                structured_thinking = reasoning_text(chunk)
                if structured_thinking:
                    full_thinking += structured_thinking
                    yield {
                        "event": "thinking",
                        "data": json.dumps({"delta": structured_thinking}, ensure_ascii=False),
                    }

                content_delta = message_text(chunk)
                if content_delta:
                    # 非 Ollama 模型可能仍将 reasoning 包在 <think> 中，保留 parser 兜底。
                    answer_delta, tagged_thinking = parser.feed(content_delta)
                    if tagged_thinking:
                        full_thinking += tagged_thinking
                        yield {
                            "event": "thinking",
                            "data": json.dumps({"delta": tagged_thinking}, ensure_ascii=False),
                        }
                    if answer_delta:
                        full_answer += answer_delta
                        yield {
                            "event": "generation",
                            "data": json.dumps({"delta": answer_delta}, ensure_ascii=False),
                        }
                await asyncio.sleep(0)

            # 流结束：兜底刷出残留 thinking
            flush_thinking = parser.flush()
            if flush_thinking:
                full_thinking += flush_thinking

            # 4. 完成事件前持久化本轮消息
            retrieved_docs, _ = _retrieve_to_response(results, req.top_n)
            await _persist_turn(
                req.session_id,
                req.query,
                full_answer,
                full_thinking,
                retrieved_docs,
                len(history),
            )
            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "answer": full_answer,
                        "thinking": full_thinking,
                        "has_thinking": bool(full_thinking),
                        "session_id": req.session_id,
                        "retrieved_docs": [d.model_dump() for d in retrieved_docs],
                        "usage": {},
                    },
                    ensure_ascii=False,
                ),
            }

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)}, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@app.post("/api/v1/index", response_model=IndexResponse)
async def index(req: IndexRequest, background_tasks: BackgroundTasks):
    """触发索引重建（异步）"""
    job_id = f"idx-{uuid.uuid4().hex[:8]}"
    started_at = datetime.utcnow().isoformat()

    job = IndexResponse(
        job_id=job_id,
        status="pending",
        started_at=started_at,
    )
    _index_jobs[job_id] = job

    background_tasks.add_task(
        _do_index,
        job_id=job_id,
        source_dir=req.source_dir or settings.raw_data_dir,
        force_rebuild=req.force_rebuild,
        chunk_size=req.chunk_size,
        chunk_overlap=req.chunk_overlap,
    )

    return job


def _do_index(
    job_id: str,
    source_dir: str,
    force_rebuild: bool,
    chunk_size: int | None,
    chunk_overlap: int | None,
):
    """后台索引任务"""
    job = _index_jobs[job_id]
    try:
        job.status = "running"

        # 1. 加载
        docs = load_markdown_dir(Path(source_dir))

        # 2. 切分
        chunks = split_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # 3. 写入向量库
        vs = get_vector_store_instance()
        if force_rebuild:
            vs.reset()

        n = vs.add(chunks)

        # 4. 更新任务
        job.total_docs = len(docs)
        job.total_chunks = n
        job.status = "completed"
        job.finished_at = datetime.utcnow().isoformat()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.finished_at = datetime.utcnow().isoformat()


@app.get("/api/v1/index/{job_id}", response_model=IndexResponse)
async def get_index_status(job_id: str):
    """查询索引状态"""
    if job_id not in _index_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} 不存在")
    return _index_jobs[job_id]


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    components = {}
    vs = get_vector_store_instance()
    try:
        components["vector_store"] = "ok"
        count = vs.count()
    except Exception:
        components["vector_store"] = "error"
        count = 0

    try:
        from ..llm import get_llm

        get_llm()
        if settings.llm_provider == "ollama":
            components["llm_api"] = f"ollama:{settings.llm_model}"
        elif settings.llm_api_key:
            components["llm_api"] = f"{settings.llm_provider}:configured"
        else:
            components["llm_api"] = "missing_key"
    except Exception:
        components["llm_api"] = "error"

    try:
        # 检查 Ollama 是否可达
        import httpx
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
        components["ollama"] = "ok" if response.status_code == 200 else "error"
    except Exception:
        components["ollama"] = "unreachable"

    return HealthResponse(
        status="ok",
        components=components,
        version="0.1.0",
        vector_count=count,
    )


@app.get("/")
async def root():
    return {
        "name": "GameGuide AI",
        "version": "0.1.0",
        "docs": "/docs",
    }


# 注册 session 路由
app.include_router(sessions_router, prefix="/api/v1")

# 注册 LangGraph 路由（Feature Flag 控制）
if settings.use_langgraph:
    from .graph_routes import router as graph_router
    app.include_router(graph_router, prefix="/api/v1")
    logger.info("LangGraph routes enabled")
else:
    logger.info("LangGraph routes disabled (USE_LANGGRAPH=false)")