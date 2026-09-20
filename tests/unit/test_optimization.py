"""性能优化测试

测试并行、缓存和批量处理
"""

import time

import pytest

from src.agents.optimization import (
    AsyncLRUCache,
    batch_retrieve,
    benchmark_parallel_vs_serial,
    clear_all_caches,
    get_cache_stats,
    parallel_tool_calls,
)


class TestAsyncLRUCache:
    """测试异步 LRU 缓存"""

    def test_cache_set_and_get(self):
        """测试设置和获取"""
        cache = AsyncLRUCache(maxsize=10, ttl=60)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        print(f"\n✅ Cache set and get works")

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = AsyncLRUCache(maxsize=10, ttl=60)

        assert cache.get("nonexistent") is None

        print(f"\n✅ Cache miss handled")

    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = AsyncLRUCache(maxsize=10, ttl=1)  # 1 秒过期

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # 等待过期
        time.sleep(1.1)
        assert cache.get("key1") is None

        print(f"\n✅ Cache expiration works")

    def test_cache_lru_eviction(self):
        """测试 LRU 淘汰"""
        cache = AsyncLRUCache(maxsize=3, ttl=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # 触发淘汰

        # key1 应该被淘汰（最旧）
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

        print(f"\n✅ LRU eviction works")

    def test_cache_stats(self):
        """测试缓存统计"""
        cache = AsyncLRUCache(maxsize=10, ttl=60)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.stats()
        assert stats["size"] == 2
        assert stats["maxsize"] == 10
        assert stats["ttl"] == 60

        print(f"\n✅ Cache stats works")
        print(f"   Stats: {stats}")


class TestParallelExecution:
    """测试并行执行"""

    @pytest.mark.asyncio
    async def test_parallel_tool_calls(self):
        """测试并行工具调用"""
        tool_calls = [
            {"tool": "rag_search", "args": {"query": "妖刀姬", "top_k": 5}},
            {"tool": "rag_search", "args": {"query": "红蝶", "top_k": 5}},
        ]

        start = time.time()
        results = await parallel_tool_calls(tool_calls)
        elapsed = time.time() - start

        assert len(results) == 2
        assert all(r["success"] for r in results)

        print(f"\n✅ Parallel tool calls work")
        print(f"   Tools: {len(tool_calls)}")
        print(f"   Time: {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_benchmark_parallel_vs_serial(self):
        """测试并行 vs 串行性能对比"""
        queries = ["妖刀姬", "红蝶", "素问"]

        result = await benchmark_parallel_vs_serial(queries)

        assert result["queries"] == 3
        assert result["parallel_time"] > 0
        assert result["serial_time"] > 0
        assert result["speedup"] > 0

        print(f"\n✅ Parallel vs Serial benchmark")
        print(f"   Queries: {result['queries']}")
        print(f"   Serial: {result['serial_time']:.2f}s")
        print(f"   Parallel: {result['parallel_time']:.2f}s")
        print(f"   Speedup: {result['speedup']:.2f}x")


class TestBatchProcessing:
    """测试批量处理"""

    @pytest.mark.asyncio
    async def test_batch_retrieve(self):
        """测试批量检索"""
        queries = ["妖刀姬", "红蝶", "素问", "茨木童子", "酒吞童子"]

        start = time.time()
        results = await batch_retrieve(queries, batch_size=2)
        elapsed = time.time() - start

        assert len(results) == len(queries)
        assert all(isinstance(r, list) for r in results)

        print(f"\n✅ Batch retrieve works")
        print(f"   Queries: {len(queries)}")
        print(f"   Time: {elapsed:.2f}s")


class TestCacheManagement:
    """测试缓存管理"""

    def test_get_cache_stats(self):
        """测试获取缓存统计"""
        stats = get_cache_stats()

        assert "retrieval_cache" in stats
        assert "llm_cache" in stats

        print(f"\n✅ Cache stats retrieval works")
        print(f"   Retrieval cache: {stats['retrieval_cache']}")
        print(f"   LLM cache: {stats['llm_cache']}")

    def test_clear_all_caches(self):
        """测试清空缓存"""
        clear_all_caches()

        stats = get_cache_stats()
        assert stats["retrieval_cache"]["size"] == 0
        assert stats["llm_cache"]["size"] == 0

        print(f"\n✅ Clear all caches works")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
