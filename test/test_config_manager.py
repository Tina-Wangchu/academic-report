"""
测试 config_manager.py —— 重点是 ~/.hermes/.env 自动加载。
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-scholar', 'scripts'))

from config_manager import ConfigManager, get_config_manager


class TestLoadEnvFile:
    """测试 _load_env_file（~/.hermes/.env 自动加载）"""

    def test_loads_keys_from_env_file(self, monkeypatch, tmp_path):
        """.env 里的 KEY=VALUE 被加载进 os.environ"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            'AGENT_SCHOLAR_TEST_KEY=hello123\n'
            '# 这是注释\n'
            '\n'
            'AGENT_SCHOLAR_QUOTED="quoted_value"\n'
            "AGENT_SCHOLAR_SINGLE='single_value'\n",
            encoding="utf-8",
        )
        monkeypatch.delenv("AGENT_SCHOLAR_TEST_KEY", raising=False)
        monkeypatch.delenv("AGENT_SCHOLAR_QUOTED", raising=False)
        monkeypatch.delenv("AGENT_SCHOLAR_SINGLE", raising=False)

        cm = ConfigManager()
        cm.env_path = env_file
        cm._load_env_file()

        assert os.environ.get("AGENT_SCHOLAR_TEST_KEY") == "hello123"
        assert os.environ.get("AGENT_SCHOLAR_QUOTED") == "quoted_value"
        assert os.environ.get("AGENT_SCHOLAR_SINGLE") == "single_value"

    def test_does_not_override_existing_env(self, monkeypatch, tmp_path):
        """已存在的环境变量优先级高于 .env（不被覆盖）"""
        env_file = tmp_path / ".env"
        env_file.write_text("AGENT_SCHOLAR_OVERRIDE=from_file", encoding="utf-8")
        monkeypatch.setenv("AGENT_SCHOLAR_OVERRIDE", "from_env")

        cm = ConfigManager()
        cm.env_path = env_file
        cm._load_env_file()

        assert os.environ.get("AGENT_SCHOLAR_OVERRIDE") == "from_env"

    def test_missing_env_file_no_error(self, tmp_path):
        """.env 不存在时不报错"""
        cm = ConfigManager()
        cm.env_path = tmp_path / "nonexistent.env"
        cm._load_env_file()  # 应静默返回


class TestSmtpConfig:
    """测试 get_smtp_config / validate_smtp_config"""

    def test_smtp_config_returns_dict(self):
        cm = get_config_manager()
        cfg = cm.get_smtp_config()
        assert "host" in cfg and "port" in cfg
        assert "user" in cfg and "password" in cfg
        assert isinstance(cfg["port"], int)

    def test_validate_missing_user(self, monkeypatch):
        """无 SMTP_USER 时校验失败"""
        cm = get_config_manager()
        for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"):
            monkeypatch.delenv(k, raising=False)
        ok, msg = cm.validate_smtp_config()
        assert ok is False
        assert "SMTP" in msg or "用户名" in msg
