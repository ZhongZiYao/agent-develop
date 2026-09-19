"""RAG Graph 节点实现

每个节点是一个异步函数，接收 State 并返回部分更新。
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..llm import get_llm, message_text, reasoning_text
from ..pipeline import build_context, retrieve
from ..prompts.templates import SYSTEM_PROMPT, build_user_prompt
from ..schemas import RetrievalResult
from .rag_state import RAGState


async def retrieve_node(state: RAGState) -> dict:
    """检索节点：召回相关文档

    Args:
        state: 当前状态（只读 query/game/top_k）

    Returns:
        部分状态更新（retrieved_docs, retrieval_scores）
    """
    # 调用现有检索逻辑
    results = retrieve(
        query=state["query"],
        top_k=state.get("top_k", 10),
        game=state.get("game", ""),
    )

    # 转换为字典格式
    retrieved_docs = [
        {
            "id": r.chunk.chunk_id,
            "content": r.chunk.content,
            "score": r.score,
            "metadata": r.chunk.metadata,
            "title": r.chunk.metadata.get("title", ""),
            "source": r.chunk.metadata.get("source", ""),
        }
        for r in results
    ]

    return {
        "retrieved_docs": retrieved_docs,
        "retrieval_scores": [r.score for r in results],
    }


async def generate_node(state: RAGState) -> dict:
    """生成节点：基于检索结果生成答案

    Args:
        state: 当前状态（读取 query/retrieved_docs/top_n/messages）

    Returns:
        部分状态更新（thinking, answer, messages）
    """
    from ..schemas import Chunk

    # 1. 构造 context
    results = [
        RetrievalResult(
            chunk=Chunk(
                chunk_id=d['id'],
                content=d['content'],
                source=d.get('source', ''),
                metadata=d['metadata'],
            ),
            score=d['score'],
        )
        for d in state["retrieved_docs"]
    ]

    context_chunks, _ = build_context(results, top_n=state.get("top_n", 5))

    # 2. 构造 messages
    user_prompt = build_user_prompt(
        query=state["query"],
        context_chunks=context_chunks,
        game=state.get("game", ""),
    )

    # LangGraph 会自动管理历史，这里只添加当前轮的 user message
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state.get("messages", []),  # 历史对话
        HumanMessage(content=user_prompt),
    ]

    # 3. 同步调用 LLM（非流式）
    llm = get_llm()
    response = await llm.ainvoke(messages)

    # 4. 提取 thinking 和 answer
    raw_answer = message_text(response)
    structured_thinking = reasoning_text(response)

    # 如果 reasoning_text 为空，尝试从 answer 中解析 <think> 标签（兜底）
    if structured_thinking:
        thinking_content = structured_thinking
        clean_answer = raw_answer
    else:
        from ..prompts.thinking_parser import parse_thinking
        clean_answer, tagged_thinking = parse_thinking(raw_answer)
        thinking_content = tagged_thinking

    # 5. 返回更新
    return {
        "thinking": thinking_content,
        "answer": clean_answer,
        "messages": [AIMessage(content=clean_answer)],
    }
