"""数据库连接管理

单例 async_engine + Base.metadata.create_all()
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..config import settings
from .models import Base

DB_PATH = Path(settings.chroma_persist_dir).parent / "gameguide.db"
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# 确保目录存在
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 引擎（全局单例）
engine = create_async_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=True,
)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """SQLite 默认关闭外键约束，显式开启以保证 session 删除时级联删除 messages。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session 工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """初始化数据库（建表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """FastAPI 依赖：获取异步 session"""
    async with AsyncSessionLocal() as session:
        yield session