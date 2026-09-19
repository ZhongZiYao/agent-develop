"""LLM provider 和消息解析单测。"""

from langchain_core.messages import AIMessage, AIMessageChunk

from src.llm import message_text, reasoning_text


def test_message_text_handles_string_and_blocks():
    assert message_text(AIMessage(content="answer")) == "answer"
    assert message_text(
        AIMessage(content=[{"type": "text", "text": "A"}, {"text": "B"}])
    ) == "AB"


def test_reasoning_text_reads_chatollama_field():
    message = AIMessageChunk(
        content="",
        additional_kwargs={"reasoning_content": "thinking"},
    )
    assert reasoning_text(message) == "thinking"
