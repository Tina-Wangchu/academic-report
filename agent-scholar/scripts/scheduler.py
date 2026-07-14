"""
定时增量报告调度器（定时报告模式入口 / Module 8）

进程内定时循环（不依赖 Hermes）：解析「每周一/每个月/每天」等周期短语，
立即首次触发（建立增量基线），之后按周期调用 pipeline 增量分支
（仅检索 [上次报告时间, 现在] 的论文）。

用法:
  python scheduler.py "每周一发送 machine learning 论文" --recipient me@x.com
  python scheduler.py "每周发送 NLP 报告" --once            # 立即触发一次并退出（测试）
  python scheduler.py "每月综述" --dry-run                  # 仅打印周期/下次触发，不运行
  python scheduler.py "每天最新论文" --no-email             # 调试：只生成不发送

可选 cron 支持：若安装 croniter，可用 --cron "0 9 * * 1"（5 字段 cron）；
未安装则忽略 cron、按周期短语（默认 weekly）运行。
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

from utils import schedule_interval
from intent_parser import IntentParser
from pipeline import run_pipeline
from config_manager import get_config_manager

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("scheduler")

# Windows 控制台默认 GBK，强制 stdout 用 utf-8，避免 emoji/中文打印崩溃
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 可选 cron 支持
try:
    from croniter import croniter       # type: ignore
    _HAS_CRONITER = True
except ImportError:
    _HAS_CRONITER = False

_RUNNING = True


def _sigint(sig, frame):
    """SIGINT：优雅退出（不强杀正在跑的 pipeline）。"""
    global _RUNNING
    _RUNNING = False
    print("\n[scheduler] 收到中断信号，将在当前任务后退出…")


def _interruptible_sleep(seconds: float) -> None:
    """分段 sleep（每 ≤5s 醒一次），以便 SIGINT 能及时退出。"""
    end = time.monotonic() + max(0.0, seconds)
    while _RUNNING and time.monotonic() < end:
        time.sleep(min(5.0, end - time.monotonic()))


def _next_fire_from_cron(cron_expr: str, base: datetime) -> Optional[datetime]:
    """有 croniter 时，算下次触发时间；否则返回 None。"""
    if not _HAS_CRONITER:
        logger.warning("未安装 croniter，忽略 cron 表达式 %r", cron_expr)
        return None
    try:
        return croniter(cron_expr, base).get_next(datetime)
    except Exception as e:
        logger.warning("cron 表达式非法 %r: %s", cron_expr, e)
        return None


def run(user_input: str,
        recipient: Optional[str] = None,
        once: bool = False,
        dry_run: bool = False,
        language: str = "bilingual",
        max_results: int = 10,
        output_format: str = "markdown",
        send_email: bool = True,
        cron: Optional[str] = None) -> int:
    """
    解析周期 → 首次立即触发（基线）→ 按周期循环增量报告。
    once=True：触发一次即退出。dry_run=True：只打印，不运行。
    """
    global _RUNNING

    intent = IntentParser().parse(user_input)
    if not intent.is_scheduled:
        print(f"[scheduler] 未检测到定时短语，按 weekly 默认运行。input={user_input!r}")
        intent.schedule = "weekly"
    interval = schedule_interval(intent.schedule)
    print(f"[scheduler] 周期={intent.schedule} → 每 {interval.days} 天")

    recipient = recipient or get_config_manager().get_email_recipient()
    if not recipient:
        print("[scheduler] 未配置收件人（config email_recipient / --recipient）。")
        return 1

    use_cron = bool(cron) and _HAS_CRONITER

    if dry_run:
        print(f"[dry-run] 收件人: {recipient}")
        if use_cron:
            nf = _next_fire_from_cron(cron, datetime.now())
            print(f"[dry-run] cron={cron}；下次触发: "
                  f"{nf:%Y-%m-%d %H:%M:%S}" if nf else f"[dry-run] cron 非法或无 croniter")
        else:
            print(f"[dry-run] 首次立即触发（基线），之后每 {interval.days} 天一次；"
                  f"下次周期触发约 {datetime.now() + interval:%Y-%m-%d %H:%M:%S}")
        print("[dry-run] 不运行 pipeline。")
        return 0

    # 首次立即触发（建立增量基线时间戳）
    next_fire = datetime.now()
    iteration = 0
    while _RUNNING:
        now = datetime.now()
        sleep_for = (next_fire - now).total_seconds()
        if sleep_for > 0:
            print(f"[scheduler] 休眠 {sleep_for:.0f}s 至 {next_fire:%Y-%m-%d %H:%M:%S}")
            _interruptible_sleep(sleep_for)
            if not _RUNNING:
                break

        print(f"\n[scheduler] === 触发增量报告 #{iteration + 1} "
              f"@ {datetime.now():%Y-%m-%d %H:%M:%S} ===")
        try:
            run_pipeline(user_input, language=language, recipient=recipient,
                         max_results=max_results, output_format=output_format,
                         send_email=send_email, incremental=True)
        except Exception as e:
            logger.error("[scheduler] 增量运行失败（不更新时间戳）: %s", e)

        if once:
            print("\n[scheduler] --once 完成，退出。")
            return 0

        iteration += 1
        if use_cron:
            nf = _next_fire_from_cron(cron, datetime.now())
            next_fire = nf or (datetime.now() + interval)
        else:
            next_fire = datetime.now() + interval

    print("[scheduler] 已退出。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Agent Scholar 定时增量报告调度器（进程内定时，不依赖 Hermes）")
    parser.add_argument("input", help="自然语言，如 '每周一发送 machine learning 论文'")
    parser.add_argument("--recipient", help="收件人（默认 config email_recipient）")
    parser.add_argument("--once", action="store_true", help="立即触发一次并退出（测试用）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印周期/下次触发，不运行")
    parser.add_argument("--language", default="bilingual", choices=["zh", "en", "bilingual"])
    parser.add_argument("--format", default="markdown", choices=["markdown", "html"])
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--no-email", action="store_true", help="只生成报告不发送")
    parser.add_argument("--cron", help="5 字段 cron 表达式（需已安装 croniter）")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _sigint)
    return run(args.input, recipient=args.recipient, once=args.once,
               dry_run=args.dry_run, language=args.language,
               max_results=args.max_results, output_format=args.format,
               send_email=not args.no_email, cron=args.cron)


if __name__ == "__main__":
    sys.exit(main())
