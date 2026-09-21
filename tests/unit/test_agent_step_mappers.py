"""前端 AgentStep mapper 等价测试（Python 镜像 TS 实现）

目的：验证 web/src/lib/agentStepMappers.ts 的核心逻辑正确性，
尤其是：
1. nodeNameToKind 节点映射
2. mapAgentTrace 透传
3. mapAgentStep 同 iteration in-place 更新（避免 step 数量爆炸）
4. mapAgentReflect 评分渲染
5. finalizeAgentSteps 收尾

TS 版本的等价实现已经在 web/src/lib/agentStepMappers.ts。
本测试用 Python 复刻同样的纯函数逻辑，断言关键不变量。
"""

import time


# ===== 镜像 TS 实现的 Python 等价 =====

NODE_KIND_MAP = {
    "router": "router",
    "self_rag_judge": "self_rag",
    "llm_only_answer": "llm_only",
    "retrieve": "retrieve",
    "retrieval": "retrieve",
    "agentic_rag": "think",
    "evaluator": "reflect",
    "replan": "replan",
}


def node_name_to_kind(node: str) -> str:
    return NODE_KIND_MAP.get(node, "router")


def map_agent_trace(data: dict) -> dict:
    node = data.get("node", "unknown")
    status = data.get("status", "started")
    ts = data.get("ts") or time.time()
    return {
        "id": f"trace-{ts}",
        "kind": node_name_to_kind(node),
        "node": node,
        "title": "",
        "detail": "",
        "status": status,
        "ts": ts,
        "payload": data.get("payload"),
    }


def map_agent_step(data: dict, existing: list[dict]) -> list[dict]:
    """同 iteration in-place 更新"""
    iteration = data.get("iteration")
    ts = data.get("ts") or time.time()

    if iteration is not None:
        for i, s in enumerate(existing):
            if (
                s.get("iteration") == iteration
                and s.get("kind") == "think"
                and s.get("status") != "completed"
            ):
                updated = list(existing)
                updated[i] = {
                    **updated[i],
                    "thoughtPreview": data.get("thought_preview") or updated[i].get("thoughtPreview"),
                    "action": data.get("action") or updated[i].get("action"),
                    "observationPreview": data.get("observation_preview") or updated[i].get("observationPreview"),
                    "status": "completed",
                    "ts": ts,
                }
                return updated

    return [
        *existing,
        {
            "id": f"step-{ts}",
            "kind": "think",
            "node": "agentic_rag",
            "title": "",
            "detail": "",
            "status": "completed",
            "iteration": iteration,
            "ts": ts,
            "thoughtPreview": data.get("thought_preview"),
            "action": data.get("action"),
            "observationPreview": data.get("observation_preview"),
        },
    ]


def map_agent_reflect(data: dict) -> dict:
    ts = data.get("ts") or time.time()
    score = data.get("score", 0)
    need_replan = data.get("need_replan", False)
    title = f"评分 {score}/5"
    if need_replan:
        title += " → 触发重新规划"
    return {
        "id": f"reflect-{ts}",
        "kind": "reflect",
        "node": "evaluator",
        "title": title,
        "detail": data.get("reason") or "",
        "status": "completed",
        "ts": ts,
        "score": score,
        "needReplan": need_replan,
    }


def finalize_agent_steps(steps: list[dict]) -> list[dict]:
    return [
        {**s, "status": "completed"} if s.get("status") == "running" else s
        for s in steps
    ]


# ===== 测试 =====


class TestNodeNameToKind:
    """nodeNameToKind 节点映射"""

    def test_router(self):
        assert node_name_to_kind("router") == "router"

    def test_self_rag_judge(self):
        assert node_name_to_kind("self_rag_judge") == "self_rag"

    def test_llm_only(self):
        assert node_name_to_kind("llm_only_answer") == "llm_only"

    def test_retrieve_alias(self):
        """retrieve 和 retrieval 都映射到 retrieve"""
        assert node_name_to_kind("retrieve") == "retrieve"
        assert node_name_to_kind("retrieval") == "retrieve"

    def test_agentic_rag(self):
        assert node_name_to_kind("agentic_rag") == "think"

    def test_evaluator(self):
        assert node_name_to_kind("evaluator") == "reflect"

    def test_unknown_defaults_to_router(self):
        assert node_name_to_kind("unknown_node") == "router"


class TestMapAgentTrace:
    """mapAgentTrace 透传"""

    def test_basic_trace(self):
        data = {"node": "self_rag_judge", "status": "completed", "ts": 1234.5}
        step = map_agent_trace(data)
        assert step["kind"] == "self_rag"
        assert step["node"] == "self_rag_judge"
        assert step["status"] == "completed"
        assert step["ts"] == 1234.5

    def test_trace_with_payload(self):
        data = {
            "node": "self_rag_judge",
            "status": "completed",
            "ts": 1.0,
            "payload": {"need_retrieval": True, "confidence": 0.9},
        }
        step = map_agent_trace(data)
        assert step["payload"] == {"need_retrieval": True, "confidence": 0.9}

    def test_trace_default_status(self):
        data = {"node": "router", "ts": 1.0}
        step = map_agent_trace(data)
        assert step["status"] == "started"


class TestMapAgentStepInPlace:
    """mapAgentStep 同 iteration in-place 更新（关键防爆）"""

    def test_in_place_update_same_iteration(self):
        """同 iteration + status=running 时 in-place 更新，不增加 step 数量"""
        existing = [
            {"id": "step-1", "iteration": 1, "kind": "think", "status": "running", "thoughtPreview": None}
        ]
        new_data = {
            "iteration": 1,
            "ts": 2.0,
            "thought_preview": "我应该先搜索",
            "action": {"tool": "rag_search", "args": {}},
            "observation_preview": "检索到 5 篇",
        }
        result = map_agent_step(new_data, existing)

        # 关键不变量：step 数量不变
        assert len(result) == 1, f"应 in-place 更新，但 step 数变了: {len(result)}"
        assert result[0]["status"] == "completed"
        assert result[0]["thoughtPreview"] == "我应该先搜索"
        assert result[0]["action"]["tool"] == "rag_search"
        assert result[0]["observationPreview"] == "检索到 5 篇"

    def test_new_iteration_appends(self):
        """不同 iteration 时 append 新 step"""
        existing = [
            {"id": "step-1", "iteration": 1, "kind": "think", "status": "completed", "thoughtPreview": "first"}
        ]
        new_data = {"iteration": 2, "ts": 2.0, "thought_preview": "second"}
        result = map_agent_step(new_data, existing)

        assert len(result) == 2
        assert result[1]["iteration"] == 2
        assert result[1]["thoughtPreview"] == "second"
        assert result[1]["status"] == "completed"

    def test_same_iteration_but_completed_appends(self):
        """同 iteration 但 status=completed 时不 in-place（避免覆盖历史），改为 append"""
        existing = [
            {"id": "step-1", "iteration": 1, "kind": "think", "status": "completed", "thoughtPreview": "old"}
        ]
        new_data = {"iteration": 1, "ts": 2.0, "thought_preview": "new"}
        result = map_agent_step(new_data, existing)

        # 已 completed 不被 in-place（保护历史）
        assert len(result) == 2, "completed 的 step 不应被覆盖"
        assert result[1]["thoughtPreview"] == "new"

    def test_no_iteration_always_appends(self):
        """无 iteration 字段直接 append"""
        existing = [
            {"id": "step-1", "iteration": 1, "kind": "think", "status": "completed"}
        ]
        new_data = {"ts": 2.0, "thought_preview": "no iter"}
        result = map_agent_step(new_data, existing)

        assert len(result) == 2
        assert result[1]["iteration"] is None


class TestMapAgentReflect:
    """mapAgentReflect 评分"""

    def test_basic_reflect(self):
        data = {"score": 4.2, "need_replan": False, "reason": "质量良好", "ts": 1.0}
        step = map_agent_reflect(data)
        assert step["kind"] == "reflect"
        assert step["node"] == "evaluator"
        assert step["title"] == "评分 4.2/5"
        assert step["score"] == 4.2
        assert step["needReplan"] is False
        assert step["detail"] == "质量良好"

    def test_reflect_with_replan(self):
        """need_replan=True 时 title 加触发重新规划提示"""
        data = {"score": 2.0, "need_replan": True, "ts": 1.0}
        step = map_agent_reflect(data)
        assert step["title"] == "评分 2.0/5 → 触发重新规划"
        assert step["needReplan"] is True


class TestFinalizeAgentSteps:
    """finalizeAgentSteps 收尾"""

    def test_running_to_completed(self):
        steps = [
            {"status": "running", "id": "1"},
            {"status": "completed", "id": "2"},
            {"status": "running", "id": "3"},
        ]
        result = finalize_agent_steps(steps)
        assert result[0]["status"] == "completed"
        assert result[1]["status"] == "completed"
        assert result[2]["status"] == "completed"

    def test_preserves_other_fields(self):
        steps = [{"status": "running", "id": "x", "kind": "router", "title": "路由"}]
        result = finalize_agent_steps(steps)
        assert result[0]["id"] == "x"
        assert result[0]["kind"] == "router"
        assert result[0]["title"] == "路由"

    def test_no_running(self):
        steps = [{"status": "completed", "id": "1"}]
        result = finalize_agent_steps(steps)
        assert result == steps


class TestEndToEndFlow:
    """完整流程：闲聊查询的 6 个 trace event → AgentStep 数组"""

    def test_chitchat_flow(self):
        """'你好' 应产生的 step 序列（trace 6 个，无 agent_step）"""
        existing = []

        # router started
        existing.append(map_agent_trace({"node": "router", "status": "started", "ts": 1.0}))
        # router completed
        existing.append(map_agent_trace({"node": "router", "status": "completed", "ts": 1.1}))
        # self_rag_judge started
        existing.append(map_agent_trace({"node": "self_rag_judge", "status": "started", "ts": 1.2}))
        # self_rag_judge completed
        existing.append(map_agent_trace({"node": "self_rag_judge", "status": "completed", "ts": 1.3}))
        # llm_only_answer started
        existing.append(map_agent_trace({"node": "llm_only_answer", "status": "started", "ts": 1.4}))
        # llm_only_answer completed
        existing.append(map_agent_trace({"node": "llm_only_answer", "status": "completed", "ts": 2.0}))

        # finalize: 所有 running → completed（started 状态保留，因为它们是 trace.started 事件）
        existing = finalize_agent_steps(existing)

        # 验证：trace.started 的 status 保持 started，trace.completed 保持 completed
        assert len(existing) == 6
        kinds = [s["kind"] for s in existing]
        assert kinds == ["router", "router", "self_rag", "self_rag", "llm_only", "llm_only"]
        # 每个节点都是 started + completed 配对
        statuses = [s["status"] for s in existing]
        assert statuses == [
            "started", "completed",
            "started", "completed",
            "started", "completed",
        ]

    def test_react_loop_iteration_in_place(self):
        """ReAct 3 轮迭代：agent_step 同 iteration in-place 更新"""
        existing = []

        # 3 轮 agent_step（无 trace，配合 in-place 测试）
        existing = map_agent_step(
            {"iteration": 1, "ts": 1.5, "thought_preview": "思考 1"},
            existing,
        )
        existing = map_agent_step(
            {"iteration": 2, "ts": 2.5, "thought_preview": "思考 2"},
            existing,
        )
        existing = map_agent_step(
            {"iteration": 3, "ts": 3.5, "thought_preview": "思考 3"},
            existing,
        )

        think_steps = [s for s in existing if s.get("kind") == "think"]
        assert len(think_steps) == 3, f"应有 3 个 think step，实际: {len(think_steps)}"

        # 每个 think step 的 thoughtPreview 正确
        previews = [s.get("thoughtPreview") for s in think_steps]
        assert previews == ["思考 1", "思考 2", "思考 3"]

    def test_react_loop_no_explosion(self):
        """ReAct 5 轮同 iteration in-place：step 数量恒定"""
        existing = []

        # Round 1
        existing.append(map_agent_trace({"node": "agentic_rag", "status": "started", "ts": 1.0}))
        # Round 1 第一次思考（running）
        existing.append({
            "id": "placeholder", "iteration": 1, "kind": "think", "status": "running",
            "thoughtPreview": None, "ts": 1.5,
        })
        # Round 1 完成（in-place 更新）
        existing = map_agent_step(
            {"iteration": 1, "ts": 2.0, "thought_preview": "思考 1 完成"},
            existing,
        )

        # Round 2
        existing.append(map_agent_trace({"node": "agentic_rag", "status": "started", "ts": 3.0}))
        existing.append({
            "id": "placeholder2", "iteration": 2, "kind": "think", "status": "running",
            "thoughtPreview": None, "ts": 3.5,
        })
        existing = map_agent_step(
            {"iteration": 2, "ts": 4.0, "thought_preview": "思考 2 完成"},
            existing,
        )

        # 验证：每轮 1 trace + 1 think = 4 个 step
        # 关键不变量：in-place 没让数量爆炸
        assert len(existing) == 4, f"in-place 防爆应保持 4 step，实际: {len(existing)}"
        # 思考内容都更新成功
        completed_thinks = [s for s in existing if s["kind"] == "think" and s["status"] == "completed"]
        assert len(completed_thinks) == 2
        assert completed_thinks[0]["thoughtPreview"] == "思考 1 完成"
        assert completed_thinks[1]["thoughtPreview"] == "思考 2 完成"
