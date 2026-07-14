# 四要素 LLM 分析方案 / Four-Element LLM Analysis Plan

> **实现状态（2026-07-13）**：
> - **Phase 1 ✅**：`llm_analyzer.py` 的 `ZhipuProvider`（智谱 GLM 的 Anthropic 兼容端点，复用 `ANTHROPIC_AUTH_TOKEN`，零新依赖）+ `FourElementAnalyzer`（LLM→规则分层 + 缓存）；接入 `paper_analyzer`。20 项 mock 单测。
> - **Phase 2 ✅**：全文增强——多源级联抓开放全文（`paper.pdf_url` → arXiv → Unpaywall(DOI)），PDF 用 `fitz`、HTML 去标签，抽关键章节（方法/结果/局限）喂 LLM；**无摘要时强制走全文**（不放弃），有 OA/arXiv 全文的论文可救回。实测「Attention Is All You Need」（摘要留空）成功从全文生成四要素。极少数「无摘要+闭源付费墙」论文（如 CheckM2，三源无摘要且 is_oa=closed）抓不到合法全文 → **标注** `analysis_source=unavailable` + 检索链接（`doi.org`/Google Scholar），报告显示「⚠️ 无法自动分析，请自行检索原文」，**不再留空四要素**；且此类论文跳过 LLM 调用（不浪费配额、不编造）。
> - **Phase 3 ✅**：评测 `test/experiments/eval_four_element.py`——规则 vs LLM 在 3 篇样本上的 A/B，LLM 在「新方案编号化(0%→67%)、具名约束(0%→100%)、效果量化(33%→67%)、四要素非空(11→12)」全面胜出。
> - **健壮性增强**：`ZhipuProvider` 加 **429/5xx/超时退避重试**（3/8/15/25s）+ **调用间隔**（1.5s），解决 Coding Plan 公平使用限流；实测 6 篇论文全链路 LLM 分析成功并发 Gmail。
> - Phase 4（大批量并发）待做。
>
> 目标：把单篇论文的四要素（解决的问题 / 已有方案 / 新方案 / 效果及局限）从**规则抽取式**升级为**LLM 生成式综合**，达到参考报告 `ai_report_20260705.pdf` 的专业深度。
>
> Goal: upgrade the per-paper four-element analysis from **rule-based extractive** to **LLM generative synthesis**, matching the depth of the reference report. This is a design/plan doc; no code yet.

---

## 1. 背景与动机 / Context

- 参考报告 `ai_report_20260705.pdf` 的每篇分析结构正是 `[解决的问题][现有方案][本文新方案][新方案的效果及约束]`——**与我们 `StructuredExtractor` 的四要素同构**。
- 但参考报告是**生成式（abstractive）**：读完整篇后用分析者语言**重写**；我们当前是**抽取式（extractive）**：按信号词挑原句（`paper_analyzer.StructuredExtractor`）。
- 实测同一篇（KRCA）对比见下表——差距是结构性的，非调参能跨越。本方案即 `abstract_improvement.md` Phase 3「LLM 生成式」向**全部四要素**的泛化。

### 1.1 差距实证（KRCA 论文）

| 要素 | 参考报告（生成式） | 当前（抽取式） |
|---|---|---|
| 解决的问题 | 综合改写，点出「极端动态性/海量规模」本质 | 原句摘录 |
| 已有方案 | 对比 2 类方法 + 各自失败模式（重训/Lost-in-the-Middle） | 首个含 `prior` 的单句 |
| 新方案 | 编号化架构分解 1./2./3.（drilldown/因果骨架/多智能体） | 首个含 `we propose` 的单句 |
| 效果及局限 | 量化（AC@1 0.88/0.79、+31%、部署 6 月）+ 具名约束 | 首个含 `outperform` 的单句（常无数字） |

---

## 2. 目标质量 / Target Quality

LLM 生成的四要素须满足（对齐参考报告）：

1. **综合而非照搬**——用分析者语言重写，融合全篇。
2. **新方案结构化**——多组件方法用编号（1. 2. 3.）拆解架构。
3. **效果量化**——优先纳入指标/百分比/数据集/部署证据。
4. **局限具名**——具体约束（依赖 X、在 Y 场景可扩展性未验证），非空话。
5. **已有方案多路对比**——并列 1-3 类既有方法及其各自不足。
6. **术语精确**——保留论文的关键技术术语。
7. **不编造**——仅基于给定文本；给不出的要素显式留空/标注。

---

## 3. 架构设计 / Architecture

新增 `scripts/llm_analyzer.py`；`paper_analyzer` 的四要素填充分层调度；复用现有四字段与 `StructuredExtractor` 作回退。**不改报告 schema**（仍是 `paper.problem/existing_approaches/new_approach/results_limitations`）。

```
paper_analyzer._analyze_single_paper(paper)
  └─ FourElementAnalyzer().analyze(paper, lang) -> dict(4 要素)
       ├─ Tier 1: LLM 生成式（配置可用且成功）        ← 新增、主路径
       │     └─ LLMProvider.summarize(prompt, text) -> 结构化文本
       └─ Tier 2: StructuredExtractor.extract(paper)   ← 既有规则、回退（离线/失败/未配置）

llm_analyzer.py（新）
 ├── LLMProvider 接口（summarize(text, system_prompt)->str）
 │    ├── AnthropicProvider（默认；anthropic SDK；claude-haiku-5 兼顾速度成本）
 │    ├── OpenAIProvider（可选）
 │    └── HermesLLMProvider（可选；Hermes Agent 上下文提供的 LLM 接口）
 ├── FourElementAnalyzer（分层调度 + 输出解析 + 缓存命中判断）
 ├── _parse_llm_output(raw) -> dict（容错：JSON / 带标签段落 都能解析）
 └── 缓存（~/.hermes/llm_cache_four_element.json，按 DOI+title 哈希）

config_manager: 新增 get_llm_config()（LLM_PROVIDER / LLM_API_KEY / LLM_MODEL / LLM_ENABLED）
utils.Paper: 复用既有四字段（无 schema 变更）；可选新增 analysis_source: "llm"|"rule" 标注来源
```

**分层不变量**：LLM 不可用/超时/解析失败/未配置 → 静默回退 `StructuredExtractor`；**绝不崩溃、绝不编造、绝不丢字段**。

---

## 4. Prompt 设计 / Prompt

系统 prompt（学术综述助手，强约束输出）：

```
你是学术综述分析师。基于给定论文标题与摘要（及可选全文片段），用学术、客观、凝练的中文
生成四要素分析，用于专业行业报告。严格遵循：

1) 解决的问题：一段，点出论文针对的核心挑战/痛点与本质难点（不要照搬原句，要综合）。
2) 已有方案：对比 1-3 类既有方法/思路，各点出其具体不足或失败模式。
3) 新方案：本文的创新内容；若为多组件方法，用「1. … 2. … 3. …」编号拆解架构。
4) 效果及局限：先给量化结果（指标/百分比/数据集/部署证据，若有），再用「约束：…」给出
   具名局限（如依赖 X、在 Y 场景未验证）。

硬约束：
- 仅基于给定文本，不得编造未提及的数据、方法或结论；某要素文本未涉及则写「（未明确提及）」。
- 术语保留原文关键英文术语；每要素 2-5 句，总量 ≤ 350 字。
- 输出严格 JSON：{"problem":"…","existing":"…","new":"…","results":"…"}，键值均为字符串。

标题：{title}
摘要：{abstract}
{fulltext_section if available}
```

调用参数：`temperature=0`（稳定、可缓存）、`max_tokens≈700`、超时 30s。

> bilingual 报告：先中文生成（默认），可选二次调用译英；或 prompt 直接要求中英并列（成本翻倍，暂不默认）。

---

## 5. 输出解析与回退 / Parsing & Fallback

- 优先按 JSON 解析（`json.loads`，容错：抽取首个 `{...}` 块）。
- JSON 失败 → 降级正则按标签解析（`解决的问题/已有方案/新方案/效果` 段落）。
- 仍失败 / 缺键 / 触发安全拒绝 → 该篇整体回退 `StructuredExtractor`，并在日志记录。
- 长度/空值校验：某要素为空字符串 → 该要素再回退规则值（要素级混合）。

---

## 6. 缓存 / Caching

- 键：`sha1(doi + "|" + title.lower())`（与 `StructuredExtractor` 无关，独立缓存文件）。
- 存储：`~/.hermes/llm_cache_four_element.json`（`{key: {problem, existing, new, results, model, ts}}`），原子写（复用模式）。
- 命中即返回，不重复调用。`temperature=0` 保证可复现。
- 提供 `--refresh` 清缓存（CLI）。

---

## 7. 集成点 / Integration

| 位置 | 改动 |
|------|------|
| `paper_analyzer._analyze_single_paper` | 用 `FourElementAnalyzer().analyze(paper, lang)` 取代直接调 `StructuredExtractor`（内部 LLM→规则分层） |
| `config_manager` | 新增 `get_llm_config()` + `~/.hermes/.env` 读 `LLM_*` |
| `utils.Paper` | 复用四字段；可选加 `analysis_source` 标注（便于评测/调试） |
| `report_generator` | 无改动（字段不变） |
| `pipeline` / `scheduler` | 无改动（透明升级） |

> 开关：`LLM_ENABLED=false` 时直接走规则（默认行为不变），零风险上线。

---

## 8. 全文增强（可选，Phase 2）/ Full-Text Augmentation

- 参考报告的方法细节/具名约束多来自正文。摘要-only 的 LLM 已远超规则法，但全文更佳。
- arXiv 有 PDF：用 `fitz`（已验证可用）下载并抽全文文本，截取「Method/Approach/Results/Limitations」段喂 LLM。
- OpenAlex/S2：用全文链接若开放。无全文 → 仅摘要。
- 成本控制：全文截断（如 ≤ 4000 tokens 关键段），仅对 `max_results` 内高优论文取全文。

---

## 9. 配置与依赖 / Config & Dependencies

| 依赖 | 用途 | 必需/可选 | 安装 |
|------|------|-----------|------|
| `LLM_API_KEY` | LLM 认证 | 必需（启用 LLM 时） | `~/.hermes/.env` |
| `anthropic` SDK | Anthropic provider（默认） | 可选 | `pip install anthropic` |
| `openai` SDK | OpenAI provider | 可选 | `pip install openai` |
| `pymupdf`(fitz) | 全文抽取（Phase 2） | 可选 | `pip install pymupdf` |
| 缓存（stdlib json） | 去重 | 内置 | 无 |

> 不硬加依赖：未安装 SDK / 未配 key → `LLM_ENABLED` 自动 false → 回退规则。Hermes 上下文也可由 Agent 直接提供 LLM 调用（`HermesLLMProvider`），免独立 key。

---

## 10. 评测 / Evaluation

在固定论文集（如 `test/experiments/` 12 场景或自选 10 篇含参考报告同款）上 A/B 对比：

| 指标 | 规则版 | LLM 版 | 目标 |
|------|--------|--------|------|
| 四要素非空率 | 基线 | ↑ | ≥ 95% |
| 新方案含编号组件 | ~0% | ↑ | ≥ 60%（多组件论文） |
| 效果含量化指标 | 低 | ↑ | ≥ 70%（有数据论文） |
| 局限「具名」率 | 低 | ↑ | ≥ 70% |
| 已有方案多路对比 | 低 | ↑ | ≥ 50% |
| 人工评分（1-5，对齐参考） | ~2 | ↑ | ≥ 4 |
| 编造率（事实核查） | 0% | 应 0% | ≤ 2%（prompt 约束+抽检） |

产出 `test/experiments/llm_vs_rule_report.md` 对比报告。

---

## 11. 风险与降级 / Risks & Fallback

| 风险 | 处理 |
|------|------|
| 未配置/无 key | `LLM_ENABLED=false` → 规则回退，行为不变 |
| 超时/限流/异常 | 单篇 try/except → 规则回退；不阻塞批次 |
| LLM 编造 | prompt「不得编造，未涉及写未明确提及」+ temperature=0 + 抽检 |
| 成本 | 缓存 + 默认 haiku 级模型 + 仅对最终入选论文调用 + 全文截断 |
| 延迟 | 单论文串行可控；Phase 3 可并发（按 LLM 限流） |
| 非确定性 | temperature=0 + 缓存 |
| 安全拒绝 | 解析为空 → 回退规则 |

---

## 12. 分阶段实现 / Phased Implementation

| 阶段 | 内容 | 产出 |
|------|------|------|
| **Phase 1：LLM 四要素 + 分层回退** | `llm_analyzer.py`（provider 接口 + Anthropic 默认 + prompt + JSON 解析 + 缓存）+ `FourElementAnalyzer` 分层 + `config_manager.get_llm_config` + `_analyze_single_paper` 接入 + mock 单测 | LLM 可用时四要素达参考深度 ✅ |
| **Phase 2：全文增强** | arXiv PDF→全文（fitz）+ 关键段抽取喂 LLM | 方法/约束细节更全 ✅ |
| **Phase 3：评测与调优** | 12 场景 A/B、指标统计、prompt/长度/触发调优 | 量化达到 §10 目标 ✅ |
| **Phase 4：并发与成本** | 批量并发（按限流）+ 缓存命中率统计 + Hermes provider | 大批量提速 ✅ |

> Phase 1 即有肉眼可见的「专业度」跃迁；无 key 时零影响（回退规则）。

---

## 13. 测试 / Testing

- **mock provider 单测**（不联网）：`FourElementAnalyzer` 命中 LLM→用其输出；LLM 异常/坏 JSON/缺键→回退规则；缓存命中不调 provider；`LLM_ENABLED=false` 直走规则。
- **解析测试**：合法 JSON / 带标签文本 / 截断 JSON / 空响应 各路径。
- **集成（有 key 时）**：真实 LLM 跑 2-3 篇，人工对照参考报告风格。
- **回归**：现有 219 项测试不破；`analysis_source` 标注便于区分来源。

---

## 14. 工作量估计 / Effort

| 阶段 | 估时 |
|------|------|
| Phase 1（provider+prompt+分层+缓存+测试） | 3-4h |
| Phase 2（全文抽取） | 2-3h |
| Phase 3（评测+调优） | 2-3h |
| Phase 4（并发+Hermes provider） | 2-3h |
| **合计** | **9-13h**，可按阶段交付；Phase 1 即质的提升 |

---

## 15. 关键文件（实现时）

- `scripts/llm_analyzer.py`（新；provider + FourElementAnalyzer + 缓存 + CLI）
- `scripts/paper_analyzer.py`（`_analyze_single_paper` 改为分层调度）
- `scripts/config_manager.py`（`get_llm_config`）
- `scripts/utils.py`（可选 `Paper.analysis_source`）
- `test/test_llm_analyzer.py`（新；mock provider）
- 文档同步：本计划 → 标注已实现；`报告格式设计.md` §11 四要素章节补「生成式（LLM）路径」；`abstract_improvement.md` Phase 3 标注泛化至四要素。

---

> **结论**：四要素的质量跃迁 = 抽取式 → 生成式（LLM）。本方案以「LLM 主路径 + 规则回退 + 缓存」零风险上线，Phase 1 即接近参考报告深度；规则法仅作离线兜底。
