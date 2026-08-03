"""
测试 intent_parser.py
覆盖：parse() 的既有字段（query / field / language / time_range / filters）基线。
周期/定时功能已移除，不再纳入测试。
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


# --------------------------- 既有字段基线 --------------------------- #

class TestParseBaseline:
    def test_query_extracted(self, parser):
        intent = parser.parse("搜索 machine learning 论文")
        assert "machine learning" in intent.query.lower()

    def test_field_identified(self, parser):
        intent = parser.parse("搜索 machine learning 论文")
        assert intent.research_field == "machine_learning"

    def test_language_default_bilingual(self, parser):
        # 无中文时默认 bilingual（来自 .env DEFAULT_LANGUAGE，缺省 bilingual）
        intent = parser.parse("search machine learning papers")
        assert intent.language == "bilingual"

    def test_default_time_range_3y(self, parser):
        """无显式时间 → 默认时间范围（.env DEFAULT_TIME_RANGE，缺省 3y）"""
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
