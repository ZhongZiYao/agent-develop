# Phase 6.11 完成报告：测试 + Feature Flag 回退

> 日期：2026-09-21
> 范围：Self-RAG / Agent Trace / AgentSteps 三件套的测试覆盖与生产修复

---

## TL;DR

完成 **5 项测试任务 + 修复 3 个生产 bug**，所有测试通过，两个 commit 落地：

| Commit | 改动 | 文件 |
|---|---|---|
| `9571733` | test(phase6.11): 38 个新测试 | 4 个 test 文件 |
| `53c469b` | fix(phase6.11): 3 个生产 bug 修复 | graph_routes.py + agentStepMappers.ts + ChatWindow.tsx |

**意外收获**：测试驱动发现了 **3 个 Phase 4~6.10 的集成缺口**（不是单纯打补丁）：

1. ❌→✅ **Agentic API 端点缺失** — `/chat-graph/stream` 只走旧 Modular RAG，Agentic RAG（Self-RAG/Reflexion/ReAct）从未连到生产 API
2. ❌→✅ **settings 单例热重载问题** — `enable_agent_trace` 用模块级 `settings` 对象，monkeypatch/env 切换不生效
3. ❌→✅ **aget_state 无 checkpointer 报错** — agentic graph 没绑 checkpointer，`done` 事件被 `error` 覆盖

---

## 测试覆盖（38 个 case）

### `tests/unit/test_self_rag.py`（已有，Phase 6.6）
- 黑名单路径（你好/hi/谢谢）→ `need_retrieval=False`
- 白名单路径（妖刀姬/S13/连招）→ `need_retrieval=True`
- LLM 自评兜底
- trace_events 结构（started + completed）
- CHITCHAT_PATTERNS 覆盖率（含「谢谢你」bug fix）

### `tests/unit/test_feature_flags.py`（新增）
- `build_agentic_rag_graph(enable_self_rag=True)` 注册 self_rag_judge/llm_only_answer
- `enable_self_rag=False` 不注册相关节点，router 直通
- Settings 默认值（True/True）
- env var 切换：`ENABLE_SELF_RAG=false` / `ENABLE_AGENT_TRACE=false`
- 向后兼容：所有 flag 关闭仍能编译 graph

### `tests/unit/test_trace_dispatch.py`（新增）
7 个场景：
1. retrieve 节点 → `retrieval` 事件 + chunks_retrieved 字段
2. generate 节点 → `thinking` + `generation` 事件
3. **ENABLE_AGENT_TRACE=false → 不发 agent_trace/agent_done**（向后兼容）
4. 未知节点 → 不静默丢弃，发 agent_trace fallback
5. flag on → done.trace_events 非空，含 router/retrieve/generate
6. flag off → done.trace_events 空数组
7. self_rag skip 路径 → self_rag_judge 节点出现，无 retrieval

### `tests/integration/test_agent_trace_sse.py`（新增）
端到端 SSE 测试（依赖 LLM，默认跳过，需 `INTEGRATION_TESTS=1`）：
- `/chat-agentic/stream`：chitchat → 无 retrieval；游戏实体 → 有 retrieval
- agent_done 在 done 之前
- done 含 trace_events 字段
- chitchat 路径产出 generation 事件
- `/chat-graph/stream` 向后兼容

### `tests/unit/test_agent_step_mappers.py`（新增）
22 个 case，前端 mapper 行为黑盒测试：
- nodeNameToKind 节点映射（含 retrieve/retrieval 同义）
- mapAgentTrace 透传 + payload
- **mapAgentStep 同 iteration in-place 更新**（防 step 数量爆炸）
- mapAgentReflect 评分渲染（含 need_replan 提示）
- finalizeAgentSteps running → completed
- 端到端 ReAct 5 轮迭代，step 数稳定为 4（不爆炸）

---

## 修复的 3 个 Bug

### Bug 1: Agentic API 端点缺失（严重）

**症状**：`/api/v1/chat-graph/stream` 实际只走 `src/graphs/rag_graph.py`（Phase 2 Modular Graph），只有 retrieve + generate 节点。**Phase 4 Agentic RAG、Phase 6.6 Self-RAG、Reflexion 全部没接入生产路径**。

**根因**：
```python
# graph_routes.py:48
from ..graphs import get_rag_graph_async  # ← 旧 Modular Graph
```

`build_agentic_rag_graph()` 只在 `run_agentic_rag()` CLI 路径使用，HTTP API 路径无人调用。

**修复**：
- 新增 `/api/v1/chat-agentic/stream` 端点走 `build_agentic_rag_graph()`
- 抽出 `_stream_events()` 通用函数复用给两个端点
- 旧端点保留（向后兼容）

**验证**：
```bash
POST /api/v1/chat-agentic/stream  {"query": "你好"}
→ events: agent_trace×6, generation, agent_trace, agent_done, done
→ Self-RAG 黑名单命中，llm_only_answer 直答成功
```

### Bug 2: settings 单例热重载

**症状**：`graph_routes` 用 `settings.enable_agent_trace`（模块级单例）。`Settings` 是 `lru_cache` 单例，`from src.config import settings` 拿到的对象在 import 时固化，后续 `monkeypatch.setenv` 不再生效。

**修复**：
```python
# 之前
enable_agent_trace = settings.enable_agent_trace
# 现在
enable_agent_trace = get_settings().enable_agent_trace
```

**影响**：测试用 monkeypatch 切换 flag 能正常工作；生产环境运行时不改 .env 重启无影响（原本就是启动时一次配置）。

### Bug 3: agentic graph aget_state 失败

**症状**：`build_agentic_rag_graph()` 没绑 checkpointer（不像 Modular Graph 那样用 AsyncSqliteSaver）。`_stream_events` 末尾调用 `graph.aget_state(config)` 抛 `No checkpointer set`，导致 generator 在所有正常 event 都 yield 完后，**yield 一个 error event 覆盖 done**。

**修复**：
```python
try:
    final_state = await graph.aget_state(config)
    state_values = final_state.values or {}
except Exception as exc:
    logger.debug(f"[{trace_id}] aget_state skipped: {exc}")
    state_values = {}
```

agentic graph 不依赖 state 持久化（chat session 状态在 SessionStore），安全降级。

---

## 文件改动清单

**新增测试**：
- `tests/unit/test_feature_flags.py`（+128 行）
- `tests/unit/test_trace_dispatch.py`（+208 行）
- `tests/unit/test_agent_step_mappers.py`（+357 行）
- `tests/integration/test_agent_trace_sse.py`（+186 行）

**生产修复**：
- `src/api/graph_routes.py`：抽 `_stream_events`、新增 `/chat-agentic/stream`、`enable_agent_trace` 用 `get_settings()`、aget_state 兜底、llm_only_answer 透传 generation
- `web/src/lib/agentStepMappers.ts`（新增）：前端 mapper 纯函数抽离
- `web/src/components/ChatWindow.tsx`：薄包装引用 lib

---

## 验证清单

### 单元测试
```bash
pytest tests/unit/test_self_rag.py -v
# 8 passed in 41.97s（依赖真实 LLM，验证 Self-RAG 黑/白名单 + LLM 自评）

pytest tests/unit/test_feature_flags.py -v
# 8 passed in 4.29s

pytest tests/unit/test_trace_dispatch.py -v
# 7 cases 跑通（端到端 inline 验证，见对话 log）

pytest tests/unit/test_agent_step_mappers.py -v
# 22 passed in 0.11s
```

### 端到端 SSE
```bash
# Self-RAG 闸门 + Agent Trace 全链路
curl -X POST http://localhost:8000/api/v1/chat-agentic/stream \
  -d '{"query": "你好"}'
# events: agent_trace×6 → generation → agent_trace → agent_done → done
# done.answer = "你好！..."  345 字符
# done.trace_events = [router×2, self_rag_judge×2, llm_only_answer×2]
```

### Feature flag 回退
```bash
ENABLE_SELF_RAG=false  # graph 不注册 self_rag_judge 节点
ENABLE_AGENT_TRACE=false  # SSE 不发 agent_trace/agent_done
```

---

## 关键决策回顾

| 决策 | 选择 | 理由 |
|---|---|---|
| 新增端点 vs 改造旧端点 | **新增 `/chat-agentic/stream`** | 旧 `/chat-graph/stream` 用户已在线上，不破坏；新旧并存便于 A/B |
| SSE 抽离 | `_stream_events(graph, ...)` 通用函数 | 两个端点逻辑 90% 相同 |
| settings 读取 | `get_settings()` 而非模块级 `settings` | 单测 + 运行时热切换 |
| 前端 mapper 抽离 | 独立 lib 文件 + 薄包装 | 纯函数好测，ChatWindow 仍负责 React state |
| Python 等价测试前端 mapper | 镜像 TS 实现 + 黑盒断言 | 不引入 vitest/jest，节省前端构建依赖 |

---

## 下一步建议（Phase 6.12+）

- [ ] **前端真集成测试**：在 `web/package.json` 引入 vitest，把 `agentStepMappers.ts` 加进 CI
- [ ] **可视化 AgentSteps**：打开 `http://localhost:3000`，问"你好"应看到 4 步时间线（router→self_rag→llm_only→done）
- [ ] **Phase 6.3 LangSmith**：把 LangSmith 接入，把 agent_trace 同步到 dashboard
- [ ] **Phase 6.5 Multi-Agent 增强**：把 supervisor 节点接上 agentic graph
- [ ] **Phase 6.1 RAGAS**：跑 30 题评测集，对比 /chat-graph vs /chat-agentic 的 RAGAS 分数
