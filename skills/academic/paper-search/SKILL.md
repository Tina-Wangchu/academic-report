---
name: paper-search
description: "Search academic papers with filtering. Use when the user asks to find papers, search literature, retrieve academic articles, or look up research publications — supports keyword search, time range filtering, multiple data sources, and citation sorting."
version: 1.0.0
author: agent-scholar
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [academic, research, papers, literature, search]
    category: my-category
required_environment_variables: []
---

# Paper Search — 学术论文检索

通过多数据源检索学术论文，支持关键词搜索、时间范围过滤、引用量排序等功能。使用免费的学术 API（Semantic Scholar、arXiv、CrossRef），无需身份认证。

## When to Use

当用户提出以下需求时激活：
- "帮我找一些关于...的论文"
- "检索...领域的学术文献"
- "Search papers on..."
- "查找近年的...研究"
- "我要写综述，需要相关参考文献"
- "Find high-citation papers about..."

## Quick Reference

| 需求 | 操作 |
|---|---|
| 基本检索 | `python paper_search.py --topic "machine learning"` |
| **领域优化检索** | `--domain ai` (人工智能) / `statistics` (统计决策) / `finance` (金融统计) |
| 关键词检索 | `--keywords "LLM,education,personalized learning"` |
| 时间范围过滤 | `--time-range 3y` (近3年) / `5y` / `10y` / `unlimited` |
| 最大结果数 | `--max-results 15` (默认8篇) |
| 按引用排序 | `--sort-by citation_count` |
| 输出 Markdown | `--output-format markdown --output results.md` |
| 输出 CSV | `--output-format csv --output papers.csv` |

## Procedure

### Step 1: 收集检索需求

向用户确认以下信息（未提及的可根据上下文推断或使用默认值）：

- **检索主题**（必需）：用户研究的核心主题
- **应用领域**（可选）：根据主要应用领域优化数据源选择
  - `statistics` - 统计决策领域（优先 CrossRef 覆盖统计期刊）
  - `ai` - 人工智能领域（优先 arXiv 最新预印本）
  - `finance` - 金融统计领域（优先 CrossRef 覆盖金融期刊）
  - `general` - 通用领域（默认）
- **关键词**（可选）：具体的检索关键词，多个关键词用逗号分隔
- **时间范围**（可选）：默认为近3年 (`3y`)，支持 `1y`/`5y`/`10y`/`unlimited`/`2020-2023`
- **文献数量**（可选）：默认返回8篇，可指定 `--max-results`
- **排序方式**（可选）：`relevance`（相关度，默认）、`citation_count`（引用量）、`publish_date`（发表时间）
- **输出格式**（可选）：`json`（默认）、`markdown`、`csv`

### Step 2: 执行检索

根据收集的参数调用检索脚本：

```bash
python ${HERMES_SKILL_DIR}/scripts/paper_search.py \
  --topic "大语言模型在教育领域的应用" \
  --keywords "LLM,education,personalized learning" \
  --time-range 3y \
  --max-results 10 \
  --sort-by citation_count \
  --output-format markdown \
  --output $env:TEMP/paper_results.md
```

**参数说明**：
- `--topic`: 自然语言描述的研究主题
- `--keywords`: 精准关键词（逗号分隔），用于提升检索精度
- `--time-range`: 时间范围，支持：
  - `1y` / `3y` / `5y` / `10y`：近X年
  - `unlimited`：不限年份
  - `2020-2023`：自定义年份范围
  - `2020-01-01:2023-06-30`：精确日期范围
- `--max-results`: 返回论文数量（建议 5-20 篇）
- `--sort-by`: 排序依据
- `--output-format`: 输出格式（json/markdown/csv）

### Step 3: 展示结果

检索完成后，根据输出格式展示结果：

**JSON 格式**（默认）：
```json
{
  "status": "success",
  "query": "machine learning in education",
  "total_found": 8,
  "sources_used": ["Semantic Scholar", "arXiv"],
  "papers": [
    {
      "title": "Large Language Models in Education...",
      "authors": ["Author1", "Author2"],
      "year": 2023,
      "abstract": "This paper explores...",
      "citationCount": 156,
      "doi": "10.xxxx/xxxxx",
      "journal": "Computers & Education",
      "url": "https://www.semanticscholar.org/paper/..."
    }
  ],
  "filters_applied": {
    "time_range": {"start_date": "2021-06-18", "end_date": "2024-06-18", "years": 3},
    "language": "bilingual",
    "max_results": 8
  },
  "timestamp": "2024-06-18T10:30:45.123Z"
}
```

**Markdown 格式**：适合直接阅读或导入文献综述
**CSV 格式**：适合导入 Excel 或进行数据分析

### Step 4: 解读与建议

根据检索结果为用户提供：

1. **检索概况**：
   - 检索主题和数据源
   - 找到的文献数量
   - 应用的筛选条件

2. **核心论文列表**：
   - 论文标题、作者、发表年份、期刊/会议
   - 摘要要点（前500字）
   - 引用量（如可获取）
   - DOI 链接

3. **研究趋势分析**：
   - 领域研究热点（基于高频关键词）
   - 年度发文量趋势（基于论文年份分布）
   - 高被引论文推荐

4. **🔴 CRITICAL: 当结果为0时的处理（用户约束保护原则）**

   当检索结果为0篇论文时，**绝对禁止**擅自修改用户参数（如自动扩大时间范围）。必须遵循以下流程：

   ```markdown
   ⚠️ 使用指定参数未找到相关论文

   🔍 实际使用的检索参数：
   - 主题：{用户指定的主题}
   - 时间范围：{用户指定的时间范围，如近1年}
   - 关键词：{用户指定的关键词}
   - 数据源：{实际使用的数据源}
   - 最大结果数：{用户指定的数量}

   💡 可能的原因：
   - 时间范围过窄（该时间范围内相关论文较少）
   - 关键词过于具体（匹配不到相关文献）
   - 该领域近期发表论文较少
   - 数据源覆盖范围有限

   🎯 建议的调整方案：
   1. 扩大时间范围：3年 / 5年 / 10年 / 不限年份
   2. 调整关键词：使用更通用的术语
   3. 指定领域优化：statistics / ai / finance / general
   4. 更换数据源或增加数量上限

   ❓ 请选择您需要的调整：
   - "扩大到3年" / "扩大到5年" / "不改，我要最新的"
   - 或说明其他调整需求
   ```

   **✅ 正确示例**：
   ```
   User: "检索近一年的AI论文"
   Agent: "⚠️ 近1年内未找到相关论文。
          🔍 检索参数：时间范围=2025-07-01至2026-07-01, 关键词=AI
          💡 建议：扩大到3年或5年可能会有更多结果。
          ❓ 是否扩大时间范围？"
   User: "扩大到5年"
   Agent: [按用户指示执行5年检索]
   ```

   **❌ 错误示例（绝对禁止）**：
   ```
   Agent: "时间范围筛选为近一年...但当前返回的论文年份集中在2021-2024，
          未满足筛选条件。我将改用近3年重新检索以获取足够的近期论文。"
   → 问题：擅自修改用户参数，未征求用户同意
   ```

   **核心原则**：
   - 🚨 **NEVER** auto-modify user parameters without permission
   - ✅ **ALWAYS** inform user when zero results found
   - ✅ **ALWAYS** explain what parameters were used
   - ✅ **ALWAYS** suggest options and ask for permission
   - ✅ **ALWAYS** wait for explicit user confirmation before re-executing

### Step 5: 延伸检索

如果用户需要更多文献或调整筛选条件：

- **扩大检索范围**：`--time-range unlimited` 或 `--time-range 10y`
- **获取更多结果**：`--max-results 20`
- **聚焦特定数据源**：可在脚本中启用/禁用特定 API（需修改配置）
- **细化主题**：调整 `--topic` 或 `--keywords` 为更具体的关键词

## Data Sources

本 Skill 使用以下**免费、无需认证**的学术数据源：

| 数据源 | 覆盖范围 | 优势 | API |
|--------|---------|------|-----|
| **Semantic Scholar** | 计算机科学、生物医学 | 提供引用量、摘要、推荐论文 | ✅ API (免费) |
| **arXiv** | 物理、数学、计算机、生物 | 预印本、最新研究、免费全文 | ✅ API (免费) |
| **CrossRef** | 全球学术文献 | DOI 元数据、覆盖面广 | ✅ API (免费) |
| **Google Scholar** (fallback) | 全学科 | 覆盖最广 | ❌ 网页抓取 (限速率) |

**数据源优先级**（根据应用领域自动优化）：

### 统计决策领域 (`--domain statistics`)
1. **CrossRef**（首选）- 覆盖统计学、运筹学期刊最佳
2. **Semantic Scholar**（次选）- 提供引用量和质量指标
3. **arXiv**（补充）- 统计学预印本

### 人工智能领域 (`--domain ai`)
1. **arXiv**（首选）- AI领域最新预印本最多
2. **Semantic Scholar**（次选）- 综合质量高，有引用数据
3. **CrossRef**（补充）- 会议论文和期刊覆盖

### 金融统计领域 (`--domain finance`)
1. **CrossRef**（首选）- 覆盖金融学、计量经济学期刊最佳
2. **Semantic Scholar**（次选）- 提供引用量和质量指标
3. **arXiv**（补充）- 金融科技（FinTech）预印本

### 通用领域 (`--domain general` 或默认)
1. **Semantic Scholar**（首选）- 综合质量最佳
2. **CrossRef**（次选）- 覆盖面广
3. **arXiv**（补充）- 预印本

如需访问**付费数据库**（Web of Science、Scopus、CNKI、万方），请提供机构订阅信息，可扩展 Skill 功能。

## Parameters

### 核心参数

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--topic` | ✅ | 无 | 研究主题（自然语言） |
| `--domain` | ❌ | `general` | 应用领域（statistics/ai/finance/general）|
| `--keywords` | ❌ | 空 | 精准关键词（逗号分隔） |
| `--time-range` | ❌ | `3y` | 时间范围（1y/3y/5y/10y/unlimited/YYYY-MM-DD:YYYY-MM-DD） |
| `--max-results` | ❌ | 8 | 返回论文数量 |
| `--sort-by` | ❌ | `relevance` | 排序方式（relevance/citation_count/publish_date） |
| `--language` | ❌ | `bilingual` | 语言偏好（zh/en/bilingual） |
| `--output-format` | ❌ | `json` | 输出格式（json/markdown/csv） |
| `--output` | ❌ | stdout | 输出文件路径 |

### 时间范围参数详解

| 参数值 | 含义 | 示例 |
|-------|------|------|
| `1y` | 近1年 | `--time-range 1y` |
| `3y` | 近3年 | `--time-range 3y` |
| `5y` | 近5年 | `--time-range 5y` |
| `10y` | 近10年 | `--time-range 10y` |
| `unlimited` | 不限年份 | `--time-range unlimited` |
| `2020-2023` | 自定义年份范围 | `--time-range 2020-2023` |
| `2020-01-01:2023-06-30` | 精确日期范围 | `--time-range 2020-01-01:2023-06-30` |

### 排序方式详解

| 参数值 | 含义 | 适用场景 |
|-------|------|---------|
| `relevance` | 相关度排序（默认） | 一般检索，找最相关论文 |
| `citation_count` | 按引用量排序 | 找高影响力、经典论文 |
| `publish_date` | 按发表时间排序 | 找最新研究 |

### 应用领域参数详解

| 参数值 | 适用领域 | 数据源优先级 | 特点说明 |
|-------|---------|------------|---------|
| `statistics` | 统计决策 | CrossRef → Semantic Scholar → arXiv | 优先统计期刊，覆盖运筹学、概率论 |
| `ai` | 人工智能 | arXiv → Semantic Scholar → CrossRef | 优先最新预印本，覆盖机器学习、深度学习 |
| `finance` | 金融统计 | CrossRef → Semantic Scholar → arXiv | 优先金融期刊，覆盖计量经济学、金融科技 |
| `general` | 通用（默认） | Semantic Scholar → CrossRef → arXiv | 综合质量最佳，适合跨学科检索 |

## Pitfalls

### API 限速率
Semantic Scholar、arXiv、CrossRef 均有请求频率限制。
**修复**：单次检索已优化为单次 API 调用，批量检索时请间隔 2 秒以上。

### 跨领域检索结果不准确
如果主题过于宽泛（如 "machine learning"），可能返回大量无关文献。
**修复**：细化检索主题，添加具体关键词（如 "machine learning in medical imaging"）。

### 中文检索效果有限
Semantic Scholar 和 CrossRef 对中文论文的支持不如英文。
**修复**：
- 优先使用英文关键词检索
- 如需检索中文核心期刊，请提供知网/万方访问权限，可扩展 Skill

### 时间范围过滤依赖 API 支持
部分 API（如 CrossRef）的时间过滤功能有限，可能返回超出时间范围的文献。
**修复**：脚本会在 API 结果基础上进行二次过滤，确保结果符合时间范围要求。

### 引用量数据不完整
并非所有论文都有引用量数据（新论文、预印本通常引用量为0）。
**修复**：按引用量排序时，引用量相同的论文按相关性排序。

## Verification

确认 skill 工作正常的测试步骤：

```bash
# 1. 基本检索测试
python ${HERMES_SKILL_DIR}/scripts/paper_search.py --topic "quantum computing" --max-results 3

# 2. 时间范围测试
python ${HERMES_SKILL_DIR}/scripts/paper_search.py --topic "blockchain" --time-range 1y

# 3. 引用量排序测试
python ${HERMES_SKILL_DIR}/scripts/paper_search.py --topic "deep learning" --sort-by citation_count

# 4. Markdown 输出测试
python ${HERMES_SKILL_DIR}/scripts/paper_search.py --topic "computer vision" --output-format markdown --output results.md
```

**预期结果**：
- 脚本正常退出（返回码 0）
- 输出包含论文列表（标题、作者、摘要等）
- 如果使用 Markdown 输出，生成 .md 文件

## Integration with Report Generator

本 Skill 检索到的论文数据可被 `report-generator` Skill 用于生成 PDF 报告：

```bash
# 步骤1：检索论文并保存为 JSON
python ${HERMES_SKILL_DIR}/scripts/paper_search.py \
  --topic "人工智能在医学影像中的应用" \
  --time-range 3y \
  --max-results 10 \
  --output-format json \
  --output papers.json

# 步骤2：生成 PDF 报告（需要 report-generator skill）
python ${HERMES_SKILL_DIR}/../report-generator/scripts/generate_report.py \
  --input papers.json \
  --output report.pdf
```

## Extensions

### 未来可扩展功能

1. **更多数据源支持**：
   - 添加 PubMed API（生物医学）
   - 添加 IEEE Xplore API（需机构订阅）
   - 添加 CNKI/万方 API（需机构认证）

2. **高级筛选**：
   - 按期刊类型筛选（SCI/EI/核心期刊）
   - 按影响因子筛选
   - 按研究方法筛选

3. **全文下载**：
   - 集成 Sci-Hub、Library Genesis（需用户自行解决法律问题）
   - 支持开放获取论文自动下载

4. **文献管理**：
   - 导出 BibTeX、EndNote 格式
   - 生成 Zotero 可导入文件
   - 管理检索历史

5. **智能推荐**：
   - 基于检索结果推荐相关论文
   - 分析研究趋势和热点
   - 识别研究空白和未来方向
