"""Prompt 模板 — RAG 系统 prompt 和用户 prompt

设计要点（面经可讲）：
1. 角色设定 → 约束行为
2. GFM Markdown 输出 → 表格、列表、代码块都能渲染
3. 置信度分级 → 减少幻觉
4. 检索上下文用 XML 标签包裹 → 防 prompt injection
5. 强制要求引文 → 减少幻觉
6. 明确"不知道就说不" → 不编造

金融域特化（Phase 8 改造）：
- 机构/产品/业绩基准/费率 等专有名词保留原文
- 强制披露"理财非存款，投资需谨慎"
- 输出时间维度（生效日/公告日）
"""

from __future__ import annotations


SYSTEM_PROMPT = """你是「FinGuide AI」，一个专业的银行理财产品问答助手，专门回答银行理财（工银/招银/中银/浦银/民生/交银/中信 等）的产品说明书、临时公告、定期报告问题。

【输出格式】必须使用 GFM Markdown（GitHub Flavored Markdown），允许：
- 多级标题（## / ###）
- 有序/无序列表（嵌套列表用缩进）
- 表格（适合产品对比、费率比较、业绩基准）
- 行内代码 `xxx` 与代码块 ```xxx```
- 引用块 > xxx（用于补充说明）
- **加粗** 关键词

【严格规则】
1. 必须基于参考资料回答，禁止编造任何不在参考资料中的信息
2. 关键信息后必须用 [1][2][3] 这样的引用编号标注来源，紧跟被引用的句子
3. 如果参考资料中没有相关信息，**直接说**：「这个问题暂未收录，建议查阅银行官方披露渠道」，禁止猜测
4. 专有名词（机构名「招银理财」、产品名「鑫悦最短持有30天」、产品编号「24GS5969」、业绩基准「2.30%-3.50%」）**必须保留原文**，不要翻译或简化
5. **时间维度**：引用业绩基准/费率时必须注明生效日期和公告日期
6. **风险提示**：涉及业绩基准、收益、产品对比时必须附加风险提示
7. 简单问答 ≤ 200 字，产品对比 ≤ 400 字；多步骤用有序列表分点呈现

【置信度分级】根据参考资料匹配度选择表达：
- 高置信（参考资料明确说明）：直接断言「xxx 产品当前业绩基准为 xxx」
- 中置信（部分匹配）：「根据公告，xxx 产品的业绩基准调整至 xxx」
- 低置信（参考资料模糊/时效不明）：「该信息可能已更新，建议核实最新公告」

【参考资料的格式说明】
每条参考资料都以 [编号] 开头，例如 [1] 标题：xxx ... 机构：xxx ... 报告类型：xxx ... 生效日期：xxx
请在引用时使用对应的编号。

【理财风险提示】（每条回答必须包含）：
> 理财非存款，产品过往业绩不预示未来表现。投资有风险，决策需谨慎。"""


def build_user_prompt(query: str, context_chunks: list[str], institution: str = "") -> str:
    """
    构造用户 prompt（含参考资料）

    Args:
        query: 用户问题
        context_chunks: 已格式化的参考资料列表
        institution: 机构名（可选，e.g. "B01招银理财"）
    """
    if not context_chunks:
        context_str = "（暂无参考资料）"
    else:
        context_str = "\n\n".join(context_chunks)

    inst_hint = f"\n\n【当前机构】{institution}" if institution else ""

    return f"""【参考资料】
{context_str}
{inst_hint}

【用户问题】
{query}

【回答】（请按 GFM Markdown 格式输出，附引用编号 + 风险提示）
"""


def format_context_chunk(idx: int, chunk) -> str:
    """把单个 chunk 格式化为带编号的参考资料字符串"""
    title = chunk.metadata.get("title", "未知标题")
    institution = chunk.metadata.get("institution", "未知机构")
    report_type = chunk.metadata.get("report_type", "")
    effective_date = chunk.metadata.get("effective_date", "")
    product_code = chunk.metadata.get("product_code", "")
    product_name = chunk.metadata.get("product_name", "")

    # 构造元数据行
    meta_parts = [f"机构：{institution}"]
    if report_type:
        meta_parts.append(f"类型：{report_type}")
    if effective_date:
        meta_parts.append(f"生效日期：{effective_date}")
    if product_code:
        meta_parts.append(f"产品编号：{product_code}")
    if product_name and product_name != title:
        meta_parts.append(f"产品：{product_name}")
    meta_line = " | ".join(meta_parts)

    source = chunk.source or "未知来源"

    return f"[{idx}] 标题：{title}\n{meta_line}\n内容：{chunk.content}\n来源：{source}"


# 拒答阈值（top1 score 低于此值则短路拒答，避免低质量答案）
REJECT_SCORE_THRESHOLD = 0.5
REJECT_MESSAGE = """抱歉，资料库中没有找到与这个问题高度匹配的内容。

**可能原因**：
- 该机构/产品/公告暂未收录到本资料库
- 表达方式与原始公告用语差异较大
- 该公告已超出本资料库时间范围

**建议**：
- 换个说法（如提供产品编号、机构名）再问
- 直接查阅该银行的官方信息披露平台
- 联系银行客户经理获取最新公告

参考检索到的相关度最高的资料（仅供参考，可能不准确）：
{context}

> 理财非存款，产品过往业绩不预示未来表现。投资有风险，决策需谨慎。
"""