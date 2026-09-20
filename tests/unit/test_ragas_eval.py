"""RAGAS 评测测试

覆盖：
1. 各项指标计算
2. 完整评测流程
3. 边界情况
"""

import pytest

from src.evaluation.ragas_eval import (
    _calc_context_precision,
    _calc_context_recall,
    _calc_faithfulness,
    _calc_answer_relevancy,
    evaluate_rag_system,
)


class TestContextPrecision:
    """测试 Context Precision"""

    def test_perfect_match(self):
        """完美匹配（所有 retrieved 都是相关的）"""
        outputs = [
            {
                "contexts": ["妖刀姬是游戏角色", "刃返是技能"],
                "expected_contexts": ["妖刀姬", "刃返"],
            }
        ]
        score = _calc_context_precision(outputs)
        # 2/2 = 1.0
        assert score == 1.0
        print(f"✅ 完美匹配: {score}")

    def test_partial_match(self):
        """部分匹配"""
        outputs = [
            {
                "contexts": ["妖刀姬是游戏角色", "无关内容"],
                "expected_contexts": ["妖刀姬"],
            }
        ]
        score = _calc_context_precision(outputs)
        # 1/2 = 0.5
        assert score == 0.5
        print(f"✅ 部分匹配: {score}")

    def test_no_match(self):
        """完全不匹配"""
        outputs = [
            {
                "contexts": ["无关内容1", "无关内容2"],
                "expected_contexts": ["期望内容"],
            }
        ]
        score = _calc_context_precision(outputs)
        assert score == 0.0
        print(f"✅ 不匹配: {score}")

    def test_empty_contexts(self):
        """空 contexts"""
        outputs = [{"contexts": [], "expected_contexts": ["x"]}]
        score = _calc_context_precision(outputs)
        assert score == 0.0


class TestContextRecall:
    """测试 Context Recall"""

    def test_full_recall(self):
        """完全召回"""
        outputs = [
            {
                "contexts": ["doc 包含 妖刀姬"],
                "expected_contexts": ["妖刀姬"],
            }
        ]
        score = _calc_context_recall(outputs)
        assert score == 1.0

    def test_partial_recall(self):
        """部分召回"""
        outputs = [
            {
                "contexts": ["doc 1"],
                "expected_contexts": ["期望 1", "期望 2"],
            }
        ]
        score = _calc_context_recall(outputs)
        # 1/2 = 0.5
        assert score == 0.5


class TestFaithfulness:
    """测试 Faithfulness"""

    def test_faithful_answer(self):
        """答案忠于上下文"""
        outputs = [
            {
                "answer": "妖刀姬使用刃返技能",
                "contexts": ["妖刀姬使用 刃返 技能"],
            }
        ]
        score = _calc_faithfulness(outputs)
        assert score == 1.0

    def test_hallucinated_answer(self):
        """答案包含幻觉"""
        outputs = [
            {
                "answer": "完全无关的内容 zzzz aaaa",
                "contexts": ["妖刀姬使用刃返"],
            }
        ]
        score = _calc_faithfulness(outputs)
        # 关键词不匹配，应该 < 1
        assert score < 1.0


class TestAnswerRelevancy:
    """测试 Answer Relevancy"""

    def test_relevant_answer(self):
        """答案相关"""
        outputs = [
            {
                "question": "妖刀姬怎么玩",
                "answer": "妖刀姬使用 刃返 连招",
            }
        ]
        score = _calc_answer_relevancy(outputs)
        assert score == 1.0

    def test_irrelevant_answer(self):
        """答案不相关"""
        outputs = [
            {
                "question": "妖刀姬怎么玩",
                "answer": "这是一个无关的回答",
            }
        ]
        score = _calc_answer_relevancy(outputs)
        # 关键词重叠率低
        assert score < 1.0


class TestEndToEnd:
    """端到端测试"""

    @pytest.mark.asyncio
    async def test_evaluate_rag_system_empty(self):
        """空测试用例"""
        async def mock_rag(q):
            return {"answer": "test", "contexts": []}

        result = await evaluate_rag_system([], mock_rag)
        assert result.test_cases_count == 0

    @pytest.mark.asyncio
    async def test_evaluate_rag_system_basic(self):
        """基本评测"""
        test_cases = [
            {
                "question": "妖刀姬怎么玩",
                "ground_truth": "用刃返连招",
                "expected_contexts": ["妖刀姬", "刃返"],
            }
        ]

        async def mock_rag(q):
            return {
                "answer": "妖刀姬使用 刃返 连招",
                "contexts": ["妖刀姬使用刃返连招"],
            }

        result = await evaluate_rag_system(test_cases, mock_rag)

        assert result.test_cases_count == 1
        assert result.context_precision > 0
        assert result.faithfulness > 0
        assert result.answer_relevancy > 0
        assert result.avg_latency_ms > 0

        print(f"✅ RAGAS 评测结果:")
        print(f"   Context Precision: {result.context_precision:.3f}")
        print(f"   Context Recall: {result.context_recall:.3f}")
        print(f"   Faithfulness: {result.faithfulness:.3f}")
        print(f"   Answer Relevancy: {result.answer_relevancy:.3f}")
        print(f"   Avg Latency: {result.avg_latency_ms:.1f}ms")


if __name__ == "__main__":
    import subprocess
    import sys

    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd="E:/Program Files/vibe_coding/RAG_system",
    )
    sys.exit(result.returncode)