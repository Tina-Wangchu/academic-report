# 论文搜索 + 报告生成 端到端实验

对 `paper_search → paper_filter → paper_analyzer → report_generator` 全链路做参数化实验，覆盖查询领域 / 语言 / 时间 / 过滤器 / 格式 / 边界等。

## 运行

```bash
cd test/experiments
python run_experiment.py E1          # 单场景
python run_experiment.py --all       # 全部 12 场景
python run_all_experiments.py        # 全部 + 生成 summary.md 对照表
```

## 12 个场景（`scenarios.py`）

| ID | 描述 | 关键参数 |
|----|------|---------|
| E1 | 基线-机器学习 | bilingual, 3y |
| E2 | 非AI领域-贝叶斯统计 | 兜底聚类 |
| E3 | 高被引过滤 | filters.highly_cited, 5y |
| E4 | SCI/EI 过滤 | filters.sci_ei |
| E5 | 排除预印本 | config.is_include_preprints=false |
| E6 | 短时间-近1周 | time=1w |
| E7 | 纯中文报告 | language=zh |
| E8 | 纯英文报告 | language=en |
| E9 | PDF 输出 | format=pdf |
| E10 | 宽泛多热点 | 多领域查询 |
| E11 | 空结果-极窄查询 | 造词，测鲁棒性 |
| E12 | 最小引用门槛 | config.get_min_citation_count=50 |

## 输出（`output/<场景ID>/`）

- `raw_papers.json` — 去重后的原始论文
- `filtered.json` — 筛选排序后
- `hotspots.json` — 热点聚类（标题/年份/引用）
- `metrics.json` — 各源数量、去重前后、过滤前后、热点分布、耗时、是否离线回退
- `report.md` 或 `report.pdf` — 最终报告
- `output/summary.md` — 预计 vs 实际对照表
- `output/all_metrics.json` — 全部指标

## 最近一次运行结果（2026-07-12）

12/12 场景全部 OK（不崩）。关键数据见 `output/summary.md`。

**实验期间发现并修复的 paper_search bug**（4 处）：
1. OpenAlex `doi` 字段为字符串 URL，原按 dict 取 `.get('id')` 崩溃
2. OpenAlex `primary_location` 可为 `null`，原 `.get('source')` 崩溃
3. arXiv 日期双 `submittedDate` 子句 AND → HTTP 500，改单区间
4. `_deduplicate` 按 DOI 命中未记录标题，重复从标题分支漏网

**已知环境限制**：
- Semantic Scholar 无 API key → 持续 429（实验主要靠 arXiv + OpenAlex 两源）
- 奠基论文查找在本环境走离线回退（无 S2 网络）

**已修复的质量问题**（报告格式设计.md §10）：
- 兜底聚类产生单论文噪声热点（`Apple(1)`、`Clinical(1)`）→ 改为 **≥2 篇共享才单列热点，单篇并入「其他」**；E1 热点 17→5、E2 18→2。
- 热点与搜索主题不相关 → `classify_by_topic` 接收 `topic_hint`（查询+领域），优先选取相关关键词（如 E2 形成 `Bayesian(15)` 主热点）。
- Abstract 缺失留白 → 显示占位「（暂无摘要 / No abstract available）」。
- 创新点无信号词时空泛默认 → 改从方法子句派生；无摘要时留空不渲染。
