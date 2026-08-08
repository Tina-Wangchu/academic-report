"""
论文信息提取与深度分析模块（模块4 / Module 4）

职责：
1. 单篇论文结构化信息提取——核心研究内容、创新点、核心结论、研究价值与应用场景。
2. APA 7th 引用格式生成（委托 utils.format_apa_citation）。
3. 方向级**整体分析**（Option B：从 report_generator 迁入）。
4. 方向级**奠基性参考论文查找**（Option B：从 report_generator 迁入，并真正调用
   Semantic Scholar references API，找出被本热点论文广泛引用的高被引经典工作）。

设计原则：
- 所有网络调用都有**优雅降级**：限流 / 离线 / API 异常时回退到基于本热点论文的
  启发式结论，绝不编造引用。
- 网络层（_collect_raw_references）与纯排序层（_rank_references）分离，便于单测。
- 规则版提取（非 LLM）；LLM 深度分析留作未来增强。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import requests

from config_manager import get_config_manager
from rate_limiter import get_rate_limiter
from utils import Paper, format_apa_citation

logger = logging.getLogger(__name__)


@dataclass
class Reference:
    """一篇参考文献（奠基性论文查找的中间结构）"""
    title: str
    authors: List[str] = field(default_factory=list)
    year: int = 0
    citation_count: int = 0
    paper_id: str = ""
    influential: bool = False


class CitationFinder:
    """
    通过 Semantic Scholar references API 查找「奠基性参考论文」。

    思路：对热点内的每篇论文，取其参考文献（references，即它引用了谁）；
    跨热点论文聚合后，「被本热点越多论文引用 + 全球引用越高 + 年份越早」的参考，
    就越可能是该方向的奠基性经典工作（报告格式设计.md §5.4）。
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None,
                 rate_limiter=None, max_papers_to_probe: int = 5):
        """
        Args:
            api_key: Semantic Scholar API key（可选，提升限流额度）
            rate_limiter: 限流器（默认全局实例）
            max_papers_to_probe: 为控制请求数，最多探查热点内多少篇论文的参考文献
        """
        self.headers = {"x-api-key": api_key} if api_key else {}
        self.rate_limiter = rate_limiter or get_rate_limiter()
        self.timeout = 30
        self.max_papers_to_probe = max_papers_to_probe
        self._id_cache: Dict[str, Optional[str]] = {}

    # ----------------------------- 网络层 ------------------------------ #

    def _get(self, path: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """带限流与异常兜底的 GET；失败返回 None。"""
        if not self.rate_limiter.wait_if_needed("semantic_scholar"):
            logger.warning("Semantic Scholar 达到限流，跳过奠基论文查找")
            return None
        try:
            resp = requests.get(f"{self.BASE_URL}{path}",
                                headers=self.headers, params=params,
                                timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.debug("Semantic Scholar 请求失败 %s: %s", path, e)
            return None

    def resolve_paper_id(self, paper: Paper) -> Optional[str]:
        """把本地 Paper 解析为 Semantic Scholar paperId（先标题匹配，后 DOI）"""
        cache_key = paper.doi or paper.title.strip().lower()
        if cache_key in self._id_cache:
            return self._id_cache[cache_key]

        pid = None
        # 1. 标题匹配（最稳，避免 DOI 中的斜杠路径问题）
        if paper.title:
            pid = self._match_by_title(paper.title)
        # 2. DOI 兜底
        if not pid and paper.doi:
            pid = self._lookup_by_doi(paper.doi)

        self._id_cache[cache_key] = pid
        return pid

    def _match_by_title(self, title: str) -> Optional[str]:
        data = self._get(
            "/paper/search/match",
            params={"query": title, "fields": "paperId,title"},
        )
        items = (data or {}).get("data") or []
        if items:
            return items[0].get("paperId")
        return None

    def _lookup_by_doi(self, doi: str) -> Optional[str]:
        from urllib.parse import quote
        data = self._get(f"/paper/DOI:{quote(doi, safe='')}",
                         params={"fields": "paperId"})
        if data and data.get("paperId"):
            return data["paperId"]
        return None

    def fetch_references(self, paper_id: str) -> List[Reference]:
        """取一篇论文的参考文献列表（它引用了谁）"""
        data = self._get(
            f"/paper/{paper_id}/references",
            params={
                "fields": "title,authors,year,citationCount,externalIds",
                "limit": 100,
            },
        )
        if not data:
            return []

        refs: List[Reference] = []
        for entry in data.get("data", []):
            # S2 references 端点把被引论文嵌套在 citedPaper；防御性兼容多种形态
            node = (entry.get("citedPaper")
                    or entry.get("citingPaper")
                    or entry.get("paper")
                    or entry)
            if not isinstance(node, dict) or not node.get("title"):
                continue
            refs.append(Reference(
                title=node.get("title", "").strip(),
                authors=[a.get("name", "") for a in node.get("authors", [])],
                year=int(node.get("year") or 0),
                citation_count=int(node.get("citationCount") or 0),
                paper_id=node.get("paperId", ""),
                influential=bool(entry.get("isInfluential", False)),
            ))
        return refs

    def collect_raw_references(self, papers: List[Paper]
                               ) -> List[Tuple[int, Reference]]:
        """
        网络层：对热点内（最多 max_papers_to_probe 篇）论文取参考文献，
        返回 (源论文下标, 参考文献) 列表。可能抛异常或返回空。
        """
        raw: List[Tuple[int, Reference]] = []
        for idx, paper in enumerate(papers[:self.max_papers_to_probe]):
            pid = self.resolve_paper_id(paper)
            if not pid:
                continue
            for ref in self.fetch_references(pid):
                raw.append((idx, ref))
        return raw

    # ----------------------------- 排序层（纯函数） -------------------- #

    @staticmethod
    def _norm_title(title: str) -> str:
        return (title or "").strip().lower()

    def rank_references(self, raw: List[Tuple[int, Reference]],
                        hotspot_titles: Set[str],
                        top_n: int = 3) -> List[str]:
        """
        纯函数：聚合、去重、排序、格式化奠基性参考论文。

        排序键：被本热点引用的源论文数 ↓ > 全球引用量 ↓ > 年份 ↑（越早越奠基）
        过滤：剔除热点自身的论文成员；要求至少被 1 篇引用。
        """
        # 聚合：paper_id（或规范化标题）→ (Reference, 引用它的源下标集合)
        agg: Dict[str, Dict] = {}
        for src_idx, ref in raw:
            key = ref.paper_id or self._norm_title(ref.title)
            if not key:
                continue
            slot = agg.setdefault(key, {"ref": ref, "sources": set()})
            slot["sources"].add(src_idx)
            # 保留信息更全的一条（citation_count 更大者）
            if ref.citation_count > slot["ref"].citation_count:
                slot["ref"] = ref

        candidates: List[Tuple[Reference, int]] = []
        for key, slot in agg.items():
            ref = slot["ref"]
            # 排除热点自身成员（避免把收录论文当成奠基参考）
            if self._norm_title(ref.title) in hotspot_titles:
                continue
            n_sources = len(slot["sources"])
            candidates.append((ref, n_sources))

        # 排序
        candidates.sort(key=lambda x: (
            -x[1],                       # 被本热点引用数 ↓
            -x[0].citation_count,        # 全球引用量 ↓
            x[0].year or 9999,           # 年份 ↑（越早越前）
        ))

        result: List[str] = []
        for ref, n_sources in candidates[:top_n]:
            note = f"被本热点 {n_sources} 篇引用"
            if ref.citation_count:
                note += f"，全球引用 {ref.citation_count}"
            if ref.influential:
                note += "（高影响力引用）"
            result.append(
                f"{self._short_authors(ref.authors)} ({ref.year}): "
                f"{ref.title} —— {note}"
            )
        return result

    @staticmethod
    def _short_authors(authors: List[str]) -> str:
        authors = [a for a in (authors or []) if a]
        if not authors:
            return "佚名"
        if len(authors) <= 3:
            return ", ".join(authors)
        return f"{authors[0]} 等"


class AbstractSummarizer:
    """
    论文摘要生成（abstract_improvement.md）。

    目标：每篇 **200-300 字** 的**完整**学术摘要（覆盖问题/方法/数据集/结果/贡献），
    而非草率的短抽取。策略：
    - 有正文摘要 → 用「去填充后的完整摘要」（仅超长才剔除低信息句），保证完整覆盖；
    - 无正文摘要但有 S2 TL;DR → 用 TL;DR（回退，TL;DR 通常偏短）；
    - 均无 → 空（报告走占位）。

    LLM 生成式摘要（Tier 2）留待 Phase 3。
    """

    # 摘要目标长度上限（≈ 200-300 字 / 250-300 英文词）；仅超长才去填充
    TARGET_MAX_CHARS = 1500

    # 数据集 / 评测信号词
    DATASET_MARKERS = ("dataset", "benchmark", "corpus", "evaluate", "evaluation",
                       "metric", "accuracy", "f1", "score", "test set",
                       "outperform", "state-of-the-art")
    # 贡献信号词
    CONTRIBUTION_MARKERS = ("contribute", "contribution", "novel", "first to",
                            "we propose", "we introduce", "we present",
                            "we develop", "enables", "we show that")

    def summarize(self, paper: Paper) -> str:
        """
        生成本篇论文的 Abstract 段（目标 200-300 字）。
        优先用完整摘要（去填充）；摘要缺失时回退 S2 TL;DR；均无则空。
        """
        condensed = self._from_rules(paper)
        if condensed:
            return condensed
        if paper.tldr:
            return self._trim(paper.tldr)
        return ""

    @staticmethod
    def _trim(text: str, max_chars: int = 1500) -> str:
        """限长，截到句边界，无 mid-sentence 省略号。"""
        text = (text or "").replace("\n", " ").strip()
        if len(text) <= max_chars:
            return text
        cut = text[:max_chars]
        last_period = cut.rfind(". ")
        if last_period > max_chars * 0.6:
            return cut[:last_period + 1]
        return cut.rstrip() + "."

    def _from_rules(self, paper: Paper, max_chars: int = 1500) -> str:
        """
        完整去填充摘要（目标 200-300 字）。
        - 无摘要 → ""；
        - 摘要 ≤ 上限 → 直接全文（已是 200-300 字量级的完整摘要）；
        - 摘要 > 上限 → 按信息量给句子打分，剔除低分填充句（保留首句=问题与末句=结论），
          维持原序，确保覆盖问题/方法/数据集/结果/贡献，不出现 mid-sentence `...`。
        """
        abstract = (paper.abstract or "").replace("\n", " ").strip()
        if not abstract:
            return ""
        if len(abstract) <= max_chars:
            return abstract

        sentences = PaperAnalyzer._split_sentences(abstract)
        if not sentences:
            return self._trim(abstract, max_chars)

        # 句子信息量打分（方法/结果 > 数据集/贡献）
        scored = [(i, s, self._sentence_score(s))
                  for i, s in enumerate(sentences)]
        keep = set(range(len(sentences)))
        total = sum(len(s) + 2 for s in sentences)

        # 从低分到高分剔除，直到总长 ≤ 上限；保留首句（问题）与末句（结论）
        for i, s, _ in sorted(scored, key=lambda x: x[2]):
            if total <= max_chars:
                break
            if i == 0 or i == len(sentences) - 1:
                continue
            keep.discard(i)
            total -= len(s) + 2

        condensed = ". ".join(sentences[i] for i in sorted(keep))
        if not condensed.endswith("."):
            condensed += "."
        return self._trim(condensed, max_chars)

    @staticmethod
    def _sentence_score(s: str) -> int:
        """句子信息量评分：方法/结果句 +3，数据集/贡献句 +2。"""
        low = s.lower()
        score = 0
        if any(m in low for m in PaperAnalyzer.METHOD_MARKERS):
            score += 3
        if any(m in low for m in PaperAnalyzer.CONCLUSION_MARKERS):
            score += 3
        if any(m in low for m in AbstractSummarizer.DATASET_MARKERS):
            score += 2
        if any(m in low for m in AbstractSummarizer.CONTRIBUTION_MARKERS):
            score += 2
        return score


class StructuredExtractor:
    """
    从论文摘要（首选语段）中摘录四要素（报告格式设计.md 单篇块新结构）：
      1. 解决的问题 / Problem
      2. 现有方案（引用先前工作）/ Existing approaches
      3. 新方案 / New approach
      4. 效果及局限性 / Results & limitations

    规则版抽取式：按句切分摘要，用信号词匹配各要素的语段做摘录。
    每个要素取首个匹配句（效果及局限可取「结果句 + 局限句」），互不重复；
    找不到则留空（报告走占位），不编造。中英文摘要均支持。
    """

    # 「解决的问题」信号词（问题/挑战/瓶颈/动机；弱词与局限词不入，避免与「效果及局限」冲突）
    PROBLEM_MARKERS = (
        "challenge", "challenging", "problem", "bottleneck", "difficult",
        "expensive", "computationally expensive", "suffer", "suffers",
        "lack", "lacks", "remains challenging",
        "motivated by", "to address", "to tackle",
        "obstacle", "barrier", "drawback", "inefficient", "slow", "issue",
        "问题", "挑战", "瓶颈", "难以", "困难", "成本高", "低效",
        "缺陷", "受限", "亟需",
    )
    # 「现有方案」= 已经存在的理论/方法/思路（既有范式、先前工作、被广泛采用的做法）
    EXISTING_MARKERS = (
        "prior", "previous", "existing", "conventional", "traditional",
        "state-of-the-art", "recent work", "recent method", "recent methods",
        "have been proposed", "have proposed", "has been proposed",
        "has been shown", "has been studied", "have been studied",
        "has been used", "have been used", "widely used", "widely adopted",
        "current method", "current approach", "current methods",
        "rely on", "relies on",
        "prior work", "prior methods", "prior solvers", "prior approaches",
        "已有", "现有", "先前", "传统", "目前", "以往", "前人", "经典",
        "广泛使用", "广泛采用",
    )
    # 「新方案」= 本文提出的创新内容（不限于「方法」——含新理论/发现/洞见/框架/模型/贡献）
    # 强信号：明确的贡献动词 / 新颖性 / 被动提出（"X is proposed"）
    NEW_STRONG = (
        "we propose", "we introduce", "we present", "we develop", "we design",
        "we build", "we formulate", "we construct", "we provide", "we describe",
        "we show", "we show that", "we find", "we found", "we prove",
        "we argue", "we establish", "we observe", "we discover", "we reveal",
        "we identify", "we derive", "we hypothesize",
        "propose", "is proposed", "are proposed",  # 含 "we propose"/被动 "X is proposed"
        "novel", "first to", "new method", "new approach", "new framework",
        "new model", "new idea", "new theory",
        "our contribution", "our insight", "our finding", "our findings",
        "our idea", "our proposed", "our key",
        "我们提出", "本文提出", "提出", "引入", "设计", "构建",
        "发现", "证明", "揭示", "贡献", "创新", "新颖", "首次",
    )
    # 弱信号：单独出现时常为背景（"this work plays a role"），仅在无强信号时回退
    NEW_WEAK = (
        "this paper", "in this paper", "this work", "in this work", "this study",
        "our method", "our approach", "our framework", "our model",
        "our work", "our theory", "本文", "我们",
    )
    NEW_APPROACH_MARKERS = NEW_STRONG + NEW_WEAK  # 供 _pick_background 跳过用
    # 「效果」信号词（动词态，避免 "evaluation" 名词误命中 "neural network evaluations"）
    RESULT_MARKERS = (
        "outperform", "achieve", "achieves", "demonstrate", "demonstrates",
        "improve", "improvement", "results", "accuracy", "benchmark",
        "experiment", "experiments", "evaluate", "show that", "shows",
        "significant", "superior", "competitive", "yield", "yields",
        "state-of-the-art", "f1", "bleu", "gain", "gains",
    )
    # 「局限性」信号词（与结果句一起构成「效果及局限性」；弱词 however/but/only/still 不入）
    LIMITATION_MARKERS = (
        "limitation", "limited", "fails", "fail to", "struggle", "struggles",
        "cannot", "can not", "does not", "do not", "future work",
        "drawback", "weakness", "remains challenging", "remains an open",
        "yet to", "but limited", "still limited",
        "局限", "不足", "未能", "无法", "不能", "未来工作", "待解决", "仍是",
    )

    def extract(self, paper: Paper) -> Dict[str, str]:
        """抽取四要素语段；无匹配则对应字段为空。"""
        abstract = (paper.abstract or "").replace("\n", " ").strip()
        empty = {"problem": "", "existing_approaches": "",
                 "new_approach": "", "results_limitations": ""}
        if not abstract:
            return empty
        sentences = PaperAnalyzer._split_sentences(abstract)
        if not sentences:
            return empty

        used: Set[str] = set()
        # 优先级：新方案（本文创新）→ 已有方案（既有理论/方法）→ 解决的问题 → 效果及局限
        # 新方案/已有方案均用打分择优，避免弱信号与结果对比句误判。
        new_approach = self._pick_new(sentences, used)
        existing = self._pick_existing(sentences, used)
        if not existing:
            existing = self._pick_background(sentences, used)
        problem = self._pick(sentences, self.PROBLEM_MARKERS, used)
        results = self._pick_results(sentences, used)

        return {
            "problem": self._norm(problem),
            "existing_approaches": self._norm(existing),
            "new_approach": self._norm(new_approach),
            "results_limitations": self._norm(results),
        }

    def _pick_new(self, sentences: List[str], used: Set[str]) -> str:
        """
        打分择优「新方案」句：强信号(贡献动词/新颖性)+2，弱信号(this work/our model)+1；
        含既有工作标记 -2（"methods have been proposed" 不应算本文创新）。
        取最高分且 >0 的句子；避免弱信号背景句抢走真正的贡献句。
        """
        best, best_score = "", 0
        for s in sentences:
            if s in used:
                continue
            low = s.lower()
            score = 0
            if any(m in low for m in self.NEW_STRONG):
                score += 2
            if any(m in low for m in self.NEW_WEAK):
                score += 1
            if any(m in low for m in self.EXISTING_MARKERS):
                score -= 2  # 描述既有工作的句子降权
            if score > best_score:
                best, best_score = s, score
        if best and best_score > 0:
            used.add(best)
            return best
        return ""

    def _pick_existing(self, sentences: List[str], used: Set[str]) -> str:
        """
        打分择优「已有方案」句：须含既有标记 +1；但结果/对比句降权
        （"compared to existing X, our model is faster" 是结果，不是既有方案描述）。
        """
        best, best_score = "", 0
        for s in sentences:
            if s in used:
                continue
            low = s.lower()
            if not any(m in low for m in self.EXISTING_MARKERS):
                continue  # 必须含既有标记
            score = 1
            if any(m in low for m in self.RESULT_MARKERS):
                score -= 1
            if any(m in low for m in ("compared to", "than existing", "outperform",
                                      "over existing", "versus", "vs ")):
                score -= 1
            if any(m in low for m in self.NEW_STRONG):
                score -= 1  # 含本文创新词（多为本文结果对比）
            if score > best_score:
                best, best_score = s, score
        if best and best_score > 0:
            used.add(best)
            return best
        return ""

    def _pick_background(self, sentences: List[str], used: Set[str]) -> str:
        """
        「已有方案」回退：取首句「中性背景」句——既非本文创新(new)、也非问题(problem)、
        也非结果/局限(result/limitation)。这类句子通常在陈述既有的理论/方法/思路。
        """
        skip = (self.NEW_APPROACH_MARKERS + self.PROBLEM_MARKERS
                + self.RESULT_MARKERS + self.LIMITATION_MARKERS)
        for s in sentences:
            if s in used:
                continue
            low = s.lower()
            if any(m in low for m in skip):
                continue
            used.add(s)
            return s
        return ""

    @staticmethod
    def _pick(sentences: List[str], markers, used: Set[str]) -> str:
        """取首个含任一 marker 的句子（排除已用句）。"""
        for s in sentences:
            if s in used:
                continue
            low = s.lower()
            if any(m in low for m in markers):
                used.add(s)
                return s
        return ""

    @staticmethod
    def _pick_results(sentences: List[str], used: Set[str]) -> str:
        """效果及局限：取 1 句结果 + 1 句局限（若有），拼接。"""
        result = ""
        limitation = ""
        for s in sentences:
            if s in used:
                continue
            low = s.lower()
            if not result and any(m in low for m in StructuredExtractor.RESULT_MARKERS):
                result = s
                used.add(s)
            elif not limitation and any(m in low for m in StructuredExtractor.LIMITATION_MARKERS):
                limitation = s
                used.add(s)
            if result and limitation:
                break
        parts = [p for p in (result, limitation) if p]
        return ". ".join(parts)

    @staticmethod
    def _norm(s: str) -> str:
        """规范语段：去首尾空白，补句末标点。"""
        s = (s or "").strip()
        if s and not s.endswith((".", "。", "?", "!", ";", ":")):
            s += "."
        return s


class PaperAnalyzer:
    """论文信息提取与深度分析器"""

    # 创新点信号词（英文模式 → 中/英标签，支持按报告语言渲染）
    INNOVATION_PATTERNS = [
        ("novel", "提出新颖方法", "proposes a novel method"),
        ("state-of-the-art", "达到最先进水平", "state-of-the-art"),
        ("outperform", "性能优于已有方法", "outperforms prior work"),
        ("first", "首次尝试该问题", "first to address this problem"),
        ("propose", "提出新方法/框架", "proposes a new method/framework"),
        ("introduce", "引入新思路", "introduces a new idea"),
        ("new approach", "提出新方法", "new approach"),
        ("breakthrough", "取得突破性进展", "breakthrough"),
    ]

    # 研究方法信号词（用于抽取「核心研究内容」子句）
    METHOD_MARKERS = ("we propose", "we introduce", "we present", "we develop",
                      "we design", "we build", "we study", "we investigate",
                      "we explore", "we formulate", "this paper", "in this paper",
                      "we propose a")

    # 结论/结果信号词（用于抽取「核心结论」子句）
    CONCLUSION_MARKERS = ("demonstrate", "achieve", "outperform", "improve",
                          "enables", "yield", "confirm", "reveal", "show",
                          "results", "find")

    # 应用领域关键词
    APPLICATION_KEYWORDS = {
        "医疗健康": ["medical", "health", "diagnosis", "clinical", "patient"],
        "金融": ["financial", "trading", "stock", "portfolio"],
        "自动驾驶": ["autonomous", "driving", "vehicle", "robot"],
        "自然语言处理": ["nlp", "text", "language", "translation"],
        "计算机视觉": ["vision", "image", "recognition", "segmentation"],
        "推荐系统": ["recommendation", "ranking", "personalization"],
        "科学发现": ["discovery", "molecule", "protein", "material", "physics"],
    }

    def __init__(self, citation_finder: Optional[CitationFinder] = None):
        """初始化分析器；可注入 CitationFinder 便于测试"""
        config = get_config_manager()
        api_keys = config.get_api_keys()
        self.citation_finder = citation_finder or CitationFinder(
            api_key=api_keys.get("semantic_scholar", ""),
        )

    # ----------------------------- 公共入口 ---------------------------- #

    def analyze_papers(self, papers: List[Paper],
                       lang: str = "bilingual") -> List[Paper]:
        """批量提取每篇论文的结构化信息（原地填充并返回）。

        Args:
            papers: 论文列表
            lang:   报告语言 zh/en/bilingual（影响创新点等标签语种）
        """
        logger.info("开始分析 %d 篇论文（lang=%s）", len(papers), lang)
        analyzed: List[Paper] = []
        for paper in papers:
            try:
                analyzed.append(self._analyze_single_paper(paper, lang))
            except Exception as e:
                logger.error("分析论文失败 %s: %s", paper.title, e)
                analyzed.append(paper)
        logger.info("分析完成")
        return analyzed

    def format_citations(self, papers: List[Paper]) -> List[str]:
        """批量生成 APA 7th 引用"""
        return [format_apa_citation(p) for p in papers]

    def generate_overall_analysis(self, topic: str,
                                  papers: List[Paper]) -> str:
        """
        方向级整体分析（报告格式设计.md §5.3，Option B 从 report_generator 迁入）。

        综合：共同主题、方法演进（按年份）、代表性贡献、发展阶段。
        规则版（非 LLM），所有结论落在真实论文上。
        """
        if not papers:
            return f"「{topic}」方向暂无论文可供分析。"

        # 共同关键词（频次 top）
        from collections import Counter
        kw = Counter()
        for p in papers:
            kw.update(p.keywords)
        common = [k for k, _ in kw.most_common(3)]

        # 方法演进：按年份排序，看时间跨度
        by_year = sorted(papers, key=lambda p: p.year or 9999)
        years = [p.year for p in by_year if p.year]
        span = (max(years) - min(years)) if years else 0

        # 代表性贡献：最高被引
        rep = max(papers, key=lambda p: p.citation_count)

        # 发展阶段
        if span >= 4:
            stage = "已进入相对成熟、持续演进阶段"
        elif span >= 2:
            stage = "处于快速活跃发展期"
        else:
            stage = "属新兴/近期热点方向"

        parts = [f"本热点 {len(papers)} 篇论文围绕「{topic}」展开"]
        if common:
            parts.append(f"，共同关注 {('、'.join(common))} 等主题")
        parts.append(
            f"；代表性工作《{rep.title[:40]}》（{rep.year}，引用 "
            f"{rep.citation_count}）贡献突出"
        )
        if span > 0:
            parts.append(
                f"，方法从 {min(years)} 年到 {max(years)} 年逐步演进"
            )
        parts.append(f"，整体{stage}。")
        return "".join(parts)

    def find_foundational_papers(self, papers: List[Paper],
                                 top_n: int = 3) -> List[str]:
        """
        方向级奠基性参考论文查找（报告格式设计.md §5.4，Option B 迁入并实装）。

        通过 Semantic Scholar references API 找出被本热点论文广泛引用的
        高被引经典工作；离线/限流/失败时回退到基于本热点的诚实启发式。
        """
        if not papers:
            return []

        try:
            raw = self.citation_finder.collect_raw_references(papers)
            if raw:
                hotspot_titles = {
                    self.citation_finder._norm_title(p.title)
                    for p in papers
                }
                ranked = self.citation_finder.rank_references(
                    raw, hotspot_titles, top_n
                )
                if ranked:
                    return ranked
        except Exception as e:
            logger.warning("奠基论文 API 查找失败，回退到启发式: %s", e)

        return self._foundational_fallback(papers, top_n)

    # ----------------------------- 单篇提取 ---------------------------- #

    def _analyze_single_paper(self, paper: Paper,
                              lang: str = "bilingual") -> Paper:
        """提取单篇论文的研究内容/创新点/结论/应用/浓缩摘要/四要素摘录；已有则跳过"""
        if not (paper.research_content and paper.innovations):
            paper.research_content = self._extract_research_content(paper)
            paper.innovations = self._extract_innovations(paper, lang)
            paper.conclusions = self._extract_conclusions(paper)
            paper.value_application = self._infer_application(paper)
            paper.condensed_abstract = AbstractSummarizer().summarize(paper)
        # 四要素（单篇块新结构）：LLM 生成式 → 规则回退；始终填充，除非已存在
        # language 透传：zh/en/bilingual 驱动 LLM 输出语种（修复点：旧版无视 lang，恒中文）
        if not paper.problem and not paper.new_approach:
            from llm_analyzer import FourElementAnalyzer  # 延迟导入，避免循环依赖
            fea = FourElementAnalyzer().analyze(paper, language=lang)
            paper.problem = fea["problem"]
            paper.existing_approaches = fea["existing_approaches"]
            paper.new_approach = fea["new_approach"]
            paper.results_limitations = fea["results_limitations"]
            paper.title_zh = fea.get("title_zh", "")
            paper.analysis_source = fea.get("analysis_source", "")
        return paper

    # ---- 句子/子句切分（让 research_content 与 conclusions 取不同片段） ---- #

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """按句号切句，保护常见缩写与小数点中的句点"""
        text = re.sub(r"\s+", " ", text or "").strip()
        if not text:
            return []
        S = "\x1f"  # unit separator 作占位，避免与正文冲突
        protected = text
        # 保护小数点（数字.数字，如 95.6），用 lambda 避免反向引用转义
        protected = re.sub(r"(\d)\.(\d)",
                           lambda m: m.group(1) + S + m.group(2), protected)
        # 保护常见缩写中的句点
        for abbr in ("i.e", "e.g", "et al", "vs", "cf", "Fig", "Eq",
                     "Dr", "Mr", "Mrs", "No", "St", "Inc", "Ltd"):
            protected = protected.replace(abbr + ".", abbr + S)
        parts = [p.strip() for p in protected.split(".") if p.strip()]
        return [p.replace(S, ".") for p in parts]

    def _split_clauses(self, text: str) -> List[str]:
        """先按句、再按逗号/分号拆子句，清洗前导连接词"""
        clauses: List[str] = []
        for sent in self._split_sentences(text):
            for part in re.split(r"[;,]", sent):
                part = part.strip()
                part = re.sub(r"^(and|or|that|which|where|while)\s+", "",
                              part, flags=re.IGNORECASE).strip()
                if part:
                    clauses.append(part)
        return clauses

    # ---- 单篇字段提取（research_content / conclusions 取不同子句，避免与 Abstract 重复） ---- #

    def _extract_research_content(self, paper: Paper) -> str:
        """
        核心研究内容 = 含方法信号词的子句（we propose/introduce/present…）；
        找不到则取首句。与 Abstract 的区别：这里是「做了什么方法」的精炼片段，
        而非整段摘要的复制。
        """
        abstract = (paper.abstract or "").strip()
        if not abstract:
            return ""
        clauses = self._split_clauses(abstract)
        for c in clauses:
            if any(m in c.lower() for m in self.METHOD_MARKERS):
                return c
        return clauses[0] if clauses else abstract[:150]

    def _extract_innovations(self, paper: Paper,
                             lang: str = "bilingual") -> str:
        """
        创新点（报告格式设计.md §10.2）。
        - 信号词命中 → 双语标签；
        - 无信号词 → 基于方法子句派生（落在论文真实方法上，不给空泛默认）；
        - 无摘要 → 留空（不渲染）。
        """
        text = (paper.abstract or "").lower()
        hits = [(zh, en) for pat, zh, en in self.INNOVATION_PATTERNS
                if pat in text]
        if hits:
            zh = "；".join(z for z, _ in hits)
            en = "; ".join(e for _, e in hits)
        else:
            method = self._extract_research_content(paper)
            if not method:
                return ""  # 无摘要，留空（报告不渲染）
            zh = f"提出：{method}"
            en = f"proposes: {method}"
        if lang == "en":
            return en
        if lang == "zh":
            return zh
        return f"{zh} / {en}"

    def _extract_conclusions(self, paper: Paper) -> str:
        """
        核心结论 = 含结果信号词的子句（demonstrate/outperform/achieve…）；
        优先选取与 research_content 不同的子句，找不到则取末句。
        """
        abstract = (paper.abstract or "").strip()
        if not abstract:
            return ""
        clauses = self._split_clauses(abstract)
        research = self._extract_research_content(paper)
        for c in clauses:
            if c == research:
                continue
            if any(m in c.lower() for m in self.CONCLUSION_MARKERS):
                return c
        # 兜底：最后一个子句通常是结论
        if clauses:
            return clauses[-1] if clauses[-1] != research else (
                clauses[-2] if len(clauses) > 1 else "")
        return ""

    def _condense_abstract(self, paper: Paper,
                           max_chars: int = 1500) -> str:
        """
        完整去填充摘要（向后兼容入口；实际逻辑见 AbstractSummarizer._from_rules）。
        目标 200-300 字，覆盖问题/方法/数据集/指标/结果/贡献；仅超长才剔除低信息句。
        """
        return AbstractSummarizer()._from_rules(paper, max_chars=max_chars)

    def _infer_application(self, paper: Paper) -> str:
        """研究价值与应用场景（基于领域关键词推断）"""
        content = f"{paper.title} {paper.abstract}".lower()
        apps = [domain for domain, kws in self.APPLICATION_KEYWORDS.items()
                if any(k in content for k in kws)]
        return "、".join(apps) if apps else "通用研究"

    # ----------------------------- 降级回退 ---------------------------- #

    @staticmethod
    def _foundational_fallback(papers: List[Paper], top_n: int) -> List[str]:
        """
        离线/限流/API 失败时的诚实回退：基于本热点最早且较高被引的论文给出线索，
        明确标注「离线回退」，绝不编造引用。
        """
        with_year = [p for p in papers if p.year]
        earliest = (
            min(with_year, key=lambda p: (p.year, -p.citation_count))
            if with_year else
            max(papers, key=lambda p: p.citation_count)
        )
        return [
            f"（离线回退）本方向可追溯的较早代表作为《{earliest.title}》"
            f"（{earliest.year}，引用 {earliest.citation_count}）；"
            f"完整奠基性工作需联网经 Semantic Scholar 引用 API 补全。"
        ]


# ---------------------------------------------------------------------- #
# 命令行入口
# ---------------------------------------------------------------------- #

def main() -> None:
    """简单自检：分析样例论文 + 演示整体分析与奠基论文查找"""
    from utils import SearchIntent  # noqa: F401  （保持与其它模块一致）

    sample = [
        Paper(title="DDIM-Solver: Fast Sampling for Diffusion Models",
              authors=["Zhang", "Wang"], venue="NeurIPS", year=2024, doi="",
              abstract="We propose a novel ODE solver for diffusion model "
                       "sampling acceleration. Our method outperforms "
                       "previous solvers and achieves 10-step sampling.",
              keywords=["diffusion", "sampling"], citation_count=187,
              venue_type="conference", ranking="顶会", source="arxiv"),
        Paper(title="Consistency-Model: One-Step Generation",
              authors=["Lee"], venue="ICML", year=2023, doi="",
              abstract="We introduce a consistency model that achieves "
                       "one-step high-quality generation, demonstrating "
                       "strong results.",
              keywords=["diffusion", "generative"], citation_count=250,
              venue_type="conference", ranking="顶会", source="openalex"),
    ]

    analyzer = PaperAnalyzer()
    analyzed = analyzer.analyze_papers(sample)

    for p in analyzed:
        print(f"《{p.title}》")
        print(f"  创新: {p.innovations}")
        print(f"  结论: {p.conclusions}")
        print(f"  应用: {p.value_application}")
        print(f"  APA:  {format_apa_citation(p)}")

    print("\n[整体分析]")
    print(analyzer.generate_overall_analysis("扩散模型采样", analyzed))

    print("\n[奠基性参考论文]")
    for ref in analyzer.find_foundational_papers(analyzed, top_n=3):
        print(" -", ref)


if __name__ == "__main__":
    main()
