"""Modular RAG Graph Builder

根据 YAML 配置动态构建 LangGraph StateGraph。
支持：
1. 配置驱动的模块实例化
2. 流程自动连接
3. 模块启用/禁用
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph
from loguru import logger

from ..graphs.state import RAGState
from .base import ModuleConfig, ModuleRegistry, RAGModule


class RAGGraphBuilder:
    """根据配置构建 RAG Graph

    用法：
        builder = RAGGraphBuilder.from_yaml("config/rag_modules.yaml")
        graph = await builder.build()
        result = await graph.ainvoke({"query": "..."})
    """

    def __init__(self, config: dict):
        """从配置 dict 初始化

        Args:
            config: 包含 modules、flow、metadata 的配置字典
        """
        self.config = config
        self.modules: dict[str, RAGModule] = {}
        self.flow: list[str] = config.get("flow", [])
        self.metadata = config.get("metadata", {})

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "RAGGraphBuilder":
        """从 YAML 文件加载配置"""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded config from {config_path}: {config.get('metadata', {}).get('name', 'unnamed')}")
        return cls(config)

    async def build(self, checkpoint_path: str | None = None) -> Any:
        """构建 LangGraph StateGraph

        Args:
            checkpoint_path: SQLite checkpoint 文件路径（可选）

        Returns:
            编译后的 StateGraph
        """
        # 1. 实例化模块
        self._instantiate_modules()

        # 2. 构建 Graph
        graph = StateGraph(RAGState)

        # 3. 添加节点
        for name, module in self.modules.items():
            logger.debug(f"Adding node: {name} ({module.__class__.__name__})")
            graph.add_node(name, self._make_node_func(module))

        # 4. 连接流程
        self._connect_flow(graph)

        # 5. 编译
        if checkpoint_path:
            checkpointer = AsyncSqliteSaver.from_conn_string(checkpoint_path)
            logger.info(f"Using checkpoint: {checkpoint_path}")
            compiled = graph.compile(checkpointer=checkpointer)
        else:
            compiled = graph.compile()

        logger.info(
            f"Built graph: {self.metadata.get('name', 'unnamed')} "
            f"with {len(self.modules)} modules"
        )
        return compiled

    def _instantiate_modules(self) -> None:
        """根据配置实例化所有启用的模块"""
        modules_config = self.config.get("modules", {})

        for name, module_config in modules_config.items():
            if not module_config.get("enabled", True):
                logger.debug(f"Module {name} is disabled, skipping")
                continue

            module_type = module_config["type"]
            module_cls = ModuleRegistry.get(module_type)

            if module_cls is None:
                raise ValueError(
                    f"Module type '{module_type}' not found in registry. "
                    f"Available: {ModuleRegistry.list_names()}"
                )

            # 实例化
            config_obj = ModuleConfig(
                name=name,
                type=module_type,
                enabled=True,
                params=module_config.get("params", {}),
            )
            module = module_cls.from_config(config_obj)
            self.modules[name] = module

            logger.debug(f"Instantiated module: {name} ({module_cls.__name__})")

    def _connect_flow(self, graph: StateGraph) -> None:
        """连接流程（顺序执行）"""
        if not self.flow:
            raise ValueError("Flow is empty, cannot connect nodes")

        # 设置入口点
        graph.set_entry_point(self.flow[0])

        # 连接节点
        for i in range(len(self.flow) - 1):
            src = self.flow[i]
            dst = self.flow[i + 1]

            # 跳过未启用的节点
            if src not in self.modules or dst not in self.modules:
                logger.warning(f"Skipping edge {src} → {dst} (module not enabled)")
                continue

            graph.add_edge(src, dst)
            logger.debug(f"Connected: {src} → {dst}")

        # 连接最后一个节点到 END
        last_node = self.flow[-1]
        if last_node in self.modules:
            graph.add_edge(last_node, END)
            logger.debug(f"Connected: {last_node} → END")

    def _make_node_func(self, module: RAGModule):
        """包装 RAGModule 为 LangGraph 节点函数

        LangGraph 节点函数签名：async def node(state: RAGState) -> dict
        RAGModule.__call__ 签名：async def __call__(state: dict) -> dict
        """

        async def node_func(state: RAGState) -> dict:
            """节点执行函数"""
            # 调用模块
            updates = await module(state)
            return updates

        return node_func

    def to_yaml(self, output_path: str | Path) -> None:
        """将当前配置导出为 YAML"""
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.config, f, allow_unicode=True)
        logger.info(f"Exported config to {output_path}")


async def build_graph_from_config(
    config_path: str | Path,
    checkpoint_path: str | None = None,
) -> Any:
    """便捷函数：从配置文件构建 Graph

    用法：
        graph = await build_graph_from_config("config/rag_modules.yaml")
        result = await graph.ainvoke({"query": "妖刀姬连招"})
    """
    builder = RAGGraphBuilder.from_yaml(config_path)
    return await builder.build(checkpoint_path)
