"""Agentic RAG Graph

组装完整的 Agentic RAG 流程：
Router → Direct RAG / Agentic RAG (ReAct Loop)
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from loguru import logger

from ..graphs.agent_state import AgentState
from ..modules import build_graph_from_config
from .react_agent import react_agent_node, should_continue
from .router import router_node


async def build_agentic_rag_graph(
    direct_rag_config: str = "config/rag_modules.yaml",
    max_iterations: int = 5,
) -> StateGraph:
    """构建 Agentic RAG Graph

    Args:
        direct_rag_config: Direct RAG 配置文件路径
        max_iterations: Agent 最大迭代次数

    Returns:
        编译后的 StateGraph
    """
    graph = StateGraph(AgentState)

    # 1. 添加 Router 节点
    graph.add_node("router", router_node)

    # 2. 添加 Direct RAG 节点（Phase 3 的 Modular RAG）
    direct_rag_graph = await build_graph_from_config(direct_rag_config)

    async def direct_rag_node(state: AgentState) -> dict:
        """Direct RAG 节点包装"""
        logger.info("[DirectRAG] Using modular RAG pipeline")
        result = await direct_rag_graph.ainvoke(state)
        return {
            "answer": result.get("answer", ""),
            "thinking": result.get("thinking", ""),
            "retrieved_docs": result.get("retrieved_docs", []),
        }

    graph.add_node("direct_rag", direct_rag_node)

    # 3. 添加 Agentic RAG 节点（ReAct Loop）
    async def agentic_rag_node(state: AgentState) -> dict:
        """Agentic RAG 节点包装"""
        logger.info("[AgenticRAG] Starting ReAct loop")

        # 初始化 Agent 状态
        if not state.get("agent_scratchpad"):
            state["agent_scratchpad"] = []
        if not state.get("iterations"):
            state["iterations"] = 0
        if not state.get("max_iterations"):
            state["max_iterations"] = max_iterations

        return await react_agent_node(state)

    graph.add_node("agentic_rag", agentic_rag_node)

    # 4. 设置入口点
    graph.set_entry_point("router")

    # 5. 添加条件路由（Router → Direct RAG / Agentic RAG）
    def route_decision(state: AgentState) -> str:
        """路由决策函数"""
        route = state.get("route", "direct_rag")
        logger.info(f"[Graph] Routing to: {route}")
        return route

    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "direct_rag": "direct_rag",
            "agentic_rag": "agentic_rag",
        },
    )

    # 6. Direct RAG 直接结束
    graph.add_edge("direct_rag", END)

    # 7. Agentic RAG 循环或结束
    graph.add_conditional_edges(
        "agentic_rag",
        should_continue,
        {
            "continue": "agentic_rag",  # 循环回自己
            "end": END,
        },
    )

    # 8. 编译
    compiled = graph.compile()
    logger.info("Agentic RAG Graph compiled successfully")

    return compiled


# ===== 便捷函数 =====


async def run_agentic_rag(
    query: str,
    session_id: str = "default",
    max_iterations: int = 5,
) -> dict:
    """便捷函数：运行 Agentic RAG

    Args:
        query: 用户查询
        session_id: 会话 ID
        max_iterations: 最大迭代次数

    Returns:
        结果字典
    """
    graph = await build_agentic_rag_graph(max_iterations=max_iterations)

    input_state = {
        "query": query,
        "session_id": session_id,
        "game": "",
        "messages": [],
        "agent_scratchpad": [],
        "iterations": 0,
        "max_iterations": max_iterations,
    }

    result = await graph.ainvoke(input_state)
    return result
