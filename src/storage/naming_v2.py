"""Session 智能命名 — Phase 2 改进版

改进要点（基于业界最佳实践）：
1. 参考检索内容生成更精准的标题
2. 长度 3-7 词（行业标准）
3. 支持多轮更新（主题变化时重新生成）
4. LLM 失败时降级到关键词提取
5. 重试机制（最多 2 次）
"""

from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from ..config import settings
from ..llm import get_llm, message_text
from ..prompts.thinking_parser import parse_thinking


# ===== 系统 Prompt（优化版）=====

NAMING_SYSTEM = """你是 GameGuide AI 的会话命名助手。

你的任务：根据用户的查询和参考信息，生成一个简洁、具体的中文会话标题。

【核心要求】
1. 长度 3-7 个中文字符（不要过长）
2. 必须具体（参考实际内容，不要"游戏问题"、"帮助"等泛词）
3. 必须包含：
   - 角色名（如「妖刀姬」「红蝶」「素问」）
   - 或核心动作（如「连招」「装备」「副本」）
   - 或问题主题（如「错误码」「更新」「攻略」）
4. 专有名词保留原文：
   - 角色名：「妖刀姬」「红蝶」等
   - 技能名：「刃返」「突刺」等
   - 错误码：「E-4048」等
   - 版本号：「S13」「S12」等

【格式示例】
✅ 正确示例：
- "妖刀姬S13连招"
- "红蝶第三技能"
- "素问副本站位"
- "E-4048错误码解决"

❌ 错误示例：
- "游戏问题"（太泛）
- "帮我查一下"（太口语）
- "Player Discussion"（混英文）
- "妖刀姬的所有相关信息"（太长）

【输出要求】
- 只输出标题文字
- 不要引号、不要标点
- 不要"标题："等前缀"""

NAMING_USER_TEMPLATE = """【用户问题】
{query}

【参考信息】（用于生成更精准的标题）
{context}

【会话标题】（3-7 字）"""


# ===== 关键词降级方案 =====


def extract_keywords_fallback(query: str, max_words: int = 7) -> str:
    """从查询中提取关键词作为降级标题"""
    # 游戏角色名（优先保留）
    game_chars = [
        "妖刀姬", "红蝶", "素问", "宁红夜", "顾清寒",
        "茨木", "酒吞", "大天狗",
    ]
    for char in game_chars:
        if char in query:
            return f"{char}相关问题"[:max_words * 2]  # 中文字符按 2 字节

    # 技能关键词
    skill_keywords = ["连招", "技能", "装备", "副本", "攻略", "升级", "加点"]
    for kw in skill_keywords:
        if kw in query:
            # 提取问题主体（如"妖刀姬连招"）
            return query[:14]  # 限制长度

    # 默认截取
    return query[:max_words * 2]


# ===== 核心函数 =====


async def generate_session_title(
    query: str,
    context: str = "",
    fallback: str | None = None,
    max_retries: int = 2,
) -> str:
    """
    异步生成会话标题（带重试和降级）

    Args:
        query: 首条用户问题
        context: 检索上下文（用于生成更精准的标题）
        fallback: 失败兜底
        max_retries: LLM 调用最大重试次数

    Returns:
        标题字符串
    """
    # 参数验证
    if not query or not query.strip():
        return fallback or "新对话"

    # 降级标题（作为 fallback）
    safe_fallback = fallback or extract_keywords_fallback(query)

    # 尝试 LLM 生成（带重试）
    for attempt in range(max_retries):
        try:
            title = await _call_llm_for_title(query, context)
            if title:
                logger.debug(f"[Naming] LLM generated title: {title}")
                return title
        except Exception as e:
            logger.warning(f"[Naming] Attempt {attempt + 1} failed: {e}")

    # 所有重试都失败，使用降级
    logger.info(f"[Naming] Using fallback: {safe_fallback}")
    return safe_fallback


async def _call_llm_for_title(query: str, context: str) -> str | None:
    """调用 LLM 生成标题（单次）"""
    llm = get_llm()

    # 简化 context（避免 prompt 过长）
    if context:
        # 只保留前 200 字符
        context_simple = context[:200].replace("\n", " ")
    else:
        context_simple = "（无检索结果，基于查询本身命名）"

    invoke_config = {"temperature": 0.3}
    if settings.llm_provider == "ollama":
        invoke_config["reasoning"] = False

    response = await llm.ainvoke(
        [
            SystemMessage(content=NAMING_SYSTEM),
            HumanMessage(
                content=NAMING_USER_TEMPLATE.format(
                    query=query,
                    context=context_simple,
                )
            ),
        ],
        **invoke_config,
    )

    raw_title = message_text(response).strip()

    # 清理响应
    clean_title, _thinking = parse_thinking(raw_title)
    title = (clean_title or raw_title).strip()

    # 去掉可能的引号、括号等
    title = re.sub(r'["\'「」『』\(\)\[\]]', '', title)
    # 去掉可能的前缀（如"标题："）
    title = re.sub(r'^(标题[:：]?|title[:：]?)', '', title, flags=re.IGNORECASE).strip()
    # 去掉末尾标点
    title = title.rstrip("。！？!?.，,").strip()

    # 验证长度（3-14 字符，灵活一些）
    if 2 <= len(title) <= 14:
        return title

    return None


async def rename_session_async(session_id: str, new_title: str) -> bool:
    """异步重命名 session（不阻塞）"""
    try:
        from .database import AsyncSessionLocal
        from .session_store import SessionStore

        async with AsyncSessionLocal() as db:
            store = SessionStore(db)
            return await store.rename_session(session_id, new_title)
    except Exception as exc:
        logger.warning(f"Failed to rename session {session_id}: {exc}")
        return False


# ===== 多轮更新（可选功能）=====

async def update_title_if_changed(
    session_id: str,
    new_query: str,
    current_title: str,
    context: str = "",
) -> str | None:
    """
    根据新查询判断是否需要更新标题

    Args:
        session_id: 会话 ID
        new_query: 新一轮的用户问题
        current_title: 当前标题
        context: 检索上下文

    Returns:
        新标题（如果需要更新）或 None（不需要更新）
    """
    # 简单判断：如果新查询的主题明显不同于当前标题
    # 使用 LLM 判断是否需要更新
    llm = get_llm()

    prompt = f"""判断新问题是否与当前标题主题明显不同，需要更新标题。

当前标题：{current_title}
新问题：{new_query}

只回复 yes 或 no：
- yes: 主题明显不同，应该更新标题
- no: 主题相同或相关，无需更新"""

    try:
        response = await llm.ainvoke(
            [HumanMessage(content=prompt)],
            temperature=0.1,
        )
        answer = message_text(response).strip().lower()
        if "yes" in answer:
            # 主题变化，重新生成标题
            return await generate_session_title(new_query, context)
        return None
    except Exception:
        return None