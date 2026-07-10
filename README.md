# Agent-Scholar - Hermes Academic Paper Search Skill

Hermes Agent 的学术论文智能检索和分析技能。支持多数据源并行检索、AI深度分析、HTML报告自动生成和邮件推送。

## Architecture

```
用户请求 → 多源并行检索 → AI深度分析 → HTML报告生成 → 邮件推送
                |                |              |
          Semantic Scholar   单篇结构化分析    美观HTML排版
          arXiv              领域综合综述      CSS渐变样式
          CrossRef           智能筛选去重       打印友好
          OpenAlex
          PubMed
```

### Three-Stage Workflow

1. **Multi-Source Search**: Parallel retrieval from 5 academic APIs with automatic rate-limit handling, deduplication by title/DOI similarity, and quality scoring
2. **AI Deep Analysis**: Agent analyzes each paper's research objective, core method, key innovation, main findings, and significance (not raw abstract copying)
3. **HTML Report + Email**: Professional HTML report with CSS styling, then email delivery

## Skill Modules

### paper-email-service (Orchestrator)
End-to-end workflow orchestration: search → analyze → report → email.
- `SKILL.md` - System prompt with mandatory AI analysis requirements
- `scripts/workflow_executor.py` - 4-step pipeline executor
- `scripts/intelligent_search_executor.py` - Multi-source search with quality scoring
- `scripts/intelligent_query_parser.py` - Natural language to structured parameters
- `config/default_config.yaml` - Default configuration

### paper-search (Data Acquisition)
Multi-source academic paper search engine.
- `SKILL.md` - Search skill definition with 5 data sources
- `scripts/paper_search.py` - Search engine (Semantic Scholar, arXiv, CrossRef, OpenAlex, PubMed)

### paper-summarizer (AI Analysis)
AI-powered paper analysis and summarization.
- `SKILL.md` - Agent-driven analysis instructions (not rule-based script)

### report-generator (Document Generation)
Professional HTML report generation.
- `SKILL.md` - Report structure with 6 standard sections
- `scripts/generate_report.py` - Report generator

### email-sender (Delivery)
Email sending via SMTP (Gmail, QQ, 163, Outlook supported).
- `SKILL.md` - Email skill definition
- `scripts/send_email.py` - SMTP email sender with SOCKS5 proxy support

## Directory Structure

```
agent-scholar/
├── paper-email-service-skill/    # Orchestrator skill
│   ├── SKILL.md                  # System prompt (AI analysis + multi-source)
│   ├── config/default_config.yaml
│   └── scripts/
│       ├── workflow_executor.py
│       ├── intelligent_search_executor.py
│       ├── intelligent_query_parser.py
│       ├── config_manager.py
│       └── utils/
│           ├── formatters.py
│           ├── validators.py
│           └── error_handler.py
├── paper-skill/                   # Sub-skills (mirror of Hermes runtime)
│   ├── paper-search/             # Search engine
│   │   ├── SKILL.md
│   │   └── scripts/paper_search.py
│   ├── paper-summarizer/         # AI analysis
│   │   ├── SKILL.md
│   │   └── scripts/paper_summarizer.py
│   ├── report-generator/         # HTML report
│   │   ├── SKILL.md
│   │   └── scripts/generate_report.py
│   └── email-sender/             # Email delivery
│       ├── SKILL.md
│       └── scripts/send_email.py
├── tests/                        # Test scripts
│   ├── test_api_rate_limits.py   # API rate limiting check
│   ├── test_intelligent_search.py # Multi-source search test
│   ├── test_hermes_fixes.py      # Comprehensive fix verification
│   ├── test_html_report.py       # HTML report generation test
│   └── ...
├── tools/                        # Utility tools
└── docs/                         # Documentation
```

## Key Features

- **Multi-source search**: 5 academic APIs (Semantic Scholar, arXiv, CrossRef, OpenAlex, PubMed)
- **AI deep analysis**: Structured analysis per paper + domain overview (not abstract copying)
- **Smart filtering**: Multi-dimensional quality scoring, diversity selection per research direction
- **HTML reports**: Professional CSS styling, print-friendly, no PDF encoding issues
- **Rate-limit resilient**: Automatic source switching on 429 errors
- **True 7-day range**: Precise date calculation with timedelta
- **Scheduled tasks**: Weekly/monthly automated reports via Hermes cron

## Deployment

Skills are deployed to Hermes runtime directory:
```
C:/Users/lanpi/AppData/Local/hermes/skills/academic/
```

To deploy changes:
1. Copy modified files to the corresponding Hermes runtime path
2. Clear Python cache: `rm -rf **/__pycache__`
3. Restart Hermes

## Testing

```bash
# Test API rate limits
python tests/test_api_rate_limits.py

# Test multi-source search
python tests/test_intelligent_search.py

# Test HTML report generation
python tests/test_html_report.py

# Verify all fixes
python tests/test_hermes_fixes.py
```

## Usage in Hermes

```
"请为我搜索统计学领域这一周的最新研究成果，把报告发送到我的邮箱"
```

---

Last updated: 2026-07-10
