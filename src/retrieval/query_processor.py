"""查询处理模块

功能：
1. Query Rewriting - 查询改写（纠正语法、补全上下文）
2. Query Expansion - 查询扩展（同义词、相关术语）
3. Keyword Extraction - 关键词提取（游戏术语、角色名）
"""

from __future__ import annotations

import re
from typing import Optional

from loguru import logger


class QueryProcessor:
    """查询优化器"""

    def __init__(self):
        # 游戏术语词典（可以从配置文件加载）
        self.game_terms = {
            "妖刀姬", "红蝶", "素问", "宁红夜", "顾清寒",
            "连招", "技能", "振刀", "蓄力", "副本", "冰火幻境",
            "S13", "S12", "版本", "更新", "平衡性",
        }

        # 同义词映射（用于查询扩展）
        self.synonyms = {
            "连招": ["技能连击", "combo", "技能顺序", "出招"],
            "怎么玩": ["攻略", "玩法", "技巧", "教学"],
            "bug": ["错误", "问题", "异常", "故障"],
            "副本": ["PVE", "关卡", "挑战"],
        }

    def process(
        self,
        query: str,
        enable_rewrite: bool = True,
        enable_expansion: bool = True,
    ) -> dict:
        """处理查询

        Args:
            query: 原始查询
            enable_rewrite: 是否启用查询改写
            enable_expansion: 是否启用查询扩展

        Returns:
            {
                "original": "原始查询",
                "rewritten": "改写后的查询",
                "expanded": ["扩展查询1", "扩展查询2"],
                "keywords": ["关键词1", "关键词2"],
            }
        """
        result = {
            "original": query,
            "rewritten": query,
            "expanded": [],
            "keywords": [],
        }

        # 1. Query Rewriting
        if enable_rewrite:
            rewritten = self._rewrite_query(query)
            result["rewritten"] = rewritten
            logger.debug(f"Query rewritten: {query} → {rewritten}")

        # 2. Keyword Extraction
        keywords = self._extract_keywords(result["rewritten"])
        result["keywords"] = keywords
        logger.debug(f"Extracted keywords: {keywords}")

        # 3. Query Expansion
        if enable_expansion:
            expanded = self._expand_query(result["rewritten"], keywords)
            result["expanded"] = expanded
            logger.debug(f"Expanded queries: {expanded}")

        return result

    def _rewrite_query(self, query: str) -> str:
        """查询改写

        规则：
        1. 补全缺失的主语（基于上下文）
        2. 纠正常见错别字
        3. 规范化表达
        """
        rewritten = query.strip()

        # 纠正常见错别字
        typo_map = {
            "要到姬": "妖刀姬",
            "洪蝶": "红蝶",
            "连召": "连招",
            "怎末": "怎么",
        }
        for typo, correct in typo_map.items():
            rewritten = rewritten.replace(typo, correct)

        # 补全缺失的上下文（例如：仅有"连招"时，可能缺少角色名）
        # 这里简化处理，实际可以结合 session 历史
        if "连招" in rewritten and not any(char in rewritten for char in self.game_terms):
            # 如果只问"连招"但没有角色名，保持原样（避免过度推测）
            pass

        # 规范化问号
        if "?" in rewritten:
            rewritten = rewritten.replace("?", "？")

        return rewritten

    def _extract_keywords(self, query: str) -> list[str]:
        """提取关键词

        策略：
        1. 匹配游戏术语词典
        2. 提取版本号（S13, S12）
        3. 提取角色名
        """
        keywords = []

        # 匹配术语词典
        for term in self.game_terms:
            if term in query:
                keywords.append(term)

        # 提取版本号（S + 数字）
        versions = re.findall(r'S\d+', query, re.IGNORECASE)
        keywords.extend([v.upper() for v in versions])

        # 去重保序
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords

    def _expand_query(self, query: str, keywords: list[str]) -> list[str]:
        """查询扩展

        策略：
        1. 基于同义词生成变体查询
        2. 保持原始查询的核心意图
        """
        expanded = []

        # 为每个关键词生成同义词变体
        for keyword in keywords:
            if keyword in self.synonyms:
                for synonym in self.synonyms[keyword]:
                    # 替换生成新查询
                    variant = query.replace(keyword, synonym)
                    if variant != query and variant not in expanded:
                        expanded.append(variant)

        # 限制扩展数量（避免过多）
        return expanded[:3]

    def get_search_queries(self, processed: dict) -> list[str]:
        """获取所有用于检索的查询

        Returns:
            [rewritten, expanded1, expanded2, ...]
        """
        queries = [processed["rewritten"]]
        queries.extend(processed["expanded"])
        return queries
