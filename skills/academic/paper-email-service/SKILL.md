---
name: paper-email-service
description: "Complete automated research workflow: multi-source paper search + AI-powered deep analysis + HTML report + email delivery. Use when user wants: research report, paper search with email, literature review, academic updates, scheduled research reports, automated paper notifications, weekly research digest. Keywords: 论文报告, 学术邮件, 研究报告, 文献检索, 论文分析, 研究综述, paper report, email papers, research digest."
version: 1.0.0
author: agent-scholar
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [academic, research, automation, email, scheduling, integration, papers, report, literature, markdown, workflow]
    category: academic
required_environment_variables:
  - name: GMAIL_ADDRESS
    prompt: "Your Gmail address (if using Gmail)"
    help: "Your full Gmail address, e.g. you@gmail.com"
    required_for: "Sending emails via Gmail SMTP"
    alternative_to: [QQ_EMAIL_ADDRESS, WORK_EMAIL_ADDRESS, EMAIL163_ADDRESS]
  - name: GMAIL_APP_PASSWORD
    prompt: "Gmail App Password (16 chars, if using Gmail)"
    help: "Generate at https://myaccount.google.com/apppasswords — NOT your Gmail login password"
    required_for: "Gmail SMTP authentication"
    alternative_to: [QQ_EMAIL_AUTH_CODE, WORK_EMAIL_PASSWORD]

optional_environment_variables:
  - name: QQ_EMAIL_ADDRESS
    prompt: "Your QQ email address (if using QQ Mail)"
    help: "Your full QQ email address, e.g. xxx@qq.com"
    required_for: "Sending emails via QQ Mail SMTP"
    alternative_to: [GMAIL_ADDRESS]
  - name: QQ_EMAIL_AUTH_CODE
    prompt: "QQ Mail Authorization Code (16 chars, if using QQ Mail)"
    help: "Get from QQ Mail Settings → Account → SMTP Service — NOT your QQ password"
    required_for: "QQ Mail SMTP authentication"
    alternative_to: [GMAIL_APP_PASSWORD]
  - name: WORK_EMAIL_ADDRESS
    prompt: "Your WeChat Work email address (if using WeChat Work Mail)"
    help: "Your WeChat Work email address, e.g. name@company.com"
    required_for: "Sending emails via WeChat Work Mail SMTP"
    alternative_to: [GMAIL_ADDRESS]
  - name: WORK_EMAIL_PASSWORD
    prompt: "WeChat Work Mail password (if using WeChat Work Mail)"
    help: "Your WeChat Work login password (no authorization code needed)"
    required_for: "WeChat Work Mail SMTP authentication"
    alternative_to: [GMAIL_APP_PASSWORD]
  - name: EMAIL163_ADDRESS
    prompt: "Your 163 email address (if using 163 Mail)"
    help: "Your full 163 email address, e.g. xxx@163.com"
    required_for: "Sending emails via 163 Mail SMTP"
    alternative_to: [GMAIL_ADDRESS]
  - name: EMAIL163_AUTH_CODE
    prompt: "163 Mail Authorization Code (if using 163 Mail)"
    help: "Get from 163 Mail Settings → POP3/SMTP/IMAP — NOT your login password"
    required_for: "163 Mail SMTP authentication"
    alternative_to: [GMAIL_APP_PASSWORD]
  - name: EMAIL126_ADDRESS
    prompt: "Your 126 email address (if using 126 Mail)"
    help: "Your full 126 email address, e.g. xxx@126.com"
    required_for: "Sending emails via 126 Mail SMTP"
    alternative_to: [GMAIL_ADDRESS]
  - name: EMAIL126_AUTH_CODE
    prompt: "126 Mail Authorization Code (if using 126 Mail)"
    help: "Get from 126 Mail Settings — NOT your login password"
    required_for: "126 Mail SMTP authentication"
    alternative_to: [GMAIL_APP_PASSWORD]
  - name: OUTLOOK_ADDRESS
    prompt: "Your Outlook address (if using Outlook)"
    help: "Your full Outlook address, e.g. xxx@outlook.com"
    required_for: "Sending emails via Outlook SMTP"
    alternative_to: [GMAIL_ADDRESS]
  - name: OUTLOOK_PASSWORD
    prompt: "Outlook password or app password (if using Outlook)"
    help: "Use app password if 2FA enabled: https://account.live.com/proofs/AppPassword"
    required_for: "Outlook SMTP authentication"
    alternative_to: [GMAIL_APP_PASSWORD]
---

# Paper Email Service — 学术论文邮件服务

集成论文检索、报告生成和邮件发送的完整学术研究工作流自动化服务。支持单次互动执行和固定周期定时任务。

## When to Use

当用户提出以下需求时激活：

**单次报告生成 / One-Time Report**：
- "生成一份XX领域的最新研究报告发送到我邮箱"
- "帮我搜索最新论文并生成报告发邮件"
- "检索transformer在NLP中的应用文献，制作报告发送"
- "生成一份人工智能领域的研究成果报告"
- "搜索XX论文并发送到我的邮箱"
- "给我一份关于XX的学术报告"
- "Generate research report on [topic] and email it"
- "Send me a research report about [topic]"
- "Search papers on [topic] and email me the report"

**定时任务设置 / Scheduled Tasks**：
- "每周一早上8点自动发送AI领域的论文报告"
- "设置每月的统计学最新研究通知"
- "定期发送我关注领域的学术更新"
- "每周发送XX领域的最新论文"
- "每月自动给我发送研究更新"
- "Every Monday send me AI research papers"
- "Set up monthly research updates"

**工作流自动化 / Workflow Automation**：
- "自动化我的学术文献调研工作流"
- "建立定期的文献更新机制"
- "创建研究领域的定期邮件通知"

**关键触发词 / Trigger Keywords**：
- 论文报告、研究报告、学术报告、文献报告
- 发送到邮箱、邮件发送、email me、send email
- 最新研究、最新论文、latest research、recent papers
- XX领域报告、领域论文、domain papers
- 自动化报告、定期报告、scheduled report

## Quick Reference

| 需求 | 操作 |
|---|---|
| 单次报告 | 对话收集参数 → 确认 → 执行工作流 → 发送邮件 |
| 周报设置 | "每周一发送AI最新论文" → 配置参数 → 确认创建 |
| 月报设置 | "每月1号发送统计学新研究" → 配置参数 → 确认创建 |
| 查看任务 | `hermes cron list` |
| 编辑任务 | `hermes cron edit <task_id>` |
| 删除任务 | `hermes cron delete <task_id>` |

## Features

### 核心功能
1. **多源并行检索**：同时检索Semantic Scholar、arXiv、CrossRef、OpenAlex、PubMed，合并去重
2. **AI深度分析**：使用Agent自身智能对每篇论文进行结构化分析，不是照搬原文摘要
3. **智能筛选**：多维度质量评分，同方向只保留最突破创新的研究
4. **专业HTML报告**：包含封面、AI分析、论文列表、趋势分析、参考文献
5. **定时任务管理**：支持按周期自动执行
6. **智能错误处理**：提供针对性解决方案

### 集成技能
- **paper-search**：多源学术论文检索（Semantic Scholar、arXiv、CrossRef、OpenAlex、PubMed）
- **paper-summarizer**：AI论文分析摘要（由Agent自身智能驱动，非规则匹配）
- **report-generator**：专业学术HTML报告生成
- **email-sender**：邮件自动发送（支持HTML附件）

---

## ⚠️ CRITICAL: AI Analysis Requirements (MANDATORY)

**本技能的核心价值在于AI分析能力。直接照搬原始搜索结果是严重错误。**

### 禁止行为
- ❌ **直接复制**论文abstract到报告中，不做任何分析提炼
- ❌ **跳过AI分析步骤**，直接用原始API返回数据生成报告
- ❌ **只使用单一数据源**（如仅arXiv），不尝试其他数据源
- ❌ **不做去重和筛选**，让同质化论文占据报告
- ❌ **仅列出论文信息**，没有研究趋势和领域洞察

### 必须执行的分析流程

```
用户请求 → 多源并行检索 → AI深度分析 → 生成HTML报告 → 发送邮件
```

**阶段1 - 多源检索**：必须调用Semantic Scholar、arXiv、CrossRef、OpenAlex多个数据源，合并去重，通过标题/DOI相似度自动合并不同源的相同论文。遇到429限流时立即切换到其他源，不要放弃。使用精确日期计算真实7天范围（timedelta）。

**阶段2 - AI深度分析（Agent自身智能，非外部脚本）**：
- **分类整理**：将检索到的论文按研究方向/应用领域分类（如"基础设施自动化"、"模型安全"、"Agent框架"等），同类论文归入同一组
- **单篇分析**：每篇论文必须提供 ① 完整abstract原文（用户需要先看到内容才能判断价值）② Agent亮点分析（研究目标、核心方法、关键创新、主要发现、研究意义，用自己的话概括，非复制）
- **领域综述**：按分类逐一撰写研究热点、代表性研究（该方向有名的高概括性研究，展示发展现状）、研究空白（基于哪几篇论文发现的缺口）、未来方向
- **引用规范**：所有分析中必须引用具体论文标题，如"《KRCA》系统在XX方面实现了..."，禁止使用"多个研究""两项研究"等模糊表述
- **智能筛选**：多维度评分（时效性20分、影响力30分、创新性25分、相关性15分、多样性10分），同研究方向只保留得分最高的1-2篇

**阶段3 - HTML报告**：生成美观的HTML报告（非PDF、非丑陋Markdown），包含AI分析内容

**阶段4 - 邮件发送**：将HTML报告作为附件发送

---

## Report Structure (HTML Report)

**生成的HTML报告必须包含以下章节**：

### 1. 报告摘要 ⭐ 最先呈现
**位于报告正文最开头（封面页之后），让读者30秒内掌握全貌。** 格式为编号要点列表：
- 高度概括本报告覆盖的 N 篇核心论文
- 点明最重要的 2-3 个研究突破或行业动态
- 提示报告涵盖的领域分类和关键发现
- 示例："1. KRCA系统实现微服务根因定位AC@1达0.88；2. Claude Sonnet 5在BrowseComp标准刷新纪录；3. OpenAI发布GPT-5.5定位推理..."

### 2. 领域综合分析（按研究方向分类） ⭐ 核心章节
**必须由Agent基于自身智能生成，不是API返回的原始数据。**

**要求**：
- ❌ 禁止使用"多个研究显示""两项研究指出"等模糊表述
- ✅ 必须引用具体论文标题：《KRCA》显示...、《OptiAgent》指出...
- ❌ 禁止简单罗列论文标题或复制abstract
- ✅ 用自己的话分析，提炼出真正的洞察

**按研究方向分组，每组包含**：
- **研究热点**：该方向近7天的核心主题，引用具体论文说明突破点。同时提及该方向上**有名的、高概括性、突破性的代表性研究**，展示该热点的发展现状（如"该方向由DeepMind的XXX工作奠定基础，本周《YYY》在此基础上..."）
- **核心论文分析**：每篇论文包含：完整abstract原文 + Agent亮点分析（研究目标、核心方法、关键创新、主要发现、研究意义）。**用户需要先看到abstract才能判断是否要精读，亮点分析帮助快速把握价值**
- **研究空白与未来方向**：基于哪几篇论文发现的缺口，明确指出"《论文A》和《论文B》尚未解决XX问题，未来方向是..."

### 3. 检索概况
- 检索主题、筛选条件、数据源覆盖、结果统计

### 4. 参考文献
- GB/T 7714-2015 格式，按领域分类排列

**重要**：
- 第1章（报告摘要）是读者最先看到的内容，必须高度概括
- 第2章必须**按研究方向分类**，每组内论文有abstract+亮点分析+原文链接
- 所有分析中**必须引用论文标题**，不能用"多个研究"等模糊表述
- 不要"方法演进"板块——用户反馈该板块无意义
- HTML报告应使用美观CSS样式，支持打印

---

## Procedure

### 单次执行模式

#### Step 1: 收集需求

向用户确认以下信息：

- **研究主题**（必需）：用户关注的学术领域
- **时间范围**（可选）：默认近1年，支持 `1y/3y/5y/10y/unlimited`
- **文献数量**（可选）：默认10篇
- **收件邮箱**（可选）：使用默认配置中的邮箱
- **报告格式**（自动）：HTML格式（美观排版，浏览器可直接打开）
- **数据源要求**（重要）：用户通常期望**多数据源全面搜索**（Semantic Scholar、arXiv、CrossRef等），而非单一数据源

#### Step 2: 展示确认

以清晰格式展示配置，等待用户确认：

```
📋 报告参数确认：
- 主题：大语言模型在教育中的应用
- 时间范围：近1年
- 文献数量：10篇
- 领域优化：教育技术
- 发送到：user@example.com（默认邮箱）
- 报告格式：HTML（浏览器可直接打开）

❓ 需要调整参数吗？
回复"确认"开始生成，或说明需要修改的部分。
```

#### Step 3: 执行工作流

**⚠️ 重要：本步骤包含AI分析环节，不能跳过。检索完成后，你必须用自己的智能分析每篇论文，然后生成包含分析的HTML报告。**

展示实时执行进度：

```
🔄 开始执行工作流...

步骤1️⃣ : 正在多源检索学术论文...
   ✓ Semantic Scholar: 检索中...
   ✓ arXiv: 检索中...
   ✓ CrossRef: 检索中...
   ✓ OpenAlex: 检索中...
   ✓ 合并去重后：15篇高质量论文
   ✓ 质量筛选后：10篇（同方向保留最佳）
   ✓ 数据源：Semantic Scholar, arXiv, CrossRef, OpenAlex
   ✓ 时间范围：2026-07-01 至 2026-07-08（真实7天）

步骤2️⃣ : 正在进行AI深度分析...
   ✓ 分析每篇论文：研究目标、核心方法、关键创新、主要发现、研究意义
   ✓ 生成领域综合分析：研究热点、方法演进、研究空白、未来方向
   ✓ 识别高影响力研究：3篇最具突破性的论文

步骤3️⃣ : 正在生成HTML报告...
   ✓ 生成封面页
   ✓ 撰写领域综合分析（AI原创内容）
   ✓ 添加论文AI分析列表
   ✓ 生成趋势分析
   ✓ 完成参考文献
   ✓ HTML文件：AI_research_report_20260708.html

步骤4️⃣ : 正在发送邮件...
   ✓ 邮件主题：📚 大语言模型在教育中的应用 研究分析报告 - 2026-07-08
   ✓ 收件人：user@example.com
   ✓ 附件：AI_research_report_20260708.html
   ✓ 发送成功
```

#### Step 4: 报告结果

提供执行摘要：

```
✅ 完成！报告已成功发送到您的邮箱。

📊 报告摘要：
- 论文总数：12篇
- 时间范围：2025-07-01 至 2026-07-01
- 主要来源：Computers & Education, IEEE Transactions on Learning Technologies
- 高引用论文：3篇（引用量>50）

💾 本地保存：/tmp/AI_research_report_20260701.html
📧 邮件已发送，请查收。
```

#### Step 5: 邮件发送失败处理

如果邮件发送失败，按以下流程诊断：

**Step 5.1: 识别错误类型**

```bash
# 查看邮件日志
python ${HERMES_SKILL_DIR}/../my-category/email-sender/scripts/send_email.py --log-show
```

**错误类型判断**：
- `WinError 10060` / `Connection timeout` → 网络连接问题，需代理
- `Authentication failed (535)` → 密码/授权码错误
- `STARTTLS not supported` → 代理协议错误（必须是SOCKS5）

**Step 5.2: 网络连接问题诊断**

**注意**：以下命令仅供用户手动诊断使用，不应由skill自动执行。

如果出现网络连接问题，请用户**手动执行**以下诊断步骤：

```bash
# 1. 检查SMTP_SOCKS_PROXY是否设置
echo $env:SMTP_SOCKS_PROXY  # PowerShell

# 2. 设置代理（如果需要）
$env:SMTP_SOCKS_PROXY = "socks5://127.0.0.1:7897"  # PowerShell
```

**重要**：这些诊断命令需要用户在终端中手动执行，不要作为skill工作流的一部分。

**新增故障模式（2026-07-06实践）**：
- **SMTP_SSL端口465 SSL握手失败**：即使SOCKS5代理能建立TCP连接到smtp.gmail.com:465，但SSL握手时出现 `[SSL: UNEXPECTED_EOF_WHILE_READING]` 错误
- **原因**：某些SOCKS5代理不支持或错误处理SSL/TLS协议，导致握手过程中连接被提前关闭
- **测试命令**：参见上述第4步的SSL连接测试
- **解决方案**：
  1. 检查代理软件的SSL/TLS设置（可能需要开启SSL隧道功能）
  2. 切换代理节点或代理软件
  3. 作为降级方案：生成报告文件后，提示用户手动发送邮件
  4. 尝试使用其他邮件提供商（QQ邮箱、163邮箱等国内服务）

**Step 5.3: 认证失败处理**

如果出现 `Authentication failed`：
1. 引导用户检查 `GMAIL_APP_PASSWORD` 是否正确
2. 提醒必须是16位应用专用密码（非登录密码）
3. 如果修改过Google密码，需重新生成应用密码
4. 访问：https://myaccount.google.com/apppasswords

### 定时任务模式

#### Step 1: 收集任务需求

- **任务名称**：如"AI领域周报"
- **执行周期**：如"每周一早上9点"
- **研究领域**：主题、关键词、时间范围
- **收件配置**：邮箱、主题模板

#### Step 2: 展示任务配置

```
📅 定时任务配置预览：

⏰ 调度信息：
- 名称：AI领域周报
- 执行时间：每周一上午9点
- 下次执行：2026-07-06 09:00

📚 检索配置：
- 主题：人工智能和机器学习最新研究
- 时间范围：近7天
- 文献数量：15篇
- 领域优化：AI领域

📧 邮件配置：
- 收件人：user@example.com
- 主题：📚 AI周报 - {date}
- 格式：HTML附件（.html文件，浏览器可直接打开）

❓ 需要调整吗？回复"确认"创建任务，或说明需要修改的部分。
```

#### Step 3: 创建定时任务

使用 Hermes cron 系统创建任务：

```bash
hermes cron create "0 9 * * 1" \
  "执行AI周报任务，检索近7天AI领域论文，生成报告并发送邮件" \
  --name "AI周报" \
  --skill paper-email-service \
  --deliver origin
```

#### Step 4: 确认创建

```
✅ 已创建定时任务

📋 任务详情：
- 任务ID: weekly_ai_report_20260701
- 调度：每周一上午9点
- 下次执行：2026-07-06 09:00

💡 任务管理：
- 查看所有任务：hermes cron list
- 编辑此任务：hermes cron edit weekly_ai_report_20260701
- 删除此任务：hermes cron delete weekly_ai_report_20260701

🔔 您将在每个周一上午9点自动收到AI领域的最新论文报告。
```

## Configuration

### 配置文件结构

配置采用环境变量 + YAML配置文件的混合方式：

```
config/
├── default_config.yaml    # 默认配置模板
└── user_config.yaml       # 用户配置（优先级更高）
```

### 环境变量要求

本服务支持多种邮箱提供商。根据您使用的邮箱服务，配置相应的环境变量：

This service supports multiple email providers. Configure the appropriate environment variables based on your email service:

#### 选择一种邮箱服务配置 / Choose One Email Service Configuration

**方式1: Gmail / Option 1: Gmail** (推荐 / Recommended)
```bash
GMAIL_ADDRESS      # Gmail完整地址，如 you@gmail.com
GMAIL_APP_PASSWORD # Gmail 16位应用专用密码（非登录密码）
```

**方式2: QQ邮箱 / Option 2: QQ Mail**
```bash
QQ_EMAIL_ADDRESS    # QQ邮箱地址，如 xxx@qq.com
QQ_EMAIL_AUTH_CODE  # QQ邮箱授权码（非QQ密码）
```

**方式3: 企业微信邮箱 / Option 3: WeChat Work Mail**
```bash
WORK_EMAIL_ADDRESS  # 企业邮箱地址，如 name@company.com
WORK_EMAIL_PASSWORD # 企业邮箱登录密码
```

**方式4: 163邮箱 / Option 4: 163 Mail**
```bash
EMAIL163_ADDRESS    # 163邮箱地址，如 xxx@163.com
EMAIL163_AUTH_CODE  # 163邮箱授权码（非登录密码）
```

**方式5: 126邮箱 / Option 5: 126 Mail**
```bash
EMAIL126_ADDRESS    # 126邮箱地址，如 xxx@126.com
EMAIL126_AUTH_CODE  # 126邮箱授权码（非登录密码）
```

**方式6: Outlook / Option 6: Outlook**
```bash
OUTLOOK_ADDRESS     # Outlook地址，如 xxx@outlook.com
OUTLOOK_PASSWORD    # Outlook密码或应用密码
```

#### 可选环境变量 / Optional Environment Variables

```bash
SMTP_SOCKS_PROXY           # SOCKS5代理（国内访问Gmail必需）
SEMANTIC_SCHOLAR_API_KEY  # Semantic Scholar API密钥（提高限流）
```

### 配置优先级

1. **用户配置** (`user_config.yaml`) - 最高优先级
2. **默认配置** (`default_config.yaml`) - 中等优先级
3. **硬编码默认值** - 最低优先级

### 配置示例

**default_config.yaml**（默认配置模板）：

```yaml
service:
  name: "Paper Email Service"
  version: "1.0.0"
  debug: false

# 默认检索参数
search_defaults:
  time_range: "1y"          # 默认时间范围：近1年
  max_results: 10          # 默认最大结果数
  sort_by: "citation_count" # 默认排序方式
  domain: "general"         # 默认领域
  output_format: "json"     # 输出格式

# 默认报告参数
report_defaults:
  format: "html"              # 报告格式：html（美观排版）
  language: "bilingual"      # 语言偏好
  include_analysis: true     # 包含趋势分析
  include_references: true   # 包含参考文献

# 默认邮件参数
email_defaults:
  from_name: "Hermes 学术助手"
  body_type: "html"          # 邮件格式
  subject_template: "📚 {topic} 学术报告 - {date}"

# 默认收件人（可覆盖）
default_recipient:
  email: "user@example.com"
  name: "默认收件人"

# 任务配置
task_settings:
  temp_dir: "/tmp/paper_email_service"
  cleanup_temp: true         # 执行后清理临时文件
  retry_on_failure: true     # 失败重试
  max_retries: 2            # 最大重试次数
  
# 日志配置
logging:
  level: "INFO"
  file: "logs/service.log"
  max_size_mb: 10
  backup_count: 3

# 预设任务模板
presets:
  weekly_ai_report:
    name: "AI领域周报"
    schedule: "0 9 * * 1"   # 每周一上午9点
    topic: "artificial intelligence and machine learning"
    keywords: "AI,machine learning,deep learning"
    time_range: "7d"         # 近7天
    max_results: 15
    
  monthly_statistics:
    name: "统计学月报"
    schedule: "0 10 1 * *"  # 每月1号上午10点
    topic: "statistical methods and decision theory"
    domain: "statistics"
    time_range: "30d"        # 近30天
    max_results: 20
    
  daily_briefing:
    name: "每日AI简报"
    schedule: "0 8 * * *"  # 每天上午8点
    topic: "AI latest research"
    time_range: "1d"         # 近1天
    max_results: 5
```

**user_config.yaml**（用户配置文件）：

```yaml
# 用户特定配置 - 此文件会被Git忽略

# 用户个人信息
user_profile:
  name: "张三"
  email: "zhangsan@example.com"

# 自定义默认参数（覆盖默认配置）
custom_defaults:
  time_range: "2y"          # 覆盖默认的1y
  max_results: 15          # 覆盖默认的10
  domain: "ai"              # 覆盖默认的general

# 自定义收件人列表
recipients:
  primary:
    - email: "zhangsan@example.com"
      name: "张三"
  secondary:
    - email: "colleague@example.com"
      name: "同事"

# 自定义定时任务
custom_tasks:
  - id: "my_custom_task"
    name: "我的自定义任务"
    schedule: "0 8 * * 1"  # 每周一上午8点
    enabled: true
    config:
      topic: "my research area"
      time_range: "7d"
      max_results: 20
```

## Pitfalls

### paper_email_service.py 主脚本导入错误
**问题**：执行 `python paper_email_service.py` 时出现 `ModuleNotFoundError` 错误：
```
ModuleNotFoundError: No module named 'utils.validators'
ModuleNotFoundError: No module named 'utils.formatters'
ModuleNotFoundError: No module named 'utils.error_handler'
```
**原因**：这些 `utils.*` 模块在技能目录中不存在，主脚本引用了未实现的辅助模块。

**修复**：使用降级工作流，直接调用子技能：
```bash
# 步骤1: 论文检索
python C:/Users/lanpi/AppData/Local/hermes/skills/academic/paper-search/scripts/paper_search.py \
  --topic "statistics" \
  --time-range 7d \
  --max-results 10 \
  --output-format json \
  --output /tmp/papers.json

# 步骤2: 生成报告
python C:/Users/lanpi/AppData/Local/hermes/skills/academic/report-generator/scripts/generate_report.py \
  --input /tmp/papers.json \
  --output /tmp/report.pdf

# 步骤3: 发送邮件
python C:/Users/lanpi/AppData/Local/hermes/skills/my-category/email-sender/scripts/send_email.py \
  --to user@gmail.com \
  --subject "报告主题" \
  --body-file /tmp/email_body.html \
  --body-type html \
  --attach /tmp/report.pdf
## Pitfalls

### 用户偏好 - 避免使用缓存/之前的报告

**用户偏好**：用户明确要求"不要用之前生成的报告 完全重新搜索"
**重要性**：当用户要求"最新"或"本周"研究报告时，必须完全重新获取数据，不能使用任何之前生成的报告或缓存数据
**正确做法**：
- 每次执行都从零开始检索
- 不引用之前会话的结果、PDF报告或缓存数据
- 即使有相同主题的历史报告，也要重新执行完整工作流
- 在报告元数据中明确标注检索日期和时间

### 用户偏好 - 文献数量与全面性

**用户偏好**：当用户说"文献数量多一点 同时要尽量全面"时
**含义**：
- 默认15篇（而非10篇）
- 尽可能覆盖多数据源（Semantic Scholar、arXiv、CrossRef、OpenAlex、PubMed）
- 同研究方向保留1-2篇最突破研究，避免同质化
- 如单一数据源受限（如API 429限流），需说明数据源限制并提供可获得的全部结果

### 技能安装问题

**问题**：缺少 `utils/__init__.py` 导致模块导入失败
**错误信息**：`ModuleNotFoundError: No module named 'utils.validators'; 'utils' is not a package`
**修复**：在 `scripts/utils/` 目录下创建空的 `__init__.py` 文件以使 Python 识别为包
**检查方法**：`ls scripts/utils/__init__.py` 应该存在

**问题**：`safe_execute` 装饰器变量作用域错误
**错误信息**：`UnboundLocalError: cannot access local variable 'exceptions_to_retry' where it is not associated with a value`
**修复**：在装饰器函数内部将 `exceptions_to_retry` 参数赋值给局部变量 `retry_exceptions`，避免与参数名冲突
**相关代码**：`error_handler.py` 中的 `safe_execute` 装饰器

### 工作流集成问题

**问题**：集成工作流失败但子技能单独执行成功
**表现**：`execute_complete_workflow` 返回 `AttributeError: 'str' object has no attribute 'get'`
**临时解决方案**：手动依次调用子技能脚本：
1. `paper_search.py` → 输出 JSON 到临时文件
2. `generate_report.py` → 使用上一步的 JSON 生成 PDF
3. `send_email.py` → 发送邮件
**根本原因**：工作流执行器在解析子技能输出时出现类型错误（字符串被当作字典处理）
**调试命令**：直接运行子技能脚本查看返回格式是否为有效 JSON

### Gmail 认证问题

**问题**：使用登录密码而非应用专用密码
**修复**：引导用户前往 https://myaccount.google.com/apppasswords 生成16位应用专用密码

**问题**：修改Google密码后应用专用密码自动失效
**修复**：重新生成应用专用密码并更新环境变量

**问题**：Gmail 认证失败 (535 错误)
**错误信息**：`(535, b'5.7.8 Username and Password not accepted')`
**诊断步骤**：
1. 验证环境变量：`echo $GMAIL_ADDRESS` 和 `echo $GMAIL_APP_PASSWORD`（检查长度应为16）
2. 确认已启用2步验证（应用专用密码必需）
3. 检查网络连接和代理：`python -c "import socket, socks; s = socks.socksocket(); s.setproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 7897); s.settimeout(10); s.connect(('smtp.gmail.com', 465)); print('OK')"`
4. 测试认证：启用 SMTP 调试模式 `server.set_debuglevel(1)` 查看详细交互
5. 访问 https://myaccount.google.com/apppasswords 重新生成密码（密码可能已过期）
**代理配置**：`SMTP_SOCKS_PROXY` 应设置为 `socks5://127.0.0.1:7897`（根据本地代理端口调整）

**问题**：STARTTLS (port 587) 在国内被阻断
**解决方案**：脚本已自动回退到 SMTP_SSL (port 465)，但认证问题仍需单独解决

**问题**：GMAIL_ADDRESS环境变量配置错误（如多字符拼写错误）
**修复**：
- 检查环境变量值是否与真实邮箱地址完全一致
- 常见错误：额外字符（tinawangchu0615@gmail.comm）、拼写错误、缺少@符号
- 诊断方法：`echo $env:GMAIL_ADDRESS` 检查实际值
- 临时修复：当前会话中设置正确值（`export GMAIL_ADDRESS="correct@email.com"`）
- 永久修复：在系统环境变量中更正，确保所有会话生效

### 网络连接问题 — Agent主动诊断流程

**问题**：国内直连 `smtp.gmail.com:587` 被阻断，出现 `[WinError 10060]` 连接超时错误

**Agent诊断步骤**（按顺序执行）：

#### Step 1: 识别错误类型
```
错误信息分析：
- WinError 10060 / Connection timeout → 网络连接问题，需要代理
- Authentication failed (535) → 密码/授权码问题，检查GMAIL_APP_PASSWORD
- STARTTLS not supported → 代理协议错误，必须是SOCKS5（非HTTP代理）
```

#### Step 2: 检查SMTP_SOCKS_PROXY环境变量
```bash
# PowerShell
echo $env:SMTP_SOCKS_PROXY

# CMD
echo %SMTP_SOCKS_PROXY%

# Bash
echo $SMTP_SOCKS_PROXY
```

**如果为空或未设置** → 进入Step 3
**如果已设置** → 跳到Step 4

#### Step 3: 检测本地代理服务
```bash
# 检查常见代理端口是否在监听
netstat -an | grep -E "7890|7897|1080|7891" | grep LISTEN
```

**如果找到端口**（如 `127.0.0.1:7897`）→ 引导用户设置环境变量：
```bash
# Windows PowerShell（当前会话）
$env:SMTP_SOCKS_PROXY = "socks5://127.0.0.1:7897"

# Windows PowerShell（永久）
[System.Environment]::SetEnvironmentVariable('SMTP_SOCKS_PROXY', 'socks5://127.0.0.1:7897', 'User')

# Bash/Mac/Linux
export SMTP_SOCKS_PROXY="socks5://127.0.0.1:7897"
```

**如果未找到代理** → 引导用户启动代理服务（Clash/V2Ray等）

#### Step 4: 测试代理能否连接到Gmail SMTP
```python
python -c "import socket, socks; s = socks.socksocket(); s.setproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 7897); s.settimeout(10); s.connect(('smtp.gmail.com', 587)); print('✅ 代理可以连接到Gmail')"
```

**如果成功** → 代理配置正确，重试邮件发送
**如果超时** → 代理本身无法访问Gmail，检查代理设置或切换代理节点

#### Step 5: 检查PySocks依赖
```bash
python -c "import socks; print('✅ PySocks已安装')" 2>&1
```

**如果报错** → 安装PySocks：
```bash
pip install pysocks
# 或
python -m pip install pysocks
```

#### Step 6: 重新测试邮件发送
```bash
# 使用email-sender直接测试
python ${HERMES_SKILL_DIR}/../my-category/email-sender/scripts/send_email.py \
  --to $env:GMAIL_ADDRESS \
  --subject "代理测试" \
  --body "测试内容" \
  --body-type plain
```

**关键提示**：
- ✅ 必须使用 **SOCKS5代理**，HTTP代理无效
- ✅ 代理端口必须是代理软件的**混合端口**（mixed port）
- ✅ 确保代理软件正在运行
- ✅ 环境变量设置后需要**重启TUI**或刷新会话

### 检索无结果或结果过少
**问题**：关键词过于具体或时间范围过窄导致0篇论文
**修复**：
- 检查时间范围是否合理（如"近一年"可能因API数据延迟导致0结果）
- 自动扩展时间范围（如从1y扩展到3y或5y）
- 使用更通用的关键词
- 在邮件中明确说明时间范围调整原因（本次会话示例：近一年无结果→扩展到近5年）
- 参考"用户约束保护"原则：宁可扩大范围获得有用结果，也不返回空报告

### 每日发送上限
**问题**：Gmail个人账户每天最多500封邮件
**修复**：控制定时任务频率，避免超限

### 附件大小限制
**问题**：HTML报告附件过大
**修复**：控制文献数量在20篇以内

### 报告格式问题（已解决）
**问题**：report-generator生成错误文件扩展名（2026-07-07实践）
**修复**：已切换为HTML报告生成器（generate_report_complex.py），直接生成.html文件，无格式混淆问题。

## Examples

### 场景1：研究人员每周接收最新论文报告

```
用户: "每周一早上8点发送AI领域的最新论文报告"

助手执行：
1. 理解需求：AI领域、周报、周一早上8点
2. 展示配置预览
3. 创建定时任务
4. 配置检索参数：topic="AI", time_range="7d", max_results=15
5. 设置邮件发送
6. 确认任务创建

结果：每个周一自动收到包含近7天AI论文的HTML分析报告
```

### 场景2：特定领域的定期文献更新

```
用户: "每月发送统计学决策理论的新研究"

助手执行：
1. 识别领域：statistics/decision theory
2. 设置月度任务：每月1号执行
3. 配置专业参数：domain="statistics", time_range="30d"
4. 生成专业报告

结果：每月自动收到统计学领域的最新研究
```

### 场景3：临时性专题文献检索

```
用户: "帮我搜索transformer在NLP中应用的最新论文，生成报告发给我"

助手执行：
1. 单次工作流执行
2. 实时检索最新论文
3. 生成专业HTML分析报告
4. 立即发送邮件

结果：几分钟后收到专题研究报告，包含最新transformer在NLP中的应用
```

### 场景4：用户有默认配置的情况

```
用户: "发送我的AI周报"（使用已配置的默认参数）

助手执行：
1. 检查用户配置文件
2. 加载预设参数
3. 立即执行工作流
4. 发送到默认邮箱

结果：快速执行，无需重复确认
```

## Verification

### 测试单次工作流

```bash
# 进入技能目录
cd C:/Users/lanpi/AppData/Local/hermes/skills/my-category/paper-email-service

# 测试核心服务
python scripts/paper_email_service.py --topic "machine learning" --test-mode

# 测试配置管理
python scripts/config_manager.py --validate

# 测试工作流执行
python scripts/workflow_executor.py --test-single-execution
```

**See also**: `references/email-troubleshooting.md` for detailed troubleshooting of Gmail SMTP connection timeouts and authentication failures.

### 测试定时任务

```bash
# 创建测试任务
hermes cron create "0 9 * * 1" "测试AI周报任务" --name "test_weekly" --skill paper-email-service

# 查看任务状态
hermes cron list

# 测试任务编辑
hermes cron edit test_weekly

# 删除测试任务
hermes cron delete test_weekly
```

### 测试完整集成

```bash
# 验证环境变量
echo $env:GMAIL_ADDRESS
echo $env:GMAIL_APP_PASSWORD

# 测试邮件发送
python ../email-sender/scripts/send_email.py --to $env:GMAIL_ADDRESS --subject "测试" --body-file "test.txt" --body-type plain

# 验证PDF生成
python ../report-generator/scripts/generate_report.py --input test_papers.json --output test.pdf

# 验证论文检索
python ../paper-search/scripts/paper_search.py --topic "test" --max-results 1
```

# Integration Notes

本技能集成以下现有技能，通过subprocess调用：

### 集成的技能
- **paper-search**: `C:\\Users\\lanpi\\AppData\\Local\\hermes\\skills\\academic\\paper-search/scripts/paper_search.py`
- **report-generator**: `C:\\Users\\lanpi\\AppData\\Local\\hermes\\skills\\academic\\report-generator/scripts/generate_report.py`
- **email-sender**: `C:\\Users\\lanpi\\AppData\\Local\\hermes\\skills\\academic/email-sender/scripts/send_email.py`（注意：路径是 academic/，不是 my-category/）

### 工作流降级策略（当主脚本失败时）

**问题**：`paper_email_service.py` 主脚本可能因模块导入错误而无法运行：
- `ModuleNotFoundError: No module named 'utils.validators'`
- `ModuleNotFoundError: No module named 'utils.formatters'`
- `ModuleNotFoundError: No module named 'utils.error_handler'`
- `UnboundLocalError: cannot access local variable 'exceptions_to_retry'`

**解决方案**：直接调用子技能（推荐 - 已验证可行）：

**场景A：paper-search API限流（HTTP 429错误）- arXiv近7天检索降级方案**

当出现 `HTTP Error 429` 或 `HTTP 500` 时，使用浏览器导航降级方案：

**步骤详解**：

1. **浏览器导航到arXiv最新提交页面**
   ```python
   browser_navigate(url="https://arxiv.org/list/stat/recent")
   ```
   - 页面显示最近几天的论文提交记录，按日期分组（如 "Tue, 7 Jul 2026"）
   - 优先提取近7天内的arXiv ID（格式：2607.05379）

2. **提取论文ID并查询arXiv API**
   ```bash
   # 使用ID列表批量查询（无需时间参数，ID本身包含时间戳）
   curl -s "https://export.arxiv.org/api/query?id_list=2607.05379,2607.05375,2607.05312,2607.05293,2607.05284,2607.05279,2607.05273,2607.05229,2607.05223" > /tmp/arxiv_response.xml
   ```

3. **解析XML响应**（使用execute_code工具）
   ```python
   import xml.etree.ElementTree as ET
   import json
   import re

   # Windows路径：C:\Users\lanpi\AppData\Local\Temp\arxiv_response.xml
   file_path = r'C:\Users\lanpi\AppData\Local\Temp\arxiv_response.xml'
   tree = ET.parse(file_path)
   root = tree.getroot()

   # 定义命名空间（必需）
   ns = {
       'atom': 'http://www.w3.org/2005/Atom',
       'arxiv': 'http://arxiv.org/schemas/atom',
       'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
   }

   papers = []
   for entry in root.findall('atom:entry', ns):
       paper = {
           'title': entry.find('atom:title', ns).text.strip(),
           'summary': entry.find('atom:summary', ns).text.strip(),
           'published': entry.find('atom:published', ns).text,
           'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
       }
       # 提取arXiv ID和URL
       paper['id'] = entry.find('atom:id', ns).text
       match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', paper['id'])
       if match:
           paper['arxiv_id'] = match.group(1)
       for link in entry.findall('atom:link', ns):
           if link.get('rel') == 'alternate':
               paper['url'] = link.get('href')
       papers.append(paper)

   # 保存为report-generator兼容的JSON格式
   with open(r'C:\Users\lanpi\AppData\Local\Temp\statistics_papers_weekly.json', 'w', encoding='utf-8') as f:
       json.dump({'status': 'success', 'query': 'statistical research recent 7 days', 'total_found': len(papers), 'papers': papers}, f, ensure_ascii=False, indent=2)
   ```

4. **生成报告**
   ```bash
   # 注意：脚本输出"Markdown report generated"，但实际创建.pdf文件
   python C:/Users/lanpi/AppData/Local/hermes/skills/academic/report-generator/scripts/generate_report.py \
     --input C:/Users/lanpi/AppData/Local/Temp/statistics_papers_weekly.json \
     --output C:/Users/lanpi/AppData/Local/Temp/statistics_weekly_report.pdf
   ```

5. **发送邮件**（禁用代理以确保端口465稳定）
   ```bash
   SMTP_SOCKS_PROXY="" python C:/Users/lanpi/AppData/Local/hermes/skills/academic/email-sender/scripts/send_email.py \
     --to user@gmail.com --subject "📚 统计学领域最新研究报告 - 2026年7月7日" \
     --body-file /tmp/email_body.html --body-type html \
     --attach C:/Users/lanpi/AppData/Local/Temp/statistics_weekly_report.pdf
   ```

**验证成功标志**：
- 浏览器页面显示真实近期提交记录（带日期分组）
- curl成功返回XML（非HTTP 429/500）
- Python输出"✓ 成功解析 N 篇论文"
- report-generator输出"[OK] Markdown report generated"（实际为.pdf）
- 邮件发送成功

**实践验证（2026-07-07）**：成功检索9篇统计学论文（7月1日-7月7日），使用arXiv stat分类，发送PDF附件。

**详细步骤参考**: `references/arxiv-7-day-recent-workflow.md`（浏览器降级方案详细步骤，2026-07-07实践，成功检索9篇论文）

**场景B：标准降级工作流**

```bash
# 步骤1: 论文检索
python C:/Users/lanpi/AppData/Local/hermes/skills/academic/paper-search/scripts/paper_search.py \
  --topic "statistics" \
  --keywords "statistics,statistical methods,data analysis" \
  --time-range 7d \
  --max-results 10 \
  --output-format json \
  --output /tmp/papers.json

# 步骤2: 生成Markdown报告
python C:/Users/lanpi/AppData/Local/hermes/skills/academic/report-generator/scripts/generate_report.py \
  --input /tmp/papers.json \
  --output /tmp/report.md

# 步骤3: 发送邮件（如环境变量存在）
# 先创建HTML邮件正文
write_file(path='/tmp/email_body.html', content='...')
# 然后发送
python C:/Users/lanpi/AppData/Local/hermes/skills/academic/email-sender/scripts/send_email.py \
  --to user@gmail.com \
  --subject "报告主题" \
  --body-file /tmp/email_body.html \
  --body-type html \
  --attach /tmp/report.md
```

**关键要点**：
1. **使用绝对路径**：避免相对路径在不同工作目录下失败
2. **Windows路径兼容性**：使用正斜杠 `C:/Users/...` Python兼容，而非 `C:\\Users\\...`
3. **降级时机**：当 `python paper_email_service.py ...` 报 `ModuleNotFoundError` 时立即切换到子技能调用模式

### 数据流转
```
用户输入 → paper_search (JSON) → AI深度分析 → report_generator (HTML) → email_sender (邮件 + .html附件)
```

### 临时文件管理
- 统一临时目录：`/tmp/paper_email_service/`
- 文件命名：带时间戳的唯一文件名
- 清理策略：成功后自动清理，失败时保留调试

### 参考文档
- **arXiv近7天检索工作流**: `references/arxiv-7-day-recent-workflow.md` - 浏览器降级方案详细步骤（2026-07-07实践，成功检索9篇论文）
- **时间范围扩展工作流**: `references/workflow-pattern-time-range-expansion.md` - 当原始时间范围返回0篇论文时的渐进式扩展策略
- **邮件故障排查**: `references/email-troubleshooting.md` - Gmail SMTP连接超时和认证失败的详细诊断步骤
- **SMTP_SSL SSL握手失败**: `references/smtp-ssl-handshake-failure.md` - SOCKS5代理通过端口465连接Gmail时SSL握手失败的诊断和解决方案
- **arXiv API降级工作流（浏览器导航）**: `references/arxiv-api-workaround.md` - API限流和时间过滤失效时的浏览器导航降级方案
- **arXiv API降级工作流（直接查询+手动过滤）**: `references/arxiv-direct-api-with-manual-filtering.md` - paper-search脚本失败时，使用curl直接查询arXiv API并用Python脚本手动过滤时间范围
- **Windows环境变量检查模式**: `references/windows-env-var-check-pattern.md` - Windows系统上使用PowerShell检查User级别环境变量的标准模式（2026-07-08验证）

## 延伸功能

### 高级配置
- 多收件人配置
- 邮件模板自定义
- 报告样式定制
- 领域专家系统优化

### 任务管理
- 任务执行历史记录
- 任务统计分析
- 失败重试和错误恢复
- 批量任务创建

### 智能优化
- 基于历史数据的参数优化
- 搜索关键词智能推荐
- 报告内容自动总结
- 最佳发送时间分析