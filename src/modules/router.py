"""Adaptive Router Module

根据 query 类型动态选择处理路径：
- factual: 事实查询 → 直接检索
- analytical: 分析查询 → 需要多步推理
- conversational: 对话查询 → 需要历史上下文
- ambiguous: 模糊查询 → 需要澄清
"""

from __future__ import annotations

from typing import Literal

from loguru import logger

from ..llm import get_llm
from .base import ModuleRegistry, RAGModule

QueryType = Literal["factual", "analytical", "conversational", "ambiguous"]


@ModuleRegistry.register
class AdaptiveRouterModule(RAGModule):
    """自适应路由模块

    输入 state:
        - query: str

    输出 state 更新:
        - query_type: str (factual/analytical/conversational/ambiguous)
        - route: str (目标路由名称)
    """

    name = "adaptive_router"

    def __init__(self, config: dict | None = None):
        super().__init__(config)

        self.llm = get_llm()
        self.enable_classification = self.config.get("enable_classification", True)

        # 路由映射
        self.route_map = self.config.get("route_map", {
            "factual": "simple_retrieve",
            "analytical": "decompose",
            "conversational": "with_history",
            "ambiguous": "clarify",
        })

        # 分类 prompt
        self.classification_prompt = self.config.get(
            "classification_prompt",
            """你是一个查询分类器。请判断以下查询属于哪种类型：

1. factual（事实查询）：直接询问事实、数据、步骤等
   例：妖刀姬的连招是什么？素问在副本里站什么位置？

2. analytical（分析查询）：需要多步推理、对比、分析
   例：妖刀姬和红蝶哪个更适合新手？S13 版本有哪些平衡性调整？

3. conversational（对话查询）：依赖上下文，需要历史消息
   例：那她的技能呢？（依赖前文"她"是谁）

4. ambiguous（模糊查询）：表述不清，需要澄清
   例：怎么玩？（玩什么？）bug 怎么解决？（什么 bug？）

查询：{query}

请只回复类型名称（factual / analytical / conversational / ambiguous），不要其他内容。
""",
        )

    async def __call__(self, state: dict) -> dict:
        """路由决策"""
        query = state.get("query", "")
        messages = state.get("messages", [])

        if not query:
            logger.warning(f"[{self.name}] Empty query, defaulting to factual")
            return {"query_type": "factual", "route": self.route_map["factual"]}

        # 分类查询
        if self.enable_classification:
            query_type = await self._classify(query, messages)
        else:
            query_type = self._heuristic_classify(query, messages)

        # 映射路由
        route = self.route_map.get(query_type, "simple_retrieve")

        logger.info(f"[{self.name}] Query classified as '{query_type}' → route '{route}'")

        return {
            "query_type": query_type,
            "route": route,
        }

    async def _classify(self, query: str, messages: list) -> QueryType:
        """使用 LLM 分类查询"""
        prompt = self.classification_prompt.format(query=query)

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            result = response.content.strip().lower()

            # 提取类型
            for query_type in ["factual", "analytical", "conversational", "ambiguous"]:
                if query_type in result:
                    return query_type  # type: ignore

            logger.warning(f"[{self.name}] Classification failed, got: {result}")
            return "factual"  # 默认
        except Exception as e:
            logger.error(f"[{self.name}] Classification error: {e}")
            return "factual"

    def _heuristic_classify(self, query: str, messages: list) -> QueryType:
        """启发式分类（不调用 LLM）"""
        query_lower = query.lower()

        # 1. 对话查询（有代词且有历史）
        if messages and any(p in query for p in ["他", "她", "它", "这个", "那个", "还有"]):
            return "conversational"

        # 2. 模糊查询（太短或太泛）
        if len(query) < 5 or query in ["怎么玩", "怎么办", "bug", "问题", "错误"]:
            return "ambiguous"

        # 3. 分析查询（对比、评价、推荐）
        if any(kw in query_lower for kw in ["哪个", "对比", "区别", "更好", "推荐", "为什么"]):
            return "analytical"

        # 4. 事实查询（默认）
        return "factual"

    def get_config(self):
        """导出配置"""
        config = super().get_config()
        config.params.update({
            "enable_classification": self.enable_classification,
            "route_map": self.route_map,
            "classification_prompt": self.classification_prompt,
        })
        return config
