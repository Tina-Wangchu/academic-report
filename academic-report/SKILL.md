---
name: academic-report
description: "学术论文搜索→分析→双语报告→邮件（arXiv/Semantic Scholar/OpenAlex + LLM 四要素 + SMTP）。当用户想【搜索/查找/最近的论文】【文献综述/调研某领域】【研究热点/趋势分析】【把论文报告发到我邮箱】时用本技能——一条命令完成检索+报告+发信。/ Academic paper search→analysis→bilingual report→email (arXiv/Semantic Scholar/OpenAlex + LLM). Use when the user wants to search recent papers, do a literature review, analyze research trends, or have a paper report emailed."
version: 2.0.0
license: MIT
---

# Academic Report

学术论文自动化：检索 → **LLM 四要素分析** → 双语报告 → 邮件，**一条命令完成**。
本技能平台无关（可用于 Claude、Codex 等任意 Agent 运行环境），不依赖任何特定 Agent 框架。

## 何时使用

- "搜索/查找最近的 X 论文"
- "对 X 领域做文献综述/调研"
- "分析 X 领域的研究热点/趋势"
- "把论文报告发到我邮箱"


## 依赖

1. **Python 3.8+**
2. **Python 依赖**：在 `academic-report/` 目录执行 `pip install -r requirements.txt`
3. **配置文件**：`academic-report/assets/.env` 已就绪（由 `.env.example` 复制并填值）
   - `SMTP_*` 四项——**必需**（否则无法发邮件）
   - `LLM_*`——推荐（四要素深度分析；未配置则自动回退规则抽取，不报错）
4. **网络**：能访问 arXiv / Semantic Scholar / OpenAlex；SMTP 出站可达

## 执行流程

从 `academic-report/` 目录运行（部署机 cwd 不同时改用绝对路径）：

```bash
python scripts/pipeline.py "<用户的检索请求原话>" --recipient <用户邮箱>
```

`pipeline.py` 是总编排器，按以下 **6 个阶段**顺序调用各模块（stdout 逐阶段打印 `[1/6]`…`[6/6]` 进度）：

**阶段 1 · 意图解析**　`intent_parser.py`　从用户原话提取查询、关键词、时间范围、筛选条件。

**阶段 2 · 多源检索**　`paper_search.py`　arXiv + Semantic Scholar + OpenAlex 并行搜索，去重合并。

**阶段 3 · 筛选排序**　`paper_filter.py`　优先级评分、质量过滤、热点聚类。

**阶段 4 · 深度分析**　`paper_analyzer.py` + `llm_analyzer.py`　LLM 四要素分析（解决的问题 / 已有方案 / 新方案 / 效果及局限）；无摘要时自动抓全文；闭源论文标注检索链接。

**阶段 5 · 报告生成**　`report_generator.py`　双语报告（Markdown / PDF），按热点分组 + 研究趋势。

**阶段 6 · 邮件发送**　`email_sender.py`　SMTP 投递（自动识别代理：直连 → SOCKS 回退；内置重试与冷却守卫）。

**你的职责**：运行命令 → 把脚本 stdout（`[1/6]…[6/6]` 各阶段 + 「发送到 …: 成功/失败」）**原样**贴给用户。
**不要**自己生成报告，**不要**自己发邮件。

**可选参数**（默认值均来自 `assets/.env`，无需显式传）：
`--language zh|en|bilingual`、`--time 3y|1y|1w|all`、`--max-results N`、`--format markdown|pdf`、`--no-email`（只生成不发送）、`--output-dir <目录>`。

## 配置

唯一配置来源：`academic-report/assets/.env`（不入 git；模板 `.env.example` 入 git）。

加载优先级：`真实环境变量（export）> .env 文件 > 代码默认值`。完整配置项见 `.env.example`，分 5 组：

- **SMTP**（必需）：`SMTP_HOST/PORT/USER/PASSWORD`、`EMAIL_RECIPIENT`
- **LLM**（推荐）：`LLM_API_KEY/BASE_URL/MODEL/PROVIDER/ENABLED`
- **API key**（可选）：`SEMANTIC_SCHOLAR_API_KEY`
- **报告参数**：`DEFAULT_LANGUAGE/TIME_RANGE/MAX_RESULTS/QUERY`、`OUTPUT_FORMAT/DIR`、`SEND_EMAIL`、过滤阈值等
- **代理**（可选）：`SMTP_SOCKS_PROXY/ALL_PROXY/HTTPS_PROXY`

## 注意事项

1. **必须用 shell/terminal 运行 `pipeline.py`**，不要用 `python -c "…"`、heredoc 或 REPL 内联脚本——隔离/沙箱环境通常读不到 `.env` 里的 SMTP 凭据，发信必败。
2. **不要绕过 pipeline**：禁止自己抓 arXiv、自己拼 JSON/报告、自己写 `smtplib` 发信。检索 + 报告 + 发信 100% 由 `pipeline.py` 完成——自己动手会编造论文（hallucination）且用错配置。
3. **邮件失败多为网络瞬时问题**：连接超时 / 意外关闭 = 直连被墙或防火墙复位，**不是密码错**。脚本已内置代理自动回退（直连 → SOCKS）与重试。失败后**等 1–2 分钟重试一次**即可；不要反复重跑（连续登录会触发 SMTP 登录限频 → 假性 535）。
4. **以脚本 stdout 为准**：只有 stdout 明示 `SMTP 认证失败` 才是真凭据问题；其余（超时 / 连接关闭）是网络问题，照实上报即可，不要让用户改配置。
5. **看到「发送冷却中」就停手**：脚本内置冷却守卫，认证失败后指数退避（30→60→120→300s）并自动拒发。stdout 提示「需再等 N 秒」时，转告用户等待，不要重跑或绕过。
6. **Windows**：用 `python`，不要用 `python3`（应用商店存根会失败）。
7. **部分闭源论文**（无摘要且抓不到全文）四要素会标注「无法自动分析」并附检索链接——属正常。
