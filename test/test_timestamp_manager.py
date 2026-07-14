"""
测试 timestamp_manager.py（定时/增量报告模块7）
覆盖：topic_key 确定性/防碰撞、防御加载（缺失/损坏）、读写 round-trip、原子写、建缺失目录。
不联网，用 tmp_path 注入文件路径。
"""

import json
import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-scholar', 'scripts'))

from timestamp_manager import TimestampManager


class TestTopicKey:
    def test_deterministic(self):
        """相同输入 → 相同 key"""
        a = TimestampManager.topic_key("machine learning", "machine_learning")
        b = TimestampManager.topic_key("machine learning", "machine_learning")
        assert a == b
        assert a  # 非空

    def test_different_field_different_key(self):
        a = TimestampManager.topic_key("transformer", "nlp")
        b = TimestampManager.topic_key("transformer", "cv")
        assert a != b

    def test_different_query_different_key(self):
        a = TimestampManager.topic_key("diffusion", "cv")
        b = TimestampManager.topic_key("gan", "cv")
        assert a != b

    def test_collision_safe_has_hash(self):
        """key 含 hash 段，防碰撞"""
        k = TimestampManager.topic_key("machine learning", "ml")
        assert "_" in k  # readable_hash 结构


class TestLoad:
    def test_missing_file_returns_empty(self, tmp_path):
        tm = TimestampManager(file_path=tmp_path / "nope.json")
        assert tm._load() == {}
        assert tm.get_last_run("any") is None

    def test_corrupt_json_returns_empty(self, tmp_path):
        fp = tmp_path / "ts.json"
        fp.write_text("{ not valid json ", encoding="utf-8")
        tm = TimestampManager(file_path=fp)
        assert tm._load() == {}          # 不抛异常
        assert tm.get_last_run("any") is None

    def test_non_dict_returns_empty(self, tmp_path):
        fp = tmp_path / "ts.json"
        fp.write_text(json.dumps(["a", "b", "c"]), encoding="utf-8")  # list 非 dict
        tm = TimestampManager(file_path=fp)
        assert tm._load() == {}

    def test_invalid_iso_returns_none(self, tmp_path):
        fp = tmp_path / "ts.json"
        fp.write_text(json.dumps({"k": "not-a-date"}), encoding="utf-8")
        tm = TimestampManager(file_path=fp)
        assert tm.get_last_run("k") is None


class TestRoundTrip:
    def test_update_then_get(self, tmp_path):
        tm = TimestampManager(file_path=tmp_path / "ts.json")
        key = TimestampManager.topic_key("ml", "machine_learning")
        when = datetime(2026, 7, 13, 9, 0, 0)
        tm.update_last_run(key, when=when)
        assert tm.get_last_run(key) == when

    def test_update_defaults_to_now(self, tmp_path):
        tm = TimestampManager(file_path=tmp_path / "ts.json")
        before = datetime.now()
        written = tm.update_last_run("k")
        after = datetime.now()
        assert before <= written <= after
        assert tm.get_last_run("k") == written

    def test_update_overwrites(self, tmp_path):
        tm = TimestampManager(file_path=tmp_path / "ts.json")
        t1 = datetime(2026, 1, 1)
        t2 = datetime(2026, 7, 13)
        tm.update_last_run("k", when=t1)
        tm.update_last_run("k", when=t2)
        assert tm.get_last_run("k") == t2

    def test_multiple_topics_independent(self, tmp_path):
        tm = TimestampManager(file_path=tmp_path / "ts.json")
        tm.update_last_run("k1", when=datetime(2026, 1, 1))
        tm.update_last_run("k2", when=datetime(2026, 2, 2))
        assert tm.get_last_run("k1") == datetime(2026, 1, 1)
        assert tm.get_last_run("k2") == datetime(2026, 2, 2)


class TestAtomicWrite:
    def test_no_tmp_leftover(self, tmp_path):
        tm = TimestampManager(file_path=tmp_path / "ts.json")
        tm.update_last_run("k", when=datetime(2026, 7, 13))
        # 不应残留 .tmp 文件
        leftovers = list(tmp_path.glob("*.tmp"))
        assert leftovers == []

    def test_preserves_other_keys(self, tmp_path):
        """原子写不应丢失既有键"""
        fp = tmp_path / "ts.json"
        fp.write_text(json.dumps({"existing": "2026-01-01T00:00:00"}),
                      encoding="utf-8")
        tm = TimestampManager(file_path=fp)
        tm.update_last_run("new", when=datetime(2026, 7, 13))
        assert tm.get_last_run("existing") == datetime(2026, 1, 1)
        assert tm.get_last_run("new") == datetime(2026, 7, 13)

    def test_creates_missing_dir(self, tmp_path):
        """目标目录不存在时应自动创建"""
        fp = tmp_path / "nested" / "deep" / "ts.json"
        tm = TimestampManager(file_path=fp)
        tm.update_last_run("k", when=datetime(2026, 7, 13))
        assert fp.exists()
        assert tm.get_last_run("k") == datetime(2026, 7, 13)
