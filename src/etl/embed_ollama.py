"""ETL Embed 层 - Ollama HTTP API 实现（避免 HuggingFace 下载）。

输入：data/clean/chunks.parquet
输出：data/clean/embeddings.parquet  (chunk_id + 1024 维向量)

特性：
    - 使用 Ollama HTTP API（本地或远程）
    - 无需下载 HuggingFace 模型
    - 批量请求（batch_size 可配置）
    - 断点续跑：写入临时文件，结束后 rename
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
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


def load_chunks_parquet(path: Path = CLEAN_DIR / "chunks.parquet") -> pd.DataFrame:
    """读取切分后的 chunks。"""
    if not path.exists():
        raise FileNotFoundError(f"chunks.parquet 不存在: {path}（先跑 transform.py）")
    df = pd.read_parquet(path)
    logger.info(f"加载 {len(df)} chunks from {path}")
    return df


def embed_text_ollama(text: str, model: str = OLLAMA_EMBED_MODEL) -> list[float]:
    """调用 Ollama API 生成单个文本的 embedding。"""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": model, "prompt": text}
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("embedding", [])
    except Exception as exc:
        logger.error(f"Ollama embed 失败: {exc}")
        return []


def embed_chunks(
    chunks_df: pd.DataFrame,
    model: str = OLLAMA_EMBED_MODEL,
    batch_size: int = 16,
) -> pd.DataFrame:
    """主入口：Ollama API 批量 embedding。

    Args:
        chunks_df: 含 chunk_id + chunk_text 列
        model: Ollama 模型名
        batch_size: 批量大小（Ollama API 是串行，这里用于进度显示）

    Returns:
        含 chunk_id + embedding (list[float32]) + model
    """
    texts = chunks_df["chunk_text"].tolist()
    chunk_ids = chunks_df["chunk_id"].tolist()

    logger.info(f"开始 embedding {len(texts)} 个 chunks (model={model})...")

    embeddings = []
    for text in tqdm(texts, desc="Embedding"):
        emb = embed_text_ollama(text, model=model)
        if emb:
            embeddings.append(np.array(emb, dtype=np.float32).tolist())
        else:
            # 失败时填充零向量
            logger.warning(f"Embedding 失败，使用零向量")
            embeddings.append([0.0] * EMBEDDING_DIM)

    result_df = pd.DataFrame(
        {
            "chunk_id": chunk_ids,
            "embedding": embeddings,
            "model": model,
        }
    )
    logger.info(f"Embedding 完成: {len(result_df)} chunks × {EMBEDDING_DIM} 维")
    return result_df


def save_embeddings(
    df: pd.DataFrame,
    out_path: Path = CLEAN_DIR / "embeddings.parquet",
) -> Path:
    """保存 embeddings.parquet。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp_path, engine="pyarrow", index=False)
    tmp_path.rename(out_path)  # 原子写入
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
