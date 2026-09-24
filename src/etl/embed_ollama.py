"""ETL Embed 层 - Ollama HTTP API 实现（避免 HuggingFace 下载）。

输入：data/clean/chunks.parquet
输出：data/clean/embeddings.parquet  (chunk_id + 1024 维向量)

特性：
    - 使用 Ollama HTTP API（本地或远程）
    - 无需下载 HuggingFace 模型
    - **并发请求**（ThreadPoolExecutor，max_workers 默认 8）— Ollama 串行推理
    - **文本截断**（MAX_EMBED_CHARS=512）— 加速 bge-m3
    - **Checkpoint 续跑**：
        - **Append 模式**：每 N chunks 把"已完成 ID + 向量"append 到小 parquet（<5000行/批）
        - flush 时**绝不读旧 parquet**（避免 N² 复杂度）
        - 启动时仅读取旧 parquet 的 chunk_id 集合（O(N) 但只在启动时一次）
        - 最终落盘时把所有 append 块合并为最终 embeddings.parquet
"""
from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from loguru import logger
from tqdm import tqdm

from src.config import settings


# ===== 路径 =====
DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
CLEAN_DIR = DATA_ROOT / "clean"

# ===== Ollama 配置 =====
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")
EMBEDDING_DIM = 1024  # bge-m3

# ===== Embedding 文本限制 =====
# bge-m3 官方建议 ≤512 token；缩短到 256 字符约 170 token，Ollama 推理快 ~2x
# （实际 benchmark：256 chars + 100 workers = 25 reqs/s vs 512 chars + 8 workers = 3 reqs/s）
MAX_EMBED_CHARS = int(os.getenv("MAX_EMBED_CHARS", "256"))

# ===== Checkpoint 配置 =====
CHECKPOINT_EVERY = int(os.getenv("CHECKPOINT_EVERY", "4000"))


def truncate_for_embed(text: str, max_chars: int = MAX_EMBED_CHARS) -> str:
    """截断超长文本以加速 bge-m3 推理。"""
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


def embed_text_ollama(text: str, model: str = OLLAMA_EMBED_MODEL, timeout: int = 60) -> list[float]:
    """调用 Ollama API 生成单个文本的 embedding。"""
    text = truncate_for_embed(text)
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": model, "prompt": text}
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("embedding", [])
    except Exception as exc:
        logger.error(f"Ollama embed 失败: {exc}")
        return []


def _scan_existing_ids(checkpoint_dir: Path, fallback_parquet: Path | None = None) -> set[str]:
    """扫描 checkpoints/ 目录下的所有 chunk，统计已完成的 chunk_id。

    兼容旧版：如果 checkpoint_dir 为空，回退到读 fallback_parquet
    （旧 ETL 写在单一 parquet 文件的情况）。

    Args:
        checkpoint_dir: chunk parquet 目录
        fallback_parquet: 旧版单文件路径（兜底）
    """
    done_ids: set[str] = set()
    if checkpoint_dir.exists():
        for ckpt in checkpoint_dir.glob("chunk_*.parquet"):
            try:
                df = pd.read_parquet(ckpt, columns=["chunk_id"])
                done_ids.update(df["chunk_id"].astype(str).tolist())
            except Exception:
                pass
    # 兜底：旧版单文件
    if not done_ids and fallback_parquet and fallback_parquet.exists():
        try:
            df = pd.read_parquet(fallback_parquet, columns=["chunk_id"])
            done_ids.update(df["chunk_id"].astype(str).tolist())
        except Exception:
            pass
    return done_ids


def _write_chunk(checkpoint_dir: Path, chunk_ids: list[str], embeddings: list, model: str, idx: int) -> Path:
    """写一个独立 chunk parquet（小，O(N) 时间）。"""
    out_path = checkpoint_dir / f"chunk_{idx:05d}.parquet"
    df = pd.DataFrame(
        {
            "chunk_id": chunk_ids,
            "embedding": embeddings,
            "model": [model] * len(chunk_ids),
        }
    )
    tmp_path = out_path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp_path, engine="pyarrow", index=False)
    tmp_path.rename(out_path)
    return out_path


def _finalize(checkpoint_dir: Path, final_path: Path, model: str) -> int:
    """把 checkpoints/ 下的所有 chunk parquet 合并成最终文件。

    Args:
        checkpoint_dir: chunks 目录
        final_path: 最终 embeddings.parquet 路径
        model: 模型名（写到 parquet）
    Returns:
        总 chunks 数
    """
    parts = sorted(checkpoint_dir.glob("chunk_*.parquet"))
    if not parts:
        logger.warning(f"没有 checkpoint chunks in {checkpoint_dir}")
        if final_path.exists():
            df = pd.read_parquet(final_path)
            return len(df)
        return 0

    logger.info(f"合并 {len(parts)} 个 chunk parquet → {final_path}")
    dfs = []
    for p in parts:
        try:
            dfs.append(pd.read_parquet(p))
        except Exception as exc:
            logger.warning(f"读 {p} 失败: {exc}")

    if not dfs:
        return 0

    merged = pd.concat(dfs, ignore_index=True)
    merged = merged.drop_duplicates(subset=["chunk_id"], keep="last")

    tmp_path = final_path.with_suffix(".parquet.tmp")
    # 清理残留 tmp（防上次失败遗留）
    if tmp_path.exists():
        try:
            tmp_path.unlink()
        except Exception:
            pass
    merged.to_parquet(tmp_path, engine="pyarrow", index=False)
    # Windows rename 容错
    for attempt in range(3):
        try:
            tmp_path.rename(final_path)
            break
        except FileExistsError:
            try:
                final_path.unlink()
            except Exception:
                pass
            if attempt == 2:
                raise
        except Exception:
            raise
    logger.info(f"✅ Final embeddings: {len(merged)} chunks → {final_path} ({final_path.stat().st_size/1e6:.1f} MB)")
    return len(merged)


def embed_chunks(
    chunks_df: pd.DataFrame,
    model: str = OLLAMA_EMBED_MODEL,
    batch_size: int = 32,
    max_workers: int = 8,
    checkpoint_dir: Path | None = None,
    final_path: Path | None = None,
    resume: bool = True,
) -> pd.DataFrame:
    """主入口：Ollama API 并发 embedding + append 模式 checkpoint。

    Args:
        chunks_df: 含 chunk_id + chunk_text 列
        model: Ollama 模型名
        max_workers: 并发线程数
        checkpoint_dir: append chunk parquet 目录（默认 CLEAN_DIR/embeddings_chunks）
        final_path: 最终合并文件（默认 CLEAN_DIR/embeddings.parquet）
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
        logger.info(f"Checkpoint: {len(done_ids)} chunks 已完成 (扫描 {checkpoint_dir} + fallback {final_path})")

    # 已存在的 chunk parquet 数量（用于下一个 chunk 编号）
    existing_chunks = sorted(checkpoint_dir.glob("chunk_*.parquet"))
    next_chunk_idx = len(existing_chunks)

    # ===== 过滤 todo =====
    texts = chunks_df["chunk_text"].tolist()
    chunk_ids = chunks_df["chunk_id"].astype(str).tolist()
    todo_pairs = [(cid, t) for cid, t in zip(chunk_ids, texts) if cid not in done_ids]

    if not todo_pairs:
        logger.info("所有 chunks 已 embed 完成")
        return _finalize(checkpoint_dir, final_path, model) and pd.read_parquet(final_path) or pd.DataFrame()

    todo_ids = [p[0] for p in todo_pairs]
    todo_texts = [p[1] for p in todo_pairs]
    logger.info(f"开始 embedding {len(todo_texts)} chunks (model={model}, workers={max_workers}, max_chars={MAX_EMBED_CHARS})...")
    logger.info(f"Append mode: 每 {CHECKPOINT_EVERY} chunks 写一个独立 parquet → {checkpoint_dir}")

    # ===== 预分配 + 流式 =====
    embeddings: list[list[float] | None] = [None] * len(todo_texts)
    completed_count = 0
    pending_ids: list[str] = []
    pending_emb: list[list[float]] = []

    _flush_lock = threading.Lock()
    _shutdown = threading.Event()

    def _flush_now():
        """把 pending 写到一个新 chunk parquet（线程安全）。"""
        nonlocal next_chunk_idx, pending_ids, pending_emb
        with _flush_lock:
            if not pending_ids:
                return
            idx = next_chunk_idx
            next_chunk_idx += 1
            n = len(pending_ids)
            _write_chunk(checkpoint_dir, pending_ids, pending_emb, model, idx)
            logger.info(f"💾 Append chunk_{idx:05d}: {n} chunks")
            pending_ids = []
            pending_emb = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(embed_text_ollama, text, model): idx
            for idx, text in enumerate(todo_texts)
        }

        with tqdm(total=len(todo_texts), desc="Embedding") as pbar:
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    embeddings[idx] = result if result else [0.0] * EMBEDDING_DIM
                except Exception:
                    embeddings[idx] = [0.0] * EMBEDDING_DIM
                completed_count += 1
                pbar.update(1)

                # ===== Append pending =====
                with _flush_lock:
                    pending_ids.append(todo_ids[idx])
                    pending_emb.append(embeddings[idx])
                    should_flush = (completed_count % CHECKPOINT_EVERY == 0)

                if should_flush:
                    _flush_now()  # 同步 flush（用 lock 串行）

    # 兜底 None → 零向量
    for i in range(len(embeddings)):
        if embeddings[i] is None:
            embeddings[i] = [0.0] * EMBEDDING_DIM

    # 最后一次 flush
    _flush_now()

    # ===== 合并为 final =====
    n = _finalize(checkpoint_dir, final_path, model)
    return pd.read_parquet(final_path)


def save_embeddings(
    df: pd.DataFrame,
    out_path: Path = CLEAN_DIR / "embeddings.parquet",
) -> Path:
    """保存 embeddings.parquet。"""
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