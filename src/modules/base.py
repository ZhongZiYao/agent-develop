"""Modular RAG 抽象基类

每个 RAG 组件都是 RAGModule 的子类。
通过 ModuleRegistry 可以按名字动态注册和获取模块。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass
class ModuleConfig:
    """模块配置（dataclass，可序列化）"""
    name: str
    type: str
    enabled: bool = True
    params: dict = field(default_factory=dict)


class RAGModule(ABC):
    """所有 RAG 模块的抽象基类

    实现方式：
        class MyModule(RAGModule):
            name = "my_module"  # 用于注册和配置查找

            async def __call__(self, state):
                # 业务逻辑：读取 state，返回部分更新
                return {"some_field": new_value}

            def get_config(self):
                return ModuleConfig(
                    name=self.name,
                    type=self.__class__.__name__,
                    params={"some_param": 42},
                )
    """

    # 子类必须设置
    name: ClassVar[str] = ""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    async def __call__(self, state: dict) -> dict:
        """处理 state，返回部分状态更新

        Args:
            state: 当前 Graph State

        Returns:
            部分状态更新 dict（可包含任意字段）
        """
        raise NotImplementedError

    def get_config(self) -> ModuleConfig:
        """导出当前模块配置（用于序列化）"""
        return ModuleConfig(
            name=self.name or self.__class__.__name__,
            type=self.__class__.__name__,
            params=self.config,
        )

    @classmethod
    def from_config(cls, config: ModuleConfig | dict) -> "RAGModule":
        """从配置创建模块实例"""
        if isinstance(config, dict):
            config = ModuleConfig(
                name=config.get("name", cls.__name__),
                type=config.get("type", cls.__name__),
                enabled=config.get("enabled", True),
                params=config.get("params", {}),
            )
        if not config.enabled:
            return None  # type: ignore
        return cls(config.params)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name or '?'}>"


class ModuleRegistry:
    """模块全局注册表

    用法：
        @ModuleRegistry.register
        class QueryRewriter(RAGModule):
            name = "query_rewriter"
            ...

        # 按名字获取类
        cls = ModuleRegistry.get("query_rewriter")
        instance = cls.from_config({"params": {...}})
    """

    _registry: dict[str, type[RAGModule]] = {}

    @classmethod
    def register(cls, target: type[RAGModule]) -> type[RAGModule]:
        """装饰器：将模块类注册到全局表"""
        if not target.name:
            raise ValueError(
                f"Module {target.__name__} must define 'name' class attribute"
            )
        cls._registry[target.name] = target
        return target

    @classmethod
    def get(cls, name: str) -> type[RAGModule] | None:
        """按名字获取模块类"""
        return cls._registry.get(name)

    @classmethod
    def list_names(cls) -> list[str]:
        """列出所有已注册模块"""
        return list(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（主要用于测试）"""
        cls._registry.clear()
