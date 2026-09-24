"""分层采样 chunks.parquet：每个 institution × report_type 抽 1/10。

输出：data/clean/chunks_sampled.parquet（用于本次 ETL demo）

Usage:
    python -m scripts.sample_chunks --ratio 0.1
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from src.config import settings


CLEAN_DIR = Path(settings.data_dir) / "clean"


def sample_chunks(
    in_path: Path = CLEAN_DIR / "chunks.parquet",
    out_path: Path = CLEAN_DIR / "chunks_sampled.parquet",
    ratio: float = 0.1,
    seed: int = 42,
) -> Path:
    """分层采样：按 institution 分组，每组随机抽 ratio 比例。"""
    df = pd.read_parquet(in_path)
    logger.info(f"原始 chunks: {len(df)}, docs: {df.doc_id.nunique()}, institutions: {df.institution.nunique()}")

    rng = np.random.RandomState(seed)
    keep_idx = []
    for inst, sub in df.groupby("institution", sort=False):
        n = max(1, int(len(sub) * ratio))
        idx = sub.index.to_numpy()
        chosen = rng.choice(idx, size=n, replace=False)
        keep_idx.extend(chosen.tolist())
        logger.info(f"  {inst}: {len(sub)} → {n} ({n/len(sub)*100:.1f}%)")

    sampled = df.loc[keep_idx].sort_index().reset_index(drop=True)
    logger.info(f"采样后: {len(sampled)} chunks, docs: {sampled.doc_id.nunique()}, institutions: {sampled.institution.nunique()}")

    sampled.to_parquet(out_path, engine="pyarrow", index=False)
    logger.info(f"写入 {out_path} ({out_path.stat().st_size/1e6:.1f} MB)")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratio", type=float, default=0.1)
    parser.add_argument("--in", dest="in_path", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    in_path = Path(args.in_path) if args.in_path else CLEAN_DIR / "chunks.parquet"
    out_path = Path(args.out) if args.out else CLEAN_DIR / "chunks_sampled.parquet"
    sample_chunks(in_path=in_path, out_path=out_path, ratio=args.ratio)