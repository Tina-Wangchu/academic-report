---
name: email-sender
description: "Send emails with attachments via Gmail SMTP. Use when the user asks to send emails, attach files, or deliver reports via email."
version: 1.0.0
author: agent-scholar
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [email, smtp, gmail, notification]
    category: my-category
required_environment_variables: [GMAIL_ADDRESS, GMAIL_APP_PASSWORD]
optional_environment_variables: [SMTP_SOCKS_PROXY]
---

# Email Sender — Gmail邮件发送

通过Gmail SMTP发送邮件，支持HTML格式、附件和SOCKS5代理。使用Gmail SMTP服务，需要应用专用密码。

## When to Use

当用户提出以下需求时激活：
- "发送邮件到..."
- "把...发送到邮箱"
- "邮件通知..."
- "Send email to..."
- "邮件附带文件..."

## Quick Reference

| 需求 | 操作 |
|---|---|
| 发送简单邮件 | `python send_email.py --to recipient@example.com --subject "Test" --body "Hello"` |
| HTML格式邮件 | `--body-type html --body "<h1>Hello</h1>"` |
| 带附件邮件 | `--attachment /path/to/file.pdf` |
| 使用外部正文文件 | `--body-file email_body.txt` |

## Environment Variables

### 必需环境变量
- `GMAIL_ADDRESS`: Gmail邮箱地址 (如: username@gmail.com)
- `GMAIL_APP_PASSWORD`: Gmail应用专用密码 (16位密码)

### 可选环境变量
- `SMTP_SOCKS_PROXY`: SOCKS5代理地址 (如: socks5://127.0.0.1:7897)

## Procedure

### Step 1: 验证环境配置

确认Gmail配置已设置：
```bash
# 检查环境变量
echo $GMAIL_ADDRESS
echo $GMAIL_APP_PASSWORD
echo $SMTP_SOCKS_PROXY  # 可选
```

### Step 2: 准备邮件内容

**HTML格式邮件** (推荐):
```html
<!DOCTYPE html>
<html>
<body>
    <h2>📚 学术报告</h2>
    <p>请查收附件中的研究报告。</p>
</body>
</html>
```

**纯文本邮件**:
```
请查收附件中的研究报告。

如有问题，请联系。
```

### Step 3: 执行邮件发送

**基本命令**:
```bash
python ${HERMES_SKILL_DIR}/scripts/send_email.py \
  --to recipient@example.com \
  --subject "学术报告" \
  --body "请查收附件"
```

**带附件的邮件**:
```bash
python ${HERMES_SKILL_DIR}/scripts/send_email.py \
  --to recipient@example.com \
  --subject "研究报告" \
  --body "请查收附件" \
  --attachment /path/to/report.pdf
```

**HTML格式邮件**:
```bash
python ${HERMES_SKILL_DIR}/scripts/send_email.py \
  --to recipient@example.com \
  --subject "学术报告" \
  --body-type html \
  --body "<h2>📚 学术报告</h2><p>请查收附件。</p>" \
  --attachment report.pdf
```

**使用外部正文文件**:
```bash
python ${HERMES_SKILL_DIR}/scripts/send_email.py \
  --to recipient@example.com \
  --subject "学术报告" \
  --body-file email_body.txt \
  --attachment report.pdf
```

**多个收件人**:
```bash
python ${HERMES_SKILL_DIR}/scripts/send_email.py \
  --to recipient1@example.com,recipient2@example.com \
  --subject "学术报告" \
  --body "请查收附件"
```

## Parameters

### 核心参数

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--to` | ✅ | 无 | 收件人邮箱（多个用逗号分隔） |
| `--subject` | ✅ | 无 | 邮件主题 |
| `--body` | ❌ | 无 | 邮件正文内容 |
| `--body-file` | ❌ | 无 | 邮件正文文件路径 |
| `--body-type` | ❌ | `plain` | 正文类型 (plain/html) |
| `--attachment` | ❌ | 无 | 附件文件路径 |

### 参数说明

- `--to`: 收件人邮箱，多个收件人用逗号分隔
  - 单个: `user@example.com`
  - 多个: `user1@example.com,user2@example.com`

- `--body` vs `--body-file`: 
  - `--body`: 直接提供邮件正文内容
  - `--body-file`: 从文件读取邮件正文
  - 如果同时提供，优先使用 `--body-file`

- `--body-type`: 邮件正文格式
  - `plain`: 纯文本 (默认)
  - `html`: HTML格式

- `--attachment`: 附件文件路径
  - 支持任意文件类型
  - 自动检测MIME类型
  - 可用于发送PDF报告等

## Gmail Setup

### 获取应用专用密码

1. **启用两步验证** (如未启用)
   - 访问: https://myaccount.google.com/security
   - 找到"两步验证"并启用

2. **生成应用专用密码**
   - 访问: https://myaccount.google.com/apppasswords
   - 选择"邮件"和"Windows计算机"
   - 点击"生成"
   - 复制16位密码 (格式: xxxx xxxx xxxx xxxx)

3. **设置环境变量**
   ```bash
   # Windows PowerShell
   $env:GMAIL_ADDRESS = "your-email@gmail.com"
   $env:GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"

   # Linux/Mac
   export GMAIL_ADDRESS="your-email@gmail.com"
   export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
   ```

### SOCKS5代理配置

如果网络环境需要代理：

```bash
# 设置SOCKS5代理环境变量
export SMTP_SOCKS_PROXY="socks5://127.0.0.1:7897"
```

## Pitfalls

### Gmail认证失败
**错误**: `Authentication failed`  
**原因**: 
- 使用了登录密码而非应用专用密码
- 应用专用密码错误
- Gmail地址格式错误

**修复**:
- 确保使用16位应用专用密码
- 验证Gmail地址格式正确
- 重新生成应用专用密码

### 连接超时
**错误**: `Connection timeout`  
**原因**: 网络连接问题或需要代理

**修复**:
- 检查网络连接
- 设置SMTP_SOCKS_PROXY环境变量
- 确认代理服务器运行正常

### 附件过大
**错误**: `Attachment too large`  
**原因**: Gmail附件限制 (25MB)

**修复**:
- 压缩附件
- 使用云存储链接
- 分多个邮件发送

### SSL/TLS错误
**错误**: `SSL certificate error`  
**原因**: 网络环境或代理问题

**修复**:
- 使用SOCKS5代理
- 检查防火墙设置
- 尝试不同端口 (587 vs 465)

## Verification

确认skill工作正常的测试步骤：

```bash
# 1. 基本邮件发送测试
python ${HERMES_SKILL_DIR}/scripts/send_email.py \
  --to $GMAIL_ADDRESS \
  --subject "Test Email" \
  --body "This is a test message"

# 2. HTML邮件测试
python ${HERMES_SKILL_DIR}/scripts/send_email.py \
  --to $GMAIL_ADDRESS \
  --subject "HTML Test" \
  --body-type html \
  --body "<h2>Test HTML Email</h2><p>This is a test.</p>"

# 3. 附件测试
echo "Test content" > test.txt
python ${HERMES_SKILL_DIR}/scripts/send_email.py \
  --to $GMAIL_ADDRESS \
  --subject "Attachment Test" \
  --body "Please check attachment" \
  --attachment test.txt
```

**预期结果**:
- 脚本正常退出 (返回码 0)
- 邮件成功发送到收件人
- 收件人收到包含正确内容和附件的邮件

## Integration

本skill可与其他skills集成：

**与paper-search集成**:
```bash
# 1. 搜索论文
python paper_search.py --topic "AI" --output papers.json

# 2. 发送结果
python send_email.py \
  --to user@example.com \
  --subject "AI Papers" \
  --body-file papers.json \
  --attachment papers.json
```

**与report-generator集成**:
```bash
# 1. 生成报告
python generate_report.py --input papers.json --output report.pdf

# 2. 发送报告
python send_email.py \
  --to user@example.com \
  --subject "Research Report" \
  --body "Please find attached report" \
  --attachment report.pdf
```

## Troubleshooting

### 查看详细错误信息

脚本会输出详细的错误信息，包括：
- 认证错误
- 连接错误
- 文件错误
- 网络错误

### 常见错误代码

- **535**: 认证失败 (检查密码)
- **550**: 邮箱地址不存在
- **552**: 附件过大
- **timeout**: 网络连接问题 (检查代理)

### 调试模式

在脚本中设置调试模式查看详细日志：
```python
import smtplib
smtplib.DEBUG_LEVEL = 4  # 启用详细调试输出
```
