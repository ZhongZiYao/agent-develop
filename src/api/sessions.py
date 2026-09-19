"""Session REST API"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..storage.session_store import SessionStore, get_session_store


router = APIRouter(prefix="/sessions", tags=["sessions"])


# ===== Pydantic Schema =====

class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    metadata: Optional[dict] = None


class SessionRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class MessageAppend(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    thinking: Optional[str] = None
    retrieved_docs: Optional[list] = None


# ===== 路由 =====

@router.get("", response_model=list[dict])
async def list_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    store: SessionStore = Depends(get_session_store),
):
    """列出所有会话（按 updated_at 倒序）"""
    return await store.list_sessions(limit=limit, offset=offset, search=search)


@router.post("", response_model=dict, status_code=201)
async def create_session(
    body: SessionCreate,
    store: SessionStore = Depends(get_session_store),
):
    """新建会话"""
    return await store.create_session(title=body.title, metadata=body.metadata)


@router.get("/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    """获取会话详情（含所有消息）"""
    result = await store.get_session(session_id, include_messages=True)
    if not result:
        raise HTTPException(status_code=404, detail=f"Session {session_id} 不存在")
    return result


@router.patch("/{session_id}", response_model=dict)
async def rename_session(
    session_id: str,
    body: SessionRename,
    store: SessionStore = Depends(get_session_store),
):
    """重命名会话"""
    success = await store.rename_session(session_id, body.title)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} 不存在")
    return await store.get_session(session_id, include_messages=True)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    """删除会话（级联删除消息）"""
    success = await store.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} 不存在")
    return None


@router.post("/{session_id}/messages", response_model=dict, status_code=201)
async def append_message(
    session_id: str,
    body: MessageAppend,
    store: SessionStore = Depends(get_session_store),
):
    """追加消息"""
    session = await store.get_session(session_id, include_messages=False)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} 不存在")

    return await store.append_message(
        session_id=session_id,
        role=body.role,
        content=body.content,
        thinking=body.thinking,
        retrieved_docs=body.retrieved_docs,
    )