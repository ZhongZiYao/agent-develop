"""索引重建脚本

用法：
  python scripts/rebuild_index.py                    # 用默认配置
  python scripts/rebuild_index.py --force-rebuild    # 强制重建
  python scripts/rebuild_index.py --source ./data/raw/yongjiewujian
  python scripts/rebuild_index.py --chunk-size 300   # 自定义切分大小
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

# 把项目根目录加到 sys.path（这样可以直接 python scripts/rebuild_index.py 跑）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings  # noqa: E402
from src.loaders.markdown_loader import load_markdown_dir  # noqa: E402
from src.splitters.recursive_splitter import split_documents  # noqa: E402
from src.vectorstore.chroma_store import get_vector_store_instance  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="重建 RAG 索引")
    parser.add_argument("--source", type=str, default=settings.raw_data_dir, help="文档目录")
    parser.add_argument("--force-rebuild", action="store_true", help="强制重建（先清空）")
    parser.add_argument("--chunk-size", type=int, default=settings.chunk_size)
    parser.add_argument("--chunk-overlap", type=int, default=settings.chunk_overlap)
    args = parser.parse_args()

    logger.info(f"开始构建索引")
    logger.info(f"  source: {args.source}")
    logger.info(f"  chunk_size: {args.chunk_size}, overlap: {args.chunk_overlap}")
    logger.info(f"  force_rebuild: {args.force_rebuild}")

    # 1. 加载文档
    source_dir = Path(args.source)
    if not source_dir.exists():
        logger.error(f"目录不存在: {source_dir}")
        sys.exit(1)

    docs = load_markdown_dir(source_dir)
    logger.info(f"加载了 {len(docs)} 个文档")

    if not docs:
        logger.warning("没有找到任何 .md 文档")
        return

    # 2. 切分
    chunks = split_documents(docs, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    logger.info(f"切分为 {len(chunks)} 个 chunk")

    # 3. 写入向量库
    vs = get_vector_store_instance()

    if args.force_rebuild:
        logger.warning("强制重建：清空当前 collection")
        vs.reset()

    if vs.count() > 0 and not args.force_rebuild:
        logger.info(f"当前 collection 有 {vs.count()} 条记录，新增 {len(chunks)} 条")
    else:
        logger.info(f"将写入 {len(chunks)} 条记录")

    n = vs.add(chunks)
    logger.success(f"索引完成！共写入 {n} 条")
    logger.info(f"当前 collection 总数: {vs.count()}")


if __name__ == "__main__":
    main()