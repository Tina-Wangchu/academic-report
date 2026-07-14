# paper_analyzer.py - Implementation Detail

## 模块概述

**模块名称**: 论文信息提取与深度分析 (paper_analyzer.py) — 模块4 / Module 4
**版本**: 1.0.0
**完成日期**: 2026-07-11
**状态**: ✅ 已完成（单元测试 28 项全通过）

---

## 功能说明

### 核心功能

本模块接收 `paper_filter` 筛选排序后的论文，完成「结构化提取 + 引用生成 + 方向级综合分析 + 奠基性参考论文查找」，输出供 `report_generator`（模块5）渲染报告。

**主要能力**:
- 🔬 单篇结构化提取——核心研究内容、创新点、核心结论、研究价值与应用场景
- 📑 APA 7th 引用格式生成
- 🧭 方向级**整体分析**（Option B：从 report_generator 迁入，规则版综合）
- 🏛️ 方向级**奠基性参考论文查找**（Option B：从 report_generator 迁入，并**真正调用 Semantic Scholar references API**，不再返回占位符）

---

## 架构设计

### 类结构

```
PaperAnalyzer                              # 公共门面
 ├── analyze_papers(papers)                # 批量单篇提取
 ├── format_citations(papers)              # APA 7th
 ├── generate_overall_analysis(topic, papers)   # Option B：方向级整体分析
 ├── find_foundational_papers(papers, top_n)    # Option B：奠基论文（含降级）
 ├── _extract_research_content / _extract_innovations
 ├── _extract_conclusions / _infer_application
 └── _foundational_fallback(papers)        # 离线/失败回退

CitationFinder                             # 奠基论文的「网络层 + 排序层」
 ├── resolve_paper_id(paper)               # 标题匹配 → DOI 兜底，带缓存
 ├── fetch_references(paper_id)            # S2 references API
 ├── collect_raw_references(papers)        # 【网络层】聚合 (源下标, 参考)
 └── rank_references(raw, hotspot_titles)  # 【纯函数】排序+格式化
```

### 数据流

```
List[Paper] (paper_filter 输出)
    ↓ analyze_papers              ← 每篇：研究内容/创新点/结论/应用
    ↓ format_citations            ← APA 7th（委托 utils）
    ↓
（按热点分组后，逐热点调用：）
    ↓ generate_overall_analysis   ← 共同主题/方法演进/代表作/发展阶段
    ↓ find_foundational_papers    ← CitationFinder.collect_raw_references (S2 API)
                                     → rank_references（被热点引用数↓ > 全球引用↓ > 年份↑）
                                     ↓ 失败/空/限流
                                     → _foundational_fallback（诚实标注，不编造）
```

---

## 实现细节

### 1. 单篇信息提取（规则版，非 LLM）

四个提取器都基于**摘要信号词匹配**，确定性、可单测；LLM 深度提取留作未来增强。

| 提取器 | 方法 | 逻辑 |
|--------|------|------|
| 核心研究内容 | `_extract_research_content` | 摘要前 200 字 + `...`；空摘要给「暂无」 |
| 创新点 | `_extract_innovations` | 匹配 `INNOVATION_PATTERNS`（novel/outperform/first/propose…）→ 中文标签；无命中给默认「提出新的研究方法」 |
| 核心结论 | `_extract_conclusions` | 找首个含 `CONCLUSION_MARKERS`（show/demonstrate/achieve…）的句子 |
| 应用场景 | `_infer_application` | `APPLICATION_KEYWORDS`（医疗/金融/自动驾驶/NLP/CV/推荐/科学发现）领域命中；无命中给「通用研究」 |

> `_analyze_single_paper` **幂等**：若 `research_content` 与 `innovations` 均已存在则跳过，不覆盖已有深度分析结果（例如未来由 LLM 回填的字段）。

### 2. APA 7th 引用 `format_citations`

直接委托 `utils.format_apa_citation`：`Author, & Author (Year). Title. *Venue* [+ DOI]`。作者 >3 人时取前 3 + `...`。

### 3. 方向级整体分析 `generate_overall_analysis`（Option B 迁入）

按 [报告格式设计.md](../../报告格式设计.md) §5.3，综合「共同主题、方法演进、各论文贡献对比、发展阶段」。规则版（非 LLM），所有结论落在真实论文上：

1. **共同主题**：聚合热点内 `keywords`，取频次 top 3。
2. **方法演进**：按 `year` 排序，计算年份跨度 `span = max(year) - min(year)`。
3. **代表性贡献**：取 `citation_count` 最高的论文（标题前 40 字 + 年份 + 引用）。
4. **发展阶段**（由跨度判定，避免空泛）：
   - `span ≥ 4` → 「已进入相对成熟、持续演进阶段」
   - `2 ≤ span < 4` → 「处于快速活跃发展期」
   - `span < 2` → 「属新兴/近期热点方向」

输出形如：
> 本热点 2 篇论文围绕「扩散模型」展开，共同关注 diffusion、sampling 等主题；代表性工作《Consistency-Model…》（2023，引用 250）贡献突出，方法从 2023 年到 2024 年逐步演进，整体属新兴/近期热点方向。

### 4. 奠基性参考论文查找（Option B 迁入 + 实装真实 API）

这是 Option B 的核心交付：把原本在 report_generator 里**返回占位符**的 `_find_foundational_papers`，升级为**真正调用 Semantic Scholar references API**。

#### 4.1 算法思路（报告格式设计.md §5.4）

> 「优先选择高被引、**被本热点论文广泛引用**的经典工作。」

对热点内的每篇论文，取它的**参考文献**（references，即它引用了谁）；跨论文聚合后，**「被本热点越多论文引用 + 全球引用越高 + 年份越早」**的参考，就越可能是该方向的奠基性经典。

#### 4.2 CitationFinder：网络层 + 排序层分离

| 层 | 方法 | 职责 | 可测性 |
|----|------|------|--------|
| 网络层 | `collect_raw_references` | 解析 paperId → 取 references → 返回 `(源下标, Reference)` 列表 | 测试用 monkeypatch 替换 |
| 排序层 | `rank_references` | 聚合/去重/排序/格式化 | **纯函数，直接单测** |

这种分离让排序逻辑无需联网即可充分测试。

#### 4.3 Semantic Scholar API 细节

| 步骤 | 端点 | 字段 |
|------|------|------|
| 解析 paperId（标题匹配） | `GET /paper/search/match?query={title}` | `paperId,title` |
| 解析 paperId（DOI 兜底） | `GET /paper/DOI:{doi}` | `paperId` |
| 取参考文献 | `GET /paper/{paper_id}/references?limit=100` | `title,authors,year,citationCount,externalIds` + `isInfluential` |

- **限流**：每次请求前 `rate_limiter.wait_if_needed('semantic_scholar')`，达限即跳过（与 `paper_search.SemanticScholarSearcher` 一致）。
- **paperId 缓存**：`_id_cache` 避免重复解析同一论文。
- **请求数封顶**：`max_papers_to_probe=5`，热点再大也只探查前 5 篇的参考文献，避免请求爆炸。
- **响应兼容**：references 端点把被引论文嵌套在 `citedPaper`；代码防御性兼容 `citedPaper` / `citingPaper` / `paper` / 扁平四种形态。

#### 4.4 排序键 `rank_references`（纯函数）

```
聚合：paper_id（或规范化标题）→ (Reference, 引用它的源下标集合)
过滤：剔除热点自身成员（norm_title ∈ hotspot_titles）
排序：(被本热点引用的源论文数 ↓, 全球引用量 ↓, 年份 ↑)
格式：「Author 等 (Year): Title —— 被本热点 N 篇引用，全球引用 X（高影响力引用）」
```

#### 4.5 排序示例

热点 2 篇论文（P0、P1），各自参考文献聚合后：

| 参考 | 被热点引用源数 | 全球引用 | 年份 | 排名 |
|------|----------------|----------|------|------|
| DDPM (Ho 2020) | 2（P0+P1 都引） | 9000 | 2020 | 🥇 1 |
| Score-SDE (Song 2021) | 2 | 5000 | 2021 | 🥈 2（同被引数，全球引用低） |
| Some Survey | 1（仅 P0） | 200 | 2018 | 🥉 3 |

#### 4.6 优雅降级（绝不编造引用）

`find_foundational_papers` 的降级链：

```
collect_raw_references (联网)
  ├─ 有结果 → rank_references → 返回（理想路径）
  ├─ 返回空  ┐
  ├─ 抛异常  ┼→ _foundational_fallback
  └─ 限流跳过┘     → 基于本热点最早+较高被引论文，标注「（离线回退）」
                   → 明确提示「完整奠基性工作需联网经 S2 引用 API 补全」
```

> **设计原则**：宁可诚实地给一条「离线回退」线索，也**不编造**看似真实但虚构的引用。这与报告格式设计.md「可追溯」目标一致。

---

## 配置依赖

### 环境变量

| 变量 | 用途 | 必需/可选 |
|------|------|----------|
| `SEMANTIC_SCHOLAR_API_KEY` | 提升奠基论文查找的限流额度 | 可选（无 key 也能用，仅额度低） |

### 模块依赖

```python
from utils import Paper, format_apa_citation       # 数据模型 + APA
from config_manager import get_config_manager      # API key
from rate_limiter import get_rate_limiter          # S2 限流
import requests                                     # HTTP
```

---

## 测试

### 单元测试（`test/test_paper_analyzer.py`，28 项全通过）

| 测试类 | 数量 | 覆盖点 |
|--------|------|--------|
| `TestExtraction` | 10 | 研究内容截断/空、创新点命中/默认、结论命中/空、应用推断/默认、幂等跳过、批量 |
| `TestFormatCitations` | 2 | APA 含作者/年份/DOI、批量 |
| `TestOverallAnalysis` | 5 | 主题+篇数+代表作、空、成熟阶段、新兴阶段、共同关键词 |
| `TestRankReferences` | 5 | 被热点引用数排序、排除热点成员、格式化含引用说明、年份 tie-break、空 |
| `TestFoundationalPapers` | 5 | API 有结果、空→回退、异常→回退、空输入、回退选最早 |
| `TestIntegration` | 1 | 提取→整体分析→奠基（离线）端到端 |

### 运行

```bash
python -m pytest test/test_paper_analyzer.py -v
python -m paper_analyzer    # 模块自检（会尝试真实 S2 API，失败自动回退）
```

测试用 `FakeRateLimiter` + monkeypatch `collect_raw_references`，**不依赖网络与配置文件**。

---

## 已知限制与未来改进

1. **提取为规则版**：创新点/结论靠信号词，精度有限；完整版接 LLM 做结构化提取（`_analyze_single_paper` 已支持「已有结果则跳过」，便于 LLM 回填）。
2. **整体分析为规则版**：发展阶段用年份跨度启发式；LLM 可生成更细腻的方向性综合（共同主题、方法分歧）。
3. **奠基论文仅用 Semantic Scholar**：未用 OpenAlex 的 `referenced_works`。S2 覆盖足够时可满足；未来可加 OpenAlex 作双源兜底。
4. **paperId 解析依赖标题/DOI**：极少数标题歧义可能解析错；已用 `_match_by_title` 取最佳匹配 + 缓存。
5. **探查数封顶 5**：超大热点只取前 5 篇的参考文献以控请求数；可按需调 `max_papers_to_probe`。

---

## 与规范/计划的对应

| 规范要求（报告格式设计.md §9 映射） | 实现位置 |
|------|------|
| 整体分析（方向级综合） | `paper_analyzer.py::generate_overall_analysis` ✅ |
| 奠基性参考论文查找 | `paper_analyzer.py::find_foundational_papers` + `CitationFinder`（真实 S2 references API）✅ |
| APA 7th 引用 | `paper_analyzer.py::format_citations`（委托 utils）✅ |
| 核心研究内容/创新点/结论/应用 | `paper_analyzer.py::_extract_*` / `_infer_application` ✅ |

> **Option B 迁移完成**：报告格式映射表里「热点介绍」归 `paper_filter`（已实现），「整体分析 + 奠基性参考」归 `paper_analyzer`（本模块）。`report_generator`（模块5）创建时应调用 `analyzer.generate_overall_analysis(...)` 与 `analyzer.find_foundational_papers(...)`，不再自带这两个方法。

---

**最后更新**: 2026-07-11
**维护者**: Agent Scholar Team
