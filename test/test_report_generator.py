"""
测试 report_generator.py 模块（模块5）
覆盖：四段式结构、双语（zh/en/bilingual）、速览不遗漏、单篇字段、Abstract 截断、
      热点块（介绍/整体分析/奠基论文，Option B 委托）、研究趋势派生、HTML 转换、保存。
用 Fake 前置模块避免联网。
"""

import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'academic-report', 'scripts'))

from utils import Paper, SearchIntent
from report_generator import ReportGenerator, _label


# ---------------------------------------------------------------------- #
# Fake 前置模块（避免联网，确定性输出）
# ---------------------------------------------------------------------- #

class FakeFilter:
    def classify_by_topic(self, papers, topic_hint=""):
        # 全部归到单一热点，便于断言
        return {"测试热点": list(papers)}

    def generate_hotspot_intro(self, topic, papers):
        return f"[介绍]{topic}"


class FakeAnalyzer:
    def analyze_papers(self, papers, lang="bilingual"):
        for p in papers:
            if not p.research_content:
                p.research_content = "研究内容X"
            if not p.innovations:
                p.innovations = "创新点X"
            if not p.conclusions:
                p.conclusions = "结论X"
            # 模拟真实 AbstractSummarizer：有摘要→完整摘要；无摘要→空（走占位）
            if not p.condensed_abstract:
                p.condensed_abstract = (p.abstract or "")
            # 四要素摘录：有摘要且未被预填时给固定值（测渲染）；无摘要时留空（测占位回退）
            if not p.new_approach and not p.problem and p.abstract:
                p.problem = "问题X"
                p.existing_approaches = "现有X"
                p.new_approach = "新方案X"
                p.results_limitations = "效果X"
        return papers

    def generate_overall_analysis(self, topic, papers):
        return f"[整体分析]{topic}"

    def find_foundational_papers(self, papers, top_n=3):
        return ["FoundationalA (2020): Classic —— 被本热点 1 篇引用"]


def _make_paper(title, abstract="A short abstract.", year=2024,
                citation_count=10, doi="", authors=None, keywords=None):
    return Paper(
        title=title,
        authors=authors or ["Smith J", "Lee K", "Wang Q"],
        venue="NeurIPS",
        year=year,
        doi=doi,
        abstract=abstract,
        keywords=keywords or ["diffusion"],
        citation_count=citation_count,
        venue_type="conference",
        ranking="顶会",
        url="https://example.com/p",
        source="test",
    )


def _make_intent(language="bilingual"):
    return SearchIntent(
        query="diffusion models", keywords=["diffusion"],
        research_field="扩散模型", language=language,
        max_results=50,
    )


@pytest.fixture
def gen():
    return ReportGenerator(paper_filter=FakeFilter(),
                           paper_analyzer=FakeAnalyzer())


# ---------------------------------------------------------------------- #
# 四段式结构
# ---------------------------------------------------------------------- #

class TestStructure:
    """测试报告四段式结构"""

    def test_has_four_parts_bilingual(self, gen):
        report = gen.generate_report([_make_paper("P1")], _make_intent("bilingual"))
        # 标题
        assert "扩散模型 报告" in report and "Diffusion" in report.upper() or "Report" in report
        # 一、二、三 段
        assert "报告速览" in report and "Report Overview" in report
        assert "分类论文展示" in report and "Classified Paper Display" in report
        assert "研究趋势" in report and "Research Trends" in report

    def test_time_labels_present(self, gen):
        report = gen.generate_report([_make_paper("P1")], _make_intent())
        assert "报告生成时间" in report and "Report generation time" in report
        assert "报告涵盖时间" in report and "Report coverage time" in report


# ---------------------------------------------------------------------- #
# 双语模式
# ---------------------------------------------------------------------- #

class TestBilingualModes:
    """测试 zh / en / bilingual 三种模式"""

    def test_bilingual_has_both_languages(self, gen):
        report = gen.generate_report([_make_paper("P1")], _make_intent("bilingual"))
        # 双语标签并存
        assert "作者" in report and "Authors" in report
        # 双语标题两行
        assert "# 扩散模型 报告" in report
        assert "# 扩散模型 Report" in report

    def test_zh_mode_chinese_only_labels(self, gen):
        report = gen.generate_report([_make_paper("P1")], _make_intent("zh"))
        assert "一、报告速览" in report
        # 不应出现英文段名
        assert "Report Overview" not in report
        assert "# 扩散模型 报告" in report
        assert "# 扩散模型 Report" not in report

    def test_en_mode_english_labels(self, gen):
        report = gen.generate_report([_make_paper("P1")], _make_intent("en"))
        assert "I. Report Overview" in report
        assert "Authors" in report
        # 不应出现中文段名
        assert "一、报告速览" not in report

    def test_default_language_is_bilingual(self, gen):
        """intent.language 为空时默认 bilingual"""
        intent = SearchIntent(query="x", keywords=[], research_field="AI",
                              language="", max_results=50)
        report = gen.generate_report([_make_paper("P1")], intent)
        assert "Report Overview" in report  # bilingual 默认


# ---------------------------------------------------------------------- #
# 速览：按热点概括
# ---------------------------------------------------------------------- #

class TestSummaryByHotspot:
    """测试速览：按热点分组、逐篇概述每篇论文的核心内容"""

    def test_summary_lists_hotspot_and_per_paper_finding(self, gen):
        """速览列出热点名 + 篇数，且每篇给出核心内容（摘要首句）"""
        papers = [_make_paper(f"P{i}") for i in range(4)]
        report = gen.generate_report(papers, _make_intent())
        overview = report.split("二、")[0]  # 速览段在「二、」之前
        assert "测试热点" in overview          # 热点名（FakeFilter 单热点）
        assert "4" in overview                # 篇数
        assert "A short abstract" in overview  # 每篇核心内容（摘要首句）

    def test_summary_covers_every_paper(self, gen):
        """速览按热点分组，覆盖其中每一篇论文（标题均出现）"""
        papers = [_make_paper(f"UniqueTitle{i}") for i in range(8)]
        report = gen.generate_report(papers, _make_intent())
        overview = report.split("二、")[0]
        # 速览段应出现每一篇标题（逐篇概述）
        for i in range(8):
            assert f"UniqueTitle{i}" in overview

    def test_paper_finding_uses_condensed_abstract(self, gen):
        """_paper_finding 取摘要前 1-2 句，回退标题"""
        p = _make_paper("T", abstract="First sentence here. Second one.")
        assert ReportGenerator._paper_finding(p) == "First sentence here."
        p_empty = _make_paper("Empty", abstract="")
        assert ReportGenerator._paper_finding(p_empty) == "Empty"


# ---------------------------------------------------------------------- #
# 单篇论文块
# ---------------------------------------------------------------------- #

class TestPaperBlock:
    """测试单篇论文字段渲染"""

    def test_renders_required_fields(self, gen):
        p = _make_paper("My Paper", authors=["A", "B", "C", "D", "E"],
                        year=2023, citation_count=42, doi="10.1234/x")
        report = gen.generate_report([p], _make_intent("bilingual"))
        assert "My Paper" in report
        assert "A, B, C" in report and "et al" in report  # >3 作者用等
        assert "2023" in report
        assert "NeurIPS" in report
        assert "42" in report
        assert "10.1234/x" in report
        assert "APA" in report

    def test_structured_parts_rendered(self, gen):
        """单篇块渲染四要素摘录（解决的问题/现有方案/新方案/效果及局限）"""
        p = _make_paper("P1", abstract="A short abstract.")
        report = gen.generate_report([p], _make_intent("bilingual"))
        assert "解决的问题" in report and "Problem" in report
        assert "现有方案" in report and "Existing approaches" in report
        assert "新方案" in report and "New approach" in report
        assert "效果及局限性" in report and "Results & limitations" in report
        # 四要素值（FakeAnalyzer 设的固定值；autospace 后 CJK 与 X 间有空格）
        assert "问题 X" in report and "现有 X" in report
        assert "新方案 X" in report and "效果 X" in report

    def test_analysis_fields_not_rendered(self, gen):
        """研究内容/创新点/核心结论 不再在单篇块渲染（已删除）"""
        p = _make_paper("P1")
        report = gen.generate_report([p], _make_intent())
        assert "研究内容X" not in report
        assert "创新点X" not in report
        assert "结论X" not in report

    def test_abstract_missing_shows_placeholder(self, gen):
        """四要素全空（无摘要）时回退完整 Abstract 占位（§10.1）"""
        p = _make_paper("NoAbstract", abstract="")
        report = gen.generate_report([p], _make_intent())
        assert "暂无摘要" in report and "No abstract available" in report

    def test_empty_part_shows_not_mentioned(self, gen):
        """某要素为空时显示「未明确提及」占位"""
        p = _make_paper("P1", abstract="A short abstract.")
        p.new_approach = ""  # 强制某要素为空，其余保留
        p.problem = "问题X"
        p.existing_approaches = "现有X"
        p.results_limitations = "效果X"
        report = gen.generate_report([p], _make_intent("bilingual"))
        assert "未明确提及" in report and "Not explicitly mentioned" in report

    def test_unavailable_paper_shows_access_note(self, gen):
        """闭源/无开放内容：标注检索链接，而非空四要素"""
        p = _make_paper("ClosedPaper", abstract="", doi="10.1038/closed")
        p.problem = p.existing_approaches = ""
        p.new_approach = p.results_limitations = ""
        p.analysis_source = "unavailable"
        report = gen.generate_report([p], _make_intent("bilingual"))
        assert "无法自动分析" in report and "Unavailable for auto-analysis" in report
        assert "doi.org/10.1038/closed" in report     # 检索链接
        assert "未明确提及" not in report              # 不再显示空四要素

    def test_value_application_rendered(self, gen):
        """研究价值与应用场景（非空时渲染）"""
        p = _make_paper("P1", abstract="A short abstract.")
        p.value_application = "医疗健康、推荐系统"
        report = gen.generate_report([p], _make_intent("bilingual"))
        assert "研究价值与应用" in report
        assert "医疗健康" in report


# ---------------------------------------------------------------------- #
# 热点块（Option B 委托）
# ---------------------------------------------------------------------- #

class TestHotspotBlock:
    """测试热点标题/介绍/整体分析/奠基论文（来自 filter/analyzer）"""

    def test_hotspot_heading_bilingual(self, gen):
        report = gen.generate_report([_make_paper("P1")], _make_intent("bilingual"))
        assert "热点一" in report and "Hotspot 1" in report

    def test_delegated_sections_present(self, gen):
        report = gen.generate_report([_make_paper("P1")], _make_intent())
        assert "[介绍]测试热点" in report          # filter.generate_hotspot_intro
        assert "[整体分析]测试热点" in report      # analyzer.generate_overall_analysis
        assert "FoundationalA" in report          # analyzer.find_foundational_papers


# ---------------------------------------------------------------------- #
# 研究趋势（派生，非空话）
# ---------------------------------------------------------------------- #

class TestTrends:
    """测试研究趋势派生"""

    def test_trends_nonempty(self, gen):
        report = gen.generate_report(
            [_make_paper("P1", keywords=["diffusion", "sampling"])],
            _make_intent())
        assert "未来研究趋势" in report or "Future Trends" in report
        assert "可深挖方向" in report or "Directions Worth Exploring" in report
        # 趋势应提到关键词
        assert "diffusion" in report

    def test_directions_derived_not_flaws(self, gen):
        """研究方向（深挖方向）应基于论文派生，且不再是旧的论文缺陷评价"""
        p = _make_paper("Diffusion sampling method", abstract="a method for sampling",
                        keywords=["diffusion", "sampling"])
        report = gen.generate_report([p], _make_intent("zh"))
        # 新章节标签存在（深挖方向）
        assert "可深挖方向" in report or "Directions Worth Exploring" in report
        # 不再出现旧的缺陷评价措辞（预印本缺评审 / 缺高被引里程碑 等"论文缺陷"判断）
        assert "缺乏经同行评审" not in report
        assert "缺乏高被引里程碑" not in report


# ---------------------------------------------------------------------- #
# PDF 生成 & 保存
# ---------------------------------------------------------------------- #

class TestPdfAndSave:
    """测试 PDF 生成与文件保存"""

    def test_pdf_smoke(self, gen):
        pdf = gen.generate_report([_make_paper("P1")], _make_intent(), "pdf")
        assert isinstance(pdf, (bytes, bytearray))
        assert bytes(pdf)[:5] == b"%PDF-"      # PDF magic bytes
        assert len(pdf) > 1000                  # 非平凡大小

    def test_generate_both_returns_md_pdf_ctx(self, gen):
        md, pdf, ctx = gen.generate_both([_make_paper("P1")], _make_intent())
        assert md and "P1" in md
        assert isinstance(pdf, (bytes, bytearray))
        assert bytes(pdf)[:5] == b"%PDF-"

    def test_save_pdf(self, gen, tmp_path):
        pdf = gen.generate_report([_make_paper("P1")], _make_intent(), "pdf")
        out = gen.save_pdf(bytes(pdf), str(tmp_path / "report.pdf"))
        assert out.exists()
        assert out.read_bytes()[:5] == b"%PDF-"

    def test_save_report_markdown(self, gen, tmp_path):
        report = gen.generate_report([_make_paper("P1")], _make_intent())
        out = gen.save_report(report, str(tmp_path / "report.md"))
        assert out.exists()
        assert "P1" in out.read_text(encoding="utf-8")


# ---------------------------------------------------------------------- #
# 工具函数
# ---------------------------------------------------------------------- #

class TestLabelHelper:
    def test_label_zh(self):
        assert _label("overview", "zh") == "一、报告速览"

    def test_label_en(self):
        assert _label("overview", "en") == "I. Report Overview"

    def test_label_bilingual(self):
        assert _label("overview", "bilingual") == "一、报告速览 / I. Report Overview"


class TestTextHelpers:
    """中英混排自动加空格 + 英文 Title Case"""

    def test_autospace_inserts_between_cjk_and_latin(self):
        from report_generator import ReportGenerator
        f = ReportGenerator._autospace_cjk_latin
        assert f("深度学习XAI") == "深度学习 XAI"
        assert f("提升20%效率") == "提升 20%效率"   # % 非拉丁/数字，其后再插空格
        assert f("AI驱动") == "AI 驱动"

    def test_autospace_protects_url_and_doi(self):
        from report_generator import ReportGenerator
        f = ReportGenerator._autospace_cjk_latin
        # URL / DOI 内部不插入空格；与 CJK 边界补空格
        assert f("见https://example.com/abc期刊") == "见 https://example.com/abc 期刊"
        assert f("https://example.com/abc") == "https://example.com/abc"   # 无 CJK 不变
        assert "10.1234/foo" in f("DOI 10.1234/foo(bar)")

    def test_titlecase_minor_words_lowercase(self):
        from report_generator import ReportGenerator
        f = ReportGenerator._titlecase_en
        assert f("artificial intelligence in education") == "Artificial Intelligence in Education"
        assert f("a survey on bert and gpt") == "A Survey on BERT and GPT"
        assert f("deep learning for nlp") == "Deep Learning for NLP"

    def test_titlecase_acronyms_uppercase(self):
        from report_generator import ReportGenerator
        assert ReportGenerator._titlecase_en("ai in healthcare") == "AI in Healthcare"
