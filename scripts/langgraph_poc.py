"""LangGraph POC：验证核心可行性

验证点：
1. AsyncSqliteSaver 能否正常工作
2. 流式输出是否符合预期
3. Checkpoint 恢复是否正确
4. 多会话隔离是否有效

运行：
    python scripts/langgraph_poc.py
"""

import asyncio
import sys
from pathlib import Path
from typing import TypedDict, Annotated

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


# ===== 1. 定义最小 State =====
class SimpleRAGState(TypedDict):
    """最简化的 RAG State"""
    query: str
    answer: str
    messages: Annotated[list, add_messages]


# ===== 2. 定义 Mock 节点 =====
async def mock_retrieve(state: SimpleRAGState) -> dict:
    """模拟检索节点"""
    print(f"[Retrieve] query={state['query']}")
    await asyncio.sleep(0.1)  # 模拟网络延迟
    return {}


async def mock_generate(state: SimpleRAGState) -> dict:
    """模拟生成节点（支持流式）"""
    print(f"[Generate] processing query={state['query']}")

    # 模拟流式生成
    answer_parts = [
        "这是",
        "一个",
        "测试",
        "答案",
        f"：{state['query']}",
    ]

    full_answer = ""
    for part in answer_parts:
        await asyncio.sleep(0.05)  # 模拟生成延迟
        full_answer += part
        print(f"[Generate] delta={part!r}")

    return {
        "answer": full_answer,
        "messages": [AIMessage(content=full_answer)],
    }


# ===== 3. 构建 Graph =====
def create_rag_graph():
    """创建最小 RAG Graph"""
    workflow = StateGraph(SimpleRAGState)

    workflow.add_node("retrieve", mock_retrieve)
    workflow.add_node("generate", mock_generate)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow


# ===== 4. 测试用例 =====
async def test_basic_execution():
    """测试 1：基本执行"""
    print("\n" + "="*60)
    print("测试 1：基本执行（无 Checkpointer）")
    print("="*60)

    workflow = create_rag_graph()
    app = workflow.compile()

    result = await app.ainvoke({
        "query": "妖刀姬怎么连招？",
        "answer": "",
        "messages": [HumanMessage(content="妖刀姬怎么连招？")],
    })

    print(f"\n[Result] answer={result['answer']!r}")
    assert result["answer"], "答案不能为空"
    print("✅ 测试 1 通过")


async def test_with_checkpointer():
    """测试 2：带 Checkpointer 的执行"""
    print("\n" + "="*60)
    print("测试 2：带 Checkpointer 执行")
    print("="*60)

    workflow = create_rag_graph()

    # 创建内存 Checkpointer
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        thread_id = "test-session-1"
        config = {"configurable": {"thread_id": thread_id}}

        # 第一轮对话
        result1 = await app.ainvoke({
            "query": "妖刀姬怎么连招？",
            "answer": "",
            "messages": [HumanMessage(content="妖刀姬怎么连招？")],
        }, config=config)

        print(f"\n[Round 1] answer={result1['answer']!r}")
        print(f"[Round 1] messages count={len(result1['messages'])}")

        # 第二轮对话（从 checkpoint 恢复）
        result2 = await app.ainvoke({
            "query": "伤害是多少？",
            "answer": "",
            "messages": [HumanMessage(content="伤害是多少？")],
        }, config=config)

        print(f"\n[Round 2] answer={result2['answer']!r}")
        print(f"[Round 2] messages count={len(result2['messages'])}")

        # 验证历史累积
        assert len(result2["messages"]) == 4, f"期望 4 条消息，实际 {len(result2['messages'])}"
        print("✅ 测试 2 通过：历史正确累积")


async def test_multi_thread_isolation():
    """测试 3：多 thread 隔离"""
    print("\n" + "="*60)
    print("测试 3：多 Thread 隔离")
    print("="*60)

    workflow = create_rag_graph()

    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        # 并行执行两个 thread
        async def run_session(thread_id: str, queries: list[str]):
            config = {"configurable": {"thread_id": thread_id}}
            results = []
            for query in queries:
                result = await app.ainvoke({
                    "query": query,
                    "answer": "",
                    "messages": [HumanMessage(content=query)],
                }, config=config)
                results.append(result)
            return results

        thread_a_results, thread_b_results = await asyncio.gather(
            run_session("session-a", ["妖刀姬连招？", "伤害多少？"]),
            run_session("session-b", ["红蝶技能？", "怎么玩？"]),
        )

        # 验证隔离
        assert len(thread_a_results[1]["messages"]) == 4, "Thread A 历史错误"
        assert len(thread_b_results[1]["messages"]) == 4, "Thread B 历史错误"

        # 验证 thread 之间不干扰
        assert "妖刀姬" in thread_a_results[0]["answer"]
        assert "红蝶" in thread_b_results[0]["answer"]

        print(f"[Thread A] 最终消息数: {len(thread_a_results[-1]['messages'])}")
        print(f"[Thread B] 最终消息数: {len(thread_b_results[-1]['messages'])}")
        print("✅ 测试 3 通过：多 Thread 正确隔离")


async def test_streaming():
    """测试 4：流式输出"""
    print("\n" + "="*60)
    print("测试 4：流式输出")
    print("="*60)

    workflow = create_rag_graph()

    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "test-stream"}}

        print("\n[Stream Mode: updates]")
        events = []
        async for event in app.astream(
            {
                "query": "流式测试",
                "answer": "",
                "messages": [HumanMessage(content="流式测试")],
            },
            config=config,
            stream_mode="updates",
        ):
            events.append(event)
            print(f"  Event: {list(event.keys())}")

        assert "retrieve" in str(events), "缺少 retrieve 事件"
        assert "generate" in str(events), "缺少 generate 事件"
        print("✅ 测试 4 通过：流式输出正常")


async def test_checkpoint_persistence():
    """测试 5：Checkpoint 文件持久化"""
    print("\n" + "="*60)
    print("测试 5：Checkpoint 文件持久化")
    print("="*60)

    db_path = Path(__file__).parent.parent / "data" / "test_checkpoint.db"
    db_path.parent.mkdir(exist_ok=True)

    # 清理旧文件
    if db_path.exists():
        db_path.unlink()

    # 使用绝对路径字符串
    db_uri = str(db_path.absolute())

    # 第一次运行：写入 checkpoint
    workflow = create_rag_graph()

    async with AsyncSqliteSaver.from_conn_string(db_uri) as checkpointer1:
        app1 = workflow.compile(checkpointer=checkpointer1)

        config = {"configurable": {"thread_id": "persistent-session"}}
        result1 = await app1.ainvoke({
            "query": "持久化测试",
            "answer": "",
            "messages": [HumanMessage(content="持久化测试")],
        }, config=config)

        print(f"[First Run] messages count={len(result1['messages'])}")

    # 模拟重启：创建新 app + checkpointer
    async with AsyncSqliteSaver.from_conn_string(db_uri) as checkpointer2:
        app2 = workflow.compile(checkpointer=checkpointer2)

        # 第二次运行：从文件恢复
        result2 = await app2.ainvoke({
            "query": "第二轮",
            "answer": "",
            "messages": [HumanMessage(content="第二轮")],
        }, config=config)

        print(f"[Second Run] messages count={len(result2['messages'])}")

        # 验证历史恢复
        assert len(result2["messages"]) == 4, "重启后历史未恢复"
        print(f"✅ 测试 5 通过：Checkpoint 文件持久化正常")
        print(f"   数据库文件：{db_path}")

    # 清理
    db_path.unlink()


# ===== 主入口 =====
async def main():
    print("LangGraph POC 验证开始\n")

    try:
        await test_basic_execution()
        await test_with_checkpointer()
        await test_multi_thread_isolation()
        await test_streaming()
        await test_checkpoint_persistence()

        print("\n" + "="*60)
        print("🎉 所有测试通过！LangGraph 可行性验证成功")
        print("="*60)
        print("\n下一步：")
        print("  1. 实现真实的 RAG 节点")
        print("  2. 集成到 FastAPI")
        print("  3. 前端多会话状态管理")

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
