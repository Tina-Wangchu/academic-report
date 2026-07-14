# Abstract 字段问题分析与修复 / Abstract Field: Analysis & Fix

> **实现状态（2026-07-12）**：Phase 1（S2 TL;DR 回退）+ Phase 2（完整去填充摘要，目标 200-300 字）已实现并测试通过；Phase 3（LLM 生成式摘要）按用户决定暂不做，留待有 LLM API key 时再启。详见 [abstract_improvement.md](abstract_improvement.md)。
>
> **2026-07-12 调整**：Abstract 目标从「短抽取式浓缩（~100-200 字）」改为「**完整去填充摘要（200-300 字）**」；单篇块不再单列研究内容/创新点/核心结论（并入 Abstract）。
>
> **2026-07-13 进一步调整**：单篇块的「Abstract 段」升级为**四要素摘录**（解决的问题 / 现有方案 / 新方案 / 效果及局限），由 `paper_analyzer.StructuredExtractor` 从摘要按句匹配信号词摘录。`condensed_abstract`（完整去填充摘要）仍保留，供速览与「四要素全空」时回退使用。本文档描述的 Abstract 生成逻辑仍然适用（作为四要素全空的回退与速览的数据源）。
>
> 端到端实验（`test/experiments/`）暴露的报告 Abstract 字段两大问题，及其根因、难点与修复方案。
>
> Two problems of the report's Abstract field surfaced by end-to-end experiments, with root causes, difficulties, and fixes.

---

## 1. 现象 / Symptoms

1. **Abstract 普遍缺失**：E6 热点一 8 篇论文全部「（暂无摘要）」；跨场景统计 arXiv 10/10 有摘要、**OpenAlex 0/10 有摘要**。
   Abstracts mostly missing: arXiv 10/10 have abstracts, **OpenAlex 0/10**.
2. **Abstract 含省略号、非浓缩**：有摘要的论文，Abstract 是原文硬截断（`... `），并非「系统分析后生成的完整浓缩」。
   When present, Abstract is a hard truncation with `...`, not a condensation after analysis.

---

## 2. 根因 / Root Causes

### 2.1 缺失：OpenAlex 摘要字段未被解析

- OpenAlex `/works` 接口**不返回** `abstract` 字符串字段，而是返回 `abstract_inverted_index`（词 → 位置列表的倒排索引）。
  OpenAlex does **not** return a plain `abstract`; it returns `abstract_inverted_index` (word → positions).
- `OpenAlexSearcher._convert_to_paper` 原写 `abstract = item.get('abstract', '')` → 永远为空。
  The converter read `item.get('abstract')` → always empty.
- 实测：`search=transformer neural network` 时 9/10 结果有非空 `abstract_inverted_index`；近期(2026)论文可能为 `None`（OpenAlex 尚未索引摘要，属数据源固有缺失）。
  Verified: 9/10 have a non-empty inverted index; very recent papers may be `None` (source-level gap).

### 2.2 省略号：硬截断而非浓缩

- `_render_paper` 对 `paper.abstract` 做 `[:1500] + "..."`，超长即出现省略号。
  Hard truncation at 1500 chars produces `...`.
- 报告格式设计.md §5.2 要求「150-200 字浓缩该论文中心成果」——**浓缩**，不是截断。截断既不「完整」（被切断），也不「浓缩」（只是砍掉尾部）。
  The spec requires a **condensation**, not a truncation. Truncation is neither complete nor condensed.

---

## 3. 难点 / Difficulties

1. **真正的「浓缩」需要 LLM**：把一篇 1500 字摘要浓缩成 150-200 字的「中心成果」，本质是摘要式生成（abstractive summarization），规则方法做不到语义级浓缩。
   True condensation needs LLM (abstractive summarization); rules can't do semantic condensation.
2. **规则方法只能做抽取式（extractive）**：可挑选「方法句 + 结果句」等关键句拼接，覆盖论文核心，但可能偏长或遗漏，且与 research_content/conclusions 字段存在部分重叠。
   Rule-based can only do extractive: pick method/result sentences. May be long, may overlap with research_content/conclusions.
3. **多源摘要异构**：arXiv 给纯文本、OpenAlex 给倒排索引、S2 给纯文本（但本环境 429）。需在搜索层统一规整成纯文本。
   Heterogeneous abstract formats across sources must be normalized at the search layer.
4. **数据源固有缺失**：即使正确解析，极新或小众论文 OpenAlex 也可能无摘要——只能占位，不能编造。
   Even with correct parsing, some papers genuinely lack abstracts; must placeholder, not fabricate.

---

## 4. 修复方案 / Fix

### 4.1 搜索层：重建 OpenAlex 摘要（`paper_search.py`）

新增 `_reconstruct_abstract(item)`：把 `abstract_inverted_index` 按 position 排序拼接为纯文本；`None`/空则返回 `""`。`_convert_to_paper` 改用它。

### 4.2 分析层：完整去填充摘要（`paper_analyzer.py`，2026-07-12 改）

`AbstractSummarizer.summarize(paper)` 生成 `paper.condensed_abstract`（目标 **200-300 字** ≈ 1500 字符）：
- 无摘要 → 回退 S2 `tldr`；均无 → `""`（报告走占位）；
- 有摘要且 ≤ 1500 字符 → **直接全文**（已是 200-300 字量级的完整摘要，无省略号）；
- 摘要 > 1500 字符 → 按信息量给句子打分（方法/结果 > 数据集/贡献），**剔除低分填充句**（保留首句=问题与末句=结论），维持原序，覆盖问题/方法/数据集/结果/贡献；
- 截到**句边界**，不出现 mid-sentence `...`；源摘要不足 200 字时按原文展示（不编造）。

> 2026-07-12 改动：从「短抽取式浓缩（背景+方法+结果句拼接，~100-200 字）」改为「**完整去填充摘要（200-300 字）**」——单篇块不再单列研究内容/创新点/核心结论，其内容并入完整 Abstract，避免重复。分析层仍内部计算 research_content/conclusions 子句供速览/整体分析复用。

### 4.3 报告层：展示浓缩（`report_generator.py`）

Abstract 段优先显示 `paper.condensed_abstract`，回退到 `paper.abstract`，再回退占位；**移除 `...` 硬截断**。

### 4.4 数据源固有无摘要

保留占位「（暂无摘要 / No abstract available）」——诚实标注，不编造。

---

## 5. 预期效果 / Expected Outcome

- OpenAlex 论文摘要缺失率从 ~100% 降到数据源固有缺失率（通常 <30%）。
- Abstract 不再出现 `...`：常规摘要（≤1500 字符）全文展示，超长摘要为句边界内的去填充版本。
- 每篇 Abstract 落在 **200-300 字**（真实 arXiv/OpenAlex 摘要通常 150-300 词，原样即达标）；源摘要过短时按原文展示，不编造。
- 无摘要的极少数论文仍诚实占位。

> LLM 深度浓缩（真正的语义级改写摘要）留作 Phase 3 未来增强；当前为「完整去填充」规则版，已满足「200-300 字、完整、无省略号、覆盖问题/方法/结果/贡献」。
