"""Phase 6 Agent Trace + Self-RAG 集成测试

测试 /api/v1/chat-agentic/stream 端到端：
1. "你好" → 命中 Self-RAG 黑名单，无 retrieval 事件，agent_trace 含 self_rag_judge
2. "妖刀姬 S13 连招" → 命中白名单，触发 retrieve + agentic_rag
3. done 事件 payload 包含 trace_events 字段
4. agent_done 事件在 done 之前发出

注：依赖真实 LangGraph + minimax 云端 LLM，集成测试运行较慢（每个 ~6-15s）。
仅在 INTEGRATION_TESTS=1 时运行。
"""

import json
import os

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


# 仅在显式开启集成测试时跑（避免常规 CI 烧 token）
pytestmark = pytest.mark.skipif(
    os.environ.get("INTEGRATION_TESTS") != "1",
    reason="需要 INTEGRATION_TESTS=1 才跑（依赖远程 LLM）",
)


@pytest.fixture
def client():
    """FastAPI 测试客户端"""
    return TestClient(app)


def _parse_sse_events(response_text: str) -> list[dict]:
    """解析 SSE 响应为事件列表

    EventSourceResponse 输出格式：
        event: <name>
        data: <json>
        \\n
    """
    events = []
    current_event = None
    current_data = None

    for line in response_text.split("\n"):
        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            current_data = line[5:].strip()
        elif line == "" and current_event and current_data:
            try:
                events.append({
                    "event": current_event,
                    "data": json.loads(current_data),
                })
            except json.JSONDecodeError:
                pass
            current_event = None
            current_data = None

    return events


class TestAgenticStreamChitchat:
    """闲聊型查询走 Self-RAG 黑名单（不检索）"""

    def test_chitchat_query_skips_retrieval(self, client):
        """'你好' → 不应触发 retrieval 事件"""
        with client.stream(
            "POST",
            "/api/v1/chat-agentic/stream",
            json={"query": "你好", "top_k": 5, "top_n": 2},
        ) as response:
            assert response.status_code == 200, response.read().decode("utf-8")
            text = response.read().decode("utf-8")

        events = _parse_sse_events(text)
        event_types = [e["event"] for e in events]

        # 关键断言：Self-RAG 黑名单短路，不应触发 retrieval
        assert "retrieval" not in event_types, (
            f"chitchat query should skip retrieval, got: {event_types}"
        )

    def test_chitchat_emits_self_rag_judge_node(self, client):
        """'你好' → agent_trace 应包含 self_rag_judge 节点"""
        with client.stream(
            "POST",
            "/api/v1/chat-agentic/stream",
            json={"query": "你好", "top_k": 5, "top_n": 2},
        ) as response:
            text = response.read().decode("utf-8")

        events = _parse_sse_events(text)
        trace_events = [e["data"] for e in events if e["event"] == "agent_trace"]
        trace_nodes = {ev.get("node") for ev in trace_events}

        assert "self_rag_judge" in trace_nodes, (
            f"agent_trace should include self_rag_judge, got: {trace_nodes}"
        )
        assert "llm_only_answer" in trace_nodes, (
            f"chitchat path should hit llm_only_answer, got: {trace_nodes}"
        )

    def test_chitchat_done_event_has_trace_events(self, client):
        """done 事件 payload 含 trace_events 字段"""
        with client.stream(
            "POST",
            "/api/v1/chat-agentic/stream",
            json={"query": "你好", "top_k": 5, "top_n": 2},
        ) as response:
            text = response.read().decode("utf-8")

        events = _parse_sse_events(text)
        done_events = [e for e in events if e["event"] == "done"]
        assert len(done_events) >= 1
        done_data = done_events[0]["data"]

        assert "trace_events" in done_data
        assert isinstance(done_data["trace_events"], list)
        assert len(done_data["trace_events"]) > 0

    def test_agent_done_before_done(self, client):
        """agent_done 事件必须在 done 之前发出"""
        with client.stream(
            "POST",
            "/api/v1/chat-agentic/stream",
            json={"query": "你好", "top_k": 5, "top_n": 2},
        ) as response:
            text = response.read().decode("utf-8")

        events = _parse_sse_events(text)
        event_types = [e["event"] for e in events]

        assert "agent_done" in event_types, (
            f"agent_done event missing: {event_types}"
        )
        idx_agent_done = event_types.index("agent_done")
        idx_done = event_types.index("done")
        assert idx_agent_done < idx_done

    def test_chitchat_produces_generation_event(self, client):
        """'你好' 应有 generation 事件（来自 llm_only_answer 节点）"""
        with client.stream(
            "POST",
            "/api/v1/chat-agentic/stream",
            json={"query": "你好", "top_k": 5, "top_n": 2},
        ) as response:
            text = response.read().decode("utf-8")

        events = _parse_sse_events(text)
        event_types = [e["event"] for e in events]

        assert "generation" in event_types, (
            f"chitchat path should emit generation event, got: {event_types}"
        )


class TestAgenticStreamGameEntity:
    """游戏实体查询触发检索"""

    def test_game_entity_triggers_retrieval(self, client):
        """'妖刀姬 S13 连招' → 触发 retrieval"""
        with client.stream(
            "POST",
            "/api/v1/chat-agentic/stream",
            json={"query": "妖刀姬 S13 怎么连招", "top_k": 5, "top_n": 2},
        ) as response:
            assert response.status_code == 200, response.read().decode("utf-8")
            text = response.read().decode("utf-8")

        events = _parse_sse_events(text)
        event_types = [e["event"] for e in events]

        assert "retrieval" in event_types, (
            f"game entity query should trigger retrieval, got: {event_types}"
        )

    def test_game_entity_trace_includes_retrieve(self, client):
        """done.trace_events 应含 retrieve 节点"""
        with client.stream(
            "POST",
            "/api/v1/chat-agentic/stream",
            json={"query": "妖刀姬连招", "top_k": 5, "top_n": 2},
        ) as response:
            text = response.read().decode("utf-8")

        events = _parse_sse_events(text)
        done_events = [e for e in events if e["event"] == "done"]
        done_data = done_events[0]["data"]
        nodes = [ev.get("node") for ev in done_data["trace_events"]]

        assert "self_rag_judge" in nodes, f"self_rag_judge should be in trace, got: {nodes}"
        assert "retrieve" in nodes, f"retrieve should be in trace, got: {nodes}"


class TestBackwardCompatibility:
    """向后兼容：保留原事件"""

    def test_chat_graph_stream_still_works(self, client):
        """旧的 /chat-graph/stream 端点仍工作（Modular RAG）"""
        with client.stream(
            "POST",
            "/api/v1/chat-graph/stream",
            json={"query": "妖刀姬", "top_k": 5, "top_n": 2},
        ) as response:
            assert response.status_code == 200, response.read().decode("utf-8")
            text = response.read().decode("utf-8")

        events = _parse_sse_events(text)
        event_types = [e["event"] for e in events]

        # 旧路径：retrieve + generate
        assert "retrieval" in event_types
        assert "done" in event_types
