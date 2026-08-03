# 已知问题：Semantic Scholar 数据源返回 0 篇

> **状态：暂缓**（2026-08-03 记录）—— 根因已诊断，代码 bug 已修；剩余为环境配置（需免费 API key），按决定暂不处理。

## 现象

`PaperSearcher` 三源并行检索中，Semantic Scholar（S2）返回 0 篇。arXiv 与 OpenAlex 正常（实测各 5 篇）。

## 根因诊断（已用只读诊断坐实）

S2 源有**两个独立问题**，叠加导致 0 篇：

### 问题 1：年份过滤参数畸形 —— ✅ 已修复

- **位置**：`academic-report/scripts/paper_search.py` → `SemanticScholarSearcher._build_year_filter`
- **原 bug**：`start_date` 与 `end_date` 同时存在时，产出 `"2023-,-2026"`（两个半开区间用逗号拼接），S2 API 视为非法参数 → 返回空 / 400。
- **正确格式**：`"2023-2026"`（闭区间）。
- **修复**：改为 `if start and end: f"{start.year}-{end.year}"`；仅 start → `f"{start.year}-"`；仅 end → `f"-{end.year}"`。

### 问题 2：无 API key → 429 限流 —— ⏸️ 暂未解决（需用户配置）

- S2 Graph API **无 key** 时走**全局公共共享配额**，近两年极度拥挤，绝大多数请求返回 `429 Too Many Requests`。
- **诊断实证**：三种 year 参数（畸形 / 正确 / 不带）**全部 429** —— 证明当前根因是缺 key，而非查询构造。
- S2 的"免费 key"是 **per-user 个人申请**（[申请地址](https://www.semanticscholar.org/product/api#api-key-form)，免费、秒批、访问量有限）；**不存在可内置的公共免费 key**。
- 开源 skill **不能硬编码 key**（违反 S2 服务条款 + 个人 key 的有限配额会被所有用户耗尽）—— 必须由用户申请后填入 `config/.env` 的 `SEMANTIC_SCHOLAR_API_KEY`。

## 已做的改进（即使不配 key 也受益）

1. **`_build_year_filter` 修正**（问题 1）—— 配 key 后立即生效，正确返回闭区间。
2. **S2 429 退避重试**：收到 429 时读 `retry-after` 响应头、退避后重试最多 3 次（缓解瞬时限流）。
3. **错误可观测**：`PaperSearcher.search_errors`（dict）聚合各源失败原因；即使日志被静音（如 `logging.disable`），失败原因也会写入 `run_data.json`，**不再表现为无声的"0 篇"**。

## 为什么暂不彻底解决

- S2 只是**三个源之一，非必需**。arXiv + OpenAlex 两源无需 key、已正常工作（实测合计 10 篇，足以生成完整报告）。
- 配 key 属于**用户环境配置**，不属代码范畴；且需用户个人申请。

## 彻底解决步骤（未来需要时）

1. 在 [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api#api-key-form) 申请免费 API key（填表，秒批）。
2. 复制 `academic-report/config/.env.example` → `academic-report/config/.env`（若尚未创建）。
3. 在 `.env` 中填写：`SEMANTIC_SCHOLAR_API_KEY=你的key`
4. 重跑 pipeline —— S2 源应返回论文；`run_data.json` 的 `source_distribution` 出现 `semantic_scholar`，`search_errors` 不再有 S2 条目。

## 影响

- **不配 key**：报告仍正常生成（基于 arXiv + OpenAlex），仅少一个数据源；引用量数据由 OpenAlex 提供，不受影响。
- `search_errors` 中会记录 `semantic_scholar: HTTPError: 429...` —— 这是**预期行为**（无 key 公共配额限流），非代码故障。

---

*关联代码：`academic-report/scripts/paper_search.py`（`SemanticScholarSearcher` / `PaperSearcher.search_errors`）*
