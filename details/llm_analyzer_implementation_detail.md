# llm_analyzer.py - Implementation Detail

## 模块概述

**模块名称**: 四要素 LLM 生成式分析（llm_analyzer.py）— 单篇深度分析增强
**版本**: 1.1.0（Phase 1 + 语言控制）
**完成日期**: 2026-07-13（Phase 1）；2026-07-22（v1.1.0 四要素按 `intent.language` 切换语种）
**状态**: ✅ 已完成（32 项 mock 单测 + 真实智谱 GLM 烟雾验证）

---

## 功能说明

把单篇论文四要素（解决的问题 / 已有方案 / 新方案 / 效果及局限）从**规则抽取式**升级为 **LLM 生成式综合**，达到参考报告 `ai_report_20260705.pdf` 的专业深度。

- 🧠 **ZhipuProvider**：走智谱 GLM 的 **Anthropic 兼容端点**（`https://open.bigmodel.cn/api/anthropic`），复用 `ANTHROPIC_AUTH_TOKEN`，用 `requests` 直发 Messages API（**零新依赖、零额外 key**）。
- 🪜 **FourElementAnalyzer 分层**：LLM 生成式（主）→ `StructuredExtractor` 规则（回退）；绝不崩溃、绝不编造。
- 💾 **缓存**：`~/.hermes/llm_cache_four_element.json`，按 `sha1(doi|title|language)` + `temperature=0`，稳定可复现、控成本。**language 纳入 key**——同论文的 zh/en/bilingual 分析互不串用缓存。
- 🧩 **不改 schema**：仍填 `paper.problem/existing_approaches/new_approach/results_limitations`（+ `analysis_source` 标注 llm/rule/cache）。
- 🌐 **语言控制（v1.1.0，修复点）**：四要素 prompt 由 `_system_prompt(language)` 按 `intent.language` 构造——`zh`=纯中文、`en`=纯英文、`bilingual`(默认)=**每个要素先中文段、换行后英文段**（内容对应一致）。旧版 prompt 硬编码中文、无视 language，导致双语报告的四要素恒为中文；现已修复。`paper_analyzer._analyze_single_paper(paper, lang)` 把 `lang` 透传给 `FourElementAnalyzer().analyze(paper, language=lang)`。摘要仍按论文原语种（英文原文，学术惯例，Option B 取舍）。

---

## 架构

```
paper_analyzer._analyze_single_paper
  └─ FourElementAnalyzer().analyze(paper) -> dict(4 要素 + analysis_source)
       ├─ Tier 1: ZhipuProvider.summarize(SYSTEM_PROMPT, 标题+摘要) → JSON 解析   [主]
       │     ├─ 解析：JSON / 代码围栏 / 标签段落（_label_parse 兜底）
       │     └─ 缓存命中 → 直接返回（source=cache）
       └─ Tier 2: StructuredExtractor.extract(paper)                              [回退]

ZhipuProvider: POST {base_url}/v1/messages
  headers: x-api-key + Authorization: Bearer + anthropic-version
  body: {model, max_tokens, temperature:0, system, messages:[{user}]}
  resp: data["content"][0]["text"]  (Anthropic Messages 格式)
```

---

## 配置（`config_manager.get_llm_config()`）

| 项 | 来源（优先级） | 默认 |
|----|----------------|------|
| enabled | `LLM_ENABLED` env > config > 有 key 即 true | 有 `ANTHROPIC_AUTH_TOKEN` 则 true |
| api_key | `LLM_API_KEY` > `ANTHROPIC_AUTH_TOKEN` > `ZHIPU_API_KEY` > config | — |
| base_url | `LLM_BASE_URL` > `ANTHROPIC_BASE_URL` > config | `https://open.bigmodel.cn/api/anthropic` |
| model | `LLM_MODEL` > config | `glm-5-turbo`（可换 `glm-5.1` 提质） |
| provider | `LLM_PROVIDER` > config | `zhipu` |

> 关闭：`LLM_ENABLED=false`（直走规则，行为与升级前一致，零风险）。

---

## Prompt 要点（学术综述助手）

- 四要素：problem（综合改写）/ existing（对比 1-3 类既有方法+不足）/ new（多组件用 1.2.3. 编号）/ results（量化+「约束：…」）。
- 硬约束：仅基于给定文本、不编造、未涉及写「（未明确提及）」、保留术语、≤350 字、**输出严格 JSON 四键**。
- `temperature=0`。

---

## 真实烟雾产出（KRCA 论文，glm-5-turbo）

- problem：综合改写「极端动态性与海量规模…兼顾实时性与因果推理准确性」
- existing：编号对比 Deep learning（重训练耗时）+ LLM（Lost-in-the-Middle/hallucination）
- new：编号三组件（API drilldown / 因果骨架 / memory-augmented multi-agent）
- results：量化（AC@1 0.88/0.79、+31%、6 月、77.3%）+ 具名约束（依赖依赖图完整性、受 LLM 延迟限制）

→ 与参考报告同深度；规则版做不到的「综合+编号+量化+具名约束」均达成。

---

## 测试（`test/test_llm_analyzer.py`，32 项，全 mock 不联网）

- ZhipuProvider 请求构造（URL/auth headers/model/temperature=0/messages）、HTTP 错误抛异常。
- FourElementAnalyzer：合法 JSON / 代码围栏 / 标签文本 / 垃圾回退规则 / 异常回退规则 / 无 provider 走规则。
- 缓存：命中跳过 provider、`use_cache=False` 重调、key 确定性。
- **语言控制（`TestLanguageControl`，9 项）**：zh/en/bilingual prompt 各自含正确语种指令、非法值默认 bilingual、`analyze(language=)` 把对应 prompt 传给 provider、默认 bilingual、**同论文不同语言各自调 LLM（key 不同）**、同语言命中缓存。
- config：读 env + 默认端点、无 key 时 disabled。

---

## 已知限制 / Phase 2-4

1. **仅摘要输入 → 已支持全文兜底（Phase 2）**：无摘要时**强制**抓开放全文（`paper.pdf_url`→arXiv→Unpaywall 级联；PDF 用 fitz、HTML 去标签）喂 LLM，从正文生成四要素。实测「Attention Is All You Need」（摘要留空）成功。极少数「无摘要+闭源」论文（如 CheckM2）仍抓不到合法全文 → 诚实留空。
2. **成本/延迟**：每篇一次 LLM 调用；已缓存去重。大批量可并发（Phase 4）。
3. **编造风险**：prompt 约束 + temperature=0 + 抽检；目前未做自动事实核查。
4. **评测**：Phase 3 在 12 场景上做规则 vs LLM 的 A/B 指标（编号率/量化率/具名约束率/人工评分）。

---

**最后更新**: 2026-07-13
