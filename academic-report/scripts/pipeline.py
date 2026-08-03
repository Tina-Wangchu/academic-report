"""
全链路编排：意图解析 → 检索 → 筛选 → 分析 → 报告 → 邮件
对应 design-init.txt「单次搜索模式」：搜索…生成报告并发送到我的邮箱

用法:
  python pipeline.py "搜索最近的 machine learning 论文，生成报告并发送到我的邮箱"
  python pipeline.py "search recent NLP papers" --language bilingual --time 3y \\
      --recipient someone@gmail.com --max-results 8 --format markdown
  python pipeline.py "..." --no-email   # 只生成报告不发送

周期性/定时报告不在本技能范围内——如需周期执行，由调用方（AI Agent / cron 等）
按需重复调用本命令即可。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils import SearchIntent, parse_date_range, safe_filename
from intent_parser import IntentParser
from paper_search import PaperSearcher
from paper_filter import PaperFilter
from paper_analyzer import PaperAnalyzer, CitationFinder
from report_generator import ReportGenerator
from email_sender import EmailSender
from config_manager import get_config_manager

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("pipeline")

# Windows 控制台默认 GBK，强制 stdout 用 utf-8，避免 emoji/中文打印崩溃
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def run_pipeline(user_input: str,
                 language: Optional[str] = None,
                 time_override: Optional[str] = None,
                 recipient: Optional[str] = None,
                 max_results: Optional[int] = None,
                 output_format: Optional[str] = None,
                 send_email: Optional[bool] = None,
                 output_dir: Optional[str] = None) -> dict:
    """
    端到端跑全链路，返回各阶段指标。
    所有默认值来自 config/.env（config_manager）；调用参数为 None 时回退到 .env。
    """
    t0 = datetime.now()
    metrics = {"user_input": user_input}

    # 1. 意图解析
    print("\n[1/6] 意图解析…")
    cfg = get_config_manager()
    intent = IntentParser().parse(user_input)
    intent.language = language or cfg.get_default_language()
    intent.max_results = max_results or cfg.get_max_results()
    # 时间范围：显式 --time 覆盖优先；未传则用 IntentParser 已按 .env DEFAULT_TIME_RANGE 解析的窗口
    if time_override:
        start, end = parse_date_range(time_override)
        if start or end:
            intent.start_date, intent.end_date = start, end

    # 输出/投递参数：None → 回退 .env
    output_format = output_format or cfg.get_output_format()
    if send_email is None:
        send_email = cfg.is_send_email()
    output_dir = output_dir or cfg.get_output_dir()

    print(f"     query={intent.query!r} | field={intent.research_field} "
          f"| lang={intent.language} | keywords={intent.keywords} "
          f"| time={intent.start_date}~{intent.end_date}")

    # 2. 多源检索
    print("\n[2/6] 多源检索…")
    _t = datetime.now()
    searcher = PaperSearcher()
    papers = searcher.search(intent)
    timings = {"search_sec": round((datetime.now() - _t).total_seconds(), 1)}
    src_dist = dict(Counter(p.source for p in papers))
    print(f"     去重后 {len(papers)} 篇，来源: {src_dist}")
    metrics["papers_after_dedup"] = len(papers)
    metrics["source_distribution"] = src_dist
    if getattr(searcher, "search_errors", None):
        print(f"     [search_errors] {searcher.search_errors}")

    # 3. 筛选排序
    print("\n[3/6] 筛选排序…")
    _t = datetime.now()
    pf = PaperFilter()
    filtered = pf.filter_and_sort(papers, intent)
    classified = pf.classify_by_topic(
        filtered, topic_hint=f"{intent.query} {intent.research_field}")
    timings["filter_sec"] = round((datetime.now() - _t).total_seconds(), 1)
    print(f"     过滤后 {len(filtered)} 篇，{len(classified)} 个热点："
          f"{ {k: len(v) for k, v in classified.items()} }")
    metrics["papers_after_filter"] = len(filtered)
    metrics["hotspots"] = {k: len(v) for k, v in classified.items()}

    # 4 & 5. 分析 + 报告（generate_both：_prepare 只跑一次，同时产出 MD + HTML）
    print("\n[4/6] 深度分析 + [5/6] 报告生成…")
    _t = datetime.now()
    cf = CitationFinder(max_papers_to_probe=2)
    cf.timeout = 6                      # 限奠基论文查找耗时
    analyzer = PaperAnalyzer(citation_finder=cf)
    rg = ReportGenerator(paper_filter=pf, paper_analyzer=analyzer)
    md_text, html_text, ctx = rg.generate_both(filtered, intent)
    timings["analyze_report_sec"] = round((datetime.now() - _t).total_seconds(), 1)
    print(f"     报告 {len(md_text)} 字符(MD) / {len(html_text)} 字符(HTML)")

    # 保存到本次运行的「时间戳文件夹」：run_data.json + report.md + report.html
    run_dir = Path(output_dir) / f"{t0:%Y-%m-%d_%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=True)
    md_path = run_dir / "report.md"
    html_path = run_dir / "report.html"
    md_path.write_text(md_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")

    run_data = {
        "generated_at": t0.isoformat(timespec="seconds"),
        "user_input": user_input,
        "intent": intent.to_dict(),
        "source_distribution": src_dist,
        "papers_raw": [p.to_dict() for p in papers],              # 去重后全量（检索原始返回）
        "papers_filtered": [p.to_dict() for p in ctx["papers"]],  # 筛选后 + 分析（含四要素）
        "classified": {k: [p.to_dict() for p in v]
                       for k, v in ctx["classified"].items()},
        "hotspots": {k: len(v) for k, v in ctx["classified"].items()},
        "research_directions": ctx["trends"].get("research_gaps", []),
        "main_trends": ctx["trends"].get("main_trends", []),
        "search_errors": getattr(searcher, "search_errors", {}),
        "timings": timings,
    }
    json_path = run_dir / "run_data.json"
    json_path.write_text(json.dumps(run_data, ensure_ascii=False, indent=2,
                                    default=str), encoding="utf-8")
    print(f"     已保存到: {run_dir}/  (report.md, report.html, run_data.json)")

    report_path = md_path   # 邮件附件默认用 MD
    metrics["report_path"] = str(report_path)
    metrics["report_chars"] = len(md_text)
    metrics["run_dir"] = str(run_dir)
    metrics["md_path"] = str(md_path)
    metrics["html_path"] = str(html_path)
    metrics["json_path"] = str(json_path)
    metrics["generated_at"] = run_data["generated_at"]

    # 6. 邮件发送
    email_ok = False
    if send_email:
        print("\n[6/6] 邮件发送…")
        _t = datetime.now()
        sender = EmailSender()
        recipient_used = recipient or sender.config_manager.get_email_recipient()
        email_ok = sender.send_report(str(report_path), recipient=recipient)
        timings["email_sec"] = round((datetime.now() - _t).total_seconds(), 1)
        print(f"     发送到 {recipient_used}: {'成功 [OK]' if email_ok else '失败 [FAIL]'}")
        metrics["email_sent"] = email_ok
        metrics["recipient"] = recipient_used
    else:
        print("\n[6/6] 跳过邮件发送（--no-email）")
        metrics["email_sent"] = False

    metrics["total_sec"] = round((datetime.now() - t0).total_seconds(), 1)
    print(f"\n全链路完成，耗时 {metrics['total_sec']}s")
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Academic Report 全链路：检索→报告→邮件")
    parser.add_argument("input", help="用户自然语言输入")
    parser.add_argument("--language", default=None, choices=["zh", "en", "bilingual"],
                        help="报告语言（默认读 .env DEFAULT_LANGUAGE）")
    parser.add_argument("--time", help="时间范围覆盖，如 3y / 1y / 1w / none（默认读 .env DEFAULT_TIME_RANGE）")
    parser.add_argument("--recipient", help="收件人邮箱（默认读 .env EMAIL_RECIPIENT）")
    parser.add_argument("--max-results", type=int, default=None,
                        help="每源最大结果数（默认读 .env MAX_RESULTS）")
    parser.add_argument("--format", default=None, choices=["markdown", "html"],
                        help="报告格式（默认读 .env OUTPUT_FORMAT）")
    parser.add_argument("--no-email", action="store_true",
                        help="本次只生成报告不发送（覆盖 .env SEND_EMAIL）")
    parser.add_argument("--output-dir", default=None, help="报告保存目录（默认读 .env OUTPUT_DIR）")
    args = parser.parse_args()

    try:
        m = run_pipeline(
            user_input=args.input,
            language=args.language,
            time_override=args.time,
            recipient=args.recipient,
            max_results=args.max_results,
            output_format=args.format,
            send_email=False if args.no_email else None,
            output_dir=args.output_dir,
        )
        return 0 if (not args.no_email and m.get("email_sent")) else 0
    except Exception as e:
        logger.error("全链路失败: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
