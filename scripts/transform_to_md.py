"""Driver: 把 data/raw/jsonl 转成 data/raw/md 单文件 .md。

用法:
    python scripts/transform_to_md.py                 # 转所有
    python scripts/transform_to_md.py --source fandom # 只转某源
    python scripts/transform_to_md.py --overwrite     # 覆盖已存在
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.etl.to_markdown import RAW_JSONL_DIR, RAW_MD_DIR, transform_file, transform_all


def main() -> int:
    parser = argparse.ArgumentParser(description="JSONL -> Markdown 转换")
    parser.add_argument("--source", type=str, default=None, help="只转某个 source (fandom/bili/...)")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在文件")
    args = parser.parse_args()

    # Windows GBK 兼容：stdout 强制 UTF-8
    import sys as _sys
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print(f"JSONL 源: {RAW_JSONL_DIR.absolute()}")
    print(f"MD 输出: {RAW_MD_DIR.absolute()}")
    print()

    if args.source:
        # 单源模式：转该 source 目录下所有 JSONL
        jsonl_dir = RAW_JSONL_DIR / args.source
        if not jsonl_dir.exists():
            print(f"[X] Source dir not found: {jsonl_dir}")
            return 1
        total = 0
        for jsonl_path in sorted(jsonl_dir.glob("*.jsonl")):
            if jsonl_path.name.startswith("_"):
                continue
            total += transform_file(jsonl_path, md_dir=RAW_MD_DIR, overwrite=args.overwrite)
        print(f"\n[OK] {args.source}: 转换 {total} 篇")
    else:
        stats = transform_all(overwrite=args.overwrite)
        print("\n=== 转换结果 ===")
        for source, count in stats.items():
            print(f"  {source}: {count} 篇")
        print(f"\n[OK] 总计 {sum(stats.values())} 篇 Markdown")

    return 0


if __name__ == "__main__":
    sys.exit(main())
