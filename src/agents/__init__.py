"""Agentic RAG 模块

实现 ReAct + Reflexion 架构的 Agent 系统：
- Router: 查询路由（simple/agentic）
- ReAct Agent: Thought → Action → Observation 循环
- Reflexion: Reflection → Evaluator → Replan 自我纠错
- Tools: rag_search, compare, finish
- Agentic RAG Graph: 完整流程编排
"""

from .agentic_rag_graph import build_agentic_rag_graph, run_agentic_rag
from .react_agent import ReActAgent, react_agent_node, should_continue
from .reflexion import evaluator_node, reflection_node, replan_node
from .router import router_node
from .tools import AGENT_TOOLS, Tool, get_tool_by_name, get_tools_description

__all__ = [
    "ReActAgent",
    "react_agent_node",
    "should_continue",
    "router_node",
    "reflection_node",
    "evaluator_node",
    "replan_node",
    "Tool",
    "AGENT_TOOLS",
    "get_tool_by_name",
    "get_tools_description",
    "build_agentic_rag_graph",
    "run_agentic_rag",
]
