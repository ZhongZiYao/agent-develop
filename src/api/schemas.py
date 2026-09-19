"""Pydantic v2 Schema — API 请求/响应定义"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """问答请求"""
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    game: Optional[str] = Field(None, description="游戏过滤")
    top_k: int = Field(10, ge=1, le=100)
    top_n: int = Field(5, ge=1, le=20)
    session_id: Optional[str] = Field(None, description="会话 ID（传入则注入历史）")


class RetrievedDoc(BaseModel):
    """单条检索文档"""
    id: str
    title: str
    content: str
    source: str
    score: float
    metadata: dict = {}


class QueryResponse(BaseModel):
    """问答响应"""
    answer: str
    thinking: str = ""  # 模型思考过程（<think>...</think> 剥离出来的）
    has_thinking: bool = False
    retrieved_docs: list[RetrievedDoc]
    citations: list[int] = []
    trace_id: str
    usage: dict = {}
    latency_ms: float
    metadata: dict = {}


class IndexRequest(BaseModel):
    """索引请求"""
    source_dir: Optional[str] = Field(None, description="文档目录（默认 data/raw）")
    force_rebuild: bool = Field(False)
    chunk_size: Optional[int] = Field(None, ge=100, le=2000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=500)


class IndexResponse(BaseModel):
    """索引响应"""
    job_id: str
    status: str
    total_docs: int = 0
    total_chunks: int = 0
    started_at: str
    finished_at: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查"""
    status: str
    components: dict
    version: str
    vector_count: int = 0