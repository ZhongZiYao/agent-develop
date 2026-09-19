"""RAG Graph 构建和编译

导出编译好的 rag_graph 供 API 层使用。
"""

from pathlib import Path

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph, END

from .nodes import retrieve_node, generate_node
from .rag_state import RAGState


def create_rag_workflow() -> StateGraph:
    """创建 RAG 工作流"""
    workflow = StateGraph(RAGState)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow


def _get_db_path() -> Path:
    """获取 Checkpoint 数据库路径"""
    from ..storage.database import DB_PATH
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


# ===== 全局连接 + Graph 单例 =====
# AsyncSqliteSaver 需要绑定到 aiosqlite.Connection。
# 全局连接在第一次 get_rag_graph_async 时建立，整个进程复用。
# 注意：pytest-asyncio 每个 test 用独立 event loop，会导致旧连接失效。
# 解决：在 close_checkpointer 里重置所有全局状态，下次调用重新建立。
_global_connection: aiosqlite.Connection | None = None
_global_saver: AsyncSqliteSaver | None = None
_compiled_graph = None


async def init_checkpointer() -> AsyncSqliteSaver:
    """初始化 Checkpointer（全局单例，应用启动时调用一次）

    使用 file URI 解决 Windows 路径问题。
    """
    global _global_connection, _global_saver

    if _global_saver is not None:
        return _global_saver

    db_path = _get_db_path().absolute()
    # 使用 file URI 让 sqlite3 正确解析 Windows 路径
    db_uri = f"file:{db_path.as_posix()}?mode=rwc"

    # 建立全局连接（应用生命周期内保持）
    _global_connection = await aiosqlite.connect(db_uri, uri=True)

    # 确保表已创建
    await _global_connection.executescript("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            parent_checkpoint_id TEXT,
            type TEXT,
            checkpoint BLOB,
            metadata BLOB,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        );
        CREATE TABLE IF NOT EXISTS writes (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            idx INTEGER NOT NULL,
            channel TEXT NOT NULL,
            type TEXT,
            value BLOB,
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        );
    """)
    await _global_connection.commit()

    # 创建 saver（绑定到连接）
    _global_saver = AsyncSqliteSaver(_global_connection)
    return _global_saver


async def close_checkpointer() -> None:
    """关闭 Checkpointer 并重置全局状态

    pytest-asyncio 每个 test 独立 event loop，
    需要重置全局状态让下次调用重新初始化。
    """
    global _global_connection, _global_saver, _compiled_graph
    if _global_connection is not None:
        try:
            await _global_connection.close()
        except Exception:
            pass
    _global_connection = None
    _global_saver = None
    _compiled_graph = None


async def get_rag_graph_async():
    """获取编译好的 RAG Graph（异步初始化版本）

    首次调用时初始化 checkpointer 和编译 graph。
    已经校验过连接的 event loop 仍然有效，否则自动重置。
    """
    global _compiled_graph, _global_connection, _global_saver

    # 检测连接是否还有效（pytest 多个 test 时 event loop 会变）
    if _global_connection is not None:
        try:
            await _global_connection.execute("SELECT 1")
        except Exception:
            # 连接失效，重置
            _global_connection = None
            _global_saver = None
            _compiled_graph = None

    if _compiled_graph is None:
        saver = await init_checkpointer()
        workflow = create_rag_workflow()
        _compiled_graph = workflow.compile(checkpointer=saver)

    return _compiled_graph


# 向后兼容：同步接口（仅供测试环境使用）
# 警告：测试中使用必须手动初始化 saver
def get_rag_graph_for_test():
    """仅用于测试：同步获取 graph，假定 saver 已初始化"""
    global _compiled_graph
    if _compiled_graph is None:
        raise RuntimeError(
            "请先调用 await init_checkpointer() 或 get_rag_graph_async()"
        )
    return _compiled_graph