---
name: academic-report
description: "学术论文搜索→分析→双语报告→邮件（arXiv/Semantic Scholar/OpenAlex + LLM 四要素 + SMTP 发送）。当用户想【搜索/查找/最近 的论文】【文献综述/调研某领域】【研究热点/趋势分析】【把论文报告发到我邮箱】时务必用本技能——一条命令完成检索+报告+发信。/ Academic paper search→analysis→bilingual report→email (arXiv/Semantic Scholar/OpenAlex + LLM). Use when the user wants to search recent papers, do a literature review, analyze research trends, or have a paper report emailed."
version: 1.2.0
author: Agent Scholar Team
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [research, academic, papers, automation, email]
    category: research
    requires_tools: [terminal, web_search]
    config:
      - key: academic.default_language
        default: "bilingual"
      - key: academic.default_time_range
        default: "3y"
      - key: academic.max_results
        default: "6"
      - key: academic.email_recipient
        default: ""
    blueprint:
      schedule: "0 9 * * 1"
      deliver: email
      prompt: "Weekly incremental academic report — run scheduler.py --once"
required_environment_variables:
  - name: SMTP_HOST
  - name: SMTP_PORT
  - name: SMTP_USER
  - name: SMTP_PASSWORD
  - name: LLM_API_KEY
    required_for: "optional (falls back to rule-based)"
required_credential_files: []
---

# Academic Scholar

学术论文自动化：检索 → **LLM 四要素分析** → 双语报告 → 邮件，**一条命令完成**。

## 🟢 第一步、也是唯一一步：用 `terminal` 工具运行这一条命令

```bash
python "scripts/pipeline.py" "<用户的检索请求原话>" --recipient "<用户邮箱>"
```

- 默认收件人 `<your-email@example.com>`（也可 `--recipient` 指定）。
- 脚本内部完成全部工作：意图解析 → arXiv/Semantic Scholar/OpenAlex 并行检索 → 筛选+热点聚类 → **LLM 四要素分析** → 双语报告 → SMTP 发送（QQ 邮箱，已配授权码；自动识别代理）。
- **Windows 必须用 `python`，不要用 `python3`**（`python3` 是应用商店存根，会失败）。
- 可选：`--max-results N`（默认 6）、`--language bilingual|zh|en`、`--time 3y|1y|1w`、`--format markdown|html`、`--no-email`。

**你的唯一职责**：运行上方命令 → 把脚本 stdout（[1/6]…[6/6] 各阶段 + 「发送到 …: 成功/失败」）**原样**贴给用户。**不要**自己生成报告，**不要**自己发邮件。

## 🚫 绝对禁止（这些都是历史真实失败，做了必然失败/被拦截）

1. **禁止 `python3 -c "..."` 或 heredoc（`<< 'EOF'` / `<< 'PYEOF'`）**：Hermes 会判为「危险命令」**自动拦截**（`BLOCKED: User denied`）。必须用上方的 `python "…/pipeline.py"` 单条命令——它**不会**被拦截（发信在脚本内部，命令本身不含触发词）。
2. **禁止用 `execute_code` 发邮件或读凭据**：`execute_code` 是隔离沙箱，**不继承环境变量**，`os.getenv('SMTP_PASSWORD')` 返回 None。只有 `terminal` 运行的脚本才能读到 `~/.hermes/.env` 里的凭据。
3. **禁止自己写 `smtplib`/`sendmail`/`MIMEText` 等内联发信代码**：既会被拦，又会用错配置。发信一律交给 pipeline 内部的 `email_sender.py`（已内置代理回退、重试、冷却守卫、发送日志）。
4. **禁止手动抓 arXiv / 自己编报告**（如 `arxiv_cv.xml`、`execute_code` 拼 JSON）：违反技能定义，且会**编造论文**（hallucination）。论文检索与报告 100% 由 pipeline 完成。
5. **禁止切换到 Gmail 配置**（`smtp.gmail.com`/`GMAIL_ADDRESS`）：本技能已配 **QQ 邮箱 `smtp.qq.com:465`** 且直连可用。不要用环境里的 `GMAIL_*` 变量。
6. **禁止查找旧技能名** `academic/paper-email-service`、`paper-search` 等（v1.0 旧名，会 not found）。本技能唯一名 `academic-report`。

> 重要：上方命令用**相对路径** `scripts/...`（从技能根目录运行，便于移植）。**部署到 Hermes 时**：若 gateway 的 `terminal` 工具 cwd 不是技能目录，需把 `scripts/...` 换成部署机上的**绝对路径**（如 `C:/Users/<you>/AppData/Local/hermes/skills/academic-report/scripts/pipeline.py`）——本环境**未设置 `$HERMES_SKILL_DIR`**，不要用它替代。

### 🚫 邮件发送失败时——必须遵守（防止误诊 + 重试轰炸，这是历史故障根因）

脚本内部**已完整处理**：代理自动识别（直连→SOCKS 回退）、瞬时错误重试、认证错误判定。所以邮件一旦失败，**你必须**：

1. **不得臆断"授权码/密码错误"**，也**不得**让用户去改 SMTP 配置。是否真为认证失败，**只以脚本 stdout 明示的 `SMTP 认证失败` 为准**。以下都是**网络瞬时问题、不是密码错**，照实上报即可：
   - `Connection unexpectedly closed`（连接被意外关闭）= 465 SSL 握手被网络/防火墙复位
   - `[WinError 10060]`（连接超时）= 直连被墙，脚本会自动回退 SOCKS
2. **不得反复重跑 pipeline**：每次重跑都会再登录 QQ SMTP，连续多次会触发 **QQ 登录限频→假性 535**。失败后**最多等 1–2 分钟重试一次**；仍失败就**如实上报并停止**，不要继续轰炸。
3. **不得尝试任何替代发信方式**：`himalaya` / `mutt` / `sendmail` / `curl smtp` / 浏览器——一律禁止。
4. **不得查找旧技能名**：`academic/paper-email-service`、`paper-search`、`paper-summarizer` 都是 v1.0 旧名（会 `not found`）。本技能唯一名是 **`academic-report`**。
5. **不得读取凭据文件**：`AppData\Local\hermes\.env`、`~/.hermes/.env` 会被拒绝访问；凭据由脚本内部读取，无需你介入。
6. **看到「发送冷却中」就停手**：脚本已内置**冷却守卫**——认证失败（含 QQ 登录限频的假性 535）后会指数退避（30→60→120→300s）并**自动拒发**（不再登录 QQ，避免轰炸加重限频）。若 stdout 出现 `[email_sender] 发送冷却中…需再等 N 秒`，**直接转告用户「请等待 N 秒后再试」并停止**，不要重跑、不要尝试绕过。冷却由脚本管，你只负责转述。

**你该做的（仅此而已）**：把脚本最后 ~15 行 stdout 原样贴给用户，并附一句——"脚本已尝试直连+SOCKS 回退仍失败，多为网络瞬时问题；建议稍等 1–2 分钟重试，或确认本地代理（Clash 等）在运行。" 然后停止。

### 单次搜索（一条命令 = 检索 + LLM 四要素 + 报告 + 发邮件）

```bash
python "scripts/pipeline.py" "<用户的检索请求原话>" --recipient "<用户邮箱>"
```

- `<用户邮箱>`：默认用已配置的收件人 `<your-email@example.com>`（也可在命令里用 `--recipient` 指定，或问用户）。
- 脚本内部完成：意图解析 → arXiv/Semantic Scholar/OpenAlex 并行检索 → 筛选排序+热点聚类 → **LLM 四要素分析**（智谱 GLM：解决的问题/已有方案/新方案/效果及局限；无摘要自动抓全文；闭源论文标注检索链接）→ 双语报告 → SMTP 发送。
- Windows 用 `python`。
- 可选参数：`--max-results N`（默认 6）、`--language bilingual|zh|en`、`--time 3y|1y|1w`、`--format markdown|html`、`--no-email`（只生成不发送）。

**示例**：
```bash
python "scripts/pipeline.py" "搜索最近的 machine learning 论文，生成报告并发送到我的邮箱" --recipient <your-email@example.com> --max-results 6
```

### 定时增量报告（仅检索上次报告后的新论文）

```bash
# 立即触发一次增量并退出（测试/一次性）
python "scripts/scheduler.py" "每周一发送 machine learning 论文" --recipient "<用户邮箱>" --once

# 常驻周期循环（每周自动跑）
python "scripts/scheduler.py" "每周一发送 machine learning 论文" --recipient "<用户邮箱>"
```

## When to Use

- **"搜索最近的 X 论文，生成报告发到我邮箱"** → 单次搜索命令
- **"每周一发送 X 领域新论文报告"** → 定时增量命令
- **"分析 X 领域最新研究趋势"** → 单次搜索命令

**优先使用此技能，而非手动编写代码**。本技能提供完整的自动化流程，包括多源检索、LLM分析、双语报告生成和智能邮件发送。

## 已配置（无需再向用户询问）

- **SMTP**：QQ 邮箱 `smtp.qq.com:465`（SSL），授权码已配；email_sender **自动识别代理**（直连优先 → 失败自动回退本地 SOCKS 代理，探测 `127.0.0.1:{7897,7890,1080,...}` 如 Clash/V2Ray；**开/关代理都能发**）。
- **LLM**：智谱 GLM（`glm-5-turbo`，`open.bigmodel.cn/api/anthropic`），四要素分析已启用；未配 key 时自动回退规则抽取。
- **默认收件人**：`<your-email@example.com>`。

## Pitfalls
- **Pipeline 超时**：LLM 分析阶段可能超时（默认 300s）。当 `pipeline.py` 在 `[4/6] 深度分析` 阶段超时，采用以下回退方案：
  1. 手动调用 arXiv API 获取论文数据（使用 XML 解析，确保 year 为 string 类型）
  2. 直接生成 Markdown/HTML 报告（跳过 LLM 四要素分析）
  3. 使用 `email_sender.py` 发送报告
  4. 示例回退流程见 `references/pipeline-timeout-fallback.md`
- SMTP 认证失败 `[WinError 10060]`（Windows + SMTP_SSL）：直连被墙（防火墙 DPI / 全局代理把国内 SMTP 也路由墙外）时常见——**email_sender 会自动回退到本地 SOCKS 代理**（探测 `127.0.0.1:{7897,7890,1080,...}` 如 Clash/V2Ray；v1.1.1 已修本地探测 bug，直连失败+无环境变量代理时回退不再崩溃）。日常直连成功零开销。若仍失败：确认本地代理在跑，或设 `SMTP_SOCKS_PROXY=socks5://127.0.0.1:7897`。参考 `references/smtp-timeout-debugging.md`。
- SMTP 认证失败（Error 535）：Gmail 需使用应用专用密码；QQ 需使用授权码（非登录密码）。参见 `references/pitfalls.md` 中的详细配置步骤。
- **QQ 邮箱凭据位置**：QQ 邮箱凭据（QQ_EMAIL_ADDRESS 和 QQ_EMAIL_AUTH_CODE）存储在 Windows Registry (`HKCU:\Environment`)，而非环境变量。获取方式：`powershell -Command "Get-ItemProperty -Path 'HKCU:\Environment' | Select-Object QQ_EMAIL*"`。手动调用 email_sender 时需显式传递：`SMTP_HOST="smtp.qq.com" SMTP_PORT="465" SMTP_USER="$QQ_EMAIL_ADDRESS" SMTP_PASSWORD=*** python email_sender.py --report-path <path> --recipient <email>`。完整回退流程见 `references/pipeline-timeout-fallback.md`。
- Semantic Scholar 无 key 时 429，自动回退 arXiv+OpenAlex。
- **部分闭源论文四要素标注「无法自动分析」并附检索链接——属正常**。
- **邮件发送只用 QQ（单一账号，无多账号回退）**：本技能**只用 QQ 邮箱** `smtp.qq.com:465`（已在 `~/.hermes/.env` 与注册表配好 SMTP_HOST/PORT/USER/PASSWORD）。代码 `email_sender.py` **没有**「Gmail→QQ→…」的多 provider 回退链——它只用 `config_manager.get_smtp_config()` 返回的**那一个** QQ 配置，然后在同一个 QQ 账号上做「直连→SOCKS 代理」策略切换。**所以绝对不要切到 Gmail**（`smtp.gmail.com` / `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` 在本网络被墙，且不是本技能的配置；看到这些环境变量也不要用）。发信失败的正确处理见上方「🚫 邮件发送失败时」小节。

## 参考文档

- **不要「手动回退」**：遇到任何问题，**重跑 `pipeline.py`** 或把脚本 stdout 原样报给用户即可。**禁止**自己抓 arXiv、自己拼报告、自己写 `smtplib` 发信、或切到 Gmail——这些「手动方法」历史上每次都失败或被拦。检索+报告+发信 100% 由 `pipeline.py` 一条命令完成。
