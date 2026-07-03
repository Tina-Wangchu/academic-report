#!/usr/bin/env python3
"""
Representative Paper Selector - 代表性论文筛选器

目标：从大量论文中选择最具代表性的论文，避免重复相似研究
- 按主题聚类
- 从每个聚类中选择最高分论文
- 确保多样性
"""

from typing import List, Dict, Set


class RepresentativePaperSelector:
    """代表性论文筛选器"""

    def __init__(self, similarity_threshold: float = 0.4):
        """
        Args:
            similarity_threshold: 相似度阈值（0-1），超过此值认为论文相似
        """
        self.similarity_threshold = similarity_threshold

    def select_representative_papers(self, papers: List[Dict],
                                   max_count: int = 10) -> List[Dict]:
        """
        从论文列表中选择最具代表性的论文

        Args:
            papers: 论文列表
            max_count: 最大返回数量

        Returns:
            选择的代表性论文列表
        """
        if len(papers) <= max_count:
            return papers

        # 步骤1: 主题聚类
        clusters = self._cluster_by_topic(papers)

        # 步骤2: 从每个聚类选择最好的论文
        representative = []
        papers_per_cluster = max(max_count // len(clusters), 1)

        for cluster in clusters:
            # 按质量分数排序
            sorted_cluster = sorted(cluster,
                                   key=lambda p: p.get("quality_score", 0),
                                   reverse=True)
            # 选择前N篇
            representative.extend(sorted_cluster[:papers_per_cluster])

        # 步骤3: 如果选多了，按分数重新排序并截断
        if len(representative) > max_count:
            representative = sorted(representative,
                                   key=lambda p: p.get("quality_score", 0),
                                   reverse=True)[:max_count]

        return representative

    def _cluster_by_topic(self, papers: List[Dict]) -> List[List[Dict]]:
        """
        基于主题对论文进行聚类

        使用简化的标题相似度聚类
        """
        clusters = []
        assigned_indices: Set[int] = set()

        for i, paper1 in enumerate(papers):
            if i in assigned_indices:
                continue

            cluster = [paper1]
            assigned_indices.add(i)

            # 查找相似论文
            for j, paper2 in enumerate(papers[i+1:], i+1):
                if j in assigned_indices:
                    continue

                if self._are_similar(paper1, paper2):
                    cluster.append(paper2)
                    assigned_indices.add(j)

            clusters.append(cluster)

        return clusters

    def _are_similar(self, paper1: Dict, paper2: Dict) -> bool:
        """
        判断两篇论文是否相似

        基于标题的关键词重叠度（Jaccard相似度）
        """
        title1 = paper1.get("title", "").lower()
        title2 = paper2.get("title", "").lower()

        # 分词为关键词集合
        words1 = set(self._extract_keywords(title1))
        words2 = set(self._extract_keywords(title2))

        if not words1 or not words2:
            return False

        # 计算Jaccard相似度
        intersection = words1 & words2
        union = words1 | words2

        similarity = len(intersection) / len(union)

        return similarity > self.similarity_threshold

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词

        简化版本：分词并过滤常见词
        """
        # 简单分词
        words = text.split()

        # 过滤常见词和短词
        common_words = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "be", "been",
            "基于", "的", "和", "与", "在", "用于", "通过"
        }

        keywords = [
            w.strip(".,!?;:")
            for w in words
            if len(w) > 3 and w.lower() not in common_words
        ]

        return keywords

    def add_quality_scores(self, papers: List[Dict]) -> List[Dict]:
        """
        为论文列表添加质量分数（如果没有的话）

        这个方法应该与 PaperQualityScorer 配合使用
        """
        for paper in papers:
            if "quality_score" not in paper:
                # 如果没有质量分数，设为默认值50
                paper["quality_score"] = 50

        return papers


if __name__ == "__main__":
    # 测试代码
    selector = RepresentativePaperSelector()

    test_papers = [
        {"title": "Deep Learning for Image Recognition", "quality_score": 85},
        {"title": "Image Recognition using Neural Networks", "quality_score": 80},
        {"title": "Statistical Methods for ML", "quality_score": 75},
        {"title": "Bayesian Inference in High Dimensions", "quality_score": 90},
    ]

    selected = selector.select_representative_papers(test_papers, max_count=2)
    print(f"Selected {len(selected)} papers:")
    for p in selected:
        print(f"  - {p['title']} (score: {p['quality_score']})")
