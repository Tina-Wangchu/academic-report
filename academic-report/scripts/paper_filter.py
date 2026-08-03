"""
文献筛选、分类、排序模块（模块3 / Module 3）

职责：
1. 质量过滤——按搜索意图与全局配置剔除不符合条件的论文
   （高被引 / SCI·EI / 核心期刊 / 最小引用量 / 是否含预印本）。
2. 优先级排序——高被引 > 顶刊 > 顶会 > SCI/EI > 普通期刊 > 预印本，
   并以引用量、发表年份作为加分与 tie-breaker。
3. 热点聚类——把相似 / 相关研究方向的论文归为同一「热点」，
   已知 AI 主题用关键词词典命中，未知领域用标题+摘要关键词频次兜底聚类，
   避免非 AI 学科（如统计、生物）全部落进「其他」。
4. 热点主题介绍生成——按 报告格式设计.md §5.1，为每个热点产出
   一行主题简介；该方法从 report_generator 迁入（见实施计划映射表，
   Option B：分层归属 paper_filter，奠基性参考与方向级整体分析归 paper_analyzer）。

依赖：utils.Paper / utils.SearchIntent，config_manager.get_config_manager()
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from config_manager import get_config_manager
from utils import Paper, SearchIntent

logger = logging.getLogger(__name__)

# 英文停用词，用于未知领域的兜底关键词抽取（含通用学术虚词，避免形成噪声热点）
_EN_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "based", "via", "using", "by", "from", "as", "is", "are", "be", "we",
    "our", "this", "that", "these", "those", "it", "its", "at", "which",
    "can", "into", "such", "than", "then", "their", "they", "but", "not",
    "no", "any", "all", "more", "most", "between", "through", "over", "under",
    "also", "has", "have", "had", "was", "were", "will", "would", "could",
    # 通用学术虚词 / 填充词（非主题词，易被误选为热点名）
    "approach", "approaches", "application", "applications", "applying",
    "study", "studies", "method", "methods", "methodological",
    "result", "results", "analysis", "analyses", "analytical",
    "research", "paper", "papers", "work", "works",
    "propose", "proposed", "proposes", "present", "presented", "presents",
    "show", "shows", "shown", "demonstrate", "demonstrates", "demonstrated",
    "novel", "new", "introduction", "tutorial", "review", "survey",
    "recent", "evaluation", "assess", "assessment", "accurate",
    "associated", "dynamics", "beyond", "clinical", "fields", "exponent",
    "model", "models", "framework", "performance", "problem", "problems",
    "data", "dataset", "datasets", "task", "tasks", "training", "learning",
    "system", "systems", "method", "effect", "effects", "impact",
    "two", "three", "first", "second", "one", "multiple", "different",
    "high", "low", "large", "small", "general", "main", "key",
}


class PaperFilter:
    """文献筛选和排序器"""

    # 顶级期刊列表
    TOP_JOURNALS = {
        "Nature", "Science", "Cell",
        "Nature Communications", "Science Advances",
        "Proceedings of the National Academy of Sciences",
        "PNAS",
    }

    # 顶会列表
    TOP_CONFERENCES = {
        "NeurIPS", "ICML", "ICLR", "AAAI", "IJCAI",
        "CVPR", "ICCV", "ECCV", "ACL", "EMNLP",
        "ICSE", "SIGMOD", "VLDB", "KDD",
    }

    # SCI/EI 出版商 / 期刊特征（简化判断）
    SCI_EI_KEYWORDS = {
        "IEEE", "ACM", "Springer", "Elsevier",
        "Oxford", "Cambridge", "Nature", "Science",
    }

    # 已知 AI 研究主题关键词（中英），用于热点命中
    TOPIC_KEYWORDS: Dict[str, List[str]] = {
        "深度学习": ["deep learning", "neural network", "神经网络", "深度学习"],
        "自然语言处理": ["nlp", "natural language", "transformer", "bert", "gpt",
                       "语言模型", "文本"],
        "计算机视觉": ["vision", "image", "visual", "cv", "图像", "视觉", "检测"],
        "强化学习": ["reinforcement", "rl", "强化学习"],
        "图神经网络": ["graph", "gnn", "图神经", "图网络"],
        "生成模型": ["generative", "gan", "vae", "diffusion", "生成模型", "扩散"],
        "大语言模型": ["llm", "large language model", "大语言模型", "大模型"],
    }

    def __init__(self):
        """初始化筛选器，注入全局配置（实例属性，避免模块级副作用）"""
        self.config = get_config_manager()

    # ------------------------------------------------------------------ #
    # 公共入口
    # ------------------------------------------------------------------ #

    def filter_and_sort(self, papers: List[Paper], intent: SearchIntent,
                        limit: Optional[int] = None) -> List[Paper]:
        """
        执行完整的筛选和排序流程。

        Args:
            papers: 原始论文列表（通常是去重后的检索结果）
            intent: 搜索意图（提供 filters 等筛选条件）
            limit: 可选，仅保留前 N 篇（None 表示不截断）

        Returns:
            筛选并按优先级排序后的论文列表
        """
        logger.info("开始筛选 %d 篇论文", len(papers))

        # 0. 时间范围过滤（搜索层 API 日期过滤的安全网，按年份比较）
        in_range = self._filter_by_time(papers, intent)

        # 1. 质量过滤
        filtered = self._apply_quality_filters(in_range, intent)

        # 2. 优先级排序；若用户要求「最新研究」，给近期论文加分
        latest = bool((intent.filters or {}).get("latest_research", False))
        sorted_papers = self._sort_by_priority(filtered, latest=latest)

        # 3. 可选截断
        if limit is not None and limit > 0:
            sorted_papers = sorted_papers[:limit]

        logger.info("筛选后剩余 %d 篇论文", len(sorted_papers))
        return sorted_papers

    def classify_by_topic(self, papers: List[Paper],
                          topic_hint: str = "") -> Dict[str, List[Paper]]:
        """
        按内容主题把论文聚类为「热点」。

        - 命中已知 AI 主题词典的，按命中关键词数最多的主题归类；
        - 未命中的论文，用标题+摘要的关键词频次兜底聚类（非 AI 学科友好），
          优先选取与 `topic_hint`（查询+领域）相关的关键词；
        - **收敛规则（报告格式设计.md §10.3）**：成员 <2 篇的桶（含已知主题
          单篇误分类与兜底单篇）并入「其他」，避免单论文噪声热点；
        - 仍无法抽取关键词的，归入「其他」。

        返回的 dict 按热点聚合优先级降序插入（「其他」恒置末尾）。
        """
        topic_papers: Dict[str, List[Paper]] = defaultdict(list)

        # 第一遍：已知主题命中
        unmatched: List[Paper] = []
        for paper in papers:
            topic = self._match_known_topic(paper)
            if topic is not None:
                topic_papers[topic].append(paper)
            else:
                unmatched.append(paper)

        # 第二遍：未知论文按关键词频次兜底聚类（倾向查询主题）
        keyword_buckets: Dict[str, List[Paper]] = defaultdict(list)
        leftover: List[Paper] = []
        for paper in unmatched:
            kw = self._extract_top_keyword(paper, topic_hint)
            if kw:
                keyword_buckets[kw].append(paper)
            else:
                leftover.append(paper)

        for kw, kw_papers in keyword_buckets.items():
            topic_papers[self._humanize_keyword(kw)].extend(kw_papers)
        if leftover:
            topic_papers["其他"].extend(leftover)

        # 收敛：<2 篇的桶并入「其他」（消除单论文噪声热点）
        misc: List[Paper] = []
        consolidated: Dict[str, List[Paper]] = defaultdict(list)
        for name, ps in topic_papers.items():
            if name == "其他":
                misc.extend(ps)
            elif len(ps) >= 2:
                consolidated[name] = ps
            else:
                misc.extend(ps)
        if misc:
            consolidated["其他"] = misc

        # 按聚合权重降序；「其他」恒置末尾
        ordered = dict(
            sorted(
                ((k, v) for k, v in consolidated.items() if k != "其他"),
                key=lambda kv: self._hotspot_weight(kv[1]),
                reverse=True,
            )
        )
        if "其他" in consolidated:
            ordered["其他"] = consolidated["其他"]

        logger.info("分类结果: %s", {k: len(v) for k, v in ordered.items()})
        return ordered

    def generate_hotspot_intro(self, topic_name: str,
                               papers: List[Paper]) -> str:
        """
        为一个热点生成一行主题介绍（报告格式设计.md §5.1，Option B 迁入）。

        介绍需落在该热点的真实论文上：高频关键词 + 代表性（最高被引）工作，
        避免空泛套话。完整版本可由 LLM 改写为更流畅的方向性简介。
        """
        if not papers:
            return f"本热点「{topic_name}」暂无论文。"

        # 高频关键词（来自已标注 keywords）
        kw_counter: Counter = Counter()
        for p in papers:
            kw_counter.update(p.keywords)
        common = [kw for kw, _ in kw_counter.most_common(3)]

        # 代表性论文：被引最高（并列取年份较新）
        rep = max(
            papers,
            key=lambda p: (p.citation_count, getattr(p, "year", 0) or 0),
        )

        parts = [f"本热点聚焦「{topic_name}」方向，共收录 {len(papers)} 篇论文"]
        if common:
            parts.append(f"，高频关键词包括 {'、'.join(common)}")
        parts.append(
            f"；代表性工作为《{rep.title}》（{rep.year}，引用 {rep.citation_count}）。"
        )
        return "".join(parts)

    # ------------------------------------------------------------------ #
    # 时间过滤
    # ------------------------------------------------------------------ #

    def _filter_by_time(self, papers: List[Paper],
                        intent: SearchIntent) -> List[Paper]:
        """
        按搜索意图的时间范围做兜底过滤（搜索层 API 日期过滤之下的安全网）。

        - **优先日级**（`paper.published_date`，YYYY-MM-DD）；缺失则回退**年份级**
          （`paper.year`）——避免误删无精确日期的有效文献。
        - `published_date` 与 `year` 都缺失 → 保留（无法判定）。
        - `intent.start_date` / `end_date` 任一为 None 时该侧不设限；闭区间含端点。
        """
        start = intent.start_date
        end = intent.end_date
        if not start and not end:
            return papers

        start_year = start.year if start else None
        end_year = end.year if end else None
        start_date = start.date() if start else None
        end_date = end.date() if end else None

        kept: List[Paper] = []
        dropped = 0
        for p in papers:
            # 既无精确日期又无年份 → 保留（无法判定）
            if not p.published_date and (not p.year or p.year <= 0):
                kept.append(p)
                continue
            # 优先日级比较
            if p.published_date is not None:
                if start_date is not None and p.published_date < start_date:
                    dropped += 1
                    continue
                if end_date is not None and p.published_date > end_date:
                    dropped += 1
                    continue
            else:  # 回退年份级
                if start_year is not None and p.year < start_year:
                    dropped += 1
                    continue
                if end_year is not None and p.year > end_year:
                    dropped += 1
                    continue
            kept.append(p)

        if dropped:
            window = ""
            if start_year and end_year:
                window = f"{start_year}-{end_year}"
            elif start_year:
                window = f"≥{start_year}"
            elif end_year:
                window = f"≤{end_year}"
            logger.info("时间过滤(%s)剔除 %d 篇，保留 %d 篇",
                        window, dropped, len(kept))
        return kept

    # ------------------------------------------------------------------ #
    # 质量过滤
    # ------------------------------------------------------------------ #

    def _apply_quality_filters(self, papers: List[Paper],
                               intent: SearchIntent) -> List[Paper]:
        """按意图 filters 与全局配置应用质量过滤"""
        filters = intent.filters or {}
        filtered = list(papers)

        # 高被引筛选（意图显式要求，或全局配置开启）
        highly_cited_threshold = self.config.get_highly_cited_threshold()
        want_highly_cited = bool(filters.get("highly_cited", False)) or \
            self.config.is_filter_highly_cited()
        if want_highly_cited and highly_cited_threshold > 0:
            filtered = [p for p in filtered
                        if p.citation_count >= highly_cited_threshold]
            logger.info("高被引筛选(≥%d): %d 篇",
                        highly_cited_threshold, len(filtered))

        # SCI/EI 筛选
        if bool(filters.get("sci_ei", False)) or self.config.is_sci_ei_only():
            filtered = [p for p in filtered if self._is_sci_ei(p)]
            logger.info("SCI/EI 筛选: %d 篇", len(filtered))

        # 核心期刊（顶刊）筛选
        if bool(filters.get("core_journal", False)):
            filtered = [p for p in filtered if self._is_top_journal(p)]
            logger.info("核心期刊筛选: %d 篇", len(filtered))

        # 最小引用量（全局配置）
        min_citations = self.config.get_min_citation_count()
        if min_citations > 0:
            filtered = [p for p in filtered
                        if p.citation_count >= min_citations]
            logger.info("最小引用量筛选(≥%d): %d 篇",
                        min_citations, len(filtered))

        # 排除预印本（若配置要求）
        if not self.config.is_include_preprints():
            filtered = [p for p in filtered if p.venue_type != "preprint"]
            logger.info("剔除预印本: %d 篇", len(filtered))

        # 剔除明显非学术 / 空标题文献
        filtered = [p for p in filtered if self._is_academic(p)]

        return filtered

    # ------------------------------------------------------------------ #
    # 优先级排序
    # ------------------------------------------------------------------ #

    def _priority_score(self, paper: Paper, latest: bool = False) -> int:
        """
        计算单篇论文的优先级得分（实施计划 §模块3 评分规则）。

        - 高被引 ≥100: +100；≥50: +50
        - 顶刊 +90 / 顶会 +80 / SCI·EI +70 / 普通期刊 +50 / 预印本 +30
        - 引用量加分: +min(citation_count, 50)
        - latest_research（用户要求「最新」）: 近 2 个自然年的论文 +40
        """
        score = 0

        # 引用量分层（互斥）
        if paper.citation_count >= 100:
            score += 100
        elif paper.citation_count >= 50:
            score += 50

        # 发表渠道分层（互斥）
        if self._is_top_journal(paper):
            score += 90
        elif self._is_top_conference(paper):
            score += 80
        elif self._is_sci_ei(paper):
            score += 70
        elif paper.venue_type == "journal":
            score += 50
        elif paper.venue_type == "preprint":
            score += 30

        # 引用量加分（封顶 50）
        score += min(paper.citation_count, 50)

        # 最新研究：近期论文加分（让 latest_research 不再是死特性）
        if latest and paper.year:
            from datetime import datetime as _dt
            if paper.year >= (_dt.now().year - 1):
                score += 40
        return score

    def _sort_by_priority(self, papers: List[Paper],
                          latest: bool = False) -> List[Paper]:
        """
        按优先级排序：得分降序，并列时按发表年份降序（新者优先）。
        latest=True 时近期论文获额外加分（对应 latest_research 筛选条件）。
        """
        return sorted(
            papers,
            key=lambda p: (-self._priority_score(p, latest), -(p.year or 0)),
        )

    def _hotspot_weight(self, papers: List[Paper]) -> int:
        """热点的聚合权重 = 成员优先级得分之和（用于热点排序）"""
        return sum(self._priority_score(p) for p in papers)

    # ------------------------------------------------------------------ #
    # 主题 / 关键词抽取
    # ------------------------------------------------------------------ #

    def _match_known_topic(self, paper: Paper) -> Optional[str]:
        """若论文命中已知 AI 主题词典，返回命中关键词最多的主题名，否则 None"""
        content = f"{paper.title} {paper.abstract}".lower()
        best_topic: Optional[str] = None
        best_hits = 0
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw.lower() in content)
            if hits > best_hits:
                best_hits = hits
                best_topic = topic
        return best_topic

    @staticmethod
    def _extract_top_keyword(paper: Paper,
                             topic_hint: str = "") -> Optional[str]:
        """
        从标题+摘要抽取代表性关键词（兜底聚类用）。
        - 优先复用已标注 keywords，且优先与 `topic_hint` 相关者；
        - 否则做英文 token 频次统计，过滤停用词/通用虚词，优先查询相关词。
        """
        hint = set(re.findall(r"[a-z][a-z0-9-]{2,}", (topic_hint or "").lower()))

        # 优先使用已标注 keywords（与查询相关者优先）
        if paper.keywords:
            for kw in paper.keywords:
                if kw.lower() in hint:
                    return kw
            return paper.keywords[0]

        text = f"{paper.title} {paper.abstract}".lower()
        tokens = re.findall(r"[a-z][a-z0-9-]{2,}", text)  # ≥3 字符英文 token
        freq: Counter = Counter()
        for tok in tokens:
            if tok in _EN_STOPWORDS:
                continue
            freq[tok] += 1

        if not freq:
            return None
        # 优先与查询相关的 token；否则取频次最高
        hint_pool = [(t, f) for t, f in freq.items() if t in hint]
        pool = hint_pool if hint_pool else list(freq.items())
        return max(pool, key=lambda kv: (kv[1], -ord(kv[0][0])))[0]

    @staticmethod
    def _humanize_keyword(keyword: str) -> str:
        """把兜底关键词整理成可读的热点名（Title Case）"""
        cleaned = keyword.replace("-", " ").strip()
        return cleaned.title() if cleaned else "其他"

    # ------------------------------------------------------------------ #
    # 渠道判定
    # ------------------------------------------------------------------ #

    def _is_top_journal(self, paper: Paper) -> bool:
        """是否顶级期刊（Nature/Science/Cell 等）"""
        venue = paper.venue or ""
        return any(j in venue for j in self.TOP_JOURNALS)

    def _is_top_conference(self, paper: Paper) -> bool:
        """是否顶级会议（NeurIPS/ICML/CVPR 等）"""
        venue = paper.venue or ""
        return any(c in venue for c in self.TOP_CONFERENCES)

    def _is_sci_ei(self, paper: Paper) -> bool:
        """是否 SCI/EI 索引（按出版商 / 期刊特征简化判断）"""
        venue = paper.venue or ""
        return any(k in venue for k in self.SCI_EI_KEYWORDS)

    @staticmethod
    def _is_academic(paper: Paper) -> bool:
        """剔除明显非学术 / 空标题文献"""
        title = (paper.title or "").strip()
        if not title:
            return False
        # 标题里出现明显的资讯 / 广告特征词则剔除
        noise = {"call for papers", "editorial", "table of contents"}
        return title.lower() not in noise


# ---------------------------------------------------------------------- #
# 命令行入口（便于手工调试）
# ---------------------------------------------------------------------- #

def main() -> None:
    """简单自检：构造若干样例论文，演示筛选 / 排序 / 聚类 / 介绍生成"""
    import json
    from utils import SearchIntent

    sample = [
        Paper(title="DDIM-Solver: Fast Sampling for Diffusion Models",
              authors=["Zhang", "Wang"], venue="NeurIPS", year=2024, doi="",
              abstract="We propose a novel ODE solver for diffusion model "
                       "sampling acceleration, reducing steps to 10.",
              keywords=["diffusion", "sampling"], citation_count=187,
              venue_type="conference", ranking="顶会", source="arxiv"),
        Paper(title="A Survey of Transformers in NLP",
              authors=["Lee"], venue="ACL", year=2023, doi="",
              abstract="This survey reviews transformer architectures for "
                       "natural language processing tasks.",
              keywords=["transformer", "nlp"], citation_count=320,
              venue_type="conference", ranking="顶会", source="openalex"),
        Paper(title="Note on arXiv preprint statistics",
              authors=["Doe"], venue="arXiv", year=2025, doi="",
              abstract="A short preprint about statistics.",
              keywords=[], citation_count=0,
              venue_type="preprint", ranking="预印本", source="arxiv"),
    ]

    pf = PaperFilter()
    intent = SearchIntent(query="machine learning", keywords=[],
                          research_field="cs", language="bilingual",
                          max_results=50)

    sorted_papers = pf.filter_and_sort(sample, intent)
    print(json.dumps([p.title for p in sorted_papers], ensure_ascii=False,
                     indent=2))

    for topic, papers in pf.classify_by_topic(sorted_papers).items():
        print(f"[{topic}] {len(papers)} 篇")
        print("  介绍:", pf.generate_hotspot_intro(topic, papers))


if __name__ == "__main__":
    main()
