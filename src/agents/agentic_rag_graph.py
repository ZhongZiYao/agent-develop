"""Agentic RAG Graph

组装完整的 Agentic RAG 流程：
Router → Direct RAG / Agentic RAG (ReAct Loop + Reflexion)
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from loguru import logger

from ..graphs.agent_state import AgentState
from ..modules import build_graph_from_config
from .react_agent import react_agent_node, should_continue
from .reflexion import evaluator_node, replan_node
from .router import router_node


async def build_agentic_rag_graph(
    direct_rag_config: str = "config/rag_modules.yaml",
    max_iterations: int = 5,
    enable_reflexion: bool = True,
) -> StateGraph:
    """构建 Agentic RAG Graph

    Args:
        direct_rag_config: Direct RAG 配置文件路径
        max_iterations: Agent 最大迭代次数
        enable_reflexion: 是否启用 Reflexion 自我纠错

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

    # 4. 添加 Evaluator 节点（Reflexion）
    if enable_reflexion:
        graph.add_node("evaluator", evaluator_node)
        graph.add_node("replan", replan_node)

    # 5. 设置入口点
    graph.set_entry_point("router")

    # 6. 添加条件路由（Router → Direct RAG / Agentic RAG）
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

    # 7. Direct RAG 直接结束
    graph.add_edge("direct_rag", END)

    # 8. Agentic RAG 循环或评估
    if enable_reflexion:
        # 启用 Reflexion：agentic_rag → continue/evaluate
        graph.add_conditional_edges(
            "agentic_rag",
            should_continue,
            {
                "continue": "agentic_rag",  # 继续循环
                "end": "evaluator",  # 进入评估
            },
        )

        # evaluator → end/replan
        def evaluate_decision(state: AgentState) -> str:
            """评估决策"""
            need_replan = state.get("need_replan", False)
            if need_replan:
                logger.warning("[Graph] Quality low, replanning...")
                return "replan"
            else:
                logger.info("[Graph] Quality acceptable, ending")
                return "end"

        graph.add_conditional_edges(
            "evaluator",
            evaluate_decision,
            {
                "replan": "replan",
                "end": END,
            },
        )

        # replan → agentic_rag (重新开始)
        graph.add_edge("replan", "agentic_rag")
    else:
        # 不启用 Reflexion：直接循环或结束
        graph.add_conditional_edges(
            "agentic_rag",
            should_continue,
            {
                "continue": "agentic_rag",
                "end": END,
            },
        )

    # 9. 编译
    compiled = graph.compile()
    logger.info(f"Agentic RAG Graph compiled (reflexion={enable_reflexion})")

    return compiled


# ===== 便捷函数 =====


async def run_agentic_rag(
    query: str,
    session_id: str = "default",
    max_iterations: int = 5,
    enable_reflexion: bool = True,
) -> dict:
    """便捷函数：运行 Agentic RAG

    Args:
        query: 用户查询
        session_id: 会话 ID
        max_iterations: 最大迭代次数
        enable_reflexion: 是否启用 Reflexion 自我纠错

    Returns:
        结果字典
    """
    graph = await build_agentic_rag_graph(
        max_iterations=max_iterations,
        enable_reflexion=enable_reflexion,
    )

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
