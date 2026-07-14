"""
测试 email_sender.py 模块（模块6）
用 FakeSMTP + FakeConfig 全程不联网；覆盖发送成功、SSL/TLS 分流、
配置/收件人/文件校验、认证错误不重试、瞬时错误重试、连接测试、邮件构建。
"""

import smtplib
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent-scholar', 'scripts'))

from email_sender import EmailSender


# ---------------------------------------------------------------------- #
# 夹具
# ---------------------------------------------------------------------- #

class FakeConfig:
    """可定假的配置管理器"""

    def __init__(self, valid=True, recipient="user@example.com",
                 host="smtp.example.com", port=587,
                 user="user@example.com", password="apppassword"):
        self._valid = valid
        self._recipient = recipient
        self._smtp = {"host": host, "port": port,
                      "user": user, "password": password}

    def validate_smtp_config(self):
        return (self._valid, "" if self._valid else "SMTP 配置无效")

    def get_smtp_config(self):
        return self._smtp

    def get_email_recipient(self):
        return self._recipient


class FakeSMTP:
    """记录调用的假 SMTP 服务器"""

    def __init__(self, host, port, timeout=None,
                 login_exc=None, send_excs=None):
        self.host, self.port, self.timeout = host, port, timeout
        self.starttls_called = False
        self.logged_in = False
        self.sent = []
        self.login_exc = login_exc
        # 共享引用：跨多次连接（重试）依次消费异常
        self.send_excs = send_excs if send_excs is not None else []

    def starttls(self):
        self.starttls_called = True

    def login(self, user, password):
        if self.login_exc:
            raise self.login_exc
        self.logged_in = True

    def send_message(self, msg):
        if self.send_excs:
            raise self.send_excs.pop(0)
        self.sent.append(msg)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def patch_smtp(monkeypatch, login_exc=None, send_excs=None):
    """把 email_sender 里的 smtplib.SMTP / SMTP_SSL 替换为 FakeSMTP 工厂，返回实例列表"""
    import email_sender
    fakes = []
    shared_send_excs = list(send_excs or [])  # 跨重试共享

    def factory(host, port, timeout=None):
        f = FakeSMTP(host, port, timeout,
                     login_exc=login_exc, send_excs=shared_send_excs)
        fakes.append(f)
        return f

    monkeypatch.setattr(email_sender.smtplib, "SMTP", factory)
    monkeypatch.setattr(email_sender.smtplib, "SMTP_SSL", factory)
    return fakes


def _write_report(tmp_path, name="report.md", content="# 报告\n内容"):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------- #
# 发送
# ---------------------------------------------------------------------- #

class TestSendReport:
    """测试 send_report"""

    def test_send_success_tls(self, monkeypatch, tmp_path):
        """587 端口：SMTP + STARTTLS，发送成功"""
        report = _write_report(tmp_path)
        fakes = patch_smtp(monkeypatch)
        sender = EmailSender(config_manager=FakeConfig(port=587),
                             max_retries=1, retry_delay=0)
        assert sender.send_report(str(report)) is True
        assert len(fakes) == 1
        assert fakes[0].starttls_called is True
        assert fakes[0].logged_in
        assert len(fakes[0].sent) == 1

    def test_send_success_ssl_465(self, monkeypatch, tmp_path):
        """465 端口：SMTP_SSL，不调用 STARTTLS"""
        report = _write_report(tmp_path)
        fakes = patch_smtp(monkeypatch)
        sender = EmailSender(config_manager=FakeConfig(port=465),
                             max_retries=1, retry_delay=0)
        assert sender.send_report(str(report)) is True
        assert fakes[0].starttls_called is False  # SSL 隐式加密，无需 starttls

    def test_invalid_config(self, tmp_path):
        sender = EmailSender(config_manager=FakeConfig(valid=False),
                             max_retries=1)
        assert sender.send_report(str(_write_report(tmp_path))) is False

    def test_no_recipient(self, tmp_path):
        sender = EmailSender(config_manager=FakeConfig(recipient=""),
                             max_retries=1)
        assert sender.send_report(str(_write_report(tmp_path))) is False

    def test_missing_file(self):
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1)
        assert sender.send_report("/nonexistent/report.md") is False

    def test_auth_error_no_retry(self, monkeypatch, tmp_path):
        """认证错误立即失败，不重试"""
        report = _write_report(tmp_path)
        exc = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        fakes = patch_smtp(monkeypatch, login_exc=exc)
        sender = EmailSender(config_manager=FakeConfig(),
                             max_retries=3, retry_delay=0)
        assert sender.send_report(str(report)) is False
        assert len(fakes) == 1  # 认证失败不重试

    def test_retry_then_success(self, monkeypatch, tmp_path):
        """瞬时 SMTPException 重试后成功"""
        report = _write_report(tmp_path)
        fakes = patch_smtp(monkeypatch,
                           send_excs=[smtplib.SMTPException("transient")])
        sender = EmailSender(config_manager=FakeConfig(),
                             max_retries=3, retry_delay=0)
        assert sender.send_report(str(report)) is True
        assert len(fakes) == 2  # 第一次抛错，第二次成功

    def test_retry_exhausted(self, monkeypatch, tmp_path):
        """持续失败 → 重试耗尽 → False"""
        report = _write_report(tmp_path)
        fakes = patch_smtp(monkeypatch,
                           send_excs=[smtplib.SMTPException("err")] * 5)
        sender = EmailSender(config_manager=FakeConfig(),
                             max_retries=3, retry_delay=0)
        assert sender.send_report(str(report)) is False
        assert len(fakes) == 3  # 重试 3 次

    def test_recipient_override(self, monkeypatch, tmp_path):
        """显式指定 recipient 优先于配置"""
        report = _write_report(tmp_path)
        fakes = patch_smtp(monkeypatch)
        sender = EmailSender(config_manager=FakeConfig(recipient="default@x.com"),
                             max_retries=1, retry_delay=0)
        sender.send_report(str(report), recipient="override@x.com")
        assert fakes[0].sent[0]["To"] == "override@x.com"


# ---------------------------------------------------------------------- #
# 连接测试
# ---------------------------------------------------------------------- #

class TestTestConnection:
    """测试 test_connection"""

    def test_connection_ok(self, monkeypatch):
        patch_smtp(monkeypatch)
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1)
        ok, msg = sender.test_connection()
        assert ok is True
        assert "成功" in msg or "OK" in msg

    def test_connection_fail(self, monkeypatch):
        exc = smtplib.SMTPException("connect failed")
        patch_smtp(monkeypatch, login_exc=exc)
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1)
        ok, msg = sender.test_connection()
        assert ok is False
        assert "失败" in msg or "failed" in msg

    def test_connection_invalid_config(self):
        sender = EmailSender(config_manager=FakeConfig(valid=False), max_retries=1)
        ok, msg = sender.test_connection()
        assert ok is False


# ---------------------------------------------------------------------- #
# 邮件构建
# ---------------------------------------------------------------------- #

class TestCreateEmail:
    """测试 _create_email"""

    def test_has_attachment_with_filename(self, tmp_path):
        report = _write_report(tmp_path, name="report.md")
        sender = EmailSender(config_manager=FakeConfig())
        msg = sender._create_email(report, "r@x.com", "s@x.com", None, "Markdown")
        # MIMEMultipart 用 walk() + get_content_disposition 找附件
        attachment_parts = [p for p in msg.walk()
                           if p.get_content_disposition() == "attachment"]
        assert len(attachment_parts) == 1
        assert attachment_parts[0].get_filename() == "report.md"

    def test_subject_default_has_date(self, tmp_path):
        report = _write_report(tmp_path)
        sender = EmailSender(config_manager=FakeConfig())
        msg = sender._create_email(report, "r@x.com", "s@x.com", None, "Markdown")
        assert "学术报告" in msg["Subject"] or "Academic" in msg["Subject"]

    def test_subject_override(self, tmp_path):
        report = _write_report(tmp_path)
        sender = EmailSender(config_manager=FakeConfig())
        msg = sender._create_email(report, "r@x.com", "s@x.com",
                                   "自定义主题", "Markdown")
        assert msg["Subject"] == "自定义主题"

    def test_body_contains_filename_and_format(self, tmp_path):
        report = _write_report(tmp_path, name="myreport.html")
        sender = EmailSender(config_manager=FakeConfig())
        msg = sender._create_email(report, "r@x.com", "s@x.com", None, "HTML")
        # 取 HTML 正文 part
        body = msg.get_payload()[0].get_payload(decode=True).decode("utf-8")
        assert "myreport.html" in body
        assert "HTML" in body


# ---------------------------------------------------------------------- #
# SSL/TLS 分流
# ---------------------------------------------------------------------- #

class TestPortRouting:
    """测试端口 → SSL/STARTTLS 分流"""

    def test_is_ssl_port(self):
        assert EmailSender._is_ssl_port(465) is True
        assert EmailSender._is_ssl_port(587) is False
        assert EmailSender._is_ssl_port(25) is False
