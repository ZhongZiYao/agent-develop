"""Query Rewriter Module

处理原始查询：
1. 纠正错别字（typo correction）
2. 提取关键词（keyword extraction）
3. 同义词扩展（synonym expansion）
"""

from __future__ import annotations

import re
from typing import Any

from loguru import logger

from .base import ModuleRegistry, RAGModule


@ModuleRegistry.register
class QueryRewriterModule(RAGModule):
    """查询改写模块

    输入 state:
        - query: str (原始查询)

    输出 state 更新:
        - query: str (改写后查询)
        - expanded_queries: list[str] (扩展查询列表)
        - keywords: list[str] (提取的关键词)
    """

    name = "query_rewriter"

    def __init__(self, config: dict | None = None):
        super().__init__(config)

        # 游戏术语词典
        self.game_terms = set(
            self.config.get("game_terms", [
                "妖刀姬", "红蝶", "素问", "宁红夜", "顾清寒",
                "连招", "技能", "振刀", "蓄力", "副本", "冰火幻境",
                "S13", "S12", "版本", "更新", "平衡性",
            ])
        )

        # 同义词映射
        self.synonyms = self.config.get("synonyms", {
            "连招": ["技能连击", "combo", "技能顺序", "出招"],
            "怎么玩": ["攻略", "玩法", "技巧", "教学"],
            "bug": ["错误", "问题", "异常", "故障"],
            "副本": ["PVE", "关卡", "挑战"],
        })

        # 错别字映射（手工维护或从数据学习）
        self.typo_map = self.config.get("typo_map", {
            "要到姬": "妖刀姬",
            "要刀姬": "妖刀姬",
            "怎末": "怎么",
            "连召": "连招",
            "站位": "站位",  # 占位
        })

        self.enable_rewrite = self.config.get("enable_rewrite", True)
        self.enable_expansion = self.config.get("enable_expansion", True)

    async def __call__(self, state: dict) -> dict:
        """处理查询"""
        query = state.get("query", "")
        if not query:
            return {}

        # 1. Query Rewriting
        rewritten = self._rewrite_query(query) if self.enable_rewrite else query
        logger.debug(f"[{self.name}] Query rewritten: {query} → {rewritten}")

        # 2. Keyword Extraction
        keywords = self._extract_keywords(rewritten)
        logger.debug(f"[{self.name}] Extracted keywords: {keywords}")

        # 3. Query Expansion
        expanded = []
        if self.enable_expansion:
            expanded = self._expand_query(rewritten, keywords)
            logger.debug(f"[{self.name}] Expanded queries: {expanded}")

        return {
            "query": rewritten,
            "keywords": keywords,
            "expanded_queries": expanded,
        }

    def _rewrite_query(self, query: str) -> str:
        """改写查询（错别字纠正 + 规范化）"""
        result = query

        # 错别字替换（按长度降序，避免部分匹配）
        for typo, correct in sorted(
            self.typo_map.items(), key=lambda x: len(x[0]), reverse=True
        ):
            result = result.replace(typo, correct)

        # 规范化空格
        result = re.sub(r"\s+", " ", result).strip()

        return result

    def _extract_keywords(self, query: str) -> list[str]:
        """提取关键词（基于术语词典）"""
        keywords = []
        for term in self.game_terms:
            if term in query:
                keywords.append(term)

        # 按长度降序（长词优先）
        keywords.sort(key=len, reverse=True)
        return keywords

    def _expand_query(self, query: str, keywords: list[str]) -> list[str]:
        """查询扩展（同义词替换）"""
        expanded = []

        for keyword in keywords:
            if keyword in self.synonyms:
                for synonym in self.synonyms[keyword]:
                    new_query = query.replace(keyword, synonym)
                    if new_query != query:
                        expanded.append(new_query)

        return expanded[:5]  # 最多返回 5 个扩展

    def get_config(self):
        """导出配置"""
        config = super().get_config()
        config.params.update({
            "game_terms": list(self.game_terms),
            "synonyms": self.synonyms,
            "typo_map": self.typo_map,
            "enable_rewrite": self.enable_rewrite,
            "enable_expansion": self.enable_expansion,
        })
        return config
