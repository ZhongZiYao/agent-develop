"""Self-RAG 单元测试

测试 Self-RAG 节点的三级判断逻辑：
1. 黑名单短路（闲聊）
2. 白名单短路（游戏实体）
3. LLM 自评
"""

import pytest

from src.agents.self_rag import (
    CHITCHAT_PATTERNS,
    GAME_ENTITY_KEYWORDS,
    llm_only_answer_node,
    self_rag_judge_node,
)


class TestSelfRAGJudge:
    """Self-RAG 判断节点测试"""

    @pytest.mark.asyncio
    async def test_blacklist_chitchat(self):
        """测试黑名单：闲聊型查询不需要检索"""
        test_cases = [
            "你好",
            "hi",
            "Hello",
            "谢谢",
            "再见",
            "你是谁",
            "你能做什么",
        ]

        for query in test_cases:
            state = {
                "query": query,
                "query_type": "simple",
                "trace_events": [],
            }

            result = await self_rag_judge_node(state)

            assert result["need_retrieval"] is False, f"黑名单查询「{query}」应该 need_retrieval=False"
            assert result["self_rag_confidence"] >= 0.9, "黑名单匹配置信度应该高"
            assert "闲聊" in result["self_rag_reason"] or "无需检索" in result["self_rag_reason"]
            assert len(result["trace_events"]) == 2  # started + completed

    @pytest.mark.asyncio
    async def test_whitelist_game_entity(self):
        """测试白名单：游戏实体查询必须检索"""
        test_cases = [
            "妖刀姬怎么连招",
            "红蝶第三技能是什么",
            "S13 赛季更新内容",
            "副本 boss 怎么打",
            "E-4048 错误码怎么解决",
            "素问装备推荐",
        ]

        for query in test_cases:
            state = {
                "query": query,
                "query_type": "simple",
                "trace_events": [],
            }

            result = await self_rag_judge_node(state)

            assert result["need_retrieval"] is True, f"白名单查询「{query}」应该 need_retrieval=True"
            assert result["self_rag_confidence"] >= 0.85, "白名单匹配置信度应该高"
            assert "游戏实体" in result["self_rag_reason"] or "必须检索" in result["self_rag_reason"]
            assert len(result["trace_events"]) == 2  # started + completed

    @pytest.mark.asyncio
    async def test_llm_judge_fallback(self):
        """测试 LLM 自评：黑白名单都没命中的走 LLM 判断

        注：这个测试依赖真实 LLM，可能较慢或不稳定（mock 测试见下）
        """
        state = {
            "query": "今天天气怎么样",  # 既不是闲聊，也不是游戏实体
            "query_type": "simple",
            "trace_events": [],
        }

        result = await self_rag_judge_node(state)

        # LLM 应该判断这是通用知识，不需要游戏攻略检索
        # （但 LLM 可能不稳定，所以只验证字段存在）
        assert "need_retrieval" in result
        assert "self_rag_confidence" in result
        assert "self_rag_reason" in result
        assert len(result["trace_events"]) == 2

    @pytest.mark.asyncio
    async def test_trace_events_structure(self):
        """测试 trace_events 结构"""
        state = {
            "query": "你好",
            "query_type": "simple",
            "trace_events": [],
        }

        result = await self_rag_judge_node(state)

        events = result["trace_events"]
        assert len(events) == 2

        # started 事件
        assert events[0]["node"] == "self_rag_judge"
        assert events[0]["type"] == "agent_trace"
        assert events[0]["status"] == "started"
        assert "ts" in events[0]

        # completed 事件
        assert events[1]["node"] == "self_rag_judge"
        assert events[1]["type"] == "agent_trace"
        assert events[1]["status"] == "completed"
        assert "payload" in events[1]
        assert events[1]["payload"]["need_retrieval"] is False


class TestLLMOnlyAnswer:
    """LLM 直答节点测试"""

    @pytest.mark.asyncio
    async def test_llm_only_answer(self):
        """测试 LLM 直答节点"""
        state = {
            "query": "你好",
            "trace_events": [],
        }

        result = await llm_only_answer_node(state)

        assert "answer" in result
        assert len(result["answer"]) > 0
        assert result["thinking"] == ""  # 无思考过程
        assert result["retrieved_docs"] == []  # 无检索文档
        assert len(result["trace_events"]) == 2  # started + completed

    @pytest.mark.asyncio
    async def test_llm_only_trace_events(self):
        """测试 LLM 直答的 trace_events"""
        state = {
            "query": "你是谁",
            "trace_events": [],
        }

        result = await llm_only_answer_node(state)

        events = result["trace_events"]
        assert len(events) == 2

        # started
        assert events[0]["node"] == "llm_only_answer"
        assert events[0]["status"] == "started"

        # completed
        assert events[1]["node"] == "llm_only_answer"
        assert events[1]["status"] == "completed"
        assert "answer_len" in events[1]["payload"]


class TestPatterns:
    """测试黑白名单 pattern 覆盖率"""

    def test_chitchat_patterns(self):
        """测试闲聊 pattern 是否覆盖常见场景"""
        import re

        test_cases = [
            ("你好", True),
            ("Hi", True),
            ("hello world", True),
            ("谢谢你", True),
            ("再见", True),
            ("妖刀姬你好", False),  # 不是纯闲聊
        ]

        for query, should_match in test_cases:
            matched = any(re.search(pat, query, re.IGNORECASE) for pat in CHITCHAT_PATTERNS)
            assert matched == should_match, f"「{query}」匹配结果应为 {should_match}"

    def test_game_entity_keywords(self):
        """测试游戏实体关键词是否覆盖常见角色/技能"""
        assert "妖刀姬" in GAME_ENTITY_KEYWORDS
        assert "红蝶" in GAME_ENTITY_KEYWORDS
        assert "S13" in GAME_ENTITY_KEYWORDS
        assert "连招" in GAME_ENTITY_KEYWORDS
        assert "副本" in GAME_ENTITY_KEYWORDS
        assert "E-4048" in GAME_ENTITY_KEYWORDS
