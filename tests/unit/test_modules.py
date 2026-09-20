"""Modular RAG 模块系统单元测试

测试：
1. 模块注册机制
2. 模块配置序列化/反序列化
3. 各模块独立功能
"""

import pytest

from src.modules import (
    GeneratorModule,
    HybridRetrieverModule,
    ModuleRegistry,
    QueryRewriterModule,
    RerankerModule,
)


class TestModuleRegistry:
    """测试模块注册表"""

    def test_registry_auto_populated(self):
        """测试模块自动注册"""
        # 所有模块应该已通过 @ModuleRegistry.register 自动注册
        registered = ModuleRegistry.list_names()
        assert "query_rewriter" in registered
        assert "hybrid_retriever" in registered
        assert "reranker" in registered
        assert "generator" in registered

    def test_get_module_class(self):
        """测试按名字获取模块类"""
        cls = ModuleRegistry.get("query_rewriter")
        assert cls is QueryRewriterModule

        cls = ModuleRegistry.get("hybrid_retriever")
        assert cls is HybridRetrieverModule

    def test_get_nonexistent_module(self):
        """测试获取不存在的模块"""
        cls = ModuleRegistry.get("nonexistent")
        assert cls is None


class TestQueryRewriterModule:
    """测试查询改写模块"""

    @pytest.mark.asyncio
    async def test_typo_correction(self):
        """测试错别字纠正"""
        config = {
            "typo_map": {"要到姬": "妖刀姬", "怎末": "怎么"},
            "enable_rewrite": True,
            "enable_expansion": False,
        }
        module = QueryRewriterModule(config)

        state = {"query": "要到姬怎末连招"}
        result = await module(state)

        assert result["query"] == "妖刀姬怎么连招"
        print(f"  ✅ Typo corrected: {result['query']}")

    @pytest.mark.asyncio
    async def test_keyword_extraction(self):
        """测试关键词提取"""
        config = {
            "game_terms": ["妖刀姬", "连招", "S13"],
            "enable_rewrite": False,
            "enable_expansion": False,
        }
        module = QueryRewriterModule(config)

        state = {"query": "妖刀姬 S13 连招"}
        result = await module(state)

        keywords = result["keywords"]
        assert "妖刀姬" in keywords
        assert "连招" in keywords
        assert "S13" in keywords
        print(f"  ✅ Keywords: {keywords}")

    @pytest.mark.asyncio
    async def test_query_expansion(self):
        """测试查询扩展"""
        config = {
            "synonyms": {"连招": ["技能连击", "combo"]},
            "game_terms": ["连招"],
            "enable_rewrite": False,
            "enable_expansion": True,
        }
        module = QueryRewriterModule(config)

        state = {"query": "妖刀姬连招"}
        result = await module(state)

        expanded = result["expanded_queries"]
        assert len(expanded) > 0
        assert any("技能连击" in q for q in expanded) or any("combo" in q for q in expanded)
        print(f"  ✅ Expanded: {expanded}")


class TestRetrieverModule:
    """测试检索模块"""

    @pytest.mark.asyncio
    async def test_basic_retrieval(self):
        """测试基础检索功能"""
        config = {"vector_top_k": 5, "use_expanded": False}
        module = HybridRetrieverModule(config)

        state = {"query": "妖刀姬连招"}
        result = await module(state)

        docs = result["retrieved_docs"]
        assert len(docs) > 0
        assert all("id" in doc for doc in docs)
        assert all("content" in doc for doc in docs)
        assert all("score" in doc for doc in docs)
        print(f"  ✅ Retrieved {len(docs)} docs")

    @pytest.mark.asyncio
    async def test_expanded_queries(self):
        """测试扩展查询检索"""
        config = {"vector_top_k": 10, "use_expanded": True}
        module = HybridRetrieverModule(config)

        state = {
            "query": "妖刀姬连招",
            "expanded_queries": ["妖刀姬技能连击", "妖刀姬combo"],
        }
        result = await module(state)

        docs = result["retrieved_docs"]
        assert len(docs) > 0
        print(f"  ✅ Retrieved {len(docs)} docs with expanded queries")


class TestRerankerModule:
    """测试重排模块"""

    @pytest.mark.asyncio
    async def test_reranker_disabled(self):
        """测试禁用重排"""
        config = {"enabled": False}
        module = RerankerModule(config)

        state = {
            "query": "妖刀姬",
            "retrieved_docs": [
                {"id": "1", "content": "test", "metadata": {}, "score": 0.5, "title": "t1", "source": ""},
            ],
        }
        result = await module(state)

        # 禁用时应返回空更新
        assert result == {}
        print("  ✅ Reranker disabled, no change")

    @pytest.mark.asyncio
    async def test_reranker_enabled(self):
        """测试启用重排（需要模型）"""
        config = {
            "enabled": True,
            "model": "BAAI/bge-reranker-v2-m3",
            "device": "cpu",
            "top_n": 3,
        }
        module = RerankerModule(config)

        # 准备假数据
        state = {
            "query": "妖刀姬连招",
            "retrieved_docs": [
                {
                    "id": f"doc-{i}",
                    "content": f"测试文档 {i}",
                    "metadata": {"title": f"文档{i}"},
                    "score": 0.5,
                    "title": f"文档{i}",
                    "source": "",
                }
                for i in range(5)
            ],
        }

        result = await module(state)

        docs = result["retrieved_docs"]
        assert len(docs) <= 3  # top_n=3
        print(f"  ✅ Reranked: {len(docs)} docs")


class TestGeneratorModule:
    """测试生成模块"""

    @pytest.mark.asyncio
    async def test_basic_generation(self):
        """测试基础生成"""
        config = {
            "enable_thinking": False,
            "max_context_docs": 3,
        }
        module = GeneratorModule(config)

        state = {
            "query": "妖刀姬怎么玩",
            "retrieved_docs": [
                {
                    "id": "1",
                    "content": "妖刀姬是近战角色",
                    "metadata": {"title": "妖刀姬攻略"},
                    "score": 0.8,
                    "title": "妖刀姬攻略",
                    "source": "",
                },
            ],
        }

        result = await module(state)

        answer = result["answer"]
        assert len(answer) > 0
        print(f"  ✅ Generated answer: {len(answer)} chars")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
