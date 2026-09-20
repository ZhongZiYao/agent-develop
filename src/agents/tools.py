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


async def calculate_tool(expression: str) -> dict:
    """计算工具

    Args:
        expression: 数学表达式（如 "1.2 * 100"）

    Returns:
        计算结果
    """
    logger.info(f"[calculate] Evaluating: {expression}")

    try:
        # 安全的数学计算（仅支持基本运算符）
        import ast
        import operator

        # 支持的运算符
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return ops[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return ops[type(node.op)](eval_expr(node.operand))
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")

        result = eval_expr(ast.parse(expression, mode='eval').body)
        logger.info(f"[calculate] Result: {result}")

        return {"result": result, "expression": expression}

    except Exception as e:
        logger.error(f"[calculate] Failed: {e}")
        return {"error": str(e), "expression": expression}


async def summarize_tool(docs: list[dict], aspect: str = "全面总结") -> str:
    """总结工具

    Args:
        docs: 文档列表
        aspect: 总结角度

    Returns:
        总结文本
    """
    logger.info(f"[summarize] Summarizing {len(docs)} docs on aspect: {aspect}")

    from ..llm import get_llm

    llm = get_llm()

    # 拼接文档内容
    content = "\n\n---\n\n".join([doc.get("content", "") for doc in docs[:5]])

    prompt = f"""请从"{aspect}"角度总结以下内容：

{content[:2000]}...

总结要求：
- 简洁明了（3-5 句话）
- 突出重点
- 保持客观
"""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    summary = response.content.strip()

    logger.info(f"[summarize] Summary generated: {len(summary)} chars")
    return summary


async def web_search_tool(query: str, num_results: int = 3) -> list[dict]:
    """Web 搜索工具

    Args:
        query: 搜索查询
        num_results: 返回结果数量

    Returns:
        搜索结果列表 [{title, url, snippet}]
    """
    logger.info(f"[web_search] Searching: {query}")

    # 简化版：返回模拟结果
    # 实际可以接入：Google Custom Search API, Bing API, DuckDuckGo
    results = [
        {
            "title": f"搜索结果 {i+1}: {query}",
            "url": f"https://example.com/result{i+1}",
            "snippet": f"这是关于 {query} 的搜索结果摘要...",
        }
        for i in range(num_results)
    ]

    logger.info(f"[web_search] Found {len(results)} results")
    return results


async def code_execution_tool(code: str, language: str = "python") -> dict:
    """代码执行工具（安全沙箱）

    Args:
        code: 要执行的代码
        language: 编程语言（目前仅支持 python）

    Returns:
        执行结果 {output, error, success}
    """
    logger.info(f"[code_execution] Executing {language} code: {code[:50]}...")

    if language != "python":
        return {"error": f"Unsupported language: {language}", "success": False}

    try:
        import io
        import sys
        from contextlib import redirect_stdout

        # 捕获输出
        output_buffer = io.StringIO()

        # 安全限制：禁止危险操作
        safe_builtins = {
            "print": print,
            "range": range,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "sum": sum,
            "max": max,
            "min": min,
            "abs": abs,
            "round": round,
        }

        # 执行代码（限制 namespace）
        with redirect_stdout(output_buffer):
            exec(code, {"__builtins__": safe_builtins}, {})

        output = output_buffer.getvalue()
        logger.info(f"[code_execution] Success: {output[:100]}...")

        return {
            "output": output,
            "error": None,
            "success": True,
        }

    except Exception as e:
        logger.error(f"[code_execution] Failed: {e}")
        return {
            "output": "",
            "error": str(e),
            "success": False,
        }


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
        name="calculate",
        description="执行数学计算。适用于伤害计算、性价比分析等。输入：expression（数学表达式，如 '1.2 * 100'）",
        func=calculate_tool,
    ),
    Tool(
        name="summarize",
        description="总结多个文档的内容。适用于信息整合。输入：docs（文档列表）, aspect（总结角度）",
        func=summarize_tool,
    ),
    Tool(
        name="web_search",
        description="搜索网络上的最新信息（超出知识库范围）。适用于版本更新、最新攻略等。输入：query, num_results",
        func=web_search_tool,
    ),
    Tool(
        name="code_execution",
        description="执行 Python 代码进行计算或数据处理。适用于复杂计算、数据分析。输入：code（Python 代码）",
        func=code_execution_tool,
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
