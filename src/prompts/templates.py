"""Prompt 模板 — RAG 系统 prompt 和用户 prompt

设计要点（面经可讲）：
1. 角色设定 → 约束行为
2. GFM Markdown 输出 → 表格、列表、代码块都能渲染
3. 置信度分级 → 减少幻觉
4. 检索上下文用 XML 标签包裹 → 防 prompt injection
5. 强制要求引文 → 减少幻觉
6. 明确"不知道就说不" → 不编造
"""

from __future__ import annotations


SYSTEM_PROMPT = """你是「GameGuide AI」，一个专业的游戏攻略问答助手，专门回答网易系游戏（永劫无间 / 第五人格 / 逆水寒）的玩家问题。

【输出格式】必须使用 GFM Markdown（GitHub Flavored Markdown），允许：
- 多级标题（## / ###）
- 有序/无序列表（嵌套列表用缩进）
- 表格（适合装备对比、技能数值）
- 行内代码 `xxx` 与代码块 ```xxx```
- 引用块 > xxx（用于补充说明）
- **加粗** 关键词

【严格规则】
1. 必须基于参考资料回答，禁止编造任何不在参考资料中的信息
2. 关键信息后必须用 [1][2][3] 这样的引用编号标注来源，紧跟被引用的句子
3. 如果参考资料中没有相关信息，**直接说**：「这个问题暂未收录，建议查阅官方 Wiki」，禁止猜测
4. 专有名词（角色名「妖刀姬」、技能名「刃返」、错误码「E-4048」）**必须保留原文**，不要翻译
5. 简单问答 ≤ 200 字，攻略解读 ≤ 400 字；多步骤用有序列表分点呈现

【置信度分级】根据参考资料匹配度选择表达：
- 高置信（参考资料明确说明）：直接断言「xxx 是 xxx」
- 中置信（部分匹配）：「根据参考资料，xxx 通常是 xxx」
- 低置信（参考资料模糊）：「参考资料未明确说明，建议核实」

【参考资料的格式说明】
每条参考资料都以 [编号] 开头，例如 [1] 标题：xxx ... 来源：xxx
请在引用时使用对应的编号。"""


def build_user_prompt(query: str, context_chunks: list[str], game: str = "") -> str:
    """
    构造用户 prompt（含参考资料）

    Args:
        query: 用户问题
        context_chunks: 已格式化的参考资料列表
        game: 游戏名（可选）
    """
    if not context_chunks:
        context_str = "（暂无参考资料）"
    else:
        context_str = "\n\n".join(context_chunks)

    game_hint = f"\n\n【当前游戏】{game}" if game else ""

    return f"""【参考资料】
{context_str}
{game_hint}

【用户问题】
{query}

【回答】（请按 GFM Markdown 格式输出，附引用编号）
"""


def format_context_chunk(idx: int, chunk) -> str:
    """把单个 chunk 格式化为带编号的参考资料字符串"""
    title = chunk.metadata.get("title", "未知标题")
    header = chunk.metadata.get("header", "")
    source = chunk.source or "未知来源"
    header_line = f"（{header}）" if header else ""
    return f"[{idx}] 标题：{title}{header_line}\n内容：{chunk.content}\n来源：{source}"


# 拒答阈值（top1 score 低于此值则短路拒答，避免低质量答案）
REJECT_SCORE_THRESHOLD = 0.5
REJECT_MESSAGE = """抱歉，资料库中没有找到与这个问题高度匹配的内容。

**可能原因**：
- 问题涉及的版本/角色/装备暂未收录
- 表达方式与资料库用语差异较大

**建议**：
- 换个说法再问
- 查阅官方 Wiki 或相关攻略文章
- 如需补充资料，可以在 GitHub 提 Issue

参考检索到的相关度最高的资料（仅供参考，可能不准确）：
{context}
"""