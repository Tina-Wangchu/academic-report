# Abstract 质量改进计划 / Abstract Improvement Plan

> **实现状态（2026-07-13 更新）**：Phase 1（S2 TL;DR 回退）+ Phase 2（完整去填充摘要）已实现。**Phase 3（LLM 生成式）已以「四要素 LLM 分析」的形式落地**——`llm_analyzer.py`（智谱 GLM，Anthropic 兼容端点）对**全部四要素**（含摘要语义）做生成式综合，LLM→规则分层回退 + 缓存；详见 [four_element_llm_plan.md](four_element_llm_plan.md)。本文件原「单摘要 LLM」思路已被四要素方案涵盖。
>
> **2026-07-12 调整**：Abstract 目标长度从「150-200 字短抽取式浓缩」改为「**200-300 字完整去填充摘要**」——常规摘要（≤1500 字符）原样全文，仅超长才剔填充句；单篇块不再单列研究内容/创新点/核心结论（已并入 Abstract）。下方「150-200 字」字样为早期计划原文，实际实现以 200-300 字为准。
>
> 当前 Abstract 为规则版抽取式浓缩（背景+方法+结果子句拼接），概括草率、难以有效涵盖学术研究成果。本计划设计**专业、学术、智能**的论文概括方案，引入工具（S2 TL;DR、LLM）与分层降级，给出架构、分阶段实现与验收标准。
>
> The current Abstract is a rule-based extractive condensation (background+method+result clauses), which is crude and fails to cover academic achievements. This plan designs a professional, academic, intelligent summarization approach, introducing tools (S2 TL;DR, LLM) with tiered fallback, plus architecture, phased implementation, and acceptance criteria.

---

## 1. 现状与不足 / Current State & Gaps

**现状**：`paper_analyzer._condense_abstract`（见 [abstract_problem.md](abstract_problem.md)）——
- 抽取式：取「背景句(首句) + 方法子句(we propose…) + 结果子句(demonstrate/outperform…)」拼接。
- 短摘要全文、长摘要截到句边界，无 `...`。

**不足**：
1. **抽取式，非生成式**：只能从原文摘句子，无法重写/综合/精炼，措辞生硬。
2. **覆盖不全**：常遗漏「研究问题、数据集、评测指标、核心贡献、局限」等学术要素；只抓方法+结果。
3. **单句摘要退化**：单句长摘要只能整段返回或截断，无真正浓缩。
4. **不专业**：拼出的句子缺乏学术综述语感，像剪报而非学术概括。
5. **无语义理解**：纯关键词/句式匹配，无法判断哪句是真正贡献。

**实测样本**（E1）：`「生成模型」(2 篇): We show that small forward-marginal error does not guarantee numerical stability` —— 只是一个结果子句，未交代问题、方法、贡献。

---

## 2. 目标 / Goals

- **专业学术**：每篇 Abstract 是一段 **200-300 字**的学术概括，覆盖「问题 → 方法 → 贡献/结果」。
- **智能**：能识别论文核心成就，而非机械摘句。
- **稳健**：工具/LLM 不可用时优雅降级，永不崩溃、不编造。
- **可控成本**：默认走免费/低成本路径，LLM 为可选增强。
- **可评测**：能在 12 场景报告上对比质量。

---

## 3. 改进方案选项 / Options

| 方案 | 做法 | 质量 | 成本/依赖 | 离线可用 |
|------|------|------|-----------|----------|
| **A. S2 TL;DR** | S2 API 的 `tldr` 字段（S2 自动生成的学术 TL;DR） | 中-高 | 免费（复用 S2 API） | 否（需 S2） |
| **B. LLM 生成式摘要** | 调 LLM（Claude 等）按学术 prompt 生成 150-200 字概括 | 高 | API key + 费用 + 延迟 | 否 |
| **C. 增强结构化抽取** | 规则抽取 问题/方法/数据集/指标/结果/贡献，模板拼接 | 中 | 无 | 是 |
| **D. 分层混合（推荐）** | A → B → C 逐级回退 | 高（可用时）/ 中（离线） | 分层 | 是（C 兜底） |

**推荐 D（分层混合）**：尽量用最好质量，不可用则逐级降级，离线也有保底。

---

## 4. 推荐方案：分层混合 / Tiered Hybrid

```
AbstractSummarizer.summarize(paper)
  ├─ Tier 1: paper.tldr（S2 TL;DR）非空 → 直接用（已是学术概括）        ✅ 免费、高质量
  ├─ Tier 2: LLM 配置可用 → LLM 生成式摘要（学术 prompt）                ✅ 最佳质量
  └─ Tier 3: 增强结构化抽取（规则）                                      ✅ 离线保底
```

- **Tier 1（S2 TL;DR）**：在 `SemanticScholarSearcher` 的 fields 加 `tldr`，存入 `Paper.tldr`；摘要器优先用它。S2 的 tldr 是其模型生成的学术一句话/短概括，质量较高且免费。
- **Tier 2（LLM）**：可选；配置 `LLM_API_KEY` 后启用。用学术 prompt 生成 150-200 字概括，覆盖问题/方法/贡献/结果。带缓存（按 paperId/DOI+title）避免重复调用。
- **Tier 3（增强规则）**：改进 `_condense_abstract` 为结构化抽取（问题句 + 方法 + 数据集/指标 + 结果 + 贡献），模板拼接，离线保底。

---

## 5. 架构设计 / Architecture

```
paper_analyzer.py
 └── AbstractSummarizer（新）
      ├── summarize(paper) -> str          # 分层调度
      ├── _from_tldr(paper)                 # Tier 1
      ├── _from_llm(paper)                  # Tier 2
      └── _from_rules(paper)                # Tier 3（增强版 _condense_abstract）

llm_summarizer.py（新，可选）
 ├── LLMProvider 接口（summarize(text, prompt) -> str）
 ├── AnthropicProvider（默认，anthropic SDK）
 └── 缓存（~/.hermes/llm_cache.json，按 paper 哈希）

paper_search.py
 └── SemanticScholarSearcher: fields 加 'tldr'；_convert_to_paper 存 paper.tldr

utils.Paper: 新增 tldr: str = "" 字段
config_manager: 新增 get_llm_config()（LLM_PROVIDER/API_KEY/MODEL）
report_generator: Abstract 段不变（仍读 paper.condensed_abstract，由 summarize 填充）
```

**LLM Prompt 模板**（学术概括）：
```
你是学术综述助手。基于以下论文标题与摘要，用 200-300 字、学术语气概括其：
(1) 研究问题；(2) 提出方法；(3) 核心贡献；(4) 主要结果/指标。
不要罗列原文句子，要综合重写；不要编造未提及的内容。
标题：{title}
摘要：{abstract}
```

---

## 6. 实现阶段 / Phased Implementation

### Phase 1：S2 TL;DR 接入（低成本、高回报）
- `SemanticScholarSearcher` fields 加 `tldr`；`_convert_to_paper` 解析 `tldr.text` → `paper.tldr`。
- `Paper` 加 `tldr` 字段。
- `AbstractSummarizer.summarize`：`paper.tldr` 非空即用（可按 150-200 字裁剪）。
- **验收**：S2 命中的论文 Abstract 质量明显提升（S2 429 时回退 Tier 3）。

### Phase 2：完整去填充摘要（离线保底升级，2026-07-12 改）
- `_from_rules` 改为**完整去填充**：常规摘要（≤1500 字符）原样全文；超长才按句信息量打分剔除低分填充句（保留首句=问题与末句=结论），维持原序，目标 **200-300 字**、句边界、无 `...`。
- **验收**：离线场景 Abstract 为 200-300 字完整摘要，覆盖问题/方法/数据集/结果/贡献。

### Phase 3：LLM 生成式摘要（最佳质量，可选）
- 新增 `llm_summarizer.py` + `AnthropicProvider`（默认 claude-haiku-5 兼顾速度/成本，可配 sonnet 提质）。
- `config_manager.get_llm_config()`；`~/.hermes/.env` 加 `LLM_API_KEY`/`LLM_MODEL`。
- `_from_llm`：调 LLM、超时/异常回退 Tier 3、带缓存。
- **验收**：配置 LLM 后 Abstract 为专业学术段落，覆盖问题/方法/贡献/结果。

### Phase 4：评测与调优
- 在 12 场景报告上对比 Tier 1/2/3 的 Abstract 质量（人工评审 + 覆盖要素计数）。
- 调 prompt / 长度 / 触发条件。
- **验收**：LLM 层覆盖四要素 ≥90%，TL;DR 层 ≥70%，规则层 ≥50%。

---

## 7. 工具与依赖 / Tools & Dependencies

| 依赖 | 用途 | 必需/可选 | 安装 |
|------|------|-----------|------|
| S2 API `tldr` 字段 | Tier 1 | 必需（Phase 1） | 无（复用现有） |
| `anthropic` SDK | Tier 2 LLM | 可选（Phase 3） | `pip install anthropic` |
| `LLM_API_KEY` | Tier 2 认证 | 可选 | `~/.hermes/.env` |
| 缓存（stdlib json） | Tier 2 去重 | 可选 | 无 |

> 注：本项目运行于 Hermes Agent 上下文，未来也可由 Agent 直接提供 LLM 调用（无需独立 API key）；Phase 3 先用独立 anthropic SDK，后续可换为 Hermes LLM 接口。

---

## 8. 测试与评估 / Testing & Evaluation

- **单元测试**：
  - `_from_tldr`：有/无 tldr 的处理。
  - `_from_rules`：结构化抽取覆盖各要素。
  - `_from_llm`：mock provider（不联网），验证调用 + 异常回退。
  - `summarize` 分层调度：Tier 1 命中不调 Tier 2/3；Tier 2 异常回退 Tier 3。
- **集成评测**：12 场景报告，记录每篇 Abstract 走的 Tier + 字数 + 要素覆盖（问题/方法/贡献/结果 各 0/1）。
- **回归**：现有 `_condense_abstract` 测试改为 `_from_rules`，新增分层测试。

---

## 9. 风险与降级 / Risks & Fallback

| 风险 | 处理 |
|------|------|
| S2 429/无 tldr | 回退 Tier 2/3 |
| LLM 超时/异常/未配置 | 回退 Tier 3（规则） |
| LLM 编造内容 | prompt 约束「不要编造」+ 仅基于给定摘要 |
| LLM 成本 | 缓存 + 默认 haiku + 仅对无 tldr 的论文调用 |
| 延迟 | 每热点最多 N 篇走 LLM；可异步/并发 |
| 非确定性 | 缓存结果；设置 temperature=0 |

---

## 10. 验收标准 / Acceptance Criteria

1. **分层生效**：有 tldr 用 tldr；无 tldr 有 LLM 用 LLM；都无用规则——三路均不崩溃。
2. **质量**：LLM 层 Abstract 为 200-300 字学术段落，覆盖问题/方法/贡献/结果 ≥90%。
3. **离线保底**：无 tldr 无 LLM 时，规则层比当前 `_condense_abstract` 多覆盖「数据集/指标/贡献」要素。
4. **无 `...` 截断**：三层均不出现 mid-sentence 省略号（句边界或自然结尾）。
5. **测试**：分层调度 + 各层 + mock LLM 全通过；12 场景报告 Abstract 字数/要素统计产出。
6. **文档**：更新 [abstract_problem.md](abstract_problem.md) → 标注已实现分层；同步 [报告格式设计.md](报告格式设计.md) §10.1 与 implementation_detail。

---

## 11. 工作量估计 / Effort

| 阶段 | 估时 | 产出 |
|------|------|------|
| Phase 1（S2 tldr） | 1-2h | tldr 接入 + Tier 1 + 测试 |
| Phase 2（增强规则） | 2-3h | 结构化抽取 + 测试 |
| Phase 3（LLM） | 3-4h | llm_summarizer + provider + 缓存 + 测试 |
| Phase 4（评测） | 1-2h | 12 场景对比 + 调优 |
| **合计** | **7-11h** | 可按阶段交付，Phase 1 即有可见提升 |

> 建议先做 Phase 1+2（无新依赖、立竿见影），Phase 3 视是否有 LLM API key 再定。
