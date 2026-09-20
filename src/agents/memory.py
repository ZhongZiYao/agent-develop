"""Memory 机制

让 Agent 从失败中学习，避免重复错误。

核心组件：
1. MemoryStore: 持久化存储失败经验
2. MemoryRetrieval: 检索相似失败案例
3. MemoryIntegration: 集成到 ReAct 循环
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from loguru import logger


class MemoryEntry:
    """Memory 条目"""

    def __init__(
        self,
        query: str,
        error_type: str,
        scratchpad: list[dict],
        solution: str = "",
        timestamp: float = None,
    ):
        self.query = query
        self.error_type = error_type  # "wrong_tool", "insufficient_info", "logic_error"
        self.scratchpad = scratchpad
        self.solution = solution
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "error_type": self.error_type,
            "scratchpad": self.scratchpad,
            "solution": self.solution,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(
            query=data["query"],
            error_type=data["error_type"],
            scratchpad=data["scratchpad"],
            solution=data.get("solution", ""),
            timestamp=data.get("timestamp"),
        )


class MemoryStore:
    """Memory 存储（JSON 文件）"""

    def __init__(self, storage_path: str = "data/agent_memory.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memories: list[MemoryEntry] = []
        self._load()

    def _load(self):
        """从文件加载 Memory"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.memories = [MemoryEntry.from_dict(item) for item in data]
                logger.info(f"[MemoryStore] Loaded {len(self.memories)} memories")
            except Exception as e:
                logger.error(f"[MemoryStore] Failed to load memories: {e}")
                self.memories = []
        else:
            logger.info("[MemoryStore] No existing memory file, starting fresh")

    def _save(self):
        """保存 Memory 到文件"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                data = [mem.to_dict() for mem in self.memories]
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"[MemoryStore] Saved {len(self.memories)} memories")
        except Exception as e:
            logger.error(f"[MemoryStore] Failed to save memories: {e}")

    def add(self, memory: MemoryEntry):
        """添加新的 Memory"""
        self.memories.append(memory)
        self._save()
        logger.info(f"[MemoryStore] Added memory for query: {memory.query[:50]}...")

    def search(self, query: str, top_k: int = 3) -> list[MemoryEntry]:
        """检索相似的 Memory（简单的关键词匹配）"""
        if not self.memories:
            return []

        # 简单的关键词匹配评分
        scores = []
        query_lower = query.lower()

        for mem in self.memories:
            mem_query_lower = mem.query.lower()

            # 计算相似度（简化版）
            common_words = set(query_lower.split()) & set(mem_query_lower.split())
            score = len(common_words) / max(len(query_lower.split()), 1)

            scores.append((score, mem))

        # 按分数排序
        scores.sort(key=lambda x: x[0], reverse=True)

        # 返回 top_k
        results = [mem for score, mem in scores[:top_k] if score > 0.1]

        if results:
            logger.info(f"[MemoryStore] Found {len(results)} similar memories for: {query[:50]}...")

        return results

    def clear(self):
        """清空所有 Memory"""
        self.memories = []
        self._save()
        logger.info("[MemoryStore] Cleared all memories")


# ===== 全局 Memory Store =====

_global_memory_store = None


def get_memory_store() -> MemoryStore:
    """获取全局 Memory Store（单例）"""
    global _global_memory_store
    if _global_memory_store is None:
        _global_memory_store = MemoryStore()
    return _global_memory_store


# ===== Memory 集成函数 =====


async def add_failure_memory(
    query: str,
    error_type: str,
    scratchpad: list[dict],
    solution: str = "",
):
    """添加失败经验到 Memory

    Args:
        query: 用户查询
        error_type: 错误类型（wrong_tool, insufficient_info, logic_error）
        scratchpad: Agent 执行历史
        solution: 解决方案（可选）
    """
    memory = MemoryEntry(
        query=query,
        error_type=error_type,
        scratchpad=scratchpad,
        solution=solution,
    )

    store = get_memory_store()
    store.add(memory)


async def retrieve_similar_memories(query: str, top_k: int = 3) -> list[dict]:
    """检索相似的失败经验

    Args:
        query: 当前查询
        top_k: 返回前 k 个

    Returns:
        Memory 列表（dict 格式）
    """
    store = get_memory_store()
    memories = store.search(query, top_k=top_k)

    return [
        {
            "query": mem.query,
            "error_type": mem.error_type,
            "solution": mem.solution,
            "scratchpad_summary": _format_scratchpad_summary(mem.scratchpad),
        }
        for mem in memories
    ]


def _format_scratchpad_summary(scratchpad: list[dict]) -> str:
    """格式化 scratchpad 摘要"""
    if not scratchpad:
        return "（无历史）"

    steps = []
    for step in scratchpad[:3]:  # 只显示前 3 步
        action = step.get("action", {})
        steps.append(f"{action.get('tool', 'unknown')}")

    summary = " → ".join(steps)
    if len(scratchpad) > 3:
        summary += f" ... ({len(scratchpad)} steps total)"

    return summary
