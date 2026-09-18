"""思考过程解析工具

业界模型（DeepSeek R1、Claude Extended Thinking、Gemini Thinking、Qwen QwQ）
都会在 answer 里输出 <scratchpad>...</scratchpad> 或 <think>...</think> 块
代表模型的"推理过程"。

本模块负责：
1. 从完整文本里剥离 thinking 块（保留 answer）
2. 在流式增量场景下做状态机解析（避免正则跨 chunk 切分出错）
"""

from __future__ import annotations

import re


# 支持多种 thinking 标签（不同厂商格式不一样）
THINKING_PATTERNS = [
    (r"<think>(.*?)</think>", "think"),
    (r"<scratchpad>(.*?)</scratchpad>", "scratchpad"),
    (r"<reasoning>(.*?)</reasoning>", "reasoning"),
]

# 编译正则（re.DOTALL 让 . 匹配换行）
THINKING_REGEXES = [
    (re.compile(p, re.DOTALL), name) for p, name in THINKING_PATTERNS
]


def parse_thinking(text: str) -> tuple[str, str]:
    """
    从完整 answer 文本里剥离 thinking 块

    Returns:
        (clean_answer, thinking_content)

    Example:
        >>> parse_thinking("<think>用户问的是 X</think>\\n\\n答案是 Y")
        ('\\n\\n答案是 Y', '用户问的是 X')
    """
    if not text:
        return "", ""

    thinking_parts: list[str] = []
    clean_text = text

    for regex, _ in THINKING_REGEXES:
        for match in regex.finditer(clean_text):
            thinking_parts.append(match.group(1).strip())
        clean_text = regex.sub("", clean_text)

    # 合并所有 thinking（按顺序）
    thinking = "\n\n".join(p for p in thinking_parts if p).strip()
    # 清理 answer 头部可能的多余空行
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()

    return clean_text, thinking


class StreamThinkingParser:
    """
    流式响应状态机解析器 — 边收 delta 边识别 thinking vs answer

    为什么不直接用正则？
    - 因为 <think> 可能跨 SSE chunk 切分（"<think>用户问" 在 chunk1，"的是X</think>答案" 在 chunk2）
    - 纯正则匹配会漏掉切分到两个 chunk 的内容

    状态机：
    - NORMAL：累积 answer
    - IN_THINKING：累积 thinking（直到遇到结束标签）
    """

    NORMAL = "normal"
    IN_THINKING = "in_thinking"

    def __init__(self):
        self.state = self.NORMAL
        self.answer_buf = ""
        self.thinking_buf = ""
        # 滑动窗口 buffer（用来检测跨 chunk 的开始标签）
        self.tail_window = ""

    def feed(self, delta: str) -> tuple[str, str]:
        """
        输入一段 delta，返回 (answer_delta, thinking_delta)
        - answer_delta：要推给用户看的答案片段
        - thinking_delta：要累积到 thinking 的片段
        """
        if not delta:
            return "", ""

        # 把 delta 加到滑动窗口
        combined = self.tail_window + delta
        answer_out = ""
        thinking_out = ""

        # 状态机处理
        i = 0
        while i < len(combined):
            if self.state == self.NORMAL:
                # 找 '<' 的位置（避免在 answer 里用 regex.match 全文扫描）
                lt_idx = combined.find("<", i)
                if lt_idx == -1:
                    # 没有 '<'，整段都是 answer
                    answer_out += combined[i:]
                    i = len(combined)
                    self.tail_window = ""
                    break
                # 检查从这个 '<' 开始的标签是不是 thinking 开始标签
                entered = False
                for regex, _ in THINKING_REGEXES:
                    m = regex.match(combined, lt_idx)
                    if m:
                        # 进入标签之前的部分作为 answer
                        answer_out += combined[i : m.start()]
                        self.thinking_buf += m.group(1)
                        self.state = self.IN_THINKING
                        i = m.end()
                        entered = True
                        break
                if not entered:
                    # 不是 thinking 标签：把 < 之前作为 answer，< 之后保留为 tail
                    answer_out += combined[i:lt_idx]
                    self.tail_window = combined[lt_idx:]
                    i = len(combined)
                    break
            else:
                # IN_THINKING：找结束标签
                ended = False
                for regex, _ in THINKING_REGEXES:
                    m = regex.search(combined, i)
                    if m:
                        # 把到结束标签之前的内容加入 thinking
                        before = combined[i : m.start()]
                        self.thinking_buf += before
                        thinking_out = before + combined[m.start() : m.end()]
                        self.state = self.NORMAL
                        i = m.end()
                        ended = True
                        break
                if not ended:
                    # 没找到结束标签：累积 thinking，保留可能跨 chunk 的尾巴
                    self.thinking_buf += combined[i:]
                    self.tail_window = combined[-32:]  # 保留长一些（含结束标签）
                    i = len(combined)
                    break

        self.answer_buf += answer_out
        return answer_out, thinking_out

    def _extract_possible_tag_prefix(self, text: str) -> str:
        """
        提取文本末尾可能跨 chunk 的开始标签前缀
        例如 text = "用户问的是<think>用户问" → 返回 "<think>用户问"
        防止 "<think>" 被切到下一个 chunk 时漏识别
        """
        # 取最后 16 个字符（足够覆盖 "<scratchpad>" 这种最长标签）
        tail = text[-16:] if len(text) >= 16 else text
        # 如果包含 '<'，取 '<' 之后的部分
        if "<" in tail:
            return tail[tail.index("<"):]
        return ""

    def flush(self) -> str:
        """
        流结束：把剩余 buffer 返回为 thinking（如果还在 thinking 状态）
        通常用于 fallback——正常情况应该已经在 IN_THINKING 结束时返回
        """
        if self.state == self.IN_THINKING and self.thinking_buf:
            remaining = self.thinking_buf
            self.thinking_buf = ""
            self.state = self.NORMAL
            return remaining
        return ""

    def get_full_thinking(self) -> str:
        """获取累积的 thinking（通常在流结束时调一次）"""
        return self.thinking_buf.strip()

    def get_full_answer(self) -> str:
        """获取累积的 answer"""
        return self.answer_buf.strip()