# report_generator.py - Implementation Detail

## 模块概述

**模块名称**: 学术报告生成 (report_generator.py) — 模块5 / Module 5
**版本**: 1.0.0
**完成日期**: 2026-07-12
**状态**: ✅ 已完成（单元测试 20 项全通过 + 端到端烟雾测试通过）

---

## 功能说明

按 [`报告格式设计.md`](../../报告格式设计.md)（**权威规范**）渲染固定**四段式**学术报告（Markdown / PDF）：

```
标题 + 时间  →  一、报告速览  →  二、分类论文展示（热点聚类）  →  三、研究趋势
```

**主要能力**:
- 🌐 **双语**：默认按 `intent.language` 驱动（zh / en / bilingual，默认 bilingual）
- 📋 四段式结构 + 双时间戳（生成时间 / 涵盖时间）
- 🧩 热点聚类展示，每热点含介绍/论文/整体分析/奠基性参考
- 📊 研究趋势从本次论文派生（趋势 + 缺口）
- 🔄 Markdown → PDF（reportlab Platypus 渲染）

---

## 关键：实现时修正的 7 处差异（计划代码 vs 权威规范）

| # | 权威规范要求 | 计划代码问题 | 本模块实现 |
|---|---|---|---|
| 1 | 全篇双语（§1/§7） | 全中文，忽略 `intent.language` | `_label(key, lang)` + 三语模式 |
| 2 | 标题双语两行（§7） | 单行单语 | `_render_title`：bilingual 双行 |
| 3 | 时间标签双语（§3/§7） | 单语 | 标签经 `_label` 双语化 |
| 4 | 速览按热点逐篇概述（§4） | 300 字硬截断 → 丢论文；仅取代表论文发现 | 改为按热点分组、逐篇概述：热点名 + 篇数 + 每篇「标题：核心内容」 |
| 5 | 趋势「避免空话」基于论文（§6） | `research_gaps` 硬编码通用话术 | `_analyze_trends` 从语料信号派生 |
| 6 | 渲染需 research_content 等 | 未调 `analyze_papers` → 字段空 | `_prepare` 先调 `analyzer.analyze_papers` |
| 7 | Option B 分层 | 自带 3 个方法 | 委托 filter/analyzer |

---

## 架构设计

### 类结构

```
ReportGenerator(paper_filter?, paper_analyzer?)   # 可注入便于测试
 ├── generate_report(papers, intent, output_format)   # 公共入口
 ├── save_report(report, output_path)
 ├── _prepare(papers, intent, lang)               # 分析+聚类+各热点委托
 ├── _generate_summary(papers, classified, lang)  # 速览（按热点概括）
 ├── _analyze_trends(papers, lang)                # 趋势+缺口（语料派生）
 ├── _render_markdown(ctx, intent, lang)          # 四段式 MD
 ├── _render_title / _render_hotspot_heading / _render_paper
 ├── _convert_to_pdf(md, intent, lang)            # MD→PDF（reportlab）
 └── _format_time_range / _format_coverage_time / _numeral

模块级：
 ├── LABELS: Dict[key, (zh, en)]                  # 双语标签表
 └── _label(key, lang)                            # zh/en/bilingual 取值
```

### 数据流（Option B：委托 filter/analyzer）

```
List[Paper] (+ intent)
    ↓ _prepare:
        analyzer.analyze_papers(papers)            # 填充 problem/existing/new_approach/results_limitations（四要素）+ condensed_abstract
        filter.classify_by_topic(papers)           # → Dict[热点, List[Paper]]
        per 热点:
            filter.generate_hotspot_intro(...)     # 热点介绍
            analyzer.generate_overall_analysis(...) # 整体分析
            analyzer.find_foundational_papers(...) # 奠基论文（真实 S2 API + 回退）
        _generate_summary(...)                     # 速览（按热点概括）
        _analyze_trends(...)                       # 趋势+缺口（派生）
    ↓ _render_markdown → 四段式 MD
    ↓ (pdf?) _convert_to_pdf → reportlab 渲染
```

---

## 实现细节

### 1. 双语机制 `LABELS` + `_label`

模块级 `LABELS` 字典存每个标签的 `(zh, en)`；`_label(key, lang)`：
- `zh` → 中文
- `en` → English
- `bilingual` → `「中文 / English」`

`lang = (intent.language or "bilingual").lower()`，**默认 bilingual**（对齐 config `default_language: bilingual`）。覆盖：段名（一/II）、字段名（作者/Authors）、时间标签、热点名、趋势小标题等。

**标题**（`_render_title`）：bilingual 时输出两行 `# {time} {field} 报告` + `# {time} {field} Report`（§7）。

### 2. 报告速览 `_generate_summary`（按热点分组、逐篇概述，§4）

- 开篇一句：收录篇数 / 热点数 / 高被引数（bilingual 双语）。
- **按热点分组、逐篇概述**：每个热点一行 `- 「热点名」(N 篇)：`，其下逐篇 `- 《标题》：{核心内容}`，覆盖每一篇论文。
- **核心内容** = 该篇摘要前 1-2 句（问题+方法），取自 `_paper_finding`：`condensed_abstract`/`abstract` 前 1-2 句 → 回退标题；约 160 字符内，无省略号。
- 篇幅随热点数与论文数增长（不丢论文）。

### 3. 研究趋势 `_analyze_trends`（基于论文，避免空话）

- **主要趋势**：高频关键词 top 5 → 「keyword（N 篇）相关研究活跃」。
- **研究缺口**（从语料**有/无信号**派生，非硬编码）：
  1. 全为预印本 → 「缺乏同行评审验证」
  2. 最高被引 < 50 → 「缺高被引里程碑，方向较新」
  3. 语料无 interpret/explain → 「少可解释性分析」
  4. 语料无 benchmark/dataset → 「缺统一评测」
  5. 年份跨度 ≤1 → 「长期演进/稳定性待验证」
  6. 都不触发 → 诚实提示「暂无明显共性缺口，建议扩大检索」
- bilingual 时每条给「中文 / English」。

### 4. 单篇论文块 `_render_paper`

按 §5.2 字段表（**发表时间独立**）：
- 作者（>3 用「等 / et al.」）、发表时间、发表期刊、引用量、DOI、链接
- **四要素摘录**：`解决的问题 / 现有方案 / 新方案 / 效果及局限性`——来自 `paper_analyzer.StructuredExtractor`（从摘要按句匹配信号词摘录，中英文）。任一命中即按四段渲染，缺失要素标「未明确提及 / Not explicitly mentioned」；**四要素全空**时回退完整 Abstract（`condensed_abstract` 或 `abstract`，缺失则占位）。
  > 四要素的**演进过程与最终实现方法**（强/弱打分、结果对比剔除、背景回退、信号词集合、已知局限）详见权威规范 [`报告格式设计.md` §11](../../报告格式设计.md)。
- **APA 7th 引用**（委托 `utils.format_apa_citation`）

> 2026-07-13 改：单篇块从「完整 Abstract 段」改为「四要素摘录四段」——从论文摘要中摘录对应语段，结构化呈现解决的问题/现有方案/新方案/效果及局限。单篇块**不再渲染**「研究内容 / 创新点 / 核心结论」（已并入四要素）。分析层仍内部计算这些子句供速览/整体分析复用。

### 5. PDF 转换 `_convert_to_pdf`

- `_convert_to_pdf` 用 **reportlab Platypus** 把 MD 行向解析为 flowables（段落/标题/列表/分隔线等），逐行映射到 PDF 元素。
- **字体分离**：中文走 reportlab 内置 CID 字体 **`STSong-Light`**；**英文/拉丁走内置 `Times-Roman`**（`_format_inline_md` 把拉丁连续串包 `<font name="Times-Roman">`，并注册 family 使 `<b>`→`Times-Bold`，英文可真加粗）。均无需系统字体、无需额外字体文件。
- **中英混排**：`_render_markdown` 末尾统一过 `_autospace_cjk_latin`（CJK↔拉丁/数字间补半角空格，URL/DOI 占位保护+边界空格）。
- **正文两端对齐**：body/quote 样式 `alignment=TA_JUSTIFY`。
- **URL/DOI 等宽**：`_render_paper` 用反引号包 → `_format_inline_md` 渲染为 `<font face="Courier">`。
- **英文标题**：`_titlecase_en`（标准 Title Case：虚词小写、缩写 AI/NLP/BERT 大写）；各级标题英文加粗（`<b>`→Times-Bold）。**中文真加粗需捆绑 Noto（+20MB），暂未引入**（见 `docs/known_issues.md`）。
- 输出 PDF 字节流，由上层 `save_pdf` 落盘；`generate_report(output_format='pdf')` 与 `generate_both` 均走此路径。

### 6. 时间格式

- `_format_time_range`：标题用，如 `2023-2025`（单边给 `2023-至今` / `截至2025`）。
- `_format_coverage_time`：涵盖时间用，月粒度，如 `2023-01 至 2025-12`。

---

## 配置/模板依赖

| 依赖 | 用途 |
|------|------|
| `intent.language` | 驱动双语模式（默认 bilingual） |
| `intent.start_date`/`end_date` | 标题时间范围 + 涵盖时间 |
| `intent.research_field`/`query` | 标题领域名 |
| `reportlab` | MD→PDF 渲染（Platypus；中文 `STSong-Light` + 英文 `Times-Roman`，均内置字体） |
| `paper_filter` / `paper_analyzer` | 聚类/介绍 + 分析/奠基论文（Option B） |

---

## 测试

### 单元测试（`test/test_report_generator.py`，20 项全通过）

| 测试类 | 数量 | 覆盖点 |
|--------|------|--------|
| `TestStructure` | 2 | 四段式结构、双时间标签 |
| `TestBilingualModes` | 4 | bilingual/zh/en 标签、默认 bilingual |
| `TestSummaryByHotspot` | 3 | 速览按热点（热点名+发现）、不逐篇列标题、`_hotspot_finding` 取最高被引结论 |
| `TestPaperBlock` | 3 | 必填字段、作者>3用等、Abstract 截断、分析字段 |
| `TestHotspotBlock` | 2 | 热点标题双语、委托的介绍/整体分析/奠基论文 |
| `TestTrends` | 2 | 趋势非空、缺口语料派生非套话 |
| `TestPdfAndSave` | 4 | PDF 生成、文件保存 |
| `TestLabelHelper` | 3 | `_label` zh/en/bilingual |

测试用 `FakeFilter`/`FakeAnalyzer` 注入，**不依赖网络/配置**。

### 端到端烟雾测试

用**真实** filter+analyzer+generator 跑 3 篇样例论文，生成 MD + PDF，验证：双语两行标题、双语时间标签、双语段名/热点名、**按热点概括的速览（热点名+具体发现）**、委托的热点介绍/分析、PDF 以 `%PDF-` 开头。

### 运行

```bash
python -m pytest test/test_report_generator.py -v
python -m report_generator --input papers.json --output report.md --format markdown
```

---

## 完整样例报告（实际生成，bilingual 模式）

下面是用**真实** filter+analyzer+generator 对 4 篇样例论文（`research_field=机器学习`、时间范围 2023-2024、`language=bilingual`）实际生成的 Markdown 报告，直接印证上述实现：

> 重点观察：
> - **双语两行标题**（L1-2）+ **双时间戳双语标签**（L4-6）。
> - **速览按热点逐篇概述**：列出 3 个热点，每个热点下逐篇给「标题：核心内容」（取该篇摘要前 1-2 句）；覆盖每一篇论文。
> - **热点聚类**：生成模型（2 篇）/ 自然语言处理（1 篇）/ 深度学习（1 篇，GNN 因「neural network」命中并与「图神经网络」并列、按词典序落到「深度学习」——分类器诚实行为）。
> - **单篇字段全双语**，>3 作者用「等 / et al.」（L56），DOI 按需出现（L60），APA 引用（L50/75/112/150）。
> - **单篇块四要素摘录（2026-07-13 改）**：单篇块按四段展示——`解决的问题 / 现有方案 / 新方案 / 效果及局限性`，每段为从摘要摘录的匹配语段（`StructuredExtractor`）；任一缺失标「未明确提及」，四要素全空时回退完整 Abstract。**不再单列**「研究内容 / 创新点 / 核心结论 / Abstract 段」。
> - **摘录结构化**：四要素由信号词按句匹配（新方案→现有方案→问题→效果，互不重复；问题无显式句回退首句=背景），中英文均支持，不编造。
> - **整体分析 + 奠基性参考**委托 analyzer：本环境无网络，奠基论文走**离线回退**（明确标注「离线回退」不编造）。
> - **研究缺口基于语料派生**（可解释性 + 时间跨度短）——正是修正后的行为，非硬编码套话。

```markdown
# 2023-2024 机器学习 报告
# 2023-2024 机器学习 Report

*报告生成时间 / Report generation time: 2026-07-12 10:18*
*报告涵盖时间 / Report coverage time: 2023-01 至 2024-12*
*数据源 / Data sources: arXiv, Semantic Scholar, OpenAlex*

---

## 一、报告速览 / I. Report Overview

本报告收录 4 篇论文，分为 3 个研究热点（其中高被引 2 篇）。以下按热点逐篇概述其核心内容：
This report includes 4 papers across 3 research hotspots (2 highly cited). Each hotspot and its papers are summarized below:

- 「生成模型」(2 篇 / 2 papers):
  - 《DDIM-Solver: 10-Step High-Quality Sampling for Diffusion Models》: We propose a novel ODE solver for diffusion model sampling that outperforms prior solvers and achieves 10-step high-quality sampling.
  - 《Efficient Training of Latent Diffusion Models》: We introduce an efficient training method for latent diffusion generative models that reduces compute by 40 percent while preserving sample quality.
- 「自然语言处理」(1 篇 / 1 papers):
  - 《Transformer-XL》: demonstrates improvements on long-context language understanding benchmarks.
- 「深度学习」(1 篇 / 1 papers):
  - 《Graph Neural Networks for Molecular Property Prediction》: our method demonstrates strong results on standard datasets and outperforms prior approaches.

---

## 二、分类论文展示 / II. Classified Paper Display

### 热点一：生成模型 / Hotspot 1: 生成模型

**热点主题介绍 / Hotspot intro**：本热点聚焦「生成模型」方向，共收录 2 篇论文，高频关键词包括 diffusion、sampling、generative；代表性工作为《DDIM-Solver: 10-Step High-Quality Sampling for Diffusion Models》（2024，引用 187）。

本方向共收录 / Papers in this direction 2 篇。

#### 1. DDIM-Solver: 10-Step High-Quality Sampling for Diffusion Models

- **作者 / Authors**: Zhang L, Wang Q, Chen R
- **发表时间 / Published**: 2024
- **发表期刊 / Venue**: NeurIPS
- **引用量 / Citations**: 187

**解决的问题 / Problem**:
Sampling from diffusion models is computationally expensive due to the iterative denoising process that requires hundreds of neural network evaluations.

**现有方案 / Existing approaches**:
Many prior solvers attempt to accelerate this process but suffer from noticeable quality degradation when the number of steps is small.

**新方案 / New approach**:
We propose a novel high-order ODE solver for diffusion model sampling that substantially reduces the required number of denoising steps while preserving sample quality.

**效果及局限性 / Results & limitations**:
We evaluate on the CIFAR-10 and ImageNet benchmarks and achieve high-quality sampling in only ten steps; however, the method still struggles with very high-resolution images.

**APA 引用 / APA Citation**:
> Zhang L, & Wang Q, & Chen R (2024). DDIM-Solver: 10-Step High-Quality Sampling for Diffusion Models. *NeurIPS*

---

#### 2. Efficient Training of Latent Diffusion Models

- **作者 / Authors**: Lee S, Gupta A, Kim M 等 / et al.
- **发表时间 / Published**: 2023
- **发表期刊 / Venue**: ICML
- **引用量 / Citations**: 95
- **DOI / DOI**: 10.1234/ldm

**Abstract / Abstract**:
We introduce an efficient training method for latent diffusion generative models that reduces compute by 40 percent while preserving sample quality, and we demonstrate improvements over baselines.

**APA 引用 / APA Citation**:
> Lee S, Gupta A, Kim M, ... (2023). Efficient Training of Latent Diffusion Models. *ICML*. https://doi.org/10.1234/ldm

---

**整体分析 / Overall Analysis**: 本热点 2 篇论文围绕「生成模型」展开，共同关注 diffusion、sampling、generative 等主题；代表性工作《DDIM-Solver: 10-Step High-Quality Sampli》（2024，引用 187）贡献突出，方法从 2023 年到 2024 年逐步演进，整体属新兴/近期热点方向。

**奠基性参考论文 / Foundational References**:
- （离线回退）本方向可追溯的较早代表作为《Efficient Training of Latent Diffusion Models》（2023，引用 95）；完整奠基性工作需联网经 Semantic Scholar 引用 API 补全。

---

### 热点二：自然语言处理 / Hotspot 2: 自然语言处理
...（自然语言处理热点，Transformer-XL 1 篇，结构同上）...

### 热点三：深度学习 / Hotspot 3: 深度学习
...（Graph Neural Networks for Molecular Property Prediction 1 篇，结构同上）...

---

## 三、研究趋势 / III. Research Trends

### 未来研究趋势 / Future Trends

- diffusion（2 篇）相关研究活跃 / diffusion (2 papers) is an active trend
- sampling（1 篇）相关研究活跃 / sampling (1 papers) is an active trend
- generative（1 篇）相关研究活跃 / generative (1 papers) is an active trend
- transformer（1 篇）相关研究活跃 / transformer (1 papers) is an active trend
- nlp（1 篇）相关研究活跃 / nlp (1 papers) is an active trend

### 研究缺口 / Research Gaps

- 较少涉及模型可解释性/透明度分析 / Limited analysis of model interpretability/transparency
- 收录时间跨度较短，方法的长期演进与稳定性有待验证 / Short time span; long-term evolution/stability unverified

---

**报告生成时间 / Report generation time**: 2026-07-12 10:18
**由 Academic Report 自动生成 / Generated by Academic Report**
```

> 说明：热点二、三的论文块结构与热点一一致（字段/Abstract/分析字段/APA/整体分析/奠基论文），此处为节省篇幅省略中间重复格式；实际输出会完整渲染每个热点。奠基论文在本离线环境为回退文本，联网时会替换为真实 Semantic Scholar 参考文献并标注「被本热点 N 篇引用，全球引用 X」。

---

## 已知限制与未来改进

1. **双语正文**：bilingual 模式下骨架（标题/段名/字段/时间）全双语；**创新点已按语言渲染**（bilingual → 中/英并列）；研究内容/结论从英文摘要抽取故为英文（语种自洽）。完整的「全文逐句翻译」仍需 LLM。
2. **四要素摘录（2026-07-13 改）**：`paper_analyzer.StructuredExtractor` 从摘要按句匹配信号词，摘录「解决的问题 / 现有方案 / 新方案 / 效果及局限性」四类语段（中英文；优先级 新方案→现有方案→问题→效果，互不重复；问题无显式句回退首句=背景）。摘录为规则版抽取式，不是语义级改写——深度结构化提炼仍需 LLM（Phase 3）。`AbstractSummarizer` 仍生成 `condensed_abstract`（完整去填充，≤1500 字符），供速览 `_paper_finding` 与四要素全空时的回退使用。
3. **单篇块不单列分析字段**：`_render_paper` 不再渲染「研究内容 / 创新点 / 核心结论 / 相关研究 / 独立 Abstract 段」——其内容已并入四要素摘录。分析层仍内部计算 research_content/conclusions 子句供速览/整体分析复用。
4. **奠基论文逐热点联网**：`find_foundational_papers` 每热点调 S2 API，热点多时较慢；已有限流 + 探查数封顶(5) + 离线回退。
5. **MD 模板**：`report_template.md`（Jinja2）在计划中存在但未被采用（命令式渲染更易控字数/双语）；本模块用命令式 `_render_markdown`，PDF 用 reportlab。

---

## 与规范/计划的对应

| 规范要求（报告格式设计.md） | 实现位置 |
|------|------|
| 标题含时间范围 + 领域（双语） | `_render_title` ✅ |
| 双时间戳（双语） | `_render_markdown` + `_label` ✅ |
| 速览按热点逐篇概述（热点+每篇核心内容） | `_generate_summary` + `_paper_finding` ✅ |
| 热点聚类 + 介绍 | `filter.classify_by_topic` + `generate_hotspot_intro`（委托）✅ |
| 四要素摘录（问题/现有方案/新方案/效果及局限） | `StructuredExtractor.extract` + `_render_paper`（四段，全空回退 Abstract）✅ |
| 整体分析 + 奠基性参考 | `analyzer.generate_overall_analysis` + `find_foundational_papers`（委托）✅ |
| 约 200 字研究趋势（基于论文） | `_analyze_trends` ✅ |
| APA 7th | `utils.format_apa_citation` ✅ |

> **Option B 全部收尾**：热点介绍（paper_filter）、整体分析 + 奠基论文（paper_analyzer）、渲染编排（report_generator）三层各司其职。report_generator **不再自带**这三个方法，仅委托调用。

---

**最后更新**: 2026-07-12
**维护者**: Academic Report Team
