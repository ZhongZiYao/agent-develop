"""Modular RAG 模块系统

每个 RAG 组件（query 重写、检索、重排、生成）被抽象为独立的 RAGModule 子类，
支持：
1. 标准化接口（__call__ 输入 state 输出 state 更新）
2. 配置化构造（from_config 类方法）
3. 灵活组合（图构建器按配置组装）

参考：Modular RAG: Transforming RAG Systems into LEGO-like Reconfigurable Frameworks
"""

from .base import ModuleConfig, ModuleRegistry, RAGModule
from .builder import RAGGraphBuilder, build_graph_from_config
from .generator import GeneratorModule
from .query_rewriter import QueryRewriterModule
from .reranker import RerankerModule
from .retriever import HybridRetrieverModule

__all__ = [
    "RAGModule",
    "ModuleRegistry",
    "ModuleConfig",
    "QueryRewriterModule",
    "HybridRetrieverModule",
    "RerankerModule",
    "GeneratorModule",
    "RAGGraphBuilder",
    "build_graph_from_config",
]
