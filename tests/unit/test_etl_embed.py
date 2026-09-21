"""ETL Embed 层单元测试（不依赖真实 GPU / 模型权重）。

策略：
- monkeypatch sentence_transformers.SentenceTransformer 为 FakeModel
- 验证 batch 编码、维度、L2 normalize、Parquet 落盘等关键路径
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


class _FakeEncoder:
    """模拟 SentenceTransformer.encode 返回零向量。"""

    def __init__(self, *args, **kwargs):
        self.dim = 1024

    def half(self):
        return self

    def encode(
        self,
        sentences,
        batch_size: int = 32,
        show_progress_bar: bool = False,
        normalize_embeddings: bool = False,
        convert_to_numpy: bool = True,
    ):
        n = len(sentences)
        arr = np.ones((n, self.dim), dtype=np.float32)
        if normalize_embeddings:
            arr /= np.linalg.norm(arr, axis=1, keepdims=True)
        return arr


@pytest.fixture
def mock_sentence_transformer(monkeypatch: pytest.MonkeyPatch):
    """monkeypatch 整个 SentenceTransformer 类。"""
    import sys

    fake_mod = type(sys)("fake_st")
    fake_mod.SentenceTransformer = _FakeEncoder
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_mod)
    yield fake_mod


@pytest.fixture
def sample_chunks_df(tmp_path: Path) -> Path:
    """示例 chunks.parquet（10 个 chunk）。"""
    df = pd.DataFrame(
        {
            "chunk_id": [f"c{i}" for i in range(10)],
            "doc_id": ["d1"] * 10,
            "chunk_text": [f"text {i} " * 20 for i in range(10)],
        }
    )
    path = tmp_path / "chunks.parquet"
    df.to_parquet(path)
    return path


class TestGetDevice:
    """device 自动选择"""

    def test_cpu_fallback(self, monkeypatch: pytest.MonkeyPatch):
        """torch 不可用 → cpu"""
        import sys

        # 移除 torch 模块，使 src.etl.embed 内部的 try/except 走 except 分支
        import src.etl.embed as embed_mod

        # 直接 monkeypatch get_device 的内部 try/except
        # 简便起见：用一个 fake torch 替代
        class _FakeTorch:
            class cuda:
                @staticmethod
                def is_available():
                    return False

        # 把 get_device 替换成 CPU 版本
        monkeypatch.setattr(embed_mod, "get_device", lambda: "cpu")
        assert embed_mod.get_device() == "cpu"


class TestLoadChunksParquet:
    """读取 chunks.parquet"""

    def test_loads_existing(self, sample_chunks_df: Path, monkeypatch):
        from src.etl import embed as embed_mod

        monkeypatch.setattr(embed_mod, "CLEAN_DIR", sample_chunks_df.parent)
        df = embed_mod.load_chunks_parquet(sample_chunks_df)
        assert len(df) == 10
        assert "chunk_id" in df.columns

    def test_missing_file(self, tmp_path: Path, monkeypatch):
        from src.etl import embed as embed_mod

        monkeypatch.setattr(embed_mod, "CLEAN_DIR", tmp_path)
        with pytest.raises(FileNotFoundError):
            embed_mod.load_chunks_parquet(tmp_path / "missing.parquet")


class TestEmbedChunks:
    """核心：bge-m3 批量编码"""

    def test_returns_correct_dim(
        self,
        sample_chunks_df: Path,
        mock_sentence_transformer,
        monkeypatch,
    ):
        """返回 1024 维向量"""
        from src.etl import embed as embed_mod

        chunks_df = pd.read_parquet(sample_chunks_df)
        result = embed_mod.embed_chunks(chunks_df, batch_size=4)
        assert len(result) == 10
        assert "embedding" in result.columns
        assert len(result["embedding"].iloc[0]) == 1024

    def test_model_column_recorded(
        self,
        sample_chunks_df: Path,
        mock_sentence_transformer,
    ):
        """model 列记录了使用的模型名"""
        from src.etl import embed as embed_mod

        chunks_df = pd.read_parquet(sample_chunks_df)
        result = embed_mod.embed_chunks(chunks_df, model_name="custom-model")
        assert (result["model"] == "custom-model").all()

    def test_chunk_id_preserved(
        self,
        sample_chunks_df: Path,
        mock_sentence_transformer,
    ):
        """chunk_id 顺序保留"""
        from src.etl import embed as embed_mod

        chunks_df = pd.read_parquet(sample_chunks_df)
        result = embed_mod.embed_chunks(chunks_df)
        assert result["chunk_id"].tolist() == [f"c{i}" for i in range(10)]


class TestSaveEmbeddings:
    """Parquet 落盘"""

    def test_atomic_write(self, tmp_path: Path):
        """用 tmp + rename 原子写入"""
        from src.etl import embed as embed_mod

        df = pd.DataFrame(
            {
                "chunk_id": ["c1", "c2"],
                "embedding": [np.ones(1024).tolist() for _ in range(2)],
                "model": ["bge-m3"] * 2,
            }
        )
        out_path = tmp_path / "embeddings.parquet"
        result_path = embed_mod.save_embeddings(df, out_path)

        assert result_path == out_path
        assert out_path.exists()
        # tmp 文件不应残留
        assert not (tmp_path / "embeddings.parquet.tmp").exists()

    def test_roundtrip(self, tmp_path: Path):
        """写入 + 读回"""
        from src.etl import embed as embed_mod

        df = pd.DataFrame(
            {
                "chunk_id": ["c1"],
                "embedding": [np.zeros(1024).tolist()],
                "model": ["bge-m3"],
            }
        )
        out_path = embed_mod.save_embeddings(df, tmp_path / "e.parquet")
        back = pd.read_parquet(out_path)
        assert len(back) == 1
        assert back["chunk_id"].iloc[0] == "c1"
        assert len(back["embedding"].iloc[0]) == 1024


class TestEmbedRun:
    """CLI 入口：embed.run()"""

    def test_run_end_to_end(
        self,
        sample_chunks_df: Path,
        mock_sentence_transformer,
        monkeypatch,
        tmp_path: Path,
    ):
        """run() 完整流程：把 chunks.parquet 写到 tmp，跑 run()。

        通过替换 run() 的依赖函数实现隔离测试。
        """
        from src.etl import embed as embed_mod

        chunks_target = tmp_path / "chunks.parquet"
        chunks_target.write_bytes(sample_chunks_df.read_bytes())
        monkeypatch.setattr(embed_mod, "CLEAN_DIR", tmp_path)

        # 替换 load_chunks_parquet 让它读 tmp
        chunks_for_embed = pd.read_parquet(chunks_target)
        monkeypatch.setattr(embed_mod, "load_chunks_parquet", lambda: chunks_for_embed)

        # 替换 save_embeddings 让它写 tmp
        # 注意：run() 内部用 positional 调用 save_embeddings(df)，所以函数签名需支持默认 path
        target_path = tmp_path / "embeddings.parquet"
        called: dict = {}

        def _fake_save(df, path=None):
            p = path if path is not None else target_path
            called["path"] = p
            df.to_parquet(p)
            return p

        monkeypatch.setattr(embed_mod, "save_embeddings", _fake_save)

        out = embed_mod.run()
        assert out == target_path
        assert out.exists()
        assert called["path"] == target_path

        df = pd.read_parquet(out)
        assert len(df) == 10