"""Multi-Agent 协作系统

实现 Supervisor + Workers 架构：
- Supervisor: 任务分配和结果汇总
- Workers: 专门任务（retrieval, analysis, generation）
- 并行执行优化
"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from ..llm import get_llm


class Worker:
    """Worker Agent 基类"""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.llm = get_llm()

    async def process(self, task: dict) -> dict:
        """处理任务（子类实现）"""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"Worker({self.name}, role={self.role})"


class RetrievalWorker(Worker):
    """检索 Worker"""

    def __init__(self):
        super().__init__(name="retrieval_worker", role="信息检索")

    async def process(self, task: dict) -> dict:
        """执行检索任务"""
        query = task.get("query", "")
        logger.info(f"[{self.name}] Processing retrieval: {query}")

        # 调用 RAG 检索工具
        from ..agents.tools import rag_search_tool

        docs = await rag_search_tool(query, top_k=10)

        return {
            "worker": self.name,
            "task_type": "retrieval",
            "query": query,
            "result": docs,
            "success": True,
        }


class AnalysisWorker(Worker):
    """分析 Worker"""

    def __init__(self):
        super().__init__(name="analysis_worker", role="信息分析")

    async def process(self, task: dict) -> dict:
        """执行分析任务"""
        data = task.get("data", [])
        aspect = task.get("aspect", "全面分析")
        logger.info(f"[{self.name}] Processing analysis: {aspect}")

        # 使用 LLM 分析
        content = "\n\n".join([str(d) for d in data[:5]])

        prompt = f"""请从"{aspect}"角度分析以下信息：

{content[:1500]}...

要求：
- 提炼关键信息
- 突出重点
- 客观准确
"""

        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        analysis = response.content.strip()

        return {
            "worker": self.name,
            "task_type": "analysis",
            "aspect": aspect,
            "result": analysis,
            "success": True,
        }


class GenerationWorker(Worker):
    """生成 Worker"""

    def __init__(self):
        super().__init__(name="generation_worker", role="答案生成")

    async def process(self, task: dict) -> dict:
        """执行生成任务"""
        query = task.get("query", "")
        context = task.get("context", [])
        logger.info(f"[{self.name}] Processing generation for: {query[:50]}...")

        # 拼接上下文
        context_text = "\n\n".join([str(c) for c in context[:3]])

        prompt = f"""基于以下信息回答用户问题。

用户问题：{query}

参考信息：
{context_text}

要求：
- 直接回答问题
- 基于参考信息
- 简洁明了
"""

        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        answer = response.content.strip()

        return {
            "worker": self.name,
            "task_type": "generation",
            "query": query,
            "result": answer,
            "success": True,
        }


class Supervisor:
    """Supervisor Agent - 任务分配和结果汇总"""

    def __init__(self):
        self.llm = get_llm()
        self.workers = {
            "retrieval": RetrievalWorker(),
            "analysis": AnalysisWorker(),
            "generation": GenerationWorker(),
        }

    async def delegate(self, query: str, query_type: str = "simple") -> dict:
        """委派任务并汇总结果

        Args:
            query: 用户查询
            query_type: 查询类型（simple, comparison, analytical）

        Returns:
            最终结果
        """
        logger.info(f"[Supervisor] Delegating query: {query[:50]}...")

        if query_type == "comparison":
            # 对比查询：并行检索 → 分析 → 生成
            return await self._handle_comparison(query)
        elif query_type == "analytical":
            # 分析查询：检索 → 分析 → 生成
            return await self._handle_analytical(query)
        else:
            # 简单查询：检索 → 生成
            return await self._handle_simple(query)

    async def _handle_simple(self, query: str) -> dict:
        """处理简单查询"""
        logger.info("[Supervisor] Strategy: simple (retrieval → generation)")

        # Step 1: 检索
        retrieval_result = await self.workers["retrieval"].process({"query": query})

        # Step 2: 生成
        generation_result = await self.workers["generation"].process({
            "query": query,
            "context": [retrieval_result["result"]],
        })

        return {
            "query": query,
            "strategy": "simple",
            "answer": generation_result["result"],
            "workflow": ["retrieval", "generation"],
        }

    async def _handle_comparison(self, query: str) -> dict:
        """处理对比查询（并行检索）"""
        logger.info("[Supervisor] Strategy: comparison (parallel retrieval → analysis → generation)")

        # 提取实体（简化版，实际应该用 LLM）
        entities = self._extract_entities(query)

        # Step 1: 并行检索多个实体
        retrieval_tasks = [
            self.workers["retrieval"].process({"query": entity})
            for entity in entities
        ]
        retrieval_results = await asyncio.gather(*retrieval_tasks)

        # Step 2: 分析对比
        analysis_result = await self.workers["analysis"].process({
            "data": [r["result"] for r in retrieval_results],
            "aspect": "对比分析",
        })

        # Step 3: 生成答案
        generation_result = await self.workers["generation"].process({
            "query": query,
            "context": [analysis_result["result"]],
        })

        return {
            "query": query,
            "strategy": "comparison",
            "answer": generation_result["result"],
            "workflow": ["parallel_retrieval", "analysis", "generation"],
            "entities": entities,
        }

    async def _handle_analytical(self, query: str) -> dict:
        """处理分析查询"""
        logger.info("[Supervisor] Strategy: analytical (retrieval → analysis → generation)")

        # Step 1: 检索
        retrieval_result = await self.workers["retrieval"].process({"query": query})

        # Step 2: 分析
        analysis_result = await self.workers["analysis"].process({
            "data": [retrieval_result["result"]],
            "aspect": "深度分析",
        })

        # Step 3: 生成
        generation_result = await self.workers["generation"].process({
            "query": query,
            "context": [analysis_result["result"]],
        })

        return {
            "query": query,
            "strategy": "analytical",
            "answer": generation_result["result"],
            "workflow": ["retrieval", "analysis", "generation"],
        }

    def _extract_entities(self, query: str) -> list[str]:
        """提取查询中的实体（简化版）"""
        # 简单的关键词匹配
        common_entities = ["妖刀姬", "红蝶", "素问", "茨木童子"]

        entities = [e for e in common_entities if e in query]

        if not entities:
            # 默认返回查询本身
            entities = [query]

        return entities[:2]  # 最多 2 个实体


# ===== LangGraph 节点包装 =====


async def multi_agent_node(state: dict) -> dict:
    """Multi-Agent 节点（用于 LangGraph）"""
    query = state.get("query", "")
    query_type = state.get("query_type", "simple")

    supervisor = Supervisor()
    result = await supervisor.delegate(query, query_type)

    return {
        "answer": result["answer"],
        "multi_agent_workflow": result["workflow"],
        "multi_agent_strategy": result["strategy"],
    }
