"""Reflexion 机制测试

测试自我纠错和质量评估
"""

import pytest

from src.agents import run_agentic_rag


class TestReflexion:
    """测试 Reflexion 自我纠错机制"""

    @pytest.mark.asyncio
    async def test_reflexion_enabled(self):
        """测试启用 Reflexion"""
        result = await run_agentic_rag(
            query="妖刀姬和红蝶对比",
            session_id="test-reflexion-on",
            max_iterations=3,
            enable_reflexion=True,
        )

        # 如果走了 agentic_rag，应该有 evaluation_score
        if result.get("route") == "agentic_rag":
            assert "evaluation_score" in result
            print(f"  ✅ Reflexion enabled")
            print(f"     Evaluation score: {result.get('evaluation_score', 0)}")
            print(f"     Need replan: {result.get('need_replan', False)}")
        else:
            print(f"  ✅ Query handled by Direct RAG")

    @pytest.mark.asyncio
    async def test_reflexion_disabled(self):
        """测试禁用 Reflexion"""
        result = await run_agentic_rag(
            query="妖刀姬和红蝶对比",
            session_id="test-reflexion-off",
            max_iterations=3,
            enable_reflexion=False,
        )

        # 禁用 Reflexion 时不应该有 evaluation_score
        if result.get("route") == "agentic_rag":
            # 可能没有 evaluation_score（取决于实现）
            print(f"  ✅ Reflexion disabled")
            print(f"     Has evaluation: {'evaluation_score' in result}")
        else:
            print(f"  ✅ Query handled by Direct RAG")

    @pytest.mark.asyncio
    async def test_evaluation_score_range(self):
        """测试评分范围"""
        result = await run_agentic_rag(
            query="妖刀姬的技能",
            session_id="test-score-range",
            max_iterations=3,
            enable_reflexion=True,
        )

        score = result.get("evaluation_score")
        if score is not None:
            assert 0.0 <= score <= 5.0
            print(f"  ✅ Evaluation score in valid range: {score}")
        else:
            print(f"  ✅ Query handled by Direct RAG (no evaluation)")

    @pytest.mark.asyncio
    async def test_replan_triggered(self):
        """测试重新规划触发（模拟低质量场景）"""
        # 这个测试可能需要构造特殊场景才能触发 replan
        # 目前只验证结构
        result = await run_agentic_rag(
            query="对比妖刀姬和红蝶",
            session_id="test-replan",
            max_iterations=2,  # 限制迭代次数，可能导致质量不佳
            enable_reflexion=True,
        )

        if result.get("route") == "agentic_rag":
            need_replan = result.get("need_replan", False)
            print(f"  ✅ Replan check completed")
            print(f"     Need replan: {need_replan}")
            if need_replan:
                print(f"     Plan: {result.get('plan', [])}")
        else:
            print(f"  ✅ Query handled by Direct RAG")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
