"""思考过程解析工具

业界模型（DeepSeek R1、Claude Extended Thinking、Gemini Thinking、Qwen QwQ）
都会在 answer 里输出 <think>...</think> 或 <scratchpad>...</scratchpad> 块
代表模型的"推理过程"。

本模块负责：
1. 从完整文本里剥离 thinking 块（保留 answer）
2. 在流式增量场景下做状态机解析（避免正则跨 chunk 切分出错）
3. 流式场景下持续返回 thinking 增量，让前端实时看到
"""

from __future__ import annotations

import re


# 完整块匹配（用于 parse_thinking 一次性剥离）
THINKING_FULL_REGEXES = [
    re.compile(r"<think>.*?</think>", re.DOTALL),
    re.compile(r"<scratchpad>.*?</scratchpad>", re.DOTALL),
    re.compile(r"<reasoning>.*?</reasoning>", re.DOTALL),
]

# 开始/结束标签（用于流式状态机）
THINKING_OPEN_REGEX = re.compile(r"<(think|scratchpad|reasoning)(?:\s[^>]*)?>", re.IGNORECASE)
THINKING_CLOSE_REGEX = re.compile(r"</(think|scratchpad|reasoning)>", re.IGNORECASE)


def parse_thinking(text: str) -> tuple[str, str]:
    """从完整 answer 文本里剥离 thinking 块。Returns (clean_answer, thinking_content)"""
    if not text:
        return "", ""

    thinking_parts: list[str] = []
    clean_text = text

    for regex in THINKING_FULL_REGEXES:
        for match in regex.finditer(clean_text):
            inner = match.group(0)
            inner = re.sub(r"^<[^>]+>", "", inner)
            inner = re.sub(r"</[^>]+>$", "", inner)
            thinking_parts.append(inner.strip())
        clean_text = regex.sub("", clean_text)

    thinking = "\n\n".join(p for p in thinking_parts if p).strip()
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()
    return clean_text, thinking


class StreamThinkingParser:
    """
    流式响应状态机解析器。

    设计原则（避免重复累积）：
    - buf 是"已确认累积"的全量
    - delta 是每次新进来的数据
    - feed() 把"delta"加到 buf，并返回本次新增
    - tail_window 只用于"还没确定的"尾巴（为了跨 chunk 检测）
    """

    NORMAL = "normal"
    IN_THINKING = "in_thinking"

    def __init__(self):
        self.state = self.NORMAL
        self.answer_buf = ""
        self.thinking_buf = ""
        # tail_window 仅用于 NORMAL 状态下保留可能跨 chunk 的开始标签前缀
        self.tail_window = ""

    def feed(self, delta: str) -> tuple[str, str]:
        """
        输入一段 delta，返回 (answer_delta, thinking_delta)。
        """
        if not delta:
            return "", ""

        if self.state == self.NORMAL:
            return self._feed_normal(delta)
        else:
            thinking_delta, answer_delta = self._process_thinking(delta)
            # _process_thinking 内部没累计 answer_buf，这里补上
            self.answer_buf += answer_delta
            return answer_delta, thinking_delta

    def _process_thinking(self, chunk: str) -> tuple[str, str]:
        """
        在 IN_THINKING 状态下处理一段 chunk，返回 (thinking_delta, answer_delta)。
        找到结束标签时切换到 NORMAL，并直接处理后续 answer 内容（不递归）。
        """
        if not chunk:
            return "", ""

        close_match = THINKING_CLOSE_REGEX.search(chunk)
        if close_match:
            before = chunk[: close_match.start()]
            after = chunk[close_match.end():]
            self.thinking_buf += before
            self.state = self.NORMAL
            self.tail_window = ""
            # 直接处理 after：当 NORMAL 状态处理
            # 简单情况：after 中没有 < 也没有跨 chunk 标签前缀
            if after:
                # 扫 after 中的 thinking 开始标签（可能在 after 里又有一个新 thinking）
                # 但通常不会有，简化处理：after 全当作 answer
                # 检查 after 是否含 < 但不是开始标签
                if "<" in after:
                    # 复杂情况：after 中可能含开始标签，按 NORMAL 处理
                    # 但要避免重复累计 answer_buf（_feed_normal 内部已经累计了）
                    answer_delta, thinking_delta = self._feed_normal(after)
                    return before, answer_delta
                return before, after
            return before, ""
        else:
            self.thinking_buf += chunk
            return chunk, ""

    def _feed_normal(self, text: str) -> tuple[str, str]:
        """NORMAL 状态处理一段文本（已包含 tail_window 处理）。返回 (answer_delta, thinking_delta)"""
        answer_out = ""
        thinking_out = ""
        combined = self.tail_window + text
        self.tail_window = ""
        i = 0
        while i < len(combined):
            lt_idx = combined.find("<", i)
            if lt_idx == -1:
                answer_out += combined[i:]
                i = len(combined)
                break
            open_match = THINKING_OPEN_REGEX.match(combined, lt_idx)
            if open_match:
                answer_out += combined[i : open_match.start()]
                self.state = self.IN_THINKING
                thinking_start = open_match.end()
                # 处理剩余部分
                remaining = combined[thinking_start:]
                close_match = THINKING_CLOSE_REGEX.search(remaining)
                if close_match:
                    before = remaining[: close_match.start()]
                    after_close = remaining[close_match.end():]
                    self.thinking_buf += before
                    thinking_out += before
                    self.state = self.NORMAL
                    self.tail_window = ""
                    answer_out += after_close
                else:
                    self.thinking_buf += remaining
                    thinking_out += remaining
                break
            else:
                answer_out += combined[i:lt_idx]
                self.tail_window = combined[lt_idx:]
                break
        self.answer_buf += answer_out
        return answer_out, thinking_out

    def flush(self) -> str:
        """流结束时返回尚未发送的残留内容；当前实现逐段发送，因此无残留。"""
        return ""

    def get_full_thinking(self) -> str:
        return self.thinking_buf.strip()

    def get_full_answer(self) -> str:
        return self.answer_buf.strip()