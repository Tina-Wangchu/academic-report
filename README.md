# Agent Scholar for Hermes Agent

> 智能化学术论文搜索、分析、报告生成与邮件发送系统

[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-Skill-blue)](https://hermes-agent.nousresearch.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📖 简介

Agent Scholar 是一个功能完整的 Hermes Agent Skill，能够通过自然语言触发，自动执行学术论文检索、智能筛选排序、深度分析、生成学术报告并通过邮件发送。

### 核心功能

- 🔍 **多数据源检索**：支持 arXiv、Semantic Scholar、OpenAlex 等多个学术数据源
- 🎯 **智能筛选排序**：高被引论文优先，SCI/EI 期刊优先级排序
- 📊 **深度分析**：提取论文核心信息、创新点、结论，生成 APA 7th 引用格式
- 📄 **报告生成**：生成 Markdown 和 HTML 双格式学术报告
- 📧 **邮件发送**：自动将报告通过 SMTP 发送到指定邮箱
- ⏰ **定时报告**：支持周期性增量报告（每周/每月）

---

## ✨ 功能特性

### 六大核心模块

| 模块 | 功能 | 状态 |
|------|------|------|
| **用户意图解析** | 解析自然语言，提取检索参数 | ✅ 完成 |
| **多数据源检索** | 并行搜索多个学术数据源，处理 API 限流 | ✅ 完成 |
| **智能筛选排序** | 优先级排序、热点聚类、质量过滤 | ✅ 完成 |
| **信息提取分析** | 提取核心信息、APA 引用、方向级分析与奠基论文；四要素 LLM 生成式分析（智谱 GLM，分层回退） | ✅ 完成 |
| **报告生成** | 四段式 MD/HTML、双语、热点聚类、速览逐篇概述、单篇四要素摘录（问题/现有方案/新方案/效果及局限）、研究趋势 | ✅ 完成 |
| **邮件发送** | SMTP/SSL 发送报告附件、重试、连接测试 | ✅ 完成 |

### 支持的数据源

| 数据源 | 类型 | API 限制 | 说明 |
|--------|------|----------|------|
| [arXiv](https://arxiv.org/) | 预印本 | 无限制 | ✅ 已接入 · 最新研究成果 |
| [Semantic Scholar](https://www.semanticscholar.org/) | 综合学术 | 5000次/天 | ✅ 已接入 · AI 驱动学术搜索 |
| [OpenAlex](https://openalex.org/) | 开放索引 | 无限制 | ✅ 已接入 · 开放学术元数据 |
| [CrossRef](https://www.crossref.org/) | 文献元数据 | 10次/秒 | ⏳ 预留（rate_limiter 已配置，Searcher 未接入） |
| PubMed | 生物医学 | 3次/秒 | ⏳ 预留（同上） |

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **Hermes Agent**: 最新版本
- **操作系统**: Linux、macOS 或 Windows

### 安装步骤

#### 1. 安装 Hermes Agent

```bash
pip install hermes-agent
```

#### 2. 安装本技能

```bash
# 克隆项目
git clone https://github.com/your-username/agent-scholar-2.0.git
cd agent-scholar-2.0

# 安装依赖
pip install -r agent-scholar/requirements.txt

# 安装技能到 Hermes
cp -r agent-scholar ~/.hermes/skills/academic-scholar
```

#### 3. 配置环境变量

```bash
# 复制环境变量模板
cp agent-scholar/config/env.example ~/.hermes/.env

# 编辑 ~/.hermes/.env，添加必需配置
# 必需：SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

#### 4. 配置 Hermes

```bash
hermes config set skills.config.academic.default_language bilingual
hermes config set skills.config.academic.max_results 50
hermes config set skills.config.academic.email_recipient your@email.com
```

---

## ⚙️ 配置说明

### 必需配置

#### SMTP 邮件配置

用于发送学术报告邮件。

```bash
# ~/.hermes/.env
SMTP_HOST=smtp.gmail.com        # SMTP 服务器
SMTP_PORT=587                   # SMTP 端口（TLS）
SMTP_USER=your@gmail.com       # SMTP 用户名
SMTP_PASSWORD=your-app-password # SMTP 密码或应用专用密码
```

> `config_manager` 启动时**自动加载** `~/.hermes/.env`（不覆盖已存在的环境变量），无需手动 `export`。QQ 邮箱用 `smtp.qq.com:465`(SSL)+授权码；Gmail 用应用专用密码。


**Gmail 配置示例**：
1. 访问 https://myaccount.google.com/apppasswords
2. 生成 16 位应用专用密码
3. 将密码作为 `SMTP_PASSWORD`

#### Hermes 配置

```yaml
# ~/.hermes/config.yaml
skills:
  config:
    academic:
      default_language: bilingual      # en/zh/bilingual
      default_time_range: 3y           # 1y/3y/all
      max_results: 50                  # 每个数据源最大结果数
      email_recipient: user@example.com
      include_preprints: true
      filter_highly_cited: false
      highly_cited_threshold: 100
      sci_ei_only: false
```

### 可选配置

#### API 密钥（可选）

提升 API 限流限制。

```bash
# ~/.hermes/.env
ARXIV_API_KEY=your-arxiv-key
SEMANTIC_SCHOLAR_API_KEY=your-s2s-key
```

---

## 📖 使用方法

### 单次搜索模式

生成指定时间内的完整学术报告。

```bash
hermes chat -q "/academic-scholar 搜索最近的深度学习论文"
```

**直接跑全链路**（不经 Hermes，便于调试/集成）：

```bash
cd agent-scholar/scripts
python pipeline.py "搜索最近的 machine learning 论文，生成报告并发送到我的邮箱" --max-results 8
# 可选参数：--language bilingual|zh|en  --time 3y|1y|1w  --recipient a@b.com
#          --format markdown|html  --no-email（只生成不发送）
```

> 一条命令跑完：意图解析 → 多源检索 → 筛选排序 → 深度分析 → 报告生成 → 邮件发送。
> 实测：QQ 邮箱(`smtp.qq.com:465`)真实发送成功（QQ→QQ、QQ→Gmail 均已验证）。

**示例输入**：
- "搜索最近的机器学习论文"
- "查找关于GPT的最新研究，近1年"
- "检索高被引的计算机视觉论文，SCI期刊，近3年"

### 定时报告模式（增量）

周期性发送**增量**学术报告——每次仅检索「上次报告时间 → 现在」之间更新的论文。状态持久化在 `~/.hermes/academic_scholar_timestamps.json`（每个主题一个时间戳）。

```bash
cd agent-scholar/scripts

# 进程内定时循环（解析周期短语，立即首次触发建基线，之后按周期跑增量）
python scheduler.py "每周一发送 machine learning 论文" --recipient your@email.com

# 测试：立即触发一次增量并退出
python scheduler.py "每周发送 NLP 报告" --once --recipient your@email.com

# 预演：只打印周期/下次触发时间，不运行
python scheduler.py "每月综述" --dry-run

# 直接跑一次增量（不经调度器）
python pipeline.py "每周一发送 machine learning 论文" --incremental --recipient your@email.com

# 可选 cron：需先 pip install croniter，再用标准 5 字段 cron
python scheduler.py "每周报告" --cron "0 9 * * 1" --recipient your@email.com

# 查看/重置时间戳
python timestamp_manager.py            # 查看所有主题的上次报告时间
python timestamp_manager.py --reset all
```

**单次搜索 vs 定时增量**：

| 维度 | 单次搜索 | 定时增量 |
|---|---|---|
| 触发 | `pipeline.py` 一次性 | `scheduler.py` 循环 / `--incremental` |
| 时间窗口 | 用户指定（近1年/3年…） | `[上次报告, 现在]`；首次=周期长度 |
| 论文范围 | 窗口内全部 | 仅上次报告后的新论文 |
| 状态 | 无 | `~/.hermes/academic_scholar_timestamps.json` |
| 报告 | 完整 landscape | 标题标「增量 / Incremental (since …)」 |
| 时间戳更新 | 从不 | 仅邮件发送成功后 |

**支持的周期**："每周一/每周/每两周/每个月/每天/每N天" + `weekly/monthly/daily/biweekly`。
**空增量**：本期无新论文时默认跳过邮件且不更新时间戳（`--send-empty` 可强制通知）。
**已知限制**：Semantic Scholar 仅按年过滤 + `Paper` 仅存年份，客户端只能按年兜底过滤，同年初段的论文可能漏入；单进程调度（同主题勿多开）。

### 命令行选项

```bash
# 查看技能状态
/skills

# 测试邮件配置
python3 ~/.hermes/skills/academic-scholar/scripts/email_sender.py --test

# 查看配置
hermes config show | grep academic
```

---

## 📂 项目结构

```
agent-scholar/
├── SKILL.md                    # 技能主定义文件
├── requirements.txt             # Python 依赖
├── config/                      # 配置模板
│   ├── config.example.yaml
│   └── env.example
├── scripts/                     # 核心功能模块
│   ├── __init__.py
│   ├── utils.py                # 数据模型和工具
│   ├── config_manager.py       # 配置管理
│   ├── rate_limiter.py         # API 限流处理
│   ├── intent_parser.py        # 用户意图解析 ✅
│   ├── paper_search.py         # 多数据源检索 ✅
│   ├── paper_filter.py         # 筛选排序/热点聚类 ✅
│   ├── paper_analyzer.py       # 信息分析/整体分析/奠基论文 ✅
│   ├── report_generator.py     # 报告生成(MD/HTML/双语) ✅
│   ├── email_sender.py         # 邮件发送(SMTP/SSL) ✅
│   ├── pipeline.py             # 全链路编排 + 增量分支 ✅
│   ├── timestamp_manager.py    # 定时报告时间戳(增量窗口) ✅
│   ├── scheduler.py            # 定时报告调度器(进程内定时) ✅
│   └── llm_analyzer.py         # 四要素 LLM 生成式分析(智谱GLM,分层回退) ✅
├── templates/                  # 报告模板
│   ├── report_template.md
│   └── report_html_template.html  ✅
└── references/                 # 参考文档
    ├── apa_citation_guide.md
    └── supported_apis.md
```

**状态说明**：
- ✅ 已完成
- ⏳ 待实现
- 🔴 高优先级
- 🟡 中优先级
- 🟢 低优先级

---

## 🛠️ 开发状态

### 当前进度

- [x] **实现审计修复（2026-07-14，对照 design-init.txt）**：latest_research 死特性→近期加分；CrossRef/PubMed 文档对齐（预留）；APA 7th 作者格式（≤20 全列/>20 省略号+Oxford 逗号）；parse_date_range 支持绝对日期区间+日历精确；value_application 孤儿字段→渲染。已知限制（跨语言检索、核心默认、文献类型筛选、增量年精度）见 [报告格式设计.md §13](报告格式设计.md)。全量 262 项测试通过。

- [x] **Phase 1**: 项目初始化（完成）
  - [x] 目录结构创建
  - [x] SKILL.md 定义
  - [x] 基础框架实现
  - [x] 配置管理模块
  
- [x] **Phase 2**: 核心功能实现（进行中）
  - [x] 论文搜索模块 ✅
  - [x] 文献筛选模块 ✅（时间安全网/质量过滤/优先级排序/热点聚类/热点介绍，26 项测试通过）
  - [x] 信息分析模块 ✅（结构化提取/APA/方向级整体分析/奠基论文真实 S2 API 查找；AbstractSummarizer 分层浓缩(S2 tldr→增强规则)、创新点按语言渲染，41 项测试通过）
  
- [x] **Phase 3**: 报告生成 ✅
  - [x] 报告生成器（四段式 MD/HTML、双语默认、速览按热点逐篇概述、单篇块四要素摘录：解决的问题/现有方案/新方案/效果及局限、趋势语料派生）
  - [x] HTML 模板创建（templates/report_html_template.html）
  - [x] HTML 转换（21 项测试 + 端到端烟雾测试通过）
  
- [x] **Phase 4**: 邮件发送 ✅
  - [x] SMTP 邮件发送（SSL/TLS 分流、HTML 正文+附件、重试、连接测试，17 项测试通过）
  - [x] 定时任务管理 ✅（`timestamp_manager.py` 每主题时间戳 + `scheduler.py` 进程内定时增量；客户端年份兜底过滤）
  
- [ ] **Phase 5**: 测试验证（待开始）
  - [x] config_manager.py 测试 ✅（5 项；含 ~/.hermes/.env 自动加载）
  - [x] paper_search.py 测试 ✅（27 项；含 OpenAlex 摘要重建、S2 tldr 解析、doi/null、arXiv 日期、去重回归）
  - [x] paper_filter.py 测试 ✅（27 项）
  - [x] paper_analyzer.py 测试 ✅（41 项）
  - [x] report_generator.py 测试 ✅（22 项 + 端到端烟雾测试）
  - [x] email_sender.py 测试 ✅（17 项，FakeSMTP 不联网）
  - [x] 端到端实验 ✅（test/experiments/，12 场景全通过）
  - [x] 全链路集成测试 ✅（pipeline.py：检索→筛选→分析→报告→邮件，QQ 真实发送成功）
  - [ ] 文档完善

### 预计完成时间

- **核心功能**: 2-3 周
- **测试优化**: 1 周
- **总计**: 约 3-4 周

---

## 🧪 测试

### 环境测试

```bash
# 测试 Python 环境
python3 --version

# 测试依赖安装
pip list | grep -E "arxiv|scholarly|jinja2"

# 测试 Hermes Agent
hermes chat -q "列出所有技能"
```

### 功能测试

```bash
# 测试基本搜索
hermes chat -q "/academic-scholar 搜索机器学习论文"

# 测试邮件配置
python3 agent-scholar/scripts/email_sender.py --test

# 测试完整流程（需要完成所有模块后）
hermes chat -q "/academic-scholar 搜索深度学习论文，生成报告并发送到我的邮箱"
```

---

## 📝 报告格式

生成的学术报告遵循 [`报告格式设计.md`](报告格式设计.md) 规范，结构如下：

### 报告结构

1. **标题 + 时间**：`时间范围 + 领域/主题 + 报告`（如 `2023-2025 统计学研究报告`），小字标注报告生成时间与涵盖时间
2. **一、报告速览**：按热点分组、逐篇概述每篇论文的核心内容（覆盖每一篇论文）
3. **二、分类论文展示**：按"热点"聚类展示论文
   - 热点名称 + 主题介绍
   - 每篇论文：标题、作者、发表时间、发表期刊、引用量、DOI
   - 四要素摘录：解决的问题 / 现有方案（引用先前工作）/ 新方案 / 效果及局限性（从摘要摘录语段；全空回退完整 Abstract）
   - 整体分析（综合本热点论文的方向性分析）
   - 奠基性参考论文（该方向过往奠基性工作）
   - APA 7th 引用格式
4. **三、研究趋势**：约 200 字，未来研究趋势与研究缺口分析

### 输出格式

- **Markdown**：默认格式，便于编辑和版本控制
- **HTML**：带样式的网页格式，适合分享和展示

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出改进建议！

### 贡献方式

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范

- 遵循 PEP 8 代码规范
- 添加单元测试
- 更新相关文档
- 保持代码简洁和可读性

---

## 📚 相关资源

- [Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs/)
- [Hermes Agent GitHub](https://github.com/NousResearch/hermes-agent)
- [SKILL.md 规范](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills)
- [实施计划文档](agent-scholar%20skill实施计划.md)

---

## ❓ 常见问题

### Q: 支持哪些语言的论文？

**A**: 支持英文、中文和双语检索。可通过配置 `default_language` 设置。

### Q: 如何提高论文检索量？

**A**: 调整 `max_results` 配置项，默认为每个数据源 50 篇。

### Q: 邮件发送失败怎么办？

**A**: 
1. 检查 SMTP 配置是否正确
2. Gmail 需要使用应用专用密码
3. 查看日志文件获取详细错误信息

### Q: 如何禁用预印本？

**A**: 设置 `include_preprints: false` 在 config.yaml 中。

### Q: 定时报告如何配置？

**A**: 用独立调度器 `python scheduler.py "每周一发送X领域论文" --recipient your@email.com`（进程内定时增量，不依赖 Hermes）；或单次增量 `python pipeline.py "..." --incremental`。可选 `pip install croniter` 后用 `--cron "0 9 * * 1"`。

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👥 作者

Agent Scholar Team

---

## 🙏 致谢

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) - 强大的 AI Agent 框架
- [arXiv](https://arxiv.org/) - 开放获取的学术论文预印本
- [Semantic Scholar](https://www.semanticscholar.org/) - AI 驱动的学术搜索
- [OpenAlex](https://openalex.org/) - 开放的学术索引

---

## 📮 联系方式

- 问题反馈：[GitHub Issues](https://github.com/your-username/agent-scholar-2.0/issues)
- 邮件联系：agent-scholar@example.com

---

**最后更新**: 2026-07-11

**版本**: 1.0.0
