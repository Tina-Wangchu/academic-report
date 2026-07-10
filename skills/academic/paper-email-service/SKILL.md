---
name: paper-email-service
description: "Complete automated research workflow: search academic papers + generate Markdown report + send email. Use when user wants: research report, paper search with email, literature review, academic updates, scheduled research reports, automated paper notifications. Keywords: 论文报告, 学术邮件, 研究报告, 文献检索, paper report, email papers."
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
- "帮我搜索最新论文并生成Markdown报告发邮件"
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
1. **一键式学术报告生成**：从检索到发送，全流程自动化
2. **灵活的参数配置**：支持领域、时间范围、文献数量等定制
3. **定时任务管理**：支持按周期自动执行
4. **专业的Markdown报告**：包含深度研究趋势分析、创新模式识别、研究热点聚类和时间演进分析
5. **智能错误处理**：提供针对性解决方案
6. **用户友好配置**：环境变量 + 配置文件混合管理

### 集成技能
- **paper-search**：多源学术论文检索（Semantic Scholar、arXiv、CrossRef）
- **report-generator**：专业学术Markdown报告生成（包含深度研究趋势分析）
- **email-sender**：Gmail邮件自动发送（支持Markdown附件）

## Markdown Report Structure

**生成的Markdown报告包含完整的深度分析章节**：

### 1. 封面页
- 报告标题（基于检索主题）
- 检索主题、检索时间、文献数量
- 数据源信息
- 生成机构：Hermes Agent 学术检索系统

### 2. 检索概况
- 检索主题和查询语句
- 筛选条件（时间范围、文献类型等）
- 数据源覆盖范围
- 结果统计（文献数量、来源分布）

### 3. 核心论文列表
每篇论文必须包含：
- 论文标题
- 作者列表（前5位，如超过显示总数）
- 发表年份
- 期刊/会议名称
- DOI 链接
- 引用量（如有）
- 摘要（前500字）
- 原始URL

### 4. 深度研究趋势分析
- 创新模式分析（新颖性、理论、方法论、性能、应用、集成）
- 研究热点聚类（Top 10研究集群，代表性论文）
- 时间演进分析（年度趋势，新兴关键词，方法论演进）
- 研究空白识别（方法论、应用、理论空白）
- 跨学科分析（跨学科研究检测和融合机会）

### 5. 未来方向建议
- 优先研究领域（基于热点和空白的战略建议）
- 影响时间线（短期、中期、长期预期发展）

### 6. 参考文献
- 按 GB/T 7714-2015 格式排序输出所有论文
- 格式示例：`[1] 作者. 论文标题. 期刊名, 年份. DOI: xxxxx`

**重要**：报告包含智能提取的关键见解、方法论分析和趋势预测。

---

## Procedure

### 单次执行模式

#### Step 1: 收集需求

向用户确认以下信息：

- **研究主题**（必需）：用户关注的学术领域
- **时间范围**（可选）：默认近1年，支持 `1y/3y/5y/10y/unlimited`
- **文献数量**（可选）：默认10篇
- **收件邮箱**（可选）：使用默认配置中的邮箱
- **报告格式**（自动）：增强Markdown格式（包含深度趋势分析）

#### Step 2: 展示确认

以清晰格式展示配置，等待用户确认：

```
📋 报告参数确认：
- 主题：大语言模型在教育中的应用
- 时间范围：近1年
- 文献数量：10篇
- 领域优化：教育技术
- 发送到：user@example.com（默认邮箱）
- 报告格式：增强Markdown（深度趋势分析）

❓ 需要调整参数吗？
回复"确认"开始生成，或说明需要修改的部分。
```

#### Step 3: 执行工作流

展示实时执行进度：

```
🔄 开始执行工作流...

步骤1️⃣ : 正在检索学术论文...
   ✓ 找到12篇相关论文
   ✓ 数据源：Semantic Scholar, arXiv
   ✓ 时间范围：2025-07-01 至 2026-07-01

步骤2️⃣ : 正在生成Markdown报告...
   ✓ 生成封面页
   ✓ 添加论文列表
   ✓ 生成趋势分析
   ✓ 完成参考文献
   ✓ Markdown文件：AI_research_report_20260701.md

步骤3️⃣ : 正在发送邮件...
   ✓ 邮件主题：📚 大语言模型在教育中的应用 学术报告 - 2026-07-01
   ✓ 收件人：user@example.com
   ✓ 附件：AI_research_report_20260701.md
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

💾 本地保存：/tmp/AI_research_report_20260701.md
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

**Step 5.2: 网络连接问题诊断流程**

```bash
# 1. 检查SMTP_SOCKS_PROXY是否设置
echo $env:SMTP_SOCKS_PROXY  # PowerShell
echo $SMTP_SOCKS_PROXY      # Bash

# 2. 如果为空，检测本地代理
netstat -an | grep -E "7890|7897|1080" | grep LISTEN

# 3. 如果找到代理端口（如7897），设置环境变量
$env:SMTP_SOCKS_PROXY = "socks5://127.0.0.1:7897"  # PowerShell
export SMTP_SOCKS_PROXY="socks5://127.0.0.1:7897"  # Bash

# 4. 测试代理连接
python -c "import socket, socks; s = socks.socksocket(); s.setproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 7897); s.settimeout(10); s.connect(('smtp.gmail.com', 587)); print('✅ 代理连接成功')"

# 5. 测试邮件发送
python ${HERMES_SKILL_DIR}/../my-category/email-sender/scripts/send_email.py \
  --to $env:GMAIL_ADDRESS \
  --subject "测试" \
  --body "测试内容" \
  --body-type plain
```

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
- 格式：Markdown附件（.md文件）

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
  format: "markdown"         # 报告格式：markdown（与PDF内容相同）
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

### Gmail 认证问题
**问题**：使用登录密码而非应用专用密码
**修复**：引导用户前往 https://myaccount.google.com/apppasswords 生成16位应用专用密码

**问题**：修改Google密码后应用专用密码自动失效
**修复**：重新生成应用专用密码并更新环境变量

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

### 检索无结果
**问题**：关键词过于具体或时间范围过窄

**🔴 修复原则 - 用户约束保护 (CRITICAL)**：
当检索结果为0时，**绝对禁止**擅自修改用户指定的参数。必须遵循以下流程：

#### ✅ 正确的处理流程

```bash
1. 检索结果为0时，告知用户：
   "⚠️ 使用指定参数未找到相关论文"

2. 展示实际使用的参数：
   "🔍 检索参数：
    - 主题：[用户指定的主题]
    - 时间范围：[用户指定的时间范围，如近1年]
    - 关键词：[用户指定的关键词]
    - 数据源：[实际使用的数据源]"

3. 提供建议方案：
   "💡 可能的原因：
    - 时间范围过窄（近1年相关论文较少）
    - 关键词过于具体
    - 该领域近期发表论文较少

   🎯 建议的调整方案：
    1. 扩大时间范围：3年 / 5年 / 10年
    2. 调整关键词：更通用的术语
    3. 更换检索策略"

4. **询问用户**（等待用户确认）：
   "❓ 请选择：
    - '扩大到3年' / '扩大到5年' / '不改，我要最新的' / '调整关键词为xxx'"

5. **按用户指示**重新执行检索
```

#### ❌ 错误的处理流程（绝对禁止）

```bash
# ❌ 严禁这样做：
Agent: "时间范围筛选为近一年...但当前返回的论文年份集中在2021-2024，
未满足筛选条件。我将改用近3年重新检索以获取足够的近期论文。"
# → 问题：擅自修改用户参数，未征求用户同意

# ❌ 严禁这样做：
Agent: [自动将1y改为5y] → [重新检索] → [返回结果]
# → 问题：用户不知情地收到了不符合其约束的结果
```

#### 为什么这个原则很重要？

1. **用户意图明确**：用户指定"近一年"是有原因的（如只需要最新研究）
2. **透明度原则**：用户有权知道何时其约束条件无法满足
3. **控制权原则**：用户可能更偏好"无结果"而非"较旧的论文"
4. **信任基础**：擅自修改参数会破坏用户对Agent的信任

#### 实际示例对比

**❌ 错误示例（实际发生过）**：
```
User: "检索近一年的AI论文"
Agent Output: "时间范围筛选为近一年（2025-07-01至2026-07-01），但当前返回的论文年份
集中在2021-2024，未满足筛选条件。我将改用近3年重新检索以获取足够的近期论文。"
→ 问题：Agent擅自将用户指定的"近一年"改为"近3年"，未征求用户同意
```

**✅ 正确示例（应该这样做）**：
```
User: "检索近一年的AI论文"
Agent Output: "⚠️ 使用指定参数未找到相关论文。

🔍 检索参数：
- 主题：AI论文
- 时间范围：近1年 (2025-07-01 至 2026-07-01)
- 数据源：Semantic Scholar, arXiv, CrossRef

💡 建议：近1年相关论文较少，可以扩大到3年或5年。

❓ 是否需要调整？请回复：
- '扩大到3年' / '扩大到5年' / '不改，我要最新的'"
User: "扩大到5年"
Agent: [按用户指示执行5年检索]
```

#### 模板响应（可直接使用）

```markdown
📊 检索结果：0篇论文

🔍 检索参数：
- 主题：{用户指定的主题}
- 时间范围：{用户指定的时间范围}
- 关键词：{用户指定的关键词}
- 数据源：{实际使用的数据源}

💡 可能的原因：
- 时间范围过窄（该时间范围内相关论文较少）
- 关键词过于具体（匹配不到相关文献）
- 该领域近期发表论文较少

🎯 建议的调整方案：
1. 扩大时间范围：3年 / 5年 / 10年 / 不限年份
2. 调整关键词：更通用的术语
3. 更换检索策略：指定不同领域或数据源

❓ 请选择：
- 扩大到3年
- 扩大到5年
- 不改，我要最新的
- 调整关键词为[您建议的关键词]
- 取消检索
```

**关键提醒**：
- 🚨 **CRITICAL**: 永远不要"替用户做决定"
- 🚨 **CRITICAL**: 永远不要"悄悄修改参数"
- 🚨 **CRITICAL**: 永远不要"假设用户会同意"
- ✅ **ALWAYS**: 先告知 → 再询问 → 后执行

### 每日发送上限
**问题**：Gmail个人账户每天最多500封邮件
**修复**：控制定时任务频率，避免超限

### 附件大小限制
**问题**：PDF报告超过25MB附件上限
**修复**：控制文献数量在20篇以内，或使用Markdown格式

### PDF生成失败
**问题**：未安装reportlab库
**修复**：`pip install reportlab`，或使用Markdown格式替代

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

结果：每个周一自动收到包含近7天AI论文的Markdown报告（.md文件）
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
3. 生成专业Markdown报告（与PDF内容相同）
4. 立即发送邮件（.md文件附件）

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

# 验证Markdown生成
python ../report-generator/scripts/generate_report.py --input test_papers.json --output test.md

# 验证论文检索
python ../paper-search/scripts/paper_search.py --topic "test" --max-results 1
```

## Integration Notes

本技能集成以下现有技能，通过subprocess调用：

### 集成的技能
- **paper-search**: `${HERMES_SKILL_DIR}/../paper-search/scripts/paper_search.py`
- **report-generator**: `${HERMES_SKILL_DIR}/../report-generator/scripts/generate_report.py`
- **email-sender**: `${HERMES_SKILL_DIR}/../email-sender/scripts/send_email.py`

### 数据流转
```
用户输入 → paper_search (JSON) → report_generator (Markdown) → email_sender (邮件 + .md附件)
```

### 临时文件管理
- 统一临时目录：`/tmp/paper_email_service/`
- 文件命名：带时间戳的唯一文件名
- 清理策略：成功后自动清理，失败时保留调试

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