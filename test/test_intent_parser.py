"""
测试 intent_parser.py
覆盖：定时检测/抽取、parse() 设 is_scheduled/schedule、定时默认短窗口，
      以及既有字段（query/field/language/time_range/filters）基线。
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-scholar', 'scripts'))

from intent_parser import IntentParser


@pytest.fixture
def parser():
    return IntentParser()


# --------------------------- 定时检测 --------------------------- #

class TestDetectSchedule:
    @pytest.mark.parametrize("text", [
        "每周一发送 machine learning 论文",
        "每个月发送 NLP 报告",
        "每两周发一次综述",
        "每天发送最新论文",
        "every week send papers",
        "monthly report",
        "daily digest",
        "定时发送",
        "周期性报告",
    ])
    def test_detected(self, parser, text):
        assert parser._detect_schedule(text) is True

    @pytest.mark.parametrize("text", [
        "搜索最近的深度学习论文",
        "find recent NLP papers",
        "检索近1年的机器学习论文",
    ])
    def test_not_detected(self, parser, text):
        assert parser._detect_schedule(text) is False


# --------------------------- 周期抽取 --------------------------- #

class TestExtractSchedule:
    @pytest.mark.parametrize("text,token", [
        ("每周一发送论文", "weekly"),
        ("每周发送", "weekly"),
        ("每个月报告", "monthly"),
        ("每月综述", "monthly"),
        ("每两周", "biweekly"),
        ("每天", "daily"),
        ("每日", "daily"),
        ("每3天", "every-3d"),
        ("every 5 days", "every-5d"),
        ("monthly", "monthly"),
        ("daily", "daily"),
        ("定时发送", "weekly"),       # 无明确周期 → 默认 weekly
    ])
    def test_token(self, parser, text, token):
        assert parser._extract_schedule(text) == token

    def test_no_schedule_returns_none(self, parser):
        assert parser._extract_schedule("搜索最近论文") is None

    def test_biweekly_before_weekly(self, parser):
        """「每两周」应判 biweekly 而非 weekly（特定先于通用）"""
        assert parser._extract_schedule("每两周发一次") == "biweekly"


# --------------------------- parse() 集成 --------------------------- #

class TestParseScheduled:
    def test_parse_sets_scheduled_fields(self, parser):
        intent = parser.parse("每周一发送 machine learning 论文")
        assert intent.is_scheduled is True
        assert intent.schedule == "weekly"

    def test_parse_non_scheduled(self, parser):
        intent = parser.parse("搜索最近的机器学习论文")
        assert intent.is_scheduled is False
        assert intent.schedule is None

    def test_scheduled_default_window_short(self, parser):
        """定时输入无显式「近N」→ 默认短窗口（≤31d），不是近3年"""
        intent = parser.parse("每周一发送 machine learning 论文")
        now = datetime.now()
        assert intent.start_date is not None
        # weekly → 7 天窗口
        span = now - intent.start_date
        assert timedelta(days=6) <= span <= timedelta(days=8)
        assert intent.is_scheduled

    def test_monthly_window(self, parser):
        intent = parser.parse("每个月发送 machine learning 报告")
        assert intent.schedule == "monthly"
        span = datetime.now() - intent.start_date
        assert timedelta(days=29) <= span <= timedelta(days=31)

    def test_scheduled_with_explicit_time_uses_explicit(self, parser):
        """定时输入 + 显式「近1年」→ 用显式时间（1年），不被定时短窗口覆盖"""
        intent = parser.parse("每周一发送近1年的 machine learning 论文")
        assert intent.is_scheduled is True
        span = datetime.now() - intent.start_date
        assert span > timedelta(days=300)   # 近1年，非短窗口


# --------------------------- 既有字段基线 --------------------------- #

class TestParseBaseline:
    def test_query_extracted(self, parser):
        intent = parser.parse("搜索 machine learning 论文")
        assert "machine learning" in intent.query.lower()

    def test_field_identified(self, parser):
        intent = parser.parse("搜索 machine learning 论文")
        assert intent.research_field == "machine_learning"

    def test_language_default_bilingual(self, parser):
        # 无中文时默认 bilingual
        intent = parser.parse("search machine learning papers")
        assert intent.language == "bilingual"

    def test_default_time_range_3y(self, parser):
        """非定时、无显式时间 → 近3年（既有行为）"""
        intent = parser.parse("search recent ml papers")
        assert intent.start_date is not None
        span = datetime.now() - intent.start_date
        assert span > timedelta(days=365 * 2)   # 约3年

    def test_explicit_time_range(self, parser):
        intent = parser.parse("检索近1个月的 machine learning 论文")
        span = datetime.now() - intent.start_date
        assert timedelta(days=25) <= span <= timedelta(days=35)

    def test_keywords_extracted(self, parser):
        intent = parser.parse("搜索 deep learning 论文")
        assert any("deep learning" in k.lower() for k in intent.keywords)
