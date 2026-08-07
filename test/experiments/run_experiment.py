"""
参数化单场景运行器：搜索 → 筛选 → 聚类 → 报告，落盘全部中间产物与指标。

用法:
    python run_experiment.py E1            # 跑指定场景
    python run_experiment.py E1 E3 E11     # 跑多个
    python run_experiment.py --all         # 跑全部
"""

import json
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# 让脚本能 import scripts 模块
SCRIPTS = Path(__file__).resolve().parents[2] / "academic-report" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from utils import SearchIntent  # noqa: E402
from paper_search import (  # noqa: E402
    ArxivSearcher, SemanticScholarSearcher, OpenAlexSearcher, PaperSearcher,
)
from paper_filter import PaperFilter  # noqa: E402
from paper_analyzer import PaperAnalyzer, CitationFinder  # noqa: E402
from report_generator import ReportGenerator  # noqa: E402
from config_manager import get_config_manager  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


class OverrideConfig:
    """包装 ConfigManager：覆盖指定无参方法（如 is_include_preprints）的返回值。"""

    def __init__(self, base, **overrides):
        self.__dict__["_base"] = base
        self.__dict__["_overrides"] = overrides

    def __getattr__(self, name):
        ov = self.__dict__["_overrides"]
        if name in ov:
            val = ov[name]
            return lambda: val
        return getattr(self.__dict__["_base"], name)


def parse_time(time_str):
    """时间范围字符串 → (start_date, end_date)"""
    now = datetime.now()
    mapping = {
        "1w": timedelta(days=7),
        "3y": timedelta(days=365 * 3),
        "5y": timedelta(days=365 * 5),
    }
    if time_str == "none":
        return None, None
    delta = mapping.get(time_str)
    if delta is None:
        return None, None
    return now - delta, now


def build_intent(sc):
    start, end = parse_time(sc["time"])
    return SearchIntent(
        query=sc["query"],
        keywords=[],
        research_field=sc["field"],
        language=sc["lang"],
        start_date=start,
        end_date=end,
        filters=sc.get("filters", {}),
        max_results=sc["max"],
    )


def _safe_search(searcher, query, max_results, start, end, label, metrics):
    """单源搜索，异常不致命"""
    try:
        t = time.time()
        papers = searcher.search(query, max_results, start, end)
        metrics[f"{label}_sec"] = round(time.time() - t, 2)
        return papers
    except Exception as e:
        metrics[f"{label}_error"] = f"{type(e).__name__}: {e}"
        return []


def run_experiment(sc):
    out = OUTPUT_DIR / sc["id"]
    out.mkdir(parents=True, exist_ok=True)

    intent = build_intent(sc)
    api_keys = get_config_manager().get_api_keys()
    metrics = {
        "id": sc["id"], "desc": sc["desc"],
        "query": sc["query"], "lang": sc["lang"], "time": sc["time"],
        "filters": sc.get("filters", {}),
        "config_overrides": sc.get("config_overrides", {}),
        "max_per_source": sc["max"], "format": sc["format"],
        "intent_time_range": (
            f"{intent.start_date:%Y-%m-%d} ~ {intent.end_date:%Y-%m-%d}"
            if intent.start_date and intent.end_date else "不限"
        ),
    }

    # 1. 搜索（逐源，便于统计；异常隔离）
    t0 = time.time()
    arxiv = _safe_search(ArxivSearcher(), intent.query, sc["max"],
                         intent.start_date, intent.end_date, "arxiv", metrics)
    s2 = _safe_search(SemanticScholarSearcher(api_keys.get("semantic_scholar", "")),
                      intent.query, sc["max"], intent.start_date, intent.end_date,
                      "s2", metrics)
    oa = _safe_search(OpenAlexSearcher(), intent.query, sc["max"],
                      intent.start_date, intent.end_date, "openalex", metrics)
    merged = arxiv + s2 + oa
    unique = PaperSearcher()._deduplicate(merged)
    metrics["search_total_sec"] = round(time.time() - t0, 2)
    metrics["per_source"] = {"arxiv": len(arxiv), "s2": len(s2), "openalex": len(oa)}
    metrics["pre_dedup"] = len(merged)
    metrics["post_dedup"] = len(unique)

    # 2. 筛选 + 聚类（注入 config 覆盖）
    pf = PaperFilter()
    if sc.get("config_overrides"):
        pf.config = OverrideConfig(get_config_manager(), **sc["config_overrides"])
    filtered = pf.filter_and_sort(unique, intent)
    # 用与 report_generator 一致的 topic_hint 聚类，保证指标与报告一致
    topic_hint = f"{intent.query} {intent.research_field}"
    classified = pf.classify_by_topic(filtered, topic_hint)
    metrics["after_filter"] = len(filtered)
    metrics["hotspots"] = {k: len(v) for k, v in classified.items()}

    # 3. 报告（注入较短超时的 CitationFinder，避免奠基论文查找久挂）
    cf = CitationFinder(api_key=api_keys.get("semantic_scholar", ""),
                        max_papers_to_probe=2)
    cf.timeout = 6
    analyzer = PaperAnalyzer(citation_finder=cf)
    rg = ReportGenerator(paper_filter=pf, paper_analyzer=analyzer)
    t1 = time.time()
    try:
        report = rg.generate_report(filtered, intent, sc["format"])
        metrics["report_sec"] = round(time.time() - t1, 2)
        metrics["report_chars"] = len(report)
        metrics["report_ok"] = True
    except Exception as e:
        metrics["report_sec"] = round(time.time() - t1, 2)
        metrics["report_error"] = f"{type(e).__name__}: {e}"
        metrics["report_ok"] = False
        report = f"# 报告生成失败\n\n{e}\n\n{traceback.format_exc()}"

    # 奠基论文是否走离线回退（PDF 为 bytes，仅对 MD 文本检查）
    if isinstance(report, str):
        metrics["foundational_offline_fallback"] = "离线回退" in report
    else:
        metrics["foundational_offline_fallback"] = False

    # 4. 落盘
    def dump(name, obj):
        (out / name).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    dump("raw_papers.json", [p.to_dict() for p in unique])
    dump("filtered.json", [p.to_dict() for p in filtered])
    dump("hotspots.json",
         {k: [{"title": p.title, "year": p.year, "citations": p.citation_count}
              for p in v] for k, v in classified.items()})
    dump("metrics.json", metrics)

    suffix = ".pdf" if sc["format"] == "pdf" else ".md"
    if isinstance(report, (bytes, bytearray)):
        (out / f"report{suffix}").write_bytes(report)
    else:
        (out / f"report{suffix}").write_text(report, encoding="utf-8")

    return metrics


if __name__ == "__main__":
    from scenarios import SCENARIOS
    ids = sys.argv[1:]
    if ids and ids[0] == "--all":
        ids = [s["id"] for s in SCENARIOS]
    if not ids:
        print("用法: python run_experiment.py E1 | --all")
        sys.exit(1)
    by_id = {s["id"]: s for s in SCENARIOS}
    for sid in ids:
        sc = by_id.get(sid)
        if not sc:
            print(f"未知场景: {sid}")
            continue
        print(f"\n=== 运行 {sid} {sc['desc']} ===")
        m = run_experiment(sc)
        print(f"  搜索: {m['per_source']} | 去重 {m['pre_dedup']}→{m['post_dedup']} "
              f"| 过滤后 {m['after_filter']} | 热点 {len(m['hotspots'])} "
              f"| 报告 {m.get('report_chars','?')} 字符 "
              f"({'OK' if m.get('report_ok') else 'FAIL'})")
