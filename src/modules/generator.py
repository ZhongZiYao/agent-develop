"""Generator Module

生成模块：根据检索到的上下文生成答案
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from ..config import settings
from ..llm import get_llm
from ..prompts.thinking_parser import StreamThinkingParser
from .base import ModuleRegistry, RAGModule


@ModuleRegistry.register
class GeneratorModule(RAGModule):
    """生成模块

    输入 state:
        - query: str
        - retrieved_docs: list[dict]
        - messages: list (历史消息，可选)
        - game: str (游戏名，可选)

    输出 state 更新:
        - answer: str
        - thinking: str (思考过程，可选)
    """

    name = "generator"

    def __init__(self, config: dict | None = None):
        super().__init__(config)

        self.llm = get_llm()
        self.enable_thinking = self.config.get("enable_thinking", settings.llm_reasoning)
        self.max_context_docs = self.config.get("max_context_docs", 5)
        self.system_prompt_template = self.config.get(
            "system_prompt",
            """你是一个游戏攻略助手，专门回答游戏相关问题。

请根据下面提供的参考资料回答用户问题：

{context}

注意事项：
1. 答案必须基于参考资料，禁止编造信息
2. 如果资料不足或无关，明确告知用户
3. 使用 Markdown 格式排版
4. 每个要点后添加引用编号 [1] [2] 等
5. 保持客观、专业、友好
""",
        )

    async def __call__(self, state: dict) -> dict:
        """生成答案"""
        query = state.get("query", "")
        retrieved_docs = state.get("retrieved_docs", [])
        messages = state.get("messages", [])
        game = state.get("game", "")

        if not query:
            logger.warning(f"[{self.name}] Empty query, returning empty answer")
            return {"answer": "", "thinking": ""}

        # 构建上下文
        context = self._build_context(retrieved_docs[: self.max_context_docs])

        # 构建 prompt
        system_prompt = self.system_prompt_template.format(context=context)
        user_prompt = query

        # 调用 LLM
        logger.debug(f"[{self.name}] Generating answer for query: {query[:50]}...")

        if self.enable_thinking:
            # 启用思考过程
            response = await self.llm.ainvoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            # 解析思考过程和答案
            parser = StreamThinkingParser()
            parser.feed(response.content)
            thinking = parser.get_thinking()
            answer = parser.get_answer()
        else:
            # 不启用思考过程
            response = await self.llm.ainvoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            thinking = ""
            answer = response.content

        logger.debug(
            f"[{self.name}] Generated answer: {len(answer)} chars, "
            f"thinking: {len(thinking)} chars"
        )

        return {
            "answer": answer,
            "thinking": thinking,
        }

    def _build_context(self, docs: list[dict]) -> str:
        """构建上下文字符串"""
        if not docs:
            return "（无相关参考资料）"

        context_parts = []
        for i, doc in enumerate(docs, start=1):
            title = doc.get("title", "未知")
            content = doc.get("content", "")
            score = doc.get("score", 0)

            context_parts.append(
                f"[{i}] {title}\n"
                f"相关度：{score:.3f}\n"
                f"{content}\n"
            )

        return "\n---\n".join(context_parts)

    def get_config(self):
        """导出配置"""
        config = super().get_config()
        config.params.update({
            "enable_thinking": self.enable_thinking,
            "max_context_docs": self.max_context_docs,
            "system_prompt": self.system_prompt_template,
        })
        return config
