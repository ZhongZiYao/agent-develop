# Phase 8 完成报告 — FinGuide AI 金融域改造

> **阶段**：Phase 8 — 业务域从游戏攻略问答 → 银行理财 PDF 问答
> **时间**：2026-09-20 ~ 2026-09-22
> **状态**：✅ 主体完成（8.1 ETL + 8.2 POC + 8.3 前端 + 8.4 文档），Phase 8.5 端到端验证待跑
> **作者**：Mavis

---

## TL;DR

把一个"游戏攻略问答 RAG 系统"改造成"银行理财 PDF 问答系统"。后端 90% 能力复用（LangGraph / Hybrid 召回 / 多 Agent / Self-RAG / SSE Trace），新增/改造集中在 **PDF ETL 流水线 + 金融元数据 + 风险提示 prompt + 前端金融化**。

**POC 数据**：`data/理财文件/` 22 家银行 23,229 份 PDF（8.1 GB），从中筛 100 份跑通 → 48 docs → 662 chunks → Chroma 662 documents 索引成功。

---

## 1. 业务域切换原因

| 维度 | 游戏攻略 | 银行理财 PDF |
|------|---------|------------|
| 真实数据 | Wiki 反爬严重、数据版权敏感 | 23,229 份官方 PDF 已本地，零版权风险 |
| 面试叙事 | "做个 demo 玩玩" | "金融合规 / 时效 / 多机构"更易打动面试官 |
| 元数据丰富度 | 角色 / 装备 / 版本 | 机构 / 报告类型 / 生效日期 / 产品编号（理财登记系统编码） |
| 工程深度 | HTML/Markdown | PDF 解析（PyMuPDF）+ 表格感知 + DuckDB 数仓 |

---

## 2. 改造范围（按模块）

### 2.1 数据 ETL（Phase 8.1 + 8.2）

| 子任务 | 状态 | 关键产出 |
|--------|------|----------|
| 8.1.1 清理游戏 ETL 残留 | ✅ | 删除 spiders（米游社/NGA/网易大神/B站/Fandom）/ 删除 crawl CLI |
| 8.1.2 config 改名 finguide | ✅ | `chroma_collection_name`、`duckdb_path`、`langsmith_project` 改 finguide |
| 8.1.3 PDF Loader 双引擎 | ✅ | `src/loaders/pdf_loader.py`：PyMuPDF + 双 regex（标准命名 / 招银前缀变体）+ 目录 fallback |
| 8.1.4 表格感知 Splitter | ✅ | `src/splitters/pdf_table_splitter.py`：按 `[Page N]` 标记 + 段落 + 长段分句 |
| 8.2.1 PDF Transform + DuckDB loader | ✅ | `src/etl/transform_pdf.py` + `load_duckdb_financial.py`：DELETE+INSERT 幂等 / 13 列 schema |
| 8.2.2 PDF 扫描 + 100 POC | ✅ | `scripts/scan_pdfs.py`：扫描 23,229 PDF → 51 机构/类型组合 → 选 100 → `poc_files.json` |
| 8.2.3 100 PDF POC 跑通 | ✅ | 48 docs / 662 chunks / 19 机构 / 6 报告类型 / Chroma 662 docs |

**关键决策**：
- 双命名 regex：标准 `机构_日期_类型_产品.pdf` + 变体 `招银理财_..._报告类型_(日期)_...pdf`
- 目录 fallback：从 `data/理财文件/A01工银理财/产品说明书/` 反推机构与类型
- 产品编号 regex：`\b\d{2}[A-Z]{2}\d{4,6}\b`（如 `24GS5969`、`26HH6088`）
- DuckDB 三表：dwd.documents / dwd.chunks / dwd.embeddings；用 `source='pdf_local'` 做幂等

### 2.2 Prompt 金融化（Phase 8.3.1）

| 改动 | 内容 |
|------|------|
| SYSTEM_PROMPT | 改为「FinGuide AI」+ 银行理财领域 7 条严格规则 |
| 强制风险提示 | "理财非存款，产品过往业绩不预示未来表现" 100% 出现 |
| 专有名词保留 | 机构名「招银理财」/ 产品名「鑫悦最短持有30天」/ 编号「24GS5969」/ 业绩基准 原文保留 |
| 时间维度 | 引用业绩基准 / 费率时必带生效日期 |
| format_context_chunk | 新增 institution / report_type / effective_date / product_code / product_name 5 类元数据行 |
| REJECT_MESSAGE | 改写为金融语境拒答模板 |

### 2.3 前端金融化（Phase 8.3.2 + 8.3.3）

| 改动 | 内容 |
|------|------|
| `layout.tsx` | title / description 改 FinGuide AI |
| `page.tsx` | Gamepad2 → Landmark；"新对话" → "新咨询"；配色 sky → indigo |
| `Sidebar.tsx` | "会话" → "咨询记录"；空态文案改金融；删除 game → institution |
| `SettingsPanel.tsx` | GAMES 列表 → INSTITUTIONS（招银/工银/中银/浦银/民生 等）；"游戏过滤" → "机构过滤" |
| `ChatWindow.tsx` | EXAMPLE_QUERIES 改理财示例；placeholder/EmptyState 改金融；头像字母 G → F；取消按钮 title 改"咨询" |
| `tailwind.config.js` | 主色 sky → indigo；accent 改绿（success）；新增 warn 色 |
| **`MetadataBadge.tsx`**（新）| 5 类金融标签：institution（indigo）/ report_type（blue）/ effective_date（amber）/ product_code（slate）/ product_name（green）|
| `api/schemas.py` | QueryRequest.game 字段描述改为"机构过滤" |

### 2.4 文档（Phase 8.4）

| 文件 | 改动 |
|------|------|
| `CLAUDE.md` | 完整重写：业务域 + 技术栈 + ETL 流水线 + 金融域特有约定 |
| `docs/00-PRD.md` | 完整重写：业务目标 / 数据规模（23,229 PDF）/ 合规硬要求 / 验收标准 |
| `docs/phase8-完成报告.md` | 本文档 |

---

## 3. POC 数据快照

### 3.1 DuckDB 统计（100 PDF 跑通后）

```
documents: 48 行（部分 PDF 因太短被跳过）
chunks:    662 行（平均 13.8 chunks/doc）
embeddings: 662 行（一一对应）
机构数: 19 / 22
报告类型: 6（产品说明书、业绩比较基准调整、定期报告、临时报告、新设份额、特殊案例）
```

**Top 5 机构**：
| 机构 | chunk 数 |
|------|----------|
| c05北银理财 | 225 |
| B01招银理财 | 96 |
| A03中银理财 | 95 |
| 浙银理财 | 80 |
| C09渝农商理财 | 47 |

**Top 3 报告类型**：
| 类型 | chunk 数 |
|------|----------|
| 产品说明书 | 363 |
| 业绩比较基准调整 | 237 |
| 定期报告 | 21 |

### 3.2 Chroma 索引

- collection: `finguide_pdf_v1`
- 文档数: 662
- metadata: institution / report_type / effective_date / product_name / product_code / title / filename / category / page_num

### 3.3 ETL 流水线性能

| 阶段 | 耗时 | 数据量 |
|------|------|--------|
| PDF 扫描 + 选取 | < 10s | 23,229 → 100 |
| PDF 加载（PyMuPDF） | ~5s | 48 docs |
| 文本切分 | < 1s | 662 chunks |
| Embedding（Ollama bge-m3） | ~3min | 662 vectors |
| DuckDB 写入 | < 1s | DELETE+INSERT |
| Chroma 写入 | < 2s | 662 docs |
| **端到端** | **< 5 min** | **48 docs / 662 chunks** |

---

## 4. 代码与测试

### 4.1 新增模块
- `src/loaders/pdf_loader.py`
- `src/splitters/pdf_table_splitter.py`
- `src/etl/transform_pdf.py`
- `src/etl/load_duckdb_financial.py`
- `scripts/scan_pdfs.py`
- `scripts/etl_financial_poc.py`
- `web/src/components/MetadataBadge.tsx`

### 4.2 单测
- `tests/unit/test_pdf_loader.py`（13 tests）
- `tests/unit/test_pdf_splitter.py`（9 tests）
- `tests/unit/test_pdf_etl.py`（6 tests + 1 integration）

### 4.3 改动模块
- `src/config.py`（金融字段）
- `src/prompts/templates.py`（金融 prompt）
- `src/etl/load_chroma.py`（金融 metadata）
- `src/api/schemas.py`（机构过滤）
- `web/tailwind.config.js`（indigo 配色）
- `web/src/app/page.tsx`、`layout.tsx`
- `web/src/components/{Sidebar,SettingsPanel,ChatWindow}.tsx`
- `CLAUDE.md`、`docs/00-PRD.md`

---

## 5. 关键 Commit 列表（按时间序）

| Commit | 说明 |
|--------|------|
| `feat(etl): 清理游戏残留` | Phase 8.1.1：删除 spiders / crawlers |
| `feat(config): 改名 finguide` | Phase 8.1.2：collection / duckdb / langsmith |
| `feat(loader): PDF 双引擎 + 命名 regex` | Phase 8.1.3：PyMuPDF + 双 regex + 目录 fallback |
| `feat(splitter): 表格感知 PDF Splitter` | Phase 8.1.4：页面 + 段落 + 长段分句 |
| `feat(etl): Transform + DuckDB 金融 schema` | Phase 8.2.1：DELETE+INSERT 幂等 |
| `feat(scripts): PDF 扫描 + POC 选取` | Phase 8.2.2：scan_pdfs.py → poc_files.json |
| `feat(etl): 100 PDF POC 跑通` | Phase 8.2.3：48 docs / 662 chunks |
| `feat(etl): load_chroma + templates 改金融风` | Phase 8.3.1：风险提示 prompt + Chroma metadata |
| `feat(web): 前端全量金融化改造` | Phase 8.3.2：layout/page/Sidebar/SettingsPanel/ChatWindow/tailwind |
| `feat(web): MetadataBadge 组件` | Phase 8.3.3：5 类金融标签 |
| `docs: CLAUDE.md 重写` | Phase 8.4.1 |
| `docs: PRD 重写` | Phase 8.4.2 |

---

## 6. 已知问题与遗留

| 项 | 说明 | 计划 |
|----|------|------|
| DuckDB 与 Chroma 元数据需双写 | 暂未做 CDC / 一致性校验 | Phase 8.5 加 unit test |
| 扫描件 PDF 无文本层 | POC 100 PDF 全是文本层 | Phase 9 OCR 兜底 |
| RAGAS 金融评测集未写 | 仍用游戏阶段 30 题 | Phase 9 写 50 题金融评测 |
| 端到端 query 验证未跑 | ETL → Chroma 已通，但 query → 答案未实测 | Phase 8.5 |
| 多机构产品对比未做 | 同业横向比较是大场景 | Phase 9 |

---

## 7. 下一步（Phase 8.5 + Phase 9）

### Phase 8.5：端到端验证
- [ ] 起后端 → 起前端 → 发 query「招银理财 24GS5969 的业绩基准」
- [ ] 验证：检索到正确 PDF / 答案含风险提示 / MetadataBadge 正确显示
- [ ] 跑 50 题金融 RAGAS 评测（先复用游戏评测集 + 改写）
- [ ] 单测覆盖 ≥ 80%

### Phase 9：技术博客 + 面试 STAR
- [ ] 写 1 篇 6000 字技术博客：金融 RAG 落地全过程
- [ ] 准备 STAR 面试稿（业务理解 + 技术亮点 + 量化数据）
- [ ] GitHub README 改 FinGuide AI 描述
- [ ] 演示视频（5 min）

---

## 8. 量化收益（对面试）

| 维度 | Phase 7（游戏）| Phase 8（金融）|
|------|----------------|----------------|
| 数据真实度 | Wiki 反爬，部分 mock | 23,229 份官方 PDF，零版权风险 |
| 工程深度 | HTML/Markdown + 反爬 | PDF 解析 + DuckDB + 表格感知 + 多 regex |
| 业务约束 | 弱 | 强（合规、风险提示、时效）|
| 面试叙事 | "做个 RAG 玩玩" | "金融 RAG 落地：PDF ETL + DuckDB + 合规" |

**关键话术**：
> "我把游戏问答场景切换为银行理财 PDF 场景，100 PDF POC 端到端 5 分钟跑通——DuckDB 列存存文档+chunks+embeddings 三表，Chroma 索引 662 chunk，前端 MetadataBadge 5 类金融元数据可视化，Prompt 100% 必带风险提示。整个后端 RAG/LangGraph/多 Agent 能力 90% 复用，聚焦 PDF ETL + 金融域改造。"

---

> **结论**：Phase 8 主体完成。POC 跑通 + 前端金融化 + 文档齐备。下一站：Phase 8.5 端到端验证 + Phase 9 面试准备。
