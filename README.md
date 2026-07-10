# Agent-Scholar - Hermes Academic Paper Search Skill

Hermes Agent 的学术论文智能检索和分析技能。支持多数据源并行检索、AI深度分析、HTML报告自动生成和邮件推送。

## Architecture

```
User Request → Multi-Source Search → AI Deep Analysis → HTML Report → Email
                  |                      |                 |
            Semantic Scholar      Per-paper structured  Professional HTML
            arXiv                  analysis             CSS styling
            CrossRef               Domain overview      Print-friendly
            OpenAlex               Smart filtering
            PubMed
```

### Three-Stage Workflow

1. **Multi-Source Search**: Parallel retrieval from 5 academic APIs with automatic rate-limit handling, deduplication by title/DOI, and multi-dimensional quality scoring
2. **AI Deep Analysis**: Agent analyzes each paper (research objective, method, innovation, findings, significance) + writes domain overview (hotspots, evolution, gaps, future directions)
3. **HTML Report + Email**: Professional HTML report with CSS styling, then email delivery

## Installation for Hermes Users

### Prerequisites

- [Hermes Agent](https://github.com/hermes-agent/hermes) installed
- Python 3.8+ with `requests`, `PySocks` packages

### Install from Git

```bash
# 1. Clone the repo
git clone https://github.com/Tina-Wangchu/agent-scholar.git

# 2. Copy skills to Hermes skills directory
#    Adjust the path if your Hermes skills directory is different
cp -r agent-scholar/skills/academic/* ~/.hermes/skills/academic/

# On Windows (PowerShell):
Copy-Item -Recurse agent-scholar\skills\academic\* "$env:LOCALAPPDATA\hermes\skills\academic\"

# 3. Clear Python cache
find ~/.hermes/skills/academic/ -type d -name "__pycache__" -exec rm -rf {} +
# On Windows:
Get-ChildItem "$env:LOCALAPPDATA\hermes\skills\academic" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# 4. Restart Hermes
```

### Configure Environment Variables

Set email credentials for the report delivery feature:

```bash
# Gmail (recommended)
export GMAIL_ADDRESS="your@gmail.com"
export GMAIL_APP_PASSWORD="your-16-char-app-password"

# Or QQ Mail
export QQ_EMAIL_ADDRESS="your@qq.com"
export QQ_EMAIL_AUTH_CODE="your-auth-code"

# Optional: SOCKS5 proxy for Gmail in China
export SMTP_SOCKS_PROXY="socks5://127.0.0.1:7897"
```

### Verify Installation

In Hermes Agent, say:

```
请为我搜索统计学领域这一周的最新研究成果，把报告发送到我的邮箱
```

Expected behavior:
- Multi-source search across Semantic Scholar, arXiv, CrossRef, OpenAlex
- AI-generated analysis (not raw abstract copying)
- Professional HTML report as email attachment

## Skill Modules

```
skills/academic/
├── DESCRIPTION.md                    # Category description
├── paper-email-service/              # Orchestrator (main entry point)
│   ├── SKILL.md                      # System prompt with AI analysis requirements
│   ├── config/default_config.yaml    # Default configuration
│   └── scripts/
│       ├── workflow_executor.py       # 4-step pipeline executor
│       ├── intelligent_search_executor.py  # Multi-source search + quality scoring
│       ├── intelligent_query_parser.py      # NL → structured parameters
│       ├── config_manager.py
│       └── utils/
│           ├── formatters.py         # Data formatting with source fallback
│           ├── validators.py
│           └── error_handler.py
├── paper-search/                      # Search engine
│   ├── SKILL.md                      # 5 data sources: Semantic Scholar, arXiv, CrossRef, OpenAlex, PubMed
│   └── scripts/paper_search.py       # Multi-source search with retry & rate-limit handling
├── paper-summarizer/                  # AI analysis
│   ├── SKILL.md                      # Agent-driven analysis (not rule-based script)
│   └── scripts/paper_summarizer.py
├── report-generator/                  # HTML report
│   ├── SKILL.md                      # 6-section report structure
│   └── scripts/
│       ├── generate_report.py         # Main report generator
│       ├── generate_report_html.py   # HTML variant with CSS styling
│       └── enhanced_analysis.py
└── email-sender/                      # Email delivery
    ├── SKILL.md
    └── scripts/send_email.py          # SMTP with SOCKS5 proxy support
```

## Key Features

- **Multi-source search**: 5 academic APIs with automatic failover on rate limits
- **AI deep analysis**: Structured per-paper analysis + domain overview (not abstract copying)
- **Smart filtering**: Quality scoring (timeliness, impact, novelty, relevance, diversity)
- **HTML reports**: Professional CSS styling, print-friendly, no encoding issues
- **Rate-limit resilient**: Automatic source switching on 429 errors
- **True 7-day range**: Precise timedelta-based date calculation
- **Scheduled tasks**: Weekly/monthly automated reports via Hermes cron

## Testing

```bash
# Test API rate limits for all data sources
python tests/test_api_rate_limits.py

# Test multi-source search executor
python tests/test_intelligent_search.py

# Test HTML report generation
python tests/test_html_report.py

# Comprehensive fix verification
python tests/test_hermes_fixes.py
```

## Repository Structure

```
agent-scholar/
├── skills/academic/              # ← Install this directory to Hermes
├── paper-email-service-skill/    # Development copy of orchestrator
├── paper-skill/                  # Development copies of sub-skills
├── tests/                        # Test scripts
├── docs/                         # Documentation
├── features/                     # Feature references
└── README.md
```

---

Last updated: 2026-07-10
License: MIT
