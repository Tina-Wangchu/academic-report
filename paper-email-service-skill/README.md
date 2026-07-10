# 📧 Paper Email Service — 学术论文邮件服务
# 📧 Paper Email Service — Academic Paper Email Service

---

## 🎯 Skill概述 / Skill Overview

**Paper Email Service** 是一个集成学术论文检索、深度分析报告生成和邮件发送的自动化研究工作流服务。支持单次执行和定时任务两种模式，让您的学术文献调研完全自动化。

**Paper Email Service** is an integrated academic research workflow automation service that combines paper retrieval, in-depth analysis report generation, and email delivery. Supports both one-time execution and scheduled tasks, making your academic literature research completely automated.

---

## ✨ 核心功能 / Key Features

### 📊 单次报告模式 / One-Time Report Mode
- **即时检索**：从多个学术数据库检索最新论文
- **专业报告**：生成包含深度趋势分析的Markdown学术报告
- **邮件发送**：自动将报告发送到您的邮箱

- **Instant Retrieval**: Search latest papers from multiple academic databases
- **Professional Reports**: Generate Markdown academic reports with in-depth trend analysis
- **Email Delivery**: Automatically send reports to your inbox

### ⏰ 定时任务模式 / Scheduled Task Mode
- **周期执行**：支持每日、每周、每月等周期任务
- **个性化配置**：自定义研究领域、时间范围、文献数量
- **自动推送**：定期接收最新研究更新，无需手动操作

- **Periodic Execution**: Supports daily, weekly, monthly recurring tasks
- **Customizable Configuration**: Personalize research field, time range, paper count
- **Automatic Delivery**: Receive regular research updates without manual effort

---

## 💬 如何在对话中使用 / How to Use in Conversation

### 单次报告生成 / One-Time Report Generation

在对话中用自然语言表达您的需求：

Express your needs in natural language during conversation:

#### 中文示例 / Chinese Examples
```
用户: "帮我生成一份机器学习领域的最新研究报告发送到我邮箱"
用户: "搜索transformer在NLP中应用的论文，制作深度分析报告发给我"
用户: "检索最近1年统计学决策理论的文献，生成报告"
用户: "我要一份关于深度强化学习的学术报告"
```

#### 英文示例 / English Examples
```
User: "Generate a latest research report in machine learning and send to my email"
User: "Search papers on transformer in NLP, create an in-depth analysis report and email it to me"
User: "Retrieve statistical decision theory literature from the past year and generate a report"
User: "I want an academic report on deep reinforcement learning"
```

### 定时任务设置 / Scheduled Task Setup

用自然语言描述定期任务需求：

Describe your recurring task needs in natural language:

#### 中文示例 / Chinese Examples
```
用户: "每周一早上8点自动发送AI领域的最新论文报告"
用户: "设置每月1号发送统计学新研究通知"
用户: "每天早上9点给我发送机器学习最新论文"
用户: "每季度发送一次计算机视觉领域的综述报告"
```

#### 英文示例 / English Examples
```
User: "Every Monday at 8 AM, automatically send me the latest AI research papers"
User: "Set up a monthly notification for new statistics research on the 1st"
User: "Send me the latest machine learning papers every day at 9 AM"
User: "Send me a quarterly overview report on computer vision research"
```

---

## 🔧 配置要求 / Configuration Requirements

### 邮箱服务选择 / Email Service Selection

本服务支持多种邮箱服务商。请根据您的邮箱选择相应配置：

This service supports multiple email providers. Choose the appropriate configuration based on your email service:

#### ✅ **推荐邮箱服务 / Recommended Email Services**

| 邮箱服务 / Service | SMTP服务器 / SMTP Server | 端口 / Port | 加密 / Encryption | 推荐度 / Rating |
|---|---|---|:---:|:---:|
| **Gmail** | smtp.gmail.com | 587 | STARTTLS | ⭐⭐⭐⭐⭐ |
| **QQ邮箱** | smtp.qq.com | 587 | STARTTLS | ⭐⭐⭐⭐⭐ |
| **企业微信邮箱** | smtp.exmail.qq.com | 587 | STARTTLS | ⭐⭐⭐⭐⭐ |
| **163邮箱** | smtp.163.com | 465 | SSL | ⭐⭐⭐⭐ |
| **126邮箱** | smtp.126.com | 465 | SSL | ⭐⭐⭐⭐ |
| **Outlook** | smtp.office365.com | 587 | STARTTLS | ⭐⭐⭐⭐ |

---

### 🌟 **配置方式 1: Gmail（推荐 / Recommended）**

#### 必需环境变量 / Required Environment Variables

```bash
# Gmail完整地址 / Full Gmail address
export GMAIL_ADDRESS="your_email@gmail.com"

# Gmail 16位应用专用密码 / 16-char Gmail App Password
export GMAIL_APP_PASSWORD="your_16_char_app_password"
```

**获取应用密码 / Get App Password**:
1. 访问 https://myaccount.google.com/apppasswords
2. 创建新应用专用密码 / Create new app-specific password
3. 复制到环境变量 / Copy to environment variable

---

### 📧 **配置方式 2: QQ邮箱 / QQ Mail**

#### 必需环境变量 / Required Environment Variables

```bash
# QQ邮箱完整地址 / Full QQ email address
export QQ_EMAIL_ADDRESS="your_qq@qq.com"

# QQ邮箱授权码（非QQ密码）/ QQ Mail Authorization Code (NOT QQ password)
export QQ_EMAIL_AUTH_CODE="your_16_char_auth_code"
```

**获取授权码 / Get Authorization Code**:
1. 登录QQ邮箱网页版 / Login to QQ Mail web version
2. 进入 **设置** → **账户** / Go to **Settings** → **Account**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务** / Find **POP3/IMAP/SMTP Services**
4. 开启 **SMTP服务** / Enable **SMTP service**
5. 点击 **生成授权码** / Click **Generate Authorization Code**
6. 通过短信验证后获得16位授权码 / Get 16-char code after SMS verification
7. 复制到环境变量 / Copy to environment variable

---

### 📧 **配置方式 3: 企业微信邮箱 / WeChat Work Mail**

#### 必需环境变量 / Required Environment Variables

```bash
# 企业微信邮箱地址 / WeChat Work email address
export WORK_EMAIL_ADDRESS="your_name@company.com"

# 企业邮箱登录密码 / WeChat Work login password
export WORK_EMAIL_PASSWORD="your_password"
```

**注意 / Note**: 企业邮箱使用登录密码即可，无需授权码。
WeChat Work uses login password directly, no authorization code needed.

---

### 📧 **配置方式 4: 163邮箱 / 163 Mail**

#### 必需环境变量 / Required Environment Variables

```bash
# 163邮箱完整地址 / Full 163 email address
export EMAIL163_ADDRESS="your_name@163.com"

# 163邮箱授权码（非登录密码）/ 163 Mail Authorization Code (NOT login password)
export EMAIL163_AUTH_CODE="your_16_char_auth_code"
```

**获取授权码 / Get Authorization Code**:
1. 登录163邮箱网页版 / Login to 163 Mail web version
2. 进入 **设置** → **POP3/SMTP/IMAP** / Go to **Settings** → **POP3/SMTP/IMAP**
3. 开启 **SMTP服务** / Enable **SMTP service**
4. 点击 **客户端授权密码** / Click **Client Authorization Password**
5. 通过短信验证后获得授权码 / Get authorization code after SMS verification
6. 复制到环境变量 / Copy to environment variable

---

### 📧 **配置方式 5: 126邮箱 / 126 Mail**

#### 必需环境变量 / Required Environment Variables

```bash
# 126邮箱完整地址 / Full 126 email address
export EMAIL126_ADDRESS="your_name@126.com"

# 126邮箱授权码（非登录密码）/ 126 Mail Authorization Code (NOT login password)
export EMAIL126_AUTH_CODE="your_16_char_auth_code"
```

**获取授权码 / Get Authorization Code**: 流程同163邮箱 / Same process as 163 Mail

---

### 📧 **配置方式 6: Outlook / Hotmail**

#### 必需环境变量 / Required Environment Variables

```bash
# Outlook完整地址 / Full Outlook address
export OUTLOOK_ADDRESS="your_name@outlook.com"

# Outlook登录密码 / Outlook login password
export OUTLOOK_PASSWORD="your_password"
```

**注意 / Note**: 
- 如果启用了双重验证，需要使用**应用密码**而非登录密码
- If 2FA is enabled, use **App Password** instead of login password
- 获取应用密码：https://account.live.com/proofs/AppPassword

---

### 🔧 **通用可选配置 / Optional Configuration**

```bash
# SOCKS5代理（国内用户访问Gmail必需）/ SOCKS5 Proxy (required for Gmail in China)
export SMTP_SOCKS_PROXY="socks5://127.0.0.1:7890"

# Semantic Scholar API密钥（提高检索限流）/ API Key (higher rate limit)
export SEMANTIC_SCHOLAR_API_KEY="your_api_key"
```

---

## 📋 使用流程 / Usage Workflow

### 单次报告流程 / One-Time Report Workflow

```
对话触发 / Conversation Trigger
    ↓
需求确认 / Requirement Confirmation
    ↓
参数配置 / Parameter Configuration
    ↓
执行工作流 / Workflow Execution
    ↓
报告发送 / Report Delivery
    ↓
完成通知 / Completion Notification
```

### 定时任务流程 / Scheduled Task Workflow

```
对话触发 / Conversation Trigger
    ↓
任务需求收集 / Task Requirement Collection
    ↓
配置预览确认 / Configuration Preview & Confirmation
    ↓
创建定时任务 / Create Scheduled Task
    ↓
周期自动执行 / Automatic Periodic Execution
    ↓
邮件推送 / Email Push Notification
```

---

## 🎨 典型使用场景 / Typical Use Cases

### 场景1：每周学术更新 / Scenario 1: Weekly Academic Updates

**需求 / Need**: 研究人员希望定期了解AI领域最新进展

**对话示例 / Conversation Example**:
```
用户: "每周一早上9点发送AI领域最新论文报告给我"

助手执行:
1. 确认研究领域：AI和机器学习
2. 设置检索范围：近7天，15篇论文
3. 配置邮件发送：每周一上午9点
4. 创建定时任务，确认配置

结果: 每周一自动收到包含最新AI研究的PDF报告
```

### 场景2：专题文献调研 / Scenario 2: Topic-Specific Literature Review

**需求 / Need**: 需要快速了解某个具体研究领域的现状

**对话示例 / Conversation Example**:
```
用户: "帮我生成transformer在计算机视觉中应用的最新研究报告"

助手执行:
1. 识别研究领域：transformer + computer vision
2. 执行论文检索：查找最新相关文献
3. 生成PDF报告：包含论文列表和分析
4. 立即发送邮件

结果: 几分钟后收到专题研究报告，包含最新论文详情
```

### 场景3：定期领域监控 / Scenario 3: Regular Domain Monitoring

**需求 / Need**: 长期关注特定研究方向的进展

**对话示例 / Conversation Example**:
```
用户: "每月1号发送统计学决策理论的新研究"

助手执行:
1. 配置专业检索：统计学 + 决策理论
2. 设置月度任务：每月1号执行
3. 优化检索参数：30天时间范围，专业领域
4. 建立定时推送

结果: 每月自动收到该领域的最新研究动态
```

---

## ⚙️ 支持的参数 / Supported Parameters

### 检索参数 / Search Parameters

| 参数 / Parameter | 说明 / Description | 默认值 / Default |
|---|---|---|
| `topic` | 研究主题 / Research topic | 用户指定 / User specified |
| `time_range` | 时间范围 / Time range | `1y` (近1年 / past 1 year) |
| `max_results` | 最大文献数 / Max papers | `10` |
| `domain` | 研究领域 / Research domain | `general` |

### 报告参数 / Report Parameters

| 参数 / Parameter | 说明 / Description | 默认值 / Default |
|---|---|---|
| `format` | 报告格式 / Report format | `pdf` |
| `language` | 语言 / Language | `bilingual` (双语 / bilingual) |
| `include_analysis` | 包含分析 / Include analysis | `true` |

### 定时任务参数 / Scheduled Task Parameters

| 参数 / Parameter | 说明 / Description | 示例 / Example |
|---|---|---|
| `schedule` | 执行周期 / Execution schedule | `"0 9 * * 1"` (每周一9点 / every Mon 9AM) |
| `name` | 任务名称 / Task name | `"AI周报"` |

---

## 🚨 故障排除 / Troubleshooting

### 🔐 认证失败问题 / Authentication Issues

#### Gmail认证失败 / Gmail Authentication Failed

**问题 / Problem**: `Authentication failed` 或 `Invalid credentials`

**解决方案 / Solutions**:
1. ✅ 确认使用应用专用密码，非登录密码 / Use app-specific password, not login password
2. 🔗 访问 https://myaccount.google.com/apppasswords 重新生成 / Regenerate at app password page
3. ✔️ 检查环境变量是否正确设置 / Verify environment variables
4. ⚠️ 如果修改过Google密码，应用密码会自动失效 / App password auto-revokes after password change

#### QQ邮箱认证失败 / QQ Mail Authentication Failed

**问题 / Problem**: `Authentication failed` 或 ` authorization failed`

**解决方案 / Solutions**:
1. ✅ 确认使用**授权码**，而非QQ登录密码 / Use **authorization code**, NOT QQ password
2. 🔗 重新生成授权码：邮箱设置 → 账户 → SMTP服务 / Regenerate: Settings → Account → SMTP
3. ✔️ 检查邮箱地址格式是否正确（如 xxx@qq.com）/ Check email format
4. ⚠️ 授权码过期后需重新生成 / Regenerate when authorization code expires

#### 163/126邮箱认证失败 / 163/126 Mail Authentication Failed

**问题 / Problem**: `Authentication failed` 或 `Login failed`

**解决方案 / Solutions**:
1. ✅ 确认使用**授权码**，而非邮箱登录密码 / Use **authorization code**, NOT login password
2. 🔗 开启SMTP服务并生成授权码 / Enable SMTP and generate authorization code
3. ✔️ 检查授权码是否已过期 / Check if authorization code expired
4. ⚠️ 部分账号需要绑定手机号才能使用SMTP / Some accounts require phone binding

#### Outlook认证失败 / Outlook Authentication Failed

**问题 / Problem**: `Authentication failed` 或 `535 5.7.3 Authentication unsuccessful`

**解决方案 / Solutions**:
1. ✅ 如果启用了双重验证，使用**应用密码** / Use **app password** if 2FA enabled
2. 🔗 获取应用密码：https://account.live.com/proofs/AppPassword
3. ✔️ 确认账户状态正常 / Verify account status is normal
4. ⚠️ 新账户可能有发送限制，需要等待几天 / New accounts may have sending limits

---

### 🌐 网络连接问题 / Network Connection Issues

#### 国内用户访问Gmail（Users in China accessing Gmail）

**问题 / Problem**: `Connection timeout` 或 `Network error` 连接 smtp.gmail.com:587

**原因 / Cause**: 国内直连Gmail SMTP服务器被阻断 / Direct connection to Gmail SMTP blocked in China

**解决方案 / Solutions**:
1. ✅ 配置SOCKS5代理 / Configure SOCKS5 proxy:
   ```bash
   export SMTP_SOCKS_PROXY="socks5://127.0.0.1:7890"
   ```
2. 📦 安装PySocks: `pip install pysocks`
3. ✔️ 确保代理服务正在运行 / Ensure proxy service is running
4. 🔍 测试代理连通性 / Test proxy connectivity:
   ```bash
   python -c "import socket; s=socket.socket(); s.settimeout(10); s.connect(('smtp.gmail.com',587)); print('OK')"
   ```

**注意 / Note**: HTTP代理无效，必须使用SOCKS5代理 / HTTP proxy doesn't work, must use SOCKS5

#### 其他邮箱连接问题 / Other Email Connection Issues

**问题 / Problem**: `Connection timeout` 或 `Network unreachable`

**解决方案 / Solutions**:
1. ✅ 检查SMTP服务器地址和端口是否正确 / Verify SMTP server and port
2. 🔍 尝试使用SSL端口（465）或STARTTLS端口（587）/ Try SSL port 465 or STARTTLS 587
3. ✔️ 检查防火墙设置 / Check firewall settings
4. 🌐 尝试切换网络环境 / Try different network

---

### 📧 发送限制问题 / Sending Limit Issues

#### Gmail发送限制 / Gmail Sending Limits

**问题 / Problem**: `Daily sending quota exceeded` 或 `Rate limit exceeded`

**解决方案 / Solutions**:
1. ⚠️ Gmail个人账户每天最多500封邮件 / Gmail personal limit: 500 emails/day
2. ⏱️ 控制定时任务频率，避免超限 / Control scheduled task frequency
3. 📊 使用 `hermes cron list` 查看任务数量 / Check task count
4. 💡 考虑升级到Google Workspace企业账户 / Consider Google Workspace

#### QQ邮箱发送限制 / QQ Mail Sending Limits

**问题 / Problem**: 发送频率过快被限制 / Limited due to high frequency

**解决方案 / Solutions**:
1. ⚠️ QQ邮箱每分钟限制发送数量 / QQ Mail has per-minute limits
2. ⏱️ 增加定时任务之间的间隔 / Increase interval between tasks
3. 📊 避免短时间内发送大量邮件 / Avoid mass sending in short time
4. 💡 升级到企业微信邮箱解除限制 / Upgrade to WeChat Work Mail

#### 163/126邮箱发送限制 / 163/126 Mail Sending Limits

**问题 / Problem**: `554 DT:SPM` 或发送被拒绝

**解决方案 / Solutions**:
1. ⚠️ 新账户有更严格的发送限制 / New accounts have stricter limits
2. 📧 经常使用邮箱提高信誉度 / Regular use improves reputation
3. ✅ 确保邮件内容符合规范 / Ensure content complies with policies
4. 📊 控制每日发送数量在合理范围 / Control daily sending volume

---

### 📎 附件问题 / Attachment Issues

#### 附件大小超限 / Attachment Size Exceeded

**问题 / Problem**: `Attachment too large` 或 `Message size exceeds fixed limit`

**解决方案 / Solutions**:
1. ⚠️ 大多数邮箱限制附件25MB / Most services limit attachment to 25MB
2. 📊 控制文献数量在20篇以内 / Limit paper count to 20
3. 📝 使用Markdown格式替代PDF / Use Markdown format instead of PDF
4. ☁️ 考虑使用云盘链接 / Consider cloud drive links

#### 附件格式不支持 / Unsupported Attachment Format

**问题 / Problem**: `Invalid attachment` 或 `File type not allowed`

**解决方案 / Solutions**:
1. ✅ 确保附件是PDF格式 / Ensure attachment is PDF format
2. 📁 检查文件路径是否正确 / Check file path is correct
3. 🔍 确认文件未损坏 / Verify file is not corrupted

---

### 🔍 论文检索问题 / Paper Retrieval Issues

#### 检索无结果 / No Papers Found

**问题 / Problem**: 找到0篇论文 / Found 0 papers

**解决方案 / Solutions**:
1. 🔍 扩大时间范围（尝试 3y 或 5y）/ Expand time range (try 3y or 5y)
2. 🎯 使用更通用的关键词 / Use more general keywords
3. 🌐 检查网络连接 / Check network connection
4. 🔑 尝试不同的关键词组合 / Try different keyword combinations
5. 📊 增加 `max_results` 参数 / Increase `max_results` parameter

#### 检索结果过少 / Too Few Results

**问题 / Problem**: 只找到1-2篇论文 / Only found 1-2 papers

**解决方案 / Solutions**:
1. ⏱️ 扩大时间范围 / Expand time range
2. 🎯 使用更广泛的关键词 / Use broader keywords
3. 📊 增加 `max_results` 到15-20 / Increase `max_results` to 15-20
4. 🌐 检查是否配置了代理（如需）/ Check proxy configuration if needed

---

### 📄 PDF生成问题 / PDF Generation Issues

#### PDF生成失败 / PDF Generation Failed

**问题 / Problem**: `Report generation failed` 或 `PDF creation error`

**解决方案 / Solutions**:
1. 📦 安装依赖库: `pip install reportlab`
2. 📁 检查临时目录权限 / Check temporary directory permissions
3. 💾 确保磁盘空间充足 / Ensure sufficient disk space
4. 📝 尝试使用Markdown格式替代PDF / Try Markdown format instead

#### PDF内容乱码 / PDF Corrupted Characters

**问题 / Problem**: PDF中显示乱码或方框 / Garbled text in PDF

**解决方案 / Solutions**:
1. 📦 安装中文字体支持 / Install Chinese font support
2. 🔧 在配置中设置字体路径 / Set font path in configuration
3. 📝 尝试英文报告 / Try English-only report

---

## 🔗 集成的技能 / Integrated Skills

本服务整合了以下三个Hermes技能：

This service integrates the following three Hermes skills:

1. **paper-search** — 多源学术论文检索 / Multi-source academic paper retrieval (Semantic Scholar, arXiv, CrossRef)
2. **report-generator** — 专业PDF报告生成 / Professional PDF report generation  
3. **email-sender** — 邮件自动发送 / Automated email delivery via SMTP

### 📧 邮箱服务支持说明 / Email Service Support

虽然本服务提供多种邮箱的配置文档，但当前 `email-sender` 技能主要针对 **Gmail SMTP** 进行优化和测试。其他邮箱服务的支持程度可能不同：

While this service provides configuration documentation for multiple email providers, the current `email-sender` skill is primarily optimized and tested for **Gmail SMTP**. Support for other email services may vary:

| 邮箱服务 / Service | 支持状态 / Status | 说明 / Notes |
|---|:---:|---|
| ✅ **Gmail** | 完全支持 / Fully Supported | 主要测试平台 / Primary test platform |
| ⚠️ **QQ邮箱** | 基本支持 / Basic Support | 需要授权码 / Requires authorization code |
| ⚠️ **企业微信** | 基本支持 / Basic Support | 使用登录密码 / Uses login password |
| ⚠️ **163/126** | 部分支持 / Partial Support | 可能需要调整 / May need adjustments |
| ⚠️ **Outlook** | 部分支持 / Partial Support | 双重验证需要应用密码 / App password for 2FA |

**注意 / Note**: 
- ✅ 推荐使用 **Gmail** 或 **QQ邮箱** 以获得最佳体验 / Use **Gmail** or **QQ Mail** for best experience
- 🔧 使用其他邮箱时可能需要调整 SMTP 服务器配置 / Other providers may need SMTP config adjustments
- 📧 如需完整的多种邮箱支持，可以考虑使用第三方邮件服务 API（如 SendGrid） / For full multi-provider support, consider third-party email APIs like SendGrid

---

## 💡 使用技巧 / Usage Tips

### 优化检索效果 / Optimize Search Results

- **使用具体关键词**：如"transformer attention mechanism"而非"AI"
- **指定时间范围**：根据需要选择 1y/3y/5y
- **设置研究领域**：AI、医学、物理学等专业领域
- **组合关键词**：使用逗号分隔多个相关术语

- **Use specific keywords**: Like "transformer attention mechanism" instead of "AI"
- **Specify time range**: Choose 1y/3y/5y based on your needs
- **Set research domain**: AI, medicine, physics, etc.
- **Combine keywords**: Use commas to separate multiple related terms

### 定时任务最佳实践 / Scheduled Task Best Practices

- **合理设置频率**：避免过于频繁导致信息过载
- **选择合适时间**：安排在您方便查阅的时间
- **定期调整参数**：根据反馈优化检索范围

- **Set reasonable frequency**: Avoid information overload
- **Choose appropriate timing**: Schedule when convenient for review
- **Regularly adjust parameters**: Optimize search scope based on feedback

---

## 📚 更多信息 / More Information

- **详细技术文档**: 查看 [SKILL.md](SKILL.md) 了解完整技术细节
- **更新日志**: 参考项目Git提交历史
- **问题反馈**: 通过Hermes对话系统报告问题

- **Detailed Documentation**: See [SKILL.md](SKILL.md) for complete technical details
- **Changelog**: Refer to project Git commit history
- **Issue Reporting**: Report issues through Hermes conversation system

---

**🎉 开始使用 / Get Started**: 在Hermes对话中直接说："发送一份机器学习最新研究报告给我"

**Start using in Hermes conversation**: Just say: "发送一份机器学习最新研究报告给我"
