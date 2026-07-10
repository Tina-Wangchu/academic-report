---
name: report-generator
description: "Generate professional academic Markdown reports with deep research trend analysis from paper search results. Use when the user asks to create a report, generate analysis, export results, or produce a formatted document from paper searches — supports comprehensive summary, detailed paper analysis, innovation patterns, research hotspots, temporal evolution, gaps analysis, and future directions."
version: 2.0.0
author: agent-scholar
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [academic, report, markdown, analysis, research-trends, innovation]
    category: my-category
required_environment_variables: []
---

# Report Generator — 学术论文深度分析报告生成器

将 paper_search.py 检索到的论文数据生成专业 Markdown 格式的学术报告，包含深度研究趋势分析、创新模式识别、研究热点聚类、时间演进分析和未来方向预测。

## When to Use

当用户提出以下需求时激活：
- "帮我生成论文检索报告"
- "创建研究报告"、"Generate research report"
- "导出检索结果"、"Export search results"
- "制作文献综述报告"、"Create literature review report"
- "生成学术分析报告"
- "研究趋势分析"

## Quick Reference

| 需求 | 操作 |
|---|---|
| 生成增强分析报告 | `python generate_report_enhanced.py --input papers.json --output report.md` |
| 生成标准Markdown报告 | `python generate_report_markdown.py --input papers.json --output report.md` |
| 查看示例 | 先用 paper_search.py 检索，然后用 generate_report_enhanced.py 生成报告 |

## Procedure

### Step 1: 确认输入数据

确保已经通过 paper_search.py 生成了 JSON 格式的检索结果：

```bash
# 示例：先执行论文检索
python ${HERMES_SKILL_DIR}/../paper-search/scripts/paper_search.py \
  --topic "machine learning in education" \
  --time-range 3y \
  --max-results 10 \
  --output-format json \
  --output papers.json
```

### Step 2: 生成增强报告

使用 generate_report_enhanced.py 生成深度分析报告：

```bash
# 生成增强Markdown报告（推荐）
python ${HERMES_SKILL_DIR}/scripts/generate_report_enhanced.py \
  --input papers.json \
  --output enhanced_report.md
```

### Step 3: 展示结果

报告生成完成后，告知用户：

```
✅ 深度分析报告已生成

📄 报告内容：
- 综合研究概况（范围、质量指标、数据源分析）
- 核心论文列表（带关键词和元数据）
- 深度论文分析（方法论、贡献、见解）
- 创新模式分析（类型分布、主导模式）
- 研究热点聚类（关键词集群、代表性论文）
- 时间演进分析（年度趋势、新兴方向）
- 研究空白识别（方法论、应用、理论空白）
- 未来方向建议（优先级、时间线）

📊 深度洞察：
- 创新模式：理论vs方法vs应用
- 研究热点：Top 10研究集群
- 演进趋势：跨年度发展方向
- 空白机会：未充分探索的领域
```

### Step 4: 交付报告

提供报告文件路径，并说明用途：

- **文献综述撰写**：可直接用于论文的文献综述部分，包含趋势分析
- **课题调研**：作为开题报告的附件，包含未来方向
- **学术分享**：Markdown格式便于转换和展示
- **研究规划**：基于空白识别制定研究计划
- **数据备份**：保存检索结果和分析供后续参考

## Report Structure

生成的增强 Markdown 报告包含以下深度分析章节：

### 1. 综合研究概况 (Comprehensive Research Summary)
- 研究范围和覆盖度分析
- 质量指标（时效性、完整性、影响因子）
- 数据源多样性和地理分布
- 语言覆盖和研究深度指标

### 2. 论文概览列表 (Papers Overview)
- 完整论文信息（标题、作者、发表时间、关键词）
- 结构化表格便于快速浏览
- 关键词提取和分类

### 3. 深度论文分析 (Individual Paper Analysis)
每篇论文包含：
- 完整元数据（作者、期刊、DOI、引用量）
- **研究焦点和方法论**：自动识别方法类型
- **关键贡献提取**：智能提取核心创新点
- **摘要智能总结**：聚焦关键发现
- **工具/技术识别**：提取使用的具体方法

### 4. 创新模式分析 (Innovation Pattern Analysis)
- **创新类型分布**：新颖性、理论、方法、性能、应用、集成
- **主导创新模式**：识别领域的主要创新驱动
- **代表性论文**：每种创新模式的典型案例
- **创新趋势**：定量分析各类型创新频率

### 5. 研究热点聚类 (Research Hotspots & Clusters)
- **Top研究集群**：基于关键词频率的聚类分析
- **热点强度**：频率、论文数量、近期增长
- **代表性论文**：每个热点领域的核心论文
- **年度分布**：热点的时间演进趋势
- **新兴热点**：识别快速增长的研究方向

### 6. 时间演进分析 (Temporal Research Evolution)
- **年度趋势表**：论文数量、增长率、新兴关键词
- **方法论演进**：主流方法的时间变化
- **新兴关键词**：每年出现的新研究方向
- **增长指标**：可视化增长趋势（📈/📉）

### 7. 研究空白识别 (Research Gaps & Opportunities)
- **方法论空白**：未充分利用的研究方法
- **应用领域空白**：应用研究的盲区
- **理论空白**：理论基础 vs 实践创新的平衡
- **战略建议**：基于空白的研究方向建议

### 8. 跨学科分析 (Cross-Domain Analysis)
- **跨学科研究检测**：识别明确的跨学科工作
- **学科融合机会**：潜在的交叉研究领域
- **融合趋势**：学科边界的演变

### 9. 未来方向建议 (Future Research Directions)
- **优先研究领域**：结合热点和空白的战略建议
- **影响时间线**：短期、中期、长期预期发展
- **研究建议**：基于数据的具体方向

### 10. 参考文献 (References)
- GB/T 7714-2015 格式的完整参考文献列表
- DOI可点击链接
- 按引用顺序编号

## Data Requirements

### 输入格式

generate_report_enhanced.py 接受 paper_search.py 输出的 JSON 格式文件，必须包含以下字段：

```json
{
  "status": "success",
  "query": "search query string",
  "total_found": 10,
  "sources_used": ["Semantic Scholar", "arXiv", "PubMed"],
  "domain": "statistics",
  "papers": [
    {
      "title": "Paper Title",
      "authors": ["Author1", "Author2"],
      "year": "2023",
      "published": "2023-05-15",
      "journal": "Journal Name",
      "doi": "10.xxxx/xxxxx",
      "citationCount": 150,
      "abstract": "Full abstract text...",
      "url": "https://...",
      "source": "Semantic Scholar"
    }
  ],
  "filters_applied": {
    "time_range": {
      "start_date": "2021-06-28",
      "end_date": "2024-06-28"
    }
  },
  "timestamp": "2024-06-28T10:30:45.123Z"
}
```

## Parameters

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | ✅ | 无 | 输入 JSON 文件路径（来自 paper_search.py） |
| `--output` | ✅ | 无 | 输出 Markdown 报告文件路径 |

## Output Format

### Markdown 格式（推荐）
- **优点**：
  - 无额外依赖，使用Python标准库
  - 深度分析功能，智能提取见解
  - 可编辑、可扩展性强
  - 支持转换到Word、LaTeX、PDF等格式
- **特点**：
  - 清晰的层次结构
  - 表格化数据展示
  - 智能关键词提取
  - 自动方法论识别
  - 研究趋势深度分析

### 转换选项
```bash
# Markdown → PDF
pandoc enhanced_report.md -o report.pdf

# Markdown → Word
pandoc enhanced_report.md -o report.docx

# Markdown → LaTeX
pandoc enhanced_report.md -o report.tex
```

## Analysis Features

### 🔍 智能关键词提取
- 基于标题和摘要的关键词识别
- 自动过滤常见停用词
- 跨领域关键词聚类分析

### 🎯 方法论识别
- 自动识别研究方法类型（理论、实验、计算、统计、机器学习、综述）
- 提取使用的具体工具和技术
- 方法论分布统计分析

### 🚀 创新模式分析
- 六种创新类型识别
- 创新频率和模式量化
- 代表性论文和案例研究

### 🔥 研究热点检测
- 基于关键词频率的聚类算法
- 热点强度和趋势分析
- 年度分布演进追踪

### 📅 时间演进分析
- 跨年度论文数量变化
- 新兴关键词识别
- 方法论趋势演进
- 增长率可视化

### 🔍 研究空白识别
- 方法论使用不足检测
- 应用领域覆盖分析
- 理论-实践平衡评估
- 基于数据的机会识别

### 🌐 跨学科分析
- 跨学科研究自动检测
- 学科融合趋势识别
- 交叉学科机会发现

## Requirements

### Python 依赖
- 使用 Python 标准库，无额外依赖
- 可选：`pandoc` 用于格式转换

### 中文支持
- Markdown 原生支持 UTF-8
- 完美支持中英文混合内容
- 无需额外字体配置

## Pitfalls

### 输入 JSON 格式错误
如果输入文件不是有效的 JSON 或缺少必需字段，会生成失败。
**修复**：
1. 检查输入文件是否来自 paper_search.py
2. 确认 JSON 包含 `status: "success"` 字段
3. 确认 `papers` 数组不为空且包含摘要字段

### 摘要数据缺失
深度分析依赖论文摘要数据，如果摘要缺失会影响分析质量。
**修复**：
1. 确保检索时获取完整摘要
2. 调整 paper_search.py 的摘要获取参数
3. 使用标准版本报告生成器

### 论文数量不足
论文数量少于5篇时，趋势分析可能不够准确。
**修复**：
1. 扩大时间范围或关键词
2. 增加 `--max-results` 参数
3. 结合多个数据源

### 关键词提取质量
某些领域特定的关键词可能无法准确提取。
**修复**：
1. 手动编辑生成的 Markdown 文件
2. 调整停用词列表
3. 基于具体领域定制关键词词典

## Complete Workflow

完整的论文检索 + 深度分析报告生成工作流：

```bash
# 步骤1：执行论文检索
python ${HERMES_SKILL_DIR}/../paper-search/scripts/paper_search.py \
  --topic "人工智能在医学影像中的应用" \
  --keywords "AI,medical imaging,deep learning" \
  --time-range 3y \
  --max-results 25 \
  --sort-by citation_count \
  --output-format json \
  --output medical_ai_papers.json

# 步骤2：生成深度分析报告
python ${HERMES_SKILL_DIR}/scripts/generate_report_enhanced.py \
  --input medical_ai_papers.json \
  --output medical_ai_analysis.md

# 步骤3：（可选）转换为PDF用于打印
pandoc medical_ai_analysis.md -o medical_ai_report.pdf --pdf-engine=xelatex
```

**输出**：
- `medical_ai_papers.json` — 原始检索数据
- `medical_ai_analysis.md` — 深度分析Markdown报告（包含所有趋势分析）
- `medical_ai_report.pdf` — 专业PDF版本（可选）

## Verification

确认 skill 工作正常的测试步骤：

```bash
# 1. 先执行论文检索
python ${HERMES_SKILL_DIR}/../paper-search/scripts/paper_search.py \
  --topic "machine learning statistics" \
  --time-range 2y \
  --max-results 10 \
  --output-format json \
  --output test_papers.json

# 2. 生成增强分析报告
python ${HERMES_SKILL_DIR}/scripts/generate_report_enhanced.py \
  --input test_papers.json \
  --output test_analysis.md

# 3. 验证输出文件
ls -la test_analysis.md
wc -l test_analysis.md  # 应该 > 100行深度分析
```

**预期结果**：
- `test_papers.json` 包含有效的检索结果和摘要
- `test_analysis.md` 文件大小 > 0
- Markdown 文件包含完整的分析章节
- 可识别创新模式、研究热点、演进趋势等分析内容

## Integration with Other Tools

### 转换为学术格式
```bash
# LaTeX格式（论文写作）
pandoc analysis.md -o paper_section.tex --standalone

# Word格式（编辑）
pandoc analysis.md -o manuscript.docx

# HTML格式（网页展示）
pandoc analysis.md -o webpage.html --standalone
```

### 文献管理集成
从报告中的参考文献部分提取，可转换为：
- **BibTeX**：用于LaTeX论文
- **EndNote**：商业文献管理软件
- **Zotero**：开源文献管理工具

## Extensions

### 高级功能扩展
1. **可视化图表**：
   - 集成 matplotlib 生成趋势图
   - 研究热点网络图
   - 跨年度演进折线图

2. **自然语言处理**：
   - 摘要自动摘要
   - 关键发现提取
   - 研究方法自动分类

3. **知识图谱**：
   - 论文引用关系网络
   - 作者合作关系图
   - 研究主题演化图

4. **预测分析**：
   - 研究趋势预测
   - 新兴方向识别
   - 投资价值评估

## Quality Assurance

### 报告质量检查清单
- ✅ 所有必需字段都存在（标题、作者、摘要）
- ✅ 关键词提取准确且相关
- ✅ 方法论识别正确
- ✅ 创新模式分析合理
- ✅ 研究热点符合直觉
- ✅ 时间演进趋势逻辑一致
- ✅ 空白识别有实际意义
- ✅ 格式化Markdown语法正确
- ✅ 参考文献格式标准

### 分析深度验证
- 📊 **定量分析**：包含频率、百分比、趋势数据
- 🎯 **定性分析**：提供见解和解释
- 🔍 **深度洞察**：不只是数据，还有分析
- 🚀 **可操作性**：提供具体建议和方向