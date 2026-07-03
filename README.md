# 🎓 Agent Scholar - Hermes Agent Skills Repository

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Hermes Agent](https://img.shields.io/badge/Hermes-Agent-compatible-green.svg)](https://hermes.ai)

> Academic research automation skills for Hermes Agent - Paper search, report generation, and email delivery workflow.

---

## 📚 **Overview**

**Agent Scholar** is a collection of Hermes Agent skills designed to automate academic research workflows. It integrates paper search, PDF report generation, and email delivery into a seamless, automated pipeline.

### ⭐ **Key Features**

- 🔍 **Multi-Source Paper Search** - Retrieve academic papers from Semantic Scholar, arXiv, and CrossRef
- 📄 **Professional PDF Reports** - Generate formatted academic reports with cover pages, analysis, and references
- 📧 **Automated Email Delivery** - Send reports via email with support for multiple providers (Gmail, QQ Mail, etc.)
- 🤖 **User-Centric Interaction** - Built-in user constraint protection principles
- ⏰ **Scheduled Tasks** - Support for periodic research updates (weekly/monthly reports)

---

## 🎯 **Main Feature: Paper Email Service**

The **paper-email-service** skill provides a complete automated research workflow:

### **Workflow**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Paper Search   │ → │ Report Generator │ → │  Email Sender   │
│  (Multi-source) │    │  (PDF Export)    │    │  (SMTP/IMAP)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **What It Does**

1. **Search Papers** - Retrieves academic papers based on topic, keywords, time range, and domain
2. **Generate Report** - Creates a professional PDF report with:
   - Cover page with metadata
   - Search summary and statistics
   - Complete paper list with abstracts
   - Research trend analysis
   - Formatted references
3. **Send Email** - Delivers the report as PDF attachment to your inbox

### **Example Usage**

```
You: "生成一份人工智能领域的最新研究报告发送到我的邮箱"

Hermes Agent:
✅ Searching academic papers...
✅ Found 12 papers (Semantic Scholar, arXiv)
✅ Generating PDF report...
✅ Sending email to tinawangchu0615@gmail.com...
✅ Report delivered successfully!
```

---

## 📁 **Repository Structure**

```
agent-scholar/
├── 📧 paper-email-service-skill/     # Main skill: automated research workflow
│   ├── SKILL.md                      # Skill documentation
│   ├── README.md                     # Skill readme
│   ├── scripts/                      # Python implementation
│   │   ├── paper_email_service.py    # Main workflow executor
│   │   ├── workflow_executor.py      # Orchestration logic
│   │   ├── config_manager.py         # Configuration management
│   │   ├── task_scheduler.py        # Scheduled task support
│   │   └── utils/                    # Utilities
│   ├── config/                       # Configuration templates
│   ├── templates/                    # Email templates
│   └── integration/                  # Integration tests
│
├── 🔍 paper-skill/                   # Paper search & report generation
│   ├── paper-search/                 # Academic paper search
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── paper_search.py       # Multi-source paper search engine
│   │
│   └── report-generator/             # PDF report generation
│       ├── SKILL.md
│       └── scripts/
│           └── generate_report.py    # Academic PDF report generator
│
├── 📮 email-skill/                   # Email sending capability
│   ├── SKILL.md
│   └── email-sender-skill-intro.md
│
├── 🧠 memory/                        # Agent interaction principles
│   └── agent-interaction-principle-user-constraint-protection.md
│
├── 📖 MEMORY.md                      # Memory index
│
├── 🔧 USER_CONSTRAINT_PROTECTION_FIX.md  # Design fix documentation
│
├── 📄 .gitignore                     # Git ignore rules
└── 📜 LICENSE                        # MIT License
```

---

## 🚀 **Quick Start**

### **Prerequisites**

- [Hermes Agent](https://hermes.ai) installed
- Python 3.8+
- Gmail account (or other supported email provider)

### **Installation**

1. **Clone this repository**
   ```bash
   git clone https://github.com/Tina-Wangchu/agent-scholar.git
   cd agent-scholar
   ```

2. **Copy skills to Hermes directory**
   ```bash
   # Copy to Hermes skills directory
   cp -r paper-email-service-skill ~/.hermes/skills/my-category/
   cp -r paper-skill/paper-search ~/.hermes/skills/my-category/
   cp -r paper-skill/report-generator ~/.hermes/skills/my-category/
   ```

3. **Configure environment variables**
   
   Edit `~/.hermes/.env` or Hermes configuration file:
   ```bash
   # Gmail configuration
   GMAIL_ADDRESS=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_char_app_password
   SMTP_SOCKS_PROXY=socks5://127.0.0.1:7897  # Optional: for Gmail access in China
   ```

   **Get Gmail App Password**: https://myaccount.google.com/apppasswords

4. **Restart Hermes Agent**
   ```bash
   hermes restart
   ```

### **Usage**

In Hermes Agent chat interface:

```
You: "生成一份人工智能领域的最新研究报告发送到我的邮箱"

Hermes Agent will:
1. Collect requirements (topic, time range, paper count)
2. Search academic papers from multiple sources
3. Generate professional PDF report
4. Send report to your email
```

---

## 🛠️ **Technical Stack**

### **Languages & Frameworks**
- **Python 3.8+** - Core implementation
- **Hermes Agent SDK** - Skill development framework

### **Key Dependencies**
- **smtplib** - Email sending (Python standard library)
- **PySocks** - SOCKS5 proxy support
- **reportlab** - PDF generation
- **urllib** - HTTP requests (no external dependencies for APIs)

### **Data Sources**
- **Semantic Scholar API** - Free, academic paper metadata
- **arXiv API** - Preprint papers (CS, physics, math)
- **CrossRef API** - Global academic literature metadata

### **Email Providers**
- Gmail (SMTP)
- QQ Mail
- 163/126 Mail
- WeChat Work Mail
- Outlook

---

## 📋 **Skills Detail**

### **1. paper-email-service** ⭐
- **Description**: Complete automated research workflow
- **Features**: Paper search + PDF report + Email delivery
- **Use case**: Regular research updates, literature review automation
- **Location**: `paper-email-service-skill/`

### **2. paper-search**
- **Description**: Multi-source academic paper search
- **Features**: 
  - Domain optimization (AI, statistics, finance)
  - Time range filtering
  - Citation-based sorting
- **Use case**: Finding relevant academic papers
- **Location**: `paper-skill/paper-search/`

### **3. report-generator**
- **Description**: Professional academic PDF report generation
- **Features**:
  - Cover page with metadata
  - Paper list with abstracts
  - Trend analysis
  - Formatted references (GB/T 7714)
- **Use case**: Creating literature review reports
- **Location**: `paper-skill/report-generator/`

---

## 🎨 **Design Principles**

### **User Constraint Protection** 🛡️

This repository implements the **User Constraint Protection** principle:

> **Agent must never modify user parameters without explicit permission.**

**Example**:
```
❌ Wrong:  "No papers found in 1 year. I'll auto-expand to 5 years."
✅ Correct: "No papers found in 1 year. Should I expand to 3 or 5 years?"
```

See: [memory/agent-interaction-principle-user-constraint-protection.md](memory/agent-interaction-principle-user-constraint-protection.md)

---

## 📊 **Usage Examples**

### **Example 1: Weekly AI Research Report**

```
You: "每周一早上8点自动发送AI领域的论文报告"

Hermes: ✅ Created scheduled task "AI Weekly Report"
       - Schedule: Every Monday 8:00 AM
       - Topic: Artificial Intelligence and Machine Learning
       - Time range: Last 7 days
       - Max papers: 15
```

### **Example 2: One-time Literature Review**

```
You: "搜索transformer在NLP中的应用，生成报告发邮件"

Hermes: ✅ Found 18 papers on "Transformer in NLP"
       ✅ Generated PDF report (12 pages)
       ✅ Sent to tinawangchu0615@gmail.com
```

### **Example 3: Statistics Domain Search**

```
You: "检索统计决策理论的最新研究"

Hermes: ✅ Using domain-optimized search (statistics)
       ✅ Prioritizing CrossRef (best for statistics journals)
       ✅ Found 8 papers from top statistics venues
```

---

## ⚙️ **Configuration**

### **Environment Variables**

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GMAIL_ADDRESS` | ✅ Yes | Your Gmail address | `user@gmail.com` |
| `GMAIL_APP_PASSWORD` | ✅ Yes | 16-char app password | `abcdefghijklmnop` |
| `SMTP_SOCKS_PROXY` | ⚠️ Conditional | SOCKS5 proxy (China) | `socks5://127.0.0.1:7897` |

### **Skill Parameters**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `time_range` | `1y` | Time range (1y/3y/5y/10y/unlimited) |
| `max_results` | `10` | Maximum papers to retrieve |
| `domain` | `general` | Domain optimization (ai/statistics/finance) |
| `sort_by` | `relevance` | Sorting (relevance/citation_count/publish_date) |

---

## 🧪 **Testing**

### **Test Paper Search**
```bash
python paper-skill/paper-search/scripts/paper_search.py \
  --topic "machine learning" \
  --time-range 1y \
  --max-results 5
```

### **Test Report Generation**
```bash
python paper-skill/report-generator/scripts/generate_report.py \
  --input papers.json \
  --output report.pdf
```

### **Test Email Sending**
```bash
python email-skill/scripts/send_email.py \
  --to $GMAIL_ADDRESS \
  --subject "Test" \
  --body "Test email"
```

---

## 🤝 **Contributing**

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 **Documentation**

- [Paper Email Service Documentation](paper-email-service-skill/README.md)
- [User Constraint Protection Principle](memory/agent-interaction-principle-user-constraint-protection.md)
- [Hermes Agent Skills Guide](https://hermes.ai/docs)

---

## 🐛 **Troubleshooting**

### **Common Issues**

**Problem**: Email sending fails with timeout error
```
Solution: Set SMTP_SOCKS_PROXY environment variable
export SMTP_SOCKS_PROXY="socks5://127.0.0.1:7897"
```

**Problem**: Authentication failed (535)
```
Solution: Use Gmail App Password, not login password
Get it at: https://myaccount.google.com/apppasswords
```

**Problem**: Paper search returns 0 results
```
Solution: The Agent will ask if you want to expand time range
(User Constraint Protection principle)
```

---

## 📜 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 **Author**

**Tina Wangchu** - Agent Scholar Project

- GitHub: [Tina-Wangchu](https://github.com/Tina-Wangchu)
- Hermes Agent: @tinawangchu0615

---

## 🙏 **Acknowledgments**

- [Hermes Agent](https://hermes.ai) - Agent platform
- [Semantic Scholar](https://www.semanticscholar.org/) - Academic paper API
- [arXiv](https://arxiv.org/) - Preprint server
- [CrossRef](https://www.crossref.org/) - Academic metadata

---

## 📫 **Contact**

For questions, suggestions, or issues:
- Open an issue on GitHub
- Email: tinawangchu0615@gmail.com

---

**Made with ❤️ for the academic research community**

⭐ If you find this project useful, please consider giving it a star!
