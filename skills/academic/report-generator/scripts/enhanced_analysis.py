#!/usr/bin/env python3
"""
Enhanced Research Analysis Module - 增强的研究分析模块

功能：
1. 研究趋势分析 - 识别热点、趋势变化
2. 研究缺口分析 - 识别研究空白和机会
3. 高频关键词提取
4. 引用量分析
5. 时间序列分析
"""

from typing import Dict, List, Any, Optional
from collections import Counter
import re


class ResearchAnalyzer:
    """研究分析器 - 趋势分析和缺口识别"""

    def __init__(self):
        # 停用词列表（英文和中文）
        self.stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            '基于', '的', '和', '与', '在', '中', '用于', '通过', '从', '到'
        }

    def analyze_research_trends(self, papers: List[Dict]) -> Dict[str, Any]:
        """
        分析研究趋势

        分析维度：
        1. 年度发文量趋势
        2. 数据源使用趋势
        3. 高频关键词（研究热点）
        4. 引用量分布（如果有）
        5. 顶级期刊发表趋势
        """
        if not papers:
            return {"error": "No papers to analyze"}

        # 1. 年度趋势
        year_trend = self._analyze_year_trend(papers)

        # 2. 数据源趋势
        source_trend = self._analyze_source_trend(papers)

        # 3. 热点关键词
        hot_topics = self._extract_hot_topics(papers)

        # 4. 引用量分析
        citation_analysis = self._analyze_citations(papers)

        # 5. 顶级期刊趋势
        venue_trend = self._analyze_venue_trend(papers)

        # 6. 综合趋势洞察
        trend_insights = self._generate_trend_insights(
            year_trend, source_trend, hot_topics, citation_analysis, venue_trend
        )

        return {
            "year_trend": year_trend,
            "source_trend": source_trend,
            "hot_topics": hot_topics,
            "citation_analysis": citation_analysis,
            "venue_trend": venue_trend,
            "trend_insights": trend_insights
        }

    def analyze_research_gaps(self, papers: List[Dict]) -> Dict[str, Any]:
        """
        分析研究缺口

        分析维度：
        1. 时间缺口（哪些年份论文较少）
        2. 主题缺口（哪些研究主题较少）
        3. 方法缺口（哪些研究方法应用不足）
        4. 跨学科机会
        """
        if not papers:
            return {"error": "No papers to analyze"}

        # 1. 时间缺口分析
        time_gaps = self._identify_time_gaps(papers)

        # 2. 主题缺口分析
        topic_gaps = self._identify_topic_gaps(papers)

        # 3. 研究方法缺口
        method_gaps = self._identify_method_gaps(papers)

        # 4. 跨学科机会识别
        interdisciplinary_opportunities = self._identify_interdisciplinary_opportunities(papers)

        # 5. 综合缺口洞察
        gap_insights = self._generate_gap_insights(
            time_gaps, topic_gaps, method_gaps, interdisciplinary_opportunities
        )

        return {
            "time_gaps": time_gaps,
            "topic_gaps": topic_gaps,
            "method_gaps": method_gaps,
            "interdisciplinary_opportunities": interdisciplinary_opportunities,
            "gap_insights": gap_insights
        }

    def _analyze_year_trend(self, papers: List[Dict]) -> Dict[str, Any]:
        """分析年度发文量趋势"""
        year_counts = Counter()
        for paper in papers:
            year = self._extract_year(paper)
            if year:
                year_counts[year] += 1

        if not year_counts:
            return {"error": "No year data available"}

        # 按年份排序
        sorted_years = sorted(year_counts.keys(), reverse=True)
        trend_data = [
            {"year": year, "count": count}
            for year, count in zip(sorted_years, [year_counts[y] for y in sorted_years])
        ]

        # 识别趋势
        if len(trend_data) >= 2:
            if trend_data[0]["count"] > trend_data[1]["count"] * 1.2:
                trend = "increasing"  # 增长趋势
            elif trend_data[0]["count"] < trend_data[1]["count"] * 0.8:
                trend = "decreasing"  # 下降趋势
            else:
                trend = "stable"  # 稳定
        else:
            trend = "insufficient_data"

        return {
            "year_distribution": trend_data,
            "trend": trend,
            "total_years": len(year_counts),
            "year_range": f"{min(year_counts.keys())}-{max(year_counts.keys())}"
        }

    def _analyze_source_trend(self, papers: List[Dict]) -> Dict[str, Any]:
        """分析数据源使用趋势"""
        source_counts = Counter()
        for paper in papers:
            source = paper.get("source", "Unknown")
            source_counts[source] += 1

        return {
            "source_distribution": [
                {"source": source, "count": count, "percentage": f"{count/len(papers)*100:.1f}%"}
                for source, count in source_counts.most_common()
            ],
            "primary_source": source_counts.most_common(1)[0] if source_counts else "Unknown",
            "total_papers": len(papers)
        }

    def _extract_hot_topics(self, papers: List[Dict]) -> List[Dict[str, Any]]:
        """提取研究热点（高频关键词）"""
        all_keywords = []

        for paper in papers:
            # 从标题提取关键词
            title = paper.get("title", "")
            if title:
                # 分词并过滤
                words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
                all_keywords.extend([w for w in words if w not in self.stop_words])

            # 从摘要提取关键词
            abstract = paper.get("abstract", "") or paper.get("summary", "")
            if abstract:
                words = re.findall(r'\b[a-zA-Z]{3,}\b', abstract.lower())
                all_keywords.extend([w for w in words if w not in self.stop_words])

        # 统计关键词频率
        keyword_counts = Counter(all_keywords)

        # 只保留出现频率>=2的关键词
        hot_keywords = [
            {"keyword": word, "frequency": count}
            for word, count in keyword_counts.items()
            if count >= 2
        ]

        # 排序并取前15个
        hot_keywords = sorted(hot_keywords, key=lambda x: x["frequency"], reverse=True)[:15]

        return hot_keywords

    def _analyze_citations(self, papers: List[Dict]) -> Dict[str, Any]:
        """分析引用量分布"""
        citations = []
        for paper in papers:
            citation_count = paper.get("citationCount", 0)
            if citation_count > 0:
                citations.append(citation_count)

        if not citations:
            return {"note": "No citation data available"}

        # 分段统计
        ranges = {
            "high_impact": sum(1 for c in citations if c >= 100),
            "moderate_impact": sum(1 for c in citations if 50 <= c < 100),
            "emerging": sum(1 for c in citations if c < 50)
        }

        return {
            "total_papers_with_citations": len(citations),
            "average_citations": sum(citations) / len(citations),
            "max_citations": max(citations),
            "impact_ranges": ranges,
            "citation_distribution": [
                {"range": "100+", "count": ranges["high_impact"]},
                {"range": "50-99", "count": ranges["moderate_impact"]},
                {"range": "1-49", "count": ranges["emerging"]}
            ]
        }

    def _analyze_venue_trend(self, papers: List[Dict]) -> Dict[str, Any]:
        """分析发表趋势（顶级期刊）"""
        venue_counts = Counter()
        top_venues = []

        for paper in papers:
            journal = paper.get("journal", "")
            if journal:
                venue_counts[journal] += 1

        # 只保留出现2次及以上的期刊
        for venue, count in venue_counts.items():
            if count >= 2:
                top_venues.append({"venue": venue, "count": count})

        # 按发表数量排序
        top_venues = sorted(top_venues, key=lambda x: x["count"], reverse=True)[:10]

        return {
            "top_venues": top_venues,
            "total_unique_venues": len(venue_counts)
        }

    def _generate_trend_insights(self, year_trend, source_trend, hot_topics,
                                citation_analysis, venue_trend) -> List[str]:
        """生成综合趋势洞察"""
        insights = []

        # 年份趋势洞察
        if year_trend.get("trend") == "increasing":
            insights.append("📈 该领域研究活跃度呈上升趋势，近年来发文量持续增长")
        elif year_trend.get("trend") == "decreasing":
            insights.append("📉 该领域研究活跃度呈下降趋势，可能进入成熟期或转向其他领域")

        # 热点主题洞察
        if hot_topics:
            top_3 = hot_topics[:3]
            keywords = ", ".join([t["keyword"] for t in top_3])
            insights.append(f"🔥 研究热点：{keywords}（出现频率最高）")

        # 引用量洞察
        if citation_analysis.get("average_citations", 0) > 50:
            insights.append("⭐ 该领域研究影响力较高，平均被引量超过50次")

        # 数据源洞察
        primary = source_trend.get("primary_source", "")
        if primary == "arXiv":
            insights.append("📝 arXiv预印本占主导，说明该领域研究更新快速，前沿性较强")

        return insights

    def _identify_time_gaps(self, papers: List[Dict]) -> List[Dict]:
        """识别时间缺口（发文量少的年份）"""
        year_counts = Counter()
        for paper in papers:
            year = self._extract_year(paper)
            if year:
                year_counts[year] += 1

        if not year_counts:
            return []

        years = sorted(year_counts.keys())
        avg_count = sum(year_counts.values()) / len(year_counts)

        # 识别发文量低于平均值的年份
        gaps = []
        for year in years:
            count = year_counts[year]
            if count < avg_count * 0.7:  # 低于平均值70%
                gaps.append({
                    "year": year,
                    "count": count,
                    "gap": avg_count - count,
                    "percentage_below_average": f"{(1 - count/avg_count)*100:.0f}%"
                })

        return gaps

    def _identify_topic_gaps(self, papers: List[Dict]) -> List[Dict]:
        """识别主题缺口（研究较少的方向）"""
        # 简化版本：基于标题关键词识别
        topic_clusters = {}

        for paper in papers:
            title = paper.get("title", "").lower()
            # 提取主题词（简化版）
            if "machine learning" in title:
                topic = "Machine Learning"
            elif "deep learning" in title:
                topic = "Deep Learning"
            elif "neural network" in title:
                topic = "Neural Network"
            elif "statistical" in title or "statistics" in title:
                topic = "Statistics"
            elif "bayesian" in title:
                topic = "Bayesian Methods"
            elif "optimization" in title:
                topic = "Optimization"
            else:
                continue

            if topic not in topic_clusters:
                topic_clusters[topic] = []
            topic_clusters[topic].append(paper)

        # 识别论文数量少的主题（潜在缺口）
        topic_counts = {topic: len(ps) for topic, ps in topic_clusters.items()}

        if topic_counts:
            avg_count = sum(topic_counts.values()) / len(topic_counts)
            gaps = []
            for topic, count in topic_counts.items():
                if count < avg_count * 0.5:  # 低于平均值50%
                    gaps.append({
                        "topic": topic,
                        "count": count,
                        "opportunity_level": "high" if count < avg_count * 0.3 else "moderate"
                    })

            return sorted(gaps, key=lambda x: x["count"])

        return []

    def _identify_method_gaps(self, papers: List[Dict]) -> List[Dict]:
        """识别研究方法缺口"""
        # 从标题和摘要中识别研究方法
        method_keywords = {
            "experimental": ["experiment", "experimental", "empirical", "trial"],
            "theoretical": ["theory", "theoretical", "mathematical", "analytical"],
            "simulation": ["simulation", "simulated", "computational", "model"],
            "survey": ["survey", "review", "overview", "meta-analysis"]
        }

        method_counts = {method: 0 for method in method_keywords.keys()}

        for paper in papers:
            text = (paper.get("title", "") + " " +
                   (paper.get("abstract", "") or paper.get("summary", ""))).lower()

            for method, keywords in method_keywords.items():
                if any(kw in text for kw in keywords):
                    method_counts[method] += 1
                    break

        # 识别使用较少的方法（潜在缺口）
        if sum(method_counts.values()) > 0:
            total = sum(method_counts.values())
            gaps = []
            for method, count in method_counts.items():
                if count == 0 or count / total < 0.1:  # 未使用或占比<10%
                    gaps.append({
                        "method": method,
                        "count": count,
                        "opportunity": "high" if count == 0 else "moderate"
                    })

            return gaps

        return []

    def _identify_interdisciplinary_opportunities(self, papers: List[Dict]) -> List[str]:
        """识别跨学科研究机会"""
        # 简化版本：识别论文中出现的跨学科关键词组合
        interdisciplinary_pairs = [
            ("computer science", "biology"),
            ("machine learning", "healthcare"),
            ("statistics", "economics"),
            ("neural networks", "physics"),
            ("optimization", "social science"),
            ("deep learning", "environment"),
            ("ai", "ethics")
        ]

        opportunities = []

        for pair in interdisciplinary_pairs:
            pair_count = 0
            for paper in papers:
                text = (paper.get("title", "") + " " +
                       (paper.get("abstract", "") or paper.get("summary", ""))).lower()

                if all(term in text for term in pair):
                    pair_count += 1

            if pair_count > 0:
                opportunity_text = f"{pair[0]} + {pair[1]}: {pair_count} papers"
                opportunities.append(opportunity_text)

        return opportunities

    def _generate_gap_insights(self, time_gaps, topic_gaps, method_gaps,
                             interdisciplinary_opportunities) -> List[str]:
        """生成缺口分析洞察"""
        insights = []

        if time_gaps:
            gap_years = ", ".join([str(g["year"]) for g in time_gaps[:3]])
            insights.append(f"⏰ 时间缺口：{gap_years}年发文量相对较少，可能是研究低谷期")

        if topic_gaps:
            gap_topics = ", ".join([g["topic"] for g in topic_gaps[:3]])
            insights.append(f"🔍 主题缺口：{gap_topics}等方向研究较少，存在研究空白")

        if method_gaps:
            gap_methods = ", ".join([g["method"] for g in method_gaps[:3]])
            insights.append(f"🔬 方法缺口：{gap_methods}等方法应用较少，可以尝试")

        if interdisciplinary_opportunities:
            insights.append(f"🔗 跨学科机会：{interdisciplinary_opportunities[0]}")

        return insights

    def _extract_year(self, paper: Dict) -> Optional[int]:
        """提取论文年份"""
        # 尝试多个字段
        year_fields = ["year", "publicationDate", "published", "pubDate"]

        for field in year_fields:
            if field in paper and paper[field]:
                value = str(paper[field])
                # 提取4位年份
                year_match = re.search(r'(\d{4})', value)
                if year_match:
                    return int(year_match.group(1))

        return None


if __name__ == "__main__":
    # 测试代码
    analyzer = ResearchAnalyzer()

    test_papers = [
        {"title": "Deep Learning for Medical Image Analysis", "year": "2025", "source": "arXiv", "journal": "Medical AI", "citationCount": 120},
        {"title": "Statistical Methods in Neural Networks", "year": "2024", "source": "arXiv", "journal": "JASA", "citationCount": 80},
        {"title": "Bayesian Optimization", "year": "2025", "source": "CrossRef", "journal": "NeurIPS", "citationCount": 150},
    ]

    trends = analyzer.analyze_research_trends(test_papers)
    gaps = analyzer.analyze_research_gaps(test_papers)

    print("=== Research Trends ===")
    print(f"Trend: {trends.get('year_trend', {}).get('trend')}")
    print(f"Hot Topics: {[t['keyword'] for t in trends.get('hot_topics', [])[:3]]}")

    print("\n=== Research Gaps ===")
    print(f"Time Gaps: {[g['year'] for g in gaps.get('time_gaps', [])[:3]]}")
    print(f"Topic Gaps: {[g['topic'] for g in gaps.get('topic_gaps', [])[:3]]}")
