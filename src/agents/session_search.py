"""会话内容搜索

基于 RAG 的会话内容搜索：
1. 用户输入查询
2. 使用当前 RAG 系统搜索历史会话
3. 返回最相关的会话列表

实现思路：
- 把每个会话的内容（messages）作为一个文档
- 用 ChromaDB 或 RAG 检索相似的会话
- 返回最相关的 top_k 个会话
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger


class SessionSearch:
    """会话内容搜索"""

    def __init__(self, vector_store=None):
        """
        Args:
            vector_store: 向量存储实例（可选，如果不提供则按需创建）
        """
        self.vector_store = vector_store
        self._session_index: dict[str, dict] = {}  # session_id -> session_content

    async def index_session(
        self,
        session_id: str,
        title: str,
        messages: list[dict],
    ) -> str:
        """
        将会话内容索引到向量存储

        Args:
            session_id: 会话 ID
            title: 会话标题
            messages: 会话消息列表

        Returns:
            索引文档 ID
        """
        # 构造文档内容（标题 + 消息）
        content_parts = [f"标题：{title}"]
        for msg in messages:
            role = msg.get("role", "")
            text = msg.get("content", "")
            content_parts.append(f"{role}: {text}")

        full_content = "\n\n".join(content_parts)

        # 保存到内存索引（实际生产可以用向量存储）
        self._session_index[session_id] = {
            "id": session_id,
            "title": title,
            "content": full_content,
            "messages": messages,
        }

        return session_id

    async def search(
        self,
        query: str,
        top_k: int = 5,
        vector_store=None,
    ) -> list[dict]:
        """
        基于内容搜索会话

        Args:
            query: 搜索查询
            top_k: 返回前 k 个会话
            vector_store: 向量存储实例（可选）

        Returns:
            匹配的会话列表
        """
        # 简化版：基于关键词匹配
        # 生产版：使用 RAG 的向量搜索

        query_lower = query.lower()
        query_words = set(query_lower.split())

        # 计算每个会话的匹配分数
        scored_sessions = []
        for session_id, session_data in self._session_index.items():
            content_lower = session_data["content"].lower()
            # 计算关键词命中数
            matches = sum(1 for word in query_words if word in content_lower)
            if matches > 0:
                scored_sessions.append({
                    "session_id": session_id,
                    "title": session_data["title"],
                    "score": matches / max(len(query_words), 1),
                    "preview": session_data["content"][:200],
                })

        # 按分数排序
        scored_sessions.sort(key=lambda x: x["score"], reverse=True)

        return scored_sessions[:top_k]

    def get_stats(self) -> dict:
        """获取搜索索引统计"""
        return {
            "indexed_sessions": len(self._session_index),
        }