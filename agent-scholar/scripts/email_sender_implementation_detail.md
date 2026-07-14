# email_sender.py - Implementation Detail

## 模块概述

**模块名称**: SMTP 邮件发送 (email_sender.py) — 模块6 / Module 6
**版本**: 1.0.0
**完成日期**: 2026-07-12
**状态**: ✅ 已完成（单元测试 17 项全通过）

---

## 功能说明

把 `report_generator` 生成的报告（.md / .html）作为附件，通过 SMTP 发送到用户邮箱，附带 HTML 正文。

**主要能力**:
- 📧 报告作为附件 + HTML 正文（双语）发送
- 🔐 SSL/TLS 自动分流（465 → SMTP_SSL；587/25 → SMTP + STARTTLS）
- 🔁 瞬时错误重试（认证错误立即失败，不重试）
- 🧪 `test_connection()` / `--test` 排查 SMTP 配置
- ⚙️ 配置来自 `config_manager`（`~/.hermes/.env` 的 SMTP_* + config 的 email_recipient）

---

## 实现细节

### 1. SSL / TLS 分流（对计划代码的修正）

计划代码恒用 `smtplib.SMTP` + `starttls()`，但 **465 端口用隐式 SSL**（`SMTP_SSL`），用 STARTTLS 会失败。本模块按端口分流：

```python
def _make_smtp(self, smtp_config):
    port = int(smtp_config["port"])
    if self._is_ssl_port(port):           # 465
        return smtplib.SMTP_SSL(host, port, timeout=self.timeout)
    return smtplib.SMTP(host, port, timeout=self.timeout)  # 587/25 等

# 发送时：
with self._make_smtp(smtp_config) as server:
    if not self._is_ssl_port(port):
        server.starttls()                # 仅非 SSL 端口才 STARTTLS
    server.login(...); server.send_message(msg)
```

### 2. 重试策略 `_send_email`

- `max_retries=3`、`retry_delay=5s`（测试可注入 0）。
- **`SMTPAuthenticationError`**：立即返回 False（重试无意义）。
- **`SMTPException` / `OSError`**：重试，间隔 `retry_delay`。
- 其它未知异常：立即 False。

### 3. 邮件构建 `_create_email`

- `MIMEMultipart`：HTML 正文（`_render_body`，双语，含报告格式/文件名）+ 报告附件（`MIMEApplication`）。
- 主题缺省：`学术报告 / Academic Report - {文件mtime日期}`。
- 附件 `Content-Disposition: attachment; filename=...`。

### 4. 配置依赖

| 来源 | 字段 | 用途 |
|------|------|------|
| `~/.hermes/.env` | `SMTP_HOST/PORT/USER/PASSWORD` | SMTP 连接与认证 |
| `~/.hermes/config.yaml` | `email_recipient` | 默认收件人（缺省回退 SMTP_USER） |

> Gmail 需用**应用专用密码**（非账户密码）；587=TLS，465=SSL。

### 5. CLI

```bash
python -m email_sender --test                      # 测试 SMTP 连接
python -m email_sender --report-path report.md     # 发送
python -m email_sender --report-path r.md --recipient a@b.com --subject "主题"
```

`main()` 用 `sys.exit(main())` 正确返回退出码（成功 0 / 失败 1）。

---

## 测试

### 单元测试（`test/test_email_sender.py`，17 项全通过）

| 测试类 | 数量 | 覆盖点 |
|--------|------|--------|
| `TestSendReport` | 8 | 587 STARTTLS 成功、465 SSL 不 starttls、配置/收件人/文件校验、认证错误不重试、瞬时错误重试成功、重试耗尽、收件人覆盖 |
| `TestTestConnection` | 3 | 连接成功、连接失败、配置无效 |
| `TestCreateEmail` | 4 | 附件+文件名、默认主题、主题覆盖、正文含文件名/格式 |
| `TestPortRouting` | 2 | `_is_ssl_port` 465/587/25 |

测试用 `FakeSMTP` + `FakeConfig`，monkeypatch `smtplib.SMTP`/`SMTP_SSL`，**全程不联网**。

### 运行

```bash
python -m pytest test/test_email_sender.py -v
python -m email_sender --test   # 真实排查（需配 ~/.hermes/.env）
```

---

## 已知限制与未来改进

1. **附件文件名非 ASCII**：当前未做 RFC 2231 编码；报告文件名经 `safe_filename` 处理通常为 ASCII，可接受。
2. **单附件**：一次发一个报告文件；未来可支持 md+html 双附件。
3. **无内嵌预览**：报告作为附件，正文仅摘要；未来可把 HTML 报告直接作为正文内嵌。
4. **重试退避固定**：`retry_delay` 固定，未做指数退避。

---

## 与规范/计划的对应

| 规范要求（design-init.txt 模块6） | 实现位置 |
|------|------|
| 配置文件/环境变量配置 SMTP | `config_manager` → `~/.hermes/.env` ✅ |
| 设置默认邮箱 | `get_email_recipient`（回退 SMTP_USER）✅ |
| 报告作为附件 + 正文发送 | `send_report` → `_create_email`（HTML 正文 + 附件）✅ |

> **全链路就绪**：检索(paper_search) → 筛选(paper_filter) → 分析(paper_analyzer) → 报告(report_generator) → 邮件(email_sender)。

---

**最后更新**: 2026-07-12
**维护者**: Agent Scholar Team
