"""Session 持久化层 — SQLite + SQLAlchemy 异步

为什么选 SQLite + 异步 ORM：
- 零运维，文件存储
- 异步 I/O 不阻塞 FastAPI
- SQLAlchemy 2.0 类型安全，迁移到 Postgres 只需改连接字符串

演进路径：
  Phase 1.5: SQLite (本文件)
  Phase 2:   + Redis 缓存热 session
  Phase 3:   迁移到 PostgreSQL + pgvector
"""