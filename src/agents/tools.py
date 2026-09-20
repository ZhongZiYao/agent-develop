"""Agentic RAG 工具集

提供 Agent 可调用的工具：
1. rag_search: 从知识库检索信息
2. compare: 对比两个实体
3. finish: 结束并返回答案
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from ..modules import HybridRetrieverModule


class Tool:
    """工具基类"""

    def __init__(self, name: str, description: str, func: callable):
        self.name = name
        self.description = description
        self.func = func

    async def run(self, **kwargs) -> Any:
        """执行工具"""
        return await self.func(**kwargs)

    def __repr__(self) -> str:
        return f"Tool(name={self.name})"


# ===== 工具实现 =====


async def rag_search_tool(query: str, top_k: int = 10) -> list[dict]:
    """RAG 检索工具

    Args:
        query: 检索查询
        top_k: 返回前 k 个结果

    Returns:
        检索到的文档列表
    """
    logger.info(f"[rag_search] Searching: {query}")

    retriever = HybridRetrieverModule({"vector_top_k": top_k, "use_expanded": False})
    result = await retriever({"query": query})

    docs = result.get("retrieved_docs", [])
    logger.info(f"[rag_search] Found {len(docs)} documents")

    return docs


async def compare_tool(entity_a: str, entity_b: str, aspect: str = "全面对比") -> str:
    """对比工具

    Args:
        entity_a: 实体 A
        entity_b: 实体 B
        aspect: 对比维度

    Returns:
        对比结果
    """
    logger.info(f"[compare] Comparing {entity_a} vs {entity_b} on {aspect}")

    # 分别检索两个实体
    docs_a = await rag_search_tool(entity_a, top_k=5)
    docs_b = await rag_search_tool(entity_b, top_k=5)

    # 简化版：返回检索到的信息
    comparison = {
        "entity_a": entity_a,
        "entity_b": entity_b,
        "aspect": aspect,
        "docs_a": docs_a,
        "docs_b": docs_b,
    }

    logger.info(f"[compare] Comparison completed")
    return comparison


async def finish_tool(answer: str) -> dict:
    """结束工具

    Args:
        answer: 最终答案

    Returns:
        结束信号
    """
    logger.info(f"[finish] Agent finished with answer: {answer[:100]}...")
    return {"type": "finish", "answer": answer}


# ===== 工具注册表 =====

AGENT_TOOLS = [
    Tool(
        name="rag_search",
        description="从知识库检索相关信息。适用于查找角色属性、技能描述、攻略等。输入：query（检索查询）",
        func=rag_search_tool,
    ),
    Tool(
        name="compare",
        description="对比两个实体（如角色、装备）。适用于'哪个更好'类问题。输入：entity_a, entity_b, aspect（对比维度）",
        func=compare_tool,
    ),
    Tool(
        name="finish",
        description="结束任务并返回最终答案。当你已经收集足够信息且能回答用户问题时使用。输入：answer（最终答案）",
        func=finish_tool,
    ),
]


def get_tool_by_name(name: str) -> Tool | None:
    """根据名字获取工具"""
    for tool in AGENT_TOOLS:
        if tool.name == name:
            return tool
    return None


def get_tools_description() -> str:
    """获取所有工具的描述（用于 LLM Prompt）"""
    descriptions = []
    for tool in AGENT_TOOLS:
        descriptions.append(f"- {tool.name}: {tool.description}")
    return "\n".join(descriptions)
