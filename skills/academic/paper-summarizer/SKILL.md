---
name: paper-summarizer
description: "AI-powered paper analysis and summarization. Use when enhanced 300-word abstracts are needed that capture key research findings, methodology, and contributions."
version: 1.0.0
author: agent-scholar
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [academic, research, ai, summarization, analysis]
    category: my-category
required_environment_variables: []
optional_environment_variables: []
---

# Paper Summarizer — AI论文分析摘要生成器

通过AI工具对论文进行深度分析，生成300字的精准摘要，覆盖关键研究成果和特点。

## When to Use

当用户需要：
- 生成详细的300字论文摘要
- 深度分析论文的研究贡献和方法
- 提炼论文的关键创新点和应用价值

## Quick Reference

| 需求 | 操作 |
|---|---|
| 基础摘要 | `python paper_summarizer.py --input papers.json --output summarized.json` |
| 批量处理 | 自动处理JSON中的所有论文 |
| 增强摘要 | 每篇论文生成300字精准摘要 |

## Procedure

### Step 1: 准备输入数据

输入JSON文件应包含论文数据：
```json
{
  "papers": [
    {
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "abstract": "Original abstract text...",
      "year": 2024,
      "journal": "Journal Name"
    }
  ]
}
```

### Step 2: 执行AI摘要生成

```bash
python ${HERMES_SKILL_DIR}/scripts/paper_summarizer.py \
  --input papers.json \
  --output summarized_papers.json
```

### Step 3: 使用增强摘要

输出的JSON文件包含：
- 原始论文数据
- 新增的 `ai_summary` 字段（300字精准摘要）
- 元数据和处理信息

## Output Format

每个论文对象新增以下字段：
```json
{
  "ai_summary": "300字的AI生成摘要，涵盖研究问题、方法、发现和贡献...",
  "summary_enhanced": true,
  "summary_date": "2026-07-05T12:00:00Z"
}
```

## Features

### 智能分析结构
1. **Research Problem** - 研究问题
2. **Methodology** - 研究方法
3. **Key Findings** - 主要发现
4. **Contributions** - 研究贡献
5. **Applications** - 应用价值

### 处理能力
- ✅ 批量处理多篇论文
- ✅ 保留原始数据完整性
- ✅ 智能提取关键信息
- ✅ 结构化摘要输出

## Integration

### 与报告生成器集成

```bash
# 步骤1：论文检索
python paper_search.py --topic "AI" --output papers.json

# 步骤2：AI摘要增强
python paper_summarizer.py --input papers.json --output summarized.json

# 步骤3：生成Markdown报告
python generate_report_markdown.py --input summarized.json --output report.md
```

## Verification

测试命令：
```bash
# 测试摘要生成
python paper_summarizer.py --input test_papers.json --output test_summarized.json

# 检查输出
cat test_summarized.json | grep -A 5 "ai_summary"
```
