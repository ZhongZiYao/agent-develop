"""Prompt 模板 — RAG 系统 prompt 和用户 prompt

设计要点（面经可讲）：
1. 角色设定 → 约束行为
2. 检索上下文用 XML 标签包裹 → 防 prompt injection
3. 强制要求引文 → 减少幻觉
4. 明确"不知道就说不" → 不编造
"""

from __future__ import annotations

SYSTEM_PROMPT = """你是「GameGuide AI」，一个专业的游戏攻略问答助手。
你的任务是：基于用户提供的【参考资料】，准确、简洁地回答玩家的游戏问题。

【严格规则】
1. 必须基于参考资料回答，禁止编造任何不在参考资料中的信息
2. 关键信息后必须用 [1][2][3] 这样的引用编号标注来源
3. 如果参考资料中没有相关信息，请直接说：「这个问题暂未收录，建议参考官方资料或 Wiki」
4. 回答控制在 300 字以内，重点突出
5. 语言风格：清晰、友好、专业，避免过度修饰

【参考资料的格式说明】
每条参考资料都以 [编号] 开头，例如 [1] 标题：xxx ... 来源：xxx
请在引用时使用对应的编号。"""


def build_user_prompt(query: str, context_chunks: list[str], game: str = "") -> str:
    """
    构造用户 prompt（含参考资料）

    Args:
        query: 用户问题
        context_chunks: 已格式化的参考资料列表（每条含 [N] 标题、内容、来源）
        game: 游戏名（可选，作为上下文提示）
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

【回答】
"""


def format_context_chunk(idx: int, chunk) -> str:
    """把单个 chunk 格式化为带编号的参考资料字符串"""
    title = chunk.metadata.get("title", "未知标题")
    header = chunk.metadata.get("header", "")
    source = chunk.source or "未知来源"
    header_line = f"（{header}）" if header else ""
    return f"[{idx}] 标题：{title}{header_line}\n内容：{chunk.content}\n来源：{source}"