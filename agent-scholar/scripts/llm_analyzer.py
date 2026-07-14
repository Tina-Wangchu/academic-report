"""
四要素 LLM 分析（Module 9，Phase 1）

把单篇论文的四要素（解决的问题 / 已有方案 / 新方案 / 效果及局限）从**规则抽取式**
升级为 **LLM 生成式综合**，达到参考报告 ai_report_20260705.pdf 的专业深度。

分层调度（four_element_llm_plan.md）：
  Tier 1: LLM 生成式（默认走智谱 GLM 的 Anthropic 兼容端点；可用且成功）→ 主路径
  Tier 2: StructuredExtractor 规则抽取（离线 / 失败 / 未配置）→ 回退，绝不崩溃、绝不编造

设计要点：
- 智谱 GLM 走 `ANTHROPIC_BASE_URL`(https://open.bigmodel.cn/api/anthropic) 的 Messages API，
  复用 `ANTHROPIC_AUTH_TOKEN`（即本环境已有的 GLM 凭证），零额外 key、零新依赖（用 requests）。
- temperature=0 + 按 DOI/title 缓存（~/.hermes/llm_cache_four_element.json），稳定可复现、控成本。
- 不改报告 schema（仍填 paper.problem/existing_approaches/new_approach/results_limitations）。
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from utils import Paper, safe_filename
from config_manager import get_config_manager

logger = logging.getLogger(__name__)

# Windows 控制台默认 GBK，强制 stdout 用 utf-8，避免中文/emoji 打印崩溃
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 四要素来源标记
SOURCE_LLM = "llm"
SOURCE_RULE = "rule"
SOURCE_CACHE = "cache"
SOURCE_UNAVAILABLE = "unavailable"   # 闭源/无开放摘要与全文，无法自动分析


# ---------------------------------------------------------------------- #
# Prompt
# ---------------------------------------------------------------------- #

SYSTEM_PROMPT = """你是学术综述分析师。基于给定论文标题与摘要，用学术、客观、凝练的中文生成四要素分析，用于专业行业报告。

严格遵循：
1) problem（解决的问题）：一段，点出论文针对的核心挑战/痛点与本质难点（综合改写，不要照搬原句）。
2) existing（已有方案）：对比 1-3 类既有方法/思路，各点出其具体不足或失败模式。
3) new（新方案）：本文的创新内容；若为多组件方法，用「1. … 2. … 3. …」编号拆解架构。
4) results（效果及局限）：先给量化结果（指标/百分比/数据集/部署证据，若有），再用「约束：…」给出具名局限（如依赖 X、在 Y 场景未验证）。

硬约束：
- 仅基于给定文本，不得编造未提及的数据、方法或结论；某要素文本未涉及则写「（未明确提及）」。
- 保留原文关键英文术语；每要素 2-5 句，总量 ≤ 350 字。
- 输出严格 JSON（且只输出 JSON）：{"problem":"…","existing":"…","new":"…","results":"…"}，四个键均为字符串。"""


# ---------------------------------------------------------------------- #
# Provider：智谱 GLM（Anthropic 兼容端点）
# ---------------------------------------------------------------------- #

class ZhipuProvider:
    """
    智谱 GLM 的 Anthropic Messages 兼容调用（用 requests，不引入 SDK 依赖）。
    默认 base_url=https://open.bigmodel.cn/api/anthropic ，POST {base_url}/v1/messages。

    健壮性：
    - 429（公平使用限流）/ 5xx / 网络超时 → 指数退避重试（max_retries 次）。
    - min_interval：两次调用间最小间隔，避免短时间突触发限流（Coding Plan 有频率限制）。
    - 4xx（非 429，如 401/400）→ 立即抛出，不重试。
    """

    # 退避等待（秒），按重试次数递增：3, 8, 15, 25
    _BACKOFF = (3, 8, 15, 25)

    def __init__(self, api_key: str, base_url: str, model: str,
                 timeout: float = 45.0, max_tokens: int = 1024,
                 max_retries: int = 4, min_interval: float = 1.5):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.min_interval = min_interval
        self._last_call_ts = 0.0

    def _throttle(self):
        """限速：确保两次调用间隔 ≥ min_interval。"""
        import time
        gap = time.monotonic() - self._last_call_ts
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self._last_call_ts = time.monotonic()

    @staticmethod
    def _extract_text(data: dict) -> str:
        """从 Anthropic Messages 响应抽文本（容错多种形态）。"""
        content = data.get("content")
        if isinstance(content, list) and content:
            for blk in content:
                if isinstance(blk, dict) and blk.get("type") == "text":
                    return blk.get("text", "")
            return content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
        if isinstance(content, str):
            return content
        if "completion" in data:           # 旧版 completions 形态
            return data["completion"]
        raise RuntimeError(f"LLM 响应无可读文本: {str(data)[:200]}")

    def summarize(self, system_prompt: str, user_text: str) -> str:
        import time
        url = f"{self.base_url}/v1/messages"
        # 同时带 x-api-key 与 Authorization: Bearer，兼容两种鉴权约定
        headers = {
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": 0,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_text}],
        }

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                resp = requests.post(url, headers=headers, json=body, timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError) as e:
                last_err = e
                wait = self._BACKOFF[min(attempt, len(self._BACKOFF) - 1)]
                logger.warning("LLM 网络/%s，%ds 后重试 (attempt %d/%d)",
                               type(e).__name__, wait, attempt + 1, self.max_retries)
                time.sleep(wait)
                continue

            # 可重试：429（限流）与 5xx
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                last_err = RuntimeError(f"LLM HTTP {resp.status_code}: {resp.text[:160]}")
                wait = self._BACKOFF[min(attempt, len(self._BACKOFF) - 1)]
                logger.warning("LLM %d 限流/服务错，%ds 后重试 (attempt %d/%d)",
                               resp.status_code, wait, attempt + 1, self.max_retries)
                time.sleep(wait)
                continue

            # 其它 4xx：不重试，立即抛出（如 401 鉴权、400 请求格式）
            if resp.status_code >= 400:
                raise RuntimeError(f"LLM HTTP {resp.status_code}: {resp.text[:300]}")

            return self._extract_text(resp.json())

        # 重试耗尽：抛出最后一个错误（上层 FourElementAnalyzer 会回退规则）
        raise last_err or RuntimeError("LLM 调用重试耗尽")


def _build_provider_from_config() -> Optional[ZhipuProvider]:
    """按 config 构建 ZhipuProvider；未启用/无 key → None。"""
    cfg = get_config_manager().get_llm_config()
    if not (cfg.get("enabled") and cfg.get("api_key")):
        return None
    return ZhipuProvider(
        api_key=cfg["api_key"], base_url=cfg["base_url"],
        model=cfg.get("model") or "glm-5-turbo")


# ---------------------------------------------------------------------- #
# Phase 2：全文增强（arXiv PDF → 文本 → 关键片段）
# ---------------------------------------------------------------------- #

def _to_arxiv_pdf_url(url: str) -> Optional[str]:
    """arXiv abs/entry URL → PDF URL；非 arXiv → None。"""
    if not url:
        return None
    if "arxiv.org/pdf/" in url:
        return url
    m = re.search(r"arxiv\.org/(?:abs|)/?([\d]{4}\.[\d]{4,5}(?:v\d+)?)", url)
    if m:
        return f"https://arxiv.org/pdf/{m.group(1)}"
    return None


def _pdf_bytes_to_text(data: bytes) -> str:
    """PDF 字节 → 纯文本（用 PyMuPDF/fitz；未装 → 空串）。"""
    try:
        import fitz  # type: ignore
    except ImportError:
        logger.debug("未安装 PyMuPDF(fitz)，跳过全文抽取")
        return ""
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as e:
        logger.debug("PDF 解析失败: %s", e)
        return ""


def _extract_key_sections(text: str, max_chars: int = 4000) -> str:
    """
    从全文中抽取关键章节片段（方法/实验/结果/局限/结论）喂 LLM。
    找不到章节标题时，回退到正文中间段（跳过开头重复的摘要）。
    """
    if not text:
        return ""
    headings = [
        "method", "methods", "approach", "our approach", "our method",
        "model", "framework", "architecture",
        "experiment", "experiments", "evaluation", "results",
        "limitation", "limitations", "conclusion", "conclusions",
        "方法", "实验", "评估", "结果", "局限", "结论",
    ]
    lower = text.lower()
    found = []
    for hd in headings:
        idx = lower.find("\n" + hd)           # 行首匹配更稳
        if idx < 0:
            idx = lower.find(hd)
        if idx >= 0:
            found.append((idx, text[idx: idx + 700]))
    if found:
        found.sort()
        joined = "\n…\n".join(s for _, s in found)
        return joined[:max_chars]
    # 兜底：跳过开头 ~1000 字符（常是重复摘要+引言），取正文段
    return text[1000: 1000 + max_chars]


def _unpaywall_pdf_url(doi: str) -> str:
    """按 DOI 查 Unpaywall 的开放 PDF URL；无 → ''。"""
    if not doi:
        return ""
    try:
        r = requests.get(f"https://api.unpaywall.org/v2/{doi}",
                         params={"email": "agent-scholar@example.com"},
                         timeout=10).json()
        loc = r.get("best_oa_location") or {}
        return loc.get("url_for_pdf") or ""
    except Exception:
        return ""


def _html_to_text(html: str) -> str:
    """简易 HTML → 纯文本（去 script/style/标签/实体）。"""
    import html as _htmlmod
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = _htmlmod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def access_url(paper: Paper) -> str:
    """给用户的检索链接：有 DOI 用 doi.org，否则 Google Scholar 按标题搜。"""
    if getattr(paper, "doi", ""):
        return f"https://doi.org/{paper.doi}"
    import urllib.parse
    title = (getattr(paper, "title", "") or "").strip()
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote(title)


def _fetch_url_text(url: str, timeout: float = 15.0) -> str:
    """抓单个 URL 的文本：PDF→fitz；HTML/文本→去标签。失败 → ''。"""
    try:
        resp = requests.get(url, timeout=timeout,
                            headers={"User-Agent": "agent-scholar/1.0"})
        if resp.status_code != 200:
            return ""
        ctype = resp.headers.get("content-type", "").lower()
        is_pdf = ("pdf" in ctype or url.lower().endswith(".pdf")
                  or resp.content[:4] == b"%PDF")
        if is_pdf:
            return _pdf_bytes_to_text(resp.content)
        return _html_to_text(resp.text)
    except Exception as e:
        logger.debug("URL 抓取失败 %s: %s", url, e)
        return ""


def _fulltext_url_candidates(paper: Paper) -> list:
    """开放全文 URL 候选（按优先级）：paper.pdf_url → arXiv → Unpaywall(DOI)。"""
    cands: list = []
    pdf = getattr(paper, "pdf_url", "") or ""
    if pdf:
        cands.append(pdf)
    arxiv = _to_arxiv_pdf_url(getattr(paper, "url", "") or "")
    if arxiv and arxiv not in cands:
        cands.append(arxiv)
    up = _unpaywall_pdf_url(getattr(paper, "doi", "") or "")
    if up and up not in cands:
        cands.append(up)
    return cands


def _fetch_fulltext(paper: Paper, max_chars: int = 4000,
                    timeout: float = 15.0) -> str:
    """
    抓开放全文（PDF/HTML）并抽关键片段；多源级联：
    paper.pdf_url → arXiv → Unpaywall(DOI)。任一成功即返回；全失败 → ''。
    无摘要时尤其依赖此函数做全文分析。
    """
    for url in _fulltext_url_candidates(paper):
        text = _fetch_url_text(url, timeout)
        if text:
            sec = _extract_key_sections(text, max_chars)
            if sec:
                logger.debug("全文命中: %s", url)
                return sec
    return ""


# ---------------------------------------------------------------------- #
# 缓存
# ---------------------------------------------------------------------- #

def _default_cache_path() -> Path:
    return Path.home() / ".hermes" / "llm_cache_four_element.json"


# ---------------------------------------------------------------------- #
# 四要素分析器（分层调度）
# ---------------------------------------------------------------------- #

# JSON 键别名 → 标准字段
_KEY_ALIASES = {
    "problem": "problem", "解决的问题": "problem",
    "existing": "existing_approaches", "existing_approaches": "existing_approaches",
    "prior": "existing_approaches", "已有方案": "existing_approaches", "现有方案": "existing_approaches",
    "new": "new_approach", "new_approach": "new_approach", "method": "new_approach",
    "新方案": "new_approach", "本文新方案": "new_approach",
    "results": "results_limitations", "results_limitations": "results_limitations",
    "效果": "results_limitations", "效果及局限": "results_limitations", "效果及局限性": "results_limitations",
}
_FIELD_KEYS = ("problem", "existing_approaches", "new_approach", "results_limitations")


class FourElementAnalyzer:
    """
    四要素分层分析：LLM 生成式（主）→ StructuredExtractor 规则（回退）→ 缓存。

    use_fulltext=True（Phase 2）：对有 arXiv 链接的论文抓取 PDF 全文关键片段喂 LLM，
    方法/约束细节更全；抓取失败/非 arXiv → 仅摘要（行为同 Phase 1）。
    """

    def __init__(self, provider: Optional[ZhipuProvider] = ...,
                 cache_path: Optional[Path] = None,
                 use_cache: bool = True,
                 use_fulltext: bool = True,
                 fulltext_max_chars: int = 4000,
                 fulltext_timeout: float = 15.0):
        # provider 默认从 config 构建；显式传 None 表示强制走规则
        self.provider = _build_provider_from_config() if provider is ... else provider
        self.cache_path = Path(cache_path) if cache_path else _default_cache_path()
        self.use_cache = use_cache
        self.use_fulltext = use_fulltext
        self.fulltext_max_chars = fulltext_max_chars
        self.fulltext_timeout = fulltext_timeout

    # ----------------------------- 公共入口 ---------------------------- #

    def analyze(self, paper: Paper) -> Dict[str, Any]:
        """
        返回 {problem, existing_approaches, new_approach, results_limitations, analysis_source}。
        分层：缓存 → 闭源检测 → LLM → 规则。
        闭源（无摘要 + 无开放全文）：四要素留空 + analysis_source=unavailable（报告据此标注检索链接），
        不调 LLM、不编造。
        """
        key = self._cache_key(paper)
        if self.use_cache:
            cached = self._cache_get(key)
            if cached is not None:
                cached["analysis_source"] = SOURCE_CACHE
                return cached

        abstract_empty = not (paper.abstract or "").strip()
        # 全文：无摘要强制抓（不放弃）；有摘要按 use_fulltext 开关
        fulltext = ""
        if abstract_empty or self.use_fulltext:
            fulltext = _fetch_fulltext(paper, self.fulltext_max_chars,
                                       self.fulltext_timeout)

        # 闭源/无开放内容：无摘要且抓不到全文 → 标注，不调 LLM
        if abstract_empty and not fulltext:
            return self._unavailable(paper)

        if self.provider is not None:
            try:
                parsed = self._from_llm(paper, fulltext)
                if parsed:
                    parsed["analysis_source"] = SOURCE_LLM
                    if self.use_cache:
                        self._cache_put(key, parsed)
                    return parsed
                logger.info("LLM 输出解析失败，回退规则: %s", paper.title[:40])
            except Exception as e:
                logger.warning("LLM 调用失败，回退规则: %s", e)

        # 规则回退
        out = self._from_rules(paper)
        out["analysis_source"] = SOURCE_RULE
        return out

    # ------------------------------ LLM 路径 --------------------------- #

    def _from_llm(self, paper: Paper, fulltext: str = "") -> Optional[Dict[str, str]]:
        raw = self.provider.summarize(SYSTEM_PROMPT, self._input_text(paper, fulltext))
        parsed = self._parse(raw)
        if not parsed:
            return None
        # 规范化键 + 补齐缺失字段为空串
        return {k: (parsed.get(k, "") or "").strip() for k in _FIELD_KEYS}

    @staticmethod
    def _unavailable(paper: Paper) -> Dict[str, Any]:
        """闭源/无开放摘要与全文：四要素留空 + 标注检索链接（不调 LLM、不编造）。"""
        return {
            **{k: "" for k in _FIELD_KEYS},
            "analysis_source": SOURCE_UNAVAILABLE,
            "access_url": access_url(paper),
        }

    @staticmethod
    def _input_text(paper: Paper, fulltext: str = "") -> str:
        abstract = (paper.abstract or "").replace("\n", " ").strip()
        doi = f"\nDOI: {paper.doi}" if paper.doi else ""
        # 无摘要 → 全文片段是唯一来源
        if not abstract and fulltext:
            return (f"标题：{paper.title}{doi}\n"
                    f"（该论文无可用摘要；以下为全文关键片段，请据此生成四要素）\n"
                    f"全文片段：\n{fulltext}")
        text = f"标题：{paper.title}{doi}\n摘要：{abstract}"
        if fulltext:
            text += (f"\n\n全文关键片段（供深度分析用，勿照搬原句，注意可能与摘要重复）：\n"
                     f"{fulltext}")
        return text

    @staticmethod
    def _parse(raw: str) -> Optional[Dict[str, str]]:
        """容错解析 LLM 输出为四要素 dict（支持 JSON / 带 JSON 块 / 标签段落）。"""
        raw = (raw or "").strip()
        # 去掉 markdown 代码围栏
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.IGNORECASE | re.MULTILINE).strip()
        obj: Optional[Dict[str, Any]] = None
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    obj = json.loads(m.group(0))
                except json.JSONDecodeError:
                    obj = None
        if isinstance(obj, dict):
            out: Dict[str, str] = {}
            for k, v in obj.items():
                std = _KEY_ALIASES.get(str(k).strip().lower()) or _KEY_ALIASES.get(str(k).strip())
                if std and isinstance(v, str):
                    out[std] = v
            if out:
                return out
        # 最后一招：标签段落解析
        return _label_parse(raw)

    # ------------------------------ 规则路径 --------------------------- #

    @staticmethod
    def _from_rules(paper: Paper) -> Dict[str, str]:
        """规则回退（复用 StructuredExtractor）。"""
        from paper_analyzer import StructuredExtractor   # 延迟导入，避免循环依赖
        out = StructuredExtractor().extract(paper)
        return {k: out.get(k, "") for k in _FIELD_KEYS}

    # ------------------------------ 缓存 ------------------------------- #

    @staticmethod
    def _cache_key(paper: Paper) -> str:
        norm = f"{(paper.doi or '').strip().lower()}|{(paper.title or '').strip().lower()}"
        return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]

    def _cache_load(self) -> Dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("LLM 缓存损坏，按空处理: %s", e)
            return {}

    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        data = self._cache_load()
        entry = data.get(key)
        if not isinstance(entry, dict):
            return None
        return {k: entry.get(k, "") for k in _FIELD_KEYS}

    def _cache_put(self, key: str, parsed: Dict[str, str]) -> None:
        data = self._cache_load()
        entry = dict(parsed)
        entry["model"] = getattr(self.provider, "model", "")
        entry["ts"] = datetime.now().isoformat()
        data[key] = entry
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.cache_path)
        except OSError as e:
            logger.warning("写 LLM 缓存失败: %s", e)


# ---------------------------------------------------------------------- #
# 标签兜底解析
# ---------------------------------------------------------------------- #

def _label_parse(raw: str) -> Optional[Dict[str, str]]:
    """当 JSON 解析失败时，按中文/英文标签切段落。"""
    label_map = [
        (r"(?:［|\[)?\s*解决的问题\s*(?:］|\])?\s*[:：]?", "problem"),
        (r"(?:［|\[)?\s*(?:已有方案|现有方案)\s*(?:］|\])?\s*[:：]?", "existing_approaches"),
        (r"(?:［|\[)?\s*(?:本文新方案|新方案)\s*(?:］|\])?\s*[:：]?", "new_approach"),
        (r"(?:［|\[)?\s*(?:效果及局限(?:性)?|效果)\s*(?:］|\])?\s*[:：]?", "results_limitations"),
    ]
    positions = []
    for pat, field in label_map:
        m = re.search(pat, raw)
        if m:
            positions.append((m.start(), m.end(), field))
    if not positions:
        return None
    positions.sort()
    out: Dict[str, str] = {}
    for i, (start, end, field) in enumerate(positions):
        body_end = positions[i + 1][0] if i + 1 < len(positions) else len(raw)
        out[field] = raw[end:body_end].strip()
    return out or None


# ---------------------------------------------------------------------- #
# 命令行入口（自检 / 单篇分析）
# ---------------------------------------------------------------------- #

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="四要素 LLM 分析（智谱 GLM，分层回退）")
    parser.add_argument("--title", help="论文标题")
    parser.add_argument("--abstract", help="论文摘要")
    parser.add_argument("--no-llm", action="store_true", help="强制走规则，不用 LLM")
    parser.add_argument("--refresh", action="store_true", help="忽略缓存重新生成")
    args = parser.parse_args()

    cfg = get_config_manager().get_llm_config()
    print(f"[config] enabled={cfg['enabled']} provider={cfg['provider']} "
          f"model={cfg['model']} base_url={cfg['base_url']} key={'***' if cfg['api_key'] else '(none)'}")

    if not args.title:
        return 0  # 仅打印配置自检

    paper = Paper(title=args.title, authors=["A"], venue="", year=0, doi="",
                  abstract=args.abstract or "", keywords=[], citation_count=0,
                  venue_type="", ranking="", source="cli")
    analyzer = FourElementAnalyzer(provider=None if args.no_llm else ...,
                                   use_cache=not args.refresh)
    result = analyzer.analyze(paper)
    print(f"\n来源: {result.get('analysis_source')}")
    for k in _FIELD_KEYS:
        print(f"\n[{k}]\n{result.get(k, '')}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
