"""RAG Graph 单元测试"""

import pytest
import pytest_asyncio

from src.graphs import get_rag_graph_async, close_checkpointer


@pytest_asyncio.fixture
async def graph():
    """异步 fixture：每个测试使用独立的 checkpointer 连接

    pytest-asyncio 默认每个 test 用独立 event loop，
    全局 AsyncSqliteSaver 连接跨 event loop 会失效。
    所以每个 test 前先重置全局状态。
    """
    await close_checkpointer()
    g = await get_rag_graph_async()
    yield g


@pytest.mark.asyncio
async def test_rag_graph_basic_invoke(graph):
    """测试基本执行：单轮对话"""
    result = await graph.ainvoke(
        {
            "query": "妖刀姬怎么连招？",
            "game": "",
            "session_id": "test-basic",
            "top_k": 5,
            "top_n": 3,
            "messages": [],
        },
        config={"configurable": {"thread_id": "test-basic"}},
    )

    assert "answer" in result
    assert "thinking" in result
    assert "retrieved_docs" in result
    assert "messages" in result

    assert len(result["retrieved_docs"]) > 0
    assert result["answer"].strip()

    assert len(result["messages"]) >= 1
    assert result["messages"][-1].content == result["answer"]


@pytest.mark.asyncio
async def test_rag_graph_multi_turn(graph):
    """测试多轮对话：历史累积"""
    thread_id = "test-multi-turn"
    config = {"configurable": {"thread_id": thread_id}}

    result1 = await graph.ainvoke(
        {
            "query": "妖刀姬 1 技能是什么？",
            "game": "",
            "session_id": thread_id,
            "top_k": 5,
            "top_n": 3,
            "messages": [],
        },
        config=config,
    )

    assert len(result1["messages"]) == 1

    result2 = await graph.ainvoke(
        {
            "query": "伤害是多少？",
            "game": "",
            "session_id": thread_id,
            "top_k": 5,
            "top_n": 3,
            "messages": [],
        },
        config=config,
    )

    assert len(result2["messages"]) == 2
    assert result2["answer"].strip()


@pytest.mark.asyncio
async def test_rag_graph_thread_isolation(graph):
    """测试多线程隔离"""
    result_a = await graph.ainvoke(
        {
            "query": "妖刀姬连招？",
            "game": "",
            "session_id": "thread-a",
            "top_k": 5,
            "top_n": 3,
            "messages": [],
        },
        config={"configurable": {"thread_id": "thread-a"}},
    )

    result_b = await graph.ainvoke(
        {
            "query": "红蝶技能？",
            "game": "",
            "session_id": "thread-b",
            "top_k": 5,
            "top_n": 3,
            "messages": [],
        },
        config={"configurable": {"thread_id": "thread-b"}},
    )

    assert len(result_a["messages"]) == 1
    assert len(result_b["messages"]) == 1
    assert result_a["answer"] != result_b["answer"]


@pytest.mark.asyncio
async def test_rag_graph_streaming(graph):
    """测试流式输出"""
    events = []
    async for event in graph.astream(
        {
            "query": "妖刀姬怎么玩？",
            "game": "",
            "session_id": "test-stream",
            "top_k": 5,
            "top_n": 3,
            "messages": [],
        },
        config={"configurable": {"thread_id": "test-stream"}},
        stream_mode="updates",
    ):
        events.append(event)

    event_names = [list(e.keys())[0] for e in events]
    assert "retrieve" in event_names
    assert "generate" in event_names
    assert event_names.index("retrieve") < event_names.index("generate")

    final_event = events[-1]
    assert "generate" in final_event
    assert final_event["generate"]["answer"].strip()
