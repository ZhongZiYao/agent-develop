"""性能优化模块

实现：
1. 并行工具调用（asyncio.gather）
2. LRU 缓存（检索结果、LLM 响应）
3. 批量处理优化
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from functools import lru_cache
from typing import Any

from loguru import logger


# ===== 缓存装饰器 =====


class AsyncLRUCache:
    """异步 LRU 缓存"""

    def __init__(self, maxsize: int = 128, ttl: int = 3600):
        """
        Args:
            maxsize: 最大缓存条目数
            ttl: 缓存过期时间（秒）
        """
        self.cache: dict[str, tuple[Any, float]] = {}
        self.maxsize = maxsize
        self.ttl = ttl

    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 将参数序列化为字符串
        key_parts = [func_name, str(args), str(sorted(kwargs.items()))]
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]

        # 检查是否过期
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None

        return value

    def set(self, key: str, value: Any):
        """设置缓存"""
        # LRU 淘汰
        if len(self.cache) >= self.maxsize:
            # 删除最旧的条目
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[key] = (value, time.time())

    def clear(self):
        """清空缓存"""
        self.cache.clear()

    def stats(self) -> dict:
        """缓存统计"""
        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "ttl": self.ttl,
        }


# ===== 全局缓存实例 =====

_retrieval_cache = AsyncLRUCache(maxsize=256, ttl=3600)  # 检索缓存 1 小时
_llm_cache = AsyncLRUCache(maxsize=128, ttl=1800)  # LLM 缓存 30 分钟


def cached_retrieval(func):
    """检索缓存装饰器"""

    async def wrapper(*args, **kwargs):
        # 生成缓存键
        key = _retrieval_cache._make_key(func.__name__, args, kwargs)

        # 尝试从缓存获取
        cached_result = _retrieval_cache.get(key)
        if cached_result is not None:
            logger.debug(f"[Cache] Hit for {func.__name__}")
            return cached_result

        # 执行函数
        logger.debug(f"[Cache] Miss for {func.__name__}")
        result = await func(*args, **kwargs)

        # 存入缓存
        _retrieval_cache.set(key, result)

        return result

    return wrapper


def cached_llm(func):
    """LLM 缓存装饰器"""

    async def wrapper(*args, **kwargs):
        # 生成缓存键
        key = _llm_cache._make_key(func.__name__, args, kwargs)

        # 尝试从缓存获取
        cached_result = _llm_cache.get(key)
        if cached_result is not None:
            logger.debug(f"[Cache] Hit for {func.__name__}")
            return cached_result

        # 执行函数
        logger.debug(f"[Cache] Miss for {func.__name__}")
        result = await func(*args, **kwargs)

        # 存入缓存
        _llm_cache.set(key, result)

        return result

    return wrapper


# ===== 并行工具调用 =====


async def parallel_tool_calls(tool_calls: list[dict]) -> list[dict]:
    """并行执行多个工具调用

    Args:
        tool_calls: [{tool, args}, ...]

    Returns:
        结果列表
    """
    from .tools import get_tool_by_name

    logger.info(f"[Parallel] Executing {len(tool_calls)} tools in parallel")

    async def execute_one(tool_call: dict) -> dict:
        """执行单个工具"""
        tool_name = tool_call.get("tool")
        args = tool_call.get("args", {})

        tool = get_tool_by_name(tool_name)
        if tool is None:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = await tool.run(**args)
            return {"tool": tool_name, "result": result, "success": True}
        except Exception as e:
            logger.error(f"[Parallel] Tool {tool_name} failed: {e}")
            return {"tool": tool_name, "error": str(e), "success": False}

    # 并行执行
    start = time.time()
    results = await asyncio.gather(*[execute_one(tc) for tc in tool_calls])
    elapsed = time.time() - start

    logger.info(f"[Parallel] Completed in {elapsed:.2f}s")

    return results


# ===== 批量处理 =====


async def batch_retrieve(queries: list[str], batch_size: int = 5) -> list[list[dict]]:
    """批量检索

    Args:
        queries: 查询列表
        batch_size: 批次大小

    Returns:
        每个查询的检索结果
    """
    from .tools import rag_search_tool

    logger.info(f"[Batch] Retrieving {len(queries)} queries in batches of {batch_size}")

    results = []

    # 分批处理
    for i in range(0, len(queries), batch_size):
        batch = queries[i : i + batch_size]

        # 并行执行当前批次
        batch_results = await asyncio.gather(*[rag_search_tool(q) for q in batch])
        results.extend(batch_results)

        logger.debug(f"[Batch] Processed batch {i // batch_size + 1}/{(len(queries) - 1) // batch_size + 1}")

    return results


# ===== 缓存管理 =====


def get_cache_stats() -> dict:
    """获取缓存统计"""
    return {
        "retrieval_cache": _retrieval_cache.stats(),
        "llm_cache": _llm_cache.stats(),
    }


def clear_all_caches():
    """清空所有缓存"""
    _retrieval_cache.clear()
    _llm_cache.clear()
    logger.info("[Cache] All caches cleared")


# ===== 性能基准测试 =====


async def benchmark_parallel_vs_serial(queries: list[str]) -> dict:
    """对比并行和串行性能

    Args:
        queries: 测试查询列表

    Returns:
        性能对比结果
    """
    from .tools import rag_search_tool

    # 串行执行
    start = time.time()
    for q in queries:
        await rag_search_tool(q)
    serial_time = time.time() - start

    # 并行执行
    start = time.time()
    await asyncio.gather(*[rag_search_tool(q) for q in queries])
    parallel_time = time.time() - start

    speedup = serial_time / parallel_time if parallel_time > 0 else 0

    return {
        "queries": len(queries),
        "serial_time": serial_time,
        "parallel_time": parallel_time,
        "speedup": speedup,
    }
