#!/usr/bin/env python3
"""
Paper Search — Academic paper retrieval with filtering.

Usage:
    python paper_search.py --topic "machine learning in education" \
        --keywords "LLM,education,personalized learning" \
        --time-range 3y --max-results 10 \
        --language en --sort-by citation_count

Supported data sources (free, no authentication required):
    - Semantic Scholar (API): covers CS, biology, medicine
    - arXiv (API): preprints in physics, CS, math, biology
    - CrossRef (API): global metadata, limited abstracts
    - Google Scholar (web scraping): fallback for broad coverage

Output formats:
    - JSON (default): structured paper metadata
    - Markdown: human-readable summary
    - CSV: for spreadsheet analysis

Requires Python 3.8+. No external dependencies (uses standard library only).
"""

import argparse
import json
import re
import ssl
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode, quote
from urllib.request import urlopen, Request
from typing import List, Dict, Any, Optional

# 导入质量评分和代表性筛选模块
try:
    from quality_scorer import PaperQualityScorer
    from representative_selector import RepresentativePaperSelector
    QUALITY_MODULES_AVAILABLE = True
except ImportError:
    QUALITY_MODULES_AVAILABLE = False
    print("Warning: Quality scoring modules not available. Install quality_scorer.py and representative_selector.py", file=sys.stderr)

# ==================== SSL Context Configuration ====================

def create_ssl_context():
    """Create SSL context - use unverified context for Windows compatibility."""
    # Windows often lacks proper SSL certificate chains
    # Using unverified context to ensure connectivity
    import warnings
    warnings.warn("Using unverified SSL context - certificate verification disabled for compatibility")
    return ssl._create_unverified_context()

SSL_CONTEXT = create_ssl_context()

# ==================== Configuration ====================

DEFAULT_MAX_RESULTS = 50  # 改进：从8篇提高到50篇（改进2：配合API请求200篇的策略）
DEFAULT_TIME_RANGE = "3y"  # 3 years
DEFAULT_LANGUAGE = "bilingual"
DEFAULT_SORT_BY = "relevance"
DEFAULT_DOMAIN = "general"  # 应用领域：general/statistics/ai/finance

USER_AGENT = "Hermes-Agent-Paper-Search/1.0"

# 应用领域对应的数据源优先级配置
DOMAIN_SOURCE_PRIORITY = {
    "general": ["Semantic Scholar", "CrossRef", "arXiv"],      # 通用领域
    "statistics": ["CrossRef", "Semantic Scholar", "arXiv"],    # 统计决策（CrossRef覆盖统计期刊最佳）
    "ai": ["arXiv", "Semantic Scholar", "CrossRef"],           # 人工智能（arXiv最新预印本最多）
    "finance": ["CrossRef", "Semantic Scholar", "arXiv"],      # 金融统计（CrossRef覆盖金融期刊）
}

# ==================== Time Range Utilities ====================

def parse_time_range(time_range: str) -> Optional[Dict[str, Any]]:
    """
    Parse time range string to start/end dates.

    Returns dict with 'start_date' and 'end_date' (ISO format),
    or None for unlimited range.
    """
    if time_range == "unlimited" or not time_range:
        return None

    now = datetime.now(timezone.utc)
    end_date = now

    # Parse patterns like "3y", "1y", "5y", "10y"
    year_match = re.match(r'^(\d+)y$', time_range)
    if year_match:
        years = int(year_match.group(1))
        start_date = now - timedelta(days=years * 365)
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "years": years
        }

    # Parse custom range like "2020-2023" or "2020-01-01:2023-12-31"
    custom_match = re.match(r'^(\d{4})-(\d{4})$', time_range)
    if custom_match:
        start_year = int(custom_match.group(1))
        end_year = int(custom_match.group(2))
        return {
            "start_date": f"{start_year}-01-01",
            "end_date": f"{end_year}-12-31",
            "years": end_year - start_year
        }

    # Parse detailed custom range like "2020-01-01:2023-06-30"
    detailed_match = re.match(r'^(\d{4}-\d{2}-\d{2}):(\d{4}-\d{2}-\d{2})$', time_range)
    if detailed_match:
        return {
            "start_date": detailed_match.group(1),
            "end_date": detailed_match.group(2),
            "years": "custom"
        }

    return None  # Invalid format, treat as unlimited


# ==================== Data Source APIs ====================

class SemanticScholarAPI:
    """Semantic Scholar API client (free, no auth required)."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    @staticmethod
    def search_papers(query: str, fields: str, limit: int = 100, year: str = None) -> List[Dict]:
        """Search papers via Semantic Scholar API."""
        params = {
            "query": query,
            "fields": fields,
            "limit": limit
        }
        if year:
            params["year"] = year

        url = f"{SemanticScholarAPI.BASE_URL}/paper/search?{urlencode(params)}"

        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("data", [])
        except Exception as e:
            print(f"Semantic Scholar API error: {e}", file=sys.stderr)
            return []


class ArxivAPI:
    """arXiv API client (free, no auth required)."""

    BASE_URL = "http://export.arxiv.org/api/query"

    @staticmethod
    def search_papers(query: str, max_results: int = 100) -> List[Dict]:
        """Search papers via arXiv API."""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        url = f"{ArxivAPI.BASE_URL}?{urlencode(params)}"

        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
                # arXiv returns XML, need to parse (simplified parsing)
                import xml.etree.ElementTree as ET
                xml_data = response.read().decode('utf-8')
                root = ET.fromstring(xml_data)

                # arXiv uses Atom namespace
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                entries = root.findall("atom:entry", ns)

                papers = []
                for entry in entries:
                    paper = {
                        "title": entry.find("atom:title", ns).text.strip(),
                        "authors": [author.find("atom:name", ns).text
                                   for author in entry.findall("atom:author", ns)],
                        "summary": entry.find("atom:summary", ns).text.strip(),
                        "published": entry.find("atom:published", ns).text,
                        "url": entry.find("atom:id", ns).text,
                        "source": "arXiv"
                    }
                    papers.append(paper)

                return papers
        except Exception as e:
            print(f"arXiv API error: {e}", file=sys.stderr)
            return []


class CrossRefAPI:
    """CrossRef API client (free, no auth required)."""

    BASE_URL = "https://api.crossref.org/works"

    @staticmethod
    def search_papers(query: str, rows: int = 100, filter_year: str = None) -> List[Dict]:
        """Search papers via CrossRef API."""
        params = {
            "query": query,
            "rows": rows,
            "select": "title,author,published-print,container-title,DOI,type,abstract"
        }
        if filter_year:
            params["filter"] = f"from-pub-date:{filter_year}"

        url = f"{CrossRefAPI.BASE_URL}?{urlencode(params)}"

        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get("message", {}).get("items", [])

                papers = []
                for item in items:
                    paper = {
                        "title": " ".join(item.get("title", [])),
                        "authors": [f"{a.get('given', '')} {a.get('family', '')}"
                                   for a in item.get("author", [])],
                        "published": item.get("published-print", {}).get("date-time", ""),
                        "journal": item.get("container-title", [""])[0],
                        "doi": item.get("DOI", ""),
                        "type": item.get("type", ""),
                        "abstract": item.get("abstract", ""),
                        "source": "CrossRef"
                    }
                    papers.append(paper)

                return papers
        except Exception as e:
            print(f"CrossRef API error: {e}", file=sys.stderr)
            return []


# ==================== Paper Search Engine ====================

class PaperSearchEngine:
    """Main paper search engine with filtering and ranking."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.time_range = parse_time_range(config.get("time_range", DEFAULT_TIME_RANGE))
        self.keywords = self._parse_keywords(config.get("keywords", []))
        self.research_topic = config.get("research_topic", "")
        # 确定应用领域（用于优化数据源选择）
        self.domain = config.get("domain", DEFAULT_DOMAIN)

        # 分离API请求量和用户返回量（改进2）
        self.api_request_limit = 200  # API固定请求200篇，确保充足的数据池
        self.user_max_results = config.get("max_results", DEFAULT_MAX_RESULTS)  # 用户期望的返回数量

        # 质量筛选功能（新增）
        self.enable_quality_filter = config.get("enable_quality_filter", False)
        if self.enable_quality_filter and QUALITY_MODULES_AVAILABLE:
            self.quality_scorer = PaperQualityScorer()
            self.representative_selector = RepresentativePaperSelector()
        else:
            self.quality_scorer = None
            self.representative_selector = None

    def _parse_keywords(self, keywords_input) -> List[str]:
        """Parse keywords from various input formats."""
        if isinstance(keywords_input, str):
            # Comma-separated string
            return [k.strip() for k in keywords_input.split(",")]
        elif isinstance(keywords_input, list):
            return keywords_input
        return []

    def _build_search_query(self) -> str:
        """Build search query from topic and keywords."""
        query_parts = []

        if self.research_topic:
            query_parts.append(self.research_topic)

        if self.keywords:
            query_parts.extend(self.keywords)

        return " ".join(query_parts)

    def _filter_by_date(self, papers: List[Dict]) -> List[Dict]:
        """
        Filter papers by publication date (精确到天).

        改进1：从按年份过滤改为精确到天的过滤
        避免返回时间范围外的论文（如2025-01-01的论文）
        """
        if not self.time_range:
            return papers

        start_date = datetime.fromisoformat(self.time_range["start_date"])
        end_date = datetime.fromisoformat(self.time_range["end_date"])

        # 统一使用UTC时区，确保时间比较准确
        start_date = start_date.replace(tzinfo=timezone.utc)
        end_date = end_date.replace(tzinfo=timezone.utc)
        end_date = end_date.replace(hour=23, minute=59, second=59)  # 包含当天最后一刻

        filtered = []
        for paper in papers:
            pub_date = self._extract_publication_date(paper)
            if pub_date and start_date <= pub_date <= end_date:
                filtered.append(paper)

        return filtered

    def _extract_publication_date(self, paper: Dict) -> Optional[datetime]:
        """
        提取论文的发表日期（精确到天）。

        支持多种日期格式：
        - ISO 8601: 2025-07-01T12:34:56Z
        - 日期格式: 2025-07-01
        - 年份: 2025（退化为该年1月1日）
        """
        # 尝试不同的日期字段
        date_fields = ["publicationDate", "published", "pubDate", "date", "year"]

        for field in date_fields:
            if field in paper and paper[field]:
                value = str(paper[field]).strip()

                # 情况1: 完整的ISO日期时间（包含T）
                if "T" in value:
                    try:
                        return datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        continue

                # 情况2: 只有日期（包含-）
                elif "-" in value and len(value) >= 8:
                    try:
                        dt = datetime.fromisoformat(value)
                        return dt.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

                # 情况3: 只有年份（4位数字）
                elif value.isdigit() and len(value) == 4:
                    # 退化为该年的1月1日
                    return datetime(int(value), 1, 1, tzinfo=timezone.utc)

        return None

    def _sort_papers(self, papers: List[Dict]) -> List[Dict]:
        """Sort papers based on configured sort_by."""
        sort_by = self.config.get("sort_by", DEFAULT_SORT_BY)

        if sort_by == "citation_count" and "citationCount" in papers[0] if papers else False:
            return sorted(papers, key=lambda p: p.get("citationCount", 0), reverse=True)
        elif sort_by == "publicationDate" or sort_by == "publish_date":
            # 改进1：使用新的_extract_publication_date方法
            return sorted(papers, key=lambda p: self._extract_publication_date(p) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        else:  # relevance (default order from APIs)
            return papers

    def _deduplicate_papers(self, papers: List[Dict]) -> List[Dict]:
        """Remove duplicate papers based on title and DOI."""
        seen = set()
        unique_papers = []

        for paper in papers:
            # Create a unique key from title (normalized) and DOI
            title = paper.get("title", "").lower().strip()
            doi = paper.get("doi", "").lower().strip()

            if not title:  # Skip papers without titles
                continue

            # Use title as primary key, DOI as secondary
            key = title if not doi else f"{title}:{doi}"

            if key not in seen:
                seen.add(key)
                unique_papers.append(paper)

        return unique_papers

    def search(self) -> Dict[str, Any]:
        """
        Execute paper search with filtering and ranking.

        根据应用领域智能选择数据源优先级：
        - 统计决策/金融统计: 优先 CrossRef（期刊覆盖最佳），其次 Semantic Scholar
        - 人工智能: 优先 arXiv（最新预印本最多），其次 Semantic Scholar
        - 通用: Semantic Scholar（综合质量最佳），其次 CrossRef

        Returns dict with search results and metadata.
        """
        query = self._build_search_query()

        if not query:
            return {
                "status": "error",
                "error": "No search query provided. Please specify --topic or --keywords.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        all_papers = []
        sources_used = []

        # 根据领域确定数据源优先级
        domain_priority = DOMAIN_SOURCE_PRIORITY.get(self.domain, DOMAIN_SOURCE_PRIORITY["general"])

        # 按优先级调用数据源（改进2：使用固定的api_request_limit确保数据充足）
        for source_name in domain_priority:
            if source_name == "Semantic Scholar":
                # Semantic Scholar: 质量最高，有引用数据
                s2_papers = SemanticScholarAPI.search_papers(
                    query=query,
                    fields="paperId,title,abstract,authors,year,publicationDate,journal,citationCount,doi,url",
                    limit=self.api_request_limit,  # 改进2：固定请求200篇
                    year=self.time_range["start_date"][:4] if self.time_range else None
                )
                if s2_papers:
                    all_papers.extend(s2_papers)
                    sources_used.append("Semantic Scholar")

            elif source_name == "arXiv":
                # arXiv: AI领域最新预印本最多
                arxiv_papers = ArxivAPI.search_papers(
                    query=query,
                    max_results=self.api_request_limit  # 改进2：固定请求200篇
                )
                if arxiv_papers:
                    all_papers.extend(arxiv_papers)
                    sources_used.append("arXiv")

            elif source_name == "CrossRef":
                # CrossRef: 统计学和金融期刊覆盖最佳
                crossref_papers = CrossRefAPI.search_papers(
                    query=query,
                    rows=self.api_request_limit,  # 改进2：固定请求200篇
                    filter_year=self.time_range["start_date"][:4] if self.time_range else None
                )
                if crossref_papers:
                    all_papers.extend(crossref_papers)
                    sources_used.append("CrossRef")

        # Apply filters（改进1：使用精确到天的日期过滤）
        filtered_papers = self._filter_by_date(all_papers)

        # 收集统计信息（改进2：提供透明度）
        api_retrieved = len(all_papers)
        after_filtering = len(filtered_papers)

        deduplicated_papers = self._deduplicate_papers(filtered_papers)
        after_dedup = len(deduplicated_papers)

        sorted_papers = self._sort_papers(deduplicated_papers)

        # 质量筛选步骤（新增核心功能1）
        if self.enable_quality_filter and self.quality_scorer and self.representative_selector:
            # 步骤1: 为每篇论文评分
            for paper in sorted_papers:
                paper["quality_score"] = self.quality_scorer.score_paper(
                    paper,
                    {"query": query, "domain": self.domain}
                )

            # 步骤2: 选择代表性论文（避免重复相似研究）
            sorted_papers = self.representative_selector.select_representative_papers(
                sorted_papers,
                max_count=self.user_max_results
            )
            # 按质量分数重新排序
            sorted_papers = sorted(
                sorted_papers,
                key=lambda p: p.get("quality_score", 0),
                reverse=True
            )

        # Limit to user requested max_results（改进2：使用user_max_results）
        final_papers = sorted_papers[:self.user_max_results]

        # Build result（改进2：添加详细统计信息）
        result = {
            "status": "success",
            "query": query,
            "total_found": len(final_papers),  # 最终返回数量
            "total_available": after_dedup,     # 过滤去重后可用数量
            "total_retrieved": api_retrieved,  # API实际返回数量
            "sources_used": list(set(sources_used)),
            "papers": final_papers,
            "filters_applied": {
                "time_range": self.time_range,
                "language": self.config.get("language", DEFAULT_LANGUAGE),
                "max_results": self.user_max_results,
                "domain": self.domain
            },
            "statistics": {  # 新增：详细统计信息
                "api_retrieved": api_retrieved,       # API返回数量
                "after_date_filtering": after_filtering,  # 日期过滤后
                "after_deduplication": after_dedup,    # 去重后
                "finally_returned": len(final_papers)  # 最终返回
            },
            "quality_filter_enabled": self.enable_quality_filter,  # 新增：质量筛选状态
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return result


# ==================== Output Formatters ====================

def format_as_markdown(result: Dict[str, Any]) -> str:
    """Format search results as Markdown."""
    if result.get("status") == "error":
        return f"❌ 检索失败：{result.get('error')}"

    md = f"# 论文检索结果\n\n"
    md += f"**检索主题**: {result['query']}\n\n"
    md += f"**数据源**: {', '.join(result['sources_used'])}\n\n"
    md += f"**检索时间**: {result['timestamp']}\n\n"
    md += f"**文献数量**: {result['total_found']} 篇\n\n"

    if result['filters_applied']['time_range']:
        tr = result['filters_applied']['time_range']
        md += f"**时间范围**: {tr['start_date']} 至 {tr['end_date']}\n\n"

    md += "---\n\n"

    for i, paper in enumerate(result['papers'], 1):
        md += f"## 论文 #{i}\n\n"

        title = paper.get('title', 'N/A')
        authors = paper.get('authors', [])
        year = paper.get('year') or paper.get('published', '')[:4] if paper.get('published') else 'N/A'

        md += f"**标题**: {title}\n\n"
        md += f"**作者**: {', '.join(str(a) for a in authors[:5])}" + \
              (f" et al. ({len(authors)} authors)" if len(authors) > 5 else "") + "\n\n"
        md += f"**年份**: {year}\n\n"

        if paper.get('journal'):
            md += f"**期刊/会议**: {paper.get('journal')}\n\n"
        if paper.get('doi'):
            md += f"**DOI**: [{paper.get('doi')}](https://doi.org/{paper.get('doi')})\n\n"
        if paper.get('citationCount'):
            md += f"**引用量**: {paper.get('citationCount')}\n\n"
        if paper.get('abstract'):
            abstract = paper.get('abstract', '')[:500]
            md += f"**摘要**: {abstract}{'...' if len(paper.get('abstract', '')) > 500 else ''}\n\n"

        md += "---\n\n"

    return md


def format_as_csv(result: Dict[str, Any]) -> str:
    """Format search results as CSV."""
    if result.get("status") == "error":
        return "error," + result.get("error", "")

    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Title", "Authors", "Year", "Journal", "DOI",
        "CitationCount", "Abstract", "URL"
    ])

    # Rows
    for paper in result.get('papers', []):
        authors = '; '.join(str(a) for a in paper.get('authors', []))
        abstract = (paper.get('abstract', '') or '').replace('\n', ' ')[:200]

        writer.writerow([
            paper.get('title', ''),
            authors,
            paper.get('year') or (paper.get('published', '')[:4] if paper.get('published') else ''),
            paper.get('journal', ''),
            paper.get('doi', ''),
            paper.get('citationCount', ''),
            abstract,
            paper.get('url', '')
        ])

    return output.getvalue()


# ==================== CLI Interface ====================

def main():
    parser = argparse.ArgumentParser(
        description="Search academic papers with filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python paper_search.py --topic "machine learning in education"

  # Search with domain optimization (AI field)
  python paper_search.py --topic "deep learning" --domain ai

  # Search with domain optimization (Statistics field)
  python paper_search.py --topic "bayesian inference" --domain statistics

  # Search with domain optimization (Finance field)
  python paper_search.py --topic "financial risk" --domain finance

  # Search with keywords and time range
  python paper_search.py --keywords "LLM,education" --time-range 3y

  # Search with max results and sort by citations
  python paper_search.py --topic "quantum computing" --max-results 15 --sort-by citation_count

  # Output as markdown
  python paper_search.py --topic "blockchain" --output-format markdown --output results.md
        """
    )

    parser.add_argument("--topic", help="Research topic (e.g., 'machine learning in education')")
    parser.add_argument("--keywords", help="Keywords (comma-separated)")
    parser.add_argument("--time-range", default=DEFAULT_TIME_RANGE,
                       help="Time range (1y, 3y, 5y, 10y, unlimited, or custom like 2020-2023)")
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS,
                       help="Maximum number of papers to return (default: 8)")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE,
                       choices=["zh", "en", "bilingual"],
                       help="Language preference (default: bilingual)")
    parser.add_argument("--sort-by", default=DEFAULT_SORT_BY,
                       choices=["relevance", "citation_count", "publish_date"],
                       help="Sort results by (default: relevance)")
    parser.add_argument("--domain", default=DEFAULT_DOMAIN,
                       choices=["general", "statistics", "ai", "finance"],
                       help="Application domain for optimized source selection (default: general)")
    parser.add_argument("--enable-quality-filter", action="store_true",
                       help="Enable quality filtering and representative paper selection (returns most impactful papers)")
    parser.add_argument("--output-format", default="json",
                       choices=["json", "markdown", "csv"],
                       help="Output format (default: json)")
    parser.add_argument("--output", help="Output file path (default: stdout)")

    args = parser.parse_args()

    # Build config
    config = {
        "research_topic": args.topic or "",
        "keywords": args.keywords or "",
        "time_range": args.time_range,
        "max_results": args.max_results,
        "language": args.language,
        "sort_by": args.sort_by,
        "domain": args.domain,  # 添加应用领域参数
        "enable_quality_filter": args.enable_quality_filter  # 添加质量筛选开关
    }

    # If no topic provided but keywords exist, use keywords as topic
    if not config["research_topic"] and config["keywords"]:
        config["research_topic"] = config["keywords"]

    # Execute search
    engine = PaperSearchEngine(config)
    result = engine.search()

    # Format output
    if args.output_format == "json":
        output = json.dumps(result, indent=2, ensure_ascii=False)
    elif args.output_format == "markdown":
        output = format_as_markdown(result)
    elif args.output_format == "csv":
        output = format_as_csv(result)
    else:
        output = json.dumps(result, indent=2, ensure_ascii=False)

    # Write output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ Results written to {args.output}", file=sys.stderr)
        return 0
    else:
        print(output)
        return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
