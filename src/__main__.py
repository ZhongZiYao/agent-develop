"""CLI 入口 — `python -m src` 命令

子命令：
  index    重建索引
  query    问答
  serve    启动 FastAPI 服务
"""

from __future__ import annotations

import argparse
import sys


def cmd_index(args):
    """重建索引"""
    from pathlib import Path

    from loguru import logger

    from src.config import settings
    from src.loaders.markdown_loader import load_markdown_dir
    from src.splitters.recursive_splitter import split_documents
    from src.vectorstore.chroma_store import get_vector_store_instance

    source = Path(args.source or settings.raw_data_dir)
    docs = load_markdown_dir(source)
    chunks = split_documents(docs)

    vs = get_vector_store_instance()
    if args.force:
        vs.reset()
    n = vs.add(chunks)
    logger.success(f"索引完成，共 {n} 条")


def cmd_query(args):
    """单次问答"""
    from src.pipeline import run_rag

    result = run_rag(args.query, game=args.game or "")
    print(f"\n{result.answer}\n")
    print(f"延迟: {result.latency_ms:.0f}ms | tokens: {result.usage.get('total_tokens', 0)}")


def cmd_serve(args):
    """启动 FastAPI"""
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=args.reload,
    )


def main():
    parser = argparse.ArgumentParser(prog="gameguide", description="GameGuide AI CLI")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # index
    p_index = subparsers.add_parser("index", help="重建索引")
    p_index.add_argument("--source", type=str, default="")
    p_index.add_argument("--force", action="store_true", help="强制重建")
    p_index.set_defaults(func=cmd_index)

    # query
    p_query = subparsers.add_parser("query", help="单次问答")
    p_query.add_argument("query", type=str)
    p_query.add_argument("--game", type=str, default="")
    p_query.set_defaults(func=cmd_query)

    # serve
    p_serve = subparsers.add_parser("serve", help="启动 FastAPI")
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()