#!/usr/bin/env bash
# 批量爬取所有数据源（米游社多游戏）

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== 批量爬取国内数据源 ==="
echo "开始时间: $(date)"
echo ""

# 米游社 - 多游戏
declare -a MIHOYO_GAMES=("genshin" "honkai_star_rail" "honkai3" "zenless")

for game in "${MIHOYO_GAMES[@]}"; do
    echo ">>> 爬取米游社 - $game"
    python scripts/crawl_mihoyo_requests.py \
        --game "$game" \
        --max-pages 5 \
        --max-articles 50 \
        || echo "[WARN] $game 爬取失败，继续..."
    echo ""
    sleep 2
done

echo "=== 爬取完成 ==="
echo "结束时间: $(date)"
echo ""

# 统计
echo "=== JSONL 文件统计 ==="
find data/raw/jsonl -name "*.jsonl" -type f | while read f; do
    count=$(wc -l < "$f")
    echo "$f: $count 条"
done
