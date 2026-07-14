"""
测试 paper_analyzer.py 模块（模块4）
覆盖：单篇信息提取、APA 引用、方向级整体分析、
      奠基性参考论文查找（纯排序逻辑 + 模拟网络 + 离线回退）。
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-scholar', 'scripts'))

from utils import Paper
from paper_analyzer import PaperAnalyzer, CitationFinder, Reference


# ---------------------------------------------------------------------- #
# 夹具
# ---------------------------------------------------------------------- #

class FakeRateLimiter:
    """始终放行的限流器"""

    def wait_if_needed(self, source):
        return True


def _make_paper(title="Test Paper", abstract="", year=2024,
                citation_count=10, keywords=None, doi="", authors=None):
    return Paper(
        title=title,
        authors=authors or ["Author A", "Author B"],
        venue="NeurIPS",
        year=year,
        doi=doi,
        abstract=abstract,
        keywords=keywords or [],
        citation_count=citation_count,
        venue_type="conference",
        ranking="顶会",
        url="",
        source="test",
    )


# 超长摘要（>1500 字符），用于触发「去填充」路径
LONG_ABSTRACT = (
    "Sampling from diffusion models is computationally expensive due to the "
    "iterative denoising process that requires hundreds of neural network "
    "evaluations, which limits their use in latency-sensitive applications. "
    "Many prior solvers attempt to accelerate this process but often suffer "
    "from noticeable quality degradation when the number of steps is small. "
    "We propose a novel high-order ODE solver for diffusion model sampling "
    "that substantially reduces the required number of denoising steps while "
    "preserving sample quality. Our formulation leverages a carefully designed "
    "trajectory and a high-order correction term derived from the score "
    "function to maintain fidelity. Several existing approaches require "
    "hundreds of steps and are prohibitively slow on large-scale models, "
    "restricting deployment in real-time interactive systems. We evaluate our "
    "method on the CIFAR-10 and ImageNet benchmarks and achieve high-quality "
    "sampling in only ten steps. Our method outperforms prior solvers and "
    "demonstrates strong results across multiple standard datasets and "
    "metrics. The proposed approach contributes a new theoretical perspective "
    "on trajectory design for diffusion solvers. We further provide a "
    "convergence analysis under standard regularity assumptions on the score "
    "function. In practice, the trade-off between sampling speed and sample "
    "quality remains a central challenge for deploying diffusion models in "
    "resource-constrained environments. A number of recent works have "
    "explored parallel sampling, distillation, and trajectory optimization "
    "as complementary directions. This work opens several promising avenues "
    "for future research in efficient generative modeling and real-time "
    "image synthesis."
)


@pytest.fixture
def analyzer():
    """注入不联网的 CitationFinder 的分析器"""
    return PaperAnalyzer(citation_finder=CitationFinder(rate_limiter=FakeRateLimiter()))


# ---------------------------------------------------------------------- #
# 单篇信息提取
# ---------------------------------------------------------------------- #

class TestExtraction:
    """测试单篇论文信息提取"""

    def test_extract_research_content_method_clause(self, analyzer):
        """研究内容应取含方法信号词的子句（we propose…），而非整段摘要"""
        p = _make_paper(
            abstract="Background is important. We propose a novel ODE solver "
                     "for sampling, and it achieves strong results."
        )
        out = analyzer._extract_research_content(p)
        assert "propose" in out.lower()
        assert "Background" not in out  # 不是首句背景

    def test_extract_research_content_empty(self, analyzer):
        p = _make_paper(abstract="")
        assert analyzer._extract_research_content(p) == ""

    def test_extract_innovations_finds_patterns_bilingual(self, analyzer):
        """创新点默认双语：含中英标签"""
        p = _make_paper(
            abstract="We propose a novel method that outperforms baselines."
        )
        out = analyzer._extract_innovations(p)  # 默认 bilingual
        assert "新颖" in out              # 中文
        assert "outperform" in out.lower()  # 英文

    def test_extract_innovations_lang_en(self, analyzer):
        p = _make_paper(abstract="We propose a novel method.")
        assert analyzer._extract_innovations(p, lang="en") == \
            "proposes a novel method; proposes a new method/framework"

    def test_extract_innovations_lang_zh(self, analyzer):
        p = _make_paper(abstract="We propose a novel method.")
        out = analyzer._extract_innovations(p, lang="zh")
        assert "新颖" in out                      # 中文标签
        assert "propose" not in out.lower()       # 无英文

    def test_extract_innovations_default_derives_from_method(self, analyzer):
        """无信号词时从方法子句派生（不给空泛默认，§10.2）"""
        p = _make_paper(abstract="We develop a graph-based ranking algorithm.")
        out = analyzer._extract_innovations(p)  # 默认 bilingual
        assert "提出：" in out and "proposes:" in out
        assert "graph-based ranking" in out  # 落在真实方法上

    def test_extract_innovations_empty_when_no_abstract(self, analyzer):
        """无摘要时创新点留空（报告不渲染）"""
        p = _make_paper(abstract="")
        assert analyzer._extract_innovations(p) == ""

    def test_extract_conclusions_finds_marker(self, analyzer):
        p = _make_paper(
            abstract="We study X. Our results demonstrate strong gains. "
                     "More analysis."
        )
        out = analyzer._extract_conclusions(p)
        # 应取含 'demonstrate' 的那句
        assert "demonstrate" in out.lower()

    def test_extract_conclusions_empty(self, analyzer):
        p = _make_paper(abstract="")
        assert analyzer._extract_conclusions(p) == ""

    def test_research_content_distinct_from_conclusions(self, analyzer):
        """研究内容（方法子句）与结论（结果子句）应不同，避免与 Abstract 重复"""
        p = _make_paper(
            abstract="We propose a novel ODE solver for diffusion sampling, "
                     "and our method outperforms prior solvers on benchmarks."
        )
        research = analyzer._extract_research_content(p)
        conclusion = analyzer._extract_conclusions(p)
        assert research != conclusion
        assert "propose" in research.lower()
        assert "outperform" in conclusion.lower()

    def test_condense_short_abstract_full(self, analyzer):
        """短摘要（≤400 字符）直接全文，无省略号"""
        short = "We propose a small method. It works well."
        p = _make_paper(abstract=short)
        assert analyzer._condense_abstract(p) == short

    def test_condense_long_abstract_no_ellipsis(self, analyzer):
        """超长摘要（>1500 字符）去填充：含方法/结果句，无 mid-sentence 省略号"""
        p = _make_paper(abstract=LONG_ABSTRACT)
        condensed = analyzer._condense_abstract(p)
        assert len(LONG_ABSTRACT) > 1500         # 确实超长
        assert "..." not in condensed            # 无省略号
        assert condensed.endswith(".")           # 句边界结尾
        assert "propose" in condensed.lower()    # 含方法
        assert "outperform" in condensed.lower()  # 含结果
        assert len(condensed) < len(LONG_ABSTRACT)  # 剔除了填充句

    def test_condense_empty_abstract(self, analyzer):
        """无摘要 → 空（报告走占位）"""
        p = _make_paper(abstract="")
        assert analyzer._condense_abstract(p) == ""


# ---------------------------------------------------------------------- #
# AbstractSummarizer（分层：S2 tldr → 增强规则）
# ---------------------------------------------------------------------- #

class TestAbstractSummarizer:
    """测试 AbstractSummarizer（目标 200-300 字完整摘要）"""

    def test_summarize_prefers_full_abstract_over_tldr(self):
        """有正文摘要时优先用完整摘要（200-300 字），而非短 tldr"""
        from paper_analyzer import AbstractSummarizer
        p = _make_paper(abstract="We propose a novel method. It outperforms baselines.")
        p.tldr = "S2 TLDR summary."
        out = AbstractSummarizer().summarize(p)
        assert "propose a novel method" in out   # 用了完整摘要
        assert out != "S2 TLDR summary."         # 没用短 tldr

    def test_summarize_uses_tldr_when_abstract_missing(self):
        """正文摘要缺失时回退 S2 tldr"""
        from paper_analyzer import AbstractSummarizer
        p = _make_paper(abstract="")
        p.tldr = "S2 TLDR summary."
        assert AbstractSummarizer().summarize(p) == "S2 TLDR summary."

    def test_summarize_falls_back_to_rules_without_tldr(self):
        """无 tldr 时用完整去填充摘要"""
        from paper_analyzer import AbstractSummarizer
        p = _make_paper(abstract="We propose a novel method. It outperforms baselines on benchmark X.")
        out = AbstractSummarizer().summarize(p)
        assert out  # 非空
        assert "..." not in out

    def test_from_rules_keeps_full_when_within_target(self):
        """摘要 ≤ 上限时原样返回全文（200-300 字量级完整摘要）"""
        from paper_analyzer import AbstractSummarizer
        abs_text = ("We propose a novel ODE solver for diffusion model sampling. "
                    "Our method outperforms prior solvers on benchmarks.")
        p = _make_paper(abstract=abs_text)
        assert AbstractSummarizer()._from_rules(p) == abs_text

    def test_from_rules_drops_filler_when_overlong(self):
        """超长摘要剔除低信息填充句，保留方法/结果，无省略号"""
        from paper_analyzer import AbstractSummarizer
        p = _make_paper(abstract=LONG_ABSTRACT)
        assert len(p.abstract) > 1500                           # 确实超长
        out = AbstractSummarizer()._from_rules(p)
        assert "propose" in out.lower()                        # 方法句保留
        assert "outperform" in out.lower()                     # 结果句保留
        assert "benchmark" in out.lower()                      # 数据集句保留
        assert len(out) < len(p.abstract)                      # 剔除了填充句
        assert "..." not in out                                 # 无省略号
        assert out.endswith(".")                                # 句边界结尾

    def test_from_rules_empty(self):
        from paper_analyzer import AbstractSummarizer
        assert AbstractSummarizer()._from_rules(_make_paper(abstract="")) == ""

    def test_analyze_papers_populates_condensed_from_abstract(self, analyzer):
        """有摘要时 condensed_abstract 用完整摘要（而非 tldr）"""
        p = _make_paper(abstract="some abstract content here.")
        p.tldr = "TLDR from S2."
        analyzer.analyze_papers([p])
        assert p.condensed_abstract == "some abstract content here."

    def test_analyze_papers_uses_tldr_when_abstract_missing(self, analyzer):
        """摘要缺失时 condensed_abstract 回退 tldr"""
        p = _make_paper(abstract="")
        p.tldr = "TLDR from S2."
        analyzer.analyze_papers([p])
        assert p.condensed_abstract == "TLDR from S2."

    def test_split_sentences_protects_decimals(self):
        """小数点（如 95.6）不应被当作句边界"""
        sents = PaperAnalyzer._split_sentences(
            "Achieves 95.6% accuracy. It works well on CIFAR.")
        assert sents[0] == "Achieves 95.6% accuracy"
        assert sents[1] == "It works well on CIFAR"

    def test_infer_application(self, analyzer):
        p = _make_paper(
            title="Medical Image Diagnosis",
            abstract="a clinical tool for diagnosis",
        )
        out = analyzer._infer_application(p)
        assert "医疗健康" in out

    def test_infer_application_default(self, analyzer):
        p = _make_paper(title="Abstract Theory", abstract="pure math")
        assert analyzer._infer_application(p) == "通用研究"

    def test_analyze_single_paper_skips_when_filled(self, analyzer):
        p = _make_paper()
        p.research_content = "已有内容"
        p.innovations = "已有创新"
        result = analyzer._analyze_single_paper(p)
        assert result.research_content == "已有内容"  # 不被覆盖

    def test_analyze_papers_batch(self, analyzer):
        papers = [_make_paper(title=f"P{i}", abstract="novel approach")
                  for i in range(3)]
        result = analyzer.analyze_papers(papers)
        assert len(result) == 3
        assert all(p.research_content for p in result)


# ---------------------------------------------------------------------- #
# StructuredExtractor（四要素摘录）
# ---------------------------------------------------------------------- #

class TestStructuredExtractor:
    """测试 StructuredExtractor：从摘要摘录 解决的问题/现有方案/新方案/效果及局限"""

    def test_extracts_four_elements(self):
        """四要素均能从典型摘要中摘录到对应语段"""
        from paper_analyzer import StructuredExtractor
        p = _make_paper(abstract=(
            "Sampling from diffusion models is computationally expensive due to "
            "the iterative denoising process. Many prior solvers attempt to "
            "accelerate this process but suffer from quality degradation. "
            "We propose a novel high-order ODE solver for diffusion model "
            "sampling. We evaluate on the CIFAR-10 and ImageNet benchmarks and "
            "achieve high-quality sampling in 10 steps."
        ))
        out = StructuredExtractor().extract(p)
        assert "expensive" in out["problem"].lower()           # 解决的问题
        assert "prior" in out["existing_approaches"].lower()   # 现有方案
        assert "propose" in out["new_approach"].lower()        # 新方案
        assert ("benchmark" in out["results_limitations"].lower()
                or "achieve" in out["results_limitations"].lower())  # 效果
        for v in out.values():
            if v:
                assert v.endswith(".")                          # 句末标点

    def test_distinct_sentences_per_element(self):
        """新方案与现有方案应取不同句，不重复"""
        from paper_analyzer import StructuredExtractor
        p = _make_paper(abstract=(
            "Existing methods are slow and suffer from quality issues. "
            "We propose a fast solver. Our method outperforms baselines."
        ))
        out = StructuredExtractor().extract(p)
        assert out["new_approach"] != out["existing_approaches"]
        assert "propose" in out["new_approach"].lower()
        assert "existing" in out["existing_approaches"].lower()

    def test_results_include_limitation(self):
        """效果及局限可含结果句 + 局限句"""
        from paper_analyzer import StructuredExtractor
        p = _make_paper(abstract=(
            "We propose a method. It achieves strong results on benchmarks. "
            "However, the method still struggles with very large images."
        ))
        out = StructuredExtractor().extract(p)
        rl = out["results_limitations"].lower()
        assert "achieves" in rl or "struggles" in rl

    def test_empty_abstract(self):
        from paper_analyzer import StructuredExtractor
        out = StructuredExtractor().extract(_make_paper(abstract=""))
        assert out == {"problem": "", "existing_approaches": "",
                       "new_approach": "", "results_limitations": ""}

    def test_existing_falls_back_to_background(self):
        """无显式先前工作标记时，「已有方案」回退首句中性背景（既有理论/方法）"""
        from paper_analyzer import StructuredExtractor
        p = _make_paper(abstract=(
            "Diffusion models generate high-quality samples. "
            "We propose a faster solver. It outperforms baselines."
        ))
        out = StructuredExtractor().extract(p)
        # 首句是中性的既有理论描述 → 归入「已有方案」
        assert "diffusion models generate" in out["existing_approaches"].lower()

    def test_existing_catches_established_practice(self):
        """已有方案 = 已经存在的理论/方法（如 widely used 的做法）"""
        from paper_analyzer import StructuredExtractor
        p = _make_paper(abstract=(
            "Transformers are widely used for sequence modeling. "
            "However their attention is slow for long sequences. "
            "We propose a linear attention mechanism. It outperforms baselines."
        ))
        out = StructuredExtractor().extract(p)
        assert "transformers" in out["existing_approaches"].lower()
        assert "slow" in out["problem"].lower() or "attention" in out["problem"].lower()

    def test_new_approach_captures_insight_or_finding(self):
        """新方案 = 本文创新内容（含发现/洞见/理论，不限于「方法」）"""
        from paper_analyzer import StructuredExtractor
        p = _make_paper(abstract=(
            "Scaling laws govern model training. "
            "We show that loss follows a power law with compute. "
            "This insight is validated on multiple benchmarks."
        ))
        out = StructuredExtractor().extract(p)
        assert ("power law" in out["new_approach"].lower()
                or "we show" in out["new_approach"].lower())

    def test_new_not_swapped_with_results_on_messy_abstract(self):
        """摘要结构乱时，被动提出的新方案不应被背景句/结果对比句抢走"""
        from paper_analyzer import StructuredExtractor
        p = _make_paper(abstract=(
            "In this age of Industry 4.0 fruit sorting is an important part "
            "wherein this work plays a vital role. Deep learning models offer "
            "promise for automating disease identification but encounter obstacles "
            "such as overfitting. Significantly our model demonstrates reduced "
            "storage compared to existing deep CNN architectures. In this study "
            "a solution for detection and classification of apple fruit diseases "
            "is proposed and experimentally validated."
        ))
        out = StructuredExtractor().extract(p)
        # 新方案 = "a solution ... is proposed"，不是背景 "Industry 4.0 / this work"
        assert ("is proposed" in out["new_approach"].lower()
                or "solution" in out["new_approach"].lower())
        assert "industry" not in out["new_approach"].lower()
        # 结果 = "our model demonstrates reduced storage compared to existing CNN"
        assert ("storage" in out["results_limitations"].lower()
                or "demonstrates" in out["results_limitations"].lower())

    def test_analyze_papers_populates_structured(self, analyzer):
        """analyze_papers 填充四要素字段"""
        p = _make_paper(abstract="We propose a novel method. It outperforms baselines on benchmarks.")
        analyzer.analyze_papers([p])
        assert p.new_approach                      # 新方案非空
        assert p.results_limitations               # 效果非空


# ---------------------------------------------------------------------- #
# APA 引用
# ---------------------------------------------------------------------- #

class TestFormatCitations:
    """测试 APA 7th 引用生成"""

    def test_format_citations_includes_authors_year_doi(self, analyzer):
        p = _make_paper(title="My Paper", authors=["Smith J", "Lee K"],
                        year=2024, doi="10.1234/test")
        cits = analyzer.format_citations([p])
        assert len(cits) == 1
        cit = cits[0]
        assert "Smith J" in cit
        assert "2024" in cit
        assert "10.1234/test" in cit

    def test_format_citations_batch(self, analyzer):
        papers = [_make_paper(title=f"P{i}") for i in range(3)]
        assert len(analyzer.format_citations(papers)) == 3


# ---------------------------------------------------------------------- #
# 方向级整体分析
# ---------------------------------------------------------------------- #

class TestOverallAnalysis:
    """测试 generate_overall_analysis（Option B 迁入）"""

    def test_mentions_topic_count_and_representative(self, analyzer):
        papers = [
            _make_paper(title="Low-Cited", year=2024, citation_count=5,
                        keywords=["diffusion"]),
            _make_paper(title="High-Cited", year=2023, citation_count=300,
                        keywords=["diffusion", "sampling"]),
        ]
        out = analyzer.generate_overall_analysis("扩散模型", papers)
        assert "扩散模型" in out
        assert "2" in out                 # 收录篇数
        assert "High-Cited" in out        # 代表性（最高被引）

    def test_empty(self, analyzer):
        out = analyzer.generate_overall_analysis("空方向", [])
        assert "暂无" in out

    def test_stage_mature_when_wide_span(self, analyzer):
        """年份跨度 ≥4 → 成熟阶段"""
        papers = [
            _make_paper(title="Old", year=2019, citation_count=10),
            _make_paper(title="New", year=2024, citation_count=10),
        ]
        out = analyzer.generate_overall_analysis("X", papers)
        assert "成熟" in out

    def test_stage_emerging_when_narrow_span(self, analyzer):
        """年份跨度 <2 → 新兴/近期"""
        papers = [
            _make_paper(title="A", year=2024, citation_count=10),
            _make_paper(title="B", year=2024, citation_count=20),
        ]
        out = analyzer.generate_overall_analysis("X", papers)
        assert "新兴" in out or "近期" in out

    def test_includes_common_keywords(self, analyzer):
        papers = [
            _make_paper(title="A", keywords=["diffusion", "sampling"]),
            _make_paper(title="B", keywords=["diffusion"]),
        ]
        out = analyzer.generate_overall_analysis("X", papers)
        assert "diffusion" in out


# ---------------------------------------------------------------------- #
# CitationFinder 纯排序逻辑
# ---------------------------------------------------------------------- #

class TestRankReferences:
    """测试 CitationFinder.rank_references（纯函数，不联网）"""

    def test_ranks_by_hotspot_citation_count(self):
        cf = CitationFinder(rate_limiter=FakeRateLimiter())
        # ref_shared 被 2 篇源论文引用；ref_solo 只被 1 篇引用
        raw = [
            (0, Reference(title="Shared Classic", year=2015,
                          citation_count=5000, paper_id="s1")),
            (1, Reference(title="Shared Classic", year=2015,
                          citation_count=5000, paper_id="s1")),
            (0, Reference(title="Solo Ref", year=2018,
                          citation_count=200, paper_id="s2")),
        ]
        out = cf.rank_references(raw, hotspot_titles=set(), top_n=3)
        assert len(out) == 2
        assert "Shared Classic" in out[0]      # 被多篇引用 → 排前
        assert "Solo Ref" in out[1]            # 只被 1 篇引用 → 排后

    def test_excludes_hotspot_members(self):
        """热点自身收录的论文不应作为奠基参考"""
        cf = CitationFinder(rate_limiter=FakeRateLimiter())
        raw = [
            (0, Reference(title="Hotspot Member", year=2024,
                          citation_count=10, paper_id="h1")),
            (0, Reference(title="Real Classic", year=2010,
                          citation_count=8000, paper_id="c1")),
        ]
        out = cf.rank_references(raw, hotspot_titles={"hotspot member"},
                                 top_n=3)
        joined = " ".join(out)
        assert "Real Classic" in joined
        assert "Hotspot Member" not in joined

    def test_formats_with_citation_note(self):
        cf = CitationFinder(rate_limiter=FakeRateLimiter())
        raw = [
            (0, Reference(title="Influential Old", authors=["Vaswani"],
                          year=2017, citation_count=90000,
                          paper_id="v1", influential=True)),
        ]
        out = cf.rank_references(raw, hotspot_titles=set(), top_n=1)
        assert len(out) == 1
        assert "Vaswani" in out[0]
        assert "2017" in out[0]
        assert "被本热点 1 篇引用" in out[0]
        assert "全球引用 90000" in out[0]
        assert "高影响力" in out[0]

    def test_tiebreak_older_year_first(self):
        """同被引数、同全球引用时，年份早者优先"""
        cf = CitationFinder(rate_limiter=FakeRateLimiter())
        raw = [
            (0, Reference(title="Newer", year=2020, citation_count=100,
                          paper_id="n1")),
            (0, Reference(title="Older", year=2010, citation_count=100,
                          paper_id="o1")),
        ]
        out = cf.rank_references(raw, hotspot_titles=set(), top_n=2)
        assert "Older" in out[0]

    def test_empty_raw(self):
        cf = CitationFinder(rate_limiter=FakeRateLimiter())
        assert cf.rank_references([], hotspot_titles=set()) == []


# ---------------------------------------------------------------------- #
# find_foundational_papers（模拟网络 + 离线回退）
# ---------------------------------------------------------------------- #

class TestFoundationalPapers:
    """测试 find_foundational_papers（Option B 实装 + 降级）"""

    def test_returns_ranked_when_api_available(self, analyzer):
        """collect_raw_references 有结果 → 返回排序后的奠基论文"""
        raw = [
            (0, Reference(title="Classic A", year=2015, citation_count=5000,
                          paper_id="a")),
            (1, Reference(title="Classic A", year=2015, citation_count=5000,
                          paper_id="a")),
            (0, Reference(title="Classic B", year=2018, citation_count=200,
                          paper_id="b")),
        ]
        analyzer.citation_finder.collect_raw_references = lambda papers: raw
        papers = [_make_paper(title="HotspotPaper1"),
                  _make_paper(title="HotspotPaper2")]
        out = analyzer.find_foundational_papers(papers, top_n=3)
        assert len(out) == 2
        assert "Classic A" in out[0]   # 被 2 篇引用 → 排前

    def test_fallback_when_api_returns_empty(self, analyzer):
        """API 返回空 → 离线回退"""
        analyzer.citation_finder.collect_raw_references = lambda papers: []
        papers = [_make_paper(title="Only Paper", year=2020,
                              citation_count=5)]
        out = analyzer.find_foundational_papers(papers)
        assert len(out) == 1
        assert "离线回退" in out[0]
        assert "Only Paper" in out[0]

    def test_fallback_when_api_raises(self, analyzer):
        """API 抛异常 → 离线回退（不向上抛）"""
        def boom(papers):
            raise RuntimeError("network down")
        analyzer.citation_finder.collect_raw_references = boom
        papers = [_make_paper(title="Only Paper", year=2020)]
        out = analyzer.find_foundational_papers(papers)
        assert len(out) == 1
        assert "离线回退" in out[0]

    def test_empty_papers(self, analyzer):
        assert analyzer.find_foundational_papers([]) == []

    def test_fallback_picks_earliest(self, analyzer):
        """回退时应选本热点最早且较高被引的论文"""
        analyzer.citation_finder.collect_raw_references = lambda papers: []
        papers = [
            _make_paper(title="Newest", year=2024, citation_count=5),
            _make_paper(title="Oldest", year=2018, citation_count=50),
        ]
        out = analyzer.find_foundational_papers(papers)
        assert "Oldest" in out[0]


# ---------------------------------------------------------------------- #
# 集成
# ---------------------------------------------------------------------- #

class TestIntegration:
    """端到端：提取 → 整体分析 → 奠基论文（离线路径）"""

    def test_full_offline_pipeline(self, analyzer):
        papers = [
            _make_paper(title="PaperA", year=2023, citation_count=100,
                        keywords=["diffusion"],
                        abstract="We propose a novel method. "
                                 "Results demonstrate improvements."),
            _make_paper(title="PaperB", year=2024, citation_count=50,
                        keywords=["diffusion", "sampling"],
                        abstract="A new approach for sampling."),
        ]
        analyzer.analyze_papers(papers)
        assert papers[0].innovations
        assert papers[0].conclusions

        overall = analyzer.generate_overall_analysis("扩散模型", papers)
        assert "扩散模型" in overall

        # 离线路径
        analyzer.citation_finder.collect_raw_references = lambda p: []
        found = analyzer.find_foundational_papers(papers)
        assert found and "离线回退" in found[0]
