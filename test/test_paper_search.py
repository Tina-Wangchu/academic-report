"""
测试 paper_search.py 模块
"""

import pytest
from datetime import datetime
import sys
import os

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-scholar', 'scripts'))

from paper_search import ArxivSearcher, SemanticScholarSearcher, OpenAlexSearcher, PaperSearcher
from utils import SearchIntent


class TestArxivSearcher:
    """测试 arXiv 搜索器"""

    def test_initialization(self):
        """测试初始化"""
        searcher = ArxivSearcher()
        assert searcher is not None
        assert searcher.client is not None

    def test_search_basic(self):
        """测试基础搜索"""
        searcher = ArxivSearcher()
        papers = searcher.search("machine learning", max_results=5)

        assert isinstance(papers, list)
        assert len(papers) <= 5
        assert all(paper.title for paper in papers)

    def test_search_with_date_filter(self):
        """测试带日期过滤的搜索"""
        searcher = ArxivSearcher()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        papers = searcher.search(
            "artificial intelligence",
            max_results=5,
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(papers, list)
        # 验证日期范围（如果返回结果）
        for paper in papers:
            if paper.year != 0:
                assert start_date.year <= paper.year <= end_date.year

    def test_paper_data_structure(self):
        """测试返回数据结构"""
        searcher = ArxivSearcher()
        papers = searcher.search("deep learning", max_results=1)

        if papers:
            paper = papers[0]
            assert hasattr(paper, 'title')
            assert hasattr(paper, 'authors')
            assert hasattr(paper, 'year')
            assert hasattr(paper, 'abstract')
            assert hasattr(paper, 'venue')
            assert hasattr(paper, 'source')
            assert paper.source == "arxiv"

    def test_date_filter_single_range(self):
        """日期过滤应为单区间（arXiv 不支持两个 submittedDate 子句 AND，会 HTTP 500）"""
        searcher = ArxivSearcher()
        start = datetime(2023, 1, 1)
        end = datetime(2025, 12, 31)
        # 完整区间
        assert searcher._build_date_filter(start, end) == \
            "submittedDate:[202301010000 TO 202512312359]"
        # 单边
        assert searcher._build_date_filter(start, None) == \
            "submittedDate:[202301010000 TO *]"
        assert searcher._build_date_filter(None, end) == \
            "submittedDate:[* TO 202512312359]"
        # 无日期
        assert searcher._build_date_filter(None, None) == ""
        # 关键：不应出现两个 submittedDate 子句
        assert searcher._build_date_filter(start, end).count("submittedDate:") == 1


class TestSemanticScholarSearcher:
    """测试 Semantic Scholar 搜索器"""

    def test_initialization(self):
        """测试初始化"""
        searcher = SemanticScholarSearcher()
        assert searcher is not None
        assert searcher.BASE_URL

    def test_initialization_with_api_key(self):
        """测试带API密钥的初始化"""
        searcher = SemanticScholarSearcher(api_key="test_key")
        assert searcher.api_key == "test_key"
        assert 'x-api-key' in searcher.headers

    def test_search_basic(self):
        """测试基础搜索（需要网络连接）"""
        searcher = SemanticScholarSearcher()
        # 注意：这个测试需要网络连接和API可用性
        papers = searcher.search("neural network", max_results=5)

        assert isinstance(papers, list)
        # Semantic Scholar 可能因为限流返回空列表
        # 所以我们只验证返回类型正确

    def test_venue_classification(self):
        """测试期刊分类逻辑"""
        searcher = SemanticScholarSearcher()

        # 测试顶级会议识别
        assert searcher._classify_venue("NeurIPS") == "conference"
        assert searcher._classify_venue("CVPR") == "conference"
        assert searcher._classify_venue("Unknown") == "preprint"

        # 测试期刊识别
        assert searcher._classify_venue("Journal of AI") == "journal"

    def test_ranking_determination(self):
        """测试等级判断"""
        searcher = SemanticScholarSearcher()

        # 高被引
        assert searcher._get_ranking("journal", 150) == "高被引"
        # 普通期刊
        assert searcher._get_ranking("journal", 10) == "核心期刊"
        # 顶会
        assert searcher._get_ranking("conference", 50) == "顶会"
        # 普通
        assert searcher._get_ranking("preprint", 0) == "普通"

    def test_convert_to_paper_parses_tldr(self):
        """S2 tldr 字段（{model, text}）应解析为 paper.tldr（Phase 1）"""
        searcher = SemanticScholarSearcher()
        item = {
            "title": "T", "authors": [], "venue": "NeurIPS", "year": 2024,
            "abstract": "abs", "citationCount": 10, "externalIds": {},
            "url": "u", "tldr": {"model": "tldr@v2", "text": "A short TLDR."},
        }
        p = searcher._convert_to_paper(item)
        assert p.tldr == "A short TLDR."

    def test_convert_to_paper_tldr_missing(self):
        """无 tldr 时 paper.tldr 为空"""
        searcher = SemanticScholarSearcher()
        item = {"title": "T", "authors": [], "venue": "arXiv", "year": 2024,
                "abstract": "abs", "citationCount": 0, "externalIds": {}, "url": "u"}
        p = searcher._convert_to_paper(item)
        assert p.tldr == ""

    def test_convert_to_paper_published_date(self):
        """S2 publicationDate → paper.published_date（日级）"""
        from datetime import date
        searcher = SemanticScholarSearcher()
        item = {"title": "T", "authors": [], "venue": "V", "year": 2026,
                "abstract": "a", "citationCount": 0, "externalIds": {}, "url": "u",
                "publicationDate": "2026-07-10"}
        p = searcher._convert_to_paper(item)
        assert p.published_date == date(2026, 7, 10)

    def test_convert_to_paper_published_date_missing(self):
        searcher = SemanticScholarSearcher()
        item = {"title": "T", "authors": [], "venue": "V", "year": 2026,
                "abstract": "a", "citationCount": 0, "externalIds": {}, "url": "u"}
        p = searcher._convert_to_paper(item)
        assert p.published_date is None

    def test_convert_to_paper_published_date_invalid(self):
        """非法日期字符串 → None（不抛异常）"""
        searcher = SemanticScholarSearcher()
        item = {"title": "T", "authors": [], "venue": "V", "year": 2026,
                "abstract": "a", "citationCount": 0, "externalIds": {}, "url": "u",
                "publicationDate": "not-a-date"}
        p = searcher._convert_to_paper(item)
        assert p.published_date is None


class TestToEnglishQuery:
    """测试中文→英文查询翻译（搜索始终用英文）"""

    def test_chinese_translated(self):
        from paper_search import _to_english_query
        assert _to_english_query("机器学习") == "machine learning"
        assert _to_english_query("深度学习") == "deep learning"

    def test_mixed_translated(self):
        from paper_search import _to_english_query
        assert "machine learning" in _to_english_query("机器学习 recent")
        assert "deep learning" in _to_english_query("深度学习 statistics")

    def test_english_unchanged(self):
        from paper_search import _to_english_query
        assert _to_english_query("machine learning") == "machine learning"

    def test_unknown_passes_through(self):
        from paper_search import _to_english_query
        assert _to_english_query("unknown term") == "unknown term"

    def test_build_search_query_translates(self):
        """PaperSearcher._build_search_query 把中文关键词翻成英文"""
        from paper_search import PaperSearcher
        from utils import SearchIntent
        intent = SearchIntent(
            query="机器学习", keywords=["机器学习"],
            research_field="machine_learning", language="zh")
        q = PaperSearcher()._build_search_query(intent)
        assert "machine learning" in q.lower()
        assert "机器学习" not in q   # 中文已翻译


# ---------------------------------------------------------------------- #
# OpenAlex
# ---------------------------------------------------------------------- #

class TestOpenAlexSearcher:
    """测试 OpenAlex 搜索器"""

    def test_initialization(self):
        """测试初始化"""
        searcher = OpenAlexSearcher()
        assert searcher is not None
        assert searcher.BASE_URL

    def test_filter_building(self):
        """测试过滤器构建"""
        searcher = OpenAlexSearcher()

        # 测试完整日期过滤
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        filter_str = searcher._build_filter(start_date, end_date)

        assert "from_publication_date:2023-01-01" in filter_str
        assert "to_publication_date:2023-12-31" in filter_str
        assert "type:article" in filter_str

    def test_filter_with_only_start_date(self):
        """测试仅开始日期的过滤器"""
        searcher = OpenAlexSearcher()
        start_date = datetime(2023, 1, 1)
        filter_str = searcher._build_filter(start_date, None)

        assert "from_publication_date:2023-01-01" in filter_str
        assert "to_publication_date" not in filter_str

    def test_filter_with_no_date(self):
        """测试无日期的过滤器"""
        searcher = OpenAlexSearcher()
        filter_str = searcher._build_filter(None, None)

        assert "type:article" in filter_str

    def test_convert_to_paper_doi_string_and_null_location(self):
        """OpenAlex 的 doi 为字符串 URL、primary_location 可能为 null（回归测试）"""
        searcher = OpenAlexSearcher()
        item = {
            "title": "Test Paper",
            "authorships": [{"author": {"display_name": "Author A"}}],
            "primary_location": None,  # null
            "doi": "https://doi.org/10.1234/test",  # 字符串，非 dict
            "publication_year": 2024,
            "cited_by_count": 10,
            "id": "https://openalex.org/W123",
        }
        p = searcher._convert_to_paper(item)
        assert p.title == "Test Paper"
        assert p.doi == "10.1234/test"      # 去除前缀
        assert p.venue == "Unknown"          # primary_location null 兜底
        assert p.year == 2024
        assert p.citation_count == 10
        assert p.source == "openalex"

    def test_convert_to_paper_dict_doi(self):
        """doi 为 dict 形态时也能处理"""
        searcher = OpenAlexSearcher()
        item = {
            "title": "X", "authorships": [],
            "primary_location": {"source": {"display_name": "V", "type": "journal"}},
            "doi": {"id": "https://doi.org/10.1/y"},
            "publication_year": 2023, "cited_by_count": 0, "id": "x",
        }
        p = searcher._convert_to_paper(item)
        assert p.doi == "10.1/y"
        assert p.venue == "V"

    def test_convert_to_paper_published_date(self):
        """OpenAlex publication_date → paper.published_date（日级）"""
        from datetime import date
        searcher = OpenAlexSearcher()
        item = {
            "title": "X", "authorships": [],
            "primary_location": {"source": {"display_name": "V", "type": "journal"}},
            "doi": "10.1/y", "publication_year": 2026,
            "publication_date": "2026-07-10",
            "cited_by_count": 0, "id": "x",
        }
        p = searcher._convert_to_paper(item)
        assert p.published_date == date(2026, 7, 10)

    def test_reconstruct_abstract_from_inverted_index(self):
        """OpenAlex 摘要需从 abstract_inverted_index 重建（回归测试，§abstract_problem）"""
        searcher = OpenAlexSearcher()
        # 倒排索引：We(0) propose(1) a(2) method(3)
        inv = {"We": [0], "propose": [1], "a": [2], "method": [3]}
        item = {
            "title": "T", "authorships": [], "primary_location": None,
            "doi": "", "abstract_inverted_index": inv,
            "publication_year": 2024, "cited_by_count": 0, "id": "x",
        }
        p = searcher._convert_to_paper(item)
        assert p.abstract == "We propose a method"

    def test_reconstruct_abstract_none(self):
        """inverted_index 为 None（数据源固有无摘要）→ 空串"""
        searcher = OpenAlexSearcher()
        assert searcher._reconstruct_abstract({"abstract_inverted_index": None}) == ""
        assert searcher._reconstruct_abstract({}) == ""


class TestPaperSearcher:
    """测试主搜索器"""

    def test_initialization(self):
        """测试初始化"""
        searcher = PaperSearcher()
        assert searcher is not None
        assert searcher.config is not None
        assert 'arxiv' in searcher.searchers
        assert 'semantic_scholar' in searcher.searchers
        assert 'openalex' in searcher.searchers

    def test_search_query_building(self):
        """测试查询构建"""
        searcher = PaperSearcher()

        # 测试使用关键词
        intent = SearchIntent(
            query="test",
            keywords=["machine learning", "AI"],
            research_field="cs",
            language="en",
            max_results=50
        )
        query = searcher._build_search_query(intent)

        assert query == "machine learning AI"

    def test_search_query_fallback(self):
        """测试查询构建（无关键词时）"""
        searcher = PaperSearcher()

        intent = SearchIntent(
            query="test query",
            keywords=[],
            research_field="general",
            language="bilingual",
            max_results=50
        )
        query = searcher._build_search_query(intent)

        assert query == "test query"

    def test_deduplication_logic(self):
        """测试去重逻辑"""
        searcher = PaperSearcher()

        from utils import Paper

        # 创建测试数据（有DOI和标题）
        papers = [
            Paper(
                title="Paper A",
                authors=["Author1"],
                venue="arXiv",
                year=2023,
                doi="10.1234/test",
                abstract="Abstract A",
                keywords=[],
                citation_count=10,
                venue_type="preprint",
                ranking="普通",
                url="https://arxiv.org/abs/1234",
                source="arxiv"
            ),
            Paper(
                title="Paper B",
                authors=["Author2"],
                venue="Conference",
                year=2023,
                doi="",
                abstract="Abstract B",
                keywords=[],
                citation_count=5,
                venue_type="conference",
                ranking="顶会",
                url="",
                source="semantic_scholar"
            ),
            Paper(
                title="Paper A",  # 重复DOI
                authors=["Author3"],
                venue="Journal",
                year=2023,
                doi="10.1234/test",  # 重复DOI
                abstract="Abstract A",
                keywords=[],
                citation_count=8,
                venue_type="journal",
                ranking="核心期刊",
                url="https://journal.com/paper",
                source="openalex"
            ),
        ]

        unique_papers = searcher._deduplicate(papers)

        # 应该只有2篇（Paper A 和 Paper B，重复的Paper A被去重）
        assert len(unique_papers) == 2
        # 验证第一篇是有DOI的原始Paper A
        assert unique_papers[0].doi == "10.1234/test"

    def test_deduplication_with_title_only(self):
        """测试仅标题去重"""
        searcher = PaperSearcher()

        from utils import Paper

        papers = [
            Paper(
                title="Same Title",
                authors=["Author1"],
                venue="arXiv",
                year=2023,
                doi="",  # 无DOI
                abstract="Abstract",
                keywords=[],
                citation_count=10,
                venue_type="preprint",
                ranking="普通",
                url="url1",
                source="arxiv"
            ),
            Paper(
                title="Same Title",  # 重复标题
                authors=["Author2"],
                venue="Journal",
                year=2023,
                doi="",  # 无DOI
                abstract="Abstract",
                keywords=[],
                citation_count=5,
                venue_type="journal",
                ranking="核心期刊",
                url="url2",
                source="semantic_scholar"
            ),
            Paper(
                title="Different Title",
                authors=["Author3"],
                venue="Conference",
                year=2023,
                doi="",
                abstract="Abstract",
                keywords=[],
                citation_count=3,
                venue_type="conference",
                ranking="顶会",
                url="url3",
                source="openalex"
            ),
        ]

        unique_papers = searcher._deduplicate(papers)

        # 应该有2篇（Same Title去重后保留第一篇，Different Title保留）
        assert len(unique_papers) == 2


class TestIntegration:
    """集成测试"""

    def test_full_search_flow(self):
        """测试完整搜索流程（需要网络）"""
        searcher = PaperSearcher()

        intent = SearchIntent(
            query="artificial intelligence",
            keywords=[],
            research_field="cs",
            language="bilingual",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 6, 30),
            max_results=5  # 小数量用于测试
        )

        papers = searcher.search(intent)

        assert isinstance(papers, list)
        # 验证至少有结果（如果API可用）
        # 或者为空列表（如果API不可用）

    def test_error_handling(self):
        """测试错误处理"""
        searcher = PaperSearcher()

        # 测试无效数据源配置
        # （暂时跳过，因为搜索器初始化时会失败）

        # 测试搜索过程中的异常处理
        intent = SearchIntent(
            query="test",
            keywords=[],
            research_field="test",
            language="en",
            max_results=5
        )

        # 即使某个数据源失败，也应该返回其他数据源的结果
        papers = searcher.search(intent)
        assert isinstance(papers, list)  # 应该始终返回列表


# 测试配置
@pytest.fixture
def sample_search_intent():
    """提供示例搜索意图"""
    return SearchIntent(
        query="machine learning",
        keywords=["machine learning"],
        research_field="ai",
        language="bilingual",
        start_date=datetime(2023, 1, 1),
        end_date=datetime.now(),
        paper_types=["journal", "conference"],
        filters={},
        max_results=10
    )
