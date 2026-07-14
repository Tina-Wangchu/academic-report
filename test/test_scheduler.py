"""
测试增量分支（定时报告模式）+ scheduler 工具函数。
不联网：用 Fake 替换 PaperSearcher/PaperFilter/ReportGenerator/EmailSender，
       注入 FakeTimestampManager（monkeypatch pipeline.get_timestamp_manager）。
scheduler.py 的运行循环测试见 Phase D 补充。
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-scholar', 'scripts'))

from utils import schedule_interval, Paper
import pipeline


# ----------------------------- 工具函数 ----------------------------- #

class TestScheduleInterval:
    def test_known_tokens(self):
        assert schedule_interval("daily") == timedelta(days=1)
        assert schedule_interval("weekly") == timedelta(days=7)
        assert schedule_interval("biweekly") == timedelta(days=14)
        assert schedule_interval("monthly") == timedelta(days=30)

    def test_every_Nd(self):
        assert schedule_interval("every-3d") == timedelta(days=3)

    def test_unknown_and_none_default(self):
        assert schedule_interval("nonsense") == timedelta(days=7)
        assert schedule_interval(None) == timedelta(days=7)


# ------------------------------- Fakes ------------------------------ #

class FakeTimestampManager:
    def __init__(self, last_run=None):
        self._last = last_run
        self.updated = []                      # (key, when)

    def topic_key(self, query, field):
        return f"fake|{query}|{field}"

    def get_last_run(self, key):
        return self._last

    def update_last_run(self, key, when=None):
        self.updated.append((key, when))
        return when or datetime.now()


def _paper(title, year):
    return Paper(title=title, authors=["A"], venue="V", year=year, doi="",
                 abstract="", keywords=[], citation_count=0,
                 venue_type="journal", ranking="普通", source="test")


class FakeSearcher:
    def search(self, intent):
        return [_paper("Old", 2020), _paper("Mid", 2025), _paper("New", 2026)]


class FakeFilter:
    def filter_and_sort(self, papers, intent):
        return list(papers)

    def classify_by_topic(self, papers, topic_hint=""):
        return {"热点": list(papers)}

    def generate_hotspot_intro(self, topic, papers):
        return "intro"


class FakeReportGen:
    def __init__(self, paper_filter=None, paper_analyzer=None):
        pass

    def generate_report(self, papers, intent, fmt="markdown"):
        return "# fake report"


class FakeEmailSender:
    succeed = True

    def __init__(self):
        self.config_manager = type(
            "CM", (), {"get_email_recipient": lambda self: "x@y.com"})()

    def send_report(self, path, recipient=None, subject=None):
        return self.succeed


@pytest.fixture
def patched(monkeypatch):
    monkeypatch.setattr(pipeline, "PaperSearcher", FakeSearcher)
    monkeypatch.setattr(pipeline, "PaperFilter", FakeFilter)
    monkeypatch.setattr(pipeline, "ReportGenerator", FakeReportGen)
    monkeypatch.setattr(pipeline, "EmailSender", FakeEmailSender)
    return monkeypatch


# --------------------------- 增量分支 ------------------------------- #

class TestIncrementalBranch:
    def test_explicit_incremental_runs(self, patched, tmp_path):
        tm = FakeTimestampManager(last_run=datetime(2026, 1, 1))
        patched.setattr(pipeline, "get_timestamp_manager", lambda: tm)
        m = pipeline.run_pipeline("搜索 machine learning 论文",
                                  incremental=True, send_email=False,
                                  output_dir=str(tmp_path))
        assert "papers_after_increment_filter" in m
        # last.year=2026 → 仅保留 year>=2026（New）
        assert m["papers_after_increment_filter"] == 1

    def test_incremental_day_level_filter(self, patched, tmp_path):
        """published_date 日级过滤：同年但早于 last_run 的论文被剔除（M6 修复）"""
        from datetime import date as _date
        # 两篇 2026 论文：一篇 last_run 之前，一篇之后
        class DateSearcher:
            def search(self, intent):
                old = _paper("OldSameYear", 2026)
                old.published_date = _date(2026, 3, 1)    # 早于 last_run
                new = _paper("NewSameYear", 2026)
                new.published_date = _date(2026, 12, 1)   # 晚于 last_run
                return [old, new]
        patched.setattr(pipeline, "PaperSearcher", DateSearcher)
        tm = FakeTimestampManager(last_run=datetime(2026, 7, 1))
        patched.setattr(pipeline, "get_timestamp_manager", lambda: tm)
        m = pipeline.run_pipeline("每周发送论文", incremental=True,
                                  send_email=False, output_dir=str(tmp_path))
        # 仅 year 级时两篇 2026 都会过；日级后 old(03-01<07-01) 被丢 → 只剩 new
        assert m["papers_after_increment_filter"] == 1

    def test_first_run_falls_back_to_interval(self, patched, tmp_path):
        tm = FakeTimestampManager(last_run=None)
        patched.setattr(pipeline, "get_timestamp_manager", lambda: tm)
        m = pipeline.run_pipeline("每周一发送 machine learning 论文",
                                  send_email=False, output_dir=str(tmp_path))
        assert tm.updated  # --no-email 时生成成功即更新（建立基线）

    def test_timestamp_updated_on_no_email(self, patched, tmp_path):
        tm = FakeTimestampManager(last_run=datetime(2026, 1, 1))
        patched.setattr(pipeline, "get_timestamp_manager", lambda: tm)
        pipeline.run_pipeline("每周一发送 machine learning 论文",
                              send_email=False, output_dir=str(tmp_path))
        assert len(tm.updated) == 1

    def test_timestamp_updated_on_email_success(self, patched, tmp_path):
        tm = FakeTimestampManager(last_run=datetime(2026, 1, 1))
        patched.setattr(pipeline, "get_timestamp_manager", lambda: tm)
        pipeline.run_pipeline("每周一发送 machine learning 论文",
                              send_email=True, output_dir=str(tmp_path))
        assert len(tm.updated) == 1

    def test_timestamp_not_updated_on_email_failure(self, patched, tmp_path):
        class FailEmail(FakeEmailSender):
            def send_report(self, path, recipient=None, subject=None):
                return False
        patched.setattr(pipeline, "EmailSender", FailEmail)
        tm = FakeTimestampManager(last_run=datetime(2026, 1, 1))
        patched.setattr(pipeline, "get_timestamp_manager", lambda: tm)
        pipeline.run_pipeline("每周一发送 machine learning 论文",
                              send_email=True, output_dir=str(tmp_path))
        assert tm.updated == []   # 失败 → 不更新

    def test_empty_increment_skips_and_no_update(self, patched, tmp_path):
        class OldSearcher:
            def search(self, intent):
                return [_paper("Old", 2019)]   # 全部早于 last.year(2026)
        patched.setattr(pipeline, "PaperSearcher", OldSearcher)
        tm = FakeTimestampManager(last_run=datetime(2026, 1, 1))
        patched.setattr(pipeline, "get_timestamp_manager", lambda: tm)
        m = pipeline.run_pipeline("每周一发送 machine learning 论文",
                                  send_email=True, output_dir=str(tmp_path))
        assert m.get("incremental_empty") is True
        assert tm.updated == []

    def test_no_incremental_when_disabled(self, patched, tmp_path):
        """定时意图 + --no-incremental → 不走增量（不读/写时间戳）"""
        tm = FakeTimestampManager(last_run=datetime(2026, 1, 1))
        patched.setattr(pipeline, "get_timestamp_manager", lambda: tm)
        m = pipeline.run_pipeline("每周一发送 machine learning 论文",
                                  no_incremental=True, send_email=False,
                                  output_dir=str(tmp_path))
        assert "papers_after_increment_filter" not in m
        assert tm.updated == []


# ----------------------- scheduler.run 循环 ------------------------- #
# 用 monkeypatch scheduler.run_pipeline + config 收件人，避免真实网络/等待。

import scheduler


class _CallTracker:
    """记录 run_pipeline 调用次数与 incremental 参数。"""
    def __init__(self):
        self.calls = []

    def __call__(self, user_input, **kwargs):
        self.calls.append(kwargs)
        return {"incremental_empty": False}


@pytest.fixture
def patched_scheduler(monkeypatch):
    tracker = _CallTracker()
    monkeypatch.setattr(scheduler, "run_pipeline", tracker)
    # 收件人默认：避免缺收件人直接 return 1
    monkeypatch.setattr(scheduler, "get_config_manager",
                        lambda: type("CM", (),
                                     {"get_email_recipient": lambda self: "me@x.com"})())
    return tracker


class TestSchedulerRun:
    def test_once_fires_exactly_once(self, patched_scheduler):
        rc = scheduler.run("每周一发送 machine learning 论文", once=True,
                           recipient="me@x.com")
        assert rc == 0
        assert len(patched_scheduler.calls) == 1
        assert patched_scheduler.calls[0]["incremental"] is True

    def test_dry_run_does_not_call_pipeline(self, patched_scheduler):
        rc = scheduler.run("每周发送 NLP 报告", dry_run=True, recipient="me@x.com")
        assert rc == 0
        assert patched_scheduler.calls == []

    def test_non_scheduled_input_defaults_weekly(self, patched_scheduler):
        """无定时短语 → 默认 weekly 仍能跑（once）"""
        rc = scheduler.run("搜索 machine learning 论文", once=True,
                           recipient="me@x.com")
        assert rc == 0
        assert len(patched_scheduler.calls) == 1

    def test_missing_recipient_returns_error(self, patched_scheduler, monkeypatch):
        """无收件人 → 返回 1，不跑 pipeline"""
        monkeypatch.setattr(scheduler, "get_config_manager",
                            lambda: type("CM", (),
                                         {"get_email_recipient": lambda self: ""})())
        rc = scheduler.run("每周发送论文", once=True)
        assert rc == 1
        assert patched_scheduler.calls == []

    def test_sigint_breaks_loop(self, patched_scheduler, monkeypatch):
        """设置 _RUNNING=False 后循环应退出（不再触发）"""
        scheduler._RUNNING = False
        try:
            rc = scheduler.run("每周发送论文", recipient="me@x.com")
            assert rc == 0
            assert patched_scheduler.calls == []   # 未触发
        finally:
            scheduler._RUNNING = True              # 复位

