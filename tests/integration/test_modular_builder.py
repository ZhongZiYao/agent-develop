"""Modular RAG Builder 集成测试

测试配置驱动的 Graph 构建和端到端执行
"""

import pytest

from src.modules import RAGGraphBuilder, build_graph_from_config


class TestRAGGraphBuilder:
    """测试 Graph 构建器"""

    @pytest.mark.asyncio
    async def test_build_from_yaml(self):
        """测试从 YAML 配置构建 Graph"""
        graph = await build_graph_from_config("config/rag_modules.yaml")
        assert graph is not None
        print("  ✅ Graph built successfully from config")

    @pytest.mark.asyncio
    async def test_build_fast_pipeline(self):
        """测试快速流水线配置"""
        graph = await build_graph_from_config("config/rag_modules_fast.yaml")
        assert graph is not None
        print("  ✅ Fast pipeline built successfully")

    @pytest.mark.asyncio
    async def test_end_to_end_execution(self):
        """测试端到端执行"""
        graph = await build_graph_from_config("config/rag_modules.yaml")

        # 输入状态
        input_state = {
            "query": "妖刀姬连招",
            "game": "",
            "session_id": "test-modular",
            "top_k": 10,
            "top_n": 3,
            "messages": [],
        }

        config = {"configurable": {"thread_id": "test-modular"}}

        # 执行
        result = await graph.ainvoke(input_state, config=config)

        # 验证输出
        assert "query" in result
        assert "retrieved_docs" in result
        assert "answer" in result
        assert len(result["retrieved_docs"]) > 0
        assert len(result["answer"]) > 0

        print(f"  ✅ End-to-end execution successful")
        print(f"     Query: {result['query']}")
        print(f"     Retrieved: {len(result['retrieved_docs'])} docs")
        print(f"     Answer: {len(result['answer'])} chars")

    @pytest.mark.asyncio
    async def test_fast_pipeline_execution(self):
        """测试快速流水线执行（无重排）"""
        graph = await build_graph_from_config("config/rag_modules_fast.yaml")

        input_state = {
            "query": "红蝶怎么玩",
            "game": "",
            "session_id": "test-fast",
            "top_k": 10,
            "top_n": 3,
            "messages": [],
        }

        config = {"configurable": {"thread_id": "test-fast"}}
        result = await graph.ainvoke(input_state, config=config)

        # 验证输出
        assert "answer" in result
        assert len(result["answer"]) > 0

        print(f"  ✅ Fast pipeline execution successful")
        print(f"     Answer: {len(result['answer'])} chars")

    @pytest.mark.asyncio
    async def test_disabled_module_skipped(self):
        """测试禁用的模块被跳过"""
        builder = RAGGraphBuilder.from_yaml("config/rag_modules_fast.yaml")
        await builder.build()

        # reranker 被禁用，不应在 modules 中
        assert "reranker" not in builder.modules
        print("  ✅ Disabled module correctly skipped")

    @pytest.mark.asyncio
    async def test_query_rewriting_in_pipeline(self):
        """测试流水线中的查询改写"""
        graph = await build_graph_from_config("config/rag_modules.yaml")

        input_state = {
            "query": "要到姬怎末连召？",  # 错别字
            "game": "",
            "session_id": "test-typo",
            "top_k": 5,
            "top_n": 2,
            "messages": [],
        }

        config = {"configurable": {"thread_id": "test-typo"}}
        result = await graph.ainvoke(input_state, config=config)

        # query 应该被改写
        assert "妖刀姬" in result["query"]
        assert "怎么" in result["query"]
        assert "连招" in result["query"]

        print(f"  ✅ Query rewriting worked")
        print(f"     Original: 要到姬怎末连召？")
        print(f"     Rewritten: {result['query']}")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
