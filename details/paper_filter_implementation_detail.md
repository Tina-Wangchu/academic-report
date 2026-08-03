# paper_filter.py - Implementation Detail

## 模块概述

**模块名称**: 文献筛选、分类、排序 (paper_filter.py) — 模块3 / Module 3
**版本**: 1.1.0（新增年份级时间安全网）
**完成日期**: 2026-07-11
**状态**: ✅ 已完成（单元测试 26 项全通过）

---

## 功能说明

### 核心功能

本模块接收 `paper_search` 去重后的原始论文列表，输出「在范围内、高价值、已排序、按热点聚类」的论文，供 `paper_analyzer`（模块4）做深度分析与 `report_generator`（模块5）渲染报告。

**主要能力**:
- ⏱️ 时间过滤——按 `intent` 时间范围做**年份级**安全网过滤
- 🎯 质量过滤——按搜索意图 `filters` 与全局 `config.yaml` 剔除不符合条件的论文
- 📊 优先级排序——高被引 > 顶刊 > 顶会 > SCI/EI > 普通期刊 > 预印本
- 🧩 热点聚类——相似/相关方向归为同一「热点」，支持非 AI 学科兜底聚类
- 📝 热点主题介绍——为每个热点生成一行主题简介（Option B：从 report_generator 迁入）

---

## 架构设计

### 类结构

```
PaperFilter
 ├── filter_and_sort(papers, intent, limit?)      # 公共入口
 ├── _filter_by_time(papers, intent)              # 年份级时间安全网
 ├── _apply_quality_filters(papers, intent)       # 质量/渠道/噪音过滤
 ├── _priority_score(paper) -> int                # 评分（可复用）
 ├── _sort_by_priority(papers)                    # 得分降序 + 年份降序 tie-break
 ├── classify_by_topic(papers) -> Dict[str,List]  # 热点聚类（按聚合权重排序）
 ├── generate_hotspot_intro(topic, papers) -> str # 热点主题介绍（Option B 迁入）
 ├── _hotspot_weight(papers) -> int               # 热点聚合权重
 ├── _match_known_topic / _extract_top_keyword    # 主题/关键词抽取
 └── _is_top_journal / _is_top_conference / _is_sci_ei / _is_academic
```

### 数据流

```
List[Paper] (paper_search 去重后)
    ↓
_filter_by_time          ← intent.start_date/end_date × paper.year（年份闭区间）
    ↓
_apply_quality_filters   ← intent.filters ∪ config（高被引/SCI·EI/核心/最小引用/预印本/噪音）
    ↓
_sort_by_priority        ← _priority_score 降序，并列按 year 降序
    ↓
(可选 limit 截断)
    ↓
classify_by_topic        ← 已知AI主题命中 → 否则关键词频次兜底 → 按权重排序
    ↓
Dict[热点名, List[Paper]]  →  report_generator 渲染「热点一/二/三」
```

---

## 实现细节

### 0. 过滤总览：多层防御（defense in depth）

论文从检索到进入报告，经过**两层过滤**，职责分离，互为兜底：

| 层级 | 模块 | 过滤维度 | 粒度 | 机制 |
|------|------|----------|------|------|
| **L1 检索层** | `paper_search.py` | 时间（提交/发表日期）、查询相关性 | 精确到天 | API 日期参数（OpenAlex `from/to_publication_date`、Semantic Scholar `year`、arXiv `submittedDate` 区间） |
| **L2 筛选层** | `paper_filter.py`（本模块） | 时间（年份安全网）、质量、噪音 | 年份级 + 业务规则 | `_filter_by_time` + `_apply_quality_filters` |

> **为什么需要 L2 时间安全网**：部分数据源（如 Semantic Scholar）的 API 日期过滤并不严格，或论文元数据的「发表年份」与「索引/提交日期」不一致，会有少量超范围论文混入。L2 按 `paper.year` 再兜底一次，保证报告涵盖时间（报告格式设计.md 的「报告涵盖时间」）与实际收录论文一致。

---

### 1. 时间过滤 `_filter_by_time`

**输入**：`intent.start_date` / `intent.end_date`（`datetime` 或 `None`），每篇论文的 `paper.year`（`int`）。
**输出**：落在时间范围内的论文子集。

#### 判定规则

1. **闭区间比较**：`start_year ≤ paper.year ≤ end_year`（含两端）。
2. **单边开放**：
   - 只有 `start_date` → 保留 `paper.year ≥ start_year`；
   - 只有 `end_date` → 保留 `paper.year ≤ end_year`。
3. **缺失年份保留**：`paper.year ≤ 0`（数据源未返回年份）的论文**不过滤**——无法判定，宁可保留也不误删有效文献。
4. **两端均 `None`**：直接放行，不做时间过滤（用户未指定时间范围时）。

#### 判定示例表

设 `intent` 时间范围 = `2023-01-01 ~ 2025-12-31`（→ `start_year=2023, end_year=2025`）：

| 论文 `year` | 判定 | 原因 |
|---|---|---|
| 2022 | ❌ 剔除 | `2022 < 2023` |
| 2023 | ✅ 保留 | `2023 ∈ [2023, 2025]` |
| 2024 | ✅ 保留 | `2024 ∈ [2023, 2025]` |
| 2025 | ✅ 保留 | `2025 ∈ [2023, 2025]`（含端点） |
| 2026 | ❌ 剔除 | `2026 > 2025` |
| 0 / 缺失 | ✅ 保留 | 无法判定 |

#### 与检索层（L1）的分工

| 场景 | L1（API 日期） | L2（年份安全网） |
|------|----------------|------------------|
| arXiv 论文提交于 2022-12，但 2023 才正式发表 | 可能按提交日过滤掉 | 看 `year` 字段决定 |
| Semantic Scholar `year` 过滤不严，混入 2026 预印本 | 可能漏过 | 兜底剔除 |
| 数据源未返回发表年份 | — | 保留（不误删） |

> 设计取舍：`Paper` 模型只存 `year`（整数），故 L2 只能做年份级比较，无法到月/日。这是有意的——更细粒度的时间控制交给 L1 的 API 参数；L2 只做「明显越界」的兜底。

---

### 2. 质量过滤 `_apply_quality_filters`

在时间过滤之后，按「**意图级 `filters` ∪ 全局 `config`**」逐维度过滤——任一来源为真，该维度即生效。各维度**顺序短路**（逐层收紧候选集）：

| 维度 | 触发条件（任一为真） | 行为 | 默认状态 |
|------|----------------------|------|----------|
| **高被引** | `intent.filters['highly_cited']` 或 `config.is_filter_highly_cited()` | 仅留 `citation_count ≥ highly_cited_threshold` | 阈值 100，默认关 |
| **SCI/EI** | `intent.filters['sci_ei']` 或 `config.is_sci_ei_only()` | 仅留 `_is_sci_ei(p)` 命中（出版商/刊名含 IEEE/ACM/Springer/Elsevier/Oxford/Cambridge/Nature/Science） | 默认关 |
| **核心期刊** | `intent.filters['core_journal']` | 仅留 `_is_top_journal(p)`（Nature/Science/Cell/PNAS…） | 默认关 |
| **最小引用量** | `config.get_min_citation_count() > 0` | 仅留 `citation_count ≥ min` | 默认 0（关） |
| **预印本** | `config.is_include_preprints() == False` | 剔除 `venue_type == 'preprint'` | 默认 True（保留） |
| **非学术噪音** | 始终 | 剔除空标题、`call for papers`/`editorial`/`table of contents` | 始终开 |

> **设计要点**：意图级与全局级**取并集**，让用户既能临时在指令里加「高被引」（一次性行为），也能在 `config.yaml` 里固化默认筛选（长期行为）。例如 `intent.filters['highly_cited']=True` 与 `config.is_filter_highly_cited()=True` 效果相同，互不覆盖。

---

### 3. 主题过滤/聚类 `classify_by_topic`

把相似/相关方向的论文归为「热点」。**两阶段 + 兜底**策略，确保任何学科都能得到有意义的聚类（而非全部落进「其他」）。

#### 阶段一：已知 AI 主题命中 `_match_known_topic`

- 词典 `TOPIC_KEYWORDS` 覆盖 7 个 AI 方向（深度学习、NLP、CV、强化学习、图网络、生成模型、大模型），每个方向含中英关键词。
- 对每篇论文，统计它在各主题下的**命中关键词数**，归入**命中数最多**的主题（并列取词典中先出现的）。
- **为什么按命中数而非「首次命中」**：一篇论文常跨多个方向（如 "diffusion model for image generation" 同时命中 CV 与生成模型），按命中数能归到与它**最相关**的方向，分类更稳。

> 未命中任何已知主题的论文进入「阶段二」。

#### 阶段二：未知领域关键词兜底 `_extract_top_keyword`

对未命中词典的论文，从标题+摘要抽取代表性关键词，按关键词聚成热点：

1. **优先复用** `paper.keywords`（数据源已标注的，取第一个）；
2. 否则做**英文 token 频次统计**：
   - 小写化，正则 `[a-z][a-z0-9-]{2,}` 抽取 ≥3 字符 token；
   - 剔除停用词（`_EN_STOPWORDS`，约 50 个虚词/常用词）；
   - 取频次最高者；**并列时按首字母序打破并列**（`-ord`），保证**确定性**——不依赖随机。
3. 关键词经 `_humanize_keyword`（`-` → 空格、Title Case）作为热点名，如 `bayesian` → `Bayesian`。

> **意义**：非 AI 学科（统计、生物、材料…）不会全部落进「其他」，而是得到有意义的英文聚类名。例如两篇统计论文都高频出现 "bayesian" → 聚到同一热点 `Bayesian`。

#### 阶段三：兜底「其他」

极少数既未命中主题、又抽不出关键词（如纯中文标题且无 keywords 标注）的论文 → 归入「其他」。

#### 热点排序：按聚合权重

返回的 `dict` **按 `_hotspot_weight`（成员 `_priority_score` 之和）降序插入**。Python 3.7+ `dict` 保持插入顺序 → 报告自动把**最重要（高价值论文最多）的方向排在最前**。

#### 聚类示例

输入 5 篇论文：

| # | 标题/摘要关键词 | 命中阶段 | 归入热点 |
|---|----------------|----------|----------|
| A | "image recognition / visual detection" | 阶段一（CV 命中 2） | 计算机视觉 |
| B | "diffusion model sampling" | 阶段一（生成模型 命中 1） | 生成模型 |
| C | "bayesian inference regression" | 阶段二（top kw = bayesian） | Bayesian |
| D | "bayesian methods" | 阶段二（top kw = bayesian） | Bayesian |
| E | 纯中文无 keywords | 阶段三 | 其他 |

→ 结果 `{"计算机视觉":[A], "Bayesian":[C,D], "生成模型":[B], "其他":[E]}`（顺序按各热点成员得分和排）。

---

### 4. 热点主题介绍 `generate_hotspot_intro`（Option B 迁入）

按 [报告格式设计.md](../../报告格式设计.md) §5.1，每个热点需一行主题简介。该方法从 `report_generator` **迁入 `paper_filter`**（分层归属：聚类相关的介绍由筛选器负责；方向级**整体分析**与**奠基性参考论文查找**归 `paper_analyzer`，见模块4）。

生成内容（确定性、基于真实论文，非空泛套话）：
- 热点名 + 收录篇数；
- 高频关键词（来自已标注 `keywords`，top 3）；
- 代表性工作（被引最高；并列取年份较新）。

输出形如：
> 本热点聚焦「生成模型」方向，共收录 2 篇论文，高频关键词包括 diffusion、sampling；代表性工作为《DDIM-Solver》（2024，引用 187）。

> 后续 `report_generator`（模块5）创建时应调用 `filter_obj.generate_hotspot_intro(topic, papers)`，**不要**再自带 `_generate_hotspot_intro`。

---

### 5. 优先级排序规则

#### 5.1 单篇评分 `_priority_score`

评分由**三个独立部分相加**（引用分层 + 渠道分层 + 引用加分）：

**① 引用量分层**（互斥，取一档）：

| 条件 | 加分 |
|------|------|
| `citation_count ≥ 100` | +100 |
| `50 ≤ citation_count < 100` | +50 |
| `< 50` | +0 |

**② 发表渠道分层**（互斥，按优先级取第一命中）：

| 优先级 | 条件 | 加分 |
|--------|------|------|
| 1 | `_is_top_journal`（Nature/Science/Cell/PNAS/Sci.Adv./Nat.Commun.） | +90 |
| 2 | `_is_top_conference`（NeurIPS/ICML/ICLR/AAAI/IJCAI/CVPR/ICCV/ECCV/ACL/EMNLP/ICSE/SIGMOD/VLDB/KDD） | +80 |
| 3 | `_is_sci_ei`（IEEE/ACM/Springer/Elsevier/Oxford/Cambridge/Nature/Science） | +70 |
| 4 | `venue_type == 'journal'`（普通期刊） | +50 |
| 5 | `venue_type == 'preprint'`（预印本） | +30 |

**③ 引用量加分**（连续）：`+ min(citation_count, 50)`（封顶 50，避免超高被引垄断排序）。

#### 5.2 排序 `_sort_by_priority`

排序键：`(-_priority_score(p), -(p.year or 0))`
- **主键**：得分降序；
- **并列打破**：发表年份降序（**新者优先**）——呼应规范「按发布时间倒序、引用量降序」。

#### 5.3 热点聚合权重 `_hotspot_weight`

`Σ _priority_score(p)` over 热点内所有论文。用于热点间排序（见 §3）。

#### 5.4 评分实战示例

| 论文 | venue | year | cit | ①引用层 | ②渠道层 | ③引用加分 | **总分** |
|------|-------|------|-----|--------|--------|-----------|---------|
| P1 | Nature | 2024 | 200 | +100 | +90（顶刊） | +50 | **240** |
| P2 | NeurIPS | 2024 | 187 | +100 | +80（顶会） | +50 | **230** |
| P3 | NeurIPS | 2023 | 320 | +100 | +80（顶会） | +50 | **230** |
| P4 | ACL | 2023 | 60 | +50 | +80（顶会） | +50 | **180** |
| P5 | IEEE Trans. | 2023 | 10 | +0 | +70（SCI/EI） | +10 | **80** |
| P6 | Some Journal | 2023 | 5 | +0 | +50（普通期刊） | +5 | **55** |
| P7 | arXiv | 2025 | 0 | +0 | +30（预印本） | +0 | **30** |

**排序结果**（注意 P2、P3 同分 230 → 并列打破取年份新的 P2 在前）：
```
P1(240) → P2(230, 2024) → P3(230, 2023) → P4(180) → P5(80) → P6(55) → P7(30)
```

---

## 配置依赖

### Hermes 配置（`~/.hermes/config.yaml` → `skills.config.academic`）

| 配置键 | 默认值 | 影响的过滤维度 |
|--------|--------|----------------|
| `include_preprints` | `true` | 预印本是否保留 |
| `min_citation_count` | `0` | 最小引用量门槛 |
| `filter_highly_cited` | `false` | 全局开启高被引筛选 |
| `highly_cited_threshold` | `100` | 高被引阈值 |
| `sci_ei_only` | `false` | 全局仅保留 SCI/EI |

> 时间范围不在 config，而来自**每次搜索的 `intent.start_date`/`end_date`**（由 `intent_parser` 从用户指令解析，如「近 3 年」「2023-2025」）。

### 模块依赖

```python
from utils import Paper, SearchIntent          # 数据模型
from config_manager import get_config_manager  # 配置管理
```

---

## 测试

### 单元测试（`test/test_paper_filter.py`，26 项全通过）

| 测试类 | 数量 | 覆盖点 |
|--------|------|--------|
| `TestPriorityScore` | 6 | 五类渠道得分 + 高被引边界 |
| `TestSortByPriority` | 2 | 得分降序 + 年份 tie-break |
| `TestTimeFilter` | 3 | 范围外剔除 + 缺失年份保留 + 无日期放行 |
| `TestQualityFilters` | 7 | 意图级（高被引/SCI·EI/核心）+ 配置级（预印本/最小引用）+ limit + 空标题 |
| `TestClassifyByTopic` | 4 | 已知主题分组 + 非 AI 兜底 + 热点按权重排序 + 顺序保持 |
| `TestGenerateHotspotIntro` | 3 | 篇数/代表作 + 空热点 + 高频关键词 |
| `TestIntegration` | 1 | 筛选→排序→聚类→介绍 端到端 |

### 运行

```bash
# 全部测试
python -m pytest test/test_paper_filter.py -v

# 模块自检（CLI）
python -m paper_filter
```

测试用 `FakeConfig` 注入确定性配置，**不依赖** `~/.hermes/config.yaml` 是否存在。

---

## 已知限制与未来改进

1. **L2 时间过滤为年份级**：`Paper` 只存 `year`，无法到月/日；更细粒度交给 L1 的 API 日期参数。若 `Paper` 未来增加 `publication_date`，可升级 L2 到日级。
2. **主题词典偏 AI**：`TOPIC_KEYWORDS` 以 AI 领域为主；其他学科依赖兜底关键词聚类（已可用，但热点名是英文 Title Case 而非精炼中文）。改进：按 `intent.research_field` 加载对应学科词典。
3. **兜底聚类为英文 TF**：中文标题/摘要的兜底聚类效果较弱（中文分词未做）。改进：引入 jieba 或按领域词典匹配中文关键词。
4. **`paper_types` 未做硬过滤**：`intent.paper_types`（journal/conference/thesis）当前仅作信息，预印本去留统一由 `is_include_preprints()` 控制，避免默认值与「含预印本」冲突。
5. **热点介绍为规则版**：当前为确定性模板；完整版可由 LLM 改写为更流畅的方向性简介（与模块4 的方向级分析一并提供）。

---

## 与规范/计划的对应

| 规范要求（报告格式设计.md §9 映射） | 实现位置 |
|------|------|
| 热点聚类 + 介绍 | `paper_filter.py::classify_by_topic` + `generate_hotspot_intro` ✅ |
| 整体分析 + 奠基性参考 | `paper_analyzer.py`（模块4，待实现）⏳ |
| 优先级排序（高被引 > SCI/EI > 顶会 > 普通 > 预印本） | `paper_filter.py::_priority_score` / `_sort_by_priority` ✅ |
| 时间范围过滤 | `paper_search.py`（L1 API 日期）+ `paper_filter.py::_filter_by_time`（L2 年份安全网）✅ |

---

**最后更新**: 2026-07-11
**维护者**: Academic Report Team
