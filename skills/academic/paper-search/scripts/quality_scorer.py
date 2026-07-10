#!/usr/bin/env python3
"""
Paper Quality Scorer - 多维度论文质量评分系统

评分维度（总分100）：
1. 引用量 (30分) - 被引次数
2. 发表质量 (25分) - 期刊/会议级别
3. 作者声誉 (20分) - 作者影响力
4. 创新性 (15分) - 基于摘要的AI评估
5. 时间权重 (10分) - 最新研究加分
"""

from typing import Dict, Optional
from datetime import datetime, timezone


class PaperQualityScorer:
    """论文质量评分系统"""

    def __init__(self):
        # 顶级期刊/会议列表
        self.tier1_venues = {
            # 综合顶级
            "Nature", "Science", "Cell",
            # AI/ML
            "NeurIPS", "ICML", "ICLR", "AAAI",
            "JMLR", "IEEE TPAMI", "IJCV",
            # Statistics
            "Annals of Statistics", "JASA", "Biometrika",
            "Journal of Royal Statistical Society",
            # General Science
            "PNAS", "Nature Communications", "Science Advances"
        }

        # 一级期刊/会议
        self.tier2_venues = {
            "CVPR", "ECCV", "ICCV", "ACL", "EMNLP",
            "AISTATS", "UAI", "ICLR Workshop",
            "Statistics in Medicine", "Biometrics",
            "Computational Statistics"
        }

        # 知名作者列表（简化版）
        self.famous_authors = {
            "Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio",
            "Andrew Ng", "Michael Jordan",
            # 可以扩展
        }

    def score_paper(self, paper: Dict, context: Optional[Dict] = None) -> float:
        """
        为单篇论文计算质量分数 (0-100)

        Args:
            paper: 论文数据字典
            context: 上下文信息（查询、领域等）

        Returns:
            质量分数 (0-100)
        """
        context = context or {}

        score = 0

        # 维度1: 引用量 (30分)
        score += self._citation_score(paper)

        # 维度2: 发表质量 (25分)
        score += self._venue_score(paper)

        # 维度3: 作者声誉 (20分)
        score += self._author_score(paper)

        # 维度4: 创新性 (15分)
        score += self._innovation_score(paper, context)

        # 维度5: 时间权重 (10分)
        score += self._recency_score(paper)

        return min(score, 100)  # 最高100分

    def _citation_score(self, paper: Dict) -> float:
        """引用量评分 (0-30分)"""
        citations = paper.get("citationCount", 0)

        if citations >= 500:
            return 30  # 高被引论文
        elif citations >= 100:
            return 25  # 中高被引
        elif citations >= 50:
            return 20  # 中等被引
        elif citations >= 10:
            return 15  # 低被引
        elif citations >= 5:
            return 10  # 很少被引
        else:
            return 5   # 未被引（可能是新论文）

    def _venue_score(self, paper: Dict) -> float:
        """发表质量评分 (0-25分)"""
        venue = paper.get("journal", "") or paper.get("venue", "")

        if not venue:
            return 10  # 无venue信息

        venue_lower = venue.lower()

        # 检查顶级
        for v in self.tier1_venues:
            if v.lower() in venue_lower:
                return 25  # 顶级

        # 检查一级
        for v in self.tier2_venues:
            if v.lower() in venue_lower:
                return 20  # 一级

        # 检查知名期刊名
        if any(x in venue_lower for x in ["nature", "science", "ieee", "acm"]):
            return 15

        return 10  # 普通期刊

    def _author_score(self, paper: Dict) -> float:
        """作者声誉评分 (0-20分)"""
        authors = paper.get("authors", [])

        if not authors:
            return 5

        # 检查知名作者
        for author in authors:
            author_str = str(author).lower()
            for famous in self.famous_authors:
                if famous.lower() in author_str:
                    return 20  # 知名作者

        # 基于作者数量评分
        num_authors = len(authors)
        if 3 <= num_authors <= 10:
            return 15  # 合理的团队规模
        elif num_authors > 10:
            return 10  # 大型合作项目
        else:
            return 12  # 小团队

    def _innovation_score(self, paper: Dict, context: Dict) -> float:
        """创新性评分 (0-15分)"""
        abstract = paper.get("abstract", "") or paper.get("summary", "")

        if not abstract:
            return 5

        # 关键词检测
        innovation_keywords = [
            "novel", "new", "first", "breakthrough", "state-of-the-art",
            "sota", "outperform", "surpass", "advance", "pioneering",
            "新型", "首次", "突破", "创新", "超越", "领先"
        ]

        abstract_lower = abstract.lower()
        keyword_count = sum(1 for kw in innovation_keywords if kw in abstract_lower)

        if keyword_count >= 5:
            return 15
        elif keyword_count >= 3:
            return 12
        elif keyword_count >= 1:
            return 8
        else:
            return 5

    def _recency_score(self, paper: Dict) -> float:
        """时间权重评分 (0-10分)"""
        pub_date_str = paper.get("published", "") or paper.get("publicationDate", "")

        if not pub_date_str:
            return 5

        try:
            # 处理ISO日期格式
            if "T" in pub_date_str:
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            else:
                pub_date = datetime.fromisoformat(pub_date_str)

            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            days_old = (datetime.now(timezone.utc) - pub_date).days

            if days_old <= 30:
                return 10  # 一个月内 - 最新
            elif days_old <= 90:
                return 8   # 3个月内
            elif days_old <= 180:
                return 6   # 半年内
            elif days_old <= 365:
                return 4   # 一年内
            else:
                return 2   # 更早的
        except:
            return 5


if __name__ == "__main__":
    # 测试代码
    scorer = PaperQualityScorer()

    test_paper = {
        "title": "Test Paper",
        "citationCount": 150,
        "journal": "Nature Machine Intelligence",
        "authors": ["Geoffrey Hinton", "Yann LeCun"],
        "abstract": "This novel breakthrough presents state-of-the-art results surpassing all previous methods.",
        "published": "2026-06-01T10:00:00Z"
    }

    score = scorer.score_paper(test_paper)
    print(f"Quality Score: {score}/100")
