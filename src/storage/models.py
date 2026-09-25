"""SQLAlchemy 模型 — Session / Message / UserProfile

表设计：
- sessions：会话元数据（id / title / 时间）
- messages：消息内容（含 thinking / retrieved_docs）
- user_profiles：用户偏好（Phase 5.5 才用）
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def new_uuid() -> str:
    return uuid.uuid4().hex[:12]


def _iso_utc(dt: datetime | None) -> str | None:
    """序列化 datetime 为带 UTC 时区的 ISO 字符串。

    背景：datetime.utcnow() 产生的 naive datetime 经 isoformat() 后无时区后缀，
    前端 new Date() 会按本地时区解析，导致 UTC+8 区域会话显示偏差 8 小时。
    修复：强制追加 '+00:00' 让前端按 UTC 解析。
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.isoformat()
    return dt.replace(tzinfo=timezone.utc).isoformat()


class Session(Base):
    """会话表"""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_uuid)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def to_dict(self, include_messages: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title or "新对话",
            "created_at": _iso_utc(self.created_at),
            "updated_at": _iso_utc(self.updated_at),
            "message_count": len(self.messages) if self.messages else 0,
        }
        if include_messages:
            data["messages"] = [m.to_dict() for m in self.messages]
        return data


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # user / assistant
    content: Mapped[str] = mapped_column(Text)
    thinking: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_docs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship("Session", back_populates="messages")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "thinking": self.thinking,
            "retrieved_docs": self.retrieved_docs,
            "created_at": _iso_utc(self.created_at),
        }


class UserProfile(Base):
    """用户偏好表（Phase 5.5 才用）"""
    __tablename__ = "user_profiles"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )