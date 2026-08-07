"""
测试 email_sender.py 模块（模块6）
用 FakeSMTP + FakeConfig 全程不联网；覆盖发送成功、SSL/TLS 分流、
配置/收件人/文件校验、认证错误不重试、瞬时错误重试、连接测试、邮件构建。
"""

import smtplib
import pytest
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'academic-report', 'scripts'))

import email_sender
from email_sender import EmailSender


@pytest.fixture(autouse=True)
def _isolate_send_state(tmp_path, monkeypatch):
    """所有用例把发送日志 + 冷却状态重定向到临时目录，绝不污染 ~/.hermes/。"""
    monkeypatch.setattr(email_sender, "DEFAULT_LOG_PATH", tmp_path / "test_sends.jsonl")
    monkeypatch.setattr(email_sender, "DEFAULT_COOLDOWN_PATH", tmp_path / "test_cooldown.json")
    monkeypatch.delenv("EMAIL_SKIP_COOLDOWN", raising=False)


def _set_cooldown(sender, user, consecutive, age_seconds=0):
    """直接写入冷却状态文件（供测试构造确定的冷却场景）。"""
    ts = (datetime.now().astimezone() - timedelta(seconds=age_seconds)).isoformat(timespec="seconds")
    Path(sender.cooldown_path).parent.mkdir(parents=True, exist_ok=True)
    Path(sender.cooldown_path).write_text(
        json.dumps({user: {"last_auth_fail_ts": ts,
                           "consecutive_auth_fails": consecutive}}),
        encoding="utf-8")


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
        report = _write_report(tmp_path, name="myreport.pdf")
        sender = EmailSender(config_manager=FakeConfig())
        msg = sender._create_email(report, "r@x.com", "s@x.com", None, "PDF")
        # 取 HTML 正文 part
        body = msg.get_payload()[0].get_payload(decode=True).decode("utf-8")
        assert "myreport.pdf" in body
        assert "PDF" in body

    def test_format_label_by_suffix(self):
        assert EmailSender._format_label(".md") == "Markdown"
        assert EmailSender._format_label(".pdf") == "PDF"
        assert EmailSender._format_label(".html") == "HTML"
        assert EmailSender._format_label("") == "HTML"


# ---------------------------------------------------------------------- #
# SSL/TLS 分流
# ---------------------------------------------------------------------- #

class TestPortRouting:
    """测试端口 → SSL/STARTTLS 分流"""

    def test_is_ssl_port(self):
        assert EmailSender._is_ssl_port(465) is True
        assert EmailSender._is_ssl_port(587) is False
        assert EmailSender._is_ssl_port(25) is False


# ---------------------------------------------------------------------- #
# 代理自动识别 + 直连/代理回退
# ---------------------------------------------------------------------- #

def _socks():
    """测试所需 pysocks；缺失则 skip（CI 无 pysocks 时跳过代理相关用例）。"""
    pytest.importorskip("socks")
    import socks
    return socks


class TestProxyDetection:
    """测试代理 URL 解析与环境变量自动发现"""

    def test_parse_schemes(self):
        socks = _socks()
        assert EmailSender._parse_proxy_url("socks5://127.0.0.1:7897", socks.SOCKS5, socks) \
            == (socks.SOCKS5, "127.0.0.1", 7897)
        assert EmailSender._parse_proxy_url("socks5h://10.0.0.1:1080", socks.SOCKS5, socks) \
            == (socks.SOCKS5, "10.0.0.1", 1080)
        assert EmailSender._parse_proxy_url("socks4://10.0.0.1:1080", socks.SOCKS5, socks)[0] \
            == socks.SOCKS4
        assert EmailSender._parse_proxy_url("http://127.0.0.1:7890", socks.SOCKS5, socks) \
            == (socks.HTTP, "127.0.0.1", 7890)

    def test_parse_bare_host_port(self):
        socks = _socks()
        assert EmailSender._parse_proxy_url("127.0.0.1:7897", socks.SOCKS5, socks) \
            == (socks.SOCKS5, "127.0.0.1", 7897)

    def test_parse_garbage_returns_none(self):
        socks = _socks()
        assert EmailSender._parse_proxy_url("garbage", socks.SOCKS5, socks) is None
        assert EmailSender._parse_proxy_url("socks5://host", socks.SOCKS5, socks) is None  # 无端口

    def test_detect_from_env(self, monkeypatch):
        socks = _socks()
        monkeypatch.setenv("SMTP_SOCKS_PROXY", "socks5://127.0.0.1:7897")
        monkeypatch.setenv("ALL_PROXY", "socks5://10.0.0.1:1080")
        monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:7890")
        proxies = EmailSender(config_manager=FakeConfig())._detect_proxies(socks)
        by_hp = {(h, p): t for (t, h, p) in proxies}
        assert ("127.0.0.1", 7897) in by_hp
        assert ("10.0.0.1", 1080) in by_hp
        assert by_hp[("127.0.0.1", 7890)] == socks.HTTP

    def test_detect_dedup(self, monkeypatch):
        socks = _socks()
        monkeypatch.setenv("SMTP_SOCKS_PROXY", "socks5://127.0.0.1:7897")
        monkeypatch.setenv("ALL_PROXY", "socks5://127.0.0.1:7897")  # 同一代理
        proxies = EmailSender(config_manager=FakeConfig())._detect_proxies(socks)
        assert len(proxies) == 1


class TestStrategyChain:
    """测试策略清单构造与直连→代理回退"""

    def test_direct_is_first_strategy(self):
        labels = [lbl for lbl, _ in
                  EmailSender(config_manager=FakeConfig())._build_strategies()]
        assert labels[0] == "direct"

    def test_env_proxy_added_after_direct(self, monkeypatch):
        _socks()
        monkeypatch.setenv("SMTP_SOCKS_PROXY", "socks5://127.0.0.1:7897")
        labels = [lbl for lbl, _ in
                  EmailSender(config_manager=FakeConfig())._build_strategies()]
        assert labels[0] == "direct"
        assert "socks5://127.0.0.1:7897" in labels
        # 兜底本地探测总在最后
        assert labels[-1] == "auto-local-socks"

    def test_fallback_when_direct_connect_fails(self, monkeypatch, tmp_path):
        """直连连接即失败 → 自动回退到代理策略并成功"""
        _socks()
        report = _write_report(tmp_path)
        import email_sender
        calls = {"n": 0}

        def factory(host, port, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("direct blocked (e.g. GFW)")  # 直连失败
            return FakeSMTP(host, port, timeout)             # 代理策略命中

        monkeypatch.setattr(email_sender.smtplib, "SMTP", factory)
        monkeypatch.setattr(email_sender.smtplib, "SMTP_SSL", factory)
        monkeypatch.setenv("SMTP_SOCKS_PROXY", "socks5://127.0.0.1:9999")
        sender = EmailSender(config_manager=FakeConfig(port=465),
                             max_retries=1, retry_delay=0)
        assert sender.send_report(str(report)) is True
        assert calls["n"] >= 2  # 直连失败后走了代理策略

    def test_direct_success_skips_proxy(self, monkeypatch, tmp_path):
        """直连成功时不触碰代理策略（只创建 1 个连接）"""
        _socks()
        report = _write_report(tmp_path)
        import email_sender
        calls = {"n": 0, "local_probe": False}

        def factory(host, port, timeout=None):
            calls["n"] += 1
            return FakeSMTP(host, port, timeout)

        monkeypatch.setattr(email_sender.smtplib, "SMTP", factory)
        monkeypatch.setattr(email_sender.smtplib, "SMTP_SSL", factory)
        # 让本地探测立即失败（证明它没被需要）
        def _no_probe(self, host, port):
            calls["local_probe"] = True
            raise ConnectionError("probe should not run when direct works")
        monkeypatch.setattr(EmailSender, "_connect_auto_local_socks", _no_probe)
        monkeypatch.setenv("SMTP_SOCKS_PROXY", "socks5://127.0.0.1:9999")
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1, retry_delay=0)
        assert sender.send_report(str(report)) is True
        assert calls["n"] == 1            # 只用了直连
        assert calls["local_probe"] is False


# ---------------------------------------------------------------------- #
# 本地 SOCKS 端口探测 —— 回归保护
# ---------------------------------------------------------------------- #

class TestAutoLocalSocksProbe:
    """
    回归保护：_connect_auto_local_socks 的端口探测必须用模块级
    _REAL_CREATE_CONNECTION，而不是 _REAL_SOCKET.create_connection
    （socket 类上没有 create_connection，它是 socket 模块的函数）。
    旧代码误用 _REAL_SOCKET.create_connection 导致直连失败时回退崩溃：
      AttributeError: type object 'socket' has no attribute 'create_connection'
    """

    def test_real_socket_class_has_no_create_connection(self):
        """不变量：_REAL_SOCKET 是 socket 类，其上无 create_connection；
        _REAL_CREATE_CONNECTION 才是可调用的模块函数。"""
        import email_sender
        # _REAL_SOCKET 是类（type），不是模块
        assert isinstance(email_sender._REAL_SOCKET, type)
        assert not hasattr(email_sender._REAL_SOCKET, "create_connection")
        # 模块级 create_connection 才存在且可调用
        assert callable(email_sender._REAL_CREATE_CONNECTION)

    def test_probe_uses_module_create_connection(self, monkeypatch):
        """探测经 _REAL_CREATE_CONNECTION；即使 _REAL_SOCKET 故意没有
        create_connection 也不报 AttributeError（旧 bug 会在此崩溃）。"""
        _socks()  # _connect_auto_local_socks 需要 pysocks
        import email_sender

        open_port = 19999
        # 只探测一个端口，保证确定性
        monkeypatch.setattr(email_sender, "_LOCAL_SOCKS_PORTS", (open_port,))

        # 模块级 create_connection：对 open_port 返回可关闭的假 socket
        probed = {"called": False}

        class _FakeSock:
            def close(self):
                pass

        def _fake_create_connection(addr, timeout=None):
            probed["called"] = True
            if addr[1] == open_port:
                return _FakeSock()
            raise OSError("no listener")

        monkeypatch.setattr(email_sender, "_REAL_CREATE_CONNECTION",
                            _fake_create_connection)

        # 故意把 _REAL_SOCKET 换成「没有 create_connection」的对象 ——
        # 若代码误用 _REAL_SOCKET.create_connection，这里会 AttributeError
        class _SentinelNoCC:
            pass
        monkeypatch.setattr(email_sender, "_REAL_SOCKET", _SentinelNoCC)

        # _connect_socks 命中后返回假服务器（无需真实 SOCKS 握手）
        socks_args = {}

        def _fake_connect_socks(self, host, port, proxy):
            socks_args["proxy"] = proxy
            return FakeSMTP(host, port)

        monkeypatch.setattr(EmailSender, "_connect_socks", _fake_connect_socks)

        sender = EmailSender(config_manager=FakeConfig())
        server = sender._connect_auto_local_socks("smtp.qq.com", 465)

        # 探测确实走了模块级 create_connection
        assert probed["called"] is True
        # 且把探测到的端口作为 SOCKS5 本地代理传给 _connect_socks
        assert socks_args["proxy"][0] == _socks().SOCKS5
        assert socks_args["proxy"][1] == "127.0.0.1"
        assert socks_args["proxy"][2] == open_port
        assert isinstance(server, FakeSMTP)

    def test_probe_skips_closed_ports(self, monkeypatch):
        """所有端口都无人监听 → 抛 ConnectionError，而非 AttributeError。"""
        _socks()
        import email_sender
        monkeypatch.setattr(email_sender, "_LOCAL_SOCKS_PORTS", (20001, 20002))

        def _all_closed(addr, timeout=None):
            raise OSError("refused")
        monkeypatch.setattr(email_sender, "_REAL_CREATE_CONNECTION", _all_closed)

        sender = EmailSender(config_manager=FakeConfig())
        with pytest.raises(ConnectionError):
            sender._connect_auto_local_socks("smtp.qq.com", 465)


# ---------------------------------------------------------------------- #
# 发送记录持久化日志（JSONL append-only）
# ---------------------------------------------------------------------- #

class TestSendLog:
    """测试 _append_send_log：成功/失败都落一条；best-effort 不影响发送结果。"""

    def test_log_appended_on_success(self, monkeypatch, tmp_path):
        """发送成功 → 日志追加一条 status=success 的记录，含策略/收件人/报告名。"""
        report = _write_report(tmp_path, name="cv_report.md")
        patch_smtp(monkeypatch)
        log_file = tmp_path / "sends.jsonl"
        sender = EmailSender(config_manager=FakeConfig(),
                             max_retries=1, retry_delay=0,
                             log_path=str(log_file))
        assert sender.send_report(str(report), recipient="to@x.com",
                                  subject="测试主题") is True

        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        rec = json.loads(lines[0])
        assert rec["status"] if "status" in rec else rec["success"] is True
        assert rec["success"] is True
        assert rec["strategy"] == "direct"          # FakeConfig 默认 587 → direct 命中
        assert rec["attempts"] == 1
        assert rec["recipient"] == "to@x.com"
        assert rec["subject"] == "测试主题"
        assert rec["report"] == "cv_report.md"
        assert rec["error"] is None
        assert "ts" in rec                           # 带时间戳

    def test_log_appended_on_failure(self, monkeypatch, tmp_path):
        """发送失败（瞬时错误重试耗尽）→ 日志追加一条 success=false + error。"""
        report = _write_report(tmp_path)
        patch_smtp(monkeypatch,
                   send_excs=[smtplib.SMTPException("Connection unexpectedly closed")] * 5)
        log_file = tmp_path / "sends.jsonl"
        sender = EmailSender(config_manager=FakeConfig(),
                             max_retries=3, retry_delay=0,
                             log_path=str(log_file))
        assert sender.send_report(str(report)) is False

        rec = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert rec["success"] is False
        assert rec["attempts"] == 3
        assert "Connection unexpectedly closed" in rec["error"]
        assert rec["error_type"] == "SMTPException"

    def test_log_auth_failure_recorded(self, monkeypatch, tmp_path):
        """认证失败也落一条，error_type=auth，attempts=1（认证错误不重试）。"""
        report = _write_report(tmp_path)
        patch_smtp(monkeypatch,
                   login_exc=smtplib.SMTPAuthenticationError(535, b"Login fail"))
        log_file = tmp_path / "sends.jsonl"
        sender = EmailSender(config_manager=FakeConfig(),
                             max_retries=3, retry_delay=0,
                             log_path=str(log_file))
        assert sender.send_report(str(report)) is False

        rec = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert rec["success"] is False
        assert rec["error_type"] == "auth"
        assert rec["attempts"] == 1

    def test_log_write_failure_never_breaks_send(self, monkeypatch, tmp_path):
        """日志路径不可写时，发送仍成功，异常不外泄（best-effort）。"""
        report = _write_report(tmp_path)
        patch_smtp(monkeypatch)
        # log_path 指向一个「已存在的目录」（open 会失败）—— 模拟写入异常
        sender = EmailSender(config_manager=FakeConfig(),
                             max_retries=1, retry_delay=0,
                             log_path=str(tmp_path))  # tmp_path 是目录，open(a) 失败
        # 发送不应因日志失败而抛错或返回 False
        assert sender.send_report(str(report)) is True

    def test_log_uses_default_path_when_none(self, tmp_path):
        """未传 log_path → 用 DEFAULT_LOG_PATH（被 autouse fixture 重定向到 tmp）。"""
        sender = EmailSender(config_manager=FakeConfig())
        assert sender.log_path == email_sender.DEFAULT_LOG_PATH


# ---------------------------------------------------------------------- #
# 冷却守卫（auth 失败指数退避，跨进程；防止 agent 重跑轰炸 QQ 限频）
# ---------------------------------------------------------------------- #

class TestCooldown:
    """测试冷却守卫：认证失败后退避，成功清零，可强制跳过。"""

    def test_no_cooldown_initially(self, monkeypatch, tmp_path):
        """无失败记录 → 冷却 0，可正常发送。"""
        patch_smtp(monkeypatch)
        report = _write_report(tmp_path)
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1, retry_delay=0)
        assert sender._cooldown_remaining("user@example.com") == 0.0
        assert sender.send_report(str(report)) is True

    def test_auth_failure_triggers_cooldown_and_blocks_next(self, monkeypatch, tmp_path):
        """认证失败后：本次返回 False 并记冷却；紧接着的第二次发送被拦截、不再登录 QQ。"""
        report = _write_report(tmp_path)
        exc = smtplib.SMTPAuthenticationError(535, b"Login fail")
        fakes = patch_smtp(monkeypatch, login_exc=exc)
        sender = EmailSender(config_manager=FakeConfig(), max_retries=3, retry_delay=0)

        # 第 1 次：认证失败（触发冷却，连续=1 → 冷却 30s）
        assert sender.send_report(str(report)) is False
        assert len(fakes) == 1                       # 只尝试 1 次登录（认证错不重试）
        assert sender._cooldown_remaining("user@example.com") > 0   # 进入冷却

        # 第 2 次：被冷却拦截，不再创建 SMTP 连接（不登录 QQ）
        assert sender.send_report(str(report)) is False
        assert len(fakes) == 1                       # 关键：没有第 2 次登录

    def test_cooldown_escalates_exponentially(self, monkeypatch, tmp_path):
        """连续失败次数越多，冷却越久：1→30s，2→60s，3→120s，上限 300s。"""
        patch_smtp(monkeypatch)  # 不会真的发，只读冷却状态
        sender = EmailSender(config_manager=FakeConfig())
        for n, expect in [(1, 30), (2, 60), (3, 120), (4, 240), (5, 300), (9, 300)]:
            _set_cooldown(sender, "user@example.com", consecutive=n, age_seconds=0)
            rem = sender._cooldown_remaining("user@example.com")
            # 刚记录，剩余≈满额；留 6s 容差吸收「写文件→读文件」I/O 耗时
            assert expect - 6 <= rem <= expect, f"n={n} expect~{expect} got {rem}"

    def test_cooldown_expires(self, monkeypatch, tmp_path):
        """冷却时间过后 → 剩余 0，可重新发送。"""
        patch_smtp(monkeypatch)
        report = _write_report(tmp_path)
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1, retry_delay=0)
        _set_cooldown(sender, "user@example.com", consecutive=1, age_seconds=31)  # 30s 冷却已过
        assert sender._cooldown_remaining("user@example.com") == 0.0
        assert sender.send_report(str(report)) is True   # 冷却已过，正常发

    def test_success_clears_cooldown(self, monkeypatch, tmp_path):
        """冷却中但已过期、且本次发送成功 → 清零冷却状态。"""
        patch_smtp(monkeypatch)
        report = _write_report(tmp_path)
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1, retry_delay=0)
        _set_cooldown(sender, "user@example.com", consecutive=3, age_seconds=999)  # 早已过期
        assert sender.send_report(str(report)) is True
        # 成功后状态清零
        state = sender._load_cooldown_state()
        assert state["user@example.com"]["consecutive_auth_fails"] == 0

    def test_skip_cooldown_env_bypasses(self, monkeypatch, tmp_path):
        """EMAIL_SKIP_COOLDOWN=1 → 即使在冷却中也强制发送（手动/调试用）。"""
        patch_smtp(monkeypatch)
        report = _write_report(tmp_path)
        monkeypatch.setenv("EMAIL_SKIP_COOLDOWN", "1")
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1, retry_delay=0)
        _set_cooldown(sender, "user@example.com", consecutive=5, age_seconds=0)  # 满冷却中
        assert sender._cooldown_remaining("user@example.com") == 0.0  # 被环境变量跳过
        assert sender.send_report(str(report)) is True

    def test_non_auth_failure_does_not_trigger_cooldown(self, monkeypatch, tmp_path):
        """非认证错误（如 SMTPServerDisconnected 网络瞬时）不计入冷却——只有 auth 才退避。"""
        report = _write_report(tmp_path)
        patch_smtp(monkeypatch,
                   send_excs=[smtplib.SMTPServerDisconnected("Connection unexpectedly closed")] * 5)
        sender = EmailSender(config_manager=FakeConfig(), max_retries=3, retry_delay=0)
        assert sender.send_report(str(report)) is False
        # 网络错误不触发冷却 → 下次仍可立即重试
        assert sender._cooldown_remaining("user@example.com") == 0.0

    def test_cooldown_writes_log_entry(self, monkeypatch, tmp_path, capsys):
        """被冷却拦截时：写一条 error_type=cooldown 的日志，且 stdout 有提示。"""
        report = _write_report(tmp_path)
        patch_smtp(monkeypatch)
        log_file = tmp_path / "cd_sends.jsonl"
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1, retry_delay=0,
                             log_path=str(log_file))
        _set_cooldown(sender, "user@example.com", consecutive=2, age_seconds=0)  # 冷却 60s
        assert sender.send_report(str(report)) is False
        rec = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert rec["error_type"] == "cooldown"
        assert rec["success"] is False
        out = capsys.readouterr().out
        assert "冷却" in out and "EMAIL_SKIP_COOLDOWN" in out   # 提示用户如何强制

    def test_cooldown_print_failure_doesnt_crash(self, monkeypatch, tmp_path):
        """print 抛异常（如 GBK 控制台遇 emoji）时，冷却逻辑仍正常返回 False，不向上抛。"""
        import builtins
        report = _write_report(tmp_path)
        patch_smtp(monkeypatch)
        sender = EmailSender(config_manager=FakeConfig(), max_retries=1, retry_delay=0)
        _set_cooldown(sender, "user@example.com", consecutive=2, age_seconds=0)

        def _boom(*a, **k):
            raise UnicodeEncodeError("gbk", "x", 0, 1, "illegal multibyte")
        monkeypatch.setattr(builtins, "print", _boom)
        # 不应抛异常 —— 冷却仍优雅返回 False
        assert sender.send_report(str(report)) is False
