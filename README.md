# Academic Report

> Turn a natural-language request into a formatted academic report delivered to your inbox.
> 把一句自然语言请求，变成一份发到邮箱的格式化学术报告。

[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 Overview / 简介

**Academic Report** is an AI Agent skill that searches multiple scholarly sources, filters and ranks the results, analyzes each paper, and generates a bilingual Markdown/PDF report — then sends it by email. Trigger it through your AI Agent (Claude Code, Codex, etc.) or run the pipeline directly.

**Academic Report** 是一个 AI Agent 技能：从多个学术数据源检索论文，筛选排序后逐篇分析，生成双语 Markdown/PDF 报告并通过邮件发送。可通过 AI Agent（Claude Code、Codex 等）触发，也可直接运行 pipeline。

---

## ✨ Features / 功能特性

### Core Modules / 核心模块

| Module / 模块 | Responsibility / 职责 |
|------|------|
| Intent Parsing / 意图解析 | Natural language → query, keywords, time range, filters / 自然语言→查询词、关键词、时间范围、过滤条件 |
| Multi-source Search / 多源检索 | Parallel search across arXiv / Semantic Scholar / OpenAlex with rate limiting / 三源并行检索，含限流 |
| Filtering & Ranking / 筛选排序 | Priority scoring, hotspot clustering, dedup / 优先级评分、热点聚类、去重 |
| Analysis / 深度分析 | Metadata extraction, four-element LLM excerpt, APA 7th, domain-level synthesis, foundational papers / 元数据提取、四要素 LLM 摘录、APA 7th、方向级综合、奠基论文 |
| Report Generation / 报告生成 | 4-section bilingual Markdown + PDF / 四段式双语 Markdown + PDF |
| Email Delivery / 邮件发送 | SMTP/SSL with attachment, retry, auto proxy detection / SMTP/SSL 带附件、重试、代理自动识别 |

### Data Sources / 数据源

| Source / 数据源 | API Limit / 限制 | Status / 状态 |
|--------|------|------|
| [arXiv](https://arxiv.org/) | None / 无 | ✅ |
| [Semantic Scholar](https://www.semanticscholar.org/) | 5000/day | ✅ |
| [OpenAlex](https://openalex.org/) | None / 无 | ✅ |
| [CrossRef](https://www.crossref.org/) / PubMed | 10/s · 3/s | ⏳ Reserved (rate-limiter ready, searcher not wired yet) / 预留（限流就绪，未接入） |

---

## 🧩 Architecture / 架构

Pipeline data flow / 管道数据流:

```
natural language → intent_parser → paper_search (parallel) → paper_filter
                                                          → paper_analyzer + llm_analyzer → report_generator → email_sender
```

All modules live in `academic-report/scripts/` / 各模块位于 `academic-report/scripts/`:

| File / 文件 | Role / 作用 |
|------|------|
| `pipeline.py` | Full-chain orchestrator / 全链路编排 |
| `intent_parser.py` | NL → `SearchIntent` / 自然语言→搜索意图 |
| `paper_search.py` | Multi-source search + dedup / 多源检索 + 去重 |
| `paper_filter.py` | Ranking + hotspot clustering / 排序 + 热点聚类 |
| `paper_analyzer.py` | Metadata, APA, overall analysis, foundational papers / 元数据、APA、整体分析、奠基论文 |
| `llm_analyzer.py` | Four-element LLM analysis (any Anthropic-compatible provider, default Zhipu GLM; rule fallback) / 四要素 LLM 分析（任意 Anthropic 兼容服务，默认智谱 GLM；规则回退） |
| `report_generator.py` | MD/PDF bilingual report / MD/PDF 双语报告 |
| `email_sender.py` | SMTP delivery with auto proxy detection / SMTP 发送，代理自动识别 |
| `config_manager.py` · `rate_limiter.py` · `utils.py` | Config / rate limiting / data models / 配置 / 限流 / 数据模型 |

---

## 🚀 Quick Start / 快速开始

### Requirements / 环境要求
- Python 3.8+
- An AI Agent runtime (Claude Code, Codex, …) — **optional**; the pipeline also runs standalone / **可选**；也可脱离 Agent 直接运行

### 1. Install / 安装

```bash
git clone https://github.com/Tina-Wangchu/academic-report.git
cd academic-report
pip install -r academic-report/requirements.txt
```

### 2. Configure / 配置

`academic-report/assets/.env` is the **single** config source — copy it from `.env.example`. Only SMTP is required. / `academic-report/assets/.env` 为**唯一**配置来源（由 `.env.example` 复制）；仅 SMTP 必填。

```bash
cp academic-report/assets/.env.example academic-report/assets/.env
```

```bash
# Required (email) / 邮件必填
SMTP_HOST=smtp.your-mailbox.com      # your mailbox SMTP host / 邮箱 SMTP 地址
SMTP_PORT=465                        # 465=SSL; 587=STARTTLS
SMTP_USER=your@email.com
SMTP_PASSWORD=xxxxxxxxxxxxxxxx       # mailbox auth code, NOT login password / 邮箱授权码，非登录密码
```

Common Chinese mailbox hosts / 常见国内邮箱:

| Mailbox / 邮箱 | `SMTP_HOST` |
|--------|-----------|
| QQ | `smtp.qq.com` |
| 网易 163 | `smtp.163.com` |
| 网易 126 | `smtp.126.com` |
| 新浪 | `smtp.sina.com` |

> All use port `465` (SSL). The `SMTP_PASSWORD` is the mailbox **authorization code** — enable POP3/SMTP service in your mailbox settings to generate it. / 均用端口 `465`（SSL）。`SMTP_PASSWORD` 是邮箱**授权码**：在邮箱设置中开启 POP3/SMTP 服务即可生成。

Optional knobs (see `.env.example` for all) / 可选项（全部见 `.env.example`）:
- `LLM_*` — any Anthropic-compatible provider (defaults to Zhipu GLM) for four-element analysis / 任意 Anthropic 兼容服务（默认智谱 GLM），用于四要素分析
- `SEMANTIC_SCHOLAR_API_KEY` — raises the S2 rate limit / 提升 Semantic Scholar 限流额度
- `DEFAULT_LANGUAGE` · `DEFAULT_TIME_RANGE` · `MAX_RESULTS` · `INCLUDE_PREPRINTS` · … — report defaults / 报告默认参数

### 3. Run / 运行

```bash
cd academic-report
python scripts/pipeline.py "搜索最近的 machine learning 论文，生成报告并发送到我的邮箱"
```

Common flags / 常用参数: `--language zh|en|bilingual` · `--time 3y|1y|1w|all` · `--max-results N` · `--no-email` (generate only / 只生成不发送) · `--recipient a@b.com`

Or invoke the `academic-report` skill from your AI Agent with the same natural-language request. / 或在 AI Agent 中以同样的自然语言调用 `academic-report` 技能。

---

## 📂 Project Structure / 项目结构

```
academic-report/                      ← repo root (dev workspace) / 仓库根（开发工作区）
├── academic-report/                  ← ★ the skill (deployable unit) / ★ 技能本体（部署单元）
│   ├── SKILL.md                     #   skill definition / 技能定义
│   ├── requirements.txt             #   Python deps / Python 依赖
│   ├── scripts/                     #   core modules (pipeline + 10 modules) / 核心模块
│   ├── assets/                      #   .env + .env.example + runtime data (logs, cache) / 配置 + 运行期数据
│   └── reports/                     #   generated reports, timestamped dirs / 生成的报告（按时间戳）
├── docs/  details/                  # design docs & implementation details / 设计文档与实现细节
├── examples/                        # sample reports (.md / .pdf) / 报告样本
└── test/  test-report/              # tests & run records / 测试与运行记录
```

> **Deploy**: copy the inner `academic-report/` directory into your agent's skill folder. / **部署**：把内层 `academic-report/` 整个拷进你 Agent 的 skill 目录即可。

---

## 📝 Report Format / 报告格式

Generated reports are bilingual (zh/en) and follow [`docs/报告格式设计.md`](docs/报告格式设计.md). / 生成的报告为双语，遵循 [`docs/报告格式设计.md`](docs/报告格式设计.md) 规范。

1. **Title + time / 标题 + 时间** — time range + topic + report / 时间范围 + 主题 + 报告
2. **Overview / 报告速览** — per-paper highlights grouped by hotspot / 按热点分组、逐篇速览
3. **Classified papers / 分类论文展示** — papers clustered by hotspot; each with metadata, four-element excerpt (problem / existing / new / results & limitations), overall analysis, foundational references, APA 7th / 按热点聚类；每篇含元数据、四要素摘录（问题/现有方案/新方案/效果与局限）、整体分析、奠基参考、APA 7th
4. **Research trends / 研究趋势** — future directions & gaps / 未来方向与研究缺口

Output formats / 输出格式: Markdown (default, also the PDF source / 默认，同时是 PDF 源) + PDF (rendered from MD via reportlab / 由 reportlab 从 MD 渲染).

---

## 🧪 For Developers / 开发者

```bash
# Module self-checks / 模块自测
python academic-report/scripts/config_manager.py          # print loaded config / 打印加载的配置
python academic-report/scripts/email_sender.py --test     # test SMTP connectivity / 测试 SMTP 连通性

# Run a search without sending email / 只检索不发邮件
cd academic-report && python scripts/pipeline.py "搜索 machine learning 论文" --no-email --max-results 5

# Full test suite / 完整测试
pytest test/
```

---

## ❓ FAQ / 常见问题

- **Paper language / 论文语言?** `en` / `zh` / `bilingual` via `--language` or `DEFAULT_LANGUAGE`. / 通过 `--language` 或 `DEFAULT_LANGUAGE` 设置。
- **More results / 更多结果?** Raise `--max-results` or `MAX_RESULTS` (default 50 per source). / 调大 `--max-results` 或 `MAX_RESULTS`（默认每源 50）。
- **Periodic reports / 定时报告?** No built-in scheduler; have the caller (Agent / cron / launchd) invoke the pipeline on a schedule. / 不内置定时；由调用方（Agent / cron / launchd）按计划重复调用 pipeline。

---

## 📄 License / 许可证

MIT — see [LICENSE](LICENSE). / MIT，详见 [LICENSE](LICENSE)。
