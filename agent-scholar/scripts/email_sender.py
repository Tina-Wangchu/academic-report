"""
邮件发送模块（模块6 / Module 6）

通过 SMTP 把生成的学术报告作为附件发送到用户邮箱。

- 配置来自 config_manager（SMTP_HOST/PORT/USER/PASSWORD 取自 ~/.hermes/.env；
  收件人取自 config.email_recipient，缺省回退到 SMTP_USER）。
- 端口 465 → SMTP_SSL（隐式 SSL）；端口 587/其它 → SMTP + STARTTLS。
  （计划代码恒用 STARTTLS，在 465 上会失败；此处按端口分流。）
- 发送失败（非认证错误）按指数退避重试，认证错误立即失败。
- 提供test_connection() 与 --test CLI 便于排查。
"""

from __future__ import annotations

import logging
import smtplib
import sys
import time
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path
from typing import Optional, Tuple

from config_manager import get_config_manager

logger = logging.getLogger(__name__)


class EmailSender:
    """SMTP 邮件发送器"""

    def __init__(self, config_manager=None, max_retries: int = 3,
                 retry_delay: float = 5.0, timeout: int = 30):
        """
        Args:
            config_manager: 配置管理器（默认全局实例；测试可注入）
            max_retries:    最大重试次数（认证错误不重试）
            retry_delay:    重试间隔秒数
            timeout:        SMTP 连接超时
        """
        self.config_manager = config_manager or get_config_manager()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

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

        try:
            msg = self._create_email(report_file, recipient,
                                     smtp_config["user"], subject, file_format)
            return self._send_email(msg, smtp_config)
        except Exception as e:
            logger.error("发送邮件失败: %s", e)
            return False

    def test_connection(self) -> Tuple[bool, str]:
        """测试 SMTP 连接与认证（不发送邮件）"""
        is_valid, error_msg = self.config_manager.validate_smtp_config()
        if not is_valid:
            return False, error_msg

        smtp_config = self.config_manager.get_smtp_config()
        try:
            with self._make_smtp(smtp_config) as server:
                if not self._is_ssl_port(smtp_config["port"]):
                    server.starttls()
                server.login(smtp_config["user"], smtp_config["password"])
            return True, "SMTP 连接测试成功 / SMTP connection OK"
        except Exception as e:
            return False, f"SMTP 连接测试失败 / SMTP connection failed: {e}"

    # ----------------------------- 邮件构建 ---------------------------- #

    def _create_email(self, report_file: Path, recipient: str,
                      sender: str, subject: Optional[str],
                      file_format: str) -> MIMEMultipart:
        """构建邮件对象（HTML 正文 + 报告附件）"""
        msg = MIMEMultipart()
        msg["From"] = formataddr(("Agent Scholar", sender))
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
    <p>本报告由 Agent Scholar for Hermes Agent 自动生成。<br>
       Generated by Agent Scholar for Hermes Agent.</p>
  </div>
  <div class="footer">
    <p>如有问题，请回复此邮件。/ Reply to this email for any questions.</p>
    <p>© {year} Agent Scholar</p>
  </div>
</div></body></html>"""

    # ----------------------------- 发送 -------------------------------- #

    def _send_email(self, msg: MIMEMultipart, smtp_config: dict) -> bool:
        """带重试的发送；认证错误立即失败，其余按 max_retries 重试"""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("尝试发送邮件 (第 %d/%d 次)", attempt, self.max_retries)
                with self._make_smtp(smtp_config) as server:
                    if not self._is_ssl_port(smtp_config["port"]):
                        server.starttls()
                    server.login(smtp_config["user"], smtp_config["password"])
                    server.send_message(msg)
                logger.info("邮件发送成功")
                return True
            except smtplib.SMTPAuthenticationError as e:
                # 认证错误重试无意义
                logger.error("SMTP 认证失败: %s", e)
                return False
            except (smtplib.SMTPException, OSError) as e:
                logger.error("SMTP 错误 (第 %d 次): %s", attempt, e)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    logger.error("达到最大重试次数，发送失败")
                    return False
            except Exception as e:
                logger.error("发送邮件时发生未知错误: %s", e)
                return False
        return False

    # ----------------------------- 连接辅助 ---------------------------- #

    @staticmethod
    def _disable_socks_proxy() -> None:
        """
        强制 SMTP 直连：若 pysocks 把 socket.socket 全局 monkeypatch 了（或设了
        默认 SOCKS 代理，常见于 SMTP_SOCKS_PROXY 环境变量），重置为直连。
        国内邮箱（QQ/163）应直连，走 SOCKS 代理（如 Clash）反而会超时。
        """
        try:
            import socks                                   # pysocks
            socks.set_default_proxy()                      # 无参 = 直连
        except Exception:
            pass
        # 清掉进程内残留的 SMTP 代理变量，避免上层工具据此再代理
        import os
        for k in ("SMTP_SOCKS_PROXY", "ALL_PROXY", "all_proxy"):
            if os.environ.get(k):
                os.environ[k] = ""

    def _make_smtp(self, smtp_config: dict) -> smtplib.SMTP:
        """按端口选择 SSL（465）或普通 SMTP（587 等，后续 STARTTLS）"""
        self._disable_socks_proxy()                        # SMTP 强制直连，绕过任何 SOCKS 代理
        host = smtp_config["host"]
        port = int(smtp_config["port"])
        if self._is_ssl_port(port):
            return smtplib.SMTP_SSL(host, port, timeout=self.timeout)
        return smtplib.SMTP(host, port, timeout=self.timeout)

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
                        help="仅测试 SMTP 连接")
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
