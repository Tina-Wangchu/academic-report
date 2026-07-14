---
name: academic-scholar
description: Academic paper search, analysis, and report generation with intelligent filtering, LLM four-element analysis, and email delivery
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

## ⚠️ CRITICAL — 必须按下方命令执行，禁止自行实现

**执行本技能时，你必须用 `terminal` 工具运行 `pipeline.py`（或定时用 `scheduler.py`）这一条命令完成全部工作。**

**严禁**：自行检索论文、自行撰写报告、自行调用邮件工具、用浏览器爬 arXiv——这些全部由脚本内部完成。
**你的唯一职责**：运行下方命令 → 把脚本 stdout（各阶段进度 + 「邮件发送 成功/失败」）原样汇报给用户。**不要**自己生成报告内容，**不要**自己发邮件。

> 重要：本环境**未设置 `$HERMES_SKILL_DIR`**，因此下方命令已写成**绝对路径**——必须原样使用，不要替换为 `$HERMES_SKILL_DIR/...`（那样会找不到文件导致整条链路失败）。

### 单次搜索（一条命令 = 检索 + LLM 四要素 + 报告 + 发邮件）

```bash
python "C:/Users/lanpi/AppData/Local/hermes/skills/research/academic-scholar/scripts/pipeline.py" "<用户的检索请求原话>" --recipient "<用户邮箱>"
```

- `<用户邮箱>`：默认用已配置的收件人 `tinawangchu0615@gmail.com`（也可在命令里用 `--recipient` 指定，或问用户）。
- 脚本内部完成：意图解析 → arXiv/Semantic Scholar/OpenAlex 并行检索 → 筛选排序+热点聚类 → **LLM 四要素分析**（智谱 GLM：解决的问题/已有方案/新方案/效果及局限；无摘要自动抓全文；闭源论文标注检索链接）→ 双语报告 → SMTP 发送。
- Windows 用 `python`。
- 可选参数：`--max-results N`（默认 6）、`--language bilingual|zh|en`、`--time 3y|1y|1w`、`--format markdown|html`、`--no-email`（只生成不发送）。

**示例**：
```bash
python "C:/Users/lanpi/AppData/Local/hermes/skills/research/academic-scholar/scripts/pipeline.py" "搜索最近的 machine learning 论文，生成报告并发送到我的邮箱" --recipient tinawangchu0615@gmail.com --max-results 6
```

### 定时增量报告（仅检索上次报告后的新论文）

```bash
# 立即触发一次增量并退出（测试/一次性）
python "C:/Users/lanpi/AppData/Local/hermes/skills/research/academic-scholar/scripts/scheduler.py" "每周一发送 machine learning 论文" --recipient "<用户邮箱>" --once

# 常驻周期循环（每周自动跑）
python "C:/Users/lanpi/AppData/Local/hermes/skills/research/academic-scholar/scripts/scheduler.py" "每周一发送 machine learning 论文" --recipient "<用户邮箱>"
```

## When to Use

- "搜索最近的 X 论文，生成报告发到我邮箱" → 单次搜索命令
- "每周一发送 X 领域新论文报告" → 定时增量命令
- "分析 X 领域最新研究趋势" → 单次搜索命令

## 已配置（无需再向用户询问）

- **SMTP**：QQ 邮箱 `smtp.qq.com:465`（SSL），授权码已配；email_sender 强制绕过 SOCKS 代理直连。
- **LLM**：智谱 GLM（`glm-5-turbo`，`open.bigmodel.cn/api/anthropic`），四要素分析已启用；未配 key 时自动回退规则抽取。
- **默认收件人**：`tinawangchu0615@gmail.com`。

## Pitfalls

- 邮件超时：本技能已强制 SMTP 直连（绕过 SOCKS）；若仍失败，检查本地网络/防火墙对 465 的拦截。
- Semantic Scholar 无 key 时 429，自动回退 arXiv+OpenAlex。
- 部分闭源论文四要素标注「无法自动分析」并附检索链接——属正常。
