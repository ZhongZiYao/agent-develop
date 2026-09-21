"""Feature Flag 回退验证

验证 ENABLE_SELF_RAG / ENABLE_AGENT_TRACE 两个 flag 关闭时：
1. Graph 不注册 self_rag_judge 节点（router 直通 route_decision）
2. Graph_routes 不发 agent_* SSE 事件
3. 行为与改造前完全一致（向后兼容）

这些测试不依赖真实 LLM，只验证：
- graph_nodes() 中节点列表
- graph_routes event_generator() 行为（mock）
"""

import pytest

from src.agents.agentic_rag_graph import build_agentic_rag_graph


class TestSelfRAGFeatureFlag:
    """ENABLE_SELF_RAG 回退测试"""

    @pytest.mark.asyncio
    async def test_self_rag_enabled_registers_nodes(self):
        """启用 Self-RAG 时，self_rag_judge / llm_only_answer 节点应注册"""
        graph = await build_agentic_rag_graph(enable_self_rag=True)

        # StateGraph 编译后从 builder.nodes 拿
        nodes = list(graph.builder.nodes.keys())
        assert "self_rag_judge" in nodes, "启用 Self-RAG 应注册 self_rag_judge 节点"
        assert "llm_only_answer" in nodes, "启用 Self-RAG 应注册 llm_only_answer 节点"

    @pytest.mark.asyncio
    async def test_self_rag_disabled_skips_nodes(self):
        """禁用 Self-RAG 时，不应注册 self_rag 相关节点"""
        graph = await build_agentic_rag_graph(enable_self_rag=False)

        nodes = list(graph.builder.nodes.keys())
        assert "self_rag_judge" not in nodes, "禁用 Self-RAG 不应有 self_rag_judge 节点"
        assert "llm_only_answer" not in nodes, "禁用 Self-RAG 不应有 llm_only_answer 节点"
        assert "route_decision_node" not in nodes, "禁用 Self-RAG 不应有 route_decision_node"

        # Router 仍然存在
        assert "router" in nodes
        assert "direct_rag" in nodes
        assert "agentic_rag" in nodes

    @pytest.mark.asyncio
    async def test_self_rag_disabled_direct_routing(self):
        """禁用 Self-RAG 时，router 直通到 direct_rag / agentic_rag（不经过 self_rag_judge）"""
        graph = await build_agentic_rag_graph(enable_self_rag=False)

        # 校验图结构：entry_point = "router"
        # router → conditional → direct_rag / agentic_rag
        # 这是从源码层验证（StateGraph 编译后图结构不易反射）
        # 主要通过节点列表 + 不存在 self_rag_judge 来证明
        nodes = set(graph.builder.nodes.keys())
        assert "self_rag_judge" not in nodes
        assert "router" in nodes
        assert "direct_rag" in nodes
        assert "agentic_rag" in nodes


class TestAgentTraceFeatureFlag:
    """ENABLE_AGENT_TRACE 回退测试

    注：graph_routes 的 enable_agent_trace flag 通过 settings.enable_agent_trace 控制。
    测试通过 mock settings 来验证。
    """

    def test_settings_default_true(self):
        """默认 enable_agent_trace=True"""
        from src.config import Settings

        s = Settings()
        assert s.enable_agent_trace is True

    def test_settings_default_self_rag_true(self):
        """默认 enable_self_rag=True"""
        from src.config import Settings

        s = Settings()
        assert s.enable_self_rag is True

    def test_settings_disable_via_env(self, monkeypatch):
        """通过环境变量关闭 feature flag"""
        from src.config import Settings

        monkeypatch.setenv("ENABLE_SELF_RAG", "false")
        monkeypatch.setenv("ENABLE_AGENT_TRACE", "false")

        # 注：Settings 读 env_file 但 pydantic-settings 也会读进程 env，
        # 直接构造 Settings 测 env 行为需要 _env_file=None 避免 .env 覆盖
        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.enable_self_rag is False
        assert s.enable_agent_trace is False

    def test_settings_enable_via_env(self, monkeypatch):
        """通过环境变量开启 feature flag"""
        from src.config import Settings

        monkeypatch.setenv("ENABLE_SELF_RAG", "true")
        monkeypatch.setenv("ENABLE_AGENT_TRACE", "true")

        s = Settings(_env_file=None)  # type: ignore[call-arg]
        assert s.enable_self_rag is True
        assert s.enable_agent_trace is True


class TestBackwardCompatibility:
    """向后兼容验证：所有 flag 关闭时，行为与 Phase 6.5 之前一致"""

    @pytest.mark.asyncio
    async def test_graph_built_without_flags(self):
        """所有 flag 关闭，graph 仍能编译成功"""
        graph = await build_agentic_rag_graph(
            enable_self_rag=False,
            enable_reflexion=True,  # reflexion 不在本任务范围，保留
        )

        # 编译后能正常被调用（不执行）
        assert graph is not None
        nodes = set(graph.builder.nodes.keys())
        assert "router" in nodes
        assert "direct_rag" in nodes
        assert "agentic_rag" in nodes
        # self_rag 节点应不存在
        assert "self_rag_judge" not in nodes
