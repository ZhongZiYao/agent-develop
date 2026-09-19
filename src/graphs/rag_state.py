"""RAG State 定义"""

from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class RAGState(TypedDict):
    """RAG Graph 状态定义

    State 在 Graph 执行过程中传递，每个节点可读写特定字段。
    """

    # ===== 输入 =====
    query: str
    """用户查询"""

    game: str
    """游戏过滤条件（可选）"""

    session_id: str
    """会话 ID（用于 SessionStore 元数据管理）"""

    top_k: int
    """召回候选数量"""

    top_n: int
    """最终使用的 context 数量"""

    # ===== 检索结果 =====
    retrieved_docs: list[dict]
    """检索到的文档列表，每个文档包含 id/content/score/metadata"""

    retrieval_scores: list[float]
    """检索分数列表"""

    # ===== 生成结果 =====
    thinking: str
    """思考过程（reasoning）"""

    answer: str
    """最终答案"""

    # ===== 对话历史 =====
    messages: Annotated[list[BaseMessage], add_messages]
    """对话历史（LangGraph 自动管理，支持增量添加）

    使用 add_messages reducer：
    - 自动合并新消息
    - 去重（根据 message.id）
    - 保持顺序
    """
