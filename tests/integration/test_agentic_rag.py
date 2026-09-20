"""Agentic RAG 集成测试

测试 ReAct Agent 的核心功能：
1. Router 路由决策
2. ReAct 循环执行
3. 工具调用
4. 端到端查询
"""

import pytest

from src.agents import run_agentic_rag


class TestAgenticRAG:
    """测试 Agentic RAG 系统"""

    @pytest.mark.asyncio
    async def test_simple_query_routes_to_direct_rag(self):
        """测试简单查询路由到 Direct RAG"""
        result = await run_agentic_rag(
            query="妖刀姬的连招是什么？",
            session_id="test-simple",
            max_iterations=3,
        )

        # 简单查询应该走 direct_rag
        assert result.get("route") == "direct_rag"
        assert "answer" in result
        assert len(result["answer"]) > 0
        print(f"  ✅ Simple query routed correctly")
        print(f"     Route: {result['route']}")
        print(f"     Answer: {result['answer'][:100]}...")

    @pytest.mark.asyncio
    async def test_comparison_query_routes_to_agentic_rag(self):
        """测试对比查询路由到 Agentic RAG"""
        result = await run_agentic_rag(
            query="妖刀姬和红蝶哪个更适合新手？",
            session_id="test-comparison",
            max_iterations=5,
        )

        # 对比查询应该走 agentic_rag
        assert result.get("route") == "agentic_rag"
        assert "answer" in result
        assert "agent_scratchpad" in result
        assert len(result["agent_scratchpad"]) > 0
        print(f"  ✅ Comparison query routed correctly")
        print(f"     Route: {result['route']}")
        print(f"     Iterations: {result.get('iterations', 0)}")
        print(f"     Tools used: {[step['action']['tool'] for step in result['agent_scratchpad']]}")

    @pytest.mark.asyncio
    async def test_react_loop_with_rag_search(self):
        """测试 ReAct 循环中的 RAG 检索"""
        result = await run_agentic_rag(
            query="妖刀姬有什么特点？",
            session_id="test-react-loop",
            max_iterations=3,
        )

        scratchpad = result.get("agent_scratchpad", [])

        if scratchpad:  # 如果走了 agentic_rag
            # 检查是否使用了 rag_search 工具
            tools_used = [step["action"]["tool"] for step in scratchpad]
            assert "rag_search" in tools_used or "finish" in tools_used
            print(f"  ✅ ReAct loop executed")
            print(f"     Iterations: {len(scratchpad)}")
            print(f"     Tools: {tools_used}")
        else:
            # 走了 direct_rag 也是正确的
            assert result.get("route") == "direct_rag"
            print(f"  ✅ Query handled by Direct RAG")

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self):
        """测试最大迭代次数限制"""
        result = await run_agentic_rag(
            query="妖刀姬和红蝶对比",
            session_id="test-max-iter",
            max_iterations=2,  # 限制为 2 次
        )

        iterations = result.get("iterations", 0)

        if result.get("route") == "agentic_rag":
            # 应该不超过 max_iterations
            assert iterations <= 2
            print(f"  ✅ Max iterations respected")
            print(f"     Iterations: {iterations}/2")
        else:
            print(f"  ✅ Query handled by Direct RAG")

    @pytest.mark.asyncio
    async def test_agent_scratchpad_format(self):
        """测试 Agent Scratchpad 格式"""
        result = await run_agentic_rag(
            query="对比妖刀姬和红蝶",
            session_id="test-scratchpad",
            max_iterations=3,
        )

        scratchpad = result.get("agent_scratchpad", [])

        if scratchpad:
            # 检查每个步骤的格式
            for step in scratchpad:
                assert "iteration" in step
                assert "thought" in step
                assert "action" in step
                assert "observation" in step

                action = step["action"]
                assert "tool" in action
                assert "args" in action

            print(f"  ✅ Scratchpad format valid")
            print(f"     Steps: {len(scratchpad)}")

            # 打印第一步示例
            if scratchpad:
                first_step = scratchpad[0]
                print(f"     Example step:")
                print(f"       Thought: {first_step['thought'][:80]}...")
                print(f"       Action: {first_step['action']['tool']}")
        else:
            print(f"  ✅ Query handled by Direct RAG (no scratchpad)")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
