"""PDF 扫描器 — 扫描理财文件目录，统计分布 + 选取 POC 子集。

输出:
1. 终端: 文件总数 / 机构分布 / 类型分布
2. data/clean/poc_files.json: 100 PDF POC 文件列表

选样策略:
- 从每个机构/事项组合中均匀采样
- 优先选短 PDF (<=10 页) 跑通 POC
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from loguru import logger

from src.config import settings
from src.loaders.pdf_loader import _extract_dir_meta, load_pdf_file


def scan_pdfs(pdf_dir: Path | str = None) -> dict:
    """扫描 PDF 目录，返回统计信息"""
    pdf_dir = Path(pdf_dir or settings.pdf_data_dir)
    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF 目录不存在: {pdf_dir}")

    files = sorted(pdf_dir.rglob("*.pdf"))
    logger.info(f"扫描 {pdf_dir}: 共 {len(files)} 个 PDF")

    # 分布统计
    by_inst: dict[str, int] = defaultdict(int)
    by_type: dict[str, int] = defaultdict(int)
    by_category: dict[str, int] = defaultdict(int)
    by_inst_type: dict[tuple[str, str], int] = defaultdict(int)

    for f in files:
        meta = _extract_dir_meta(f)
        by_inst[meta["institution"] or "未知"] += 1
        by_type[meta["report_type"] or "未知"] += 1
        # 一级分类
        for p in f.parts:
            if p in {"产品说明书&发行公告", "定期报告", "临时报告"}:
                cat = {"产品说明书&发行公告": "产品说明书"}.get(p, p)
                by_category[cat] += 1
                break
        by_inst_type[(meta["institution"], meta["report_type"])] += 1

    return {
        "total": len(files),
        "by_institution": dict(by_inst),
        "by_report_type": dict(by_type),
        "by_category": dict(by_category),
        "by_inst_type": {f"{k[0]}|{k[1]}": v for k, v in by_inst_type.items()},
    }


def select_poc_files(
    pdf_dir: Path | str = None,
    n: int = 100,
    max_pages: int = 10,
) -> list[Path]:
    """选取 N 个适合 POC 的 PDF（短 + 覆盖多机构/多类型）。

    Args:
        pdf_dir: PDF 目录
        n: 选取数量
        max_pages: 最大页数（避免选大文件）

    Returns:
        PDF 路径列表
    """
    pdf_dir = Path(pdf_dir or settings.pdf_data_dir)
    files = sorted(pdf_dir.rglob("*.pdf"))

    # 按 (institution, report_type) 分组
    groups: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for f in files:
        meta = _extract_dir_meta(f)
        groups[(meta["institution"], meta["report_type"])].append(f)

    # 每个组合取样（按目录均匀采样）
    selected: list[Path] = []
    per_group = max(1, n // len(groups))

    # 用文件大小做粗筛（小文件 → 短 PDF 概率高），避免逐一 PyMuPDF 解析
    # 经验: 招银理财临时公告类 PDF 约 50KB/页
    max_size_bytes = max_pages * 80 * 1024  # 80KB/页 阈值

    for (inst, rtype), group_files in sorted(groups.items()):
        # 优先选短 PDF（按文件大小粗筛）
        group_files_sorted = sorted(group_files, key=lambda f: f.stat().st_size)
        sampled = []
        for f in group_files_sorted:
            if len(sampled) >= per_group:
                break
            if f.stat().st_size <= max_size_bytes:
                sampled.append(f)
        selected.extend(sampled)

    logger.info(f"POC 选取: {len(selected)} 个 PDF (覆盖 {len(groups)} 个组合)")
    return selected[:n]


def main():
    """CLI 入口"""
    stats = scan_pdfs()
    print(f"\n=== PDF 统计 ===")
    print(f"总数: {stats['total']}")
    print(f"\n按机构 (top 10):")
    for k, v in sorted(stats["by_institution"].items(), key=lambda x: -x[1])[:10]:
        print(f"  {k}: {v}")
    print(f"\n按报告类型:")
    for k, v in sorted(stats["by_report_type"].items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\n按一级分类:")
    for k, v in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    # POC 选取
    selected = select_poc_files(n=100, max_pages=10)

    # 落 json
    output = Path("data/clean/poc_files.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            [{"path": str(p.relative_to(settings.pdf_data_dir))} for p in selected],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nPOC 列表写入: {output} ({len(selected)} 文件)")


if __name__ == "__main__":
    main()