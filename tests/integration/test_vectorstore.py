"""Vector Store 单测（需要 Ollama 运行）"""

import os

import pytest

from src.schemas import Chunk
from src.vectorstore.chroma_store import VectorStore, get_vector_store_instance


# 跳过需要 Ollama 的测试（CI 环境无 Ollama）
pytestmark = pytest.mark.skipif(
    not os.environ.get("INTEGRATION_TESTS"),
    reason="需要 Ollama 运行，设置 INTEGRATION_TESTS=1 启用",
)


@pytest.fixture
def vs():
    store = get_vector_store_instance()
    store.reset()
    yield store
    store.reset()


def test_add_and_search(vs: VectorStore):
    """测试 add + search"""
    chunks = [
        Chunk(
            content="永劫无间妖刀姬是近战刺客",
            source="test1.md",
            chunk_id="c1",
            doc_id="d1",
            chunk_index=0,
            metadata={"title": "test1"},
        ),
        Chunk(
            content="逆水寒素问是治疗职业",
            source="test2.md",
            chunk_id="c2",
            doc_id="d2",
            chunk_index=0,
            metadata={"title": "test2"},
        ),
    ]

    n = vs.add(chunks)
    assert n == 2
    assert vs.count() == 2

    results = vs.search("妖刀姬怎么玩", top_k=1)
    assert len(results) == 1
    assert "妖刀姬" in results[0].chunk.content
    assert results[0].score > 0