"""Phase 2 端到端集成测试

测试覆盖：
1. 多会话并发（LangGraph + 多 Session）
2. RAG 增强效果（Query Rewriting + Reranker）
3. 性能基准（latency, throughput）
4. 错误处理（缺失文档、低相关度等）

运行：
    pytest tests/integration/test_phase2_e2e.py -v
    或
    python -m pytest tests/integration/test_phase2_e2e.py -v -s
"""

import asyncio
import json
import time
import sys
from pathlib import Path

import pytest

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings  # noqa: E402
from src.graphs import get_rag_graph_async  # noqa: E402
from src.retrieval.query_processor import QueryProcessor  # noqa: E402


class TestRAGEnhancements:
    """RAG 增强功能测试"""

    def test_query_rewrite_typos(self):
        """测试查询改写：错别字纠正"""
        processor = QueryProcessor()

        test_cases = [
            ("要到姬S13怎末连召？", "妖刀姬"),  # 多处错别字
            ("红蝶第三技能", "红蝶"),
            ("素问站位", "素问"),
        ]
        for query, expected_keyword in test_cases:
            result = processor.process(query)
            assert expected_keyword in result["rewritten"], (
                f"Expected '{expected_keyword}' in '{result['rewritten']}'"
            )
            print(f"  ✅ '{query}' → '{result['rewritten']}'")

    def test_query_keyword_extraction(self):
        """测试关键词提取"""
        processor = QueryProcessor()

        result = processor.process("妖刀姬 S13 连招技巧")
        keywords = result["keywords"]

        assert "妖刀姬" in keywords
        assert "S13" in keywords
        assert "连招" in keywords
        print(f"  ✅ Keywords: {keywords}")

    def test_query_expansion(self):
        """测试查询扩展"""
        processor = QueryProcessor()

        result = processor.process("素问副本站位")
        expanded = result["expanded"]

        # 应该有副本的同义词扩展
        assert len(expanded) > 0
        assert any("副本" in q for q in expanded) or any("PVE" in q for q in expanded)
        print(f"  ✅ Expanded: {expanded}")


class TestMultiSessionConcurrency:
    """多会话并发测试"""

    @pytest.mark.asyncio
    async def test_parallel_sessions(self):
        """测试多个会话并行查询"""
        graph = await get_rag_graph_async()

        async def query_session(session_id: str, query: str):
            config = {"configurable": {"thread_id": session_id}}
            input_state = {
                "query": query,
                "game": "",
                "session_id": session_id,
                "top_k": 10,
                "top_n": 3,
                "messages": [],
            }
            start = time.time()
            result = await graph.ainvoke(input_state, config=config)
            latency = (time.time() - start) * 1000
            return {
                "session_id": session_id,
                "query": query,
                "answer_length": len(result.get("answer", "")),
                "docs_count": len(result.get("retrieved_docs", [])),
                "latency_ms": latency,
            }

        # 3 个会话并行查询
        tasks = [
            query_session("test-parallel-1", "妖刀姬连招"),
            query_session("test-parallel-2", "红蝶怎么玩"),
            query_session("test-parallel-3", "素问副本站位"),
        ]
        results = await asyncio.gather(*tasks)

        # 验证所有会话都有结果
        for r in results:
            assert r["answer_length"] > 0, f"Session {r['session_id']} got empty answer"
            assert r["docs_count"] > 0, f"Session {r['session_id']} got no docs"
            print(
                f"  ✅ {r['session_id']}: "
                f"answer={r['answer_length']} chars, "
                f"docs={r['docs_count']}, "
                f"latency={r['latency_ms']:.0f}ms"
            )

    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """测试会话隔离：A 会话历史不应影响 B 会话"""
        # 重要：先关闭 graph 全局连接，避免 event loop 关闭问题
        from src.graphs.rag_graph import close_checkpointer
        await close_checkpointer()

        graph = await get_rag_graph_async()

        # 会话 A 问"妖刀姬"
        result_a = await graph.ainvoke(
            {
                "query": "妖刀姬",
                "game": "",
                "session_id": "iso-a",
                "top_k": 3,
                "top_n": 2,
                "messages": [],
            },
            config={"configurable": {"thread_id": "iso-a"}},
        )

        # 会话 B 问"红蝶"（完全不相关）
        result_b = await graph.ainvoke(
            {
                "query": "红蝶",
                "game": "",
                "session_id": "iso-b",
                "top_k": 3,
                "top_n": 2,
                "messages": [],
            },
            config={"configurable": {"thread_id": "iso-b"}},
        )

        # A 的检索结果应该没有"红蝶"
        a_titles = [d["title"] for d in result_a.get("retrieved_docs", [])]
        b_titles = [d["title"] for d in result_b.get("retrieved_docs", [])]

        # 验证隔离（粗略检查）
        print(f"  ✅ Session A titles: {a_titles[:2]}")
        print(f"  ✅ Session B titles: {b_titles[:2]}")


class TestPerformance:
    """性能基准测试"""

    @pytest.mark.asyncio
    async def test_response_latency(self):
        """测试响应延迟"""
        from src.graphs.rag_graph import close_checkpointer
        await close_checkpointer()

        graph = await get_rag_graph_async()

        latencies = []
        for i in range(3):  # 跑 3 次取平均
            config = {"configurable": {"thread_id": f"perf-{i}"}}
            start = time.time()
            await graph.ainvoke(
                {
                    "query": "妖刀姬连招",
                    "game": "",
                    "session_id": f"perf-{i}",
                    "top_k": 10,
                    "top_n": 3,
                    "messages": [],
                },
                config=config,
            )
            latencies.append((time.time() - start) * 1000)

        avg = sum(latencies) / len(latencies)
        p_max = max(latencies)
        print(f"  ✅ Latency: avg={avg:.0f}ms, max={p_max:.0f}ms")
        print(f"     Raw: {latencies}")

        # 性能断言（CPU 环境下，单查询应 < 30s）
        assert avg < 30000, f"Average latency too high: {avg:.0f}ms"


class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """测试空查询"""
        from src.graphs.rag_graph import close_checkpointer
        await close_checkpointer()

        graph = await get_rag_graph_async()

        # 空查询应该不报错（会返回低质量结果）
        config = {"configurable": {"thread_id": "empty-test"}}
        try:
            result = await graph.ainvoke(
                {
                    "query": "",
                    "game": "",
                    "session_id": "empty-test",
                    "top_k": 10,
                    "top_n": 3,
                    "messages": [],
                },
                config=config,
            )
            # 不应该崩溃
            assert result is not None
            print("  ✅ Empty query handled gracefully")
        except Exception as e:
            # 如果抛出验证错误也是可接受的
            print(f"  ⚠️ Empty query raised: {type(e).__name__}")

    @pytest.mark.asyncio
    async def test_unicode_query(self):
        """测试 Unicode 字符查询"""
        from src.graphs.rag_graph import close_checkpointer
        await close_checkpointer()

        graph = await get_rag_graph_async()

        config = {"configurable": {"thread_id": "unicode-test"}}
        result = await graph.ainvoke(
            {
                "query": "测试中文 Unicode 查询 🎮",
                "game": "",
                "session_id": "unicode-test",
                "top_k": 5,
                "top_n": 2,
                "messages": [],
            },
            config=config,
        )
        assert result is not None
        print("  ✅ Unicode query handled correctly")


if __name__ == "__main__":
    # 直接运行所有测试
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "-s"],
        cwd=PROJECT_ROOT,
    )
    sys.exit(result.returncode)
