"""Memory 机制测试

测试失败经验记录和检索
"""

import pytest

from src.agents.memory import (
    MemoryEntry,
    MemoryStore,
    add_failure_memory,
    get_memory_store,
    retrieve_similar_memories,
)


class TestMemory:
    """测试 Memory 机制"""

    def setup_method(self):
        """每个测试前清空 Memory"""
        store = get_memory_store()
        store.clear()

    @pytest.mark.asyncio
    async def test_add_and_retrieve_memory(self):
        """测试添加和检索 Memory"""
        # 添加失败经验
        await add_failure_memory(
            query="妖刀姬和红蝶哪个更好？",
            error_type="insufficient_info",
            scratchpad=[
                {
                    "iteration": 1,
                    "action": {"tool": "rag_search", "args": {"query": "妖刀姬"}},
                }
            ],
            solution="应该同时检索两个角色再对比",
        )

        # 检索相似 Memory
        memories = await retrieve_similar_memories("妖刀姬和红蝶对比", top_k=1)

        assert len(memories) > 0
        assert "妖刀姬" in memories[0]["query"]
        assert memories[0]["error_type"] == "insufficient_info"
        assert "应该同时检索" in memories[0]["solution"]

        print(f"✅ Memory added and retrieved")
        print(f"   Query: {memories[0]['query']}")
        print(f"   Solution: {memories[0]['solution']}")

    @pytest.mark.asyncio
    async def test_memory_search_similarity(self):
        """测试 Memory 相似度搜索"""
        # 添加多个失败经验
        await add_failure_memory(
            query="妖刀姬连招是什么？",
            error_type="wrong_tool",
            scratchpad=[],
            solution="应该用 rag_search 而不是 calculate",
        )

        await add_failure_memory(
            query="红蝶技能介绍",
            error_type="insufficient_info",
            scratchpad=[],
            solution="需要检索更多文档",
        )

        # 检索与"妖刀姬"相关的 Memory
        memories = await retrieve_similar_memories("妖刀姬怎么玩", top_k=2)

        assert len(memories) > 0
        # 第一个应该是关于妖刀姬的
        assert "妖刀姬" in memories[0]["query"]

        print(f"✅ Memory similarity search works")
        print(f"   Found {len(memories)} similar memories")

    @pytest.mark.asyncio
    async def test_memory_persistence(self):
        """测试 Memory 持久化"""
        # 添加 Memory
        await add_failure_memory(
            query="测试持久化",
            error_type="test",
            scratchpad=[],
            solution="测试解决方案",
        )

        # 创建新的 MemoryStore（模拟重启）
        store = MemoryStore(storage_path="data/agent_memory.json")
        memories = store.search("测试持久化", top_k=1)

        assert len(memories) > 0
        assert memories[0].query == "测试持久化"

        print(f"✅ Memory persists across restarts")

    def test_memory_store_clear(self):
        """测试清空 Memory"""
        store = get_memory_store()

        # 添加一些 Memory
        store.add(MemoryEntry("query1", "error1", []))
        store.add(MemoryEntry("query2", "error2", []))

        assert len(store.memories) >= 2

        # 清空
        store.clear()

        assert len(store.memories) == 0

        print(f"✅ Memory store cleared")

    @pytest.mark.asyncio
    async def test_empty_memory_search(self):
        """测试空 Memory 搜索"""
        # 清空 Memory
        store = get_memory_store()
        store.clear()

        # 搜索
        memories = await retrieve_similar_memories("任意查询", top_k=1)

        assert len(memories) == 0

        print(f"✅ Empty memory search handled")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
