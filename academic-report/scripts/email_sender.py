"""
邮件发送模块（模块6 / Module 6）

通过 SMTP 把生成的学术报告作为附件发送到用户邮箱。

连接策略 —— 自动识别代理，开/关代理都能发：
  按序尝试，命中即用，全失败才报错：
    1. direct            —— 重置 pysocks 全局包装，纯直连（国内 QQ/163 首选，最快）
    2. 环境变量代理       —— 自动解析 SMTP_SOCKS_PROXY / ALL_PROXY / HTTPS_PROXY
                            （直连被墙时，如国内直连 Gmail 必败 → 经代理回退）
    3. 本地 SOCKS 端口探测 —— 懒探测 127.0.0.1:{7897,7890,1080,...}（Clash 等本地代理）
  认证错误与代理无关，任一策略命中即立刻判定（不重试）。

- 配置来自 config_manager（SMTP_HOST/PORT/USER/PASSWORD 取自 config/.env；
  收件人取自 config.email_recipient，缺省回退到 SMTP_USER）。
- 端口 465 → SMTP_SSL（隐式 SSL）；端口 587/其它 → SMTP + STARTTLS。
- 发送失败（非认证错误）按指数退避重试，认证错误立即失败。
- 提供 test_connection() 与 --test CLI 便于排查。
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import socket as _socket_module
import sys
import time
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path
from typing import List, Optional, Tuple

from config_manager import get_config_manager
from utils import get_skill_data_dir

logger = logging.getLogger(__name__)

# 在任何 pysocks monkeypatch 之前，捕获真实 socket.create_connection / socket.socket，
# 供 _reset_socket_to_direct() 一键还原（直连策略必须用真 socket，不走任何代理）。
_REAL_SOCKET = _socket_module.socket
_REAL_CREATE_CONNECTION = _socket_module.create_connection

# pysocks 代理类型 → 可读名称（仅用于日志/策略标签）
_PTYPE_NAME = {1: "socks4", 2: "socks5", 3: "http"}

# 本地常见 SOCKS 代理端口（Clash/V2Ray 等），用于兜底探测
_LOCAL_SOCKS_PORTS = (7897, 7890, 1080, 10808, 10809)

# 运行期数据目录（唯一路径：academic-report/config/，与 .env 同目录）。
# 发送日志、冷却状态、LLM 缓存等运行期文件统一存放于此。
_DATA_DIR = get_skill_data_dir()

# 发送记录持久化日志（append-only JSONL）：每次发送尝试（成功/失败）追加一行，便于排查。
# 采用 JSONL（每行一条独立 JSON）而非单个 JSON 数组——append-only、crash-safe（崩溃不会撕裂整文件）、
# 无读-改-写竞争。写入失败仅告警，绝不影响发送结果。
DEFAULT_LOG_PATH = _DATA_DIR / "email_sends.jsonl"

# 冷却守卫状态文件：记录每个 SMTP 账号的「上次认证失败时间 + 连续失败次数」。
# 用途：认证失败（含 QQ 登录限频的假性 535）后，强制指数退避冷却，防止 agent 反复重跑
# → 轰炸 QQ → 触发/加深限频的死循环。跨进程持久（agent 每次重跑 pipeline 是新进程）。
DEFAULT_COOLDOWN_PATH = _DATA_DIR / "email_send_cooldown.json"
_COOLDOWN_BASE_SEC = 30.0   # 第 1 次失败冷却 30s
_COOLDOWN_MAX_SEC = 300.0   # 上限 5 分钟


def _import_socks():
    """惰性导入 pysocks；缺失返回 None（此时仅保留直连策略）。"""
    try:
        import socks  # noqa
        return socks
    except ImportError:
        return None


class EmailSender:
    """SMTP 邮件发送器（自动识别代理，直连/代理回退）"""

    def __init__(self, config_manager=None, max_retries: int = 3,
                 retry_delay: float = 5.0, timeout: int = 30,
                 log_path: Optional[str] = None,
                 cooldown_path: Optional[str] = None):
        """
        Args:
            config_manager: 配置管理器（默认全局实例；测试可注入）
            max_retries:    最大重试次数（认证错误不重试）
            retry_delay:    重试间隔秒数
            timeout:        SMTP 连接超时
            log_path:       发送记录日志路径（默认 <数据目录>/email_sends.jsonl）
            cooldown_path:  冷却守卫状态路径（默认 <数据目录>/email_send_cooldown.json）
        """
        self.config_manager = config_manager or get_config_manager()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.log_path = Path(log_path) if log_path else DEFAULT_LOG_PATH
        self.cooldown_path = Path(cooldown_path) if cooldown_path else DEFAULT_COOLDOWN_PATH

    # ----------------------------- 公共入口 ---------------------------- #

    def send_report(self, report_path: str, recipient: Optional[str] = None,
                    subject: Optional[str] = None) -> bool:
        """
        发送报告邮件（附件 + HTML 正文）。

        Args:
            report_path: 报告文件路径（.md / .html）
            recipient:   收件人（可选，默认用 config 的 email_recipient）
            subject:     邮件主题（可选）

        Returns:
            是否发送成功
        """
        # 1. 校验 SMTP 配置
        is_valid, error_msg = self.config_manager.validate_smtp_config()
        if not is_valid:
            logger.error("SMTP 配置无效: %s", error_msg)
            return False

        smtp_config = self.config_manager.get_smtp_config()

        # 2. 收件人
        if not recipient:
            recipient = self.config_manager.get_email_recipient()
        if not recipient:
            logger.error("未指定收件人邮箱")
            return False

        # 3. 报告文件
        report_file = Path(report_path)
        if not report_file.exists():
            logger.error("报告文件不存在: %s", report_path)
            return False

        file_format = "Markdown" if report_file.suffix == ".md" else "HTML"

        user = smtp_config["user"]

        # 冷却守卫：距上次认证失败不足冷却窗口 → 拒发，防止反复登录轰炸 QQ 触发/加深限频螺旋。
        # 认证失败（含 QQ 登录限频的假性 535）后指数退避：30s→60s→120s…上限 5 分钟。
        remaining = self._cooldown_remaining(user)
        if remaining > 0:
            # 纯 ASCII + 中文（GBK 控制台可编码），避免 emoji 导致 print 崩溃；
            # print 再套 try/except，确保任何控制台编码异常都不影响冷却逻辑。
            notice = (
                f"\n[email_sender] 发送冷却中 (cooldown): 距上次 SMTP 认证失败需再等 {int(remaining)} 秒。\n"
                f"   连续认证失败（含 QQ 登录限频造成的假性 535）触发指数退避: 30s/60s/120s... 上限 300s。\n"
                f"   本次未发送，避免反复登录轰炸 QQ 导致限频死循环。\n"
                f"   请等待冷却结束再重试，不要反复重跑 pipeline。\n"
                f"   手动强制发送可设环境变量 EMAIL_SKIP_COOLDOWN=1。\n"
            )
            logger.warning("发送冷却中：user=%s 还需 %ds（认证失败退避）", user, int(remaining))
            try:
                print(notice)
            except Exception:
                pass  # 控制台编码（如 GBK）异常不应影响冷却逻辑
            self._append_send_log({
                "recipient": recipient, "subject": subject,
                "report": report_file.name,
                "success": False, "strategy": None, "attempts": 0,
                "error": f"cooldown: {int(remaining)}s remaining",
                "error_type": "cooldown",
            })
            return False

        msg = None
        try:
            msg = self._create_email(report_file, recipient, user, subject, file_format)
            result = self._send_email(msg, smtp_config)
        except Exception as e:
            logger.error("发送邮件失败: %s", e)
            result = {
                "success": False, "strategy": None, "attempts": 0,
                "error": f"{type(e).__name__}: {e}",
                "error_type": type(e).__name__,
            }

        # 冷却状态更新：成功→清零；认证失败→计数+1（触发下次指数退避）；其它错误不动冷却状态
        if result["success"]:
            self._record_send_success(user)
        elif result.get("error_type") == "auth":
            self._record_auth_failure(user)

        # 持久化发送记录（成功/失败都记一条；best-effort，绝不影响发送结果）
        self._append_send_log({
            "recipient": recipient,
            "subject": msg["Subject"] if msg is not None else subject,
            "report": report_file.name,
            **result,
        })
        return result["success"]

    def test_connection(self) -> Tuple[bool, str]:
        """测试 SMTP 连接与认证（不发送邮件）；自动遍历直连+代理策略"""
        is_valid, error_msg = self.config_manager.validate_smtp_config()
        if not is_valid:
            return False, error_msg

        smtp_config = self.config_manager.get_smtp_config()
        try:
            server, label = self._open_and_login(smtp_config)
            with server:  # 关闭连接
                pass
            return True, (f"SMTP 连接测试成功 [策略={label}] / "
                          f"SMTP connection OK [{label}]")
        except smtplib.SMTPAuthenticationError as e:
            return False, f"SMTP 认证失败 / SMTP auth failed: {e}"
        except Exception as e:
            return False, (f"SMTP 连接测试失败（已尝试直连+代理回退）/ "
                           f"SMTP connection failed: {e}")

    # ----------------------------- 邮件构建 ---------------------------- #

    def _create_email(self, report_file: Path, recipient: str,
                      sender: str, subject: Optional[str],
                      file_format: str) -> MIMEMultipart:
        """构建邮件对象（HTML 正文 + 报告附件）"""
        msg = MIMEMultipart()
        msg["From"] = formataddr(("Academic Report", sender))
        msg["To"] = recipient

        if not subject:
            date_str = datetime.fromtimestamp(
                report_file.stat().st_mtime).strftime("%Y-%m-%d")
            subject = f"学术报告 / Academic Report - {date_str}"
        msg["Subject"] = subject

        body = self._render_body(report_file, file_format)
        msg.attach(MIMEText(body, "html", "utf-8"))

        # 附件
        with open(report_file, "rb") as f:
            part = MIMEApplication(f.read())
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=report_file.name,
        )
        msg.attach(part)
        return msg

    @staticmethod
    def _render_body(report_file: Path, file_format: str) -> str:
        """HTML 邮件正文"""
        year = datetime.now().year
        return f"""<html><head><meta charset="utf-8"><style>
body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
.container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
.header {{ background: #3498db; color: #fff; padding: 20px; text-align: center;
           border-radius: 5px 5px 0 0; }}
.content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
.footer {{ text-align: center; margin-top: 20px; color: #7f8c8d; font-size: 0.9em; }}
</style></head><body>
<div class="container">
  <div class="header"><h2>🎓 学术报告 / Academic Report</h2></div>
  <div class="content">
    <p>您好！/ Hello!</p>
    <p>最新的学术研究报告已生成完成，请查收附件。<br>
       The latest academic research report is attached.</p>
    <p><strong>报告格式 / Format:</strong> {file_format}<br>
       <strong>文件名 / File:</strong> {report_file.name}</p>
    <p>本报告由 Academic Report 自动生成。<br>
       Generated by Academic Report.</p>
  </div>
  <div class="footer">
    <p>如有问题，请回复此邮件。/ Reply to this email for any questions.</p>
    <p>© {year} Academic Report</p>
  </div>
</div></body></html>"""

    # ----------------------------- 发送（策略回退）--------------------- #

    def _send_email(self, msg: MIMEMultipart, smtp_config: dict) -> dict:
        """
        带重试 + 策略回退的发送：
        每轮内 _open_and_login 已穷尽「直连→代理」；非认证错误才进入下一轮重试。

        Returns:
            dict{success, strategy, attempts, error, error_type} —— 供 send_report 落日志。
        """
        last_strategy: Optional[str] = None
        last_err: Optional[str] = None
        last_err_type: Optional[str] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                server, label = self._open_and_login(smtp_config)
                last_strategy = label
                with server:
                    server.send_message(msg)
                logger.info("邮件发送成功 [策略=%s]", label)
                return {"success": True, "strategy": label, "attempts": attempt,
                        "error": None, "error_type": None}
            except smtplib.SMTPAuthenticationError as e:
                # 认证错误与代理无关，重试/换策略都没意义
                logger.error("SMTP 认证失败（与代理无关，不重试）: %s", e)
                return {"success": False, "strategy": last_strategy,
                        "attempts": attempt,
                        "error": f"SMTPAuthenticationError: {e}",
                        "error_type": "auth"}
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
                last_err_type = type(e).__name__
                logger.error("发送失败 (第 %d/%d 轮，已穷尽直连+代理策略): %s",
                             attempt, self.max_retries, e)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
        logger.error("达到最大重试次数，发送失败")
        return {"success": False, "strategy": last_strategy,
                "attempts": self.max_retries,
                "error": last_err, "error_type": last_err_type or "unknown"}

    def _append_send_log(self, entry: dict) -> None:
        """
        追加一条发送记录到 JSONL 日志（best-effort）。
        每行一条独立 JSON —— append-only、crash-safe、无读-改-写竞争。
        任何写入异常仅记 warning，绝不向上抛出（绝不影响发送结果）。
        """
        try:
            record = {"ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                      **entry}
            log_path = Path(self.log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning("写入发送日志失败（不影响发送结果）: %s", e)

    # ----------------------------- 冷却守卫 ---------------------------- #

    def _load_cooldown_state(self) -> dict:
        """读取冷却状态 {smtp_user: {last_auth_fail_ts, consecutive_auth_fails}}。防御加载。"""
        try:
            p = Path(self.cooldown_path)
            if not p.exists():
                return {}
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_cooldown_state(self, state: dict) -> None:
        """原子写冷却状态（tmp + os.replace，防撕裂）。失败仅告警，绝不影响发送。"""
        try:
            p = Path(self.cooldown_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(p.suffix + ".tmp")
            tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, p)
        except Exception as e:
            logger.warning("写入冷却状态失败（不影响发送）: %s", e)

    def _cooldown_remaining(self, user: str) -> float:
        """
        该 user 还需冷却多少秒；0 表示可发。
        冷却时长 = min(30 * 2^(连续失败次数-1), 300)。EMAIL_SKIP_COOLDOWN=1 可强制跳过。
        """
        if os.environ.get("EMAIL_SKIP_COOLDOWN"):
            return 0.0
        entry = self._load_cooldown_state().get(user)
        if not entry:
            return 0.0
        last = entry.get("last_auth_fail_ts")
        n = int(entry.get("consecutive_auth_fails", 0))
        if n <= 0 or not last:
            return 0.0
        try:
            last_dt = datetime.fromisoformat(last)
        except Exception:
            return 0.0
        now = datetime.now(last_dt.tzinfo) if last_dt.tzinfo else datetime.now()
        elapsed = (now - last_dt).total_seconds()
        required = min(_COOLDOWN_BASE_SEC * (2 ** (n - 1)), _COOLDOWN_MAX_SEC)
        return max(0.0, required - elapsed)

    def _record_auth_failure(self, user: str) -> None:
        """记录一次认证失败：刷新时间戳、连续计数+1（下次进入指数退避冷却）。"""
        state = self._load_cooldown_state()
        entry = state.get(user, {})
        entry["last_auth_fail_ts"] = datetime.now().astimezone().isoformat(timespec="seconds")
        entry["consecutive_auth_fails"] = int(entry.get("consecutive_auth_fails", 0)) + 1
        state[user] = entry
        self._save_cooldown_state(state)
        n = entry["consecutive_auth_fails"]
        logger.warning("记录认证失败：user=%s 连续 %d 次 → 下次冷却 %ds",
                       user, n, min(_COOLDOWN_BASE_SEC * (2 ** (n - 1)), _COOLDOWN_MAX_SEC))

    def _record_send_success(self, user: str) -> None:
        """发送成功 → 清零该 user 的冷却状态（一次成功即视为限频已解除）。"""
        state = self._load_cooldown_state()
        if user in state:
            state[user] = {"last_auth_fail_ts": None, "consecutive_auth_fails": 0}
            self._save_cooldown_state(state)

    def _open_and_login(self, smtp_config: dict):
        """
        依次尝试所有连接策略，返回首个「连接 + 认证」成功的 (server, label)。
        认证错误立刻抛出（与策略无关）；其余错误换下一策略。
        全部策略失败 → 抛出最后一个异常。
        """
        host = smtp_config["host"]
        port = int(smtp_config["port"])
        user = smtp_config["user"]
        password = smtp_config["password"]
        strategies = self._build_strategies()
        logger.info("连接策略（按序尝试直到成功）: %s", [lbl for lbl, _ in strategies])

        last_err: Optional[Exception] = None
        for label, connect in strategies:
            # —— 连接 ——
            try:
                server = connect(host, port)
            except smtplib.SMTPAuthenticationError:
                raise
            except Exception as e:
                logger.info("[策略=%s] 连接失败: %s", label, e)
                last_err = e
                continue
            # —— 连接成功 → 握手 + 认证 ——
            try:
                if not self._is_ssl_port(port):
                    server.starttls()
                server.login(user, password)
                logger.info("[策略=%s] 连接 + 认证成功", label)
                return server, label
            except smtplib.SMTPAuthenticationError:
                with server:
                    pass
                raise
            except Exception as e:
                logger.info("[策略=%s] 握手/认证失败: %s", label, e)
                last_err = e
                with server:
                    pass
                continue

        raise last_err if last_err else RuntimeError("无可用连接策略")

    # ----------------------------- 策略构造 ---------------------------- #

    def _build_strategies(self) -> List[Tuple[str, callable]]:
        """
        构造连接策略清单（按优先级）：
          direct → 环境变量代理… → 本地 SOCKS 端口探测（懒执行）
        环境变量在此一次性快照（之后 _connect_direct 会重置 socket，不影响已捕获的代理）。
        """
        strategies: List[Tuple[str, callable]] = [("direct", self._connect_direct)]

        socks = _import_socks()
        if socks is None:
            logger.warning("pysocks 未安装：仅支持直连，无法走 SOCKS 代理回退")
            return strategies

        for proxy in self._detect_proxies(socks):
            ptype, phost, pport = proxy
            name = _PTYPE_NAME.get(ptype, "socks")
            strategies.append(
                (f"{name}://{phost}:{pport}",
                 lambda h, p, px=proxy: self._connect_socks(h, p, px))
            )
        # 兜底：探测本地常见 SOCKS 端口（仅前面策略都失败时才真正执行探测）
        strategies.append(("auto-local-socks", self._connect_auto_local_socks))
        return strategies

    def _detect_proxies(self, socks) -> List[tuple]:
        """从环境变量自动发现代理（去重，保序）。"""
        import os
        found: List[tuple] = []
        seen = set()

        def add(ptype, host, port):
            if not host or not port:
                return
            key = (ptype, host, int(port))
            if key in seen:
                return
            seen.add(key)
            found.append(key)

        env_sources = [
            ("SMTP_SOCKS_PROXY", socks.SOCKS5),
            ("ALL_PROXY", socks.SOCKS5),
            ("all_proxy", socks.SOCKS5),
            ("HTTPS_PROXY", socks.HTTP),
            ("https_proxy", socks.HTTP),
        ]
        for var, fallback_type in env_sources:
            val = (os.environ.get(var) or "").strip()
            if not val:
                continue
            parsed = self._parse_proxy_url(val, fallback_type, socks)
            if parsed:
                add(*parsed)
        return found

    @staticmethod
    def _parse_proxy_url(url: str, fallback_type, socks):
        """
        解析代理 URL → (ptype, host, port)。
        支持 socks5:// socks5h:// socks4:// http:// host:port；无法解析 → None。
        """
        import re
        m = re.match(r'^(?:([a-zA-Z0-9+]+)://)?([^:/]+)(?::(\d+))?', url.strip())
        if not m or not m.group(2) or not m.group(3):
            return None
        scheme = (m.group(1) or "").lower()
        host, port = m.group(2), int(m.group(3))
        type_map = {
            "socks5": socks.SOCKS5, "socks5h": socks.SOCKS5,
            "socks4": socks.SOCKS4, "socks4a": socks.SOCKS4,
            "http": socks.HTTP, "https": socks.HTTP,
        }
        return (type_map.get(scheme, fallback_type), host, port)

    # ----------------------------- 连接实现 ---------------------------- #

    @staticmethod
    def _reset_socket_to_direct() -> None:
        """
        一键还原为直连：撤销任何 pysocks 对 socket 模块的全局包装
        （socket.socket 与 socket.create_connection 都可能被 wrapmodule 改写），
        并清空 pysocks 默认代理。确保国内 SMTP（QQ/163）走直连，而非被 Clash 等代理劫持。
        """
        _socket_module.socket = _REAL_SOCKET
        _socket_module.create_connection = _REAL_CREATE_CONNECTION
        socks = _import_socks()
        if socks is not None:
            try:
                socks.set_default_proxy()  # 无参 = 直连
            except Exception:
                pass

    def _connect_direct(self, host, port):
        """策略 1：纯直连（重置 pysocks 包装）。"""
        self._reset_socket_to_direct()
        if self._is_ssl_port(port):
            return smtplib.SMTP_SSL(host, port, timeout=self.timeout)
        return smtplib.SMTP(host, port, timeout=self.timeout)

    def _connect_socks(self, host, port, proxy):
        """
        策略 2/3：经 SOCKS/HTTP 代理连接。
        临时把 socket.socket 换成 socks.socksocket（带默认代理），连接成功后立即还原，
        因此 monkeypatch 只作用于「建立连接」这一瞬，不污染后续。
        """
        socks = _import_socks()
        if socks is None:
            raise RuntimeError("pysocks 不可用，无法走代理")
        ptype, phost, pport = proxy
        socks.set_default_proxy(ptype, phost, pport)
        _socket_module.socket = socks.socksocket
        try:
            if self._is_ssl_port(port):
                server = smtplib.SMTP_SSL(host, port, timeout=self.timeout)
            else:
                server = smtplib.SMTP(host, port, timeout=self.timeout)
        finally:
            # 连接已建立在 server.sock 上；后续 login/send 用的是该已连接 socket，
            # 不再依赖全局 socket.socket，故立即还原。
            self._reset_socket_to_direct()
        return server

    def _connect_auto_local_socks(self, host, port):
        """
        策略 3（兜底，懒执行）：探测本地常见 SOCKS 端口，经首个可用端口连接。
        仅在 direct + 环境变量代理都失败时才会被调用 → 日常直连成功时零开销。
        """
        socks = _import_socks()
        if socks is None:
            raise RuntimeError("pysocks 不可用")
        for pport in _LOCAL_SOCKS_PORTS:
            # 快速 TCP 探测（0.6s）端口是否监听。
            # 注意：必须用 _REAL_CREATE_CONNECTION（模块级函数），
            # 而非 _REAL_SOCKET.create_connection —— socket 类上没有 create_connection
            # （它是 socket 模块的函数，不是 socket 类的方法），否则抛
            # "type object 'socket' has no attribute 'create_connection'"，
            # 导致直连失败时 SOCKS 回退彻底无法启动。
            try:
                s = _REAL_CREATE_CONNECTION(("127.0.0.1", pport), timeout=0.6)
                s.close()
            except OSError:
                continue
            logger.info("发现本地代理端口 127.0.0.1:%d，尝试经 SOCKS5 连接", pport)
            try:
                return self._connect_socks(host, port, (socks.SOCKS5, "127.0.0.1", pport))
            except Exception as e:
                logger.info("经 127.0.0.1:%d 连接失败: %s", pport, e)
                continue
        raise ConnectionError("未发现可用的本地 SOCKS 代理端口")

    @staticmethod
    def _is_ssl_port(port: int) -> bool:
        return int(port) == 465


# ---------------------------------------------------------------------- #
# 命令行入口
# ---------------------------------------------------------------------- #

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="发送学术报告邮件")
    parser.add_argument("--report-path", type=str, help="报告文件路径")
    parser.add_argument("--recipient", type=str, help="收件人邮箱")
    parser.add_argument("--subject", type=str, help="邮件主题")
    parser.add_argument("--test", action="store_true",
                        help="仅测试 SMTP 连接（自动遍历直连+代理策略）")
    args = parser.parse_args()

    sender = EmailSender()

    if args.test:
        ok, message = sender.test_connection()
        print(message)
        return 0 if ok else 1

    if not args.report_path:
        parser.error("--report-path 是必需的（除非用 --test）")

    ok = sender.send_report(args.report_path, args.recipient, args.subject)
    if ok:
        print("邮件发送成功！/ Email sent successfully!")
        return 0
    print("邮件发送失败，请查看日志。/ Email sending failed, see logs.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
