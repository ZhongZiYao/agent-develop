"""Trace Dispatch 单测

验证 graph_routes 在不同节点名 + 不同 enable_agent_trace flag 下的事件发射逻辑：
1. retrieve/generate 节点 → retrieval/thinking/generation 事件（向后兼容）
2. self_rag_judge 节点 → 无 retrieval 事件（不需要检索路径）
3. enable_agent_trace=False 时不发出 agent_trace / agent_done
4. 未知节点 → 不静默丢弃，至少 agent_trace fallback
5. done 事件 payload 包含 trace_events

策略：mock 一个 minimal async graph + 替换 get_rag_graph_async / _persist_turn
不依赖真实 LLM、真实 graph、真实数据库。
"""

import json

import pytest

from src.api.graph_routes import chat_graph_stream
from src.api.schemas import QueryRequest


class _FakeGraph:
    """模拟 LangGraph，只产出预设的节点事件序列"""

    def __init__(self, events: list[dict]):
        self._events = events

    async def astream(self, input_state, config=None, stream_mode="updates"):
        for ev in self._events:
            yield ev

    async def aget_state(self, config):
        class _State:
            values = {"retrieved_docs": []}

        return _State()


async def _no_persist(*args, **kwargs):
    """替代 _persist_turn 的 async no-op"""
    return None


async def _collect(req: QueryRequest, fake_events: list[dict]) -> list[dict]:
    """调用 chat_graph_stream 收集所有 yield 的事件

    EventSourceResponse body_iterator yield 的就是 dict（已含 event/data）。
    """
    from src import api.graph_routes as gr

    async def fake_get_graph():
        return _FakeGraph(fake_events)

    gr.get_rag_graph_async = fake_get_graph
    gr._persist_turn = _no_persist

    response = await chat_graph_stream(req)
    out = []
    async for ev in response.body_iterator:
        if isinstance(ev, dict):
            out.append(ev)
    return out


def _setup_settings(monkeypatch, enable_agent_trace: str, use_langgraph: str = "true"):
    """monkeypatch env + 清除 settings 缓存

    注：graph_routes 已在生产代码里改成 get_settings() 重新读，
    所以我们只需清 cache，单测和 .env 切换都能正确生效。
    """
    monkeypatch.setenv("ENABLE_AGENT_TRACE", enable_agent_trace)
    monkeypatch.setenv("USE_LANGGRAPH", use_langgraph)
    from src.config import get_settings

    get_settings.cache_clear()


class TestRetrieveNodeDispatch:
    """retrieve 节点事件测试（向后兼容）"""

    @pytest.mark.asyncio
    async def test_retrieve_emits_retrieval_event(self, monkeypatch):
        """retrieve 节点 → 发出 retrieval 事件 + chunks_retrieved 字段正确"""
        _setup_settings(monkeypatch, "true")

        events = await _collect(
            QueryRequest(query="妖刀姬", game=""),
            [
                {"retrieve": {"retrieved_docs": [{"id": str(i)} for i in range(3)]}},
                {"generate": {"answer": "x", "thinking": ""}},
            ],
        )

        event_types = [e.get("event") for e in events]

        # 向后兼容事件
        assert "retrieval" in event_types, f"应发出 retrieval 事件，实际: {event_types}"
        assert "generation" in event_types
        assert "done" in event_types

        # Agent Trace 事件（flag 开启）
        assert "agent_trace" in event_types
        assert "agent_done" in event_types

        # retrieval payload 校验
        retrieval = [
            json.loads(e["data"]) for e in events if e.get("event") == "retrieval"
        ]
        assert len(retrieval) == 1
        assert retrieval[0]["chunks_retrieved"] == 3
        assert retrieval[0]["node"] == "retrieve"


class TestGenerateNodeDispatch:
    """generate 节点事件测试"""

    @pytest.mark.asyncio
    async def test_generate_emits_thinking_and_generation(self, monkeypatch):
        """generate 节点 → thinking（如果有）+ generation 事件"""
        _setup_settings(monkeypatch, "true")

        events = await _collect(
            QueryRequest(query="x", game=""),
            [
                {"retrieve": {"retrieved_docs": []}},
                {
                    "generate": {
                        "answer": "最终答案",
                        "thinking": "我应该先思考",
                    }
                },
            ],
        )

        event_types = [e.get("event") for e in events]
        assert "thinking" in event_types
        assert "generation" in event_types

        # thinking + generation payload
        thinking = [json.loads(e["data"]) for e in events if e.get("event") == "thinking"]
        generation = [
            json.loads(e["data"]) for e in events if e.get("event") == "generation"
        ]
        assert thinking[0]["delta"] == "我应该先思考"
        assert generation[0]["delta"] == "最终答案"


class TestAgentTraceDisabled:
    """enable_agent_trace=False 时不发出 agent_* 事件"""

    @pytest.mark.asyncio
    async def test_no_agent_trace_when_disabled(self, monkeypatch):
        """flag 关闭时不应有 agent_trace / agent_done"""
        _setup_settings(monkeypatch, "false")

        events = await _collect(
            QueryRequest(query="x", game=""),
            [
                {"retrieve": {"retrieved_docs": [{"id": "1"}]}},
                {"generate": {"answer": "x", "thinking": ""}},
            ],
        )

        event_types = [e.get("event") for e in events]

        # 关键断言：不应有 agent_trace / agent_done
        assert "agent_trace" not in event_types, f"flag 关闭时不应有 agent_trace，实际: {event_types}"
        assert "agent_done" not in event_types

        # 向后兼容：retrieval/generation/done 仍应有
        assert "retrieval" in event_types
        assert "generation" in event_types
        assert "done" in event_types


class TestUnknownNodeFallback:
    """未知节点 → 不静默丢弃（agent_trace fallback）"""

    @pytest.mark.asyncio
    async def test_unknown_node_has_agent_trace(self, monkeypatch):
        """未知节点仍应有 agent_trace{started, completed}"""
        _setup_settings(monkeypatch, "true")

        events = await _collect(
            QueryRequest(query="x", game=""),
            [
                {"new_fancy_node_v2": {"answer": "x"}},
            ],
        )

        trace_datas = [
            json.loads(e["data"])
            for e in events
            if e.get("event") == "agent_trace"
        ]

        # 至少 started + completed
        assert len(trace_datas) >= 2
        statuses = [d.get("status") for d in trace_datas]
        assert "started" in statuses
        assert "completed" in statuses

        # 节点名正确传递
        for d in trace_datas:
            assert d["node"] == "new_fancy_node_v2"


class TestDoneEventTraceEvents:
    """done 事件 payload 包含 trace_events"""

    @pytest.mark.asyncio
    async def test_done_event_includes_trace_events_when_enabled(self, monkeypatch):
        """flag 开启时 done.trace_events 非空且含各节点"""
        _setup_settings(monkeypatch, "true")

        events = await _collect(
            QueryRequest(query="x", game=""),
            [
                {"router": {"route": "direct_rag"}},
                {"retrieve": {"retrieved_docs": [{"id": "1"}]}},
                {"generate": {"answer": "x", "thinking": ""}},
            ],
        )

        done_data = None
        for e in events:
            if e.get("event") == "done":
                done_data = json.loads(e["data"])
                break

        assert done_data is not None
        assert "trace_events" in done_data
        assert isinstance(done_data["trace_events"], list)
        nodes = [ev.get("node") for ev in done_data["trace_events"]]
        assert "router" in nodes
        assert "retrieve" in nodes
        assert "generate" in nodes

    @pytest.mark.asyncio
    async def test_done_event_empty_trace_when_disabled(self, monkeypatch):
        """flag 关闭时 done.trace_events 是空数组"""
        _setup_settings(monkeypatch, "false")

        events = await _collect(
            QueryRequest(query="x", game=""),
            [
                {"retrieve": {"retrieved_docs": [{"id": "1"}]}},
                {"generate": {"answer": "x", "thinking": ""}},
            ],
        )

        done_data = None
        for e in events:
            if e.get("event") == "done":
                done_data = json.loads(e["data"])
                break

        assert done_data is not None
        assert done_data.get("trace_events") == []


class TestSelfRagSkipNoRetrieval:
    """Self-RAG 判定为 skip 时不走 retrieve"""

    @pytest.mark.asyncio
    async def test_skip_path_emits_self_rag_judge_node(self, monkeypatch):
        """need_retrieval=False → self_rag_judge 节点出现在 trace 中，没有 retrieval 事件"""
        _setup_settings(monkeypatch, "true")

        events = await _collect(
            QueryRequest(query="你好", game=""),
            [
                {"router": {"route": "direct_rag", "query_type": "simple"}},
                {
                    "self_rag_judge": {
                        "need_retrieval": False,
                        "self_rag_confidence": 0.95,
                    }
                },
                {
                    "llm_only_answer": {
                        "answer": "你好！",
                        "thinking": "",
                        "retrieved_docs": [],
                    }
                },
            ],
        )

        event_types = [e.get("event") for e in events]
        # 不应有 retrieval（因为跳过了检索）
        assert "retrieval" not in event_types, f"skip 路径不应有 retrieval 事件，实际: {event_types}"

        # agent_trace 应覆盖 self_rag_judge 和 llm_only_answer
        trace_datas = [
            json.loads(e["data"])
            for e in events
            if e.get("event") == "agent_trace"
        ]
        trace_nodes = {d["node"] for d in trace_datas}
        assert "self_rag_judge" in trace_nodes
        assert "llm_only_answer" in trace_nodes
