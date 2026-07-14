# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical Workflow Rules

### Rule 1: Re-Understand Project Intent Before Changes

**EVERY TIME before creating or modifying files**, you MUST:

1. Read `agent-scholar skill实施计划.md` to re-understand the project's complete intent and requirements
2. Align your implementation with the detailed specifications in that plan (2357 lines of detailed implementation code)
3. Ensure your changes support the 6 core modules and 2 functional modes as specified in design-init.txt

**Why**: The implementation plan contains the authoritative specifications for all 6 modules. Reading it prevents drift from requirements and ensures consistency with the overall architecture.

### Rule 2: Synchronize Documentation After Changes

**After EVERY code modification or file creation**, you MUST:

1. Update `agent-scholar skill实施计划.md`:
   - Mark implemented modules as ✅ completed
   - Update progress sections
   - Add any new implementation details or code changes
   - Ensure the plan reflects current actual state

2. Update `README.md`:
   - Update module completion status in the功能特性 table
   - Update development progress in the🛠️开发状态 section
   - Add any new features or commands
   - Ensure documentation matches implementation reality

**Why**: This keeps documentation in sync with code, prevents outdated docs, and maintains a single source of truth for project status.

## Project Overview

Agent Scholar is a Hermes Agent Skill that performs automated academic paper search, analysis, and report generation with email delivery. It integrates with multiple academic data sources (arXiv, Semantic Scholar, OpenAlex) to retrieve papers, intelligently filter and rank them, extract key information, and generate formatted academic reports sent via email.

## Architecture

### Core Data Flow

```
User Natural Language Input
    ↓
Intent Parser (extracts: query, keywords, time range, filters, schedule)
    ↓
Paper Searcher (parallel multi-source search with rate limiting)
    ↓
Paper Filter (priority ranking, topic classification, deduplication)
    ↓
Paper Analyzer (extract metadata, analyze content, generate APA citations)
    ↓
Report Generator (Markdown/HTML report generation with trends analysis)
    ↓
Email Sender (SMTP delivery with attachments)
```

### Module Architecture

The system follows a pipeline architecture with 6 core modules + 2 mode/infra modules in `agent-scholar/scripts/`:

**Completed Modules** ✅:
- `utils.py` - Data models (`Paper`, `SearchIntent`) and utility functions (APA citation, date parsing, `schedule_interval`)
- `config_manager.py` - Unified configuration management (loads `~/.hermes/config.yaml` and `~/.hermes/.env`)
- `rate_limiter.py` - API rate limiting handler for multiple data sources (已接入 arXiv/Semantic Scholar/OpenAlex；CrossRef/PubMed 已配置限流但 Searcher 暂未接入)
- `intent_parser.py` - Natural language parser extracting search parameters + **schedule detection** (`is_scheduled`/`schedule`)
- `paper_search.py` - Multi-source paper searcher (arXiv, Semantic Scholar, OpenAlex; date filtering)
- `paper_filter.py` - Intelligent filtering, ranking, hotspot clustering
- `paper_analyzer.py` - Information extraction, four-element excerpts, APA 7th, overall analysis, foundational papers
- `report_generator.py` - Academic report generator (Markdown + HTML, bilingual, four-element excerpts, incremental label)
- `email_sender.py` - SMTP/SSL email sender (attachments, retry, connection test)
- `pipeline.py` - Full-chain orchestrator (search→report→email) + **incremental branch** (`--incremental`)
- `timestamp_manager.py` ✅ - Persists per-topic last-run timestamps (`~/.hermes/academic_scholar_timestamps.json`) for incremental mode
- `scheduler.py` ✅ - Standalone in-process scheduler (定时报告入口): parses周期 → loops `run_pipeline(incremental=True)`; `--once/--dry-run`; SIGINT; optional croniter
- `llm_analyzer.py` ✅ - Four-element **LLM generative** analysis (Zhipu GLM via Anthropic-compatible endpoint; LLM→rule fallback + cache); fills the 4 per-paper elements at reference depth

### Key Design Patterns

**Singleton Managers**:
- `get_config_manager()` returns global ConfigManager instance
- `get_rate_limiter()` returns global RateLimiter instance
- `get_timestamp_manager()` returns global TimestampManager instance

**Data Model**:
- `Paper` (dataclass) - Core paper metadata with analysis fields
- `SearchIntent` (dataclass) - Parsed user search parameters

**Configuration Layers**:
1. Environment variables (`~/.hermes/.env`) - Secrets (SMTP credentials, API keys)
2. Hermes config (`~/.hermes/config.yaml`) - Non-sensitive settings (language, time_range, max_results)
3. Module-level defaults - Fallback values

## Essential Configuration

### Required Setup

Before any development or testing:

```bash
# Install Hermes Agent
pip install hermes-agent

# Install dependencies
cd agent-scholar-2.0/agent-scholar
pip install -r requirements.txt

# Configure environment variables (REQUIRED for email functionality)
cat > ~/.hermes/.env << EOF
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-app-password
EOF

# Configure Hermes settings
hermes config set skills.config.academic.default_language bilingual
hermes config set skills.config.academic.max_results 50
hermes config set skills.config.academic.email_recipient your@email.com
```

### Gmail App Password

For Gmail SMTP, generate an app password: https://myaccount.google.com/apppasswords

## Development Commands

### Testing Individual Modules

```bash
# Test configuration loading
python3 agent-scholar/scripts/config_manager.py

# Test intent parsing
python3 agent-scholar/scripts/intent_parser.py --input "搜索最近的深度学习论文"

# Test email configuration (requires SMTP setup)
python3 agent-scholar/scripts/email_sender.py --test
```

### Test File Requirements

**ALL test scripts MUST follow these conventions:**

1. **Naming Convention**: All test files must be prefixed with `test_`
   - ✅ Correct: `test_paper_search.py`, `test_intent_parser.py`, `test_report_generator.py`
   - ❌ Incorrect: `paper_search_test.py`, `test_search.py`, `tests.py`

2. **File Location**: All test files must be saved in the `test/` directory
   - ✅ Correct: `test/test_paper_search.py`, `test/test_filter.py`
   - ❌ Incorrect: `scripts/test_paper_search.py`, `tests/test_filter.py`

3. **Test Structure**: 
   - Unit tests for a module should be named `test_<module_name>.py`
   - Example: Tests for `paper_search.py` → `test/test_paper_search.py`

**Test Directory Structure**:
```
test/
├── __init__.py
├── test_intent_parser.py      # Tests for scripts/intent_parser.py
├── test_paper_search.py        # Tests for scripts/paper_search.py
├── test_paper_filter.py        # Tests for scripts/paper_filter.py
├── test_paper_analyzer.py      # Tests for scripts/paper_analyzer.py
├── test_report_generator.py    # Tests for scripts/report_generator.py
├── test_email_sender.py        # Tests for scripts/email_sender.py
└── test_integration.py         # Integration tests
```

**Running Tests**:
```bash
# Run all tests
pytest test/

# Run specific test file
pytest test/test_paper_search.py

# Run specific test function
pytest test/test_paper_search.py::test_arxiv_search

# Run with verbose output
pytest test/ -v

# Run with coverage
pytest test/ --cov=agent_scholar --cov-report=html
```

### Hermes Agent Integration

```bash
# Install skill to Hermes
cp -r agent-scholar-2.0/agent-scholar ~/.hermes/skills/academic-scholar

# Test skill loading
hermes chat -q "/academic-scholar 帮助"

# List all skills
/skills
```

### Running in Hermes

```bash
# Single search mode
hermes chat -q "/academic-scholar 搜索最近的机器学习论文，生成报告并发送到我的邮箱"

# Scheduled report (accept blueprint suggestion)
hermes chat
/suggestions accept 1
```

## Module Implementation Priorities

**Phase 1 (High Priority)** - Core search and filtering:
1. `paper_search.py` - Implement ArxivSearcher, SemanticScholarSearcher, PaperSearcher with parallel execution
2. `paper_filter.py` - Implement priority scoring algorithm, topic classification, deduplication

**Phase 2 (Medium Priority)** - Analysis and reporting:
3. `paper_analyzer.py` - Information extraction, APA 7th formatting, related paper lookup
4. `report_generator.py` - Markdown generation, HTML conversion, trend analysis, template rendering

**Phase 3 (Low Priority)** - Delivery and testing:
5. `email_sender.py` - SMTP integration with retry logic
6. `templates/` - Create report_template.md and report_html_template.html

## Data Source Integration

### API Rate Limits (Handled by RateLimiter)

| Source | Limit | Implementation |
|--------|-------|----------------|
| arXiv | None | Direct `arxiv` library |
| Semantic Scholar | 5000/day | REST API with optional API key |
| OpenAlex | None | REST API |
| CrossRef | 10/sec | **Reserved**（rate_limiter 已配置，Searcher 暂未接入） |
| PubMed | 3/sec | **Reserved**（同上） |

### Search Strategy

When implementing `paper_search.py`:
- Use `ThreadPoolExecutor` for parallel searches (max_workers=3)
- Call `rate_limiter.wait_if_needed(source)` before each API call
- Merge results with `_deduplicate()` (prioritize papers with DOI)
- Handle exceptions gracefully, log errors, continue with other sources

## Report Structure

Generated reports follow the spec in `报告格式设计.md` (bilingual CN/EN, **authoritative**). The `report_generator.py` Module 5 and `templates/report_template.md` / `report_html_template.html` must conform. Structure:

1. **Title + Time** — `{time_range} {field/topic} Report` (e.g., `2023-2025 Statistics Research Report`); a small-font line shows both the **report generation time** and the **report coverage time** (paper publication range from `intent.start_date`–`end_date`)
2. **I. Report Overview (报告速览)** — summarize **by hotspot** (not per-paper): list which hotspots the report covers + each hotspot's specific finding (representative paper's result/conclusion); do not list every paper title
3. **II. Classified Paper Display (分类论文展示)** — papers grouped by "hotspot" (similar/related directions). Each hotspot:
   - Hotspot name (e.g., `热点一：XXXX`) + hotspot topic intro
   - Per paper: title; authors, publication time, venue, citation count, DOI; **Abstract (~150-200 words, condensing the paper's central achievements)**; APA 7th citation
   - Overall analysis (synthesize the hotspot's papers into a direction-level analysis)
   - Foundational reference papers (1-3 most foundational/groundbreaking past works in this direction)
4. **III. Research Trends (研究趋势)** — ~200 words; future research trends + research gaps, grounded in the included papers (avoid generic platitudes)

## Common Issues

### SMTP Authentication Failure
- Gmail requires app password, not account password
- Check `SMTP_PORT`: 587 for TLS, 465 for SSL
- Verify `SMTP_USER` matches email address

### API Rate Limiting
- Semantic Scholar: Monitor remaining requests with `rate_limiter.get_remaining_requests('semantic_scholar')`
- Automatic waiting implemented in `rate_limiter.wait_if_needed()`
- For development, consider caching results to avoid repeated API calls

### Module Dependencies
All scripts import from `utils.py`, ensure it's implemented first:
- `from utils import Paper, SearchIntent, parse_date_range, format_apa_citation`
- `from config_manager import get_config_manager`
- `from rate_limiter import get_rate_limiter`

## File Context

- **SKILL.md** - Hermes Agent skill definition with frontmatter (metadata, environment variables, blueprint schedule)
- **design-init.txt** - Original Chinese requirements document (6 core modules, 2 modes)
- **agent-scholar skill实施计划.md** - Detailed implementation plan (2000+ lines with complete code for all 6 modules)
- **报告格式设计.md** - Authoritative bilingual (CN/EN) report format spec; Module 5 and report templates must conform
- **requirements.txt** - Python dependencies (arxiv, scholarly, pandas, markdown, jinja2, secure-smtplib, python-dateutil, pyyaml)

## Implementation Notes

### When implementing `paper_search.py`:

Follow the pattern from the implementation plan in `agent-scholar skill实施计划.md` (lines 518+):

```python
class PaperSearcher:
    def __init__(self):
        self.config = get_config_manager()
        api_keys = self.config.get_api_keys()
        self.searchers = {
            'arxiv': ArxivSearcher(),
            'semantic_scholar': SemanticScholarSearcher(api_keys['semantic_scholar']),
            # Add other sources...
        }
    
    def search(self, intent: SearchIntent) -> List[Paper]:
        # Parallel search with ThreadPoolExecutor
        # Deduplicate results
        # Return merged list
```

### When implementing `paper_filter.py`:

Priority scoring algorithm (from plan, lines 953+):
- Highly cited (≥100 citations): +100 points
- Top journals (Nature/Science/Cell): +90 points
- Top conferences (NeurIPS/ICML/ICCV): +80 points
- SCI/EI indexed: +70 points
- General journals: +50 points
- Preprints: +30 points
- Citation count bonus: +min(citation_count, 50)
