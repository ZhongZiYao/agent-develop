"""Reflexion 自我纠错机制

实现：
1. Reflection: 评估当前步骤质量
2. Evaluator: 评估最终答案质量
3. Replan: 质量不佳时重新规划
"""

from __future__ import annotations

from loguru import logger

from ..llm import get_llm
from .memory import add_failure_memory


async def reflection_node(state: dict) -> dict:
    """反思节点：评估当前步骤的质量

    在每次 Agent 行动后，反思：
    - 这一步的结果有用吗？
    - 信息是否足够？
    - 需要调整策略吗？
    """
    llm = get_llm()

    agent_scratchpad = state.get("agent_scratchpad", [])
    query = state.get("query", "")

    if not agent_scratchpad:
        return {"reflection": ""}

    # 获取最后一步
    last_step = agent_scratchpad[-1]
    thought = last_step.get("thought", "")
    action = last_step.get("action", {})
    observation = last_step.get("observation", "")

    prompt = f"""你是一个自我反思的 AI Agent。

用户问题：{query}

最后一步：
- 思考：{thought}
- 动作：{action.get('tool')} with {action.get('args')}
- 观察：{str(observation)[:500]}...

请反思这一步的质量：
1. 这一步是否朝着解决问题的方向前进？
2. 获得的信息是否有用？
3. 是否需要调整策略？

输出格式：
质量评分：[1-5]
反思：[你的反思]
建议：[下一步建议]
"""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    reflection_text = response.content.strip()

    logger.debug(f"[Reflection] {reflection_text[:100]}...")

    return {"reflection": reflection_text}


async def evaluator_node(state: dict) -> dict:
    """评估节点：评估最终答案质量

    检查：
    - 信息完整性
    - 逻辑准确性
    - 是否需要补充
    """
    llm = get_llm()

    query = state.get("query", "")
    answer = state.get("answer", "")
    agent_scratchpad = state.get("agent_scratchpad", [])

    if not answer:
        logger.warning("[Evaluator] No answer to evaluate")
        return {"evaluation_score": 0.0, "need_replan": True}

    prompt = f"""你是一个答案质量评估器。

用户问题：{query}

Agent 的答案：{answer}

Agent 执行了 {len(agent_scratchpad)} 步：
{_format_scratchpad_summary(agent_scratchpad)}

请评估答案质量（1-5 分）：

评分标准：
- 5 分：完整准确，逻辑清晰，无需补充
- 4 分：基本完整，有小瑕疵
- 3 分：信息不足，需要补充
- 2 分：逻辑混乱，需要重新组织
- 1 分：完全错误，需要重新规划

输出格式：
分数：[1-5]
完整性：[评价]
准确性：[评价]
建议：[改进建议]
"""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    evaluation_text = response.content.strip()

    # 提取分数
    score = _extract_score(evaluation_text)

    logger.info(f"[Evaluator] Score: {score}/5")
    logger.debug(f"[Evaluator] {evaluation_text}")

    # 决定是否需要重新规划
    need_replan = score < 3.0

    # 如果质量低，记录到 Memory
    if need_replan:
        logger.info("[Evaluator] Low quality, recording to memory")
        await add_failure_memory(
            query=query,
            error_type="low_quality_answer",
            scratchpad=agent_scratchpad,
            solution="",  # 解决方案将在 replan 后更新
        )

    return {
        "evaluation_score": score,
        "need_replan": need_replan,
    }


async def replan_node(state: dict) -> dict:
    """重新规划节点：质量不佳时调整策略

    分析：
    - 哪里出了问题？
    - 应该采取什么不同的策略？
    """
    llm = get_llm()

    query = state.get("query", "")
    agent_scratchpad = state.get("agent_scratchpad", [])
    evaluation_score = state.get("evaluation_score", 0.0)

    prompt = f"""你是一个任务规划器。Agent 第一次尝试失败了，需要重新规划。

用户问题：{query}

第一次尝试（评分 {evaluation_score}/5）：
{_format_scratchpad_summary(agent_scratchpad)}

问题分析：
1. 哪个环节出了问题？
2. 为什么会失败？
3. 应该采取什么不同的策略？

请提供新的执行计划（3-5 步）：
1. [新策略第 1 步]
2. [新策略第 2 步]
...
"""

    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    new_plan = response.content.strip()

    logger.info(f"[Replan] New plan generated")
    logger.debug(f"[Replan] {new_plan}")

    # 解析新计划
    plan_steps = _parse_plan(new_plan)

    return {
        "plan": plan_steps,
        "current_step": 0,
        "agent_scratchpad": [],  # 清空历史，重新开始
        "iterations": 0,
    }


# ===== 辅助函数 =====


def _format_scratchpad_summary(scratchpad: list[dict]) -> str:
    """格式化 scratchpad 摘要"""
    if not scratchpad:
        return "（未执行任何步骤）"

    lines = []
    for item in scratchpad:
        iteration = item.get("iteration", 0)
        action = item.get("action", {})
        lines.append(f"Step {iteration}: {action.get('tool')} - {action.get('args')}")

    return "\n".join(lines)


def _extract_score(evaluation_text: str) -> float:
    """从评估文本中提取分数"""
    import re

    # 匹配 "分数：X" 或 "评分：X" 或 "X 分"
    patterns = [
        r'分数[：:]\s*([0-5](?:\.\d+)?)',
        r'评分[：:]\s*([0-5](?:\.\d+)?)',
        r'([0-5](?:\.\d+)?)\s*分',
    ]

    for pattern in patterns:
        match = re.search(pattern, evaluation_text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

    # 默认中等分数
    logger.warning("[Evaluator] Failed to extract score, defaulting to 3.0")
    return 3.0


def _parse_plan(plan_text: str) -> list[str]:
    """解析计划文本为步骤列表"""
    import re

    lines = plan_text.split('\n')
    steps = []

    for line in lines:
        # 匹配 "1. xxx" 或 "- xxx" 格式
        match = re.match(r'^\s*(?:\d+\.|[-*])\s*(.+)$', line)
        if match:
            steps.append(match.group(1).strip())

    return steps
