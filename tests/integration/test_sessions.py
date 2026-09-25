"""Session / Memory 集成测试（不调用真实 MiniMax / Ollama）。"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from langchain_core.messages import AIMessageChunk

from src.api import main as api_main
from src.pipeline import load_history
from src.schemas import Chunk, RetrievalResult
from src.storage.database import init_db


class FakeStreamingLLM:
    async def astream(self, _messages):
        for text in [
            "<think>需要结合上一轮问题",
            "判断代词指向</think>",
            "## 回答\n\n1 技能是「刃返」[1]。",
        ]:
            yield AIMessageChunk(content=text)


@pytest.mark.asyncio
async def test_stream_persists_session_and_restores_history(monkeypatch):
    await init_db()

    chunk = Chunk(
        content="妖刀姬 S13 的 1 技能是刃返。",
        metadata={"title": "妖刀姬攻略"},
        source="test.md",
        chunk_id="test-chunk",
        doc_id="test-doc",
    )
    monkeypatch.setattr(
        api_main,
        "retrieve",
        lambda *_args, **_kwargs: [
            RetrievalResult(chunk=chunk, score=0.95, rank=0)
        ],
    )
    monkeypatch.setattr(api_main, "get_streaming_llm", lambda: FakeStreamingLLM())

    import src.storage.naming_v2 as naming

    async def fake_title(_query: str, context: str = "", fallback: str | None = None, max_retries: int = 2) -> str:
        return "妖刀姬技能"

    async def fake_rename(_session_id: str, _new_title: str) -> bool:
        return True

    monkeypatch.setattr(naming, "generate_session_title", fake_title)
    monkeypatch.setattr(naming, "rename_session_async", fake_rename)

    transport = httpx.ASGITransport(app=api_main.app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
    ) as client:
        created = await client.post("/api/v1/sessions", json={})
        assert created.status_code == 201
        session_id = created.json()["id"]

        try:
            events: list[tuple[str, dict]] = []
            async with client.stream(
                "POST",
                "/api/v1/stream",
                json={
                    "query": "妖刀姬的一技能是什么？",
                    "session_id": session_id,
                    "top_k": 5,
                    "top_n": 3,
                },
            ) as response:
                assert response.status_code == 200
                current_event = ""
                async for line in response.aiter_lines():
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        events.append(
                            (current_event, json.loads(line[5:].strip()))
                        )

            event_names = [name for name, _ in events]
            assert "thinking" in event_names
            assert "generation" in event_names
            assert "done" in event_names

            done = next(data for name, data in events if name == "done")
            assert done["has_thinking"] is True
            assert "代词指向" in done["thinking"]
            assert "刃返" in done["answer"]
            assert "<think>" not in done["answer"]

            detail = await client.get(f"/api/v1/sessions/{session_id}")
            assert detail.status_code == 200
            messages = detail.json()["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "user"
            assert messages[1]["role"] == "assistant"
            assert "代词指向" in messages[1]["thinking"]
            assert messages[1]["retrieved_docs"][0]["title"] == "妖刀姬攻略"

            history = await load_history(session_id)
            assert [item["role"] for item in history] == ["user", "assistant"]
            assert "刃返" in history[-1]["content"]

            # 等待后台命名任务收尾，避免测试结束后悬空。
            await asyncio.sleep(0)
        finally:
            deleted = await client.delete(f"/api/v1/sessions/{session_id}")
            assert deleted.status_code == 204
            missing = await client.get(f"/api/v1/sessions/{session_id}")
            assert missing.status_code == 404
