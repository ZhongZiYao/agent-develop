# FinGuide AI — 产品需求文档（PRD）

> 项目代号：`finguide-ai`
> 版本：v0.2 (2026-09) — 金融域改造
> 作者：Mavis（基于用户学习需求 + AI Agent 实习面试要求）
> 项目目标：在已有的 RAG/LangGraph 工程能力基础上，**落地银行理财 PDF 问答场景**，演示真实数据 ETL → 检索 → 合规回答的全链路

---

## 1. 项目背景与目标

### 1.1 背景
学习者原本以"游戏攻略问答"作为 RAG 演示场景，但游戏领域数据质量参差、版权敏感，且对面试官的吸引有限。

2026 年 9 月起，场景切换为**银行理财产品智能问答**：
- **真实语料**：手头已有 23,229 份理财 PDF（8.1 GB），覆盖 22 家银行 / 理财子公司的产品说明书、临时公告、定期报告
- **强约束场景**：金融问答对**时效性、机构归属、产品编号、风险披露**有严格要求 → 更有展示价值
- **场景真实**：理财客户经理、监管机构、个人投资者 都会用 AI 查询"X 银行 Y 产品 业绩基准 多少"

后端 RAG / LangGraph / 多 Agent / Self-RAG / Trace 等能力在游戏阶段已成熟，金融域改造聚焦：
1. **真实 PDF 数据 ETL 流水线**
2. **金融元数据**（机构 / 报告类型 / 生效日期 / 产品编号）抽取与展示
3. **Prompt 风险提示与时效披露**
4. **前端 Metadata Badge**（一眼看出"哪家、什么类型、何时生效"）

### 1.2 目标

**业务目标**：为理财经理与个人投资者提供一个基于官方公告 PDF 的智能问答助手，支持产品对比、业绩基准查询、费率与公告解读。

**学习目标**（按优先级）：
1. 跑通 RAG 全链路（已具备）✅
2. 真实 PDF ETL：PyMuPDF 解析 + 表格感知切分 + DuckDB 数仓
3. 金融域 prompt 工程（合规、风险、专有名词保留）
4. 金融元数据可视化（前端 Metadata Badge）
5. 输出可面试的作品集（GitHub + 技术博客）

### 1.3 非目标
- ❌ 不做实时联网（用离线 PDF 语料）
- ❌ 不做真实交易（理财咨询，不涉及购买流程）
- ❌ 不做复杂合规校验（提示风险，但不替代法律审查）

---

## 2. 业务场景定义

### 2.1 目标用户
- **核心用户**：银行理财经理 / 个人投资者
- **画像**：30-45 岁、购买或代销理财产品的银行客户/经理、需要快速查阅某理财产品的业绩基准、费率、生效日期
- **使用场景**：
  - "招银理财 24GS5969 的业绩基准是多少？"
  - "工银理财最近发布了哪些新设份额公告？"
  - "中银理财 2024 年产品说明书里关于赎回的规定？"
  - "浦银理财的费率优惠活动有哪些？"

### 2.2 核心场景示例（来自真实用户问题）

| ID | 用户 Query | 期望答案 |
|----|-----------|---------|
| Q1 | "招银理财 24GS5969 当前业绩基准是多少？" | 业绩区间 + 生效日期 + 来源文件 |
| Q2 | "工银理财最近 30 天发了哪些临时公告？" | 公告列表 + 类型分布 |
| Q3 | "中银理财某产品的赎回规则" | 产品说明书原文片段 + 文档定位 |
| Q4 | "A 银行 vs B 银行同类产品对比" | 表格对比 + 风险提示 |
| Q5 | "理财登记系统编码 26HH6088 对应哪个产品？" | 产品名 + 机构 + 文档链接 |

### 2.3 数据来源

- **主数据源**：`data/理财文件/` 下 23,229 份 PDF，来自 22 家银行/理财子公司
- **数据规模**：8.1 GB（未压缩）；POC 选 100 份 ~ 6 MB
- **机构分布（部分）**：A01工银、A03中银、A05交银、B01招银、B03中信、B05浦银、B07民生、B09广银、C09渝农商、c03南银、c05北银、c07青银、浙银、上海农商、中原、光大、杭州联合 等
- **报告类型**：产品说明书 / 临时报告 / 定期报告；子类含"业绩比较基准调整 / 新设份额 / 费率调整及优惠 / 特殊案例"
- **更新频率**：手动（季度批量导入）

---

## 3. 功能需求

### 3.1 P0 功能（Phase 8 必须有）

| ID | 功能 | 说明 | 验收 |
|----|------|------|------|
| F1 | PDF 加载 | PyMuPDF + 表格感知 | 100 PDF 加载无报错 |
| F2 | 元数据抽取 | 文件名 + 目录 fallback | 机构/类型/日期/产品编号 ≥ 95% |
| F3 | 文本切分 | 页面 + 段落 + 长段分句 | chunk_size 500 / overlap 50 |
| F4 | 向量化 | Ollama bge-m3 | 1000 chunks < 3min |
| F5 | 召回 | 向量 + BM25 + Rerank | Recall@10 > 0.8 |
| F6 | DuckDB 数仓 | 文档 / chunks / embeddings 三表 | 100 PDF 端到端 < 5min |
| F7 | 生成 | Qwen-Long + 金融 prompt | 风险提示 100% 包含 |
| F8 | 前端 Metadata Badge | 5 类金融标签可视化 | 资料卡片显示机构/类型/日期/编号/产品 |

### 3.2 P1 功能（已具备，新增金融域适配）

| ID | 功能 | 说明 |
|----|------|------|
| F9 | Hybrid 召回 (RRF) | 沿用游戏阶段 |
| F10 | LangGraph Agent | Router + ReAct + Reflexion |
| F11 | Multi-Agent Supervisor | Planner / Worker / Critic |
| F12 | Self-RAG 闸门 | 黑白名单 + LLM 自评 |
| F13 | SSE Trace 推送 | 前端 AgentSteps 时间线 |

### 3.3 P2 功能（Phase 8.5+，面试加分项）

| ID | 功能 | 对应面经考点 |
|----|------|-------------|
| F14 | 业绩基准时序对比 | DuckDB 时序查询 |
| F15 | 同类机构产品对比 | 多文档聚合 |
| F16 | DuckDB 数仓 BI | SQL 评测指标 |
| F17 | RAGAS 金融评测集 | 50 测试题 |

---

## 4. 非功能需求

### 4.1 性能
- 100 PDF POC 端到端（PDF → chunks → embeddings → Chroma）< 5 分钟
- 单次查询 P95 延迟 < 8s（含 LLM 流式生成）
- 支持并发 5 QPS

### 4.2 质量
- Faithfulness（答案忠实于 PDF） > 0.92
- Context Recall > 0.85
- Answer Relevance > 0.88
- 风险提示覆盖率 100%（合规硬要求）

### 4.3 合规
- 风险提示（"理财非存款..."）每条回答必含
- 专有名词原文保留（机构、产品、编号、业绩基准）
- 业绩基准附带生效日期

### 4.4 可观测
- LangSmith 接入
- 每次 query 都有 SSE Trace
- DuckDB 存全量审计（文档 / chunks / embeddings）

---

## 5. 技术栈

| 层级 | 选型 | 理由 |
|------|------|------|
| LLM | Ollama 本地 qwen3:8b / minimax 云端 | 沿用 |
| Embedding | Ollama bge-m3（1024 维） | 中文 SOTA |
| Reranker | bge-reranker-large | 中文开源 |
| Vector Store | Chroma PersistentClient | 本地零成本 |
| **数仓** | **DuckDB** | 列存，文档/分块/向量元数据 |
| **PDF 解析** | **PyMuPDF (fitz)** | 快、表格友好 |
| BM25 | rank_bm25 | 沿用 |
| 框架 | LangChain + LangGraph | 沿用 |
| 后端 | FastAPI + SSE | 沿用 |
| 前端 | Next.js 14 + Tailwind（indigo 配色） | 沿用 + 金融稳重色调 |
| 评测 | RAGAS | 沿用 |
| 追踪 | LangSmith | 沿用 |
| 部署 | Docker | 沿用 |

---

## 6. 项目结构

```
finguide-ai/
├── docs/                          # 文档
│   ├── 00-PRD.md                  # 本文档
│   ├── 01-架构设计.md
│   ├── 02-学习路线.md
│   ├── 03-API 设计.md
│   └── phase-XX-*.md              # 各 Phase 报告
├── data/
│   ├── 理财文件/                    # 原始 PDF 语料（22 家，2万+）
│   ├── clean/                      # ETL 中间产物（gitignore）
│   ├── chroma/                     # 向量库（gitignore）
│   └── warehouse/                  # DuckDB（gitignore）
├── src/
│   ├── loaders/                    # 文档加载（pdf_loader 支持双引擎）
│   ├── splitters/                  # 文本切分（pdf_table_splitter）
│   ├── embeddings/                 # 向量化封装
│   ├── vectorstore/                # 向量库封装
│   ├── retrievers/                 # 召回（向量/BM25/Hybrid）
│   ├── rerankers/                  # 重排
│   ├── prompts/                    # Prompt 模板（金融域：风险提示）
│   ├── agents/                     # LangGraph Agent（Self-RAG / ReAct / Reflexion）
│   ├── graphs/                     # StateGraph
│   ├── etl/                        # ETL（transform_pdf / load_duckdb / load_chroma）
│   ├── api/                        # FastAPI
│   └── storage/                    # SQLite Session / Memory
├── scripts/                        # 数据处理（含 etl_financial_poc / scan_pdfs）
├── tests/                          # pytest 单测 + 集成
├── web/                            # Next.js 14 前端（含 MetadataBadge）
├── eval/                           # RAGAS 评测
├── notebooks/
├── configs/
├── requirements.txt
├── docker-compose.yml
└── CLAUDE.md                       # Claude Code 项目记忆
```

---

## 7. 学习路径（Phase 8 重点）

| Phase | 状态 | 产出 | 面试可讲的点 |
|-------|------|------|-------------|
| **P0–P6** | ✅ | 核心 RAG + Agent + Trace | "完整 RAG 演进 + LangGraph 多 Agent" |
| **P7** | ✅ | ETL 流水线（游戏） | "通用 ETL 架构设计" |
| **P8** | ⏳ | **金融域落地** | "真实 PDF 解析 / DuckDB 数仓 / 金融 prompt / 元数据可视化" |
| **P9** | ⏳ | 技术博客 + 面试 STAR | "业务+技术双叙事" |

---

## 8. 风险与依赖

### 8.1 风险
| 风险 | 概率 | 应对 |
|------|------|------|
| PDF 扫描件无文本层 | 中 | 用 OCR 兜底（pytesseract）— POC 暂不覆盖 |
| 理财文件命名不统一 | 中 | 双 regex + 目录 fallback |
| DuckDB 与 Chroma 元数据漂移 | 低 | 用 doc_id 主键 + DELETE+INSERT 幂等 |
| 风险提示被 LLM 漏掉 | 低 | prompt 硬约束 + 评测覆盖 |

### 8.2 依赖
- Python 3.11+
- 至少 8GB RAM（跑 bge-m3）
- Ollama 已部署（qwen3:8b + bge-m3）
- PyMuPDF / pdfplumber 任一
- DuckDB 0.10+

---

## 9. 验收标准（Phase 8 POC）

- [x] 100 PDF 端到端 POC 跑通（ETL → DuckDB → Chroma）
- [x] DuckDB 文档/分块/向量三表数据完整
- [x] Chroma 662 个 chunk 索引成功
- [x] 前端 Metadata Badge 显示 5 类金融元数据
- [x] Prompt 模板每条必含风险提示
- [ ] 端到端 demo：query → 答案（带引用 + 风险提示）— Phase 8.5
- [ ] 50 题 RAGAS 评测集 + Faithfulness > 0.92 — Phase 8.5/9

---

## 10. 未来扩展

- 接入 OCR 兜底（扫描件 PDF）
- DuckDB 时序查询（业绩基准历史走势）
- 多模态（PDF 中的图表 OCR + 解读）
- 接入监管公告 RSS 实时更新
- 个人理财画像（推荐偏好）

---

> **下一步**：进入 Phase 8.4 — 文档收尾（PRD/架构/完成报告）+ Phase 8.5 端到端验证
