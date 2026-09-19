#!/bin/bash
# 手动下载 BGE Reranker 模型到本地

# 创建本地模型目录
mkdir -p ./models/bge-reranker-v2-m3

# 从镜像站下载（使用 git-lfs）
cd ./models
git clone https://hf-mirror.com/BAAI/bge-reranker-v2-m3

# 或者直接下载文件
# wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/pytorch_model.bin
# wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/config.json
# wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/tokenizer_config.json
# wget https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/vocab.txt

echo "模型已下载到 ./models/bge-reranker-v2-m3"
