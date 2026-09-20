"""Adaptive Router 集成测试

测试查询分类和自适应路由
"""

import pytest

from src.modules import AdaptiveRouterModule


class TestAdaptiveRouter:
    """测试自适应路由器"""

    @pytest.mark.asyncio
    async def test_factual_query_heuristic(self):
        """测试事实查询分类（启发式）"""
        config = {"enable_classification": False}
        router = AdaptiveRouterModule(config)

        state = {"query": "妖刀姬的连招是什么？", "messages": []}
        result = await router(state)

        assert result["query_type"] == "factual"
        assert result["route"] == "simple_retrieve"
        print(f"  ✅ Factual query: {result['query_type']} → {result['route']}")

    @pytest.mark.asyncio
    async def test_analytical_query_heuristic(self):
        """测试分析查询分类（启发式）"""
        config = {"enable_classification": False}
        router = AdaptiveRouterModule(config)

        state = {"query": "妖刀姬和红蝶哪个更适合新手？", "messages": []}
        result = await router(state)

        assert result["query_type"] == "analytical"
        assert result["route"] == "decompose"
        print(f"  ✅ Analytical query: {result['query_type']} → {result['route']}")

    @pytest.mark.asyncio
    async def test_conversational_query_heuristic(self):
        """测试对话查询分类（启发式）"""
        config = {"enable_classification": False}
        router = AdaptiveRouterModule(config)

        state = {
            "query": "那她的技能呢？",
            "messages": [{"role": "user", "content": "妖刀姬怎么玩"}],
        }
        result = await router(state)

        assert result["query_type"] == "conversational"
        assert result["route"] == "with_history"
        print(f"  ✅ Conversational query: {result['query_type']} → {result['route']}")

    @pytest.mark.asyncio
    async def test_ambiguous_query_heuristic(self):
        """测试模糊查询分类（启发式）"""
        config = {"enable_classification": False}
        router = AdaptiveRouterModule(config)

        state = {"query": "怎么玩", "messages": []}
        result = await router(state)

        assert result["query_type"] == "ambiguous"
        assert result["route"] == "clarify"
        print(f"  ✅ Ambiguous query: {result['query_type']} → {result['route']}")

    @pytest.mark.asyncio
    async def test_custom_route_map(self):
        """测试自定义路由映射"""
        config = {
            "enable_classification": False,
            "route_map": {
                "factual": "my_custom_route",
                "analytical": "another_route",
            },
        }
        router = AdaptiveRouterModule(config)

        state = {"query": "妖刀姬连招", "messages": []}
        result = await router(state)

        assert result["query_type"] == "factual"
        assert result["route"] == "my_custom_route"
        print(f"  ✅ Custom route map: {result['route']}")

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """测试空查询"""
        config = {"enable_classification": False}
        router = AdaptiveRouterModule(config)

        state = {"query": "", "messages": []}
        result = await router(state)

        # 空查询默认为 factual
        assert result["query_type"] == "factual"
        print(f"  ✅ Empty query: defaults to {result['query_type']}")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
