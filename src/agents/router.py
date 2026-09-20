"""Router 节点

根据查询复杂度决定路由：
- simple_factual → Direct RAG（Phase 3 的 Modular RAG）
- complex/analytical → Agentic RAG（ReAct Agent）
"""

from __future__ import annotations

from loguru import logger

from ..llm import get_llm


async def router_node(state: dict) -> dict:
    """路由决策节点"""
    query = state.get("query", "")

    if not query:
        logger.warning("[Router] Empty query, defaulting to direct_rag")
        return {"route": "direct_rag", "query_type": "simple"}

    # 启发式分类（快速）
    query_type = _heuristic_classify(query)
    logger.info(f"[Router] Query classified as: {query_type}")

    # 路由映射
    if query_type in ["simple_factual", "ambiguous"]:
        route = "direct_rag"
    elif query_type in ["complex_analytical", "multi_hop", "comparison"]:
        route = "agentic_rag"
    else:
        route = "direct_rag"  # 默认

    logger.info(f"[Router] Route decision: {route}")

    return {
        "query_type": query_type,
        "route": route,
    }


def _heuristic_classify(query: str) -> str:
    """启发式分类查询类型"""
    query_lower = query.lower()

    # 1. 对比查询（需要多步检索 + 对比）
    if any(kw in query_lower for kw in ["哪个", "对比", "vs", "还是", "更好", "区别"]):
        return "comparison"

    # 2. 复杂分析查询
    if any(kw in query_lower for kw in ["为什么", "怎么会", "原因", "分析", "评价"]):
        return "complex_analytical"

    # 3. 多跳查询（需要多步推理）
    if any(kw in query_lower for kw in ["然后", "之后", "接下来", "还有", "另外"]):
        return "multi_hop"

    # 4. 模糊查询
    if len(query) < 5 or query_lower in ["怎么玩", "怎么办", "bug", "问题"]:
        return "ambiguous"

    # 5. 简单事实查询（默认）
    return "simple_factual"


async def llm_classify_query(query: str) -> str:
    """使用 LLM 分类查询（可选，更准确但慢）"""
    llm = get_llm()

    prompt = f"""你是一个查询分类器。请判断以下查询属于哪种类型：

1. simple_factual: 简单事实查询（如"妖刀姬的连招是什么"）
2. comparison: 对比查询（如"妖刀姬和红蝶哪个更好"）
3. complex_analytical: 复杂分析查询（如"为什么 S13 削弱妖刀姬"）
4. multi_hop: 多跳推理查询（如"妖刀姬的连招是什么，然后在副本里怎么站位"）
5. ambiguous: 模糊查询（如"怎么玩"）

查询：{query}

只回复类型名称，不要其他内容。
"""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    result = response.content.strip().lower()

    # 提取类型
    for query_type in ["simple_factual", "comparison", "complex_analytical", "multi_hop", "ambiguous"]:
        if query_type in result:
            return query_type

    return "simple_factual"  # 默认
