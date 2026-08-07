#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Academic Report —— 分模块测试运行
逐个跑 6 个核心模块，捕获每个模块的【返回字段/结果】，存到本目录（test-report/）。

用法：python run_modules.py
（需在 anaconda 或已装 arxiv 的环境运行）
"""
import sys
import os
import json
import time
import logging
from pathlib import Path
from collections import Counter

# 静音第三方日志，让输出干净
logging.disable(logging.CRITICAL)

SCRIPTS = Path(__file__).resolve().parent.parent / "academic-report" / "scripts"
sys.path.insert(0, str(SCRIPTS))
OUT = Path(__file__).resolve().parent  # test-report/

QUERY = "search recent deep learning papers"
MAX_RESULTS = 5
LANG = "bilingual"

results = {}


def save(name, data):
    p = OUT / name
    if isinstance(data, str):
        p.write_text(data, encoding="utf-8")
    else:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str),
                     encoding="utf-8")
    print(f"   ↳ saved {name}")


def step(mod, fn):
    t = time.time()
    try:
        out = fn()
        elapsed = round(time.time() - t, 2)
        results[mod] = {"ok": True, "elapsed_sec": elapsed}
        return out, elapsed
    except Exception as e:
        elapsed = round(time.time() - t, 2)
        import traceback
        results[mod] = {"ok": False, "elapsed_sec": elapsed,
                        "error": f"{type(e).__name__}: {e}",
                        "trace": traceback.format_exc()[:800]}
        print(f"   ✗ FAILED: {type(e).__name__}: {e}")
        return None, elapsed


# =========================================================================
print("\n" + "=" * 60)
print("[1/6] intent_parser  ——  返回 SearchIntent")
print("=" * 60)
from intent_parser import IntentParser  # noqa: E402


def _intent():
    it = IntentParser().parse(QUERY)
    it.max_results = MAX_RESULTS
    return it


intent, dt = step("intent_parser", _intent)
if intent:
    fields = intent.to_dict()
    save("01_intent.json", {
        "_module": "intent_parser.IntentParser.parse(query) -> SearchIntent",
        "_elapsed_sec": dt,
        "input_query": QUERY,
        "field_names": list(fields.keys()),
        "fields": fields,
    })
    print(f"   query={intent.query!r} field={intent.research_field} "
          f"lang={intent.language} time={intent.start_date}~{intent.end_date}")

# =========================================================================
print("\n" + "=" * 60)
print("[2/6] paper_search  ——  返回 List[Paper]")
print("=" * 60)
from paper_search import PaperSearcher  # noqa: E402


def _search():
    return PaperSearcher().search(intent)


papers, dt = step("paper_search", _search)
if papers:
    src_dist = dict(Counter(p.source for p in papers))
    sample = papers[:MAX_RESULTS]
    view = [{
        "title": p.title,
        "authors": p.authors[:3],
        "year": p.year,
        "venue": p.venue,
        "venue_type": p.venue_type,
        "ranking": p.ranking,
        "doi": p.doi,
        "citation_count": p.citation_count,
        "source": p.source,
        "published_date": str(p.published_date) if p.published_date else None,
        "keywords": p.keywords,
        "tldr": (p.tldr[:100] + "...") if p.tldr else "",
        "condensed_abstract": (p.condensed_abstract[:100] + "...") if p.condensed_abstract else "",
        "url": p.url,
        "pdf_url": p.pdf_url,
    } for p in sample]
    all_fields = list(papers[0].to_dict().keys()) if papers else []
    save("02_search.json", {
        "_module": "paper_search.PaperSearcher.search(intent) -> List[Paper]",
        "_elapsed_sec": dt,
        "total_count": len(papers),
        "source_distribution": src_dist,
        "all_paper_field_names": all_fields,
        f"sample_papers(first_{MAX_RESULTS})": view,
    })
    print(f"   去重后 {len(papers)} 篇，来源分布: {src_dist}")

# =========================================================================
print("\n" + "=" * 60)
print("[3/6] paper_filter  ——  返回 filtered + classified(热点)")
print("=" * 60)
from paper_filter import PaperFilter  # noqa: E402
pf = PaperFilter()


def _filter():
    filt = pf.filter_and_sort(papers, intent)
    cls = pf.classify_by_topic(
        filt, topic_hint=f"{intent.query} {intent.research_field}")
    return filt, cls


(filtered, classified), dt = step("paper_filter", _filter)
if filtered is not None:
    save("03_filter.json", {
        "_module": "paper_filter.PaperFilter.filter_and_sort / classify_by_topic",
        "_elapsed_sec": dt,
        "before_count": len(papers),
        "after_filter_count": len(filtered),
        "hotspot_count": len(classified),
        "hotspot_distribution": {k: len(v) for k, v in classified.items()},
        "hotspots": {k: [p.title for p in ps] for k, ps in classified.items()},
    })
    print(f"   过滤 {len(papers)}→{len(filtered)} 篇，{len(classified)} 个热点: "
          f"{ {k: len(v) for k, v in classified.items()} }")

# =========================================================================
print("\n" + "=" * 60)
print("[4/6] paper_analyzer + llm_analyzer  ——  四要素 + 研究方向")
print("=" * 60)
from llm_analyzer import FourElementAnalyzer, generate_research_directions  # noqa: E402
fea = FourElementAnalyzer()


def _analysis():
    samples = []
    for p in (filtered or [])[:2]:   # 取前 2 篇做四要素（LLM 调用，控量）
        r = fea.analyze(p, LANG)
        samples.append({"title": p.title, "four_element": r})
    dirs = generate_research_directions(filtered or [], LANG)
    return samples, dirs


(fe_samples, directions), dt = step("analysis(llm)", _analysis)
if fe_samples is not None:
    save("04_analysis.json", {
        "_module": "paper_analyzer.PaperAnalyzer / llm_analyzer.FourElementAnalyzer / generate_research_directions",
        "_elapsed_sec": dt,
        "four_element_field_names": ["problem", "existing_approaches",
                                     "new_approach", "results_limitations",
                                     "analysis_source"],
        f"four_element_samples(first_{min(2, len(filtered or []))})": fe_samples,
        "research_directions(deep_dive)": [{"zh": zh, "en": en} for zh, en in directions],
    })
    print(f"   四要素样本 {len(fe_samples)} 篇；研究方向 {len(directions)} 条")

# =========================================================================
print("\n" + "=" * 60)
print("[5/6] report_generator  ——  返回 report 文本(MD/HTML)")
print("=" * 60)
from paper_analyzer import PaperAnalyzer, CitationFinder  # noqa: E402
from report_generator import ReportGenerator  # noqa: E402


def _report():
    cf = CitationFinder(max_papers_to_probe=2)
    cf.timeout = 6
    analyzer = PaperAnalyzer(citation_finder=cf)
    rg = ReportGenerator(paper_filter=pf, paper_analyzer=analyzer)
    md = rg.generate_report(filtered, intent, "markdown")
    pdf = rg.generate_report(filtered, intent, "pdf")
    return md, pdf


(md, pdf), dt = step("report_generator", _report)
if md is not None:
    (OUT / "05_report.md").write_text(md, encoding="utf-8")
    (OUT / "05_report.pdf").write_bytes(pdf)
    save("05_report_meta.json", {
        "_module": "report_generator.ReportGenerator.generate_report() -> str|bytes",
        "_elapsed_sec": dt,
        "markdown_chars": len(md),
        "pdf_bytes": len(pdf),
        "saved_files": ["05_report.md", "05_report.pdf"],
    })
    print(f"   报告 {len(md)} 字符(MD) / {len(pdf)} 字节(PDF)")

# =========================================================================
print("\n" + "=" * 60)
print("[6/6] email_sender  ——  SMTP 配置校验 + 连接测试(不发送)")
print("=" * 60)
from email_sender import EmailSender  # noqa: E402
from config_manager import get_config_manager  # noqa: E402


def _email():
    cfg = get_config_manager()
    valid, err = cfg.validate_smtp_config()
    smtp = cfg.get_smtp_config()
    out = {
        "smtp_configured": valid,
        "smtp_host": smtp.get("host"),
        "smtp_port": smtp.get("port"),
        "smtp_user": (smtp.get("user") or "(none)"),
        "validation_error": (err if not valid else None),
    }
    if valid:
        try:
            ok, msg = EmailSender().test_connection()
            out["test_connection"] = {"ok": ok, "message": msg}
        except Exception as e:  # noqa: BLE001
            out["test_connection"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return out


email_out, dt = step("email_sender", _email)
if email_out:
    email_out["_elapsed_sec"] = dt
    save("06_email_test.json", email_out)
    print(f"   SMTP configured={email_out['smtp_configured']} "
          f"test={email_out.get('test_connection', {}).get('ok')}")

# =========================================================================
print("\n" + "=" * 60)
print("汇总")
print("=" * 60)
summary = {
    "query": QUERY,
    "max_results_per_source": MAX_RESULTS,
    "language": LANG,
    "modules": results,
}
save("summary.json", summary)

# 人类可读 summary.md
lines = ["# Academic Report 分模块测试运行结果\n",
         f"- 查询: `{QUERY}`",
         f"- 每源最大结果数: {MAX_RESULTS}",
         f"- 报告语言: {LANG}\n",
         "## 各模块状态\n",
         "| 模块 | 状态 | 耗时(s) | 说明 |",
         "|------|------|---------|------|"]
for mod, info in results.items():
    status = "✅" if info.get("ok") else "❌"
    extra = ""
    if mod == "paper_search" and info.get("ok"):
        extra = f"{info.get('count', '?')} 篇" if 'count' in info else ""
    note = info.get("error", extra) if not info.get("ok") else extra
    lines.append(f"| {mod} | {status} | {info.get('elapsed_sec','?')} | {note} |")
lines += ["\n## 结果文件\n",
          "- `01_intent.json` SearchIntent 字段",
          "- `02_search.json` Paper 列表 + 全部字段名",
          "- `03_filter.json` 筛选/热点聚类",
          "- `04_analysis.json` 四要素样本 + 研究方向",
          "- `05_report.md` / `05_report.pdf` 生成的报告",
          "- `05_report_meta.json` 报告元信息",
          "- `06_email_test.json` SMTP 测试",
          "- `summary.json` 机器可读汇总"]
(OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")

print("\nDONE. 结果见 test-report/")
print(json.dumps(results, ensure_ascii=False, indent=2))
