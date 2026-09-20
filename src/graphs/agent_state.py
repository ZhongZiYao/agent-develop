"""Agentic RAG State Definition

扩展 RAGState，支持 Agent 循环所需的额外字段：
- agent_scratchpad: Agent 思考和行动的历史记录
- iterations: 当前迭代次数
- tools_used: 已使用的工具列表
- reflection: 反思记录
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Agent State (扩展自 RAGState)"""

    # ===== 基础字段（继承自 RAGState）=====
    query: str  # 用户查询
    game: str  # 游戏名（可选）
    session_id: str  # 会话 ID
    messages: Annotated[list, add_messages]  # 对话历史

    # ===== 检索相关 =====
    retrieved_docs: list[dict]  # 检索到的文档
    keywords: list[str]  # 提取的关键词
    expanded_queries: list[str]  # 扩展查询

    # ===== 生成相关 =====
    answer: str  # 最终答案
    thinking: str  # 思考过程

    # ===== Agent 特有字段 =====
    agent_scratchpad: list[dict]  # Agent 思考历史 [{thought, action, observation}]
    iterations: int  # 当前迭代次数
    max_iterations: int  # 最大迭代次数
    tools_used: list[str]  # 已使用的工具列表

    # ===== Reflexion 相关 =====
    reflection: str  # 当前步骤的反思
    evaluation_score: float  # 答案质量评分（0-1）
    need_replan: bool  # 是否需要重新规划

    # ===== 路由相关 =====
    query_type: str  # 查询类型（simple/agentic）
    route: str  # 路由目标

    # ===== 规划相关（可选）=====
    plan: list[str]  # 子任务列表
    current_step: int  # 当前执行到第几步

    # ===== Self-RAG（Phase 6.6）=====
    need_retrieval: bool  # 是否需要 RAG 检索
    self_rag_confidence: float  # Self-RAG 判断置信度（0-1）
    self_rag_reason: str  # 判断理由

    # ===== Agent Trace（Phase 6.7）=====
    trace_events: list[dict]  # 所有节点的 trace 事件（时间线）
