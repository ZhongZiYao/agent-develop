"""ETL Embed 层 - BGE FlagEmbedding GPU 实现。

输入：data/clean/chunks.parquet
输出：data/clean/embeddings.parquet  (chunk_id + 1024 维向量)

特性：
    - 直接调用 BAAI/FlagEmbedding（官方实现），GPU 推理 bge-m3
    - 绕开 Ollama HTTP / llama.cpp 后端，走原生 PyTorch CUDA
    - 懒加载单例模型（首次调用才加载，避免 import 时间）
    - device 自动探测：CUDA → MPS → CPU
    - **append-mode checkpoint** 复用 embed_ollama._scan_existing_ids/_finalize
    - 批次推理（GPU 友好）：use_fp16=True RTX 50 系起

性能（RTX 5070 8GB，bge-m3 fp16）：
    - Ollama CPU (12.8 chunks/s) vs BGE GPU (~300-500 chunks/s)
    - 100k chunks 嵌入预计 3-5 分钟
"""
from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm

from src.config import settings
from src.etl.embed_ollama import _finalize, _scan_existing_ids, _write_chunk


# ===== 路径 =====
DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
CLEAN_DIR = DATA_ROOT / "clean"

# ===== 模型配置 =====
MODEL_NAME = os.getenv("BGE_MODEL_NAME", "BAAI/bge-m3")
EMBEDDING_DIM = 1024  # bge-m3
MAX_EMBED_CHARS = int(os.getenv("MAX_EMBED_CHARS", "256"))
USE_FP16 = os.getenv("BGE_USE_FP16", "true").lower() == "true"

# ===== Checkpoint =====
CHECKPOINT_EVERY = int(os.getenv("CHECKPOINT_EVERY", "4000"))

# 全局模型句柄（线程安全懒加载）
_model = None
_model_lock = threading.Lock()
_model_device = None


def _detect_device() -> str:
    """自动选择 device：CUDA > MPS > CPU。"""
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _get_model():
    """懒加载 BGE FlagModel（单例）。"""
    global _model, _model_device
    if _model is None:
        with _model_lock:
            if _model is None:
                from FlagEmbedding import BGEM3FlagModel

                _model_device = _detect_device()
                logger.info(f"🚀 加载 BGE FlagModel: {MODEL_NAME} on {_model_device} (fp16={USE_FP16})")
                t0 = time.time()
                _model = BGEM3FlagModel(
                    MODEL_NAME,
                    use_fp16=USE_FP16,
                    device=_model_device,
                    normalize_embeddings=True,  # 与 Ollama cosine 一致
                )
                logger.info(f"✅ BGE 加载耗时 {time.time()-t0:.1f}s")
    return _model


def truncate_for_embed(text: str, max_chars: int = MAX_EMBED_CHARS) -> str:
    """截断超长文本以加速推理（与 embed_ollama 一致）。"""
    if not isinstance(text, str):
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def load_chunks_parquet(path: Path = CLEAN_DIR / "chunks.parquet") -> pd.DataFrame:
    """读取切分后的 chunks。"""
    if not path.exists():
        raise FileNotFoundError(f"chunks.parquet 不存在: {path}（先跑 transform.py）")
    df = pd.read_parquet(path)
    logger.info(f"加载 {len(df)} chunks from {path}")
    return df


def embed_batch_bge(texts: list[str]) -> list[list[float]]:
    """GPU 批量推理（核心入口）：一次 encode 一批文本。

    Returns:
        list[list[float]]  每个元素是 1024 维向量
    """
    model = _get_model()
    truncated = [truncate_for_embed(t) for t in texts]
    try:
        # bge-m3 返回 dict: {'dense_vecs': ndarray (B, 1024), 'lexical_weights': ...}
        out = model.encode(
            truncated,
            batch_size=len(truncated),
            max_length=MAX_EMBED_CHARS,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        dense = out["dense_vecs"]
        return dense.tolist()
    except Exception as exc:
        logger.error(f"BGE encode 失败 (batch={len(texts)}): {exc}")
        return [[0.0] * EMBEDDING_DIM for _ in texts]


def embed_chunks(
    chunks_df: pd.DataFrame,
    model_name: str = MODEL_NAME,
    batch_size: int = 32,  # GPU batch：RTX 5070 8GB 上 bge-m3 fp16 安全起步值
    checkpoint_dir: Path | None = None,
    final_path: Path | None = None,
    resume: bool = True,
) -> pd.DataFrame:
    """BGE GPU 主入口：批量推理 + append-mode checkpoint。

    与 embed_ollama.embed_chunks 接口对齐（同名同位置参数）。

    Args:
        chunks_df: 含 chunk_id + chunk_text 列
        model_name: BGE 模型名（默认 bge-m3）
        batch_size: GPU 一次 encode 的 batch（根据显存调整；8GB RTX 50 系起步 32）
        checkpoint_dir: append chunk parquet 目录
        final_path: 最终合并 embeddings.parquet
        resume: True 时跳过已 embed 的 chunk_id

    Returns:
        最终合并的 DataFrame
    """
    if checkpoint_dir is None:
        checkpoint_dir = CLEAN_DIR / "embeddings_chunks"
    if final_path is None:
        final_path = CLEAN_DIR / "embeddings.parquet"

    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # ===== Resume =====
    done_ids: set[str] = set()
    if resume:
        done_ids = _scan_existing_ids(checkpoint_dir, fallback_parquet=final_path)
        logger.info(f"Checkpoint: {len(done_ids)} chunks 已完成")

    existing_chunks = sorted(checkpoint_dir.glob("chunk_*.parquet"))
    next_chunk_idx = len(existing_chunks)

    # ===== 过滤 todo =====
    texts = chunks_df["chunk_text"].tolist()
    chunk_ids = chunks_df["chunk_id"].astype(str).tolist()
    todo_pairs = [(cid, t) for cid, t in zip(chunk_ids, texts) if cid not in done_ids]

    if not todo_pairs:
        logger.info("所有 chunks 已 embed 完成")
        _finalize(checkpoint_dir, final_path, model_name)
        return pd.read_parquet(final_path)

    todo_ids = [p[0] for p in todo_pairs]
    todo_texts = [p[1] for p in todo_pairs]
    logger.info(
        f"开始 BGE GPU 推理 {len(todo_texts)} chunks "
        f"(model={model_name}, batch_size={batch_size}, device={_model_device or 'pending'})..."
    )

    # ===== GPU 推理流（不要 ThreadPoolExecutor——GPU 是单设备，并发反而慢）=====
    pending_ids: list[str] = []
    pending_emb: list[list[float]] = []
    flush_lock = threading.Lock()

    def _flush():
        nonlocal next_chunk_idx, pending_ids, pending_emb
        with flush_lock:
            if not pending_ids:
                return
            idx = next_chunk_idx
            next_chunk_idx += 1
            _write_chunk(checkpoint_dir, pending_ids, pending_emb, model_name, idx)
            logger.info(f"💾 chunk_{idx:05d}: {len(pending_ids)} chunks")
            pending_ids, pending_emb = [], []

    completed = 0
    n_batches = (len(todo_texts) + batch_size - 1) // batch_size
    t0 = time.time()

    with tqdm(total=len(todo_texts), desc="BGE-GPU") as pbar:
        for batch_start in range(0, len(todo_texts), batch_size):
            batch_ids = todo_ids[batch_start : batch_start + batch_size]
            batch_texts = todo_texts[batch_start : batch_start + batch_size]
            embs = embed_batch_bge(batch_texts)

            with flush_lock:
                pending_ids.extend(batch_ids)
                pending_emb.extend(embs)
                should_flush = (len(pending_ids) >= CHECKPOINT_EVERY)

            completed += len(batch_ids)
            pbar.update(len(batch_ids))

            if should_flush:
                _flush()

    _flush()  # 最后一批

    elapsed = time.time() - t0
    rate = len(todo_texts) / elapsed if elapsed > 0 else 0
    logger.info(f"✅ BGE 完成: {len(todo_texts)} chunks in {elapsed:.1f}s ({rate:.1f} chunks/s)")

    # ===== 合并 =====
    n = _finalize(checkpoint_dir, final_path, model_name)
    return pd.read_parquet(final_path)


def save_embeddings(
    df: pd.DataFrame,
    out_path: Path = CLEAN_DIR / "embeddings.parquet",
) -> Path:
    """保存 embeddings.parquet（与 embed_ollama 一致）。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp_path, engine="pyarrow", index=False)
    tmp_path.rename(out_path)
    size_mb = out_path.stat().st_size / 1e6
    logger.info(f"写入 {out_path} ({size_mb:.1f} MB, {len(df)} rows)")
    return out_path


def run() -> Path:
    """CLI 入口。"""
    chunks_df = load_chunks_parquet()
    embeddings_df = embed_chunks(chunks_df)
    return save_embeddings(embeddings_df)


if __name__ == "__main__":
    run()