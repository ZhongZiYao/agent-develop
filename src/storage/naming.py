"""Session 智能命名 — 用 LLM 生成简洁标题

策略：
- 首条 query 后触发（异步，不阻塞主对话）
- prompt 让 LLM 输出 ≤10 字的中文标题
- 失败回退到 query 前 15 字
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from ..config import settings
from ..llm import get_llm, message_text
from ..prompts.thinking_parser import parse_thinking


NAMING_SYSTEM = """你是 GameGuide AI 的会话命名助手。
根据用户的首条问题，生成一个简洁的中文会话标题。

【要求】
1. 标题长度 ≤ 10 个中文字符（不超过 10 字）
2. 直接说主题，不要"关于..."等废话
3. 专有名词保留原文（角色名「妖刀姬」、错误码「E-4048」）
4. 输出只包含标题文字，不要引号、不要标点
"""

NAMING_USER_TEMPLATE = """【首条用户问题】
{query}

【会话标题】（≤10 字）"""


async def generate_session_title(query: str, fallback: str | None = None) -> str:
    """
    异步生成会话标题

    Args:
        query: 首条用户问题
        fallback: 失败兜底（默认用 query 前 15 字）

    Returns:
        标题字符串
    """
    try:
        llm = get_llm()
        # 限制 max_tokens 让 LLM 简短输出
        invoke_config = {"temperature": 0.3}
        if settings.llm_provider == "ollama":
            invoke_config["reasoning"] = False
        response = await llm.ainvoke(
            [
                SystemMessage(content=NAMING_SYSTEM),
                HumanMessage(content=NAMING_USER_TEMPLATE.format(query=query)),
            ],
            **invoke_config,
        )

        raw_title = message_text(response).strip()
        clean_title, _thinking = parse_thinking(raw_title)
        title = (clean_title or raw_title).strip()
        # 去掉可能的引号和末尾标点。
        title = title.strip('"').strip("'").strip("「").strip("」").strip()
        title = title.rstrip("。！？!?.，,").strip()
        # 严格限制为 10 个字符。
        if len(title) > 10:
            title = title[:10]

        return title or (fallback or query[:10])

    except Exception:
        return fallback or query[:10]


async def rename_session_async(session_id: str, new_title: str) -> bool:
    """异步重命名 session（不阻塞）"""
    try:
        from .storage.database import AsyncSessionLocal
        from .storage.session_store import SessionStore

        async with AsyncSessionLocal() as db:
            store = SessionStore(db)
            return await store.rename_session(session_id, new_title)
    except Exception:
        return False