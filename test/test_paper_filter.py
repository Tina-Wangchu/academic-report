"""
测试 paper_filter.py 模块（模块3）
覆盖：优先级评分、质量过滤、优先级排序（含 tie-breaker）、
      热点聚类（已知主题 + 兜底聚类 + 排序）、热点主题介绍生成。
"""

import pytest
import sys
import os

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-scholar', 'scripts'))

from utils import Paper, SearchIntent
from paper_filter import PaperFilter


# ---------------------------------------------------------------------- #
# 测试夹具
# ---------------------------------------------------------------------- #

class FakeConfig:
    """可定假的配置管理器，保证筛选测试确定性（不依赖 ~/.hermes/config.yaml）"""

    def __init__(self, include_preprints=True, min_citation_count=0,
                 filter_highly_cited=False, highly_cited_threshold=100,
                 sci_ei_only=False):
        self._include_preprints = include_preprints
        self._min_citation_count = min_citation_count
        self._filter_highly_cited = filter_highly_cited
        self._highly_cited_threshold = highly_cited_threshold
        self._sci_ei_only = sci_ei_only

    def is_include_preprints(self):
        return self._include_preprints

    def get_min_citation_count(self):
        return self._min_citation_count

    def is_filter_highly_cited(self):
        return self._filter_highly_cited

    def get_highly_cited_threshold(self):
        return self._highly_cited_threshold

    def is_sci_ei_only(self):
        return self._sci_ei_only


def _make_paper(title, venue, year, citation_count, venue_type,
                abstract="", keywords=None, doi=""):
    """构造一篇 Paper（其他字段给合理默认）"""
    return Paper(
        title=title,
        authors=["Author A", "Author B"],
        venue=venue,
        year=year,
        doi=doi,
        abstract=abstract or f"This paper discusses {title}.",
        keywords=keywords or [],
        citation_count=citation_count,
        venue_type=venue_type,
        ranking="普通",
        url="",
        source="test",
    )


def _make_intent(filters=None):
    return SearchIntent(
        query="test",
        keywords=[],
        research_field="cs",
        language="bilingual",
        max_results=50,
        filters=filters or {},
    )


@pytest.fixture
def filter_with_default_config():
    """默认配置（含预印本、无最小引用量）的 PaperFilter"""
    pf = PaperFilter()
    pf.config = FakeConfig()
    return pf


# ---------------------------------------------------------------------- #
# 优先级评分
# ---------------------------------------------------------------------- #

class TestPriorityScore:
    """测试 _priority_score 评分规则"""

    def test_highly_cited_top_journal_scores_highest(self, filter_with_default_config):
        pf = filter_with_default_config
        # 高被引(≥100) + 顶刊 + 引用加分
        p = _make_paper("X", "Nature", 2024, 200, "journal")
        # 100(高被引) + 90(顶刊) + min(200,50)=50  => 240
        assert pf._priority_score(p) == 240

    def test_top_conference_score(self, filter_with_default_config):
        pf = filter_with_default_config
        p = _make_paper("X", "NeurIPS", 2024, 60, "conference")
        # 50(≥50) + 80(顶会) + min(60,50)=50  => 180
        assert pf._priority_score(p) == 180

    def test_sci_ei_journal_score(self, filter_with_default_config):
        pf = filter_with_default_config
        p = _make_paper("X", "IEEE Transactions on X", 2023, 10, "journal")
        # 0 + 70(SCI/EI) + 10  => 80
        assert pf._priority_score(p) == 80

    def test_plain_journal_score(self, filter_with_default_config):
        pf = filter_with_default_config
        p = _make_paper("X", "Some Journal", 2023, 5, "journal")
        # 0 + 50(普通期刊) + 5  => 55
        assert pf._priority_score(p) == 55

    def test_preprint_score(self, filter_with_default_config):
        pf = filter_with_default_config
        p = _make_paper("X", "arXiv", 2025, 0, "preprint")
        # 0 + 30(预印本) + 0  => 30
        assert pf._priority_score(p) == 30

    def test_highly_cited_threshold_boundary(self, filter_with_default_config):
        pf = filter_with_default_config
        # 恰好 100 引用应进入高被引分层
        p = _make_paper("X", "arXiv", 2025, 100, "preprint")
        # 100 + 30 + min(100,50)=50  => 180
        assert pf._priority_score(p) == 180

    def test_latest_research_recency_bonus(self, filter_with_default_config):
        """latest_research=True：近 2 年论文 +40，老论文不加分（不再是死特性）"""
        pf = filter_with_default_config
        recent = _make_paper("Recent", "arXiv", 2026, 0, "preprint")   # base 30
        old = _make_paper("Old", "arXiv", 2020, 0, "preprint")         # base 30
        assert pf._priority_score(recent, latest=True) == 30 + 40
        assert pf._priority_score(old, latest=True) == 30              # 老论文无加分
        # 端到端：latest 意图下，近期 preprint(70) 排到老 journal(50) 前面
        old_journal = _make_paper("OldJ", "Some Journal", 2020, 0, "journal")  # 50
        intent = SearchIntent(query="x", keywords=[], research_field="x",
                              language="bilingual", filters={"latest_research": True})
        out = pf.filter_and_sort([old_journal, recent], intent)
        assert out[0].title == "Recent"


# ---------------------------------------------------------------------- #
# 优先级排序（含 tie-breaker）
# ---------------------------------------------------------------------- #

class TestSortByPriority:
    """测试 _sort_by_priority"""

    def test_orders_by_score_desc(self, filter_with_default_config):
        pf = filter_with_default_config
        preprint = _make_paper("preprint", "arXiv", 2025, 0, "preprint")
        top = _make_paper("top", "NeurIPS", 2024, 60, "conference")
        nature = _make_paper("nature", "Nature", 2024, 200, "journal")

        result = pf._sort_by_priority([preprint, top, nature])
        assert result[0].title == "nature"
        assert result[1].title == "top"
        assert result[2].title == "preprint"

    def test_tie_breaker_by_year_desc(self, filter_with_default_config):
        """同分时按发表年份降序（新者优先）"""
        pf = filter_with_default_config
        older = _make_paper("older", "arXiv", 2022, 0, "preprint")
        newer = _make_paper("newer", "arXiv", 2025, 0, "preprint")
        # 两者得分相同（均为 30）
        result = pf._sort_by_priority([older, newer])
        assert result[0].title == "newer"
        assert result[1].title == "older"


# ---------------------------------------------------------------------- #
# 质量过滤
# ---------------------------------------------------------------------- #

class TestTimeFilter:
    """测试 _filter_by_time（年份级时间安全网）"""

    def test_filters_outside_range(self, filter_with_default_config):
        from datetime import datetime
        pf = filter_with_default_config
        papers = [
            _make_paper("old", "NeurIPS", 2018, 100, "conference"),
            _make_paper("in1", "NeurIPS", 2023, 100, "conference"),
            _make_paper("in2", "NeurIPS", 2025, 100, "conference"),
            _make_paper("future", "NeurIPS", 2027, 100, "conference"),
        ]
        intent = SearchIntent(query="t", keywords=[], research_field="cs",
                              language="en",
                              start_date=datetime(2023, 1, 1),
                              end_date=datetime(2025, 12, 31), max_results=50)
        result = pf.filter_and_sort(papers, intent)
        years = {p.year for p in result}
        assert 2018 not in years      # 早于范围，剔除
        assert 2027 not in years      # 晚于范围，剔除
        assert {2023, 2025}.issubset(years)

    def test_missing_year_kept(self, filter_with_default_config):
        """year<=0（缺失）的论文应保留，不因时间过滤被误删"""
        from datetime import datetime
        pf = filter_with_default_config
        papers = [
            _make_paper("unknown", "NeurIPS", 0, 100, "conference"),
        ]
        intent = SearchIntent(query="t", keywords=[], research_field="cs",
                              language="en",
                              start_date=datetime(2023, 1, 1),
                              end_date=datetime(2025, 12, 31), max_results=50)
        result = pf.filter_and_sort(papers, intent)
        assert len(result) == 1

    def test_no_dates_passthrough(self, filter_with_default_config):
        """intent 无 start/end_date 时不做时间过滤"""
        pf = filter_with_default_config
        papers = [_make_paper("a", "NeurIPS", 2010, 100, "conference")]
        result = pf.filter_and_sort(papers, _make_intent())
        assert len(result) == 1


class TestQualityFilters:
    """测试 _apply_quality_filters / filter_and_sort"""

    def test_highly_cited_filter_via_intent(self, filter_with_default_config):
        pf = filter_with_default_config
        papers = [
            _make_paper("low", "arXiv", 2024, 10, "preprint"),
            _make_paper("high", "Nature", 2024, 200, "journal"),
        ]
        intent = _make_intent(filters={"highly_cited": True})
        result = pf.filter_and_sort(papers, intent)
        assert len(result) == 1
        assert result[0].title == "high"

    def test_sci_ei_filter_via_intent(self, filter_with_default_config):
        pf = filter_with_default_config
        papers = [
            _make_paper("plain", "Some Journal", 2024, 5, "journal"),
            _make_paper("ieee", "IEEE Transactions", 2024, 5, "journal"),
        ]
        intent = _make_intent(filters={"sci_ei": True})
        result = pf.filter_and_sort(papers, intent)
        assert len(result) == 1
        assert result[0].title == "ieee"

    def test_core_journal_filter_via_intent(self, filter_with_default_config):
        pf = filter_with_default_config
        papers = [
            _make_paper("plain", "Some Journal", 2024, 5, "journal"),
            _make_paper("nature", "Nature", 2024, 5, "journal"),
        ]
        intent = _make_intent(filters={"core_journal": True})
        result = pf.filter_and_sort(papers, intent)
        assert len(result) == 1
        assert result[0].title == "nature"

    def test_preprint_exclusion_via_config(self):
        """配置 is_include_preprints=False 时剔除预印本"""
        pf = PaperFilter()
        pf.config = FakeConfig(include_preprints=False)
        papers = [
            _make_paper("preprint", "arXiv", 2024, 0, "preprint"),
            _make_paper("journal", "Some Journal", 2024, 5, "journal"),
        ]
        result = pf.filter_and_sort(papers, _make_intent())
        assert len(result) == 1
        assert result[0].venue_type != "preprint"

    def test_min_citation_via_config(self):
        """配置 min_citation_count 过滤低引用论文"""
        pf = PaperFilter()
        pf.config = FakeConfig(min_citation_count=50)
        papers = [
            _make_paper("low", "NeurIPS", 2024, 10, "conference"),
            _make_paper("high", "NeurIPS", 2024, 80, "conference"),
        ]
        result = pf.filter_and_sort(papers, _make_intent())
        assert len(result) == 1
        assert result[0].citation_count >= 50

    def test_limit_truncation(self, filter_with_default_config):
        pf = filter_with_default_config
        papers = [
            _make_paper(f"p{i}", "arXiv", 2024, i, "preprint")
            for i in range(10)
        ]
        result = pf.filter_and_sort(papers, _make_intent(), limit=3)
        assert len(result) == 3

    def test_empty_title_removed(self, filter_with_default_config):
        pf = filter_with_default_config
        papers = [
            _make_paper("", "arXiv", 2024, 0, "preprint"),
            _make_paper("real", "arXiv", 2024, 0, "preprint"),
        ]
        result = pf.filter_and_sort(papers, _make_intent())
        titles = [p.title for p in result]
        assert "" not in titles
        assert "real" in titles


# ---------------------------------------------------------------------- #
# 热点聚类
# ---------------------------------------------------------------------- #

class TestClassifyByTopic:
    """测试 classify_by_topic（含 ≥2 收敛规则，报告格式设计.md §10.3）"""

    def test_known_topic_grouping(self, filter_with_default_config):
        pf = filter_with_default_config
        cv1 = _make_paper("cv1", "CVPR", 2024, 50, "conference",
                          abstract="image recognition and visual detection",
                          keywords=["vision"])
        cv2 = _make_paper("cv2", "CVPR", 2024, 50, "conference",
                          abstract="image segmentation visual",
                          keywords=["vision"])
        nlp1 = _make_paper("nlp1", "ACL", 2024, 50, "conference",
                           abstract="transformer for natural language processing",
                           keywords=["nlp"])
        nlp2 = _make_paper("nlp2", "ACL", 2024, 50, "conference",
                           abstract="natural language generation",
                           keywords=["nlp"])
        result = pf.classify_by_topic([cv1, cv2, nlp1, nlp2])
        # 每主题 ≥2 篇 → 两个热点
        assert len(result) == 2
        assert "计算机视觉" in result
        assert "自然语言处理" in result

    def test_fallback_clustering_for_non_ai_field(self, filter_with_default_config):
        """非 AI 学科按关键词频次兜底聚类；≥2 共享才成热点"""
        pf = filter_with_default_config
        p1 = _make_paper("bayesian inference", "Annals of Statistics", 2023,
                         30, "journal",
                         abstract="bayesian inference for statistical models")
        p2 = _make_paper("more bayesian methods", "JRSS", 2023, 20, "journal",
                         abstract="bayesian methods in regression")
        result = pf.classify_by_topic([p1, p2], topic_hint="bayesian statistics")
        # 两篇共享 "bayesian" → 一个热点（非「其他」）
        assert len(result) == 1
        assert "Bayesian" in result

    def test_singleton_consolidated_into_misc(self, filter_with_default_config):
        """单篇桶（含已知主题单篇误分类）并入「其他」"""
        pf = filter_with_default_config
        # 1 篇 CV + 1 篇 NLP + 1 篇无关 → 都单篇 → 全进「其他」
        cv = _make_paper("cv", "CVPR", 2024, 50, "conference",
                         abstract="image recognition visual", keywords=["vision"])
        nlp = _make_paper("nlp", "ACL", 2024, 50, "conference",
                          abstract="natural language", keywords=["nlp"])
        other = _make_paper("other", "arXiv", 2024, 0, "preprint",
                            abstract="a preprint about xyzqqq unique")
        result = pf.classify_by_topic([cv, nlp, other])
        assert list(result.keys()) == ["其他"]
        assert len(result["其他"]) == 3

    def test_hotspots_ordered_by_weight(self, filter_with_default_config):
        """热点按聚合优先级降序：高权重热点排在前；「其他」恒置末尾"""
        pf = filter_with_default_config
        heavy1 = _make_paper("h1", "Nature", 2024, 300, "journal",
                             abstract="image recognition visual detection",
                             keywords=["vision"])
        heavy2 = _make_paper("h2", "CVPR", 2024, 200, "conference",
                             abstract="image segmentation visual",
                             keywords=["vision"])
        light1 = _make_paper("l1", "arXiv", 2024, 0, "preprint",
                             abstract="a preprint about xyzqqq one")
        light2 = _make_paper("l2", "arXiv", 2024, 0, "preprint",
                             abstract="another preprint xyzqqq two")
        result = pf.classify_by_topic([light1, heavy1, heavy2, light2])
        keys = list(result.keys())
        # 高权重 CV 热点在前
        assert "计算机视觉" in keys[0]
        # 「其他」恒置末尾
        assert keys[-1] == "其他"
        assert heavy1 in result["计算机视觉"]

    def test_misc_always_last(self, filter_with_default_config):
        """「其他」即便权重高也排在最后"""
        pf = filter_with_default_config
        # 2 篇低分预印本（→其他，权重低）+ 2 篇 CV（权重高）
        misc1 = _make_paper("m1", "arXiv", 2024, 0, "preprint",
                            abstract="xyzqqq alpha")
        misc2 = _make_paper("m2", "arXiv", 2024, 0, "preprint",
                            abstract="xyzqqq beta")
        cv1 = _make_paper("c1", "CVPR", 2024, 50, "conference",
                          abstract="image visual", keywords=["vision"])
        cv2 = _make_paper("c2", "CVPR", 2024, 50, "conference",
                          abstract="image detection", keywords=["vision"])
        result = pf.classify_by_topic([misc1, misc2, cv1, cv2])
        assert list(result.keys())[-1] == "其他"


# ---------------------------------------------------------------------- #
# 热点主题介绍
# ---------------------------------------------------------------------- #

class TestGenerateHotspotIntro:
    """测试 generate_hotspot_intro（Option B 从 report_generator 迁入）"""

    def test_mentions_count_and_representative(self, filter_with_default_config):
        pf = filter_with_default_config
        papers = [
            _make_paper("low", "arXiv", 2024, 5, "preprint",
                        keywords=["diffusion"]),
            _make_paper("high", "NeurIPS", 2024, 200, "conference",
                        keywords=["diffusion", "sampling"]),
        ]
        intro = pf.generate_hotspot_intro("生成模型", papers)
        assert "2" in intro                      # 收录篇数
        assert "生成模型" in intro                # 热点名
        assert "high" in intro                    # 代表性论文（被引最高）

    def test_empty_papers(self, filter_with_default_config):
        pf = filter_with_default_config
        intro = pf.generate_hotspot_intro("空热点", [])
        assert "暂无论文" in intro

    def test_includes_common_keywords(self, filter_with_default_config):
        pf = filter_with_default_config
        papers = [
            _make_paper("a", "NeurIPS", 2024, 50, "conference",
                        keywords=["diffusion", "sampling"]),
            _make_paper("b", "NeurIPS", 2024, 50, "conference",
                        keywords=["diffusion"]),
        ]
        intro = pf.generate_hotspot_intro("生成模型", papers)
        # diffusion 是高频关键词，应在介绍中出现
        assert "diffusion" in intro.lower()


# ---------------------------------------------------------------------- #
# 集成
# ---------------------------------------------------------------------- #

class TestIntegration:
    """端到端：筛选 → 排序 → 聚类 → 介绍"""

    def test_full_pipeline(self, filter_with_default_config):
        pf = filter_with_default_config
        papers = [
            _make_paper("cv-high", "Nature", 2024, 250, "journal",
                        abstract="image recognition visual detection",
                        keywords=["vision"]),
            _make_paper("nlp-mid", "ACL", 2023, 80, "conference",
                        abstract="transformer for natural language",
                        keywords=["nlp"]),
            _make_paper("preprint-low", "arXiv", 2025, 0, "preprint",
                        abstract="random preprint xyzqqq",
                        keywords=[]),
        ]
        intent = _make_intent()

        sorted_papers = pf.filter_and_sort(papers, intent)
        classified = pf.classify_by_topic(sorted_papers)

        # 排序后最高分论文在前
        assert sorted_papers[0].title == "cv-high"
        # 每个热点都能生成非空介绍
        for topic, group in classified.items():
            intro = pf.generate_hotspot_intro(topic, group)
            assert isinstance(intro, str) and len(intro) > 0
