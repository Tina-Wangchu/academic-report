# Agent Scholar — 模块实现细节文档

本目录汇集 Agent Scholar 各核心模块的**实现细节说明**（设计动机、内部机制、关键算法、测试要点），
供开发者深入理解模块内部。这些文档与源码分离——源码在 `agent-scholar/scripts/`，本目录在其外层，
保持 skill 目录（`agent-scholar/`）只含可执行代码与配置，干净清爽。

> 文档对应 v2.0 重构后的代码。`scheduler` / `timestamp_manager` 两模块已在 v2.0 去周期化重构中移除，
> 其历史实现细节文档不再保留。

## 文档索引

| 文档 | 对应模块 | 说明 |
|------|----------|------|
| [paper_search_implementation_detail.md](paper_search_implementation_detail.md) | `paper_search.py` | 多源并行检索（arXiv / Semantic Scholar / OpenAlex）、去重合并、日期过滤、限流接入 |
| [paper_filter_implementation_detail.md](paper_filter_implementation_detail.md) | `paper_filter.py` | 优先级评分、质量过滤、热点聚类（≥2 收敛 + topic_hint 相关性）、时间安全网 |
| [paper_analyzer_implementation_detail.md](paper_analyzer_implementation_detail.md) | `paper_analyzer.py` | 结构化提取、APA 7th、方向级整体分析、奠基论文（S2 References API + 离线回退）、AbstractSummarizer 分层浓缩 |
| [llm_analyzer_implementation_detail.md](llm_analyzer_implementation_detail.md) | `llm_analyzer.py` | 四要素 LLM 生成式分析（智谱 GLM Anthropic 兼容端点）、分层回退（LLM→规则）、按 DOI/title/language 缓存、全文增强 |
| [report_generator_implementation_detail.md](report_generator_implementation_detail.md) | `report_generator.py` | 四段式 MD/HTML 报告、双语骨架、热点分组渲染、四要素摘录、趋势语料派生 |
| [email_sender_implementation_detail.md](email_sender_implementation_detail.md) | `email_sender.py` | SMTP/SSL 分流、代理自动识别（直连→SOCKS 回退→本地端口探测）、重试、冷却守卫、发送日志 |

## 与其它文档的关系

- **`docs/agent-scholar skill实施计划.md`** — 项目整体实施计划与模块设计规范（权威）。
- **`docs/报告格式设计.md`** — 生成的学术报告的格式规范（双语、四段式、四要素）。
- **本目录** — 各模块**实现层面**的细节展开（实施计划的补充）。

> 若文档与源码不一致，**以源码为准**；如发现漂移，请按 `CLAUDE.md` 规则 2 同步更新本文档。
