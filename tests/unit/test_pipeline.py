"""RAG Pipeline 单测（mock LLM）"""

from unittest.mock import MagicMock, patch

import pytest

from src.schemas import Chunk, RetrievalResult
from src.pipeline import build_context, generate


def test_build_context_top_n():
    """测试 context 构建"""
    chunks = [
        RetrievalResult(
            chunk=Chunk(content=f"内容 {i}", metadata={"title": f"标题{i}"}),
            score=1.0 - i * 0.1,
        )
        for i in range(5)
    ]

    formatted, raw = build_context(chunks, top_n=3)
    assert len(formatted) == 3
    assert len(raw) == 3
    assert "[1]" in formatted[0]
    assert "[3]" in formatted[2]


def test_generate_with_mock():
    """测试生成（mock LLM）"""
    mock_response = MagicMock()
    mock_response.content = "这是测试答案 [1]"
    mock_response.response_metadata = {
        "token_usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    }

    with patch("src.pipeline.get_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        answer, usage = generate("测试 query", ["[1] 标题：test\n内容：xxx"])
        assert "测试答案" in answer
        assert usage["total_tokens"] == 150