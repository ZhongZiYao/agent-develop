"""ReAct Agent 核心节点

实现 ReAct 循环：
1. Thought: 思考下一步
2. Action: 选择工具并执行
3. Observation: 记录结果
4. Reflection: 反思质量
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from loguru import logger

from ..llm import get_llm
from .memory import add_failure_memory, retrieve_similar_memories
from .tools import AGENT_TOOLS, get_tool_by_name, get_tools_description


class ReActAgent:
    """ReAct Agent"""

    def __init__(self, max_iterations: int = 5):
        self.llm = get_llm()
        self.max_iterations = max_iterations

    async def run(self, state: dict) -> dict:
        """执行 ReAct 循环"""
        query = state.get("query", "")
        agent_scratchpad = state.get("agent_scratchpad", [])
        iterations = state.get("iterations", 0)
        trace_events = list(state.get("trace_events") or [])  # Phase 6.7

        logger.info(f"[ReActAgent] Starting iteration {iterations + 1}/{self.max_iterations}")

        # 1. Thought: 思考下一步
        thought = await self._think(query, agent_scratchpad)
        logger.debug(f"[ReActAgent] Thought: {thought}")

        # 2. Action: 选择工具
        action = await self._select_action(thought, agent_scratchpad)
        logger.debug(f"[ReActAgent] Action: {action}")

        # 3. Observation: 执行工具
        observation = await self._execute_action(action)
        logger.debug(f"[ReActAgent] Observation: {str(observation)[:100]}...")

        # 4. 记录到 scratchpad
        agent_scratchpad.append({
            "iteration": iterations + 1,
            "thought": thought,
            "action": action,
            "observation": observation,
        })

        # 5. Phase 6.7: push agent_step event 到 trace_events
        trace_events.append({
            "ts": time.time(),
            "node": "agentic_rag",
            "type": "agent_step",
            "iteration": iterations + 1,
            "status": "completed",
            "thought_preview": thought[:200],  # 截断
            "action": action,
            "observation_preview": str(observation)[:300],
        })

        # 6. 检查是否结束
        if action.get("tool") == "finish":
            return {
                "answer": action.get("args", {}).get("answer", ""),
                "agent_scratchpad": agent_scratchpad,
                "iterations": iterations + 1,
                "trace_events": trace_events,
            }

        # 7. 更新状态
        return {
            "agent_scratchpad": agent_scratchpad,
            "iterations": iterations + 1,
            "trace_events": trace_events,
        }

    async def _think(self, query: str, scratchpad: list[dict]) -> str:
        """思考下一步"""
        # 构建历史记录
        history = self._format_scratchpad(scratchpad)

        # 检索相似的失败经验
        memories = await retrieve_similar_memories(query, top_k=2)
        memory_context = self._format_memories(memories)

        prompt = f"""你是一个游戏攻略 AI Agent，使用 ReAct 框架回答用户问题。

用户问题：{query}

你可以使用以下工具：
{get_tools_description()}

已执行步骤：
{history}

{memory_context}

请思考：
1. 当前已经获得了哪些信息？
2. 还需要什么信息才能回答问题？
3. 下一步应该做什么？

只输出你的思考过程，不要输出工具调用。
"""

        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        return response.content.strip()

    async def _select_action(self, thought: str, scratchpad: list[dict]) -> dict:
        """选择下一个动作"""
        tools_desc = get_tools_description()

        prompt = f"""基于以下思考，选择下一个工具调用。

思考：{thought}

可用工具：
{tools_desc}

输出格式（JSON）：
{{
    "tool": "工具名称",
    "args": {{"参数名": "参数值"}}
}}

如果你认为已经有足够信息回答问题，使用 finish 工具。

只输出 JSON，不要其他内容。
"""

        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        action_text = response.content.strip()

        # 解析 JSON
        try:
            # 提取 JSON（可能包含 markdown code block）
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', action_text, re.DOTALL)
            if json_match:
                action_text = json_match.group(1)

            action = json.loads(action_text)
            return action
        except Exception as e:
            logger.error(f"[ReActAgent] Failed to parse action: {e}")
            # 默认：结束
            return {"tool": "finish", "args": {"answer": "抱歉，我无法解析下一步操作。"}}

    async def _execute_action(self, action: dict) -> Any:
        """执行工具"""
        tool_name = action.get("tool")
        args = action.get("args", {})

        tool = get_tool_by_name(tool_name)
        if tool is None:
            logger.error(f"[ReActAgent] Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = await tool.run(**args)
            return result
        except Exception as e:
            logger.error(f"[ReActAgent] Tool execution failed: {e}")
            return {"error": str(e)}

    def _format_scratchpad(self, scratchpad: list[dict]) -> str:
        """格式化历史记录"""
        if not scratchpad:
            return "（还没有执行任何步骤）"

        lines = []
        for item in scratchpad:
            iteration = item.get("iteration", 0)
            thought = item.get("thought", "")
            action = item.get("action", {})
            observation = item.get("observation", "")

            lines.append(f"--- Iteration {iteration} ---")
            lines.append(f"Thought: {thought}")
            lines.append(f"Action: {action.get('tool')} with args {action.get('args')}")
            lines.append(f"Observation: {str(observation)[:200]}...")
            lines.append("")

        return "\n".join(lines)

    def _format_memories(self, memories: list[dict]) -> str:
        """格式化 Memory 上下文"""
        if not memories:
            return ""

        lines = ["过去的失败经验（供参考）："]
        for i, mem in enumerate(memories, 1):
            lines.append(f"\n经验 {i}:")
            lines.append(f"- 查询：{mem['query']}")
            lines.append(f"- 错误类型：{mem['error_type']}")
            lines.append(f"- 尝试过的步骤：{mem['scratchpad_summary']}")
            if mem.get('solution'):
                lines.append(f"- 解决方案：{mem['solution']}")

        return "\n".join(lines)


# ===== LangGraph 节点包装 =====


async def react_agent_node(state: dict) -> dict:
    """ReAct Agent 节点（用于 LangGraph）"""
    agent = ReActAgent(max_iterations=state.get("max_iterations", 5))
    return await agent.run(state)


async def should_continue(state: dict) -> str:
    """判断是否继续循环"""
    iterations = state.get("iterations", 0)
    max_iterations = state.get("max_iterations", 5)
    answer = state.get("answer", "")

    # 已经有答案 → 结束
    if answer:
        logger.info("[ReActAgent] Answer ready, ending loop")
        return "end"

    # 达到最大迭代次数 → 强制结束
    if iterations >= max_iterations:
        logger.warning(f"[ReActAgent] Max iterations ({max_iterations}) reached")
        return "end"

    # 继续循环
    logger.info(f"[ReActAgent] Continue loop (iteration {iterations}/{max_iterations})")
    return "continue"
