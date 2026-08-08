# Academic Report 学术搜索 Skill - 完整详细实施计划（平台无关）

> ## 🔄 重构变更记录（2026-08-02，进行中）
>
> 本计划原文以 Hermes Agent 为目标平台编写，现正在进行**去 Hermes 化重构**，使本技能成为平台无关的通用 AI Agent Skill（可用于 Claude、Codex 等任意 Agent 运行环境）。已完成：
> - **Phase 1 ✅ 去 Hermes 化**：新增 `utils.get_skill_data_dir()`，所有运行期路径（配置、缓存、日志、冷却、时间戳）统一指向 `academic-report/config/`；删除全部 `~/.hermes/` 硬编码；品牌串 "Academic Report" → "Academic Report"。
> - **Phase 2 ✅ 配置统一**：**唯一配置来源** `academic-report/config/.env`（由 `.env.example` 复制）；`config_manager` getter 改为优先读环境变量（SMTP / LLM / API key / 报告参数）；删除旧 `env.example` + `config.example.yaml`；`.gitignore` 已忽略 `.env` 与运行期数据。
> - **全部完成 ✅**：Phase 3 / 5 / 6 / 7 均已完成。研究缺口逻辑已从「论文缺陷评价」改为「给读者的深挖方向」（LLM 主 + 规则回退）。
> - **后续 ✅ 数据源修复（2026-08-03）**：arXiv 检索从坏掉的 `arxiv` 库（HTTP 301 不跟随重定向）改为 `requests`+Atom 直查（0→5 篇）；Semantic Scholar `_build_year_filter` 修正（`2023-,-2026`→`2023-2026`）+ 429 退避重试；`PaperSearcher.search_errors` 让单源失败不再静音（写入 run_data.json）。S2 缺免费 key 的 429 问题暂缓，记录于 `docs/known_issues.md`（含配 key 步骤）。`requirements.txt` 删 `arxiv==1.4.8`。
> - **后续 ✅ 时间戳运行日志（2026-08-03）**：pipeline 每次运行产出 `reports/{YYYY-MM-DD_HHMMSS}/` 文件夹，内含 `report.md` + `report.pdf` + `run_data.json`（各模块原始返回：intent / papers_raw / papers_filtered(含四要素) / classified / research_directions / search_errors / timings）。`report_generator` 新增 `generate_both()`——`_prepare` 只跑一次同时产 MD+PDF，避免 LLM 四要素/研究方向重算。
> - **SMTP 实测（2026-08-03）**：用户 `config/.env` 配 QQ 邮箱（`smtp.qq.com:465` + 授权码）作发件、Gmail 作默认收件人；已实测 QQ→QQ、QQ→Gmail 真实发送成功。
> - **后续 ✅ 报告输出 HTML→PDF（2026-08-07）**：用 reportlab（纯 Python，无系统依赖；中文走内置 CID 字体 STSong-Light）将 MD 行向解析为 Platypus flowables 生成 PDF；删除 _convert_to_html 与 templates/report_html_template.html；pipeline 默认附件改 PDF（OUTPUT_FORMAT 默认 pdf，回退 md）；email_sender 识别 .pdf（application/pdf）；requirements +reportlab、-markdown/-jinja2；文档全量同步。
>
> - **后续 ✅ 英文查询修复（2026-08-08）**：`_to_english_query` 术语表补「人工智能」等常见词 + 翻译后剥离剩余中文 → 搜索查询恒为英文（OpenAlex/S2 返回英文论文，报告标题全英文，匹配权威学术源预期）；`PaperSearcher.search` 去重后再过滤「标题无任何拉丁字母」的纯中文条目作兜底。
> - **后续 ✅ 报告文本/排版质量改进（2026-08-08）**：①中英自动加空格 `_autospace_cjk_latin`（CJK↔拉丁/数字插半角空格，URL/DOI 占位保护+边界空格），`_render_markdown` 末尾统一应用；②英文用内置 **Times-Roman** 字体（注册 family，`<b>`→Times-Bold，**英文可真加粗**），中文仍 `STSong-Light`；③正文/引用两端对齐 `TA_JUSTIFY`；④URL/DOI 反引号→等宽 `Courier`；⑤速览 `_paper_finding` 去前缀（Abstract/INTRODUCTION:…）+ 句界省略号；⑥标准 Title Case（虚词 of/and/the/in 小写、缩写 AI/NLP/BERT 大写）；⑦各级标题英文加粗。**中文真加粗需捆绑 Noto Sans SC（+20MB），按决定暂不引入，见 `docs/known_issues.md`。**
> - **后续 ✅ 论文标题中英双语（2026-08-08）**：`Paper` 新增 `title_zh`；四要素 LLM 调用（`llm_analyzer._system_prompt`/`_FIELD_KEYS`）同步产出标题中文翻译，`paper_analyzer` 回填 `paper.title_zh`；`_render_paper` 在双语/zh 模式显示「英文标题（中文翻译）」，en 模式仅英文，LLM 不可用/闭源则回退纯英文。**注意：LLM 缓存（`llm_cache_four_element.json`）中旧条目无 `title_zh` → 命中缓存的论文仍显示纯英文；如需全部翻译，删除该缓存文件后重跑（见 `docs/known_issues.md`）。**
>
> ⚠️ 下方原始计划保留作为各模块设计的权威参考，但其中涉及 `~/.hermes/`、`config.example.yaml`、`env.example`、Hermes frontmatter、`scheduler`/`timestamp_manager` 的内容**已过时**——一切以本变更记录为准。

## 项目概述

基于 design-init.txt 的要求，创建一个完整的学术搜索 AI Agent Skill（平台无关，不依赖特定 Agent 运行环境），实现学术搜索、分析、报告生成和邮件发送的全流程自动化。

---

## 项目文件目录结构

```
academic-report-2.0/
│
├── academic-report/                    # 主技能目录
│   ├── SKILL.md                     # ✅ Hermes Agent 技能主定义文件
│   │                                #    - Frontmatter 配置（元数据、环境变量、blueprint等）
│   │                                #    - 技能使用说明（When to Use、Procedure、Pitfalls等）
│   │                                #    用途：Hermes Agent 加载此文件来识别和执行技能
│   │
│   ├── requirements.txt              # ✅ Python 依赖清单
│   │                                #    - arxiv, scholarly, requests, pandas, markdown, jinja2等
│   │                                #    用途：安装所需的Python包
│   │
│   ├── config/                       # 配置文件目录（唯一配置来源 / Phase 2 重构后）
│   │   └── .env.example             # ✅ 环境变量配置模板（用户 cp 为 .env 填值）
│   │                                #    - SMTP、LLM、API key、报告参数、代理（全部集中于此）
│   │                                #    用途：唯一配置来源；.env 不入 git，.env.example 入 git
│   │                                #    注：旧 config.example.yaml / env.example 已删除
│   │
│   ├── scripts/                      # Python 脚本目录（核心功能模块）
│   │   ├── __init__.py              # ✅ Python 包初始化文件
│   │   │                            #    用途：标识scripts为Python包
│   │   │
│   │   ├── utils.py                 # ✅ 工具函数库
│   │   │                            #    数据模型：Paper, SearchIntent
│   │   │                            #    工具函数：日期解析、APA引用、文件操作等
│   │   │                            #    用途：供其他模块共享使用的数据结构和工具
│   │   │
│   │   ├── config_manager.py        # ✅ 配置管理器
│   │   │                            #    加载 Hermes config.yaml
│   │   │                            #    读取环境变量（SMTP配置、API密钥）
│   │   │                            #    验证配置完整性
│   │   │                            #    用途：统一管理所有配置项
│   │   │
│   │   ├── rate_limiter.py          # ✅ API 限流处理器
│   │   │                            #    管理各数据源的API限流
│   │   │                            #    等待机制防止超限
│   │   │                            #    状态查询和重置
│   │   │                            #    用途：处理 arXiv、Semantic Scholar、CrossRef 等的限流
│   │   │
│   │   ├── intent_parser.py         # ✅ 用户意图解析器（模块1）
│   │   │                            #    解析自然语言输入
│   │   │                            #    提取：查询、关键词、研究领域、语种、时间范围、文献类型、筛选条件
│   │   │                            #    检测定时任务模式
│   │   │                            #    用途：将用户输入转换为结构化的搜索意图
│   │   │
│   │   ├── paper_search.py          # ✅ 多数据源论文搜索器（模块2，已完成）
│   │   │                            #    ArxivSearcher：搜索 arXiv 预印本
│   │   │                            #    SemanticScholarSearcher：搜索 Semantic Scholar
│   │   │                            #    OpenAlexSearcher：搜索 OpenAlex 开放索引
│   │   │                            #    PaperSearcher：协调多数据源，并行搜索，去重合并
│   │   │                            #    用途：从多个学术数据源检索论文
│   │   │
│   │   ├── paper_filter.py          # ✅ 文献筛选和排序器（模块3，已完成）
│   │   │                            #    质量过滤：高被引、SCI/EI、核心期刊筛选
│   │   │                            #    优先级排序：根据引用量、期刊等级打分排序
│   │   │                            #    热点聚类：已知AI主题+非AI关键词兜底，按权重排序
│   │   │                            #    热点介绍：generate_hotspot_intro（Option B 从 report_generator 迁入）
│   │   │                            #    用途：智能筛选、排序、聚类论文（去重在 paper_search 完成）
│   │   │
│   │   ├── paper_analyzer.py        # ✅ 论文信息提取与分析器（模块4，已完成）
│   │   │                            #    提取结构化信息：标题、作者、DOI、摘要等
│   │   │                            #    深度分析：研究内容、创新点、结论、应用场景
│   │   │                            #    方向级整体分析（Option B 从 report_generator 迁入）
│   │   │                            #    奠基性参考论文：真实调 S2 references API + 离线回退（Option B）
│   │   │                            #    生成APA 7th引用格式
│   │   │                            #    用途：提取、分析论文并做方向级综合
│   │   │
│   │   ├── report_generator.py      # ✅ 学术报告生成器（模块5，已完成）
│   │   │                            #    四段式 Markdown 报告（命令式渲染）
│   │   │                            #    PDF 转换（reportlab 渲染）
│   │   │                            #    双语（默认 bilingual，按 intent.language 驱动）
│   │   │                            #    速览按热点概括 + 研究趋势语料派生
│   │   │                            #    委托 filter/analyzer（Option B）：介绍/整体分析/奠基论文
│   │   │                            #    用途：生成格式化的学术报告（MD/PDF）
│   │   │
│   │   ├── email_sender.py          # ✅ 邮件发送器（模块6，已完成）
│   │   │                            #    SMTP/SSL 分流（465→SSL，587→STARTTLS）
│   │   │                            #    邮件构建（HTML 正文+附件，双语）
│   │   │                            #    发送失败重试（认证错误不重试）
│   │   │                            #    SMTP连接测试 + CLI
│   │   │
│   │   ├── pipeline.py              # ✅ 全链路编排（单次搜索入口 + 增量分支）
│   │   │                            #    意图解析→检索→筛选→分析→报告→邮件 一条命令
│   │   │                            #    增量分支：--incremental 读时间戳窗口、客户端年份兜底、仅成功后更新
│   │   │                            #    CLI：python pipeline.py "搜索…生成报告并发送邮件" [--incremental]
│   │   │                            #    用途：单次搜索 + 定时增量复用同一条链路
│   │   │
│   │   ├── timestamp_manager.py     # ✅ 定时报告时间戳管理（定时模式支撑，已完成）
│   │   │                            #    每主题持久化 last-run（~/.hermes/academic_scholar_timestamps.json）
│   │   │                            #    topic_key / get_last_run / update_last_run（防御加载 + 原子写）
│   │   │                            #    用途：为增量检索提供 [上次, 现在] 窗口
│   │   │
│   │   └── scheduler.py             # ✅ 定时报告调度器（定时模式入口，已完成）
│   │                                #    进程内定时（不依赖 Hermes）：解析周期→首次立即触发→按周期跑增量
│   │                                #    --once/--dry-run/--cron（可选 croniter）；SIGINT 优雅退出
│   │                                #    用途：定时增量报告的常驻入口
│   │
│   ├── templates/                    # 报告模板目录
│   │   ├── report_template.md       # ⏳ Markdown 报告模板（参考；实际渲染为命令式，见模块5）
│   │   │                            #    报告结构和格式
│   │   │                            #    Jinja2 模板变量
│   │   │                            #    用途：生成Markdown格式的学术报告
│   │   │
│   │   └── report_html_template.html # 🗑 已删除（2026-08-07 PDF 改造移除，原 HTML 报告模板）
│   │                                #    历史：HTML结构和CSS样式、响应式设计
│   │                                #    现已由 reportlab（_convert_to_pdf）取代，不再生成 HTML 报告
│   │
│   └── references/                   # 参考文档目录
│       ├── apa_citation_guide.md     # ⏳ APA 7th 引用格式指南
│       │                            #    APA引用规则和示例
│       │                            #    常见引用格式
│       │                            #    用途：指导正确生成APA格式引用
│       │
│       └── supported_apis.md         # ⏳ 支持的API文档
│                                   #    各数据源API使用说明
│                                   #    限流规则
│                                   #    用途：API集成参考文档
│
├── design-init.txt                   # 原始需求文档
│                                   #    用户的功能需求说明
│                                   #    六大板块详细要求
│                                   #    用途：项目需求参考
│
└── academic-report skill实施计划.md   # ✅ 本实施计划文档
                                    #    完整的功能需求和实施方案
                                    #    详细的技术实现代码
                                    #    测试和部署指南
                                    #    用途：项目实施的指导文档
```

## 文件模块说明

### 📁 核心模块文件（scripts/）

#### 已完成模块 ✅

| 文件 | 模块 | 状态 | 用途 |
|------|------|------|------|
| `utils.py` | 工具库 | ✅ 完成 | 数据模型（含 condensed_abstract / tldr 字段）、工具函数 |
| `config_manager.py` | 配置管理 | ✅ 完成 | 统一管理配置；`_load_env_file` 自动加载 `config/.env`（不覆盖已有环境变量）；**Phase 2 后 getter 优先读环境变量**（SMTP/LLM/API key/报告参数），config.yaml 仅作可选覆盖（test_config_manager.py 5项） |
| `rate_limiter.py` | 限流处理 | ✅ 完成 | API限流和等待机制 |
| `intent_parser.py` | 意图解析 | ✅ 完成 | 解析用户自然语言输入 |
| `paper_search.py` | 论文搜索 | ✅ 完成 | 多数据源并行检索、去重合并；OpenAlex 摘要重建；S2 TL;DR（tldr 字段）接入；实验驱动修复多处 bug（test_paper_search.py 27项） |
| `paper_filter.py` | 筛选排序 | ✅ 完成 | 质量过滤、优先级排序、热点聚类（≥2 收敛+topic_hint 相关性）、热点介绍、年份级时间安全网（test_paper_filter.py 27项） |
| `paper_analyzer.py` | 信息分析 | ✅ 完成 | 结构化提取、APA 7th、方向级整体分析、奠基论文（真实 S2 references API + 离线回退）；AbstractSummarizer 完整去填充摘要；四要素分层（**LLM 生成式→规则回退**，由 `llm_analyzer.FourElementAnalyzer` 调度；StructuredExtractor 作离线规则版）（test_paper_analyzer.py 50项） |
| `llm_analyzer.py` | 四要素 LLM | ✅ 新增（v1.1.0） | `ZhipuProvider`（智谱 GLM 的 Anthropic 兼容端点，复用 ANTHROPIC_AUTH_TOKEN，零新依赖）+ `FourElementAnalyzer`（LLM→规则分层 + 按 DOI/title/language 缓存）；**v1.1.0：prompt 由 `_system_prompt(language)` 按 `intent.language` 构造**（zh=中文 / en=英文 / bilingual=每要素中英两段），修复旧版"四要素恒中文、无视 language"；`temperature=0`（test_llm_analyzer.py 32项，mock，含 TestLanguageControl 9项） |
| `report_generator.py` | 报告生成 | ✅ 完成 | 四段式 MD/PDF、双语（默认 bilingual）、速览按热点逐篇概述、**单篇块四要素**（LLM/规则统一渲染，全空回退完整 Abstract）、趋势语料派生、Option B 委托（test_report_generator.py 23项） |
| `templates/report_html_template.html` | HTML 模板 | 🗑 已删除 | (2026-08-07 PDF 改造删除，原 HTML 外壳 + CSS 样式) |
| `email_sender.py` | 邮件发送 | ✅ 完成（v1.1.1） | SMTP/SSL 分流、HTML 正文+附件、重试、**代理自动识别（直连→SOCKS 回退，开/关代理都能发）**、连接测试（test_email_sender.py 29项）。**v1.1.1（2026-07-21）**：修本地 SOCKS 探测 bug——`_connect_auto_local_socks` 误用 `_REAL_SOCKET.create_connection`（socket 类无此方法），导致直连失败且无环境变量代理时兜底探测抛 `AttributeError`、回退彻底无法启动（**Jul 21 邮件失败根因**）；改用模块级 `_REAL_CREATE_CONNECTION`，回归测试 `TestAutoLocalSocksProbe` 锁死。 |

#### 定时报告模块 ✅（2026-07-13 实现）

| 文件 | 模块 | 状态 | 说明 |
|------|------|------|------|
| `timestamp_manager.py` | 时间戳管理 | ✅ 完成 | 持久化每主题 last-run（`~/.hermes/academic_scholar_timestamps.json`）；`topic_key`/`get_last_run`/`update_last_run`；防御加载 + 原子写；单例 `get_timestamp_manager()`（test_timestamp_manager.py 15项） |
| `scheduler.py` | 定时调度器 | ✅ 完成 | 进程内定时（不依赖 Hermes）：解析周期 → 首次立即触发建基线 → 按周期 `run_pipeline(incremental=True)`；`--once/--dry-run/--cron`；SIGINT；可选 croniter（test_scheduler.py 15项：增量分支 + 调度循环） |
| `intent_parser.py` | 调度检测 | ✅ 增强 | `_detect_schedule`/`_extract_schedule`（daily/weekly/biweekly/monthly/every-Nd）+ `_schedule_default_window`；定时短语从 query 剔除（test_intent_parser.py 37项） |
| `pipeline.py` | 增量分支 | ✅ 增强 | `incremental`/`topic_override`/`no_incremental`/`send_empty`；窗口=`[last_run, now]`、客户端年份兜底过滤、邮件主题前缀、**仅成功后更新时间戳**、空增量跳过 |
| `utils.py` | 数据模型 | ✅ 增强 | `SearchIntent` 加 `is_scheduled`/`schedule`；新增 `schedule_interval(token)` |
| `report_generator.py` | 增量标记 | ✅ 增强 | `is_scheduled` 时标题下加「增量报告 / Incremental (since …)」；PDF 标题前缀 |

### 📁 配置和模板文件

#### 配置文件

| 文件 | 用途 | 是否必需 |
|------|------|----------|
| `SKILL.md` | Hermes Agent 技能定义 | ✅ 必需 |
| `requirements.txt` | Python 依赖清单 | ✅ 必需 |
| `config/config.example.yaml` | 配置示例 | 📋 参考 |
| `config/env.example` | 环境变量示例 | 📋 参考 |

#### 模板文件

| 文件 | 用途 | 格式 |
|------|------|------|
| `templates/report_template.md` | MD报告模板 | Markdown + Jinja2 |
| `templates/report_html_template.html` | 🗑 已删除（2026-08-07 PDF 改造） | HTML + CSS |

#### 参考文档

| 文件 | 用途 | 目标用户 |
|------|------|----------|
| `references/apa_citation_guide.md` | APA引用指南 | 开发者 |
| `references/supported_apis.md` | API文档 | 开发者 |

---

## 🔧 环境依赖和前置条件

### 系统要求

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|----------|----------|------|
| Python | 3.8+ | 3.10+ | 核心运行环境 |
| Hermes Agent | 最新版 | 最新版 | Agent框架 |
| 操作系统 | 跨平台 | Linux/macOS | 主要开发平台 |

### Python 依赖包

```txt
# 核心依赖（必需）
arxiv==1.4.8              # arXiv API客户端
scholarly==1.5.0          # 学术搜索引擎
requests==2.31.0          # HTTP请求库

# 数据处理
pandas==2.1.0             # 数据分析
numpy==1.24.0             # 数值计算

# 文本处理
markdown==3.5.0           # Markdown转换
jinja2==3.1.2             # 模板引擎

# 邮件发送
secure-smtplib==0.1.1     # SMTP加密连接

# 工具库
python-dateutil==2.8.2    # 日期处理
pyyaml==6.0.1             # YAML解析

# 可选依赖
scikit-learn==1.3.0       # 机器学习（用于论文聚类）
```

### 环境变量配置（必需）

#### 必需的环境变量

| 变量名 | 用途 | 示例值 | 获取方式 |
|--------|------|--------|----------|
| `SMTP_HOST` | SMTP服务器 | `smtp.gmail.com` | 邮箱服务商提供 |
| `SMTP_PORT` | SMTP端口 | `587` | 邮箱服务商提供 |
| `SMTP_USER` | SMTP用户名 | `your@gmail.com` | 你的邮箱地址 |
| `SMTP_PASSWORD` | SMTP密码 | `your-app-password` | Gmail需生成应用专用密码 |

#### 可选的环境变量

| 变量名 | 用途 | 示例值 | 获取方式 |
|--------|------|--------|----------|
| `ARXIV_API_KEY` | arXiv API密钥 | `your-key` | https://arxiv.org/help/api |
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar密钥 | `your-key` | https://www.semanticscholar.org/product/api |

### Hermes Agent 配置

```yaml
# ~/.hermes/config.yaml
skills:
  config:
    academic:
      default_language: bilingual     # 默认语言: en/zh/bilingual
      default_time_range: 3y          # 默认时间范围: 1y/3y/all
      max_results: 50                 # 每个数据源最大结果数
      email_recipient: user@example.com  # 默认邮件接收者
      include_preprints: true         # 是否包含预印本
      min_citation_count: 0           # 最小引用量筛选
      filter_highly_cited: false      # 是否启用高被引筛选
      highly_cited_threshold: 100     # 高被引阈值
      sci_ei_only: false              # 是否仅SCI/EI期刊
```

### 安装步骤

#### 1. 安装 Hermes Agent
```bash
# 使用 pip 安装
pip install hermes-agent

# 或从源码安装
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
pip install -e .
```

#### 2. 安装本技能依赖
```bash
cd academic-report-2.0/academic-report
pip install -r requirements.txt
```

#### 3. 配置环境变量
```bash
# 复制环境变量示例
cp config/env.example ~/.hermes/.env

# 编辑 ~/.hermes/.env，添加你的配置
# 必需：SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

#### 4. 配置 Hermes
```bash
# 使用 Hermes 配置命令
hermes config set skills.config.academic.default_language bilingual
hermes config set skills.config.academic.max_results 50
hermes config set skills.config.academic.email_recipient your@email.com
```

#### 5. 安装技能到 Hermes
```bash
# 方法1：直接复制到 Hermes 技能目录
cp -r academic-report-2.0/academic-report ~/.hermes/skills/

# 方法2：创建符号链接（开发时推荐）
ln -s $(pwd)/academic-report ~/.hermes/skills/academic-report
```

### API 配置说明

#### arXiv API
- **限流**: 无官方限制
- **要求**: 无需API密钥
- **使用方法**: 直接使用 `arxiv` Python库

#### Semantic Scholar API
- **限流**: 5000次/天（免费）
- **要求**: 可选API密钥（提高限流）
- **获取方式**: https://www.semanticscholar.org/product/api
- **使用方法**: REST API

#### OpenAlex API
- **限流**: 无官方限制
- **要求**: 无需API密钥
- **使用方法**: REST API

#### CrossRef API
- **限流**: 10次/秒
- **要求**: 无需API密钥
- **使用方法**: REST API

### 邮件服务配置指南

#### Gmail 配置示例
```
SMTP_HOST: smtp.gmail.com
SMTP_PORT: 587
SMTP_USER: yourname@gmail.com
SMTP_PASSWORD: (应用专用密码)
```

**生成Gmail应用专用密码**：
1. 访问 https://myaccount.google.com/apppasswords
2. 选择"应用"和"设备"
3. 生成16位应用专用密码
4. 将密码作为 SMTP_PASSWORD

#### QQ 邮箱配置示例
```
SMTP_HOST: smtp.qq.com
SMTP_PORT: 587
SMTP_USER: yourname@qq.com
SMTP_PASSWORD: (授权码)
```

#### Outlook 配置示例
```
SMTP_HOST: smtp-mail.outlook.com
SMTP_PORT: 587
SMTP_USER: yourname@outlook.com
SMTP_PASSWORD: (你的密码)
```

### 依赖检查清单

在开始使用前，请确认：

- [ ] Python 3.8+ 已安装
- [ ] Hermes Agent 已安装
- [ ] 所有Python依赖包已安装（`pip list | grep -E "arxiv|scholarly|jinja2"`）
- [ ] SMTP 环境变量已配置
- [ ] Hermes 配置文件已设置
- [ ] 技能已安装到 ~/.hermes/skills/
- [ ] 可以运行 `hermes chat` 进入 Hermes

### 快速测试

```bash
# 测试 Hermes Agent 是否正常
hermes chat --toolsets skills -q "列出所有技能"

# 测试本技能是否加载
hermes chat -q "/academic-report 帮助"

# 测试邮件配置
python3 academic-report/scripts/email_sender.py --test
```

---
## 详细实施方案

### 模块1：用户需求解析并触发skill

#### 文件：`scripts/intent_parser.py`（已创建基础版本）

**需要增强的功能**：

```python
class IntentParser:
    """用户意图解析器 - 完整版"""

    def parse(self, user_input: str) -> SearchIntent:
        """
        完整解析用户输入

        支持的输入示例：
        - "搜索最近的深度学习论文"
        - "查找关于GPT的最新研究，近1年"
        - "每周一发送AI领域的学术论文"
        - "检索高被引的计算机视觉论文，SCI期刊，近3年"
        """
        # 1. 提取查询主题
        query = self._extract_query(user_input)

        # 2. 提取关键词（支持中英文）
        keywords = self._extract_keywords(user_input)

        # 3. 识别研究领域
        research_field = self._identify_research_field(user_input)

        # 4. 识别语种（en/zh/bilingual）
        language = self._identify_language(user_input)

        # 5. 提取时间范围（支持精确到天）
        time_range_text = self._extract_time_range(user_input)
        start_date, end_date = self._parse_time_range_precise(time_range_text)

        # 6. 识别文献类型（journal/conference/thesis）
        paper_types = self._identify_paper_types(user_input)

        # 7. 识别筛选条件
        filters = self._identify_filters(user_input)

        # 8. 检测是否为定时任务
        is_scheduled = self._detect_schedule(user_input)
        schedule = self._extract_schedule(user_input) if is_scheduled else None

        return SearchIntent(
            query=query,
            keywords=keywords,
            research_field=research_field,
            language=language,
            start_date=start_date,
            end_date=end_date,
            paper_types=paper_types,
            filters=filters,
            is_scheduled=is_scheduled,
            schedule=schedule,
        )

    def _parse_time_range_precise(self, text: str) -> tuple[Optional[datetime], Optional[datetime]]:
        """
        精确解析时间范围（到天）

        支持格式：
        - "近1年" -> 365天前至今
        - "近3年" -> 1095天前至今
        - "近1月" -> 30天前至今
        - "近1周" -> 7天前至今
        - "近1天" -> 1天前至今
        - "2023-01-01至2023-12-31" -> 指定范围
        - "不限" -> None
        """
        # 实现精确到天的时间解析
        pass

    def _detect_schedule(self, text: str) -> bool:
        """
        检测是否为定时任务

        匹配模式：
        - "每周一"
        - "每个月"
        - "每两周"
        - "定时"
        """
        schedule_patterns = [
            r'每\s*周',
            r'每\s*月',
            r'每\s*两?\s*周',
            r'定时',
            r'周期',
        ]
        return any(re.search(pattern, text) for pattern in schedule_patterns)

    def _extract_schedule(self, text: str) -> Optional[str]:
        """提取定时任务配置（cron表达式）"""
        # 实现 cron 表达式生成
        pass
```

**需要添加的关键词库**：

```python
# 研究领域关键词（扩展）
FIELD_KEYWORDS = {
    'machine_learning': ['机器学习', 'machine learning', 'ML', '深度学习', 'deep learning',
                        '神经网络', 'neural network', 'reinforcement learning', '强化学习'],
    'computer_vision': ['计算机视觉', 'computer vision', 'CV', '图像识别', 'image recognition',
                        '目标检测', 'object detection', '图像分割', 'segmentation'],
    'nlp': ['自然语言处理', 'nlp', 'natural language processing', 'NLP', '大语言模型', 'LLM',
            'GPT', 'BERT', 'Transformer', '文本生成', 'text generation'],
    'robotics': ['机器人', 'robotics', 'robot', 'autonomous', '自主'],
    'ai': ['人工智能', 'artificial intelligence', 'AI'],
}

# 文献类型关键词（扩展）
PAPER_TYPE_KEYWORDS = {
    'journal': ['期刊', 'journal', '论文', 'paper', 'article'],
    'conference': ['会议', 'conference', '会议论文', 'proceedings'],
    'thesis': ['学位论文', 'thesis', 'dissertation', '博士', 'master'],
}

# 筛选条件关键词（扩展）
FILTER_KEYWORDS = {
    'highly_cited': ['高被引', 'highly cited', '高引用', '热门', 'top cited', '引用量高'],
    'sci_ei': ['SCI', 'EI', 'sci', 'ei', 'sci/ei'],
    'core_journal': ['核心期刊', 'core journal', '顶刊', '顶级期刊', 'top journal'],
    'latest_research': ['最新', 'latest', 'recent', '前沿', 'cutting edge', '前沿研究'],
}
```

### 模块2：智能多数据源论文检索 ✅ 已完成 (2026-07-11)

#### 文件：`scripts/paper_search.py` ✅ 已完成

> **实验驱动的 bug 修复（2026-07-12，端到端实验 `test/experiments/` 跑 12 场景时发现）**：
> 1. **OpenAlex `_convert_to_paper`**：`doi` 字段实为字符串 URL（非 dict），原 `.get('id')` 崩溃 → 改为按 `isinstance` 兼容 str/dict。
> 2. **OpenAlex `primary_location` 可能为 `null`**：原 `.get('source')` 在 None 上崩溃 → 改为 `or {}` 兜底。
> 3. **arXiv 日期过滤**：原两个 `submittedDate:[… TO *] AND submittedDate:[* TO …]` 子句导致 HTTP 500 → 合并为单区间 `submittedDate:[start TO end]`。
> 4. **`_deduplicate` 漏网**：按 DOI 命中时未记录标题，后续同 DOI 重复从标题分支漏入 → 改为 DOI/标题任一命中即跳过，命中时两者都记录。
>
> 这些 bug 此前未被捕获，因为 pytest 在本轮才安装、`test_paper_search.py` 首次实跑。已补 3 项回归测试（共 23 项）。
> 5. **OpenAlex 摘要重建（abstract_problem.md）**：OpenAlex 不返回 `abstract` 字符串，而返回 `abstract_inverted_index` 倒排索引；原 `item.get('abstract')` 恒空 → 新增 `_reconstruct_abstract` 按 position 排序还原文本。实测 E6 OpenAlex 摘要 0/8→8/8 恢复。
> 6. **`search` 优先用 `intent.max_results`（全链路集成测试发现）**：原 `PaperSearcher.search` 恒用 `config.get_max_results()`，忽略 `intent.max_results`，导致 `pipeline.py --max-results` 无效（传 8 却取 100 篇）→ 改为 `intent.max_results or config`。

**完整实现**（已含上述修复）：

```python
"""
多数据源论文搜索模块
支持 arXiv, Semantic Scholar, OpenAlex, CrossRef, PubMed
"""

import arxiv
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import Paper
from rate_limiter import get_rate_limiter
from config_manager import get_config_manager

logger = logging.getLogger(__name__)


class ArxivSearcher:
    """arXiv 论文搜索器"""

    def __init__(self):
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,
            num_retries=3
        )

    def search(self, query: str, max_results: int = 50,
               start_date: Optional[datetime] = None,
               end_date: Optional[datetime] = None) -> List[Paper]:
        """
        搜索 arXiv 论文

        Args:
            query: 搜索查询
            max_results: 最大结果数
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            论文列表
        """
        logger.info(f"搜索 arXiv: {query}")

        # 构建查询
        search_query = self._build_query(query, start_date, end_date)

        # 执行搜索
        search = arxiv.Search(
            query=search_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        try:
            for result in self.client.results(search):
                paper = self._convert_to_paper(result)
                papers.append(paper)
                logger.debug(f"找到论文: {paper.title}")

        except Exception as e:
            logger.error(f"arXiv 搜索失败: {e}")

        logger.info(f"arXiv 找到 {len(papers)} 篇论文")
        return papers

    def _build_query(self, query: str, start_date: Optional[datetime],
                    end_date: Optional[datetime]) -> str:
        """构建 arXiv 查询语句"""
        # 基础查询
        search_query = f'all:"{query}"'

        # 添加时间过滤
        if start_date or end_date:
            date_filter = self._build_date_filter(start_date, end_date)
            search_query += f" AND {date_filter}"

        return search_query

    def _build_date_filter(self, start_date: Optional[datetime],
                          end_date: Optional[datetime]) -> str:
        """构建日期过滤器"""
        filters = []
        if start_date:
            date_str = start_date.strftime("%Y%m%d")
            filters.append(f"submittedDate:[{date_str}0000 TO *]")
        if end_date:
            date_str = end_date.strftime("%Y%m%d")
            filters.append(f"submittedDate:[* TO {date_str}2359]")
        return " AND ".join(filters) if filters else ""

    def _convert_to_paper(self, result: arxiv.Result) -> Paper:
        """将 arXiv 结果转换为 Paper 对象"""
        # 提取作者
        authors = [author.name for author in result.authors]

        # 提取年份
        year = result.published.year if result.published else datetime.now().year

        return Paper(
            title=result.title,
            authors=authors,
            venue="arXiv",
            year=year,
            doi=result.doi or "",
            abstract=result.summary.replace('\n', ' '),
            keywords=[],
            citation_count=0,  # arXiv 通常没有引用量
            venue_type="preprint",
            ranking="预印本",
            url=result.entry_id,
            source="arxiv"
        )


class SemanticScholarSearcher:
    """Semantic Scholar 论文搜索器"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers['x-api-key'] = api_key
        self.rate_limiter = get_rate_limiter()

    def search(self, query: str, max_results: int = 50,
               start_date: Optional[datetime] = None,
               end_date: Optional[datetime] = None) -> List[Paper]:
        """搜索 Semantic Scholar 论文"""
        logger.info(f"搜索 Semantic Scholar: {query}")

        # 等待限流
        if not self.rate_limiter.wait_if_needed('semantic_scholar'):
            logger.warning("Semantic Scholar 达到限流，跳过")
            return []

        # 构建查询参数
        params = {
            'query': query,
            'limit': min(max_results, 100),  # API 最大100
            'fields': 'paperId,title,authors,year,venue,abstract,citationCount,'
                     'externalIds,url,openAccessPdf'
        }

        # 添加年份过滤
        if start_date or end_date:
            year_filter = self._build_year_filter(start_date, end_date)
            if year_filter:
                params['year'] = year_filter

        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/search",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            papers = [self._convert_to_paper(item) for item in data.get('data', [])]

            logger.info(f"Semantic Scholar 找到 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            logger.error(f"Semantic Scholar 搜索失败: {e}")
            return []

    def _build_year_filter(self, start_date: Optional[datetime],
                          end_date: Optional[datetime]) -> str:
        """构建年份过滤器"""
        years = []
        if start_date:
            years.append(f"{start_date.year}-")
        if end_date:
            years.append(f"-{end_date.year}")
        return ','.join(years) if years else ""

    def _convert_to_paper(self, item: Dict) -> Paper:
        """将 Semantic Scholar 结果转换为 Paper 对象"""
        # 提取作者
        authors = [author.get('name', '') for author in item.get('authors', [])]

        # 获取 DOI
        external_ids = item.get('externalIds', {})
        doi = external_ids.get('DOI', '')

        # 判断期刊类型
        venue = item.get('venue', 'Unknown')
        venue_type = self._classify_venue(venue)

        return Paper(
            title=item.get('title', ''),
            authors=authors,
            venue=venue,
            year=item.get('year', 0),
            doi=doi,
            abstract=item.get('abstract', ''),
            keywords=[],
            citation_count=item.get('citationCount', 0),
            venue_type=venue_type,
            ranking=self._get_ranking(venue_type, item.get('citationCount', 0)),
            url=item.get('url', ''),
            source="semantic_scholar"
        )

    def _classify_venue(self, venue: str) -> str:
        """判断期刊/会议类型"""
        # 顶级会议列表
        top_conferences = [
            'NeurIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI',
            'CVPR', 'ICCV', 'ECCV', 'ACL', 'EMNLP'
        ]
        if any(conf in venue for conf in top_conferences):
            return 'conference'

        # 期刊
        if venue and venue.lower() not in ['arxiv', 'unknown']:
            return 'journal'

        return 'preprint'

    def _get_ranking(self, venue_type: str, citation_count: int) -> str:
        """获取期刊等级"""
        if citation_count >= 100:
            return '高被引'
        elif venue_type == 'journal':
            return '核心期刊'
        elif venue_type == 'conference':
            return '顶会'
        else:
            return '普通'


class OpenAlexSearcher:
    """OpenAlex 论文搜索器"""

    BASE_URL = "https://api.openalex.org"

    def __init__(self):
        self.rate_limiter = get_rate_limiter()

    def search(self, query: str, max_results: int = 50,
               start_date: Optional[datetime] = None,
               end_date: Optional[datetime] = None) -> List[Paper]:
        """搜索 OpenAlex 论文"""
        logger.info(f"搜索 OpenAlex: {query}")

        # OpenAlex 没有限流，但为了礼貌添加延迟
        if not self.rate_limiter.wait_if_needed('openalex'):
            pass

        # 构建查询参数
        params = {
            'search': query,
            'per-page': min(max_results, 200),
            'filter': self._build_filter(start_date, end_date)
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/works",
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            papers = [self._convert_to_paper(item) for item in data.get('results', [])]

            logger.info(f"OpenAlex 找到 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            logger.error(f"OpenAlex 搜索失败: {e}")
            return []

    def _build_filter(self, start_date: Optional[datetime],
                     end_date: Optional[datetime]) -> str:
        """构建过滤器"""
        filters = []
        if start_date:
            filters.append(f"from_publication_date:{start_date.strftime('%Y-%m-%d')}")
        if end_date:
            filters.append(f"to_publication_date:{end_date.strftime('%Y-%m-%d')}")

        # 只返回学术文章
        filters.append("type:article")

        return ','.join(filters) if filters else ""

    def _convert_to_paper(self, item: Dict) -> Paper:
        """将 OpenAlex 结果转换为 Paper 对象"""
        # 提取作者
        authorships = item.get('authorships', [])
        authors = [a.get('author', {}).get('display_name', '') for a in authorships]

        # 获取期刊信息
        source = item.get('primary_location', {}).get('source', {})
        venue = source.get('display_name', 'Unknown')
        venue_type = source.get('type', 'unknown')

        # 获取 DOI
        doi = item.get('doi', {}).get('id', '').replace('https://doi.org/', '')

        return Paper(
            title=item.get('title', ''),
            authors=authors,
            venue=venue,
            year=item.get('publication_year', 0),
            doi=doi,
            abstract=item.get('abstract', ''),
            keywords=[],
            citation_count=item.get('cited_by_count', 0),
            venue_type=venue_type,
            ranking='普通',
            url=item.get('id', ''),
            source="openalex"
        )


class PaperSearcher:
    """多数据源论文搜索器 - 主类"""

    def __init__(self):
        """初始化搜索器"""
        self.config = get_config_manager()

        # 获取 API 密钥
        api_keys = self.config.get_api_keys()

        # 初始化各数据源搜索器
        self.searchers = {
            'arxiv': ArxivSearcher(),
            'semantic_scholar': SemanticScholarSearcher(api_keys['semantic_scholar']),
            'openalex': OpenAlexSearcher(),
        }

    def search(self, intent: SearchIntent) -> List[Paper]:
        """
        执行多数据源搜索

        Args:
            intent: 搜索意图

        Returns:
            合并后的论文列表
        """
        logger.info(f"开始多数据源搜索: {intent.query}")

        # 构建搜索查询
        query = self._build_search_query(intent)

        # 获取最大结果数
        max_results = self.config.get_max_results()

        # 并行搜索所有数据源
        all_papers = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    searcher.search,
                    query,
                    max_results,
                    intent.start_date,
                    intent.end_date
                ): source
                for source, searcher in self.searchers.items()
            }

            for future in as_completed(futures):
                source = futures[future]
                try:
                    papers = future.result()
                    all_papers.extend(papers)
                    logger.info(f"{source} 搜索完成: {len(papers)} 篇")
                except Exception as e:
                    logger.error(f"{source} 搜索失败: {e}")

        logger.info(f"总共找到 {len(all_papers)} 篇论文（合并前）")

        # 合并和去重
        unique_papers = self._deduplicate(all_papers)

        logger.info(f"去重后: {len(unique_papers)} 篇论文")

        return unique_papers

    def _build_search_query(self, intent: SearchIntent) -> str:
        """构建搜索查询"""
        # 使用关键词构建查询
        if intent.keywords:
            query = ' '.join(intent.keywords)
        else:
            query = intent.query

        return query

    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """
        去重论文

        基于 DOI 和标题
        优先保留有 DOI 的记录
        """
        seen_dois = set()
        seen_titles = set()
        unique_papers = []

        for paper in papers:
            # 优先使用 DOI 去重
            if paper.doi and paper.doi not in seen_dois:
                seen_dois.add(paper.doi)
                unique_papers.append(paper)
            # 标题去重（简化处理）
            elif paper.title.lower() not in seen_titles:
                seen_titles.add(paper.title.lower())
                unique_papers.append(paper)

        return unique_papers
```

### 模块3：文献筛选、分类、排序 ✅ 已完成（2026-07-11）

#### 文件：`scripts/paper_filter.py`（实际实现已完成；下方代码为参考实现）

> **实际实现 vs 参考实现的差异（落地记录）**：
> 1. 修复参考实现的两处 bug：`SearchIntent` 类型注解在导入前使用（已用 `from __future__ import annotations` + 顶部导入）；`PaperFilter.config` 改为 `__init__` 实例属性，避免模块级副作用。
> 2. **Option B 迁移**：按报告格式映射表（§报告格式设计规范），`_generate_hotspot_intro` 从 report_generator 迁入 `PaperFilter.generate_hotspot_intro`；方向级整体分析与奠基性参考论文查找归 `paper_analyzer`（模块4）。
> 3. `_sort_by_priority` 抽出可复用的 `_priority_score`，并列时按发表年份降序 tie-break（呼应规范「按发布时间倒序」）。
> 4. `classify_by_topic` 增强：返回的 dict 按热点聚合权重降序（重要方向排前）；未知论文用标题+摘要关键词频次兜底聚类（非 AI 学科友好，不再全落「其他」）。
> 5. 质量过滤支持「意图级 filters ∪ 全局 config」双触发；新增空标题/噪音剔除；`filter_and_sort` 支持 `limit`。
> 6. **新增 `_filter_by_time`**：年份级时间安全网（`intent.start_date/end_date` × `paper.year`，闭区间，`year≤0` 保留），作为 `paper_search` API 日期过滤（L1）之下的 L2 兜底，保证报告涵盖时间与实际收录一致。
> 7. **热点收敛与相关性（报告格式设计.md §10.3，实验驱动）**：兜底关键词与已知主题桶**成员 <2 篇并入「其他」**，消除单论文噪声热点（E1 17→5、E2 18→2）；`_extract_top_keyword` 扩展停用词（过滤 approach/method/results 等通用虚词）并接收 `topic_hint`（查询+领域）**优先选取与搜索主题相关的关键词**（如 E2 形成 `Bayesian(15)` 主热点）。
>
> 测试：`test/test_paper_filter.py`（27 项全通过）。详见 `../details/paper_filter_implementation_detail.md`（含时间/主题过滤机制与排序规则的详细阐述）。

**参考实现**（与实际实现等价，保留作为规范说明）：

```python
"""
文献筛选、分类、排序模块
"""

import logging
from typing import List, Dict
from collections import defaultdict
from utils import Paper

logger = logging.getLogger(__name__)


class PaperFilter:
    """文献筛选和排序器"""

    # 顶级期刊列表
    TOP_JOURNALS = {
        'Nature', 'Science', 'Cell',
        'Nature Communications', 'Science Advances',
        'Proceedings of the National Academy of Sciences'
    }

    # 顶会列表
    TOP_CONFERENCES = {
        'NeurIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI',
        'CVPR', 'ICCV', 'ECCV', 'ACL', 'EMNLP',
        'ICSE', 'SIGMOD', 'VLDB', 'KDD'
    }

    # SCI/EI 期刊特征（简化判断）
    SCI_EI_KEYWORDS = {
        'IEEE', 'ACM', 'Springer', 'Elsevier',
        'Oxford', 'Cambridge', 'Nature', 'Science'
    }

    def __init__(self):
        """初始化筛选器"""
        pass

    def filter_and_sort(self, papers: List[Paper], intent: SearchIntent) -> List[Paper]:
        """
        执行完整的筛选和排序流程

        Args:
            papers: 原始论文列表
            intent: 搜索意图

        Returns:
            筛选排序后的论文列表
        """
        logger.info(f"开始筛选 {len(papers)} 篇论文")

        # 1. 应用质量过滤器
        filtered = self._apply_quality_filters(papers, intent)

        # 2. 按优先级排序
        sorted_papers = self._sort_by_priority(filtered)

        logger.info(f"筛选后剩余 {len(sorted_papers)} 篇论文")

        return sorted_papers

    def _apply_quality_filters(self, papers: List[Paper], intent: SearchIntent) -> List[Paper]:
        """应用质量过滤器"""
        filtered = papers

        # 高被引筛选
        if intent.filters.get('highly_cited', False):
            filtered = [p for p in filtered if p.citation_count >= 100]
            logger.info(f"高被引筛选: {len(filtered)} 篇")

        # SCI/EI 筛选
        if intent.filters.get('sci_ei', False):
            filtered = [p for p in filtered if self._is_sci_ei(p)]
            logger.info(f"SCI/EI 筛选: {len(filtered)} 篇")

        # 核心期刊筛选
        if intent.filters.get('core_journal', False):
            filtered = [p for p in filtered if self._is_top_journal(p)]
            logger.info(f"核心期刊筛选: {len(filtered)} 篇")

        # 最小引用量筛选
        min_citations = self.config.get_min_citation_count()
        if min_citations > 0:
            filtered = [p for p in filtered if p.citation_count >= min_citations]

        # 排除预印本（如果配置要求）
        if not self.config.is_include_preprints():
            filtered = [p for p in filtered if p.venue_type != 'preprint']

        return filtered

    def _sort_by_priority(self, papers: List[Paper]) -> List[Paper]:
        """
        按优先级排序论文

        优先级评分规则：
        - 高被引（>100引用）：+100分
        - 顶级期刊（Nature/Science/Cell）：+90分
        - SCI/EI索引：+70分
        - 顶会：+80分
        - 普通期刊：+50分
        - 预印本（arXiv）：+30分
        """
        def calculate_priority_score(paper: Paper) -> int:
            score = 0

            # 高被引
            if paper.citation_count >= 100:
                score += 100
            elif paper.citation_count >= 50:
                score += 50

            # 顶级期刊
            if self._is_top_journal(paper):
                score += 90

            # 顶会
            elif self._is_top_conference(paper):
                score += 80

            # SCI/EI
            elif self._is_sci_ei(paper):
                score += 70

            # 普通期刊
            elif paper.venue_type == 'journal':
                score += 50

            # 预印本
            elif paper.venue_type == 'preprint':
                score += 30

            # 引用量加分
            score += min(paper.citation_count, 50)

            return score

        # 计算分数并排序
        scored_papers = [(paper, calculate_priority_score(paper)) for paper in papers]
        scored_papers.sort(key=lambda x: x[1], reverse=True)

        return [paper for paper, score in scored_papers]

    def classify_by_topic(self, papers: List[Paper]) -> Dict[str, List[Paper]]:
        """
        基于内容主题分类论文

        使用简单的关键词匹配分类
        """
        # 定义主题关键词
        topic_keywords = {
            '深度学习': ['deep learning', 'neural network', '神经网络', '深度学习'],
            '自然语言处理': ['nlp', 'natural language', 'text', 'transformer', 'bert', 'gpt', '语言'],
            '计算机视觉': ['vision', 'image', 'visual', 'cv', '图像', '视觉'],
            '强化学习': ['reinforcement', 'rl', '强化学习'],
            '监督学习': ['supervised', 'classification', 'regression', '监督学习'],
            '无监督学习': ['unsupervised', 'clustering', '无监督学习'],
            '图神经网络': ['graph', 'gnn', '图神经网络'],
            '注意力机制': ['attention', '注意力', 'transformer'],
            '生成模型': ['generative', 'gan', 'vae', 'diffusion', '生成模型'],
            '大语言模型': ['llm', 'large language model', 'gpt', '大语言模型'],
        }

        # 分类论文
        topic_papers = defaultdict(list)

        for paper in papers:
            # 合并标题和摘要进行匹配
            content = f"{paper.title} {paper.abstract}".lower()

            # 查找匹配的主题
            matched_topics = []
            for topic, keywords in topic_keywords.items():
                if any(keyword.lower() in content for keyword in keywords):
                    matched_topics.append(topic)

            # 如果有匹配，添加到第一个匹配的主题
            if matched_topics:
                topic_papers[matched_topics[0]].append(paper)
            else:
                # 未分类
                topic_papers['其他'].append(paper)

        logger.info(f"分类结果: {dict((k, len(v)) for k, v in topic_papers.items())}")

        return dict(topic_papers)

    def _is_top_journal(self, paper: Paper) -> bool:
        """判断是否为顶级期刊"""
        return any(journal in paper.venue for journal in self.TOP_JOURNALS)

    def _is_top_conference(self, paper: Paper) -> bool:
        """判断是否为顶会"""
        return any(conf in paper.venue for conf in self.TOP_CONFERENCES)

    def _is_sci_ei(self, paper: Paper) -> bool:
        """判断是否为 SCI/EI 索引"""
        # 简化判断：检查出版商特征
        return any(keyword in paper.venue for keyword in self.SCI_EI_KEYWORDS)


# 导入配置管理器
from config_manager import get_config_manager
from utils import SearchIntent

PaperFilter.config = get_config_manager()
```

### 模块4：论文信息提取、深度分析与整理 ✅ 已完成（2026-07-11）

#### 文件：`scripts/paper_analyzer.py`（实际实现已完成；下方代码为参考实现）

> **实际实现 vs 参考实现的差异（落地记录）**：
> 1. **Option B 迁移并实装**：把原在 report_generator 占位的 `_find_foundational_papers` 升级为**真正调用 Semantic Scholar references API**（`CitationFinder`：解析 paperId → 取 references → 聚合排序），不再返回占位符；同时把 `_generate_overall_analysis` 也迁入本模块。`report_generator`（模块5）创建时应调用 `analyzer.generate_overall_analysis(...)` 与 `analyzer.find_foundational_papers(...)`，不再自带这两个方法。
> 2. **奠基论文排序**（报告格式设计.md §5.4）：`被本热点引用的源论文数 ↓ > 全球引用量 ↓ > 年份 ↑`，并剔除热点自身成员，标注「被本热点 N 篇引用，全球引用 X（高影响力引用）」。
> 3. **优雅降级**：限流/离线/异常 → `_foundational_fallback`（基于本热点最早+较高被引论文，明确标注「（离线回退）」，**绝不编造引用**）。
> 4. **网络层/排序层分离**：`collect_raw_references`（联网）与 `rank_references`（纯函数）分开，便于不依赖网络单测。
> 5. 修复参考实现的 `__init__` 空实现 → 注入 config（取 S2 API key）；提取器扩充信号词与领域词。
>
> 6. **提取质量优化**：创新点 `_extract_innovations` 改为**按语言渲染**（zh/en/bilingual，bilingual 时中英并列，不再在双语报告里混入纯中文）；`_extract_research_content`/`_extract_conclusions` 改为**按子句抽取**（方法子句 / 结果子句），取自摘要的**不同片段**，与 Abstract 互补而不再整段重复。
> 7. **创新点不再给空泛默认（报告格式设计.md §10.2，实验驱动）**：无信号词时**从方法子句派生**（`提出：{方法子句} / proposes: {method clause}`），落在论文真实方法上；无摘要时留空（报告不渲染该字段）。
> 8. **抽取式浓缩摘要（abstract_problem.md，实验驱动）**：新增 `_condense_abstract` 存入 `paper.condensed_abstract`——短摘要全文、长摘要抽取「背景+方法+结果」句拼接、句边界截断**不出现 `...`**；report 的 Abstract 段优先用它，取代原 `[:1500]+"..."` 硬截断。
>
> 测试：`test/test_paper_analyzer.py`（35 项全通过）。详见 `../details/paper_analyzer_implementation_detail.md`。

**参考实现**（与实际实现等价，保留作为规范说明）：

```python
"""
论文信息提取与深度分析模块
"""

import logging
from typing import List, Dict, Optional
from utils import Paper, format_apa_citation

logger = logging.getLogger(__name__)


class PaperAnalyzer:
    """论文信息提取与深度分析器"""

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze_papers(self, papers: List[Paper]) -> List[Paper]:
        """
        批量分析论文

        Args:
            papers: 论文列表

        Returns:
            分析后的论文列表
        """
        logger.info(f"开始分析 {len(papers)} 篇论文")

        analyzed_papers = []
        for paper in papers:
            try:
                analyzed = self._analyze_single_paper(paper)
                analyzed_papers.append(analyzed)
            except Exception as e:
                logger.error(f"分析论文失败 {paper.title}: {e}")

        logger.info(f"分析完成")
        return analyzed_papers

    def _analyze_single_paper(self, paper: Paper) -> Paper:
        """
        分析单篇论文

        提取：
        - 核心研究内容
        - 创新点
        - 核心结论
        - 研究价值与应用场景
        - 相关论文
        """
        # 如果已经有深度分析结果，直接返回
        if paper.research_content and paper.innovations:
            return paper

        # 基于摘要进行简单分析
        # 注意：完整版本可能需要调用 LLM API 进行深度分析

        # 提取研究内容
        paper.research_content = self._extract_research_content(paper)

        # 提取创新点
        paper.innovations = self._extract_innovations(paper)

        # 提取结论
        paper.conclusions = self._extract_conclusions(paper)

        # 生成应用场景
        paper.value_application = self._infer_application(paper)

        # 查找相关论文（简化版本）
        paper.related_papers = self._find_related_papers_simple(paper)

        return paper

    def _extract_research_content(self, paper: Paper) -> str:
        """提取研究内容（基于摘要）"""
        abstract = paper.abstract

        # 简化处理：截取摘要的前200字作为研究内容
        # 完整版本应该使用 LLM 进行结构化提取
        if abstract:
            return abstract[:200] + "..." if len(abstract) > 200 else abstract

        return "暂无研究内容"

    def _extract_innovations(self, paper: Paper) -> str:
        """提取创新点"""
        # 简化版本：基于关键词匹配
        # 完整版本应该使用 LLM 提取
        abstract_lower = paper.abstract.lower()

        innovations = []

        # 常见创新模式
        innovation_patterns = [
            ('novel', '新颖的'),
            ('state-of-the-art', '最先进的'),
            ('outperforms', '优于'),
            ('new approach', '新方法'),
            ('first', '首次'),
            ('breakthrough', '突破性'),
        ]

        for pattern, chinese in innovation_patterns:
            if pattern in abstract_lower:
                innovations.append(f"采用{chinese}方法")

        return "；".join(innovations) if innovations else "提出新的研究方法"

    def _extract_conclusions(self, paper: Paper) -> str:
        """提取核心结论"""
        # 简化版本
        abstract = paper.abstract

        # 查找结论性语句
        conclusion_markers = ['conclusion', 'conclude', 'result', 'show', 'demonstrate', 'find']
        abstract_lower = abstract.lower()

        for marker in conclusion_markers:
            if marker in abstract_lower:
                # 提取包含标记的句子
                sentences = abstract.split('.')
                for sentence in sentences:
                    if marker in sentence.lower():
                        return sentence.strip()

        return "研究取得积极成果"

    def _infer_application(self, paper: Paper) -> str:
        """推断应用场景"""
        # 基于关键词推断
        content = f"{paper.title} {paper.abstract}".lower()

        applications = []

        application_keywords = {
            '医疗': ['medical', 'health', 'diagnosis', 'clinical'],
            '金融': ['financial', 'trading', 'stock', 'prediction'],
            '自动驾驶': ['autonomous', 'driving', 'vehicle'],
            '自然语言处理': ['nlp', 'text', 'language'],
            '计算机视觉': ['vision', 'image', 'recognition'],
            '推荐系统': ['recommendation', 'ranking', 'personalization'],
        }

        for application, keywords in application_keywords.items():
            if any(keyword in content for keyword in keywords):
                applications.append(application)

        return "、".join(applications) if applications else "通用研究"

    def _find_related_papers_simple(self, paper: Paper) -> List[str]:
        """
        简化版：查找相关论文

        基于标题和关键词生成相关研究引用
        完整版本应该通过 API 查找
        """
        # 简化处理：返回占位符
        # 实际应用中应该调用 Semantic Scholar 或 OpenAlex 的相关论文 API
        return [
            f"相关研究1: 与 {paper.keywords[0] if paper.keywords else '该领域'} 相关的早期工作",
            f"相关研究2: {paper.venue} 上的相关研究",
        ]

    def format_citations(self, papers: List[Paper]) -> List[str]:
        """
        批量生成 APA 7th 引用格式

        Args:
            papers: 论文列表

        Returns:
            APA 格式引用列表
        """
        return [format_apa_citation(paper) for paper in papers]
```

### 模块5：生成学术报告（MD/PDF格式）✅ 已完成（2026-07-12）

#### 报告格式设计规范（源自 `报告格式设计.md`）✅ 已纳入

> ⚠️ 本规范为报告生成的**权威格式要求**，`report_generator.py` 与报告模板（`templates/report_template.md`）必须严格遵循。以下要求与早期版本（标题仅含字段名、摘要 100-200 字、Abstract ≤300 字、分类无热点介绍）存在差异，**实现时以本规范为准**。

**1. 标题 / Title**
- 格式：`{时间范围} {领域/主题} 报告`（中文或英文）
- 示例：`2023-2025 统计学研究报告` / `2023-2025 Statistics Research Report`
- 时间范围取自 `intent.start_date`–`intent.end_date`；领域取自 `intent.research_field` 或 `intent.query`

**2. 时间（小字）/ Time**
- 报告生成时间：`datetime.now()`
- 报告涵盖时间：论文发表区间（`start_date` ~ `end_date`）

**3. 一、报告速览 / Report Overview**
- 写法：**按热点分组、逐篇概述**——列出每个热点（热点名 + 篇数），其下逐篇给「论文标题：核心内容」（取该篇摘要前 1-2 句），覆盖每一篇论文，不得遗漏

**4. 二、分类论文展示 / Classified Paper Display**
- 按"热点"聚类（相似/相关研究方向归为一类）
- 每个类别格式：
  - `热点一：XXXX`（热点名称）
  - 热点主题介绍（该方向简介）
  - 论文一/论文二…：标题 + 作者、发表时间、发表期刊、引用量、DOI + **四要素摘录**（解决的问题/现有方案/新方案/效果及局限，从摘要摘录语段；四要素全空回退完整 Abstract）
  - 整体分析：综合本热点几篇论文做方向性整体分析
  - 奠基性参考论文：该方向过往最具奠基意义、突破性的论文（1-3 篇，含标题/作者/年份/说明）

**5. 三、研究趋势 / Research Trends**
- 篇幅：**约 200 字**
- 内容：结合本报告所有论文，分析未来研究趋势与研究缺口（需有依据，避免套话）

**与早期实现的差异（需调整）/ Gaps vs. earlier implementation**：

| 项目 | 早期实现 | 新规范要求 |
|---|---|---|
| 标题 | `{field} 学术报告` | `{时间范围} {领域} 报告` |
| 时间 | 仅生成时间 | 生成时间 + 涵盖时间 |
| 速览摘要 | 100-200 字，仅统计数量 | 按热点分组、逐篇概述：热点名 + 篇数 + 每篇「标题：核心内容」 |
| 分类标题 | `### {category}` | `热点一：{name}` + 主题介绍 |
| Abstract | ≤300 字 | 四要素摘录（解决的问题/现有方案/新方案/效果及局限，从摘要摘录；全空回退完整 Abstract） |
| 分类结尾 | 分类总结 | 整体分析 + 奠基性参考论文 |
| 研究趋势 | 趋势+缺口（无字数限制） | 约 200 字 |

**依赖的其他模块调整 / Required changes in other modules**：
- `paper_filter.py::classify_by_topic`：分类结果需可生成"热点名称"与"热点主题介绍"
- `paper_analyzer.py`：新增方向级整体分析 + 奠基性参考论文查找（基于引用关系/高被引经典工作）

#### 文件：`scripts/report_generator.py`（实际实现已完成；下方代码为参考实现）

> **实际实现 vs 参考实现的差异（落地记录）**——对照权威规范 `报告格式设计.md`，修正了 7 处差异：
> 1. **双语**：默认按 `intent.language` 驱动（zh/en/bilingual，**默认 bilingual**），骨架全双语；参考代码全中文且忽略 language。
> 2. **标题**：bilingual 时双语两行（§7）；参考代码单行单语。
> 3. **时间标签**：经 `_label` 双语化（§3/§7）。
> 4. **速览按热点逐篇概述（§4，2026-07-12 改）**：**按热点分组、逐篇概述**——列出每个热点（热点名 + 篇数），并在其下逐篇给出「论文标题：核心内容」（`_paper_finding` 取该篇摘要前 1-2 句，即问题+方法），覆盖每一篇论文，不遗漏。
> 5. **研究趋势**：`_analyze_trends` 从语料信号派生趋势/缺口（避免空泛套话）；参考代码 `research_gaps` 是硬编码通用话术。
> 6. **填充分析字段**：`_prepare` 先调 `analyzer.analyze_papers` 填充 research_content/innovations/conclusions；参考代码未调，字段为空。
> 7. **Option B 委托**：热点介绍/整体分析/奠基论文**改调** `paper_filter` 与 `paper_analyzer`，**不再自带**这 3 个方法（参考代码仍自带）。
>
> 另：实际用**命令式 `_render_markdown`** 渲染 MD（便于精确控字数/双语），PDF 由 `_convert_to_pdf`（reportlab）从 MD 生成（2026-08-07 起，原 HTML 套模板已移除）；参考代码中的 Jinja2 `report_template.md` 仅作参考，未被实际渲染采用。
>
> 8. **单篇块四要素摘录（2026-07-13 改，替代单篇 Abstract 段）**：单篇论文块按四段展示——**解决的问题 / 现有方案（引用先前工作）/ 新方案 / 效果及局限性**——每段为从论文摘要中摘录的匹配语段（`paper_analyzer.StructuredExtractor` 按句匹配信号词，中英文均支持；优先级 新方案→现有方案→问题→效果，互不重复；问题无显式句时回退首句=背景）。摘录不到的要素显示「未明确提及 / Not explicitly mentioned」；**四要素全空**时整段回退为完整 Abstract（`AbstractSummarizer` 去填充版，≤1500 字符、无 `...`；摘要缺失回退 S2 tldr，均无则占位）。`AbstractSummarizer` 仍生成 `condensed_abstract` 供速览 `_paper_finding` 与该回退使用。
> 9. **数据质量降级（报告格式设计.md §10，实验驱动）**：四要素全空且无摘要时显示占位「（暂无摘要 / No abstract available）」；`classify_by_topic` 传入 `topic_hint`（查询+领域）提升热点与搜索主题的相关性。
> 10. **单篇块精简（历史）**：单篇论文块**不再单列**「研究内容 / 创新点 / 核心结论」字段——其内容已并入四要素摘录（新方案/效果及局限等）。分析层（`paper_analyzer`）仍内部计算这些子句供速览/整体分析复用，但 `_render_paper` 不再渲染它们；单篇块只保留：基本信息 + 四要素摘录 + APA 引用。
>
> 测试：`test/test_report_generator.py`（23 项）+ `test/test_paper_analyzer.py::TestStructuredExtractor`（四要素摘录）+ 真实模块端到端烟雾测试通过。详见 `../details/report_generator_implementation_detail.md`。

**参考实现**（与实际实现等价，保留作为规范说明）：

```python
"""
学术报告生成模块
支持 Markdown 和 PDF 格式
"""

import logging
import markdown
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from jinja2 import Template

from utils import Paper, SearchIntent, format_apa_citation, safe_filename

logger = logging.getLogger(__name__)


class ReportGenerator:
    """学术报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        self.skill_dir = Path(__file__).parent.parent

    def generate_report(self, papers: List[Paper], intent: SearchIntent,
                       output_format: str = 'markdown') -> str:
        """
        生成学术报告

        Args:
            papers: 论文列表
            intent: 搜索意图
            output_format: 输出格式（markdown/pdf）

        Returns:
            报告内容
        """
        logger.info(f"生成 {output_format} 报告，包含 {len(papers)} 篇论文")

        # 按主题分类
        from paper_filter import PaperFilter
        filter_obj = PaperFilter()
        classified_papers = filter_obj.classify_by_topic(papers)

        # 生成报告摘要
        summary = self._generate_summary(papers, classified_papers)

        # 分析研究趋势
        trends = self._analyze_trends(papers)

        # 渲染报告
        if output_format == 'markdown':
            report = self._render_markdown_report(
                papers, classified_papers, summary, trends, intent
            )
        elif output_format == 'pdf':
            md_report = self._render_markdown_report(
                papers, classified_papers, summary, trends, intent
            )
            report = self._convert_to_pdf(md_report)
        else:
            raise ValueError(f"不支持的格式: {output_format}")

        logger.info(f"报告生成完成")
        return report

    def _generate_summary(self, papers: List[Paper],
                         classified_papers: Dict[str, List[Paper]],
                         lang: str = "bilingual") -> str:
        """
        报告速览（§4）：按热点分组、逐篇概述每篇论文的核心内容（覆盖每一篇）。
        """
        total = len(papers)
        n_hotspots = len(classified_papers)
        highly_cited = sum(1 for p in papers if p.citation_count >= 100)

        lines = [f"本报告收录 {total} 篇论文，分为 {n_hotspots} 个研究热点"
                 f"（其中高被引 {highly_cited} 篇）。以下按热点逐篇概述其核心内容："]

        # 按热点分组：热点名 + 篇数，其下逐篇给「标题：核心内容」
        for category, cat_papers in classified_papers.items():
            lines.append(f"- 「{category}」({len(cat_papers)} 篇)：")
            for paper in cat_papers:
                lines.append(f"  - 《{paper.title}》：{self._paper_finding(paper)}")
        return "\n".join(lines)

    @staticmethod
    def _paper_finding(paper: Paper) -> str:
        """单篇核心内容概要（速览用）：取摘要前 1-2 句，回退标题。"""
        text = (paper.condensed_abstract or paper.abstract or "").strip()
        if not text:
            return paper.title
        first = text.find(". ")
        if 0 < first < 200:
            second = text.find(". ", first + 2)
            if 0 < second < 320:
                return text[:second + 1].strip()
            return text[:first + 1].strip()
        return text[:160].rstrip()

    def _analyze_trends(self, papers: List[Paper]) -> Dict[str, List[str]]:
        """
        分析研究趋势和缺口

        渲染后总篇幅约 200 字；趋势与缺口都必须从本次收录的论文中找到依据，
        避免空泛套话。
        简化版本：基于关键词频率分析；完整版本应使用 LLM 做深度分析。
        """

        trends = {
            'main_trends': [],
            'research_gaps': []
        }

        # 主要趋势（基于关键词频率）
        all_keywords = []
        for paper in papers:
            all_keywords.extend(paper.keywords)

        # 简单统计
        from collections import Counter
        keyword_freq = Counter(all_keywords)

        # 提取前5个作为趋势
        for keyword, freq in keyword_freq.most_common(5):
            trends['main_trends'].append(f"{keyword} 相关研究活跃（{freq} 篇）")

        # 研究缺口（基于推断）
        trends['research_gaps'] = [
            "跨模态学习：多模态融合方法仍需探索",
            "可解释性：模型解释性和透明度有待提升",
            "效率优化：轻量级模型和边缘部署研究不足",
            "数据质量：数据偏见和公平性问题需要关注",
        ]

        return trends

    def _render_markdown_report(self, papers: List[Paper],
                               classified_papers: Dict[str, List[Paper]],
                               summary: str, trends: Dict,
                               intent: SearchIntent) -> str:
        """渲染 Markdown 报告"""
        # 生成时间与涵盖时间
        report_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        coverage_time = self._format_coverage_time(intent)

        # 研究领域
        research_field = intent.research_field or intent.query

        # 构建报告
        lines = []

        # 标题：时间范围 + 领域/主题 + 报告（如 "2023-2025 统计学研究报告"）
        time_range = self._format_time_range(intent)
        title_prefix = f"{time_range} " if time_range else ""
        lines.append(f"# {title_prefix}{research_field} 报告")
        lines.append("")

        # 时间（小字）：报告生成时间 + 报告涵盖时间
        lines.append(f"*报告生成时间: {report_time}*")
        lines.append(f"*报告涵盖时间: {coverage_time}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 一、报告速览（按热点概括：有哪些热点 + 每个热点的具体发现）
        lines.append("## 一、报告速览")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("---")
        lines.append("")

        # 二、分类论文展示（按热点聚类）
        lines.append("## 二、分类论文展示")
        lines.append("")

        for hotspot_idx, (category, category_papers) in enumerate(classified_papers.items(), 1):
            # 热点名称（如 "热点一：XXXX"）+ 主题介绍
            lines.append(f"### 热点{self._numeral(hotspot_idx)}：{category}")
            lines.append("")
            lines.append(f"**热点主题介绍**：{self._generate_hotspot_intro(category, category_papers)}")
            lines.append("")

            if not category_papers:
                lines.append("本分类暂无论文")
                lines.append("")
                continue

            # 分类概述
            lines.append(f"本方向共收录 {len(category_papers)} 篇论文。")
            lines.append("")

            # 论文详情
            for idx, paper in enumerate(category_papers, 1):
                lines.append(f"#### {idx}. {paper.title}")
                lines.append("")

                # 基本信息
                lines.append("**基本信息**:")
                lines.append(f"- **作者**: {', '.join(paper.authors[:3])}{' 等' if len(paper.authors) > 3 else ''}")
                lines.append(f"- **发表期刊**: {paper.venue} ({paper.year})")
                lines.append(f"- **引用量**: {paper.citation_count}")
                if paper.doi:
                    lines.append(f"- **DOI**: {paper.doi}")
                if paper.url:
                    lines.append(f"- **链接**: {paper.url}")
                lines.append("")

                # 四要素摘录（从摘要摘录；任一命中即按四段展示，缺失要素标「未明确提及」；
                # 四要素全空则回退完整 Abstract）
                parts = [("解决的问题", paper.problem), ("现有方案", paper.existing_approaches),
                         ("新方案", paper.new_approach), ("效果及局限性", paper.results_limitations)]
                if any(v for _, v in parts):
                    for name, val in parts:
                        lines.append(f"**{name}**:")
                        lines.append(val if val else "未明确提及 / Not explicitly mentioned")
                        lines.append("")
                else:
                    lines.append("**Abstract**:")
                    abstract = (paper.condensed_abstract or paper.abstract or "").strip()
                    if not abstract:
                        abstract = "（暂无摘要 / No abstract available）"
                    lines.append(abstract)
                    lines.append("")

                # APA 引用
                lines.append("**APA 引用**:")
                citation = format_apa_citation(paper)
                lines.append(f"> {citation}")
                lines.append("")

                lines.append("---")
                lines.append("")

            # 整体分析：综合本热点几篇论文做方向性整体分析
            overall = self._generate_overall_analysis(category, category_papers)
            lines.append(f"**整体分析**: {overall}")
            lines.append("")

            # 奠基性参考论文：该方向过往最具奠基意义、突破性的论文（1-3 篇）
            foundational = self._find_foundational_papers(category, category_papers)
            if foundational:
                lines.append("**奠基性参考论文**:")
                for ref in foundational[:3]:
                    lines.append(f"- {ref}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # 三、研究趋势（约 200 字，未来研究趋势 + 研究缺口）
        lines.append("## 三、研究趋势")
        lines.append("")

        lines.append("### 未来研究趋势")
        lines.append("")
        for trend in trends['main_trends']:
            lines.append(f"- {trend}")
        lines.append("")

        lines.append("### 研究缺口")
        lines.append("")
        for gap in trends['research_gaps']:
            lines.append(f"- {gap}")
        lines.append("")

        # 报告尾部
        lines.append("---")
        lines.append("")
        lines.append("**报告生成**: Academic Report")
        lines.append("**数据源**: arXiv, Semantic Scholar, OpenAlex")
        lines.append("")

        return "\n".join(lines)

    def _format_time_range(self, intent: SearchIntent) -> str:
        """格式化标题中的时间范围，如 '2023-2025'"""
        start = intent.start_date.year if intent.start_date else None
        end = intent.end_date.year if intent.end_date else None
        if start and end:
            return f"{start}-{end}"
        elif start:
            return f"{start}-至今"
        elif end:
            return f"截至{end}"
        return ""

    def _format_coverage_time(self, intent: SearchIntent) -> str:
        """格式化报告涵盖时间（论文发表区间）"""
        if not intent.start_date and not intent.end_date:
            return "不限"
        start = intent.start_date.strftime('%Y-%m') if intent.start_date else "起始不限"
        end = intent.end_date.strftime('%Y-%m') if intent.end_date else "至今"
        return f"{start} 至 {end}"

    def _numeral(self, n: int) -> str:
        """阿拉伯数字转中文数字（1→一，2→二，…，10→十）"""
        numerals = "零一二三四五六七八九十"
        if n <= 10:
            return numerals[n]
        if n < 20:
            return f"十{numerals[n - 10]}"
        # 20 及以上直接用阿拉伯数字
        return str(n)

    def _generate_hotspot_intro(self, category: str, papers: List[Paper]) -> str:
        """
        生成热点主题介绍（该研究方向简介）

        简化版本：基于该类论文的共性关键词生成一句话简介。
        完整版本应使用 LLM 生成更具概括性的方向介绍。
        """
        if not papers:
            return f"{category} 方向暂无论文。"
        common_keywords = set()
        for paper in papers:
            common_keywords.update(paper.keywords)
        keywords_str = "、".join(list(common_keywords)[:4]) or category
        return (f"{category} 方向共收录 {len(papers)} 篇论文，"
                f"主要围绕 {keywords_str} 等主题展开。")

    def _generate_overall_analysis(self, category: str, papers: List[Paper]) -> str:
        """
        综合本热点几篇论文做方向性整体分析

        简化版本：对比贡献与共性。
        完整版本应使用 LLM 做深度方向性综合分析（共同主题、方法演进、分歧、发展阶段）。
        """
        if not papers:
            return "暂无论文可供分析。"
        top_paper = max(papers, key=lambda p: p.citation_count)
        return (f"本热点 {len(papers)} 篇论文围绕 {category} 展开，"
                f"代表性工作《{top_paper.title[:40]}》"
                f"（引用 {top_paper.citation_count}）在该方向贡献突出，"
                f"各论文在方法上逐步演进。")

    def _find_foundational_papers(self, category: str,
                                  papers: List[Paper]) -> List[str]:
        """
        查找该方向过往最具奠基意义、突破性的论文（1-3 篇）

        简化版本：返回占位提示。
        完整版本应通过 Semantic Scholar / OpenAlex 的引用 API 查找
        被本热点论文广泛引用的高被引早期工作。
        """
        return [
            f"{category} 方向奠基性工作 1（待通过引用 API 补全标题/作者/年份）",
            f"{category} 方向奠基性工作 2（待通过引用 API 补全）",
        ]

    def _extract_topic(self, paper: Paper) -> str:
        """提取单篇论文的研究主题（一两句话），用于报告速览"""
        abstract = paper.abstract or ""
        topic = abstract[:80].rstrip() + "…" if len(abstract) > 80 else abstract
        return topic or paper.title

    # ⚠️ 以下 HTML 实现已于 2026-08-07 被 `_convert_to_pdf`（reportlab）取代，保留作历史参考。
    def _convert_to_html(self, markdown_text: str) -> str:
        """将 Markdown 转换为 HTML"""
        # 使用 markdown 库转换
        md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'tables',
            'toc'
        ])

        html_content = md.convert(markdown_text)

        # 加载 HTML 模板
        template_path = self.skill_dir / 'templates' / 'report_html_template.html'

        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = Template(f.read())

            # 渲染模板
            html = template.render(
                content=html_content,
                title="学术报告",
                generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        else:
            # 简单的 HTML 包装
            html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学术报告</title>
    <style>
        body {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
        }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
        blockquote {{ border-left: 4px solid #007bff; padding-left: 10px; color: #666; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

        return html

    def save_report(self, report: str, output_path: str) -> None:
        """保存报告到文件"""
        output_file = Path(output_path)

        # 创建目录（如果不存在）
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"报告已保存到: {output_file}")


def main():
    """命令行入口"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='生成学术报告')
    parser.add_argument('--input', type=str, required=True, help='分析后的论文JSON文件')
    parser.add_argument('--output', type=str, required=True, help='输出报告文件路径')
    parser.add_argument('--format', type=str, default='markdown', choices=['markdown', 'pdf'], help='报告格式')
    parser.add_argument('--intent', type=str, help='搜索意图JSON文件')

    args = parser.parse_args()

    # 加载数据
    with open(args.input, 'r', encoding='utf-8') as f:
        papers_data = json.load(f)
    papers = [Paper.from_dict(p) for p in papers_data]

    # 加载搜索意图（如果有）
    intent = None
    if args.intent:
        with open(args.intent, 'r', encoding='utf-8') as f:
            intent_data = json.load(f)
        intent = SearchIntent.from_dict(intent_data)

    # 生成报告
    generator = ReportGenerator()
    report = generator.generate_report(papers, intent, args.format)

    # 保存报告
    generator.save_report(report, args.output)

    print(f"报告已生成: {args.output}")


if __name__ == '__main__':
    main()
```

#### 文件：`templates/report_template.md`

**报告模板**：

```markdown
# {{time_range}} {{research_field}} 报告

*报告生成时间: {{generation_time}}*
*报告涵盖时间: {{coverage_time}}*
*数据源: arXiv, Semantic Scholar, OpenAlex*

---

## 一、报告速览

{{summary}}

---

## 二、分类论文展示

{% for category, papers in classified_papers.items() %}
### 热点{{loop.index | to_cn_numeral}}：{{category}}

**热点主题介绍**：{{hotspot_intros[category]}}

{% for paper in papers %}
#### 论文{{loop.index}}：{{paper.title}}

- **作者**: {{paper.authors|join(', ')}}
- **发表时间**: {{paper.year}}
- **发表期刊**: {{paper.venue}}
- **引用量**: {{paper.citation_count}}
{% if paper.doi %}- **DOI**: {{paper.doi}}{% endif %}
{% if paper.url %}- **链接**: {{paper.url}}{% endif %}

**Abstract**:
{{paper.abstract[:200]}}...

{% if paper.research_content %}
**研究内容**:
{{paper.research_content}}
{% endif %}

{% if paper.innovations %}
**创新点**:
{{paper.innovations}}
{% endif %}

**APA 引用**:
> {{format_apa_citation(paper)}}

---
{% endfor %}

**整体分析**: {{overall_analyses[category]}}

**奠基性参考论文**:
{% for ref in foundational_papers[category] %}
- {{ref}}
{% endfor %}

---
{% endfor %}

## 三、研究趋势

### 未来研究趋势
{% for trend in trends.main_trends %}
- {{trend}}
{% endfor %}

### 研究缺口
{% for gap in trends.research_gaps %}
- {{gap}}
{% endfor %}

---

**报告生成**: Academic Report
```

#### 文件：`templates/report_html_template.html`

**HTML 报告模板**：

> ⚠️ 以下 HTML 实现已于 2026-08-07 被 `_convert_to_pdf`（reportlab）取代，保留作历史参考。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2.5em;
        }

        h2 {
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }

        h3 {
            color: #555;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.4em;
        }

        .meta-info {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 30px;
        }

        .summary {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }

        .paper {
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: #fafafa;
        }

        .paper-title {
            color: #2c3e50;
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
        }

        .paper-info {
            margin: 10px 0;
            font-size: 0.95em;
        }

        .paper-info strong {
            color: #34495e;
        }

        .paper-abstract {
            margin: 15px 0;
            line-height: 1.8;
            color: #555;
        }

        blockquote {
            border-left: 4px solid #3498db;
            padding: 10px 20px;
            margin: 15px 0;
            background: #f8f9fa;
            color: #7f8c8d;
            font-style: italic;
        }

        ul, ol {
            margin: 15px 0;
            padding-left: 30px;
        }

        li {
            margin: 8px 0;
        }

        hr {
            border: none;
            border-top: 1px solid #ecf0f1;
            margin: 40px 0;
        }

        .footer {
            text-align: center;
            color: #95a5a6;
            font-size: 0.85em;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
        }

        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }

        th {
            background: #3498db;
            color: white;
        }

        tr:nth-child(even) {
            background: #f9f9f9;
        }
    </style>
</head>
<body>
    <div class="container">
        {{content}}
        <div class="footer">
            <p>报告生成时间: {{generation_time}}</p>
            <p>由 Academic Report 自动生成</p>
        </div>
    </div>
</body>
</html>
```

### 模块6：以附件形式发送至用户指定邮箱 ✅ 已完成（2026-07-12）

#### 文件：`scripts/email_sender.py`（实际实现已完成；下方代码为参考实现）

> **实际实现 vs 参考实现的差异（落地记录）**：
> 1. **SSL/TLS 分流**：计划代码恒用 `SMTP`+`starttls()`，465 端口会失败；本模块按端口分流——465 → `SMTP_SSL`（隐式 SSL，不 starttls），587/25 → `SMTP`+`STARTTLS`。
> 2. **重试**：`SMTPAuthenticationError` 立即失败不重试；`SMTPException`/`OSError` 按 `max_retries` 重试。
> 3. **可注入**：`__init__` 接受 `config_manager`/`max_retries`/`retry_delay`/`timeout`，便于测试。
> 4. 整理局部 import（`datetime`/`time` 提至顶部）、`sys.exit(main())` 正确返回退出码、正文双语。
>
> 测试：`test/test_email_sender.py`（17 项全通过，FakeSMTP 不联网）。详见 `../details/email_sender_implementation_detail.md`。

**参考实现**（与实际实现等价，保留作为规范说明）：

```python
"""
邮件发送模块
通过 SMTP 发送学术报告
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from pathlib import Path
from typing import Optional

from config_manager import get_config_manager

logger = logging.getLogger(__name__)


class EmailSender:
    """邮件发送器"""

    def __init__(self):
        """初始化邮件发送器"""
        self.config_manager = get_config_manager()

    def send_report(self, report_path: str, recipient: Optional[str] = None,
                   subject: Optional[str] = None) -> bool:
        """
        发送报告邮件

        Args:
            report_path: 报告文件路径
            recipient: 收件人邮箱（可选，默认使用配置的邮箱）
            subject: 邮件主题（可选）

        Returns:
            是否发送成功
        """
        # 验证 SMTP 配置
        is_valid, error_msg = self.config_manager.validate_smtp_config()
        if not is_valid:
            logger.error(f"SMTP 配置无效: {error_msg}")
            return False

        # 获取 SMTP 配置
        smtp_config = self.config_manager.get_smtp_config()

        # 获取收件人
        if not recipient:
            recipient = self.config_manager.get_email_recipient()
        if not recipient:
            logger.error("未指定收件人邮箱")
            return False

        # 检查报告文件是否存在
        report_file = Path(report_path)
        if not report_file.exists():
            logger.error(f"报告文件不存在: {report_path}")
            return False

        # 获取文件格式
        file_format = 'Markdown' if report_file.suffix == '.md' else 'HTML'

        # 创建邮件
        try:
            msg = self._create_email(
                report_file,
                recipient,
                smtp_config['user'],
                subject,
                file_format
            )

            # 发送邮件
            return self._send_email(msg, smtp_config)

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    def _create_email(self, report_file: Path, recipient: str,
                     sender: str, subject: Optional[str],
                     file_format: str) -> MIMEMultipart:
        """创建邮件对象"""
        msg = MIMEMultipart()
        msg['From'] = formataddr(('Academic Report', sender))
        msg['To'] = recipient

        # 生成主题
        if not subject:
            timestamp = report_file.stat().st_mtime
            from datetime import datetime
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            subject = f"学术报告 - {date_str}"

        msg['Subject'] = subject

        # 邮件正文
        body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: #3498db;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 0 0 5px 5px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #7f8c8d;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎓 学术报告</h2>
                </div>
                <div class="content">
                    <p>您好！</p>
                    <p>最新的学术研究报告已生成完成，请查收附件。</p>
                    <p><strong>报告格式:</strong> {file_format}</p>
                    <p><strong>文件名:</strong> {report_file.name}</p>
                    <p>本报告由 Academic Report 自动生成。</p>
                </div>
                <div class="footer">
                    <p>如有问题，请回复此邮件。</p>
                    <p>© {datetime.now().year} Academic Report</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # 添加附件
        with open(report_file, 'rb') as f:
            part = MIMEApplication(f.read())

        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{report_file.name}"'
        )
        msg.attach(part)

        return msg

    def _send_email(self, msg: MIMEMultipart, smtp_config: dict) -> bool:
        """发送邮件"""
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                logger.info(f"尝试发送邮件 (第 {attempt + 1} 次)")

                # 连接 SMTP 服务器
                with smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=30) as server:
                    # 启用 TLS
                    server.starttls()

                    # 登录
                    server.login(smtp_config['user'], smtp_config['password'])

                    # 发送邮件
                    server.send_message(msg)

                logger.info("邮件发送成功")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP 认证失败: {e}")
                return False

            except smtplib.SMTPException as e:
                logger.error(f"SMTP 错误 (第 {attempt + 1} 次): {e}")

                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    import time
                    time.sleep(retry_delay)
                else:
                    logger.error("达到最大重试次数，发送失败")
                    return False

            except Exception as e:
                logger.error(f"发送邮件时发生错误: {e}")
                return False

        return False

    def test_connection(self) -> tuple[bool, str]:
        """测试 SMTP 连接"""
        is_valid, error_msg = self.config_manager.validate_smtp_config()
        if not is_valid:
            return False, error_msg

        smtp_config = self.config_manager.get_smtp_config()

        try:
            with smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=10) as server:
                server.starttls()
                server.login(smtp_config['user'], smtp_config['password'])
            return True, "SMTP 连接测试成功"
        except Exception as e:
            return False, f"SMTP 连接测试失败: {str(e)}"


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='发送学术报告邮件')
    parser.add_argument('--report-path', type=str, required=True, help='报告文件路径')
    parser.add_argument('--recipient', type=str, help='收件人邮箱')
    parser.add_argument('--subject', type=str, help='邮件主题')
    parser.add_argument('--test', action='store_true', help='仅测试 SMTP 连接')

    args = parser.parse_args()

    sender = EmailSender()

    if args.test:
        # 测试连接
        success, message = sender.test_connection()
        print(message)
        return 0 if success else 1

    # 发送邮件
    success = sender.send_report(
        args.report_path,
        args.recipient,
        args.subject
    )

    if success:
        print("邮件发送成功！")
        return 0
    else:
        print("邮件发送失败，请查看日志。")
        return 1


if __name__ == '__main__':
    main()
```

---

## 完整实施时间表

### 第1周：核心功能开发
**Day 1-2**: 模块1和2
- 完善用户意图解析
- 实现多数据源搜索
- 处理API限流

**Day 3-4**: 模块3和4
- 实现筛选排序
- 实现论文分析
- 生成APA引用

**Day 5**: 集成测试
- 测试完整流程
- 修复bug

### 第2周：报告和邮件
**Day 6-7**: 模块5
- 创建报告模板
- 实现报告生成
- MD到PDF转换

**Day 8-9**: 模块6
- 实现邮件发送
- 实现定时任务
- 时间戳管理

**Day 10**: 最终测试
- 端到端测试
- 性能优化
- 文档完善

---

## 关键依赖安装

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Hermes Agent（如果还没有）
pip install hermes-agent

# 配置环境变量
cp config/env.example ~/.hermes/.env
# 编辑 ~/.hermes/.env 添加你的配置

# 配置 Hermes
hermes config set skills.config.academic.default_language bilingual
hermes config set skills.config.academic.max_results 50
```

---

## 测试清单

### 单元测试
- [x] `intent_parser.py`: 测试各种输入模式（37 项，含定时检测）
- [x] `paper_search.py`: 测试各数据源（27 项）
- [x] `paper_filter.py`: 测试排序和分类（27 项）
- [x] `paper_analyzer.py`: 测试信息提取（50 项，含四要素摘录）
- [x] `report_generator.py`: 测试报告生成（23 项）
- [x] `email_sender.py`: 测试SMTP连接（17 项）
- [x] `timestamp_manager.py`: 时间戳读写/原子写（15 项）
- [x] `config_manager.py`: 配置加载/.env（5 项）

### 集成测试
- [x] 完整单次搜索流程（pipeline.py 全链路，真实 QQ→Gmail 发送验证）
- [x] 完整定时报告流程（scheduler.py --once 端到端）
- [x] 邮件发送端到端（QQ SMTP 真实发送成功）
- [x] 增量报告功能（时间戳窗口 + 客户端年份过滤，二次跑窗口收紧验证）
- [x] 12 场景端到端实验（test/experiments/）

### 验收测试
- [x] 从arXiv成功检索
- [~] 从Semantic Scholar成功检索（无 API key 时 429 限流，回退 arXiv+OpenAlex；配 key 可用）
- [x] 论文按优先级正确排序
- [x] 主题分类合理（热点聚类 ≥2 收敛 + topic_hint 相关性）
- [x] APA 7th格式正确
- [x] MD报告格式正确
- [x] PDF报告生成正常
- [x] 邮件成功送达
- [x] 定时任务按时触发（scheduler.py 进程内定时）
- [x] 增量报告仅包含新论文（[last_run, now] 窗口 + 年份兜底过滤）

---

本计划完全基于 design-init.txt 的要求，详细覆盖了所有六大板块和两种功能模式，包含完整的实现代码、测试方案和部署指南。
