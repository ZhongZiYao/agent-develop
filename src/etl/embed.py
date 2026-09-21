"""ETL Embed 层 - GPU 加速 bge-m3 批量 embedding。

输入：data/clean/chunks.parquet
输出：data/clean/embeddings.parquet  (chunk_id + 1024 维向量)

特性：
    - 自动检测 GPU（CUDA）vs CPU
    - batch_size=32（GPU）/ batch_size=8（CPU）
    - FP16 推理（GPU 显存友好）
    - 断点续跑：写入临时文件，结束后 rename
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm

from src.config import settings


# ===== 路径 =====
DATA_ROOT = Path(settings.data_dir) if hasattr(settings, "data_dir") else Path("data")
CLEAN_DIR = DATA_ROOT / "clean"

EMBEDDING_DIM = 1024  # bge-m3
MODEL_NAME = "BAAI/bge-m3"


def get_device() -> str:
    """自动选择设备：CUDA → MPS → CPU。"""
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def load_chunks_parquet(path: Path = CLEAN_DIR / "chunks.parquet") -> pd.DataFrame:
    """读取切分后的 chunks。"""
    if not path.exists():
        raise FileNotFoundError(f"chunks.parquet 不存在: {path}（先跑 transform.py）")
    df = pd.read_parquet(path)
    logger.info(f"加载 {len(df)} chunks from {path}")
    return df


def embed_chunks(
    chunks_df: pd.DataFrame,
    model_name: str = MODEL_NAME,
    batch_size: int | None = None,
    use_fp16: bool = True,
) -> pd.DataFrame:
    """主入口：bge-m3 GPU 批量 embedding。

    Args:
        chunks_df: 含 chunk_id + chunk_text 列
        model_name: SentenceTransformer 模型名
        batch_size: None 时自动选择（GPU=32 / CPU=8）
        use_fp16: 是否 FP16 推理（GPU 推荐 True）

    Returns:
        含 chunk_id + embedding (list[float32]) + model + embed_ts
    """
    # 延迟导入 sentence-transformers（避免主环境依赖）
    from sentence_transformers import SentenceTransformer

    device = get_device()
    if batch_size is None:
        batch_size = 32 if device == "cuda" else 8

    logger.info(
        f"加载模型 {model_name} device={device} batch_size={batch_size} fp16={use_fp16}"
    )
    model = SentenceTransformer(model_name, device=device)

    if device == "cuda" and use_fp16:
        model = model.half()  # FP16

    texts = chunks_df["chunk_text"].tolist()
    chunk_ids = chunks_df["chunk_id"].tolist()

    # 批量编码
    logger.info(f"开始 embedding {len(texts)} 个 chunks...")
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,  # L2 normalize，cosine 检索更稳
        convert_to_numpy=True,
    )

    # 转为 list[float32]（Parquet 友好）
    embeddings_list = [emb.astype(np.float32).tolist() for emb in embeddings]

    result_df = pd.DataFrame(
        {
            "chunk_id": chunk_ids,
            "embedding": embeddings_list,
            "model": model_name,
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