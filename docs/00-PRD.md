# GameGuide AI — 产品需求文档（PRD）

> 项目代号：`gameguide-ai`
> 版本：v0.1 (2026-09)
> 作者：Mavis（基于用户学习需求 + 网易互娱 AI Agent 岗面试要求）
> 项目目标：从 0 构建一个生产级 RAG 系统，作为 Agent 开发学习路径的核心载体

---

## 1. 项目背景与目标

### 1.1 背景
学习者正在准备网易互娱 AI Agent 实习面试，面经中 RAG、LangGraph、Agent Eval 是核心考点。
当前缺乏一个**端到端可演示、可量化、有面试叙事**的实战项目。

### 1.2 目标
**业务目标**：为游戏玩家提供一个基于官方资料库的智能攻略问答系统。

**学习目标**（按优先级）：
1. 跑通 RAG 全链路（Naive → Advanced → Modular → Agentic）
2. 掌握 LangGraph 多 Agent 编排
3. 接入 RAGAS 做端到端评测
4. 沉淀 Memory / Skill / MCP / Harness 设计经验
5. 输出可面试的作品集（GitHub + 技术博客）

### 1.3 非目标
- ❌ 不做完整商业产品（不要 UI 设计师、不要 SSR 优化）
- ❌ 不做实时联网（用离线语料）
- ❌ 不做付费 LLM API 兜底（用通义千问 + Claude 即可）

---

## 2. 业务场景定义

### 2.1 目标用户
- **核心用户**：游戏玩家（想了解装备、技能、活动、版本更新）
- **画像**：30 岁以下、玩网易系游戏、懒得看长篇攻略
- **使用场景**：
  - "新出的 XX 装备怎么获得？"
  - "XX 角色的连招怎么打？"
  - "上周更新改了什么？"
  - "XX 副本怎么打？"

### 2.2 核心场景示例（来自真实玩家问题）

| ID | 用户 Query | 期望答案 |
|----|-----------|---------|
| Q1 | "永劫无间妖刀姬 S13 怎么连招？" | 视频教程链接 + 文字步骤 |
| Q2 | "E-4048 错误码怎么解决？" | 错误码定义 + 解决方案（**测向量召回失败**） |
| Q3 | "上周更新的内容有哪些？" | 公告摘要（**测多跳推理**） |
| Q4 | "A 装备 vs B 装备哪个好？" | 装备对比表（**测多文档聚合**） |

### 2.3 数据来源
- **主数据源**：游戏官方 Wiki（如「永劫无间 Wiki」）、官方公告
- **数据规模**（MVP）：100-500 篇 Markdown/HTML 文档
- **数据更新频率**：手动 / 半自动（每周）

---

## 3. 功能需求

### 3.1 P0 功能（Phase 1-2 必须有）

| ID | 功能 | 说明 | 验收 |
|----|------|------|------|
| F1 | 文档加载 | 支持 Markdown / PDF / HTML | 加载 100 篇无报错 |
| F2 | 文本切分 | 语义切分 + 标题感知 | chunk_size 500-800 |
| F3 | 向量化 | BGE-M3 中文 | 1000 docs < 5min |
| F4 | 召回 | BM25 + 向量混合 (RRF) | Recall@10 > 0.8 |
| F5 | 重排 | bge-reranker-large | Precision@5 > 0.7 |
| F6 | 生成 | Qwen-Long + Prompt 模板 | Faithfulness > 0.9 |
| F7 | API 服务 | FastAPI + SSE 流式 | 端到端 < 5s |
| F8 | 评估 | RAGAS 评测 | 50 测试集 |

### 3.2 P1 功能（Phase 3-4）

| ID | 功能 | 说明 |
|----|------|------|
| F9 | Query 改写 | LLM 改写 + HyDE |
| F10 | Contextual Retrieval | Anthropic 方案 |
| F11 | Modular 化 | 每步可插拔 |
| F12 | 多 Agent | Planner / Researcher / Writer / Critic |

### 3.3 P2 功能（Phase 5+，面试加分项）

| ID | 功能 | 对应面经考点 |
|----|------|-------------|
| F13 | Memory | 用户偏好（"我喜欢用妖刀姬"）|
| F14 | MCP Server | 游戏内 API 接入 |
| F15 | Harness | 完整可观测性 |
| F16 | Multi-Agent | Planner/Worker/Critic 模式 |
| F17 | Eval Dashboard | 评测可视化 |

---

## 4. 非功能需求

### 4.1 性能
- 端到端查询延迟 < 5s（P95）
- 单文档处理 < 100ms
- 支持并发 10 QPS

### 4.2 质量
- Faithfulness（答案忠实于检索内容）> 0.9
- Context Recall > 0.8
- Answer Relevance > 0.85

### 4.3 可观测
- LangSmith 接入
- 每次 query 都有 trace

### 4.4 可复现
- 所有 prompt、配置、模型版本入 Git
- 测试集版本化

---

## 5. 技术栈

| 层级 | 选型 | 理由 |
|------|------|------|
| LLM | 通义千问 Qwen-Long | 中文强 + 长 context + 便宜 |
| Embedding | BGE-M3 (智源) | 中文 SOTA + 多语种 |
| Reranker | bge-reranker-large | 中文开源 |
| Vector Store | Chroma | 本地零成本 |
| BM25 | rank_bm25 | Python 原生 |
| 框架 | LangChain + LangGraph | 面试核心考点 |
| 后端 | FastAPI + SSE | 流式体验 |
| 前端 | Streamlit | 快速演示 |
| 评测 | RAGAS | 业界标准 |
| 追踪 | LangSmith | 官方 trace |
| 部署 | Docker | 可移植 |

---

## 6. 项目结构

```
gameguide-ai/
├── docs/                          # 文档
│   ├── 00-PRD.md                  # 本文档
│   ├── 01-架构设计.md
│   ├── 02-学习路线.md
│   └── 03-API 设计.md
├── data/
│   ├── raw/                       # 原始文档（Wiki/公告）
│   ├── processed/                 # 处理后 chunks
│   └── eval/                      # 测试集
├── src/
│   ├── loaders/                   # 文档加载器
│   ├── splitters/                 # 文本切分
│   ├── embeddings/                # 向量化封装
│   ├── vectorstore/               # 向量库封装
│   ├── retrievers/                # 召回策略
│   ├── rerankers/                 # 重排
│   ├── prompts/                   # Prompt 模板
│   ├── agents/                    # LangGraph Agent
│   ├── api/                       # FastAPI
│   └── ui/                        # Streamlit
├── tests/
│   ├── unit/                      # 单元测试
│   └── integration/               # 集成测试
├── eval/
│   ├── ragas_eval.py              # 评测脚本
│   └── datasets/                  # 评测数据集
├── notebooks/                     # 实验性代码
├── configs/                       # 配置文件
├── scripts/                       # 数据处理脚本
├── docker/
├── requirements.txt
├── README.md
└── CLAUDE.md                      # Claude Code 项目记忆
```

---

## 7. 学习路径（10 周渐进式）

| Phase | 周次 | 产出 | 面试可讲的点 |
|-------|------|------|-------------|
| **P0 准备** | W1 | PRD + 架构设计 + 数据准备 | "我有完整 PRD 思维" |
| **P1 Naive RAG** | W2-3 | MVP + Streamlit 演示 | "手写过 embed/retrieval/generate" |
| **P2 Advanced RAG** | W4-5 | Hybrid + Rerank + Eval | "49% 失败率下降的优化" |
| **P3 Modular** | W6 | 每步可插拔 | "我有 Modular 思维" |
| **P4 Agentic** | W7-8 | LangGraph 多 Agent | "LangGraph Supervisor" |
| **P5 加分项** | W9 | Memory/MCP/Harness 任选 2 | "我懂完整 Agent 栈" |
| **P6 输出** | W10 | 技术博客 + 面试 STAR | "有公开技术输出" |

---

## 8. 风险与依赖

### 8.1 风险
| 风险 | 概率 | 应对 |
|------|------|------|
| BGE-M3 太大，本地跑不动 | 中 | 远程 API（智源开放平台）|
| Qwen-Long 调用限速 | 低 | 申请更高的 quota |
| 数据爬取被反爬 | 中 | 用公开 Wiki API / 离线 dump |
| 学习时间不足 | 中 | 压缩为 6 周版 |

### 8.2 依赖
- Python 3.11+
- 至少 8GB RAM（跑 BGE-M3）
- LLM API Key（Qwen / Claude / OpenAI 任一）
- LangSmith 账号（可选）

---

## 9. 验收标准（Phase 1 MVP）

- [ ] 加载 100 篇游戏攻略文档无报错
- [ ] 端到端 demo 跑通：query → 答案（带引用）
- [ ] 5 个示例 query 答案正确率 > 80%
- [ ] Streamlit 简单 UI 可演示
- [ ] GitHub 仓库公开 + 完整 README

---

## 10. 未来扩展

- 接入更多网易游戏（永劫无间 / 逆水寒 / 第五人格）
- 用户画像（玩家偏好角色）
- 实时联网（官方公告 RSS）
- 多模态（视频攻略 / 截图识别）
- A/B 测试框架

---

> **下一步**：本 PRD 经你确认后，进入 Phase 0 收尾工作：
> 1. 写架构设计文档
> 2. 准备 50-100 篇测试语料
> 3. 创建项目目录 + Git 初始化
> 4. 写 CLAUDE.md（让 Claude Code 理解这个项目）
> 5. Phase 1 第一周任务清单