# Reranker 模型管理指南

## 📦 **模型信息**

### **默认模型：BAAI/bge-reranker-v2-m3**

| 属性 | 值 |
|------|-----|
| **来源** | HuggingFace |
| **大小** | 568 MB |
| **类型** | Cross-Encoder |
| **语言** | 多语言（中文优化） |
| **用途** | 文档相关性重排 |
| **架构** | BERT-based Sequence Classification |

**HuggingFace 链接**：https://huggingface.co/BAAI/bge-reranker-v2-m3

---

## 🚀 **下载方式**

### **方式 1：自动下载（推荐）**

```bash
# 启用 Reranker
RERANK_ENABLED=true

# 首次 API 请求时自动下载
# 下载位置：~/.cache/huggingface/hub/
```

**优点**：
- ✅ 零配置
- ✅ 自动缓存
- ✅ 版本管理

**缺点**：
- ❌ 首次下载需要网络
- ❌ 国内速度慢（可用镜像加速）

---

### **方式 2：国内镜像加速**

#### **配置环境变量**

```bash
# 方法 1：临时设置
export HF_ENDPOINT=https://hf-mirror.com

# 方法 2：在 docker-compose.yml 中配置
services:
  api:
    environment:
      - HF_ENDPOINT=https://hf-mirror.com
      
# 方法 3：在 .env 中添加（需要代码支持）
HF_ENDPOINT=https://hf-mirror.com
```

#### **验证镜像可用**

```bash
curl -I https://hf-mirror.com/BAAI/bge-reranker-v2-m3
# 返回 200 OK 表示可用
```

---

### **方式 3：手动下载到本地**

#### **Step 1: 下载模型**

```bash
# 使用脚本
bash scripts/download_reranker_model.sh

# 或手动下载
mkdir -p models/bge-reranker-v2-m3
cd models

# 使用 git-lfs（推荐）
git lfs install
git clone https://hf-mirror.com/BAAI/bge-reranker-v2-m3

# 或直接下载文件
wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/pytorch_model.bin
wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/config.json
wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/tokenizer_config.json
wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/vocab.txt
wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/special_tokens_map.json
```

#### **Step 2: 配置使用本地模型**

```bash
# .env
RERANK_MODEL=/app/models/bge-reranker-v2-m3  # 容器内路径

# 或使用相对路径
RERANK_MODEL=./models/bge-reranker-v2-m3
```

#### **Step 3: 挂载到容器**

```yaml
# docker-compose.yml
services:
  api:
    volumes:
      - ./models:/app/models  # 挂载本地模型目录
```

---

## ❓ **常见问题**

### **Q1: Ollama 可以用于 Reranker 吗？**

**❌ 不能**

**原因**：
- Ollama 专为 LLM（生成式模型）设计
- Reranker 是判别式模型（Cross-Encoder）
- 输入输出格式完全不同

**对比**：

| 特性 | LLM (Ollama) | Reranker (HuggingFace) |
|------|--------------|------------------------|
| 任务 | 文本生成 | 相关性打分 |
| 输入 | 文本 Prompt | (query, doc) 对 |
| 输出 | Token 序列 | 浮点数分数 |
| 模型格式 | GGUF/GGML | PyTorch/Safetensors |
| 支持工具 | Ollama | Transformers |

---

### **Q2: 模型会重复下载吗？**

**✅ 不会**

- 首次下载后缓存在 `~/.cache/huggingface/`
- 后续加载直接从缓存读取（<1s）
- 跨项目共享同一缓存

---

### **Q3: 如何查看已下载的模型？**

```bash
# Linux/Mac
ls -lh ~/.cache/huggingface/hub/

# Windows
dir %USERPROFILE%\.cache\huggingface\hub\

# 或在 Python 中
python -c "from transformers import snapshot_download; print(snapshot_download('BAAI/bge-reranker-v2-m3', local_files_only=True))"
```

---

### **Q4: 如何清理模型缓存？**

```bash
# 删除特定模型
rm -rf ~/.cache/huggingface/hub/models--BAAI--bge-reranker-v2-m3

# 清空所有缓存（谨慎）
rm -rf ~/.cache/huggingface/
```

---

### **Q5: 模型加载失败怎么办？**

**检查步骤**：

1. **确认网络连接**
   ```bash
   curl -I https://huggingface.co
   # 或使用镜像
   curl -I https://hf-mirror.com
   ```

2. **检查磁盘空间**
   ```bash
   df -h ~/.cache/huggingface/
   # 至少需要 1GB 空闲空间
   ```

3. **查看错误日志**
   ```bash
   docker compose logs api | grep -i "rerank\|transformers"
   ```

4. **降级到更小的模型**
   ```bash
   # .env
   RERANK_MODEL=sentence-transformers/ms-marco-MiniLM-L-12-v2  # 120MB
   ```

---

## 🎯 **推荐配置**

### **开发环境**

```bash
# .env
RERANK_ENABLED=true
RERANK_MODEL=BAAI/bge-reranker-v2-m3
RERANK_DEVICE=cpu
HF_ENDPOINT=https://hf-mirror.com  # 国内加速
```

### **生产环境**

```bash
# 1. 预先下载模型到本地
bash scripts/download_reranker_model.sh

# 2. .env 配置
RERANK_ENABLED=true
RERANK_MODEL=/app/models/bge-reranker-v2-m3  # 本地路径
RERANK_DEVICE=cuda  # 使用 GPU 加速

# 3. docker-compose.yml 挂载
volumes:
  - ./models:/app/models:ro  # 只读挂载
```

---

## 🔄 **替代模型**

如果 BGE-reranker-v2-m3 不适合，可以尝试：

### **选项 1：更小的模型（快速）**

```bash
RERANK_MODEL=sentence-transformers/ms-marco-MiniLM-L-12-v2
# 大小: 120MB
# 速度: 快 3-4 倍
# 精度: 略低（英文优化）
```

### **选项 2：更大的模型（精准）**

```bash
RERANK_MODEL=BAAI/bge-reranker-v2-minicpm-layerwise
# 大小: 2.4GB
# 速度: 慢 2 倍
# 精度: 更高
```

### **选项 3：中文专用模型**

```bash
RERANK_MODEL=BAAI/bge-reranker-large
# 大小: 1.3GB
# 语言: 中文优化
# 精度: 高
```

---

## 📊 **性能对比**

| 模型 | 大小 | CPU延迟 | GPU延迟 | MRR@10 |
|------|------|---------|---------|---------|
| **bge-reranker-v2-m3** | 568MB | 300ms | 50ms | 0.89 |
| ms-marco-MiniLM | 120MB | 100ms | 20ms | 0.82 |
| bge-reranker-large | 1.3GB | 500ms | 80ms | 0.92 |

**测试环境**：50 candidates → top 10

---

## 🛠️ **故障排查**

### **问题：下载超时**

```bash
# 解决方案 1：使用镜像
export HF_ENDPOINT=https://hf-mirror.com

# 解决方案 2：手动下载
bash scripts/download_reranker_model.sh

# 解决方案 3：禁用 Reranker
RERANK_ENABLED=false
```

### **问题：内存不足**

```bash
# 解决方案 1：使用更小的模型
RERANK_MODEL=sentence-transformers/ms-marco-MiniLM-L-12-v2

# 解决方案 2：减少 batch size（代码层面）
# 解决方案 3：增加 swap 空间
```

### **问题：推理太慢**

```bash
# 解决方案 1：使用 GPU
RERANK_DEVICE=cuda

# 解决方案 2：减少召回数量
TOP_K=30  # 从 50 降到 30

# 解决方案 3：使用更快的模型
RERANK_MODEL=sentence-transformers/ms-marco-MiniLM-L-12-v2
```

---

## 📚 **参考资料**

- [BGE Reranker 官方文档](https://github.com/FlagOpen/FlagEmbedding/tree/master/FlagEmbedding/reranker)
- [HuggingFace Transformers 文档](https://huggingface.co/docs/transformers/index)
- [HuggingFace 镜像站使用指南](https://hf-mirror.com/)

---

## 💡 **最佳实践**

1. **开发环境**：使用自动下载 + 镜像加速
2. **生产环境**：预先下载到本地 + 挂载到容器
3. **首次部署**：先禁用 Reranker，验证基础功能后再启用
4. **性能优化**：GPU > 小模型 > 减少召回数量
5. **监控**：记录 Reranker 延迟和内存占用

---

**总结**：Reranker 模型必须从 HuggingFace 下载（Ollama 不支持），建议使用国内镜像加速或预先下载到本地。首次下载后会永久缓存，后续加载很快。**
