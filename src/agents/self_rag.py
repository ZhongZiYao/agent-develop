"""Self-RAG 节点 — 判断查询是否需要 RAG 检索

Phase 6.6 新增功能：
- 在 Router 之后插入一道闸门，自评"该不该查"
- 闲聊型查询（你好/谢谢）直接 LLM 答，省检索
- 游戏实体查询（妖刀姬/S13/连招）必查
- 其余走 LLM 自评（复用 llm_classify_query 逻辑）
"""

from __future__ import annotations

import json
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from ..config import settings
from ..llm import get_llm, message_text


# ===== 黑白名单 =====

# 闲聊黑名单（不需要检索，直接 LLM 答）
CHITCHAT_PATTERNS = [
    r"^(你好|hi|hello|嗨|hey)",
    r"(谢谢|thank|thx|多谢)",
    r"^(再见|拜拜|bye|see you)",
    r"(你是谁|你能做什么|你会什么|介绍一下自己)",
]

# 游戏实体白名单（必须检索，保证游戏攻略查询准确）
GAME_ENTITY_KEYWORDS = [
    # 角色名
    "妖刀姬", "红蝶", "素问", "宁红夜", "顾清寒", "茨木", "酒吞", "大天狗",
    "座敷童子", "雪女", "面灵气", "追月神", "夜溟彼岸花", "阎魔", "缘结神",
    # 技能/装备
    "刃返", "突刺", "鬼缚", "连招", "装备", "御魂", "觉醒", "技能加点",
    # 版本/赛季
    "S13", "S12", "S11", "赛季", "版本", "更新",
    # 副本/活动
    "副本", "boss", "攻略", "阵容", "站位", "通关",
    # 错误码
    "E-4048", "E-", "错误码", "报错",
]


# ===== Prompt 模板 =====

SELF_RAG_SYSTEM = """你是一个查询意图分析器。判断用户问题是否需要检索 RAG 知识库。

【不需要检索】（need_retrieval=false）：
- 闲聊问候、自我介绍、能力询问
- 通用知识问答（不依赖特定游戏/产品）
- LLM 自身能直接回答的常识

【需要检索】（need_retrieval=true）：
- 涉及具体游戏角色/装备/技能/版本号
- 需要最新攻略或私有知识
- 涉及具体副本/任务/活动
- 询问错误码、配置项等专有内容

输出严格 JSON，不要其他内容：
{"need_retrieval": bool, "confidence": 0.0~1.0, "reason": "一句话理由"}"""

SELF_RAG_USER_TEMPLATE = """用户问题：{query}
启发式分类：{query_type}"""


# ===== Self-RAG 判断节点 =====


async def self_rag_judge_node(state: dict) -> dict:
    """Self-RAG 判断节点 — 评估查询是否需要 RAG 检索

    三级判断：
    1. 黑名单短路（闲聊型，不需要检索）
    2. 白名单短路（游戏实体，必须检索）
    3. LLM 自评（其余走 LLM 判断）

    Returns:
        {
            "need_retrieval": bool,
            "self_rag_confidence": float,
            "self_rag_reason": str,
            "trace_events": list[dict],  # 记录决策过程
        }
    """
    query = state.get("query", "")
    query_type = state.get("query_type", "simple")  # 从 router 继承

    ts_start = time.time()
    trace_events = list(state.get("trace_events") or [])

    # Push trace: started
    trace_events.append({
        "ts": ts_start,
        "node": "self_rag_judge",
        "type": "agent_trace",
        "status": "started",
        "payload": {"query_len": len(query), "query_type": query_type},
    })

    # 1. 黑名单短路
    for pattern in CHITCHAT_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            reason = "闲聊型查询，无需检索"
            logger.info(f"[SelfRAG] Blacklist match: {reason}")

            trace_events.append({
                "ts": time.time(),
                "node": "self_rag_judge",
                "type": "agent_trace",
                "status": "completed",
                "payload": {
                    "need_retrieval": False,
                    "confidence": 0.95,
                    "reason": reason,
                    "method": "blacklist",
                },
            })

            return {
                "need_retrieval": False,
                "self_rag_confidence": 0.95,
                "self_rag_reason": reason,
                "trace_events": trace_events,
            }

    # 2. 白名单短路
    for keyword in GAME_ENTITY_KEYWORDS:
        if keyword in query:
            reason = f"命中游戏实体关键词「{keyword}」，必须检索"
            logger.info(f"[SelfRAG] Whitelist match: {reason}")

            trace_events.append({
                "ts": time.time(),
                "node": "self_rag_judge",
                "type": "agent_trace",
                "status": "completed",
                "payload": {
                    "need_retrieval": True,
                    "confidence": 0.9,
                    "reason": reason,
                    "method": "whitelist",
                    "matched_keyword": keyword,
                },
            })

            return {
                "need_retrieval": True,
                "self_rag_confidence": 0.9,
                "self_rag_reason": reason,
                "trace_events": trace_events,
            }

    # 3. LLM 自评
    try:
        result = await _llm_judge_need_retrieval(query, query_type)
        logger.info(f"[SelfRAG] LLM judge: need_retrieval={result['need_retrieval']}, confidence={result['confidence']}")

        trace_events.append({
            "ts": time.time(),
            "node": "self_rag_judge",
            "type": "agent_trace",
            "status": "completed",
            "payload": {
                "need_retrieval": result["need_retrieval"],
                "confidence": result["confidence"],
                "reason": result["reason"],
                "method": "llm",
            },
        })

        return {
            "need_retrieval": result["need_retrieval"],
            "self_rag_confidence": result["confidence"],
            "self_rag_reason": result["reason"],
            "trace_events": trace_events,
        }

    except Exception as exc:
        # 降级：保守策略，默认需要检索
        reason = f"LLM 自评失败，保守策略默认检索（{exc}）"
        logger.warning(f"[SelfRAG] {reason}")

        trace_events.append({
            "ts": time.time(),
            "node": "self_rag_judge",
            "type": "agent_trace",
            "status": "completed",
            "payload": {
                "need_retrieval": True,
                "confidence": 0.5,
                "reason": reason,
                "method": "fallback",
            },
        })

        return {
            "need_retrieval": True,
            "self_rag_confidence": 0.5,
            "self_rag_reason": reason,
            "trace_events": trace_events,
        }


async def _llm_judge_need_retrieval(query: str, query_type: str) -> dict:
    """LLM 判断是否需要检索

    Returns:
        {"need_retrieval": bool, "confidence": float, "reason": str}
    """
    llm = get_llm()

    user_prompt = SELF_RAG_USER_TEMPLATE.format(
        query=query,
        query_type=query_type,
    )

    # 调用 LLM（temperature 低一些，更确定性）
    invoke_config = {"temperature": 0.1}
    if settings.llm_provider == "ollama":
        invoke_config["reasoning"] = False  # Self-RAG 不需要推理模式

    response = await llm.ainvoke(
        [
            SystemMessage(content=SELF_RAG_SYSTEM),
            HumanMessage(content=user_prompt),
        ],
        **invoke_config,
    )

    raw_text = message_text(response).strip()

    # 解析 JSON
    try:
        # 尝试提取 JSON 块（有些模型会包一层 ```json）
        json_match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
        else:
            result = json.loads(raw_text)

        # 验证字段
        need_retrieval = bool(result.get("need_retrieval", True))
        confidence = float(result.get("confidence", 0.5))
        reason = str(result.get("reason", "LLM 未提供理由"))

        # confidence 低于 0.5 时保守策略：默认需要检索
        if confidence < 0.5:
            need_retrieval = True

        return {
            "need_retrieval": need_retrieval,
            "confidence": confidence,
            "reason": reason,
        }

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"[SelfRAG] Failed to parse LLM response: {raw_text[:200]}, error: {e}")
        # 解析失败，保守策略
        return {
            "need_retrieval": True,
            "confidence": 0.5,
            "reason": "LLM 响应格式异常，保守策略默认检索",
        }


# ===== 直答节点（不检索） =====


async def llm_only_answer_node(state: dict) -> dict:
    """LLM 直答节点 — 不检索，直接用 LLM 回答

    适用场景：Self-RAG 判断 need_retrieval=False 的查询
    """
    query = state.get("query", "")
    ts_start = time.time()
    trace_events = list(state.get("trace_events") or [])

    # Push trace: started
    trace_events.append({
        "ts": ts_start,
        "node": "llm_only_answer",
        "type": "agent_trace",
        "status": "started",
        "payload": {},
    })

    llm = get_llm()

    # 简单对话 prompt（不需要 RAG 上下文）
    system_prompt = """你是 GameGuide AI，一个友好的游戏助手。

用户向你打招呼或问一些通用问题，请简洁、礼貌地回答。不要编造游戏攻略细节。

如果用户问游戏相关问题，提示他们可以问更具体的问题（如角色名、技能名、副本名）。"""

    invoke_config = {"temperature": 0.3}
    if settings.llm_provider == "ollama":
        invoke_config["reasoning"] = False

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query),
            ],
            **invoke_config,
        )

        answer = message_text(response).strip()
        logger.info(f"[LLM_Only] Generated answer (len={len(answer)})")

        trace_events.append({
            "ts": time.time(),
            "node": "llm_only_answer",
            "type": "agent_trace",
            "status": "completed",
            "payload": {"answer_len": len(answer)},
        })

        return {
            "answer": answer,
            "thinking": "",  # 无思考过程
            "retrieved_docs": [],  # 无检索文档
            "trace_events": trace_events,
        }

    except Exception as exc:
        logger.error(f"[LLM_Only] Error: {exc}")

        trace_events.append({
            "ts": time.time(),
            "node": "llm_only_answer",
            "type": "agent_trace",
            "status": "failed",
            "payload": {"error": str(exc)},
        })

        return {
            "answer": "抱歉，我遇到了一些问题，请稍后再试。",
            "thinking": "",
            "retrieved_docs": [],
            "trace_events": trace_events,
        }
