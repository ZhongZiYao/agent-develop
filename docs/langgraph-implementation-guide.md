# LangGraph 集成实施指南

## 第一步：更新依赖（5 分钟）

### 1. 升级 LangGraph 相关包

```powershell
cd "E:\Program Files\vibe_coding\RAG_system"

# 升级核心依赖
pip install --upgrade langgraph langchain-core langchain-ollama aiosqlite

# 验证版本
python -c "import langgraph; print(f'langgraph: {langgraph.__version__}')"
python -c "import langchain_core; print(f'langchain-core: {langchain_core.__version__}')"
```

**期望输出**：
```
langgraph: 0.2.x
langchain-core: 0.3.x
```

---

## 第二步：运行 POC 验证（10 分钟）

### 1. 运行完整 POC

```powershell
python scripts/langgraph_poc.py
```

### 2. 预期输出

```
LangGraph POC 验证开始

============================================================
测试 1：基本执行（无 Checkpointer）
============================================================
[Retrieve] query=妖刀姬怎么连招？
[Generate] processing query=妖刀姬怎么连招？
[Generate] delta='这是'
[Generate] delta='一个'
[Generate] delta='测试'
[Generate] delta='答案'
[Generate] delta='：妖刀姬怎么连招？'

[Result] answer='这是一个测试答案：妖刀姬怎么连招？'
✅ 测试 1 通过

============================================================
测试 2：带 Checkpointer 执行
============================================================
[Retrieve] query=妖刀姬怎么连招？
[Generate] processing query=妖刀姬怎么连招？
...

[Round 1] answer='这是一个测试答案：妖刀姬怎么连招？'
[Round 1] messages count=2

[Retrieve] query=伤害是多少？
[Generate] processing query=伤害是多少？
...

[Round 2] answer='这是一个测试答案：伤害是多少？'
[Round 2] messages count=4
✅ 测试 2 通过：历史正确累积

============================================================
测试 3：多 Thread 隔离
============================================================
[Thread A] 最终消息数: 4
[Thread B] 最终消息数: 4
✅ 测试 3 通过：多 Thread 正确隔离

============================================================
测试 4：流式输出
============================================================
[Stream Mode: updates]
  Event: ['retrieve']
  Event: ['generate']
✅ 测试 4 通过：流式输出正常

============================================================
测试 5：Checkpoint 文件持久化
============================================================
[First Run] messages count=2
[Second Run] messages count=4
✅ 测试 5 通过：Checkpoint 文件持久化正常
   数据库文件：E:\Program Files\vibe_coding\RAG_system\data\test_checkpoint.db

============================================================
🎉 所有测试通过！LangGraph 可行性验证成功
============================================================

下一步：
  1. 实现真实的 RAG 节点
  2. 集成到 FastAPI
  3. 前端多会话状态管理
```

### 3. 常见问题排查

#### 问题 1：`ImportError: cannot import name 'AsyncSqliteSaver'`

**原因**：LangGraph 版本过低

**解决**：
```powershell
pip install --upgrade langgraph>=0.2.55
```

#### 问题 2：`ModuleNotFoundError: No module named 'aiosqlite'`

**原因**：缺少异步 SQLite 驱动

**解决**：
```powershell
pip install aiosqlite>=0.20.0
```

#### 问题 3：测试卡住不动

**原因**：异步事件循环问题

**解决**：
```powershell
# Windows 上使用 ProactorEventLoop
python scripts/langgraph_poc.py
```

如果仍卡住，检查是否有其他 Jupyter/IPython 进程占用事件循环。

---

## 第三步：检查当前架构（参考）

### 当前问题诊断

运行诊断脚本查看当前状态：

```powershell
python -c "
import sys
sys.path.insert(0, '.')

# 检查当前 LLM 配置
from src.config import settings
print(f'LLM Provider: {settings.llm_provider}')
print(f'LLM Model: {settings.llm_model}')
print(f'Use LangGraph: {getattr(settings, \"use_langgraph\", False)}')

# 检查 Session 数据
import sqlite3
conn = sqlite3.connect('data/gameguide.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM sessions')
print(f'Current Sessions: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM messages')
print(f'Current Messages: {cursor.fetchone()[0]}')
conn.close()
"
```

**期望输出**：
```
LLM Provider: ollama
LLM Model: qwen3:8b
Use LangGraph: False
Current Sessions: X
Current Messages: Y
```

---

## 第四步：下一步工作（明天开始）

### 任务清单

- [ ] **Task #47**: ✅ 架构设计文档（已完成）
- [ ] **Task #48**: ✅ POC 验证（当前）
- [ ] **Task #49**: 实现 RAG StateGraph 核心逻辑
- [ ] **Task #50**: API 层 Feature Flag 灰度切换
- [ ] **Task #51**: 前端多会话状态管理重构
- [ ] **Task #52**: 端到端集成测试与性能基准

### 预计时间线

| 任务 | 时间 | 状态 |
|------|------|------|
| 架构设计 + POC | 今天 | ✅ |
| 实现 RAG Graph | 明天上午 | 🔜 |
| API 集成 + Feature Flag | 明天下午 | 🔜 |
| 前端重构 | 后天 | 🔜 |
| 测试 + 优化 | 第 4 天 | 🔜 |

---

## 验收标准

POC 阶段通过标准：

- ✅ 5 个测试用例全部通过
- ✅ Checkpoint 文件正常生成
- ✅ 多会话状态正确隔离
- ✅ 流式输出符合预期
- ✅ 无依赖冲突或运行时错误

**POC 通过后，进入下一阶段：实现真实 RAG 节点。**

---

## 遇到问题？

### 调试技巧

1. **查看详细日志**：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查 Checkpoint 内容**：
   ```python
   import sqlite3
   conn = sqlite3.connect(':memory:')  # 或实际路径
   cursor = conn.cursor()
   cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
   print(cursor.fetchall())
   ```

3. **验证 LangGraph 安装**：
   ```powershell
   python -c "from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver; print('OK')"
   ```

### 回滚方案

如果 POC 失败，不影响现有功能：
```powershell
# 回滚依赖（可选）
git checkout requirements.txt
pip install -r requirements.txt

# 删除 POC 文件
rm scripts/langgraph_poc.py
rm docs/adr/001-langgraph-integration.md
```

---

## 参考文档

- [LangGraph Quick Start](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- [AsyncSqliteSaver 文档](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver)
- [ADR-001: LangGraph 集成架构](./docs/adr/001-langgraph-integration.md)
