"""Multi-Agent 测试

测试 Supervisor + Workers 协作
"""

import pytest

from src.agents.multi_agent import (
    AnalysisWorker,
    GenerationWorker,
    RetrievalWorker,
    Supervisor,
)


class TestWorkers:
    """测试各个 Worker"""

    @pytest.mark.asyncio
    async def test_retrieval_worker(self):
        """测试检索 Worker"""
        worker = RetrievalWorker()
        result = await worker.process({"query": "妖刀姬"})

        assert result["success"] is True
        assert result["worker"] == "retrieval_worker"
        assert "result" in result
        assert isinstance(result["result"], list)

        print(f"\n✅ Retrieval worker works")
        print(f"   Retrieved: {len(result['result'])} docs")

    @pytest.mark.asyncio
    async def test_analysis_worker(self):
        """测试分析 Worker"""
        worker = AnalysisWorker()
        result = await worker.process({
            "data": ["妖刀姬是输出型式神", "红蝶是控制型式神"],
            "aspect": "对比分析",
        })

        assert result["success"] is True
        assert result["worker"] == "analysis_worker"
        assert "result" in result
        assert len(result["result"]) > 0

        print(f"\n✅ Analysis worker works")
        print(f"   Analysis: {result['result'][:100]}...")

    @pytest.mark.asyncio
    async def test_generation_worker(self):
        """测试生成 Worker"""
        worker = GenerationWorker()
        result = await worker.process({
            "query": "妖刀姬怎么玩？",
            "context": ["妖刀姬是输出型式神", "连招：1技能 → 普攻 → 2技能"],
        })

        assert result["success"] is True
        assert result["worker"] == "generation_worker"
        assert "result" in result
        assert len(result["result"]) > 0

        print(f"\n✅ Generation worker works")
        print(f"   Answer: {result['result'][:100]}...")


class TestSupervisor:
    """测试 Supervisor"""

    @pytest.mark.asyncio
    async def test_simple_strategy(self):
        """测试简单策略"""
        supervisor = Supervisor()
        result = await supervisor.delegate("妖刀姬的连招是什么？", query_type="simple")

        assert "answer" in result
        assert result["strategy"] == "simple"
        assert "retrieval" in result["workflow"]
        assert "generation" in result["workflow"]

        print(f"\n✅ Simple strategy works")
        print(f"   Workflow: {' → '.join(result['workflow'])}")
        print(f"   Answer: {result['answer'][:100]}...")

    @pytest.mark.asyncio
    async def test_comparison_strategy(self):
        """测试对比策略（并行检索）"""
        supervisor = Supervisor()
        result = await supervisor.delegate("妖刀姬和红蝶哪个更好？", query_type="comparison")

        assert "answer" in result
        assert result["strategy"] == "comparison"
        assert "parallel_retrieval" in result["workflow"]
        assert "entities" in result

        print(f"\n✅ Comparison strategy works")
        print(f"   Workflow: {' → '.join(result['workflow'])}")
        print(f"   Entities: {result['entities']}")
        print(f"   Answer: {result['answer'][:100]}...")

    @pytest.mark.asyncio
    async def test_analytical_strategy(self):
        """测试分析策略"""
        supervisor = Supervisor()
        result = await supervisor.delegate("为什么妖刀姬适合新手？", query_type="analytical")

        assert "answer" in result
        assert result["strategy"] == "analytical"
        assert "analysis" in result["workflow"]

        print(f"\n✅ Analytical strategy works")
        print(f"   Workflow: {' → '.join(result['workflow'])}")
        print(f"   Answer: {result['answer'][:100]}...")

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """测试并行执行效率"""
        import time

        supervisor = Supervisor()

        # 测试对比查询（应该并行执行）
        start = time.time()
        result = await supervisor.delegate("妖刀姬和红蝶对比", query_type="comparison")
        elapsed = time.time() - start

        assert "answer" in result
        # 并行应该比串行快（但这里只是验证能执行）
        print(f"\n✅ Parallel execution completed")
        print(f"   Time: {elapsed:.2f}s")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)
