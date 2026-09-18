"""命令行问答工具

用法：
  python scripts/cli_query.py "妖刀姬怎么连招？"
  python scripts/cli_query.py "E-4048 错误码" --game 永劫无间
  python scripts/cli_query.py "妖刀姬怎么连招？" --stream
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from loguru import logger  # noqa: E402

from src.config import settings  # noqa: E402
from src.pipeline import run_rag  # noqa: E402


def run_sync(query: str, game: str):
    """同步问答"""
    result = run_rag(query, game=game)

    print("\n" + "=" * 60)
    print(f"Q: {query}")
    print("=" * 60)
    print(f"\n{result.answer}\n")

    if result.retrieved_docs:
        print("─" * 60)
        print(f"参考资料（{len(result.retrieved_docs)} 条）：")
        for i, r in enumerate(result.retrieved_docs[: settings.top_n], 1):
            title = r.chunk.metadata.get("title", "未知")
            print(f"  [{i}] {title} (score={r.score:.3f})")

    print("─" * 60)
    print(f"延迟: {result.latency_ms:.0f}ms | tokens: {result.usage.get('total_tokens', 0)}")
    print("=" * 60)


async def run_stream(query: str, game: str):
    """流式问答"""
    from langchain_core.messages import HumanMessage, SystemMessage

    from src.llm import get_streaming_llm
    from src.pipeline import build_context, retrieve
    from src.prompts.templates import SYSTEM_PROMPT, build_user_prompt

    print(f"\nQ: {query}\n")
    print("A: ", end="", flush=True)

    results = retrieve(query, top_k=settings.top_k, game=game)
    context_chunks, _ = build_context(results, top_n=settings.top_n)

    llm = get_streaming_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=build_user_prompt(query, context_chunks, game)),
    ]

    async for chunk in llm.astream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
    print("\n")


def main():
    parser = argparse.ArgumentParser(description="命令行 RAG 问答")
    parser.add_argument("query", type=str, help="问题")
    parser.add_argument("--game", type=str, default="", help="游戏名")
    parser.add_argument("--stream", action="store_true", help="流式输出")
    args = parser.parse_args()

    if args.stream:
        asyncio.run(run_stream(args.query, args.game))
    else:
        run_sync(args.query, args.game)


if __name__ == "__main__":
    main()