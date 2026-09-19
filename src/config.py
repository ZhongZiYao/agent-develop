"""全局配置 — 从 .env / 环境变量加载"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# 项目根目录（E:/Program Files/vibe_coding/RAG_system）
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """所有配置项集中管理，类型安全"""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== LLM =====
    # ollama: 本地 ChatOllama；minimax/openai: OpenAI 兼容 API
    llm_provider: str = Field(default="ollama", description="LLM provider: ollama/minimax/openai")
    llm_api_key: str = Field(default="", description="远程 LLM API key；Ollama 不需要")
    llm_base_url: str = Field(default="http://localhost:11434", description="LLM API base URL")
    llm_model: str = Field(default="qwen3:8b", description="模型名")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2048, ge=1, le=8192)
    llm_timeout: int = Field(default=180, description="API 超时秒数")
    llm_context_window: int = Field(default=8192, ge=1024, description="Ollama 上下文窗口")
    llm_reasoning: bool = Field(default=True, description="是否启用本地模型 reasoning")
    llm_keep_alive: str = Field(default="15m", description="Ollama 模型驻留时间")

    # ===== Embedding（Ollama 本地） =====
    embedding_provider: str = Field(default="ollama", description="embedding provider: ollama/openai/bge")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API 地址")
    ollama_embed_model: str = Field(default="bge-m3", description="Ollama embedding 模型名")
    ollama_embed_dim: int = Field(default=1024, description="bge-m3 维度")

    # ===== Vector Store =====
    chroma_persist_dir: str = Field(default=str(PROJECT_ROOT / "data" / "chroma"))
    chroma_collection_name: str = Field(default="gameguide")

    # ===== 数据 =====
    raw_data_dir: str = Field(default=str(PROJECT_ROOT / "data" / "raw"))
    eval_data_dir: str = Field(default=str(PROJECT_ROOT / "data" / "eval"))
    processed_data_dir: str = Field(default=str(PROJECT_ROOT / "data" / "processed"))

    # ===== Splitter =====
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)

    # ===== Retriever =====
    top_k: int = Field(default=10, ge=1, le=100, description="召回数量")
    top_n: int = Field(default=5, ge=1, le=20, description="最终送 LLM 的数量")

    # ===== Reranker（Phase 2） =====
    rerank_enabled: bool = Field(default=False)
    rerank_model: str = Field(default="BAAI/bge-reranker-large")

    # ===== Query 处理（Phase 2） =====
    query_rewrite_enabled: bool = Field(default=False)
    hyde_enabled: bool = Field(default=False)

    # ===== 服务 =====
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    web_port: int = Field(default=3000)

    # ===== LangSmith（可选） =====
    langsmith_tracing: bool = Field(default=False)
    langsmith_api_key: str = Field(default="")
    langsmith_project: str = Field(default="gameguide-ai")

    # ===== 调试 =====
    debug: bool = Field(default=False)

    # ===== LangGraph Feature Flag =====
    use_langgraph: bool = Field(default=False, description="是否启用 LangGraph 端点")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例获取配置（lru_cache 保证全局唯一）"""
    return Settings()


# 方便外部直接 import
settings = get_settings()