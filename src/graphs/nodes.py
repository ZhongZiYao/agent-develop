"""RAG Graph 节点实现

每个节点是一个异步函数，接收 State 并返回部分更新。

Phase 2 增强：
- retrieve_node: 支持混合检索、查询优化、重排
- generate_node: 保持不变
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..config import settings
from ..llm import get_llm, message_text, reasoning_text
from ..pipeline import build_context, retrieve
from ..prompts.templates import SYSTEM_PROMPT, build_user_prompt
from ..schemas import RetrievalResult
from .rag_state import RAGState


async def retrieve_node(state: RAGState) -> dict:
    """检索节点：召回相关文档（支持增强检索）

    Phase 2 增强流程：
    1. Query Processing（查询优化）
    2. Hybrid Retrieval（混合检索）
    3. Reranking（重排）

    Args:
        state: 当前状态（只读 query/game/top_k）

    Returns:
        部分状态更新（retrieved_docs, retrieval_scores）
    """
    query = state["query"]
    top_k = state.get("top_k", settings.top_k)
    game = state.get("game", "")

    # Phase 2: 查询优化
    if settings.query_rewrite_enabled or settings.query_expansion_enabled:
        from ..retrieval.query_processor import QueryProcessor
        processor = QueryProcessor()
        processed = processor.process(
            query,
            enable_rewrite=settings.query_rewrite_enabled,
            enable_expansion=settings.query_expansion_enabled,
        )
        # 使用改写后的查询
        search_queries = processor.get_search_queries(processed)
    else:
        search_queries = [query]

    # Phase 2: 混合检索（如果启用）
    if settings.hybrid_search_enabled:
        from ..retrieval.hybrid_retriever import HybridRetriever
        from ..vectorstore.chroma_store import get_vector_store_instance

        vs = get_vector_store_instance()
        hybrid_retriever = HybridRetriever(vs, bm25_index=None)  # BM25 暂未实现

        # 多查询检索
        if len(search_queries) > 1:
            results = hybrid_retriever.multi_query_search(
                search_queries,
                top_k=top_k,
                game=game,
            )
        else:
            results = hybrid_retriever.search(
                search_queries[0],
                top_k=top_k,
                vector_weight=settings.vector_weight,
                bm25_weight=settings.bm25_weight,
                game=game,
            )
    else:
        # 原始向量检索
        results = retrieve(
            query=query,
            top_k=top_k,
            game=game,
        )

    # Phase 2: 重排（如果启用）
    if settings.rerank_enabled and len(results) > settings.rerank_top_n:
        from ..retrieval.reranker import get_reranker

        reranker = get_reranker(
            model_name=settings.rerank_model,
            device=settings.rerank_device,
        )
        results = reranker.rerank(
            query=query,  # 使用原始查询进行重排
            results=results,
            top_n=settings.rerank_top_n,
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
