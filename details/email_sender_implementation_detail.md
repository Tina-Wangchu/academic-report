# email_sender.py - Implementation Detail

## 模块概述

**模块名称**: SMTP 邮件发送 (email_sender.py) — 模块6 / Module 6
**版本**: 1.3.0
**完成日期**: 2026-07-12（v1.1.0 增「代理自动识别 + 回退」，2026-07-21；v1.1.1 修本地 SOCKS 探测 bug，2026-07-21；v1.2.0 增「发送记录持久化日志」，2026-07-21；v1.3.0 增「冷却守卫」，2026-07-21）
**状态**: ✅ 已完成（单元测试 42 项全通过）

---

## 功能说明

把 `report_generator` 生成的报告（.md / .pdf）作为附件，通过 SMTP 发送到用户邮箱，附带 HTML 正文。

**主要能力**:
- 📧 报告作为附件 + HTML 正文（双语）发送
- 🔐 SSL/TLS 自动分流（465 → SMTP_SSL；587/25 → SMTP + STARTTLS）
- 🔄 **代理自动识别 + 回退**（v1.1.0）：开/关代理都能发——直连失败自动经 SOCKS 代理重试
- 🔁 瞬时错误重试（认证错误立即失败，不重试）
- 🧪 `test_connection()` / `--test` 排查 SMTP 配置（同样遍历直连+代理）
- ⚙️ 配置来自 `config_manager`（`~/.hermes/.env` 的 SMTP_* + config 的 email_recipient）

---

## 实现细节

### 1. 连接策略链 —— 自动识别代理，开/关代理都能发（v1.1.0 核心）

历史上本模块「恒直连」（`_disable_socks_proxy` 强制清空 pysocks）。这在**国内 SMTP（QQ/163）直连可达**时没问题，但一旦**直连被墙、必须经代理**（如国内直连 Gmail）就必败（旧日志满是 `gmail:587 [WinError 10060]`）。

v1.1.0 改为**按序尝试、命中即用、全失败才报错**的策略链：

```
direct  →  环境变量代理(SMTP_SOCKS_PROXY/ALL_PROXY/HTTPS_PROXY)  →  本地 SOCKS 端口探测
```

| 策略 | 做什么 | 何时命中 |
|------|--------|----------|
| `direct` | `_reset_socket_to_direct()` 还原真 socket + 清空 pysocks 默认代理，纯直连 | 国内 SMTP（QQ/163），无论代理开/关——最快，首选 |
| `socks5://host:port`（环境变量） | 解析 `SMTP_SOCKS_PROXY` 等，临时把 `socket.socket` 换成 `socks.socksocket` 经代理连接，连接后立即还原 | 直连被墙（GFW）但代理可达（如 Gmail） |
| `auto-local-socks`（兜底，懒执行） | 探测 `127.0.0.1:{7897,7890,1080,...}`（Clash/V2Ray），经首个可用端口连接 | 环境变量没设、但本地代理在跑 |

**关键不变量**：
- **认证错误与代理无关** → 任一策略命中即立刻判定，不重试、不换策略。
- **直连成功时不触碰代理** → 日常零额外开销（直连是 O(1) 命中）。
- **SOCKS monkeypatch 只作用于「建立连接」一瞬**：`_connect_socks` 在 `try/finally` 里连接后立即 `_reset_socket_to_direct()`，不污染后续。
- **真 socket 在模块加载时捕获**：`_REAL_SOCKET`/`_REAL_CREATE_CONNECTION` 在任何 pysocks 包装前保存，`_reset_socket_to_direct` 据此一键还原（防 `wrapmodule` 同时改写 `socket.socket` 与 `create_connection`）。

**实测验证**（本机，Clash@7897 运行中）：
- QQ `smtp.qq.com:465`：策略链 `[direct, socks5://127.0.0.1:7897, auto-local-socks]` → **direct 命中**（代理开/关都走直连）。
- Gmail `smtp.gmail.com:587`（模拟直连被墙）：`direct` 超时 `[WinError 10060]` → **自动回退 socks5://127.0.0.1:7897 → 经 Clash 隧道抵达 Gmail 认证服务器**（返回 Gmail 真实 `535` 拒绝，证明隧道通；QQ 凭据不匹配 Gmail 属预期）。
- **Jul 21 故障复现 + 修复验证**：清空所有代理环境变量（`SMTP_SOCKS_PROXY=""`，策略链退化为 `[direct, auto-local-socks]`）+ 强制 `direct` 抛 `10060` → `auto-local-socks` 探测 `127.0.0.1:7897` 成功 → 经 SOCKS5 连接 QQ SMTP **连接+认证成功**（旧版在此崩溃，见下）。

> **🐛 v1.1.1 修复 —— 本地 SOCKS 探测的 `create_connection` bug（Jul 21 邮件失败根因）**
> `_connect_auto_local_socks` 的端口探测误写成 `_REAL_SOCKET.create_connection(...)`。但 `_REAL_SOCKET` 是 **socket 类**（`socket.socket`），`create_connection` 是 **socket 模块的函数、并非类方法** → 直连失败、无环境变量代理时，兜底探测直接抛
> `AttributeError: type object 'socket' has no attribute 'create_connection'`，**SOCKS 回退彻底无法启动**，邮件必败。
> 修复：改用 `_REAL_CREATE_CONNECTION(...)`（模块级函数，模块加载时捕获）。这样直连被墙时兜底探测才能真正找到本地 Clash 端口并经代理连上。回归测试 `TestAutoLocalSocksProbe` 锁死该不变量（断言 `_REAL_SOCKET` 无 `create_connection`、`_REAL_CREATE_CONNECTION` 可调用，且探测路径不抛 `AttributeError`）。

### 2. SSL / TLS 分流

465 端口用隐式 SSL（`SMTP_SSL`），587/25 用 `SMTP + STARTTLS`。分流在 `_connect_direct` / `_connect_socks` 内按 `_is_ssl_port(port)`（`==465`）判定：

```python
if self._is_ssl_port(port):
    return smtplib.SMTP_SSL(host, port, timeout=self.timeout)
return smtplib.SMTP(host, port, timeout=self.timeout)
```

### 3. 发送与重试 `_send_email`

- 每轮 `_open_and_login()` 已穷尽「直连→代理」；非认证错误才进入下一轮重试。
- `max_retries=3`、`retry_delay=5s`（测试可注入 0）。
- **`SMTPAuthenticationError`**：立即返回 False（重试/换策略都无意义）。
- 其余错误：换策略（同轮内）→ 仍失败则重试（下一轮）。

### 4. 邮件构建 `_create_email`

- `MIMEMultipart`：HTML 正文（`_render_body`，双语，含报告格式/文件名）+ 报告附件（`MIMEApplication`）。
- 主题缺省：`学术报告 / Academic Report - {文件mtime日期}`。
- 附件 `Content-Disposition: attachment; filename=...`。

### 5. 代理发现 `_detect_proxies` / `_parse_proxy_url`

- 环境变量优先级：`SMTP_SOCKS_PROXY` → `ALL_PROXY`/`all_proxy`（SOCKS5）→ `HTTPS_PROXY`/`https_proxy`（HTTP）。
- 解析 `socks5://` / `socks5h://` / `socks4://` / `http://` / `host:port`，去重保序。
- `_build_strategies` 一次性快照环境变量（之后 `_connect_direct` 重置 socket 不影响已捕获的代理元组）。

### 6. 配置依赖

| 来源 | 字段 | 用途 |
|------|------|------|
| `~/.hermes/.env` | `SMTP_HOST/PORT/USER/PASSWORD` | SMTP 连接与认证 |
| `~/.hermes/config.yaml` | `email_recipient` | 默认收件人（缺省回退 SMTP_USER） |
| 环境变量 | `SMTP_SOCKS_PROXY` / `ALL_PROXY` / `HTTPS_PROXY` | 代理回退（直连失败时） |

> Gmail 需用**应用专用密码**（非账户密码）；587=TLS，465=SSL。依赖 `pysocks`（Hermes venv 已装；缺失则仅直连，日志告警）。

### 7. CLI

```bash
python email_sender.py --test                      # 测试 SMTP 连接（遍历直连+代理）
python email_sender.py --report-path report.md      # 发送
python email_sender.py --report-path r.md --recipient a@b.com --subject "主题"
```

`main()` 用 `sys.exit(main())` 正确返回退出码（成功 0 / 失败 1）。

### 8. 发送记录持久化日志（v1.2.0）

每次发送尝试（**成功或失败都记**）追加一条到 `~/.hermes/email_sends.jsonl`，便于排查"邮件到底发没发、用什么策略、为何失败"——不再只能依赖 agent 的（常误诊的）转述。

- **格式**：JSONL（每行一条独立 JSON），**append-only、crash-safe**（崩溃不会撕裂整文件）、无读-改-写竞争。相对旧的 `email_log.json`（JSON 数组、读-改-写、易撕裂）更稳健；旧文件保留为历史。
- **每条字段**：`ts`（带时区 ISO 时间）、`recipient`、`subject`、`report`（文件名）、`success`(bool)、`strategy`(`direct`/`socks5://...`/`auto-local-socks`/`null`)、`attempts`、`error`、`error_type`(`auth`/`SMTPServerDisconnected`/`SMTPException`/...)。
- **best-effort**：写入异常仅 `warning`，**绝不向上抛**（绝不影响发送结果）。
- **示例**（本机实测）：
  ```json
  {"ts":"2026-07-21T18:49:23+08:00","recipient":"tinawangchu0615@gmail.com","subject":"[日志验证]...","report":"computer_vision_20260721_1824.md","success":true,"strategy":"direct","attempts":1,"error":null,"error_type":null}
  ```
- **排查用法**：`tail -n 20 ~/.hermes/email_sends.jsonl` 看最近发送；连续多条 `success:false, error_type:auth` = 认证问题；`SMTPServerDisconnected`/`OSError` = 网络瞬时；短时间多条失败 = 可能触发 QQ 登录限频（见下）。
- **可注入**：`EmailSender(log_path=...)` 指定路径；测试用 autouse fixture 重定向到 tmp，绝不污染真实日志。

### 9. 冷却守卫（v1.3.0）—— 斩断「agent 重跑 → 轰炸 QQ → 限频 535」死循环

**背景**：QQ 邮箱对短时间高频 SMTP 登录会临时返回 `535`（登录限频），几分钟自动解除。Hermes agent 遇到一次失败后常**反复重跑 pipeline**（每次重跑都是新进程、都会再登录 QQ），把偶发的网络复位/限频放大成"持续失败"，并误报成"授权码错"。SKILL.md 的行为约束靠 agent 遵从（不 100%），故再加一道**代码层硬防线**。

**机制**：
- 认证失败（`error_type=="auth"`，含限频假性 535）→ 记录 `{last_auth_fail_ts, consecutive_auth_fails}` 到 `~/.hermes/email_send_cooldown.json`（**跨进程持久**，按 SMTP 账号分隔）。
- 下次发送前先查冷却：`冷却剩余 = min(30 × 2^(连续失败-1), 300) − 已耗时`。剩余 > 0 → **直接拒发、0 秒返回、不登录 QQ**，stdout 打印「发送冷却中，需再等 N 秒」，并落一条 `error_type=cooldown` 日志。
- **指数退避**：30s → 60s → 120s → 240s → 300s（上限 5 分钟）。agent 越是重跑，冷却越久，强制等待。
- **成功即清零**：一次成功发送就把该账号冷却状态重置（视为限频已解除）。
- **手动强制**：`EMAIL_SKIP_COOLDOWN=1` 跳过冷却（调试/紧急用）。
- **非认证错误不触发**：`SMTPServerDisconnected`（网络瞬时）/超时等不计入冷却——那些是网络问题，不该惩罚。

**关键不变量**：
- 冷却检查在 `_send_email` **之前** → 冷却中**绝不创建 SMTP 连接**（实测 `elapsed 0.00s`，QQ 零登录）。
- cooldown 状态读写均 **best-effort**（防御加载、原子写 `tmp+os.replace`），任何异常都不影响发送主流程。
- 冷却提示为 **纯 ASCII + 中文**（GBK 控制台可编码），且 `print` 套 try/except——控制台编码异常绝不向上抛。

**实测**（本机，模拟"刚连续认证失败 2 次"）：
```
cooldown_remaining: 59.1s
[email_sender] 发送冷却中 (cooldown): 距上次 SMTP 认证失败需再等 59 秒。…
returned: False | elapsed 0.00s (<<1s = QQ 未被联系)
send-log: {"...","success":false,"error_type":"cooldown",...}
real ~/.hermes/email_send_cooldown.json untouched (测试用 tmp 路径)
```

---

## 测试

### 单元测试（`test/test_email_sender.py`，42 项全通过）

| 测试类 | 数量 | 覆盖点 |
|--------|------|--------|
| `TestSendReport` | 8 | 587 STARTTLS 成功、465 SSL 不 starttls、配置/收件人/文件校验、认证错误不重试、瞬时错误重试成功、重试耗尽、收件人覆盖 |
| `TestTestConnection` | 3 | 连接成功、连接失败、配置无效 |
| `TestCreateEmail` | 4 | 附件+文件名、默认主题、主题覆盖、正文含文件名/格式 |
| `TestPortRouting` | 1 | `_is_ssl_port` |
| `TestProxyDetection` | 5 | `_parse_proxy_url` 各协议/bare/垃圾输入、`_detect_proxies` 环境变量发现、去重 |
| `TestStrategyChain` | 4 | direct 首位、环境代理追加、**直连失败→代理回退**、直连成功不触发本地探测 |
| `TestAutoLocalSocksProbe` | 3 | **回归保护**：`_REAL_SOCKET` 类无 `create_connection`/`_REAL_CREATE_CONNECTION` 可调用；探测经模块级函数（不抛 AttributeError）；全端口关闭→ConnectionError |
| `TestSendLog` | 5 | 成功落一条、失败落一条（含 error/error_type）、认证失败落一条、**日志写失败不影响发送**、默认路径解析；autouse fixture 重定向日志防污染 |
| `TestCooldown` | 8 | 认证失败触发冷却并拦截下一次（不再登录 QQ）、指数退避 30/60/120/300、冷却到期解除、成功清零、`EMAIL_SKIP_COOLDOWN=1` 强制跳过、非认证错误不触发冷却、冷却写日志+stdout 提示、**print 异常不崩** |

测试用 `FakeSMTP` + `FakeConfig`，monkeypatch `smtplib.SMTP`/`SMTP_SSL`，**全程不联网**；代理回退用例把直连工厂首调抛 `OSError`，验证自动换代理策略。

### 运行

```bash
python -m pytest test/test_email_sender.py -v
python email_sender.py --test   # 真实排查（需配 ~/.hermes/.env；日志打印策略链与命中策略）
```

---

## 已知限制与未来改进

1. **附件文件名非 ASCII**：当前未做 RFC 2231 编码；报告文件名经 `safe_filename` 处理通常为 ASCII，可接受。
2. **单附件**：一次发一个报告文件；未来可支持 md+pdf 双附件。
3. **无内嵌预览**：报告作为附件，正文仅摘要；未来可把 PDF 报告直接作为正文内嵌。
4. **重试退避固定**：`retry_delay` 固定，未做指数退避。
5. **直连超时较长**：直连被墙时需等 `timeout`（默认 30s）才回退到代理；如常用墙外 SMTP，可调小 `timeout` 或手动设 `SMTP_SOCKS_PROXY`。
6. **TUN 模式劫持**：若代理以系统 TUN 模式劫持全部流量（含国内 SMTP），Python 层无法绕过；当前策略链已覆盖应用层（pysocks/环境变量/本地端口）所有常见情形。

---

## 与规范/计划的对应

| 规范要求（design-init.txt 模块6） | 实现位置 |
|------|------|
| 配置文件/环境变量配置 SMTP | `config_manager` → `~/.hermes/.env` ✅ |
| 设置默认邮箱 | `get_email_recipient`（回退 SMTP_USER）✅ |
| 报告作为附件 + 正文发送 | `send_report` → `_create_email`（HTML 正文 + 附件）✅ |
| 邮件可靠送达（代理无关） | `_open_and_login` 策略链（直连→代理回退）✅ v1.1.0 |

> **全链路就绪**：检索(paper_search) → 筛选(paper_filter) → 分析(paper_analyzer) → 报告(report_generator) → 邮件(email_sender)。

---

**最后更新**: 2026-07-21（v1.3.0 增冷却守卫；v1.2.0 增发送记录持久化日志；v1.1.1 修本地 SOCKS 探测 `create_connection` bug）
**维护者**: Academic Report Team
