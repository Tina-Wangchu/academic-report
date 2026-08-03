# Academic Report

> Intelligent academic paper search, analysis, report generation, and email delivery system
> 智能化学术论文搜索、分析、报告生成与邮件发送系统

[![Platform](https://img.shields.io/badge/Platform-Agnostic-blueviolet)](#)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 简介 / Overview

[English](#english-overview) | [中文](#chinese-overview)

---

## 📖 Overview / 简介

**Academic Report** is a fully-featured, **platform-agnostic AI Agent skill** (works with Claude, Codex, and any agent runtime — no Hermes dependency) that automatically executes academic paper retrieval, intelligent filtering, in-depth analysis, academic report generation, and email delivery through natural language triggers.

**Academic Report** 是一个功能完整的**平台无关 AI Agent 技能**（可用于 Claude、Codex 等任意 Agent 运行环境，不依赖 Hermes），能够通过自然语言触发，自动执行学术论文检索、智能筛选排序、深度分析、生成学术报告并通过邮件发送。

### Key Features / 核心功能

- 🔍 **Multi-source Search / 多数据源检索**: Supports arXiv, Semantic Scholar, OpenAlex, and other academic data sources
- 🎯 **Intelligent Filtering / 智能筛选排序**: Prioritizes highly cited papers and SCI/EI journals
- 📊 **Deep Analysis / 深度分析**: Extracts core information, innovations, and conclusions; generates APA 7th citation format
- 📄 **Report Generation / 报告生成**: Generates Markdown and HTML format academic reports
- 📧 **Email Delivery / 邮件发送**: Automatically sends reports via SMTP

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

## 📦 仓库结构 / Repository Structure（部署前先看 / Read this first）

本仓库是**开发工作区**——包含 skill 本体 + 设计文档 + 测试。**实际部署只需要内层的 `academic-report/` 目录**；仓库里其它文件都是开发过程产物，skill 运行完全不需要。

This repo is a **development workspace** (skill + design docs + tests). **To deploy, you only need the inner `academic-report/` directory** — everything else is dev-only.

```
academic-report/                 ← 仓库根 / repo root（开发工作区 / dev workspace）
├── academic-report/             ← ★ skill 本体（部署单元 / deployable unit = 拷这个）
│   ├── SKILL.md              #   技能定义（Agent 据此识别技能）
│   ├── scripts/              #   运行脚本：pipeline.py 等
│   ├── config/               #   配置：.env（由 .env.example 复制）
│   └── templates/            #   报告模板
│
├── docs/   details/          ← 开发文档（设计/实施计划/实现细节）— 运行不需要
├── test/   test-report/      ← 测试与运行记录 — 运行不需要
└── README.md / CLAUDE.md     ← 开发说明 — 运行不需要
```

**使用方式 / Usage**：把内层 `academic-report/` 整个目录拷到你 AI Agent 的 skill 目录即可。Copy the inner `academic-report/` into your agent's skill directory:

```bash
# 例：拷到 Claude Code 的 skill 目录（不同 Agent 路径不同，按你的 Agent 规范来）
cp -r academic-report/academic-report ~/.claude/skills/academic-report
```

> 💡 部署的目标目录必须保留 `SKILL.md` + `scripts/` + `config/` + `templates/` 四项。`docs/`、`details/`、`test/` 等留在仓库即可，skill 运行不读它们。
> The deployed dir only needs `SKILL.md` + `scripts/` + `config/` + `templates/`. Leave `docs/`, `details/`, `test/` in the repo — the skill never reads them at runtime.

---

## 🚀 Quick Start / 快速开始

### Requirements / 环境要求

- **Python**: 3.8 or higher / 3.8 或更高版本
- **OS**: Linux, macOS, or Windows / Linux、macOS 或 Windows
- **An AI Agent runtime** (Claude Code, Codex, etc.) — optional; the pipeline also runs directly via `python pipeline.py` / 可选任意 AI Agent 运行环境（Claude Code、Codex 等）；也可直接 `python pipeline.py` 运行

### Installation Steps / 安装步骤

#### 1. Install This Skill / 安装本技能

```bash
# Clone project / 克隆项目
git clone https://github.com/your-username/academic-report.git
cd academic-report

# Install dependencies / 安装依赖
pip install -r academic-report/requirements.txt
```

#### 2. Configure / 配置（唯一配置来源）

```bash
# Copy the env template and fill in your values / 复制配置模板并填入你的值
cp academic-report/config/.env.example academic-report/config/.env

# Edit academic-report/config/.env — required for email / 编辑 .env，邮件功能必需：
#   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
# 必需：SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

> `.env` 是本工程**唯一**的配置来源（含密钥与非敏感参数），不被 git 跟踪。其余可选项（LLM 分析、报告参数、代理）见 `.env.example` 内注释。 / `.env` is the **single** source of config (secrets + non-secret params), gitignored. Other optional items (LLM, report params, proxy) are documented inside `.env.example`.

---

## ⚙️ Configuration / 配置说明

### Required Configuration / 必需配置

#### SMTP Email Configuration / SMTP 邮件配置

For sending academic report emails / 用于发送学术报告邮件。

**配置位置 / Where to configure**: `academic-report/config/.env`（本工程唯一配置来源 / the single source of config for this project）

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
系统环境变量 (OS env, e.g. Windows 用户变量)  >  config/.env  >  代码默认值
```

若你在 **Windows 用户环境变量**里设过 `SMTP_*`，它会**覆盖** `.env`！改了 `.env` 却没效果，多半是系统环境变量在抢先生效。清掉它： / If you've set `SMTP_*` in your **OS user environment** (e.g. Windows User vars), it **overrides** `.env`. If `.env` edits don't take effect, a stale OS env var is winning — clear it:

```bash
unset SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD        # 当前 shell / current shell
# Windows 永久清除 / Windows permanent:
#   控制面板 → 用户环境变量 → 删除 SMTP_*  （或 `setx SMTP_PASSWORD ""` 后重开终端）
#   Control Panel → User env vars → delete SMTP_*  (or `setx SMTP_PASSWORD ""` then reopen terminal)
```

> 💡 **配置只在一个地方**：`academic-report/config/.env`（本工程唯一配置来源），避免「环境变量 vs .env」双源漂移导致排查困惑。 / Configure in **ONE place**: `academic-report/config/.env` (the single config source) to avoid two-source drift.

**收件人 / Recipient**: 在 `.env` 中设置 `EMAIL_RECIPIENT`（留空则回退到 `SMTP_USER`，即发给自己）/ Set `EMAIL_RECIPIENT` in `.env` (empty → falls back to `SMTP_USER`, i.e. send to yourself):

```bash
# academic-report/config/.env
EMAIL_RECIPIENT=your@email.com
```

> `config_manager` 启动时**自动加载** `config/.env`（仅在对应环境变量未设置时填充），无需手动 `export`；每次运行重新读取，改完即生效。 / `config_manager` **auto-loads** `config/.env` on startup (only fills env vars that aren't already set) — no manual `export`; re-read every run, so changes take effect immediately.

**Gmail 应用专用密码 / Gmail app password**: https://myaccount.google.com/apppasswords → 生成 16 位 → 填入 `SMTP_PASSWORD`。 / Generate a 16-char app password → put in `SMTP_PASSWORD`.

#### Report Defaults / 报告默认参数

All non-secret report defaults live in `.env` too (all optional, with sensible defaults) / 所有非敏感默认参数也写在 `.env`（均可选，有默认值）：

```bash
# academic-report/config/.env
DEFAULT_LANGUAGE=bilingual        # en / zh / bilingual
DEFAULT_TIME_RANGE=3y             # 1y / 3y / all
MAX_RESULTS=50                    # 每个数据源最大结果数 / max results per source
INCLUDE_PREPRINTS=true
FILTER_HIGHLY_CITED=false
HIGHLY_CITED_THRESHOLD=100
SCI_EI_ONLY=false
```

### Optional Configuration / 可选配置

#### API Keys (Optional) / API 密钥（可选）

To increase API rate limits / 提升 API 限流限制。

```bash
# academic-report/config/.env
SEMANTIC_SCHOLAR_API_KEY=your-s2s-key
# (arXiv / OpenAlex 无需 key / no key needed)
```

---

## 📖 Usage / 使用方法

### Single Search Mode / 单次搜索模式

Generate a complete academic report for a specified time period / 生成指定时间内的完整学术报告。

```bash
cd academic-report
python scripts/pipeline.py "搜索最近的 machine learning 论文，生成报告并发送到我的邮箱" --max-results 8
# Optional parameters / 可选参数（默认值见 config/.env）：
#   --language zh|en|bilingual  --time 3y|1y|1w|all  --recipient a@b.com
#   --format markdown|html  --no-email (只生成不发送 / generate only)  --output-dir <dir>
```

> Or invoke the `academic-report` skill through your AI Agent (Claude Code, Codex, etc.) with the same natural-language request — the agent runs the pipeline above. / 或通过你的 AI Agent（Claude Code、Codex 等）以同样的自然语言调用 `academic-report` 技能——Agent 会运行上面的 pipeline。

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

### Command Line Options / 命令行选项

```bash
# Test email configuration / 测试邮件配置
python academic-report/scripts/email_sender.py --test

# Check loaded config (SMTP/LLM defaults from .env) / 查看加载的配置（来自 .env）
python academic-report/scripts/config_manager.py
```

---

## 📂 Project Structure / 项目结构

```
academic-report/
├── SKILL.md                    # Skill definition / 技能主定义文件
├── requirements.txt             # Python dependencies / Python 依赖
├── config/                      # Configuration (single source) / 配置（唯一来源）
│   └── .env.example             # Template — copy to .env and fill in / 模板，复制为 .env 填值
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
│   ├── pipeline.py             # Full pipeline orchestrator ✅ / 全链路编排
│   └── llm_analyzer.py         # Four-element LLM analysis (Zhipu GLM, layered fallback) ✅ / 四要素 LLM 分析
├── templates/                  # Report templates / 报告模板
│   └── report_html_template.html  ✅
└── reports/                    # Generated reports — runtime, gitignored / 运行时生成（已 gitignore）
```

> 仓库根还有：`docs/`（`design-init.txt` 原始需求、`academic-report skill实施计划.md` 详细实施计划、`报告格式设计.md` 报告规范、`v1.0_vs_v2.0_对比.md` 迭代复盘、`notes/` 设计笔记）、`examples/`（真实报告样本）、`作品展示/`（求职/科研作品集）、`test/`（308 项 pytest）。

**Status Legend / 状态说明**：
- ✅ Complete / 已完成
- ⏳ Pending / 待实现
- 🔴 High Priority / 高优先级
- 🟡 Medium Priority / 中优先级
- 🟢 Low Priority / 低优先级

---

## 🛠️ Development Status / 开发状态

### Current Progress / 当前进度

- [x] **Refactor — De-Hermes & Unified Config (2026-08-02, in progress)**: making the skill **platform-agnostic** (Claude / Codex / any agent). Phase 1 ✅ — removed all `~/.hermes/` hardcoded paths via a single data dir (`academic-report/config/`); de-branded "Academic Report" → "Academic Report". Phase 2 ✅ — **single config source**: `academic-report/config/.env` (copied from `.env.example`); config_manager getters now read env vars (SMTP / LLM / API keys / report params); deleted legacy `env.example` + `config.example.yaml`; `.gitignore` updated. Scheduled-feature removal (Phase 5) and SKILL.md cleanup (Phase 3) pending. / 重构——去 Hermes 化与配置统一（2026-08-02，进行中）：技能改为**平台无关**（Claude / Codex / 任意 agent）。Phase 1 ✅——以单一数据目录 `academic-report/config/` 取代全部 `~/.hermes/` 硬编码路径；品牌串去 Hermes。Phase 2 ✅——**唯一配置来源** `config/.env`（由 `.env.example` 复制）；config_manager getter 改读环境变量；删除旧 `env.example` + `config.example.yaml`；更新 `.gitignore`。周期功能移除（Phase 5）与 SKILL.md 清理（Phase 3）待办。

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
  - [~] ~~Scheduled task management~~ — **removed in v2.0 refactor**（周期功能移除：`scheduler.py`/`timestamp_manager.py` 已删，改由调用方按需重复调用 pipeline）/ periodic reporting removed; callers repeat the pipeline call as needed

- [x] **Phase 5**: Testing & Verification (Complete, **308 tests** total) / 测试验证（完成，合计 **308 项**）
  - [x] config_manager.py tests ✅ (5 tests; including config/.env auto-loading / 5 项；含 config/.env 自动加载)
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

# Test config loading (from config/.env) / 测试配置加载（来自 config/.env）
python academic-report/scripts/config_manager.py
```

### Function Tests / 功能测试

```bash
# Test basic search (generate only, no email) / 测试基本检索（只生成不发送）
cd academic-report
python scripts/pipeline.py "搜索机器学习论文" --no-email --max-results 5

# Test email configuration / 测试邮件配置
python scripts/email_sender.py --test

# Test complete workflow (search → report → email) / 测试完整流程（检索→报告→邮件）
python scripts/pipeline.py "搜索深度学习论文，生成报告并发送到我的邮箱"
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

- [Implementation Plan / 实施计划文档](docs/academic-report%20skill实施计划.md)
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
5. **看到「发送冷却中」属正常**（v1.3.0）：认证失败（含 QQ 登录限频的假性 535）后，`email_sender` 会**指数退避冷却**（30→60→120→300s）并自动拒发（不再登录 QQ，避免轰炸加重限频）。等待冷却结束或设 `EMAIL_SKIP_COOLDOWN=1` 手动强制。每次发送（成功/失败/冷却）都记录在 `academic-report/config/email_sends.jsonl`，`tail` 即可排查。/ **"In cooldown" is expected** (v1.3.0): after an auth failure (incl. QQ throttle's false 535), `email_sender` **backs off exponentially** (30→60→120→300s) and auto-skips sending (no QQ login, to avoid deepening the throttle). Wait it out, or set `EMAIL_SKIP_COOLDOWN=1` to force. Every attempt (success/fail/cooldown) is logged to `academic-report/config/email_sends.jsonl` — `tail` it to diagnose.

### Q: How to disable preprints? / 如何禁用预印本？

**A**: Set `include_preprints: false` in config.yaml. / 设置 `include_preprints: false` 在 config.yaml 中。

### Q: 定时/周期报告怎么做？ / How to run periodic reports?

**A**: 本技能不内置定时功能（v2.0 已移除 scheduler）。如需周期报告，由调用方（AI Agent、系统 cron、launchd 等）按需重复调用 pipeline 即可 / This skill ships no built-in scheduler (removed in v2.0). For periodic reports, have the caller (AI Agent, system cron, launchd, etc.) invoke the pipeline on a schedule:

```bash
# 系统 cron 示例：每周一 09:00 跑一次 / system cron example: every Monday 09:00
# 0 9 * * 1  cd /path/to/academic-report && python scripts/pipeline.py "搜索 machine learning 论文，发到我邮箱"
```

---

## 📄 License / 许可证

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details. / 本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👥 Authors / 作者

Academic Report Team

---

## 🙏 Acknowledgments / 致谢

- [arXiv](https://arxiv.org/) - Open access academic paper preprints / 开放获取的学术论文预印本
- [Semantic Scholar](https://www.semanticscholar.org/) - AI-driven academic search / AI 驱动的学术搜索
- [OpenAlex](https://openalex.org/) - Open scholarly index / 开放的学术索引

---

## 📮 Contact / 联系方式

- Issue Feedback / 问题反馈: [GitHub Issues](https://github.com/your-username/academic-report-2.0/issues)
- Email / 邮件联系: academic-report@example.com

---

**Last Updated / 最后更新**: 2026-07-31

**Version / 版本**: 1.3.0（v1.3.0 增冷却守卫 + 发送记录日志；v1.2.1 修本地 SOCKS 探测 bug —— 7 月 21 日邮件失败根因 / v1.3.0 cooldown guard + send log; v1.2.1 fix local-SOCKS-probe bug; 2026-07-31 docs consolidation & repo reorg）
