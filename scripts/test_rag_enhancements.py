"""RAG 增强功能测试脚本

测试：
1. Query Processing（查询优化）
2. Hybrid Retrieval（混合检索）
3. Reranking（重排）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


async def test_query_processor():
    """测试查询优化"""
    from src.retrieval.query_processor import QueryProcessor

    logger.info("=" * 50)
    logger.info("测试 Query Processor")
    logger.info("=" * 50)

    processor = QueryProcessor()

    test_queries = [
        "妖刀姬 S13 怎么连招？",
        "红蝶bug",
        "素问副本怎么玩",
    ]

    for query in test_queries:
        logger.info(f"\n原始查询: {query}")
        result = processor.process(query, enable_rewrite=True, enable_expansion=True)
        logger.info(f"  改写后: {result['rewritten']}")
        logger.info(f"  关键词: {result['keywords']}")
        logger.info(f"  扩展查询: {result['expanded']}")


async def test_hybrid_retrieval():
    """测试混合检索"""
    from src.retrieval.hybrid_retriever import HybridRetriever
    from src.vector_store import get_vector_store_instance

    logger.info("\n" + "=" * 50)
    logger.info("测试 Hybrid Retrieval")
    logger.info("=" * 50)

    vs = get_vector_store_instance()
    retriever = HybridRetriever(vs, bm25_index=None)

    query = "妖刀姬 S13 连招技巧"
    logger.info(f"\n查询: {query}")

    results = retriever.search(query, top_k=10, vector_weight=0.7, bm25_weight=0.3)

    logger.info(f"检索到 {len(results)} 条结果:")
    for i, result in enumerate(results[:5], 1):
        logger.info(f"  [{i}] score={result.score:.4f} | {result.chunk.content[:50]}...")


async def test_reranker():
    """测试重排"""
    from src.retrieval.reranker import Reranker
    from src.vector_store import get_vector_store_instance
    from src.pipeline import retrieve

    logger.info("\n" + "=" * 50)
    logger.info("测试 Reranker")
    logger.info("=" * 50)

    query = "妖刀姬连招"
    logger.info(f"\n查询: {query}")

    # 1. 向量检索
    logger.info("步骤 1: 向量检索 top_k=20")
    results = retrieve(query, top_k=20)
    logger.info(f"  检索到 {len(results)} 条结果")
    logger.info(f"  Top 3 分数: {[f'{r.score:.4f}' for r in results[:3]]}")

    # 2. 重排
    logger.info("\n步骤 2: Reranker 重排到 top_n=10")
    reranker = Reranker(model_name="BAAI/bge-reranker-v2-m3", device="cpu")
    reranked = reranker.rerank(query, results, top_n=10)

    logger.info(f"  重排后 {len(reranked)} 条结果")
    logger.info(f"  Top 3 分数: {[f'{r.score:.4f}' for r in reranked[:3]]}")

    logger.info("\n对比前 3 条内容:")
    for i in range(min(3, len(reranked))):
        logger.info(f"  [{i+1}] 原始排名: #{i+1} → 重排后: #{i+1}")
        logger.info(f"      {reranked[i].chunk.content[:80]}...")


async def test_full_pipeline():
    """测试完整增强 Pipeline"""
    from src.config import settings
    from src.graphs import get_rag_graph_async

    logger.info("\n" + "=" * 50)
    logger.info("测试完整 RAG Pipeline（启用所有增强）")
    logger.info("=" * 50)

    # 临时启用所有增强功能
    original_flags = {
        "query_rewrite_enabled": settings.query_rewrite_enabled,
        "query_expansion_enabled": settings.query_expansion_enabled,
        "hybrid_search_enabled": settings.hybrid_search_enabled,
        "rerank_enabled": settings.rerank_enabled,
    }

    settings.query_rewrite_enabled = True
    settings.query_expansion_enabled = True
    settings.hybrid_search_enabled = False  # BM25 未实现，暂时关闭
    settings.rerank_enabled = True
    settings.rerank_top_n = 10

    try:
        graph = await get_rag_graph_async()

        query = "妖刀姬 S13 怎么连招？"
        logger.info(f"\n查询: {query}")

        config = {"configurable": {"thread_id": "test-enhanced"}}
        input_state = {
            "query": query,
            "game": "",
            "session_id": "test",
            "top_k": 20,
            "top_n": 5,
            "messages": [],
        }

        logger.info("执行 LangGraph...")
        result = await graph.ainvoke(input_state, config=config)

        logger.info(f"\n检索到 {len(result['retrieved_docs'])} 条文档")
        logger.info(f"答案长度: {len(result.get('answer', ''))} 字符")
        logger.info(f"答案预览: {result.get('answer', '')[:200]}...")

    finally:
        # 恢复原始配置
        for key, value in original_flags.items():
            setattr(settings, key, value)


async def main():
    """运行所有测试"""
    logger.info("开始 RAG 增强功能测试\n")

    try:
        await test_query_processor()
        await test_hybrid_retrieval()
        # await test_reranker()  # 需要下载模型，可选
        # await test_full_pipeline()  # 完整测试
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
