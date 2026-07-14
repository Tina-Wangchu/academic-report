"""
多数据源论文搜索模块
已实现数据源：arXiv、Semantic Scholar、OpenAlex（三源并行检索 + 去重）。
预留（暂未实现）：CrossRef、PubMed——rate_limiter 已留限流配置，待后续接入。
"""

import arxiv
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import Paper, SearchIntent
from rate_limiter import get_rate_limiter
from config_manager import get_config_manager

logger = logging.getLogger(__name__)


def _arxiv_pdf_url(entry_id: str) -> str:
    """arXiv entry_id（abs 链接）→ PDF 链接；无法识别 → ''。"""
    if not entry_id:
        return ""
    import re
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([\d]{4}\.[\d]{4,5}(?:v\d+)?)", entry_id)
    return f"https://arxiv.org/pdf/{m.group(1)}" if m else ""


def _parse_date(s) -> Optional[object]:
    """解析 YYYY-MM-DD 字符串 → datetime.date；非法/空 → None。"""
    if not s or not isinstance(s, str):
        return None
    try:
        from datetime import date as _date
        return _date.fromisoformat(s.strip()[:10])
    except (ValueError, TypeError):
        return None


class ArxivSearcher:
    """arXiv 论文搜索器"""

    def __init__(self):
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3
        )

    def search(self, query: str, max_results: int = 50,
               start_date: Optional[datetime] = None,
               end_date: Optional[datetime] = None) -> List[Paper]:
        """
        搜索 arXiv 论文

        Args:
            query: 搜索查询
            max_results: 最大结果数
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            论文列表
        """
        logger.info(f"搜索 arXiv: {query}")

        # 构建查询
        search_query = self._build_query(query, start_date, end_date)

        # 执行搜索
        search = arxiv.Search(
            query=search_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        try:
            for result in self.client.results(search):
                paper = self._convert_to_paper(result)
                papers.append(paper)
                logger.debug(f"找到论文: {paper.title}")

        except Exception as e:
            logger.error(f"arXiv 搜索失败: {e}")

        logger.info(f"arXiv 找到 {len(papers)} 篇论文")
        return papers

    def _build_query(self, query: str, start_date: Optional[datetime],
                    end_date: Optional[datetime]) -> str:
        """构建 arXiv 查询语句"""
        # 基础查询
        search_query = f'all:"{query}"'

        # 添加时间过滤
        if start_date or end_date:
            date_filter = self._build_date_filter(start_date, end_date)
            search_query += f" AND {date_filter}"

        return search_query

    def _build_date_filter(self, start_date: Optional[datetime],
                          end_date: Optional[datetime]) -> str:
        """构建日期过滤器（单区间，arXiv 不支持两个 submittedDate 子句 AND）"""
        if not start_date and not end_date:
            return ""
        start = start_date.strftime("%Y%m%d0000") if start_date else "*"
        end = end_date.strftime("%Y%m%d2359") if end_date else "*"
        return f"submittedDate:[{start} TO {end}]"

    def _convert_to_paper(self, result: arxiv.Result) -> Paper:
        """将 arXiv 结果转换为 Paper 对象"""
        # 提取作者
        authors = [author.name for author in result.authors]

        # 提取年份 + 精确发表日
        published = result.published
        year = published.year if published else datetime.now().year

        return Paper(
            title=result.title,
            authors=authors,
            venue="arXiv",
            year=year,
            doi=result.doi or "",
            published_date=published.date() if published else None,
            abstract=result.summary.replace('\n', ' '),
            keywords=[],
            citation_count=0,  # arXiv 通常没有引用量
            venue_type="preprint",
            ranking="预印本",
            url=result.entry_id,
            source="arxiv",
            pdf_url=_arxiv_pdf_url(result.entry_id),
        )


class SemanticScholarSearcher:
    """Semantic Scholar 论文搜索器"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers['x-api-key'] = api_key
        self.rate_limiter = get_rate_limiter()

    def search(self, query: str, max_results: int = 50,
               start_date: Optional[datetime] = None,
               end_date: Optional[datetime] = None) -> List[Paper]:
        """搜索 Semantic Scholar 论文"""
        logger.info(f"搜索 Semantic Scholar: {query}")

        # 等待限流
        if not self.rate_limiter.wait_if_needed('semantic_scholar'):
            logger.warning("Semantic Scholar 达到限流，跳过")
            return []

        # 构建查询参数
        params = {
            'query': query,
            'limit': min(max_results, 100),  # API 最大100
            'fields': 'paperId,title,authors,year,venue,abstract,citationCount,'
                     'externalIds,url,openAccessPdf,tldr'
        }

        # 添加年份过滤
        if start_date or end_date:
            year_filter = self._build_year_filter(start_date, end_date)
            if year_filter:
                params['year'] = year_filter

        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/search",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            papers = [self._convert_to_paper(item) for item in data.get('data', [])]

            logger.info(f"Semantic Scholar 找到 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            logger.error(f"Semantic Scholar 搜索失败: {e}")
            return []

    def _build_year_filter(self, start_date: Optional[datetime],
                          end_date: Optional[datetime]) -> str:
        """构建年份过滤器"""
        years = []
        if start_date:
            years.append(f"{start_date.year}-")
        if end_date:
            years.append(f"-{end_date.year}")
        return ','.join(years) if years else ""

    def _convert_to_paper(self, item: Dict) -> Paper:
        """将 Semantic Scholar 结果转换为 Paper 对象"""
        # 提取作者
        authors = [author.get('name', '') for author in item.get('authors', [])]

        # 获取 DOI
        external_ids = item.get('externalIds', {})
        doi = external_ids.get('DOI', '')

        # 判断期刊类型
        venue = item.get('venue', 'Unknown')
        venue_type = self._classify_venue(venue)

        # S2 自动生成的 TL;DR（学术概括，{model, text}）
        tldr_field = item.get('tldr')
        tldr = tldr_field.get('text', '') if isinstance(tldr_field, dict) else ''

        return Paper(
            title=item.get('title', ''),
            authors=authors,
            venue=venue,
            year=item.get('year', 0),
            doi=doi,
            published_date=_parse_date(item.get('publicationDate')),
            abstract=item.get('abstract', ''),
            keywords=[],
            citation_count=item.get('citationCount', 0),
            venue_type=venue_type,
            ranking=self._get_ranking(venue_type, item.get('citationCount', 0)),
            url=item.get('url', ''),
            source="semantic_scholar",
            tldr=tldr,
            pdf_url=(item.get('openAccessPdf') or {}).get('url', ''),
        )

    def _classify_venue(self, venue: str) -> str:
        """判断期刊/会议类型"""
        # 顶级会议列表
        top_conferences = [
            'NeurIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI',
            'CVPR', 'ICCV', 'ECCV', 'ACL', 'EMNLP'
        ]
        if any(conf in venue for conf in top_conferences):
            return 'conference'

        # 期刊
        if venue and venue.lower() not in ['arxiv', 'unknown']:
            return 'journal'

        return 'preprint'

    def _get_ranking(self, venue_type: str, citation_count: int) -> str:
        """获取期刊等级"""
        if citation_count >= 100:
            return '高被引'
        elif venue_type == 'journal':
            return '核心期刊'
        elif venue_type == 'conference':
            return '顶会'
        else:
            return '普通'


class OpenAlexSearcher:
    """OpenAlex 论文搜索器"""

    BASE_URL = "https://api.openalex.org"

    def __init__(self):
        self.rate_limiter = get_rate_limiter()

    def search(self, query: str, max_results: int = 50,
               start_date: Optional[datetime] = None,
               end_date: Optional[datetime] = None) -> List[Paper]:
        """搜索 OpenAlex 论文"""
        logger.info(f"搜索 OpenAlex: {query}")

        # OpenAlex 没有限流，但为了礼貌添加延迟
        if not self.rate_limiter.wait_if_needed('openalex'):
            pass

        # 构建查询参数
        params = {
            'search': query,
            'per-page': min(max_results, 200),
            'filter': self._build_filter(start_date, end_date)
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            papers = [self._convert_to_paper(item) for item in data.get('results', [])]

            logger.info(f"OpenAlex 找到 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            logger.error(f"OpenAlex 搜索失败: {e}")
            return []

    def _build_filter(self, start_date: Optional[datetime],
                     end_date: Optional[datetime]) -> str:
        """构建过滤器"""
        filters = []
        if start_date:
            filters.append(f"from_publication_date:{start_date.strftime('%Y-%m-%d')}")
        if end_date:
            filters.append(f"to_publication_date:{end_date.strftime('%Y-%m-%d')}")

        # 只返回学术文章
        filters.append("type:article")

        return ','.join(filters) if filters else ""

    def _convert_to_paper(self, item: Dict) -> Paper:
        """将 OpenAlex 结果转换为 Paper 对象"""
        # 提取作者
        authorships = item.get('authorships', [])
        authors = [a.get('author', {}).get('display_name', '') for a in authorships]

        # 获取期刊信息（primary_location / source 可能为 null）
        primary = item.get('primary_location') or {}
        source = primary.get('source') or {}
        venue = source.get('display_name', 'Unknown')
        venue_type = source.get('type', 'unknown')

        # 获取 DOI（OpenAlex 的 doi 字段为字符串 URL，非 dict）
        doi_field = item.get('doi')
        if isinstance(doi_field, str):
            doi = doi_field.replace('https://doi.org/', '')
        elif isinstance(doi_field, dict):
            doi = (doi_field.get('id', '') or '').replace('https://doi.org/', '')
        else:
            doi = ''

        # 摘要：OpenAlex 不返回 abstract 字符串，需从 abstract_inverted_index 重建
        abstract = self._reconstruct_abstract(item)

        # 开放获取 PDF/全文 URL：best_oa_location.pdf_url 或 open_access.oa_url
        pdf_url = ""
        best_oa = item.get('best_oa_location') or {}
        pdf_url = (best_oa.get('pdf_url') or
                   (item.get('open_access') or {}).get('oa_url') or "")

        return Paper(
            title=item.get('title', ''),
            authors=authors,
            venue=venue,
            year=item.get('publication_year', 0),
            doi=doi,
            published_date=_parse_date(item.get('publication_date')),
            abstract=abstract,
            keywords=[],
            citation_count=item.get('cited_by_count', 0),
            venue_type=venue_type,
            ranking='普通',
            url=item.get('id', ''),
            source="openalex",
            pdf_url=pdf_url or "",
        )

    @staticmethod
    def _reconstruct_abstract(item: Dict) -> str:
        """
        从 OpenAlex 的 abstract_inverted_index 重建摘要文本。
        OpenAlex 不返回 abstract 字符串，而返回 {word: [positions]} 倒排索引；
        按 position 排序拼接即可还原。None/空 → ""。
        """
        inv = item.get('abstract_inverted_index')
        if not inv or not isinstance(inv, dict):
            return ''
        positions = []
        for word, locs in inv.items():
            for pos in locs:
                positions.append((pos, word))
        if not positions:
            return ''
        positions.sort()
        return ' '.join(w for _, w in positions)


# 中文→英文学术术语映射（确保搜索查询始终用英文）
CN_EN_ACADEMIC = {
    "深度学习": "deep learning", "机器学习": "machine learning",
    "神经网络": "neural network", "自然语言处理": "natural language processing",
    "计算机视觉": "computer vision", "强化学习": "reinforcement learning",
    "大语言模型": "large language model", "生成对抗网络": "generative adversarial network",
    "图神经网络": "graph neural network", "联邦学习": "federated learning",
    "迁移学习": "transfer learning", "无监督学习": "unsupervised learning",
    "监督学习": "supervised learning", "推荐系统": "recommendation system",
    "知识图谱": "knowledge graph", "自动驾驶": "autonomous driving",
    "机器人": "robotics", "统计学习": "statistical learning",
    "统计学": "statistics", "时间序列": "time series",
    "异常检测": "anomaly detection", "数据挖掘": "data mining",
    "图像分割": "image segmentation", "目标检测": "object detection",
    "语音识别": "speech recognition", "文本分类": "text classification",
    "情感分析": "sentiment analysis", "机器翻译": "machine translation",
    "问答系统": "question answering", "贝叶斯": "Bayesian",
    "马尔可夫": "Markov", "优化算法": "optimization algorithm",
    "梯度下降": "gradient descent", "反向传播": "backpropagation",
    "过拟合": "overfitting", "正则化": "regularization",
    "卷积": "convolutional", "注意力机制": "attention mechanism",
    "预训练": "pre-training", "微调": "fine-tuning",
    "量化": "quantization", "蒸馏": "distillation",
    "对抗训练": "adversarial training", "扩散模型": "diffusion model",
    "对比学习": "contrastive learning", "自监督学习": "self-supervised learning",
    "元学习": "meta-learning", "多模态": "multimodal",
    "因果推断": "causal inference", "半监督学习": "semi-supervised learning",
    "生成模型": "generative model", "排名学习": "learning to rank",
    "排序": "ranking", "分类": "classification",
    "回归": "regression", "聚类": "clustering",
    "降维": "dimensionality reduction", "特征提取": "feature extraction",
    "信号处理": "signal processing", "网络安全": "network security",
    "入侵检测": "intrusion detection", "恶意软件检测": "malware detection",
    "漏洞检测": "vulnerability detection", "区块链": "blockchain",
    "量子计算": "quantum computing", "边缘计算": "edge computing",
    "云计算": "cloud computing", "物联网": "internet of things",
    "5G": "5G", "6G": "6G",
}


def _to_english_query(text: str) -> str:
    """将查询中的中文术语翻译为英文（确保搜索始终用英文）。未知中文保留原样。"""
    for cn, en in CN_EN_ACADEMIC.items():
        text = text.replace(cn, en)
    return text.strip()


class PaperSearcher:
    """多数据源论文搜索器 - 主类"""

    def __init__(self):
        """初始化搜索器"""
        self.config = get_config_manager()

        # 获取 API 密钥
        api_keys = self.config.get_api_keys()

        # 初始化各数据源搜索器
        self.searchers = {
            'arxiv': ArxivSearcher(),
            'semantic_scholar': SemanticScholarSearcher(api_keys.get('semantic_scholar', '')),
            'openalex': OpenAlexSearcher(),
        }

    def search(self, intent: SearchIntent) -> List[Paper]:
        """
        执行多数据源搜索

        Args:
            intent: 搜索意图

        Returns:
            合并后的论文列表
        """
        logger.info(f"开始多数据源搜索: {intent.query}")

        # 构建搜索查询
        query = self._build_search_query(intent)

        # 获取最大结果数：优先用 intent.max_results，回退到 config
        max_results = intent.max_results or self.config.get_max_results()

        # 并行搜索所有数据源
        all_papers = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    searcher.search,
                    query,
                    max_results,
                    intent.start_date,
                    intent.end_date
                ): source
                for source, searcher in self.searchers.items()
            }

            for future in as_completed(futures):
                source = futures[future]
                try:
                    papers = future.result()
                    all_papers.extend(papers)
                    logger.info(f"{source} 搜索完成: {len(papers)} 篇")
                except Exception as e:
                    logger.error(f"{source} 搜索失败: {e}")

        logger.info(f"总共找到 {len(all_papers)} 篇论文（合并前）")

        # 合并和去重
        unique_papers = self._deduplicate(all_papers)

        logger.info(f"去重后: {len(unique_papers)} 篇论文")

        return unique_papers

    def _build_search_query(self, intent: SearchIntent) -> str:
        """构建搜索查询——始终使用英文（中文术语翻译为英文，搜索语言 ≠ 报告语言）"""
        raw = ' '.join(intent.keywords) if intent.keywords else intent.query
        return _to_english_query(raw)

    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """
        去重论文

        基于 DOI 和标题；优先保留有 DOI 的记录。
        注意：按 DOI 命中时也要记录标题，否则后续同 DOI 的重复会从标题分支漏网。
        """
        seen_dois = set()
        seen_titles = set()
        unique_papers = []

        for paper in papers:
            title_key = paper.title.lower()
            # DOI 重复 → 跳过
            if paper.doi and paper.doi in seen_dois:
                continue
            # 标题重复 → 跳过
            if title_key in seen_titles:
                continue
            if paper.doi:
                seen_dois.add(paper.doi)
            seen_titles.add(title_key)
            unique_papers.append(paper)

        return unique_papers


def main():
    """命令行入口"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='多数据源论文搜索')
    parser.add_argument('--query', type=str, required=True, help='搜索查询')
    parser.add_argument('--max-results', type=int, default=50, help='最大结果数')
    parser.add_argument('--output', type=str, help='输出JSON文件路径')
    parser.add_argument('--start-date', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='结束日期 (YYYY-MM-DD)')

    args = parser.parse_args()

    # 解析日期
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else None
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else None

    # 创建搜索意图（简化版）
    from utils import SearchIntent
    intent = SearchIntent(
        query=args.query,
        keywords=[],
        research_field='general',
        language='bilingual',
        start_date=start_date,
        end_date=end_date,
        paper_types=['journal', 'conference'],
        filters={},
        max_results=args.max_results
    )

    # 执行搜索
    searcher = PaperSearcher()
    papers = searcher.search(intent)

    # 输出结果
    print(f"找到 {len(papers)} 篇论文")

    # 保存到文件
    if args.output:
        papers_data = [paper.to_dict() for paper in papers]
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(papers_data, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")


if __name__ == '__main__':
    main()
