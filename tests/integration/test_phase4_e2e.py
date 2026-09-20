"""Phase 4 端到端测试

测试完整的 Agentic RAG 流程，包括：
1. 简单查询 → Direct RAG
2. 对比查询 → Agentic RAG + 多工具调用
3. 计算查询 → Agentic RAG + calculate 工具
4. Reflexion 质量评估
"""

import pytest

from src.agents import run_agentic_rag


class TestAgenticRAGEndToEnd:
    """端到端测试"""

    @pytest.mark.asyncio
    async def test_simple_factual_query(self):
        """测试简单事实查询（走 Direct RAG）"""
        result = await run_agentic_rag(
            query="妖刀姬的连招是什么？",
            session_id="e2e-simple",
            max_iterations=3,
            enable_reflexion=False,
        )

        assert "answer" in result
        assert len(result["answer"]) > 0
        assert result.get("route") == "direct_rag"

        print(f"\n✅ Simple query → Direct RAG")
        print(f"   Answer: {result['answer'][:100]}...")

    @pytest.mark.asyncio
    async def test_comparison_query_with_tools(self):
        """测试对比查询（走 Agentic RAG + 多工具）"""
        result = await run_agentic_rag(
            query="妖刀姬和红蝶哪个更适合新手？",
            session_id="e2e-comparison",
            max_iterations=5,
            enable_reflexion=False,
        )

        assert "answer" in result

        # 如果走了 agentic_rag
        if result.get("route") == "agentic_rag":
            scratchpad = result.get("agent_scratchpad", [])
            assert len(scratchpad) > 0

            # 检查工具使用
            tools_used = [step["action"]["tool"] for step in scratchpad]
            print(f"\n✅ Comparison query → Agentic RAG")
            print(f"   Iterations: {len(scratchpad)}")
            print(f"   Tools used: {tools_used}")
            print(f"   Answer: {result['answer'][:150]}...")
        else:
            print(f"\n✅ Query handled by Direct RAG")

    @pytest.mark.asyncio
    async def test_analytical_query_with_calculation(self):
        """测试分析查询（可能需要计算）"""
        result = await run_agentic_rag(
            query="如果妖刀姬伤害系数是 1.2，振刀 100 点基础伤害，实际伤害是多少？",
            session_id="e2e-calc",
            max_iterations=5,
            enable_reflexion=False,
        )

        assert "answer" in result

        if result.get("route") == "agentic_rag":
            scratchpad = result.get("agent_scratchpad", [])
            tools_used = [step["action"]["tool"] for step in scratchpad]

            # 检查是否使用了 calculate 工具
            has_calculate = "calculate" in tools_used

            print(f"\n✅ Analytical query with calculation")
            print(f"   Tools used: {tools_used}")
            print(f"   Used calculate: {has_calculate}")
            print(f"   Answer: {result['answer'][:150]}...")
        else:
            print(f"\n✅ Query handled by Direct RAG")

    @pytest.mark.asyncio
    async def test_with_reflexion_enabled(self):
        """测试启用 Reflexion 的完整流程"""
        result = await run_agentic_rag(
            query="对比妖刀姬和红蝶的优缺点",
            session_id="e2e-reflexion",
            max_iterations=4,
            enable_reflexion=True,
        )

        assert "answer" in result

        if result.get("route") == "agentic_rag":
            # 应该有评估分数
            score = result.get("evaluation_score")
            need_replan = result.get("need_replan", False)

            print(f"\n✅ Reflexion enabled")
            print(f"   Evaluation score: {score}")
            print(f"   Need replan: {need_replan}")
            print(f"   Answer quality: {'Good' if score and score >= 4 else 'Acceptable' if score and score >= 3 else 'Low'}")
        else:
            print(f"\n✅ Query handled by Direct RAG (no reflexion needed)")

    @pytest.mark.asyncio
    async def test_max_iterations_respected(self):
        """测试最大迭代次数限制"""
        result = await run_agentic_rag(
            query="妖刀姬和红蝶详细对比",
            session_id="e2e-max-iter",
            max_iterations=2,  # 限制为 2 次
            enable_reflexion=False,
        )

        if result.get("route") == "agentic_rag":
            iterations = result.get("iterations", 0)
            assert iterations <= 2

            print(f"\n✅ Max iterations respected")
            print(f"   Iterations: {iterations}/2")
        else:
            print(f"\n✅ Query handled by Direct RAG")

    @pytest.mark.asyncio
    async def test_scratchpad_completeness(self):
        """测试 Scratchpad 记录完整性"""
        result = await run_agentic_rag(
            query="对比妖刀姬和红蝶",
            session_id="e2e-scratchpad",
            max_iterations=4,
            enable_reflexion=False,
        )

        if result.get("route") == "agentic_rag":
            scratchpad = result.get("agent_scratchpad", [])

            for i, step in enumerate(scratchpad):
                # 验证每步的完整性
                assert "iteration" in step
                assert "thought" in step
                assert "action" in step
                assert "observation" in step

                action = step["action"]
                assert "tool" in action
                assert "args" in action

            print(f"\n✅ Scratchpad completeness verified")
            print(f"   Total steps: {len(scratchpad)}")

            # 打印第一步示例
            if scratchpad:
                first = scratchpad[0]
                print(f"   Example step:")
                print(f"     Thought: {first['thought'][:80]}...")
                print(f"     Action: {first['action']['tool']}")
        else:
            print(f"\n✅ Query handled by Direct RAG (no scratchpad)")


class TestToolUsage:
    """测试各种工具的使用"""

    @pytest.mark.asyncio
    async def test_rag_search_tool(self):
        """测试 rag_search 工具"""
        from src.agents.tools import rag_search_tool

        docs = await rag_search_tool("妖刀姬", top_k=5)

        assert isinstance(docs, list)
        assert len(docs) > 0
        assert "content" in docs[0]

        print(f"\n✅ rag_search tool works")
        print(f"   Retrieved: {len(docs)} docs")

    @pytest.mark.asyncio
    async def test_calculate_tool(self):
        """测试 calculate 工具"""
        from src.agents.tools import calculate_tool

        result = await calculate_tool("1.2 * 100")

        assert "result" in result
        assert result["result"] == 120.0

        print(f"\n✅ calculate tool works")
        print(f"   1.2 * 100 = {result['result']}")

    @pytest.mark.asyncio
    async def test_calculate_tool_with_complex_expression(self):
        """测试复杂计算"""
        from src.agents.tools import calculate_tool

        result = await calculate_tool("(1.2 + 0.3) * 100 - 50")

        assert "result" in result
        expected = (1.2 + 0.3) * 100 - 50
        assert abs(result["result"] - expected) < 0.01

        print(f"\n✅ calculate tool handles complex expression")
        print(f"   (1.2 + 0.3) * 100 - 50 = {result['result']}")

    @pytest.mark.asyncio
    async def test_compare_tool(self):
        """测试 compare 工具"""
        from src.agents.tools import compare_tool

        result = await compare_tool("妖刀姬", "红蝶", "新手友好度")

        assert "entity_a" in result
        assert "entity_b" in result
        assert "docs_a" in result
        assert "docs_b" in result

        print(f"\n✅ compare tool works")
        print(f"   Comparing: {result['entity_a']} vs {result['entity_b']}")
        print(f"   Docs A: {len(result['docs_a'])}, Docs B: {len(result['docs_b'])}")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
