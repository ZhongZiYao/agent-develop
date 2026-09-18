# RAG 召回与重排技术深度解析（2026.09）

> 主题：召回策略全景 + 重排技术全景 + 工程经验 + 常见坑 + 业界处理手段
> 适用：AI Agent / LLM 应用工程师面试、RAG 系统设计、生产优化

---

## 目录

1. [为什么需要召回 + 重排？](#1-为什么需要召回--重排)
2. [召回策略全景](#2-召回策略全景)
3. [重排策略全景](#3-重排策略全景)
4. [混合检索：BM25 + 向量](#4-混合检索bm25--向量)
5. [高级召回：Query 改写 / HyDE / Graph / Agentic](#5-高级召回query-改写--hyde--graph--agentic)
6. [工程经验与最佳实践](#6-工程经验与最佳实践)
7. [常见坑 + 业界处理手段](#7-常见坑--业界处理手段)
8. [选型决策表](#8-选型决策表)
9. [面试高频 QA](#9-面试高频-qa)
10. [业界 Benchmark 数据](#10-业界-benchmark-数据)

---

## 1. 为什么需要召回 + 重排？

### 1.1 单阶段检索的天花板

朴素 RAG（embed → top-K → generate）的核心问题：

```
"向量相似度" ≠ "语义相关性"
```

**经典反例**：
- 问「E-4048 错误码怎么修？」
  - 期望返回：错误码定义文档
  - 实际返回：E-4047、E-4049 文档（embedding 编码把它当成"通用错误码"）
- 问「Python 内存溢出处理」
  - 期望返回：Python 内存管理文档
  - 实际返回：Java 大文件处理、Python 基础语法（主题相似但答非所问）

### 1.2 两阶段范式

工业界共识：**"先粗筛、再精排"** —— 来自搜索引擎和推荐系统十几年沉淀。

```
全量文档库（百万级）
    ↓ 向量召回 / BM25（粗筛，追求 Recall）
候选集 Top-50
    ↓ Cross-Encoder Rerank（精排，追求 Precision）
Top-5
    ↓ LLM 生成
最终答案
```

**关键数据**（业界 benchmark 共识）：
- 加 Rerank 后 Recall@10 通常提升 **10-20%**
- 端到端答案质量提升 **8-13%**
- 延迟代价：**100-200ms**（Cross-Encoder）

### 1.3 Bi-Encoder vs Cross-Encoder 本质

| 维度 | Bi-Encoder | Cross-Encoder |
|------|-----------|---------------|
| 编码方式 | Query / Doc **独立**编码 | Query + Doc **一起**编码 |
| 注意力 | 各自内部 | 跨 token 全注意力交互 |
| 速度 | O(1) per doc（预计算）| O(n) per query |
| 精度 | 中（压缩损失）| 高（细粒度）|
| 适用 | 全库检索 | 候选集精排 |
| 代表 | BGE / OpenAI Embedding | BGE-Reranker / Cohere Rerank / MiniLM Cross-Encoder |

**为什么 Bi-Encoder 会丢精度？**
- 一篇 1000 字的文档被压成 768 维向量，所有语义信息塞进一个点
- 不可避免的信息损失：细粒度交互、词级别匹配、否定、双关全没了
- Cross-Encoder 让 Q 和 D 互相看到彼此每个 token，注意力机制做全交互

---

## 2. 召回策略全景

### 2.1 召回方法分类

```
召回
├── 稀疏召回（传统 IR）
│   ├── BM25
│   └── TF-IDF（已淘汰）
├── 稠密召回（向量检索）
│   ├── 单向量（Dense Embedding）
│   ├── 多向量 / Late Interaction（ColBERT）
│   └── 稀疏-稠密统一（BGE-M3 / SPLADE）
├── 混合召回
│   ├── BM25 + Dense → RRF / Weighted
│   └── Multi-Query / HyDE / Step-Back
├── 高级召回
│   ├── Query 改写 / Decomposition
│   ├── HyDE（假设性文档）
│   ├── GraphRAG（图谱）
│   ├── Self-RAG / CRAG（自反思）
│   └── Agentic RAG
└── 结构化召回
    ├── Metadata Filter
    ├── SQL / Tool Call
    └── Parent-Document Retriever
```

### 2.2 稀疏召回：BM25

**原理**：基于词频（TF）和逆文档频率（IDF）的经典 IR 算法。
```
BM25(q, d) = Σ IDF(qi) · (f·(k1+1)) / (f + k1·(1−b+b·dl/avgdl))
```
- k1（饱和参数）：常取 1.2-1.5
- b（长度归一化）：常取 0.75
- IDF = log((N - df + 0.5) / (df + 0.5) + 1)

**优势**：
- 精确匹配（型号、错误码、人名、专业术语）
- 无需训练，开箱即用
- 极快（倒排索引）

**劣势**：
- 不懂语义（同义词、上下文）
- 词形变化不友好（中文较英文好）

### 2.3 稠密召回：单向量 Embedding

**原理**：用预训练 Embedding 模型把文本映射到 N 维向量空间，按余弦相似度 / 内积召回。

**选型决策（2026 业界主流）**：

| 模型 | 维度 | MTEB | 优势 | 适用 |
|------|------|------|------|------|
| **OpenAI text-embedding-3-large** | 3072（可降到 256-3072）| 64.1 | 通用稳定 | 英文为主 |
| **BGE-M3** | 1024 | - | 多语言、稀疏-稠密统一 | 国际化、混合检索 |
| **BGE-large-zh-v1.5** | 1024 | - | 中文首选 | 中文场景 |
| **M3E** | 1024 | - | 中文轻量 | 中文中小规模 |
| **Jina-embeddings-v3** | 1024 | 65.2 | 性价比高 | 通用 |
| **Nomic-embed-text-v2** | 768 | 63.5 | 可本地 | 隐私场景 |
| **Cohere Embed v4** | 1024 | 66.0 | 多语种 | 商业 |

**关键工程要点**：
- **维度选择**：维度↑ → 容量↑ → 存储↑ → 检索↓。大库用 Matryoshka 降维
- **版本管理**：embedding 模型换版本 = 全量重灌，**绝对不能静默切换**
- **batch 化**：embedding API 调批（如 256/请求），吞吐量提升 10x
- **多语种**：混合语料优先 BGE-M3（支持 100+ 语种）

### 2.4 多向量召回：ColBERT / Late Interaction

**核心思想**：放弃单向量压缩，每个 token 保留独立向量，查询时再交互。

**MaxSim 打分**：
```
score(q, d) = Σᵢ maxⱼ cosine(qᵢ, dⱼ)
```
每个 query token 找文档里最匹配的 token，分数累加。

**优势**：
- 处理**多面查询**（一文档答 query 多个方面）
- 对**罕见词 / 专有名词**鲁棒（不会被平均稀释）
- 接近 cross-encoder 质量但可大规模检索

**代价**：
- 存储：**每个 token 一个向量**，比 dense 大 50-500 倍
- ColBERTv2 用 **residual compression** 缓解
- 查询时算 MaxSim，比 dense 慢

**业界位置**：
> "dense for first pass, ColBERT for token-level recall at scale, cross-encoder for final precision"

### 2.5 统一表示：BGE-M3 / SPLADE

**BGE-M3**：同时输出 **dense + sparse + multi-vector** 三种表示
- 一个模型，三种召回方式
- 适合：既要语义又要精确匹配、要多语种、要省存储

**SPLADE**：神经网络学到的稀疏表示
- 保持 BM25 的精确性 + 神经网络的语义扩展
- 仍可用倒排索引
- 适合：代码搜索、专名密集场景

---

## 3. 重排策略全景

### 3.1 重排方法分类

```
Rerank
├── Cross-Encoder（精排主流）
│   ├── 开源：BGE-Reranker / MiniLM Cross-Encoder / bce-reranker
│   └── 商业：Cohere Rerank / Jina Rerank / Voyage rerank
├── LLM-based Rerank
│   ├── Pointwise（逐 doc 打分）
│   ├── Pairwise（两两比较）
│   └── Listwise（RankGPT 滑动窗口）
├── 轻量特征融合
│   ├── BM25 分数 + 向量分数 + 时效性 + 权威性
│   └── Learning-to-Rank（LambdaMART / XGBoost）
└── 混合（Cross-Encoder + 业务规则）
```

### 3.2 Cross-Encoder 重排（最主流）

**原理**：Query + Doc 拼接成 `[CLS] query [SEP] doc [SEP]`，过一遍 Transformer，输出相关性分数（logit / sigmoid）。

**代表性模型**：

| 模型 | 参数量 | 多语种 | 速度 | 适用 |
|------|--------|--------|------|------|
| **BGE-reranker-v2-m3** | 568M | ✅ 中英日韩 | 中 | 通用首选（Apache 2.0）|
| **BGE-reranker-large** | 560M | 中英 | 中 | 中文场景强 |
| **bce-reranker（网易）** | - | 中文 | 中 | 纯中文最佳 |
| **Jina Reranker v2/v3** | - | 100+ | 中 | 长文本（8K）|
| **Cohere Rerank 3.5** | API | 100+ | 快（API）| 商业、稳定 |
| **ms-marco-MiniLM-L-6** | 22M | 英 | 快 | 轻量兜底 |
| **Voyage rerank-2.5** | API | 多 | 快 | 商业 |

**关键工程经验**：
- **候选集大小**：Top-K → rerank 取 Top-N，K 建议 **50-200**，N 建议 **3-10**
- **延迟**：
  - 100 doc × bge-reranker-large：~200-500ms（GPU）/ 1-3s（CPU）
  - 50 doc × MiniLM：~50-100ms
- **性价比原则**：先 BGE-reranker-v2-m3 / Cohere，扛不住再降级到 MiniLM

### 3.3 LLM-based Rerank

**方式 1：Pointwise（逐 doc 打分）**
```
Prompt: 对下面 doc 和 query 给出 1-10 分相关性
Query: {q}
Doc: {d}
Score:
```
- 简单直接
- 成本高：每 doc 一次 LLM 调用
- 适合：候选集 < 20 的高价值场景

**方式 2：Listwise（RankGPT 滑动窗口）**
```
Prompt: 给定 query 和 N 个 docs，请输出按相关性排序的列表
Docs: [d1, d2, d3, d4, d5]
Output: [d3, d1, d5, d2, d4]
```
- 质量可能比 Cross-Encoder 还高
- 窗口滑动（sliding window）做全集排序
- 适合：离线评估 / 极高精度场景
- 成本：每次 LLM 调用 token 消耗大

**方式 3：Pairwise（两两比较）**
- 比较 doc_i 和 doc_j 谁更相关
- 成本 O(N²)，N 大时不可行
- 适合：N < 10 的精排

### 3.4 轻量特征融合（生产常用）

**不只看语义，综合多信号**：
```
final_score = α·cosine_sim 
            + β·bm25_score（归一化）
            + γ·recency_score（时间衰减）
            + δ·authority_score（来源权威性）
            + ε·click_through_rate（点击率）
```
- 可用 LTR 模型（LambdaMART / XGBoost）学习权重
- 优势：极快、可解释、可融入业务规则
- 劣势：需要标注数据 / 行为数据

### 3.5 Reranker 选型决策树

```
延迟预算 < 200ms？
  ├─ 是 → 不要 Rerank，或用 MiniLM（22M）/ Cohere API
  └─ 否 → 
      通用场景？
        ├─ 是 → BGE-reranker-v2-m3（开源）/ Cohere Rerank 3.5（API）
        ├─ 中文优先 → bce-reranker / BGE-reranker-large
        ├─ 长文本（> 512 token）→ Jina Reranker v2/v3
        └─ 极致精度 → LLM-based（RankGPT）
```

---

## 4. 混合检索：BM25 + 向量

### 4.1 为什么必须混合？

**业界 benchmark 数据**（Microsoft 实际生产索引测试）：
- 纯关键词：48.4 平均相关性
- 纯向量：43.8 平均相关性
- **混合：59.4 平均相关性**

**典型 query 分布**：
| Query 类型 | 纯向量 | 纯 BM25 | 混合 |
|-----------|--------|---------|------|
| "退款政策" | ✅ | ✅ | ✅ |
| "error code 0x80004005" | ❌ 错位 | ✅ 精确 | ✅ |
| "SDK 概念解释" | ✅ | ❌ 无关键词 | ✅ |
| "NVIDIA H100 specs" | ❌ 型号错位 | ✅ | ✅ |
| "Explain RLHF" | ✅ | ❌ | ✅ |

结论：**任何生产级 RAG 都该默认上 hybrid**。

### 4.2 融合算法

#### RRF（Reciprocal Rank Fusion，主流）

**公式**：
```
RRF(d) = Σᵢ 1 / (k + rankᵢ(d))
```
- k 默认 60（来自原论文）
- **只用 rank，不用原始 score** → 不需要归一化
- 不同 retriever 分数量纲不一致也无所谓
- 工程上最稳，业界默认

**例子**：
```
Doc A: dense rank 1, BM25 rank 5
       RRF = 1/(60+1) + 1/(60+5) = 0.0164 + 0.0154 = 0.0318

Doc B: dense rank 3, BM25 rank 1  
       RRF = 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323  ← 胜出
```

**RRF 的关键优势**：
- 不需要分数归一化
- 对个别 retriever 故障鲁棒
- 业界 5-15% NDCG@10 提升

#### 加权求和

```
final = α·norm(dense) + (1-α)·norm(BM25)
```
- α 通常 0.3-0.7
- 语义任务偏 dense → α 取 0.7
- 专名任务偏 BM25 → α 取 0.3
- **必须先归一化**（min-max 或 z-score）

**经验**：默认 RRF，有 held-out eval 再切加权。

### 4.3 各家向量库的混合支持

| 数据库 | 原生 Hybrid | 融合方法 |
|--------|-------------|---------|
| **Elasticsearch** | ✅ | native RRF |
| **OpenSearch** | ✅ | native RRF |
| **Weaviate** | ✅ | configurable alpha |
| **Qdrant** | ✅ | sparse + dense vectors |
| **Milvus** | ✅ | hybrid + rerank |
| **Pinecone** | ✅ | sparse + dense |
| **pgvector** | ❌ | 需手动 + Postgres FTS |

### 4.4 混合检索的 Trade-off

**优势**：
- NDCG@10 提升 5-15%
- 处理长尾 query（专名 / 同义 / 罕见术语）
- 成本：~6ms 额外延迟（fuse 阶段）

**代价**：
- 维护两套索引（存储 1.4x）
- 复杂度↑
- 小语料可能没必要（< 1k doc）

**关键提醒**：dense / sparse 索引的 schema 变更触发条件不同——tokenizer 改 → sparse 重灌；embedding 改 → dense 重灌。

---

## 5. 高级召回：Query 改写 / HyDE / Graph / Agentic

### 5.1 Query 改写（Query Transformation）

**为什么需要？** 用户自然语言 query 跟文档存储的"长段落"严重不对称。

#### 5.1.1 Query Decomposition

**场景**：多跳 / 比较 / 聚合问题

**例子**：
> Query: "GPT-4 跟 Claude 3 在代码生成和数学推理上对比"

**拆解**：
1. "GPT-4 code generation benchmarks"
2. "Claude 3 code generation benchmarks"
3. "GPT-4 mathematical reasoning"
4. "Claude 3 mathematical reasoning"

**收益**：复杂 query recall 提升 **10-25%**。

#### 5.1.2 Multi-Query

**思路**：一个 query 产生 N 个变体，分别检索，合并去重。
- 适合：模糊 query、多意图 query
- 风险：变体太相似浪费 token
- 调优：`QueryVariantCount = 2-3` 足够

#### 5.1.3 Step-Back Prompting

**思路**：先问一个更宽泛的"上层问题"，从更宽的答案里定位具体答案。

```
原 query: "2024 Q3 法国 GDP 是多少？"
step-back: "法国近期经济指标和 GDP 数字？"
```

#### 5.1.4 Query Rewriting / Self-Query

**用途**：多轮对话、专名 / 缩写 / 错别字

```
用户: "那内存呢？"（接前文服务器配置）
改写: "XX 服务器的内存配置"
```

**实现**：每次 query 前 LLM 改写（结合历史 context）

### 5.2 HyDE（Hypothetical Document Embeddings）

**核心思想**：让 LLM 先**凭空写一个假答案**，然后用这个假答案的 embedding 去检索真文档。

```
User query: "timeout issue"
LLM 凭空生成: "This document discusses database connection pool timeouts in production environments..."
   ↓ embed
向量检索（用假答案的向量，而不是 query 的向量）
   ↓
召回真实文档
```

**为什么有效？**
- 假答案在 embedding 空间里**接近真实文档的分布**（同样是段落形式）
- 短 query vs 长文档的语义鸿沟被桥接

**何时有效 / 何时有害**：

| 有效 | 有害 |
|------|------|
| 短 query vs 长文档 | 高度专业 / 私有领域 |
| 通用知识 QA | 幻觉的假答案把检索带偏 |
| 用户问题开放、宽泛 | 极窄 fact-lookup query |

**代价**：每次 +1 次 LLM 调用（+200-500ms）

### 5.3 GraphRAG（微软方案）

**核心思想**：先用 LLM 从文档构建**实体-关系图谱**，再基于图做检索。

**适用场景**：
- 多跳推理问题（"A 公司和该协会有什么关系"）
- 全局性问题（"整个语料的核心主题"）
- 跨文档关联（科研、法律、组织架构）

**流程**：
1. 实体抽取（人名、公司、概念）
2. 关系抽取（"X 是 Y 的子公司"）
3. 社区检测（聚类）
4. 社区摘要（每个社区 LLM 生成摘要）
5. 检索：本地搜索（具体实体）+ 全局搜索（社区摘要）

**代价**：
- 索引成本极高（一次性 LLM 调用密集）
- 文档更新需要重跑
- 不适合：简单 FAQ、单一文档

### 5.4 Self-RAG / CRAG（自反思）

**Self-RAG**：训练 LLM 输出特殊 token（[Retrieve]、[IsRel]、[IsSup]、[IsUse]）自评检索质量。

**CRAG（Corrective RAG）**：
- 检索结果分类：Correct / Incorrect / Ambiguous
- Correct → 直接用
- Incorrect → 改写 query 重试 / 走 web search
- Ambiguous → 混合

**价值**：让系统**自适应**检索策略，而不是固定流程。

### 5.5 Agentic RAG

**核心思想**：让 Agent 决定**何时检索、检索什么、用什么工具**，不再硬编码流程。

```
Agent Loop:
  Thought: 用户问对比 A B 方案，需要分别检索
  Action: 搜索 "A 方案"
  Observation: 拿到 A 资料
  Thought: 现在需要 B
  Action: 搜索 "B 方案"
  Observation: 拿到 B 资料
  Thought: 足够生成对比了
  Action: 生成答案
```

**实现**：LangGraph / ReAct / Plan-and-Execute

**代价**：
- 决策出错难 debug
- 检索次数膨胀 → token 暴涨
- 需要 loop budget 控制

**何时用**：复杂多步任务；简单场景反而是负担。

### 5.6 RAPTOR（层次化检索）

**思路**：递归把 chunk 聚类、生成摘要，建一棵**层次树**：
- Level 0：原始 chunk
- Level 1：方法级摘要
- Level 2：类级摘要
- Level 3：服务级摘要
- Level 4：架构摘要

**价值**：保留**全局上下文**，适合"整本书在讲什么"类问题。

---

## 6. 工程经验与最佳实践

### 6.1 召回阶段选型矩阵

| 业务特征 | 推荐方案 |
|---------|---------|
| 通用 RAG，无明显特征 | Dense + BM25 + RRF + Rerank |
| 中文文档为主 | BGE-large-zh + BM25 + bce-reranker |
| 多语种 | BGE-M3（统一输出）|
| 专名 / 型号 / 错误码密集 | Hybrid + Rerank（提升精度）|
| 极专业领域 | Fine-tune embedding + Rerank |
| 超长文档（书 / 报告）| RAPTOR / Parent-Document |
| 跨文档多跳 | GraphRAG / Agentic |
| 用户 query 短 / 模糊 | HyDE + Multi-Query |
| 高频热点 | 加 metadata filter（时效性）|

### 6.2 关键参数经验值

| 参数 | 经验值 | 说明 |
|------|--------|------|
| **chunk_size** | 300-500 token | 大了稀释语义，小了缺上下文 |
| **chunk_overlap** | 10-20% (50-100 token) | 防止边界信息丢失 |
| **Top-K 召回** | 20-50 | 给 Rerank 留足候选 |
| **Top-N 输出** | 3-7 | 多了干扰，少了不够 |
| **RRF k** | 60 | 原论文默认值 |
| **RRF k 调优** | 10-60 | k 大 → 排名差异稀释；k 小 → 头部权重集中 |
| **Cohere top_n** | 3-5 | |
| **Cross-Encoder batch** | 32-64 | GPU 显存允许下越大越好 |
| **Lost in middle** | 重要 chunk 放**首尾** | 中段注意力衰减 |

### 6.3 召回 K 与质量的关系

**拐点法**：
1. 跑一组实验：K = 10, 20, 50, 100, 200
2. 观察 Recall@K 曲线
3. 找到**收益开始平缓的拐点**——通常 20-50
4. 这就是给 Rerank 的候选集大小

### 6.4 Chunking 是"命门"

业界共识（80% 失败可追溯到 chunking）：

| 策略 | 适用 | 切分长度 |
|------|------|---------|
| 固定大小 | 通用 baseline | 200-500 token, overlap 10-20% |
| 递归字符 | 常规技术文档 | 400-800 token |
| 按结构（标题/段落）| 说明书、报告 | 按结构切 |
| **语义切分** | 复杂论述 | 按主题转换点 |
| Agentic（LLM 决定）| 复杂 PDF / 书 | LLM 判断 |
| Parent-Child | 精确 + 上下文 | 小 child 检索，大 parent 喂 LLM |

**关键经验**：
- 表格 / 代码 / 列表**单独处理**（不要混在 prose 里切）
- 切分时保留 metadata（标题、章节、来源）
- **不要一刀切**：技术手册 512 token，会议纪录 800-1200 token

### 6.5 成本与延迟预算

| 阶段 | 延迟 | 成本 |
|------|------|------|
| Query embedding | 30-50ms | $0.0001 |
| 向量检索 | 10-50ms | - |
| BM25 | 5-20ms | - |
| RRF 融合 | < 5ms | - |
| Cross-Encoder（50 doc）| 150-300ms | GPU 占用 |
| LLM 生成 | 500-2000ms | $0.001-0.01 |

**典型 RAG 端到端**：~800ms-3s

### 6.6 Rerank 落地最佳实践

1. **候选集 K**：20-50（不是 100+，平衡召回 + 延迟）
2. **输出 N**：3-7（少于 3 信息不够，多于 7 干扰）
3. **降级方案**：Rerank 服务挂了 → fallback 到 bi-encoder 分数（不要直接失败）
4. **缓存**：相同 (query, doc) pair 重复算 → 缓存
5. **批处理**：50 doc 一次过 GPU，不要 1 doc 一次
6. **监控**：cross-encoder 分数分布（如果都 < 0.3 说明检索本身就有问题）
7. **阈值过滤**：rerank 分数低 → 直接拒答（避免幻觉）

---

## 7. 常见坑 + 业界处理手段

### 坑 1：Chunk 把表格 / 列表切散

**症状**：问"Q3 营收"，召回的 chunk 行列错位，模型乱答。

**业界处理**：
- 表格单独切，**保留表头 + 第一行**作为元数据
- 用 Vision LLM（GPT-4o / Claude）把 PDF 表格转 Markdown
- Unstructured / LlamaParse 做 layout-aware 解析
- 转成自然语言描述："内存 16GB 的型号售价 5999 元"

### 坑 2：跨页 / 跨段上下文断裂

**症状**：定义在第 3 页，引用在第 40 页，召回只回其中一段。

**业界处理**：
- **Parent-Document Retriever**：检索小 chunk，返回大 chunk
- **Auto-merging Retrieval**：合并相邻 sibling chunk
- **Sentence Window Retrieval**：检索单句，返回前后 N 句

### 坑 3：版本漂移（Doc 改了，向量库没更新）

**症状**：AI 引用了 v6 的政策，但实际已更新到 v7。

**业界处理**：
- 每个 chunk 带 metadata：doc_id / last_updated / version
- 增量更新管道：检测文件 hash 变化 → 删旧 chunk → 写新 chunk
- 定时任务扫描文件系统 / Confluence
- 查询时按 updated_at 过滤

### 坑 4：多轮对话指代丢失

**症状**："那内存呢？" → 拿"那内存"去搜，无结果。

**业界处理**：
- **Query Rewriting**：每轮把历史对话 + 当前 query 用 LLM 改写成自包含 query
- 或：把历史摘要也塞进 query
- LangChain 的 `ConversationalRetrievalChain`

### 坑 5：检索返回的 chunk 不在 LLM 上下文里

**症状**：retrieve top-5，但 LLM 实际用的不是这 5 个。

**业界处理**：
- 在 prompt 里**显式标注**每个 chunk 的编号 / 来源
- 要求 LLM 引用："请基于 [1][2][3] 的资料回答，并标注引用"
- Lost-in-Middle 缓解：**关键 chunk 放首尾**

### 坑 6：Recall 高但 Precision 低（召回准、引用歪）

**症状**：召回的 chunk 跟 query 相似但不是用户真正要的。

**业界处理**：
- 加 Rerank（最直接）
- 优化 chunking（语义切分）
- 加 metadata filter 缩小范围
- Query 改写 / HyDE

### 坑 7：检索为空 / 全是低分

**症状**：cross-encoder 全 0.0-0.1 区间。

**业界处理**：
- **不要硬塞 LLM 生成**——直接说"未找到相关信息"
- 检查：embedding 模型是否匹配语种？chunk 大小是否合理？文档是否真的覆盖？
- 兜底：触发 web search 兜底

### 坑 8：Vector DB 版本切换 / Embedding 升级

**症状**：换了 embedding 模型但只重灌了一半。

**业界处理**：
- **绝对不能静默切换**
- 全量重灌 + 双写双读灰度
- 每个 chunk 记录 embedding_model_version
- 监控相似度分布突变了

### 坑 9：TopK 太大导致"反向降级"

**症状**：TopK 从 5 调到 20 答案质量反而变差。

**原因**：弱相关 chunk 干扰 LLM。

**业界处理**：
- 严格控制 Top-N（3-7）
- 用 Rerank 截断
- 设最低分数阈值

### 坑 10：HyDE 幻觉把检索带偏

**症状**：HyDE 生成的"假答案"错得离谱，召回也跟着错。

**业界处理**：
- 限制 HyDE 输出 token 数（防编长）
- 监控：query embedding vs hypothetical embedding 相似度（太低说明偏题）
- Fallback：hypothetical 分数 < 阈值时回退到原 query

### 坑 11：长 query 反而检索差

**症状**：用户写了一段 200 字的问题，召回质量反而不如 5 字。

**原因**：长 query 自身就是段落，embedding 时跟文档分布冲突。

**业界处理**：
- LLM 把长 query 总结成短 query
- 或拆成多个 sub-query 分别检索

### 坑 12：Rerank 反而把对的排到后面

**症状**：人工确认 ground truth 在 top-20，但 cross-encoder 把它排到 50。

**原因**：cross-encoder 训练领域跟你的语料不匹配。

**业界处理**：
- 不要硬用阈值过滤（cross-encoder 分数不可信作绝对值）
- 用 **rank 顺序**而不是**绝对分数**做截断
- 在自己语料上做 cross-encoder 微调（小成本）

### 坑 13：召回评估指标看起来很好但生产翻车

**症状**：Recall@10 = 0.95，但用户投诉答案错。

**原因**：评估集分布跟真实用户 query 分布不一致。

**业界处理**：
- 评估集必须来自**真实用户 query 采样**（不是 LLM 生成）
- 至少 100 条，分布真实
- 每月增量更新
- 在线 A/B 验证最终答案质量

### 坑 14：扫描件 PDF / OCR 错误

**症状**：扫描件 OCR 出来的 chunk 充满错字，embedding 完全乱。

**业界处理**：
- 提前 OCR（Tesseract / PaddleOCR / 云 OCR）
- 商业 OCR（百度 / 腾讯 / Google Document AI）
- 扫描件用 Vision LLM 直接读图，不要 OCR

### 坑 15：实时数据 RAG 搞不定

**症状**：用户问"今天的股价"，但 RAG 知识库是昨天入库的。

**业界处理**：
- **RAG 不是万能**：实时数据走 Tool Call / API
- 三层架构：
  - 静态层（历史文档、政策）
  - 半动态层（changelog、价格表）
  - 实时层（API / DB）
- Agent 决策：先 RAG，必要时调 API

---

## 8. 选型决策表

### 8.1 召回方法选择

| 业务场景 | 首选 | 备选 | 不推荐 |
|---------|------|------|--------|
| 通用 RAG | Hybrid (Dense + BM25) + Rerank | Dense + Rerank | 纯 BM25 |
| 中文 FAQ | BGE-large-zh + BM25 + bce-reranker | 同左 | OpenAI embedding（中文弱）|
| 多语种 | BGE-M3 | Cohere Embed v4 | 单一语言模型 |
| 专名密集（型号、错误码）| BM25 权重加大 + Rerank | Hybrid | 纯 Dense |
| 极专业领域（医疗 / 法律）| Fine-tune embedding + 专用 Rerank | Hybrid | 通用模型 |
| 多跳推理 | GraphRAG / Agentic RAG | Multi-Query + Self-RAG | 单步 Naive RAG |
| 长文档（书 / 报告）| RAPTOR / Parent-Document | 加大 chunk_size | 固定小 chunk |
| 实时数据 | 不适用，用 Tool Call | Hybrid + 时效性 metadata filter | - |

### 8.2 Rerank 模型选择

| 业务场景 | 首选 | 备选 |
|---------|------|------|
| 通用 + 多语种 | BGE-reranker-v2-m3 / Cohere Rerank 3.5 | Jina Reranker v2 |
| 纯中文 | bce-reranker / BGE-reranker-large | Cohere |
| 延迟极敏感（< 100ms）| ms-marco-MiniLM-L-6 | Cohere API |
| 长文档（> 512 token）| Jina Reranker v2/v3 | BGE-reranker-v2-m3 |
| 极致精度（成本不敏感）| LLM-based (RankGPT) | - |
| 商业、稳定 | Cohere Rerank 3.5 / Voyage | - |

### 8.3 何时不需要 Rerank？

- 延迟预算 < 200ms 且**第一阶段已经很准**
- 候选集 < 10（rerank 收益边际）
- 强 metadata filter 已经把候选集缩到很小

### 8.4 何时不需要向量检索？

- **强结构化查询**："订单 ID 12345" → 直接 SQL
- **精确 ID / SKU 检索** → 直接 ES / DB
- **小语料**（< 1k doc）→ 全文检索可能就够
- **实时性强** → Tool Call

---

## 9. 面试高频 QA

### Q1. 为什么需要 Rerank？只做向量检索不行吗？

**答**：
- 向量检索用 Bi-Encoder，query 和 doc 独立编码，丢失细粒度交互
- "相似" ≠ "相关"：语义相似但答非所问的 chunk 会被召回
- Cross-Encoder 让 Q + D 全交互，精准判断相关性
- 业界数据：Rerank 后 Recall@10 提升 10-20%，端到端答案质量提升 8-13%
- 类比：HR 招聘——JD 投简历（向量粗筛）→ HR 筛选简历（Rerank 精排）→ 部门面试（LLM 生成）

### Q2. Bi-Encoder 和 Cross-Encoder 的本质区别？

**答**：
- **Bi-Encoder**：Q / D 独立编码 → 单向量 → cosine 相似度
  - 快（文档预计算）但丢精度
  - 单向量压缩所有语义，细粒度交互没了
- **Cross-Encoder**：Q + D 拼接 → 一次 Transformer 前向 → 相关性分数
  - 慢（每对都要算）但精准
  - token 级全注意力，细粒度匹配
- 工业组合：Bi-Encoder 召回 → Cross-Encoder 精排

### Q3. RRF 是什么？为什么比加权融合好用？

**答**：
- **RRF（Reciprocal Rank Fusion）**：只基于 rank，不基于原始分数的融合
- 公式：`RRF(d) = Σᵢ 1 / (k + rankᵢ(d))`
- **为什么好用**：
  - 不用归一化（BM25 vs cosine 量纲不同）
  - 对个别 retriever 故障鲁棒
  - 几乎不需要调参（k 默认 60）
- 业界 benchmark：比加权融合在多数场景下 NDCG 持平或更好

### Q4. 怎么评估 RAG 系统的检索质量？

**答**：
- **检索指标**：Recall@K（正确答案在不在前 K）、MRR（正确排在第几位）、NDCG@10（综合排序质量）
- **生成指标**：Faithfulness（答案是否基于检索内容）、Answer Relevancy
- **端到端**：用户满意度、追问率、转人工率
- **框架**：RAGAS（最流行，自动 LLM-as-Judge 打分）
- **必须做**：50-200 条真实 query 标注集，CI 自动化跑

### Q5. 向量库怎么选？

**答**：
- **小规模 / 原型**：Chroma、FAISS
- **生产 / 分布式**：Milvus、Weaviate、Qdrant
- **云托管**：Pinecone、Zilliz
- **已有 Postgres**：pgvector
- **要混合检索**：Qdrant、Weaviate、Elasticsearch
- 选型维度：数据规模、QPS、是否要 hybrid、运维成本、私有化

### Q6. Embedding 模型怎么选？

**答**：
- **英文**：OpenAI text-embedding-3-large、BGE-large-en
- **中文**：BGE-large-zh、M3E、bge-large-zh
- **多语种**：BGE-M3、Jina v3、Cohere Embed v4
- **本地 / 隐私**：BGE-M3、Nomic-embed
- **决策依据**：MTEB 榜单、语种、维度、私有化能力、推理速度、成本
- **关键提醒**：**chunking 比 embedding 影响更大**（业界共识）

### Q7. Rerank 候选集 K 怎么选？输出 N 怎么选？

**答**：
- K（召回多少给 rerank）：**20-50**
  - 太低（< 10）：rerank 提升边际
  - 太高（> 100）：rerank 慢、增益稀释
  - 经验法：跑实验找 Recall@K 拐点
- N（rerank 后给 LLM 多少）：**3-7**
  - 太少：上下文不够
  - 太多：干扰 + 成本↑
  - 经验：4-6 是大多数场景甜点
- 比例：**K : N ≈ 10 : 1**

### Q8. 怎么解决"召回准、引用歪"问题？

**答**：
- "召回准"：embedding 召回的 chunk 跟 query 相似
- "引用歪"：但这些 chunk 不是用户真正想要的答案
- **解决**：
  1. 加 Rerank（cross-encoder 判断相关性）
  2. 优化 chunking（语义切分、保留结构）
  3. Query 改写 / HyDE
  4. Metadata filter 缩小范围
  5. 监控"是否被 LLM 引用"作为反馈指标

### Q9. HyDE 什么时候用，什么时候不用？

**答**：
- **用**：
  - 用户 query 短（如 2-3 个词），文档是长段落
  - 通用知识 QA，LLM 有背景知识
  - 提升 short query 召回率
- **不用**：
  - 高度专业 / 私有领域（LLM 幻觉假答案）
  - 极窄 fact-lookup（具体数字、ID）
  - 延迟极敏感（+1 LLM 调用 = +200-500ms）
  - 已有高质量 chunking + 强大 Rerank

### Q10. Naive RAG / Advanced RAG / Modular RAG 演进？

**答**：
- **Naive RAG**：固定 pipeline（load → split → embed → retrieve → generate）
- **Advanced RAG**：加入 query 优化、chunking 优化、rerank、prompt 优化
- **Modular RAG**：每个模块抽象化、可插拔、可重排（Adaptive RAG、Self-RAG、CRAG）
- **趋势**：从流水线 → 模块化 → Agentic（让 LLM 决定流程）

### Q11. Agentic RAG 和传统 RAG 区别？

**答**：
- **传统 RAG**：固定流程，retrieve 一次
- **Agentic RAG**：Agent 决定何时检索、检索什么、用什么工具
- **优势**：复杂多步任务灵活
- **代价**：决策难 debug、token 消耗↑
- **何时用**：多跳推理、需要 Tool Call 配合的复杂场景
- **何时不用**：简单 QA，反而是负担

### Q12. GraphRAG 适用场景？

**答**：
- 适用：
  - 多跳推理（"A 公司和该协会有什么关系"）
  - 全局性问题（"语料库核心主题"）
  - 跨文档实体关联（科研、法律）
  - 知识密集型（公司组织架构）
- 不适用：
  - 简单 FAQ
  - 单一文档检索
  - 成本敏感（建图成本极高）
  - 文档频繁更新（图维护贵）

### Q13. 怎么解决多轮对话的 RAG 召回？

**答**：
- 核心问题：query 依赖前文（指代、省略）
- 方案：
  1. **Query Rewriting**：LLM 把历史 + 当前 query 改写成自包含 query
  2. **Contextualized Embedding**：把历史摘要也塞进 query embedding
  3. **Session-level Retrieval**：把整个 session 作为检索单位
  4. **HyDE + 历史**：让 LLM 生成的假答案考虑历史

### Q14. Embedding 升级 / 换模型怎么平滑过渡？

**答**：
- 永远不要静默切换（会导致新旧向量混在库里）
- 流程：
  1. 准备新 embedding 模型，全量重灌到新 index
  2. 双写：老 index 继续服务，新 index 写但只读 0%
  3. 灰度切流：10% → 30% → 50% → 100%
  4. 监控 NDCG@10、用户反馈
  5. 没问题后下掉老 index
- 经验：embedding 升级是**重灌级别**的工程，不是 config flip

### Q15. Self-RAG 怎么工作？

**答**：
- 训练 LLM 输出**特殊 token**自评：
  - `[Retrieve]`：要不要检索
  - `[IsRel]`：检索内容相关吗
  - `[IsSup]`：答案有检索内容支撑吗
  - `[IsUse]`：答案整体有用吗
- 流程：
  - 决定要不要检索（不必要的问题不检索）
  - 检索后判断相关性（不相关重新检索）
  - 答案生成后判断支撑度（幻觉检测）
- 价值：让系统**自适应**，避免不必要检索 / 幻觉

---

## 10. 业界 Benchmark 数据

### 10.1 Hybrid vs Pure 检索

来源：Microsoft 实际生产索引测试
| 方法 | 平均相关性分数 |
|------|--------------|
| 纯关键词 | 40.6 |
| 纯向量 | 43.8 |
| **混合 (Hybrid)** | **48.4** |

来源：Supermemory 实战
| 方法 | Recall@10 |
|------|-----------|
| Sparse only (BM25) | 65% |
| Dense only | 78% |
| **Hybrid (RRF)** | **91%** |

### 10.2 Rerank 收益

来源：kunwar.page 综合 benchmark
- 加 Rerank 后答案准确率 +8-13%
- MRR / NDCG@10 提升 10-20%
- 代价：+100-200ms 延迟

### 10.3 不同 Rerank 模型速度

| 模型 | 单次推理 | 50 doc batch |
|------|---------|--------------|
| MiniLM-L-6 (CPU) | ~30ms | ~150ms |
| BGE-reranker-large (CPU) | ~80ms | ~1.5s |
| BGE-reranker-v2-m3 (GPU) | ~15ms | ~200ms |
| Cohere Rerank (API) | - | ~300ms（含网络）|

### 10.4 Chunking 影响

来源：codexops 实战
- 固定 512 token chunk → 语义 chunk：retrieval precision 提升 **31%**
- 跨所有 embedding 模型稳定提升
- **结论**：chunking 比 embedding 模型影响大

### 10.5 Embedding 模型对比（2026 主流）

| 模型 | 维度 | MTEB | 速度 | 成本 |
|------|------|------|------|------|
| OpenAI text-embedding-3-small | 1536 | 62.3 | 快 | $0.02/1M |
| OpenAI text-embedding-3-large | 3072 | 64.1 | 中 | $0.13/1M |
| BGE-M3 | 1024 | - | 中 | 开源 |
| BGE-large-zh | 1024 | - | 中 | 开源 |
| Nomic-embed-v2 | 768 | 63.5 | 快 | 开源 |
| Jina-embeddings-v3 | 1024 | 65.2 | 中 | 开源/API |
| Cohere Embed v4 | 1024 | 66.0 | 快 | $0.10/1M |

### 10.6 Rerank 模型对比

| 模型 | 参数量 | 多语种 | 延迟（GPU 50 doc）|
|------|--------|--------|------------------|
| BGE-reranker-v2-m3 | 568M | ✅ | ~200ms |
| bce-reranker-base | 300M | 中 | ~150ms |
| bce-reranker-large | 500M | 中 | ~250ms |
| Jina Reranker v2 | - | ✅ 100+ | ~180ms |
| ms-marco-MiniLM-L-6 | 22M | 英 | ~50ms |
| Cohere Rerank 3.5 | API | ✅ 100+ | ~300ms |

---

## 附录：核心概念速查

| 缩写 | 全称 | 一句话 |
|------|------|--------|
| RAG | Retrieval-Augmented Generation | 检索增强生成 |
| RRF | Reciprocal Rank Fusion | 基于排名的融合算法 |
| BM25 | Best Matching 25 | 经典 TF-IDF 类算法 |
| HyDE | Hypothetical Document Embeddings | 用 LLM 假答案检索 |
| LTR | Learning to Rank | 学习排序 |
| CE | Cross-Encoder | 交叉编码器 |
| BE | Bi-Encoder | 双塔编码器 |
| ANN | Approximate Nearest Neighbor | 近似最近邻 |
| HNSW | Hierarchical Navigable Small World | 一种 ANN 索引 |
| MRR | Mean Reciprocal Rank | 平均倒数排名 |
| NDCG | Normalized Discounted Cumulative Gain | 归一化折损累计增益 |
| CRAG | Corrective RAG | 自我纠错 RAG |
| MTEB | Massive Text Embedding Benchmark | 嵌入模型评测基准 |
| BEIR | Benchmarking IR | IR 评测基准 |
| FTS | Full-Text Search | 全文检索 |
| ACL | Anthropic Contextual Compression | 上下文压缩检索 |

---

> 整理人：Mavis（基于用户简历 + 互联网公开技术资料）
> 整理时间：2026-09
> 资料来源：premai.io、codexops、datalaria、kua/redis.io、kunwar.page、enterprisedna.co、aws labs、nitinkc 等公开技术博客与论文
