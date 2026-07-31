# Agent Scholar for Hermes Agent

> Intelligent academic paper search, analysis, report generation, and email delivery system
> 智能化学术论文搜索、分析、报告生成与邮件发送系统

[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-Skill-blue)](https://hermes-agent.nousresearch.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 简介 / Overview

[English](#english-overview) | [中文](#chinese-overview)

---

## 📖 Overview / 简介

**Agent Scholar** is a fully-featured Hermes Agent Skill that automatically executes academic paper retrieval, intelligent filtering, in-depth analysis, academic report generation, and email delivery through natural language triggers.

**Agent Scholar** 是一个功能完整的 Hermes Agent Skill，能够通过自然语言触发，自动执行学术论文检索、智能筛选排序、深度分析、生成学术报告并通过邮件发送。

### Key Features / 核心功能

- 🔍 **Multi-source Search / 多数据源检索**: Supports arXiv, Semantic Scholar, OpenAlex, and other academic data sources
- 🎯 **Intelligent Filtering / 智能筛选排序**: Prioritizes highly cited papers and SCI/EI journals
- 📊 **Deep Analysis / 深度分析**: Extracts core information, innovations, and conclusions; generates APA 7th citation format
- 📄 **Report Generation / 报告生成**: Generates Markdown and HTML format academic reports
- 📧 **Email Delivery / 邮件发送**: Automatically sends reports via SMTP
- ⏰ **Scheduled Reports / 定时报告**: Supports periodic incremental reports (weekly/monthly)

---

## ✨ Features / 功能特性

### Six Core Modules / 六大核心模块

| Module / 模块 | Function / 功能 | Status / 状态 |
|------|------|------|
| **User Intent Parsing / 用户意图解析** | Parses natural language, extracts search parameters / 解析自然语言，提取检索参数 | ✅ Complete / 完成 |
| **Multi-source Search / 多数据源检索** | Parallel search across academic data sources with API rate limiting / 并行搜索多个学术数据源，处理 API 限流 | ✅ Complete / 完成 |
| **Intelligent Filtering / 智能筛选排序** | Priority ranking, hotspot clustering, quality filtering / 优先级排序、热点聚类、质量过滤 | ✅ Complete / 完成 |
| **Information Analysis / 信息提取分析** | Extracts core information, APA citations, domain-level analysis, and foundational papers; **four-element LLM analysis (Zhipu GLM, layered fallback)** / 提取核心信息、APA 引用、方向级分析与奠基论文；四要素 LLM 生成式分析（智谱 GLM，分层回退） | ✅ Complete / 完成 |
| **Report Generation / 报告生成** | 4-section MD/HTML, bilingual, hotspot clustering, per-paper overview, four-element excerpts (problem/existing/new/limitations), research trends / 四段式 MD/HTML、双语、热点聚类、速览逐篇概述、单篇四要素摘录（问题/现有方案/新方案/效果及局限）、研究趋势 | ✅ Complete / 完成 |

> 🌐 **报告语言控制 / Report language control**: 四要素 LLM 分析严格跟随 `intent.language`（`--language bilingual|zh|en`）——bilingual 时**每个要素都中英两段**（中文段+英文段），zh=纯中文，en=纯英文；骨架标签始终双语。论文标题/摘要保留英文原文（学术惯例）。/ The four-element LLM analysis strictly follows `intent.language`: bilingual → **each element has both a Chinese and an English segment**; zh = Chinese only; en = English only. Skeleton labels are always bilingual. Paper titles/abstracts stay in the original English.
| **Email Delivery / 邮件发送** | SMTP/SSL with attachments, retry, connection test; **auto-detect proxy (direct→SOCKS fallback, works whether proxy on/off)** / SMTP/SSL 发送报告附件、重试、连接测试；**自动识别代理**（直连→SOCKS 回退，开/关代理都能发） | ✅ Complete / 完成 |

### Supported Data Sources / 支持的数据源

| Data Source / 数据源 | Type / 类型 | API Limit / API 限制 | Status / 状态 |
|--------|------|----------|------|
| [arXiv](https://arxiv.org/) | Preprints / 预印本 | No limit / 无限制 | ✅ Integrated · Latest research / 已接入 · 最新研究成果 |
| [Semantic Scholar](https://www.semanticscholar.org/) | Comprehensive / 综合学术 | 5000/day / 5000次/天 | ✅ Integrated · AI-driven academic search / 已接入 · AI 驱动学术搜索 |
| [OpenAlex](https://openalex.org/) | Open Index / 开放索引 | No limit / 无限制 | ✅ Integrated · Open scholarly metadata / 已接入 · 开放学术元数据 |
| [CrossRef](https://www.crossref.org/) | Bibliographic Metadata / 文献元数据 | 10/sec / 10次/秒 | ⏳ Reserved / 预留（rate_limiter configured, Searcher not integrated / rate_limiter 已配置，Searcher 未接入） |
| PubMed | Biomedical / 生物医学 | 3/sec / 3次/秒 | ⏳ Reserved / 预留（同上 / same above） |

---

## 🚀 Quick Start / 快速开始

### Requirements / 环境要求

- **Python**: 3.8 or higher / 3.8 或更高版本
- **Hermes Agent**: Latest version / 最新版本
- **OS**: Linux, macOS, or Windows / Linux、macOS 或 Windows

### Installation Steps / 安装步骤

#### 1. Install Hermes Agent / 安装 Hermes Agent

```bash
pip install hermes-agent
```

#### 2. Install This Skill / 安装本技能

```bash
# Clone project / 克隆项目
git clone https://github.com/your-username/agent-scholar-2.0.git
cd agent-scholar-2.0

# Install dependencies / 安装依赖
pip install -r agent-scholar/requirements.txt

# Install skill to Hermes / 安装技能到 Hermes
cp -r agent-scholar ~/.hermes/skills/academic-report
```

#### 3. Configure Environment Variables / 配置环境变量

```bash
# Copy environment template / 复制环境变量模板
cp agent-scholar/config/env.example ~/.hermes/.env

# Edit ~/.hermes/.env, add required config / 编辑 ~/.hermes/.env，添加必需配置
# Required: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
# 必需：SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

#### 4. Configure Hermes / 配置 Hermes

```bash
hermes config set skills.config.academic.default_language bilingual
hermes config set skills.config.academic.max_results 50
hermes config set skills.config.academic.email_recipient your@email.com
```

---

## ⚙️ Configuration / 配置说明

### Required Configuration / 必需配置

#### SMTP Email Configuration / SMTP 邮件配置

For sending academic report emails / 用于发送学术报告邮件。

**配置位置 / Where to configure**: `~/.hermes/.env`（推荐只在这里配，避免与环境变量冲突 / recommended: configure here only, avoid env-var conflict）

```bash
# QQ 邮箱（推荐，国内直连可用）/ QQ Mail (recommended, direct in China)
SMTP_HOST=smtp.qq.com
SMTP_PORT=465                      # 465=SSL（隐式）；587=STARTTLS / 465=SSL implicit; 587=STARTTLS
SMTP_USER=your_qq@qq.com           # 完整 QQ 邮箱地址（不是 QQ 号）/ full QQ email (not QQ number)
SMTP_PASSWORD=xxxxxxxxxxxxxxxx      # QQ「授权码」16 位，不是登录密码！/ QQ auth code (16-char), NOT login password

# Gmail（国内通常需代理）/ Gmail (usually needs a proxy in China)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your@gmail.com
# SMTP_PASSWORD=your-16-char-app-password
```

**如何获取 QQ 授权码 / How to get a QQ auth code**:
1. 登录 [mail.qq.com](https://mail.qq.com) → **设置 → 账户** / Login → **Settings → Account**
2. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务」→ 点 **开启** POP3/SMTP 服务 / Find the section → **Enable** POP3/SMTP service
3. 按提示发短信验证 → 生成 **16 位授权码** / SMS verify → generate the **16-char authorization code**
4. 把这 16 位填进 `SMTP_PASSWORD` / Put it in `SMTP_PASSWORD`

> ⚠️ **授权码 ≠ 登录密码**：授权码是独立的 16 位字符串，专给第三方 SMTP 客户端用。 / The auth code is **NOT** your login password — it's a separate 16-char string for third-party SMTP clients.

**授权码何时会失效 / When an auth code stops working**:
- ✅ **不会自动过期**（生成后长期有效）/ Does **NOT** auto-expire — valid long-term once generated.
- ❌ 在 QQ 邮箱里**重新生成新授权码** → 旧码**立即失效**（最常见原因）/ Regenerating a new code **invalidates the old one** (most common cause).
- ❌ **修改 QQ 账号登录密码** / **账号安全验证/异常** → 可能让授权码失效 / Changing your QQ login password, or a QQ security review, can invalidate it.
- ❌ 关闭 POP3/SMTP 服务 → 授权码停用 / Disabling POP3/SMTP service disables the code.
- ⏳ **登录过于频繁** → QQ 会**临时**返回 `535`（限频，非永久失效，几分钟自动恢复）/ Too-rapid logins make QQ **temporarily** return `535` (throttle, not permanent — clears in minutes).

**配置优先级（重要！改了不生效多半是这里）/ Config precedence (important — changes not taking effect? check this)**:

```
系统环境变量 (OS env, e.g. Windows 用户变量)  >  ~/.hermes/.env  >  代码默认值
```

若你在 **Windows 用户环境变量**里设过 `SMTP_*`，它会**覆盖** `.env`！改了 `.env` 却没效果，多半是系统环境变量在抢先生效。清掉它： / If you've set `SMTP_*` in your **OS user environment** (e.g. Windows User vars), it **overrides** `.env`. If `.env` edits don't take effect, a stale OS env var is winning — clear it:

```bash
unset SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD        # 当前 shell / current shell
# Windows 永久清除 / Windows permanent:
#   控制面板 → 用户环境变量 → 删除 SMTP_*  （或 `setx SMTP_PASSWORD ""` 后重开终端）
#   Control Panel → User env vars → delete SMTP_*  (or `setx SMTP_PASSWORD ""` then reopen terminal)
```

> 💡 **建议只在一个地方配置**（推荐 `~/.hermes/.env`），避免「环境变量 vs .env」双源漂移导致排查困惑。 / Configure in **ONE place** (recommend `~/.hermes/.env`) to avoid two-source drift.

**收件人 / Recipient**: 配在 `~/.hermes/config.yaml`（非敏感）/ in `~/.hermes/config.yaml` (non-secret):

```yaml
skills:
  config:
    academic:
      email_recipient: "your@email.com"
```

> `config_manager` 启动时**自动加载** `~/.hermes/.env`（仅在对应环境变量未设置时填充），无需手动 `export`；每次运行重新读取，改完即生效。 / `config_manager` **auto-loads** `~/.hermes/.env` on startup (only fills env vars that aren't already set) — no manual `export`; re-read every run, so changes take effect immediately.

**Gmail 应用专用密码 / Gmail app password**: https://myaccount.google.com/apppasswords → 生成 16 位 → 填入 `SMTP_PASSWORD`。 / Generate a 16-char app password → put in `SMTP_PASSWORD`.

#### Hermes Configuration / Hermes 配置

```yaml
# ~/.hermes/config.yaml
skills:
  config:
    academic:
      default_language: bilingual      # en/zh/bilingual
      default_time_range: 3y           # 1y/3y/all
      max_results: 50                  # Max results per data source / 每个数据源最大结果数
      email_recipient: user@example.com
      include_preprints: true
      filter_highly_cited: false
      highly_cited_threshold: 100
      sci_ei_only: false
```

### Optional Configuration / 可选配置

#### API Keys (Optional) / API 密钥（可选）

To increase API rate limits / 提升 API 限流限制。

```bash
# ~/.hermes/.env
ARXIV_API_KEY=your-arxiv-key
SEMANTIC_SCHOLAR_API_KEY=your-s2s-key
```

---

## 📖 Usage / 使用方法

### Single Search Mode / 单次搜索模式

Generate a complete academic report for a specified time period / 生成指定时间内的完整学术报告。

```bash
hermes chat -q "/academic-report 搜索最近的深度学习论文"
```

**Run full pipeline directly** (bypass Hermes, for debugging/integration) / **直接跑全链路**（不经 Hermes，便于调试/集成）：

```bash
cd agent-scholar/scripts
python pipeline.py "搜索最近的 machine learning 论文，生成报告并发送到我的邮箱" --max-results 8
# Optional parameters / 可选参数：--language bilingual|zh|en  --time 3y|1y|1w  --recipient a@b.com
#          --format markdown|html  --no-email (generate only, no send / 只生成不发送)
```

> One command completes: intent parsing → multi-source search → filtering & ranking → in-depth analysis → report generation → email delivery.
>
> 一条命令跑完：意图解析 → 多源检索 → 筛选排序 → 深度分析 → 报告生成 → 邮件发送。
>
> Verified: QQ Mail (`smtp.qq.com:465`) sends successfully (QQ→QQ, QQ→Gmail verified).
>
> 实测：QQ 邮箱(`smtp.qq.com:465`)真实发送成功（QQ→QQ、QQ→Gmail 均已验证）。
>
> **Proxy-agnostic / 代理无关**: Strategy chain `direct → SMTP_SOCKS_PROXY/ALL_PROXY → local SOCKS port probe`. Domestic SMTP (QQ) hits direct (works whether proxy on/off); direct-blocked (e.g., Gmail) auto-fallbacks via Clash proxy—no manual proxy switching needed.
>
> 代理无关：策略链 `direct → SMTP_SOCKS_PROXY/ALL_PROXY → 本地 SOCKS 端口探测`。国内 SMTP(QQ) 直连命中（代理开/关都行）；直连被墙(如 Gmail)自动经 Clash 等代理回退——无需手动切换代理。

**Example Inputs / 示例输入**：
- "搜索最近的机器学习论文" / "Search recent machine learning papers"
- "查找关于GPT的最新研究，近1年" / "Find latest GPT research, past 1 year"
- "检索高被引的计算机视觉论文，SCI期刊，近3年" / "Retrieve highly cited computer vision papers, SCI journals, past 3 years"

### Scheduled Report Mode (Incremental) / 定时报告模式（增量）

Periodically send **incremental** academic reports—each run retrieves only papers updated between「last report time → now」. State persisted in `~/.hermes/academic_scholar_timestamps.json` (one timestamp per topic).

周期性发送**增量**学术报告——每次仅检索「上次报告时间 → 现在」之间更新的论文。状态持久化在 `~/.hermes/academic_scholar_timestamps.json`（每个主题一个时间戳）。

```bash
cd agent-scholar/scripts

# In-process scheduled loop (parses period phrase, triggers immediately once to build baseline, then runs incrementally by period)
# 进程内定时循环（解析周期短语，立即首次触发建基线，之后按周期跑增量）
python scheduler.py "每周一发送 machine learning 论文" --recipient your@email.com

# Test: trigger one incremental run and exit / 测试：立即触发一次增量并退出
python scheduler.py "每周发送 NLP 报告" --once --recipient your@email.com

# Dry-run: only print period/next trigger time, don't run / 预演：只打印周期/下次触发时间，不运行
python scheduler.py "每月综述" --dry-run

# Run incremental directly (without scheduler) / 直接跑一次增量（不经调度器）
python pipeline.py "每周一发送 machine learning 论文" --incremental --recipient your@email.com

# Optional cron: requires `pip install croniter` first, then use standard 5-field cron / 可选 cron：需先 pip install croniter，再用标准 5 字段 cron
python scheduler.py "每周报告" --cron "0 9 * * 1" --recipient your@email.com

# View/reset timestamps / 查看/重置时间戳
python timestamp_manager.py            # View all topics' last report times
python timestamp_manager.py --reset all
```

**Single Search vs Scheduled Incremental / 单次搜索 vs 定时增量**：

| Dimension / 维度 | Single Search / 单次搜索 | Scheduled Incremental / 定时增量 |
|---|---|---|
| Trigger / 触发 | `pipeline.py` one-time / 一次性 | `scheduler.py` loop / `--incremental` |
| Time Window / 时间窗口 | User-specified (past 1 year/3 years…) / 用户指定（近1年/3年…） | `[last report, now]` / `[上次报告, 现在]`；first=period length / 首次=周期长度 |
| Paper Scope / 论文范围 | All in window / 窗口内全部 | Only new papers since last report / 仅上次报告后的新论文 |
| State / 状态 | None / 无 | `~/.hermes/academic_scholar_timestamps.json` |
| Report / 报告 | Complete landscape / 完整 landscape | Title marked "Incremental / 增量 (since …)" / 标题标「增量 / Incremental (since …)」 |
| Timestamp Update / 时间戳更新 | Never / 从不 | Only after successful email send / 仅邮件发送成功后 |

**Supported Periods / 支持的周期**: "每周一/每周/每两周/每个月/每天/每N天" + `weekly/monthly/daily/biweekly`.
**Empty Incremental / 空增量**: Default skips email and doesn't update timestamp when no new papers in current period (`--send-empty` forces notification). / 默认跳过邮件且不更新时间戳（`--send-empty` 可强制通知）。
**Known Limits / 已知限制**: Semantic Scholar filters by year only + `Paper` stores year only, client-side can only filter by year as fallback, papers in same year's early period may leak in; single-process scheduling (don't run multiple for same topic). / Semantic Scholar 仅按年过滤 + `Paper` 仅存年份，客户端只能按年兜底过滤，同年初段的论文可能漏入；单进程调度（同主题勿多开）。

### Command Line Options / 命令行选项

```bash
# View skill status / 查看技能状态
/skills

# Test email configuration / 测试邮件配置
python ~/.hermes/skills/academic-report/scripts/email_sender.py --test

# View configuration / 查看配置
hermes config show | grep academic
```

---

## 📂 Project Structure / 项目结构

```
agent-scholar/
├── SKILL.md                    # Skill definition / 技能主定义文件
├── requirements.txt             # Python dependencies / Python 依赖
├── config/                      # Configuration templates / 配置模板
│   ├── config.example.yaml
│   └── env.example
├── scripts/                     # Core modules / 核心功能模块
│   ├── __init__.py
│   ├── utils.py                # Data models and utilities / 数据模型和工具
│   ├── config_manager.py       # Configuration management / 配置管理
│   ├── rate_limiter.py         # API rate limiting / API 限流处理
│   ├── intent_parser.py        # User intent parsing ✅ / 用户意图解析
│   ├── paper_search.py         # Multi-source search ✅ / 多数据源检索
│   ├── paper_filter.py         # Filtering & ranking ✅ / 筛选排序/热点聚类
│   ├── paper_analyzer.py       # Information analysis ✅ / 信息分析/整体分析/奠基论文
│   ├── report_generator.py     # Report generation (MD/HTML/bilingual) ✅ / 报告生成
│   ├── email_sender.py         # Email delivery (SMTP/SSL) ✅ / 邮件发送
│   ├── pipeline.py             # Full pipeline + incremental branch ✅ / 全链路编排 + 增量分支
│   ├── timestamp_manager.py    # Scheduled report timestamps (incremental window) ✅ / 定时报告时间戳
│   ├── scheduler.py            # Scheduled report scheduler (in-process) ✅ / 定时报告调度器
│   └── llm_analyzer.py         # Four-element LLM analysis (Zhipu GLM, layered fallback) ✅ / 四要素 LLM 分析
├── templates/                  # Report templates / 报告模板
│   └── report_html_template.html  ✅
└── reports/                    # Generated reports — runtime, gitignored / 运行时生成（已 gitignore）
```

> 仓库根还有：`docs/`（`design-init.txt` 原始需求、`agent-scholar skill实施计划.md` 详细实施计划、`报告格式设计.md` 报告规范、`v1.0_vs_v2.0_对比.md` 迭代复盘、`notes/` 设计笔记）、`examples/`（真实报告样本）、`作品展示/`（求职/科研作品集）、`test/`（308 项 pytest）。

**Status Legend / 状态说明**：
- ✅ Complete / 已完成
- ⏳ Pending / 待实现
- 🔴 High Priority / 高优先级
- 🟡 Medium Priority / 中优先级
- 🟢 Low Priority / 低优先级

---

## 🛠️ Development Status / 开发状态

### Current Progress / 当前进度

- [x] **Documentation Consolidation (2026-07-31)**: repo reorg — design/plan/report files consolidated under `docs/` & `docs/notes/`; README skill name aligned to `academic-report` (matches `name:` field); test counts corrected to **308**; project-structure block fixed (removed non-existent `references/` + `report_template.md`, noted `reports/` as gitignored); 作品展示 sample-report links repointed to `examples/`; source `SKILL.md` switched to portable relative paths. / 文档整理（2026-07-31）：目录重组——设计/计划/报告文件归入 `docs/` 与 `docs/notes/`；README 技能名对齐 `academic-report`（与 `name:` 字段一致）；测试数校正为 **308**；项目结构块修正（删除不存在的 `references/` + `report_template.md`，标注 `reports/` 为 gitignore）；作品展示 报告样本链接改指 `examples/`；源码 `SKILL.md` 改可移植相对路径。

- [x] **Implementation Audit Fixes (2026-07-14, vs docs/design-init.txt)**: latest_research dead feature→recent bonus; CrossRef/PubMed doc alignment (reserved); APA 7th author format (≤20 list all />20 ellipsis+Oxford comma); parse_date_range supports absolute date range+calendar precision; value_application orphan field→render. Known limits (cross-language search, core default, paper type filter, incremental year precision) see [docs/报告格式设计.md §13](docs/报告格式设计.md). 308 tests passing. / 实现审计修复（2026-07-14，对照 docs/design-init.txt）：latest_research 死特性→近期加分；CrossRef/PubMed 文档对齐（预留）；APA 7th 作者格式（≤20 全列/>20 省略号+Oxford 逗号）；parse_date_range 支持绝对日期区间+日历精确；value_application 孤儿字段→渲染。已知限制（跨语言检索、核心默认、文献类型筛选、增量年精度）见docs/报告格式设计.md §13。全量 308 项测试通过。

- [x] **Phase 1**: Project Initialization (Complete) / 项目初始化（完成）
  - [x] Directory structure creation / 目录结构创建
  - [x] SKILL.md definition / SKILL.md 定义
  - [x] Basic framework implementation / 基础框架实现
  - [x] Configuration module / 配置管理模块
  
- [x] **Phase 2**: Core Feature Implementation (Complete) / 核心功能实现（完成）
  - [x] Paper search module ✅ / 论文搜索模块 ✅
  - [x] Paper filter module ✅ (time safety net / quality filtering / priority ranking / hotspot clustering / hotspot intro, 26 tests passing / 文献筛选模块 ✅（时间安全网/质量过滤/优先级排序/热点聚类/热点介绍，26 项测试通过）
  - [x] Paper analysis module ✅ (structured extraction/APA/domain-level analysis/foundational papers via real S2 References API; AbstractSummarizer layered condensation (S2 tldr→enhanced rules); innovation renders by language, 41 tests passing / 信息分析模块 ✅（结构化提取/APA/方向级整体分析/奠基论文真实 S2 API 查找；AbstractSummarizer 分层浓缩(S2 tldr→增强规则)、创新点按语言渲染，41 项测试通过）
  
- [x] **Phase 3**: Report Generation ✅ / 报告生成 ✅
  - [x] Report generator (4-section MD/HTML, bilingual default, per-paper overview by hotspot, four-element excerpts per paper: problem/existing/new/limitations, trend derivation) / 报告生成器（四段式 MD/HTML、双语默认、速览按热点逐篇概述、单篇块四要素摘录：解决的问题/现有方案/新方案/效果及局限、趋势语料派生）
  - [x] HTML template creation (templates/report_html_template.html) / HTML 模板创建
  - [x] HTML conversion (21 tests + end-to-end smoke test passing / HTML 转换（21 项测试 + 端到端烟雾测试通过）
  
- [x] **Phase 4**: Email Delivery ✅ / 邮件发送 ✅
  - [x] SMTP email delivery (SSL/TLS branching, HTML body+attachment, retry, connection test, 42 tests incl. proxy auto-detect, local-SOCKS-probe regression, send-log, cooldown guard / SMTP 邮件发送（SSL/TLS 分流、HTML 正文+附件、重试、连接测试，42 项测试含代理自动识别 + 本地 SOCKS 探测回归 + 发送日志 + 冷却守卫）
  - [x] Scheduled task management ✅ (`timestamp_manager.py` per-topic timestamps + `scheduler.py` in-process incremental scheduler; client-side year fallback filtering / 定时任务管理 ✅（`timestamp_manager.py` 每主题时间戳 + `scheduler.py` 进程内定时增量；客户端年份兜底过滤）
  
- [x] **Phase 5**: Testing & Verification (Complete, **308 tests** total) / 测试验证（完成，合计 **308 项**）
  - [x] config_manager.py tests ✅ (5 tests; including ~/.hermes/.env auto-loading / 5 项；含 ~/.hermes/.env 自动加载)
  - [x] paper_search.py tests ✅ (36 tests; including OpenAlex abstract reconstruction, S2 tldr parsing, doi/null handling, arXiv date, dedup regression / 36 项；含 OpenAlex 摘要重建、S2 tldr 解析、doi/null、arXiv 日期、去重回归)
  - [x] paper_filter.py tests ✅ (28 tests / 28 项)
  - [x] paper_analyzer.py tests ✅ (53 tests / 53 项)
  - [x] report_generator.py tests ✅ (25 tests + end-to-end smoke test / 25 项 + 端到端烟雾测试)
  - [x] email_sender.py tests ✅ (43 tests: proxy detect/fallback + local-SOCKS-probe regression + send-log + cooldown guard / 43 项：代理识别/回退 + 本地 SOCKS 探测回归 + 发送日志 + 冷却守卫)
  - [x] End-to-end experiments ✅ (test/experiments/, 12 scenarios all passing / 端到端实验 ✅（12 场景全通过）
  - [x] Full pipeline integration test ✅ (pipeline.py: search→filter→analyze→report→email, QQ real send success / 全链路集成测试 ✅（检索→筛选→分析→报告→邮件，QQ 真实发送成功）)
  - [x] Documentation sync / 文档同步

### Estimated Completion Time / 预计完成时间

- **Core Features / 核心功能**: 2-3 weeks / 2-3 周
- **Testing & Optimization / 测试优化**: 1 week / 1 周
- **Total / 总计**: ~3-4 weeks / 约 3-4 周

---

## 🧪 Testing / 测试

### Environment Tests / 环境测试

```bash
# Test Python environment / 测试 Python 环境
python3 --version

# Test dependency installation / 测试依赖安装
pip list | grep -E "arxiv|scholarly|jinja2"

# Test Hermes Agent / 测试 Hermes Agent
hermes chat -q "List all skills" / 列出所有技能
```

### Function Tests / 功能测试

```bash
# Test basic search / 测试基本搜索
hermes chat -q "/academic-report 搜索机器学习论文"

# Test email configuration / 测试邮件配置
python3 agent-scholar/scripts/email_sender.py --test

# Test complete workflow (requires all modules) / 测试完整流程（需要完成所有模块）
hermes chat -q "/academic-report 搜索深度学习论文，生成报告并发送到我的邮箱"
```

---

## 📝 Report Format / 报告格式

Generated academic reports follow the [`docs/报告格式设计.md`](docs/报告格式设计.md) specification / 生成的学术报告遵循 [`docs/报告格式设计.md`](docs/报告格式设计.md) 规范。

### Report Structure / 报告结构

1. **Title + Time / 标题 + 时间**: `Time range + field/topic + Report` (e.g., `2023-2025 Statistics Research Report`), with small-font note of report generation time and coverage time / `时间范围 + 领域/主题 + 报告`，小字标注报告生成时间与涵盖时间
2. **I. Report Overview / 一、报告速览**: Grouped by hotspot, per-paper overview of each paper's core content (covers every paper) / 按热点分组、逐篇概述每篇论文的核心内容（覆盖每一篇论文）
3. **II. Classified Paper Display / 二、分类论文展示**: Papers clustered by "hotspot" / 按"热点"聚类展示论文
   - Hotspot name + topic introduction / 热点名称 + 主题介绍
   - Per paper: title, authors, publication time, venue, citation count, DOI / 每篇论文：标题、作者、发表时间、发表期刊、引用量、DOI
   - Four-element excerpt: problem / existing approach (citing prior work) / new approach / results & limitations (excerpted from abstract; all-empty fallback to full Abstract) / 四要素摘录：解决的问题 / 现有方案（引用先前工作）/ 新方案 / 效果及局限性（从摘要摘录语段；全空回退完整 Abstract）
   - Overall analysis (synthesizes all papers in this hotspot into a domain-level analysis) / 整体分析（综合本热点论文的方向性分析）
   - Foundational reference papers (past foundational work in this direction) / 奠基性参考论文（该方向过往奠基性工作）
   - APA 7th citation format / APA 7th 引用格式
4. **III. Research Trends / 三、研究趋势**: ~200 words, future research trends and research gap analysis / 约 200 字，未来研究趋势与研究缺口分析

### Output Formats / 输出格式

- **Markdown**: Default format, easy for editing and version control / 默认格式，便于编辑和版本控制
- **HTML**: Styled web format, suitable for sharing and presentation / 带样式的网页格式，适合分享和展示

---

## 🤝 Contributing / 贡献

Contributions are welcome! Please report issues or suggest improvements! / 欢迎贡献代码、报告问题或提出改进建议！

### How to Contribute / 贡献方式

1. Fork this project / Fork 本项目
2. Create a feature branch / 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. Commit changes / 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch / 推送到分支 (`git push origin feature/AmazingFeature`)
5. Open a Pull Request / 开启 Pull Request

### Development Guidelines / 开发规范

- Follow PEP 8 code style / 遵循 PEP 8 代码规范
- Add unit tests / 添加单元测试
- Update relevant documentation / 更新相关文档
- Keep code clean and readable / 保持代码简洁和可读性

---

## 📚 Related Resources / 相关资源

- [Hermes Agent Official Documentation / Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs/)
- [Hermes Agent GitHub / Hermes Agent GitHub](https://github.com/NousResearch/hermes-agent)
- [SKILL.md Specification / SKILL.md 规范](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills)
- [Implementation Plan / 实施计划文档](docs/agent-scholar%20skill实施计划.md)
- [Portfolio / 作品展示](作品展示/README.md) — 求职/科研申请作品集(技术文档、Demo 脚本、使用案例、性能评估、对比表格)

---

## ❓ FAQ / 常见问题

### Q: What languages are supported for papers? / 支持哪些语言的论文？

**A**: Supports English, Chinese, and bilingual search. Configure via `default_language`. / 支持英文、中文和双语检索。可通过配置 `default_language` 设置。

### Q: How to increase paper retrieval quantity? / 如何提高论文检索量？

**A**: Adjust the `max_results` configuration item. Default is 50 per data source. / 调整 `max_results` 配置项，默认为每个数据源 50 篇。

### Q: What if email sending fails? / 邮件发送失败怎么办？

**A**:
1. Check if SMTP configuration is correct / 检查 SMTP 配置是否正确
2. Gmail requires app-specific passwords / Gmail 需要使用应用专用密码
3. Check log files for detailed error messages / 查看日志文件获取详细错误信息
4. **SMTP timeout `[WinError 10060]` / SMTP 连接超时**：直连被墙（防火墙 DPI / 全局代理把国内 SMTP 也路由到墙外）时属正常——`email_sender` 会**自动回退**到本地 SOCKS 代理（探测 `127.0.0.1:{7897,7890,1080,...}`，如 Clash/V2Ray）。若仍失败：确认本地代理在跑、或显式设 `SMTP_SOCKS_PROXY=socks5://127.0.0.1:7897`。可用 `python scripts/email_sender.py --test` 单独排查（日志打印策略链与命中策略）。/ Direct connection blocked (firewall DPI / global proxy routing domestic SMTP abroad) is expected — `email_sender` **auto-falls-back** to a local SOCKS proxy (probes `127.0.0.1:{7897,7890,1080,...}`, e.g. Clash/V2Ray). If still failing: ensure the local proxy is running, or set `SMTP_SOCKS_PROXY=socks5://127.0.0.1:7897` explicitly. Run `python scripts/email_sender.py --test` to isolate (logs print the strategy chain and the hit strategy).
   - **历史根因（v1.1.1 已修，2026-07-21）**：本地 SOCKS 端口探测曾误用 `socket` 类的 `create_connection`（实为模块函数），导致直连失败且无环境变量代理时兜底探测抛 `AttributeError`、回退彻底无法启动。已改用模块级 `_REAL_CREATE_CONNECTION`，回归测试 `TestAutoLocalSocksProbe` 锁死。/ **Historical root cause (fixed in v1.1.1, 2026-07-21)**: the local-SOCKS port probe mistakenly called `create_connection` on the `socket` *class* (it's a module function), so when direct failed with no env-var proxy the fallback crashed with `AttributeError` and email always failed. Fixed to use the module-level `_REAL_CREATE_CONNECTION`; regression-locked by `TestAutoLocalSocksProbe`.
5. **看到「发送冷却中」属正常**（v1.3.0）：认证失败（含 QQ 登录限频的假性 535）后，`email_sender` 会**指数退避冷却**（30→60→120→300s）并自动拒发（不再登录 QQ，避免轰炸加重限频）。等待冷却结束或设 `EMAIL_SKIP_COOLDOWN=1` 手动强制。每次发送（成功/失败/冷却）都记录在 `~/.hermes/email_sends.jsonl`，`tail` 即可排查。/ **"In cooldown" is expected** (v1.3.0): after an auth failure (incl. QQ throttle's false 535), `email_sender` **backs off exponentially** (30→60→120→300s) and auto-skips sending (no QQ login, to avoid deepening the throttle). Wait it out, or set `EMAIL_SKIP_COOLDOWN=1` to force. Every attempt (success/fail/cooldown) is logged to `~/.hermes/email_sends.jsonl` — `tail` it to diagnose.

### Q: How to disable preprints? / 如何禁用预印本？

**A**: Set `include_preprints: false` in config.yaml. / 设置 `include_preprints: false` 在 config.yaml 中。

### Q: How to configure scheduled reports? / 定时报告如何配置？

**A**: Use the standalone scheduler `python scheduler.py "每周一发送X领域论文" --recipient your@email.com` (in-process incremental scheduler, no Hermes dependency); or single incremental run `python pipeline.py "..." --incremental`. Optional cron: run `pip install croniter` first, then use `--cron "0 9 * * 1"`. / 用独立调度器 `python scheduler.py "每周一发送X领域论文" --recipient your@email.com`（进程内定时增量，不依赖 Hermes）；或单次增量 `python pipeline.py "..." --incremental`。可选 `pip install croniter` 后用 `--cron "0 9 * * 1"`。

---

## 📄 License / 许可证

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details. / 本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👥 Authors / 作者

Agent Scholar Team

---

## 🙏 Acknowledgments / 致谢

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) - Powerful AI Agent framework / 强大的 AI Agent 框架
- [arXiv](https://arxiv.org/) - Open access academic paper preprints / 开放获取的学术论文预印本
- [Semantic Scholar](https://www.semanticscholar.org/) - AI-driven academic search / AI 驱动的学术搜索
- [OpenAlex](https://openalex.org/) - Open scholarly index / 开放的学术索引

---

## 📮 Contact / 联系方式

- Issue Feedback / 问题反馈: [GitHub Issues](https://github.com/your-username/agent-scholar-2.0/issues)
- Email / 邮件联系: agent-scholar@example.com

---

**Last Updated / 最后更新**: 2026-07-31

**Version / 版本**: 1.3.0（v1.3.0 增冷却守卫 + 发送记录日志；v1.2.1 修本地 SOCKS 探测 bug —— 7 月 21 日邮件失败根因 / v1.3.0 cooldown guard + send log; v1.2.1 fix local-SOCKS-probe bug; 2026-07-31 docs consolidation & repo reorg）
