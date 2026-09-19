"""SessionStore — 会话 CRUD 封装（返回 dict 而非 ORM 对象，避免 lazy load）

所有方法都是 async（接 FastAPI 异步）
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Message, Session


def _session_to_dict(session: Session, message_count: int = 0, messages: list[dict] | None = None) -> dict:
    """ORM -> dict（避免在 to_dict 中触发 lazy load）"""
    return {
        "id": session.id,
        "title": session.title or "新对话",
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "message_count": message_count,
        "messages": messages or [],
    }


def _message_to_dict(msg: Message) -> dict:
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "thinking": msg.thinking,
        "retrieved_docs": msg.retrieved_docs,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


class SessionStore:
    """会话存储 CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ===== Session =====

    async def create_session(self, title: str | None = None, metadata: dict | None = None) -> dict:
        """新建会话"""
        new_id = uuid.uuid4().hex[:12]
        session = Session(id=new_id, title=title, metadata_=metadata)
        self.db.add(session)
        await self.db.commit()
        # expire_on_commit=False 避免访问触发 lazy load
        return _session_to_dict(session, message_count=0, messages=[])

    async def get_session(self, session_id: str, include_messages: bool = False) -> dict | None:
        """获取单个会话"""
        stmt = select(Session).where(Session.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            return None

        messages: list[dict] = []
        message_count = 0

        if include_messages:
            msg_stmt = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at)
            )
            msg_result = await self.db.execute(msg_stmt)
            msgs = list(msg_result.scalars().all())
            messages = [_message_to_dict(m) for m in msgs]
            message_count = len(messages)

        return _session_to_dict(session, message_count=message_count, messages=messages)

    async def list_sessions(self, limit: int = 50, offset: int = 0, search: str | None = None) -> list[dict]:
        """列出所有会话（按 updated_at 倒序）"""
        stmt = select(Session).order_by(Session.updated_at.desc()).limit(limit).offset(offset)
        if search:
            stmt = stmt.where(Session.title.contains(search))
        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())

        # 批量统计消息数（一次查询）
        count_stmt = (
            select(Message.session_id, func.count(Message.id))
            .group_by(Message.session_id)
        )
        count_result = await self.db.execute(count_stmt)
        counts = dict(count_result.all())

        return [
            _session_to_dict(s, message_count=counts.get(s.id, 0))
            for s in sessions
        ]

    async def rename_session(self, session_id: str, new_title: str) -> bool:
        """重命名会话"""
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(title=new_title, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def touch_session(self, session_id: str) -> None:
        """更新会话的 updated_at"""
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        await self.db.commit()

    async def delete_session(self, session_id: str) -> bool:
        """删除会话（级联删除消息）"""
        stmt = delete(Session).where(Session.id == session_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    # ===== Messages =====

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        thinking: str | None = None,
        retrieved_docs: list | None = None,
    ) -> dict:
        """追加消息并更新 session 的 updated_at"""
        new_id = uuid.uuid4().hex[:12]
        msg = Message(
            id=new_id,
            session_id=session_id,
            role=role,
            content=content,
            thinking=thinking,
            retrieved_docs=retrieved_docs,
        )
        self.db.add(msg)
        await self.db.flush()
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        await self.db.commit()
        return _message_to_dict(msg)

    async def get_messages(
        self,
        session_id: str,
        limit: int | None = None,
        from_the_end: bool = False,
    ) -> list[dict]:
        """获取会话的消息（返回 dict）"""
        stmt = select(Message).where(Message.session_id == session_id)
        if from_the_end:
            stmt = stmt.order_by(Message.created_at.desc())
        else:
            stmt = stmt.order_by(Message.created_at)
        if limit:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        msgs = list(result.scalars().all())
        if from_the_end:
            msgs.reverse()
        return [_message_to_dict(m) for m in msgs]


async def get_session_store() -> SessionStore:
    """FastAPI 依赖：获取 SessionStore"""
    from .database import AsyncSessionLocal

    db = AsyncSessionLocal()
    try:
        yield SessionStore(db)
    finally:
        await db.close()