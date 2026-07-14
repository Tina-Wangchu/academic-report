"""
全链路编排：意图解析 → 检索 → 筛选 → 分析 → 报告 → 邮件
对应 design-init.txt「单次搜索模式」：/academic-scholar 搜索…生成报告并发送到我的邮箱

用法:
  python pipeline.py "搜索最近的 machine learning 论文，生成报告并发送到我的邮箱"
  python pipeline.py "search recent NLP papers" --language bilingual --time 3y \\
      --recipient someone@gmail.com --max-results 8 --format markdown
  python pipeline.py "..." --no-email   # 只生成报告不发送
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils import SearchIntent, parse_date_range, safe_filename, schedule_interval
from intent_parser import IntentParser
from paper_search import PaperSearcher
from paper_filter import PaperFilter
from paper_analyzer import PaperAnalyzer, CitationFinder
from report_generator import ReportGenerator
from email_sender import EmailSender
from config_manager import get_config_manager
from timestamp_manager import get_timestamp_manager

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("pipeline")

# Windows 控制台默认 GBK，强制 stdout 用 utf-8，避免 emoji/中文打印崩溃
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def run_pipeline(user_input: str,
                 language: str = "bilingual",
                 time_override: Optional[str] = None,
                 recipient: Optional[str] = None,
                 max_results: int = 10,
                 output_format: str = "markdown",
                 send_email: bool = True,
                 output_dir: str = "reports",
                 incremental: bool = False,
                 topic_override: Optional[str] = None,
                 no_incremental: bool = False,
                 send_empty: bool = False) -> dict:
    """
    端到端跑全链路，返回各阶段指标。

    增量模式（incremental=True 或 intent.is_scheduled 且未禁用）：
    - 时间窗口 = [上次报告时间, now]（首次 = [now-周期, now]）。
    - 客户端按年份兜底过滤（S2 仅年粒度）。
    - 仅邮件发送成功后才更新时间戳（--no-email 时生成成功即更新）。
    - 空增量默认跳过邮件、不更新时间戳（--send-empty 强制通知）。
    """
    t0 = datetime.now()
    metrics = {"user_input": user_input}

    # 1. 意图解析
    print("\n[1/6] 意图解析…")
    intent = IntentParser().parse(user_input)
    intent.language = language          # 项目默认 bilingual
    intent.max_results = max_results
    if time_override:
        start, end = parse_date_range(time_override)
        if start or end:
            intent.start_date, intent.end_date = start, end

    # 增量模式：显式开启 或 检测到定时意图（未被 --no-incremental 禁用）
    do_incremental = incremental or (intent.is_scheduled and not no_incremental)
    last_run = None
    topic_key = None
    if do_incremental:
        tm = get_timestamp_manager()
        topic_key = topic_override or tm.topic_key(intent.query, intent.research_field)
        now = datetime.now()
        last_run = tm.get_last_run(topic_key)
        if last_run is None:
            # 首次运行：用调度周期作基线窗口
            last_run = now - schedule_interval(intent.schedule)
            print(f"     [incremental] 首次运行，基线窗口 = {intent.schedule or 'weekly'}")
        intent.start_date = last_run
        intent.end_date = now
        print(f"     [incremental] topic={topic_key} "
              f"window={last_run:%Y-%m-%d}..{now:%Y-%m-%d}")

    print(f"     query={intent.query!r} | field={intent.research_field} "
          f"| lang={intent.language} | keywords={intent.keywords} "
          f"| time={intent.start_date}~{intent.end_date}"
          f"{' [incremental]' if do_incremental else ''}")

    # 2. 多源检索
    print("\n[2/6] 多源检索…")
    papers = PaperSearcher().search(intent)
    print(f"     去重后 {len(papers)} 篇")
    metrics["papers_after_dedup"] = len(papers)

    # 增量客户端兜底过滤：丢掉早于 last_run 的论文（日级精确，回退 year）
    # S2 API 仅年粒度 → 会返回整年论文；这里用 published_date 精修到「last_run 之后」
    if do_incremental and last_run is not None:
        before = len(papers)
        cutoff_date = last_run.date()
        cutoff_year = last_run.year

        def _after_last_run(p):
            # 优先日级（published_date）；缺失则回退年粒度（避免误删无日期论文）
            if p.published_date is not None:
                return p.published_date >= cutoff_date
            return (p.year or 0) >= cutoff_year

        papers = [p for p in papers if _after_last_run(p)]
        print(f"     [incremental] 客户端增量过滤 {before}→{len(papers)} "
              f"(≥{cutoff_date}，日级；无日期回退年)")
        metrics["papers_after_increment_filter"] = len(papers)

    # 3. 筛选排序
    print("\n[3/6] 筛选排序…")
    pf = PaperFilter()
    filtered = pf.filter_and_sort(papers, intent)
    classified = pf.classify_by_topic(
        filtered, topic_hint=f"{intent.query} {intent.research_field}")
    print(f"     过滤后 {len(filtered)} 篇，{len(classified)} 个热点："
          f"{ {k: len(v) for k, v in classified.items()} }")
    metrics["papers_after_filter"] = len(filtered)
    metrics["hotspots"] = {k: len(v) for k, v in classified.items()}

    # 空增量：本期无新论文 → 跳过报告/邮件/时间戳更新（--send-empty 可强制）
    if do_incremental and not filtered and not send_empty:
        print("\n[incremental] 本期无新论文，跳过报告与邮件，不更新时间戳。"
              "（--send-empty 可强制发通知）")
        metrics["incremental_empty"] = True
        metrics["total_sec"] = round((datetime.now() - t0).total_seconds(), 1)
        print(f"\n全链路完成（空增量），耗时 {metrics['total_sec']}s")
        return metrics

    # 4 & 5. 分析 + 报告（report_generator 内部完成分析/聚类/奠基/渲染）
    print("\n[4/6] 深度分析 + [5/6] 报告生成…")
    cf = CitationFinder(max_papers_to_probe=2)
    cf.timeout = 6                      # 限奠基论文查找耗时
    analyzer = PaperAnalyzer(citation_finder=cf)
    rg = ReportGenerator(paper_filter=pf, paper_analyzer=analyzer)
    report = rg.generate_report(filtered, intent, output_format)
    print(f"     报告 {len(report)} 字符")

    # 保存报告
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".html" if output_format == "html" else ".md"
    field_slug = safe_filename(intent.research_field or "report")[:20]
    report_path = out_dir / f"{field_slug}_{datetime.now():%Y%m%d_%H%M}{suffix}"
    report_path.write_text(report, encoding="utf-8")
    print(f"     已保存: {report_path}")
    metrics["report_path"] = str(report_path)
    metrics["report_chars"] = len(report)

    # 6. 邮件发送
    inc_subject = None
    if do_incremental and intent.start_date and intent.end_date:
        inc_subject = (f"增量报告 / Incremental "
                       f"({intent.start_date:%Y-%m-%d} → {intent.end_date:%Y-%m-%d})")

    email_ok = False
    if send_email:
        print("\n[6/6] 邮件发送…")
        sender = EmailSender()
        recipient_used = recipient or sender.config_manager.get_email_recipient()
        email_ok = sender.send_report(
            str(report_path), recipient=recipient, subject=inc_subject)
        print(f"     发送到 {recipient_used}: {'成功 ✅' if email_ok else '失败 ❌'}"
              f"{f'  [{inc_subject}]' if inc_subject else ''}")
        metrics["email_sent"] = email_ok
        metrics["recipient"] = recipient_used
    else:
        print("\n[6/6] 跳过邮件发送（--no-email）")
        metrics["email_sent"] = False

    # 增量时间戳：仅邮件成功后更新（--no-email 时生成成功即更新，供本地测试）
    if do_incremental and topic_key:
        if (send_email and email_ok) or not send_email:
            get_timestamp_manager().update_last_run(topic_key)
            print(f"     [incremental] 时间戳已更新: {topic_key}")

    metrics["total_sec"] = round((datetime.now() - t0).total_seconds(), 1)
    print(f"\n全链路完成，耗时 {metrics['total_sec']}s")
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Scholar 全链路：检索→报告→邮件")
    parser.add_argument("input", help="用户自然语言输入")
    parser.add_argument("--language", default="bilingual",
                        choices=["zh", "en", "bilingual"])
    parser.add_argument("--time", help="时间范围覆盖，如 3y / 1y / 1w / none")
    parser.add_argument("--recipient", help="收件人邮箱（默认 ~/.hermes/.env 配置）")
    parser.add_argument("--max-results", type=int, default=10, help="每源最大结果数")
    parser.add_argument("--format", default="markdown", choices=["markdown", "html"])
    parser.add_argument("--no-email", action="store_true", help="只生成报告不发送")
    parser.add_argument("--output-dir", default="reports", help="报告保存目录")
    parser.add_argument("--incremental", action="store_true",
                        help="增量模式：仅检索上次报告后的论文（读时间戳窗口）")
    parser.add_argument("--topic", help="覆盖增量 topic_key（自定义增量主题）")
    parser.add_argument("--no-incremental", action="store_true",
                        help="即使检测到定时意图也禁用增量")
    parser.add_argument("--send-empty", action="store_true",
                        help="本期无新论文时仍发通知邮件")
    args = parser.parse_args()

    try:
        m = run_pipeline(
            user_input=args.input,
            language=args.language,
            time_override=args.time,
            recipient=args.recipient,
            max_results=args.max_results,
            output_format=args.format,
            send_email=not args.no_email,
            output_dir=args.output_dir,
            incremental=args.incremental,
            topic_override=args.topic,
            no_incremental=args.no_incremental,
            send_empty=args.send_empty,
        )
        return 0 if (not args.no_email and m.get("email_sent")) else 0
    except Exception as e:
        logger.error("全链路失败: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
