# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 关键工作流程规则

### 规则 1：修改前重新理解项目意图

**每次创建或修改文件之前**，你必须：

1. 阅读 `docs/academic-report skill实施计划.md` 以重新理解项目的完整意图和需求
2. 使你的实现与该计划中的详细规范保持一致（2357 行详细的实现代码）
3. 确保你的更改支持 docs/design-init.txt 中指定的 6 个核心模块和 2 种功能模式

**原因**：实施计划包含所有 6 个模块的权威规范。阅读它可以防止偏离需求并确保与整体架构的一致性。

### 规则 2：更改后同步文档

**每次代码修改或文件创建之后**，你必须：

1. 更新 `docs/academic-report skill实施计划.md`：
   - 将已实现的模块标记为 ✅ 完成
   - 更新进度部分
   - 添加任何新的实现细节或代码更改
   - 确保计划反映当前实际状态

2. 更新 `README.md`：
   - 在功能特性表中更新模块完成状态
   - 在 🛠️ 开发状态部分更新开发进度
   - 添加任何新功能或命令
   - 确保文档与实现现实相符

**原因**：这使文档与代码保持同步，防止文档过时，并维护项目状态的单一真实来源。

## 项目概述

Academic Report 是一个**平台无关的 AI Agent 技能**（可用于 Claude、Codex 等，不依赖任何特定 Agent 运行环境），可执行自动化学术论文搜索、分析和报告生成并通过电子邮件发送。它与多个学术数据源（arXiv、Semantic Scholar、OpenAlex）集成以检索论文，智能过滤和排序，提取关键信息，并生成通过电子邮件发送的格式化学术报告。

## 架构

### 核心数据流

```
用户自然语言输入
    ↓
意图解析器（提取：查询、关键词、时间范围、过滤器、调度）
    ↓
论文搜索器（带限流的多源并行搜索）
    ↓
论文过滤器（优先级排序、主题分类、去重）
    ↓
论文分析器（提取元数据、分析内容、生成 APA 引用）
    ↓
报告生成器（Markdown/PDF 报告生成与趋势分析）
    ↓
邮件发送器（SMTP 附件投递）
```

### 模块架构

系统遵循管道架构，在 `academic-report/scripts/` 中包含 6 个核心模块 + 2 种模式/基础设施模块：

**已完成模块** ✅：
- `utils.py` - 数据模型（`Paper`、`SearchIntent`）和工具函数（APA 引用、日期解析、`schedule_interval`）
- `config_manager.py` - 统一配置管理（**唯一配置来源 `academic-report/assets/.env`**，由 `.env.example` 复制；getter 优先读环境变量）
- `rate_limiter.py` - 多数据源的 API 限流处理器（已接入 arXiv/Semantic Scholar/OpenAlex；CrossRef/PubMed 已配置限流但 Searcher 暂未接入）
- `intent_parser.py` - 自然语言解析器，提取搜索参数 + **调度检测**（`is_scheduled`/`schedule`）
- `paper_search.py` - 多源论文搜索器（arXiv、Semantic Scholar、OpenAlex；日期过滤）
- `paper_filter.py` - 智能过滤、排序、热点聚类
- `paper_analyzer.py` - 信息提取、四要素摘录、APA 第七版、整体分析、奠基性论文
- `report_generator.py` - 学术报告生成器（Markdown + PDF、双语、四要素摘录、增量标签）
- `email_sender.py` - SMTP/SSL 邮件发送器（附件、重试、**自动检测代理：直连 → SOCKS 回退**，无论代理开关都能发邮件）
- `pipeline.py` - 全链路编排器（搜索→报告→邮件）+ **增量分支**（`--incremental`）
- `timestamp_manager.py` ✅ - 持久化每个主题的上次运行时间戳（`~/.hermes/academic_scholar_timestamps.json`）用于增量模式
- `scheduler.py` ✅ - 独立进程内调度器（定时报告入口）：解析周期 → 循环 `run_pipeline(incremental=True)`；`--once/--dry-run`；SIGINT；可选 croniter
- `llm_analyzer.py` ✅ - 四要素 **LLM 生成式**分析（通过 Anthropic 兼容端点使用智谱 GLM；LLM→规则回退 + 缓存）；填充参考深度的 4 个单论文要素

### 关键设计模式

**单例管理器**：
- `get_config_manager()` 返回全局 ConfigManager 实例
- `get_rate_limiter()` 返回全局 RateLimiter 实例
- `get_timestamp_manager()` 返回全局 TimestampManager 实例

**数据模型**：
- `Paper`（dataclass）- 具有分析字段的核心论文元数据
- `SearchIntent`（dataclass）- 解析的用户搜索参数

**配置层次**（唯一配置文件 `academic-report/assets/.env`）：
1. 真实环境变量（`os.environ`，优先级最高，便于 CI/容器临时覆盖）
2. `.env` 文件（用户配置：密钥 + 非敏感参数，由 `.env.example` 复制而来）
3. 代码默认值（各 getter 的 default 参数兜底）

> 不读取 `~/.hermes/` 或任何其它路径。全部可用配置项见 `academic-report/assets/.env.example`。

## 必要配置

### 必需设置

在任何开发或测试之前（从项目根目录 `academic-report/` 出发）：

```bash
# 1. 安装依赖
cd academic-report
pip install -r requirements.txt

# 2. 配置：复制模板并填入你自己的值（.env 是本工程唯一配置来源）
cp assets/.env.example assets/.env
# 然后编辑 assets/.env，至少填写 SMTP_* 四项（邮件功能必需）：
#   SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD
```

`.env` 中其余配置（LLM 分析、报告参数、代理）均为可选，详见 `academic-report/assets/.env.example` 内的分组注释。

### Gmail 应用密码

对于 Gmail SMTP，生成应用密码：https://myaccount.google.com/apppasswords

## 开发命令

### 测试单个模块

```bash
# 测试配置加载
python3 academic-report/scripts/config_manager.py

# 测试意图解析
python3 academic-report/scripts/intent_parser.py --input "搜索最近的深度学习论文"

# 测试邮件配置（需要 SMTP 设置）
python3 academic-report/scripts/email_sender.py --test
```

### 测试文件要求

**所有测试脚本必须遵循以下约定**：

1. **命名约定**：所有测试文件必须以 `test_` 为前缀
   - ✅ 正确：`test_paper_search.py`、`test_intent_parser.py`、`test_report_generator.py`
   - ❌ 错误：`paper_search_test.py`、`test_search.py`、`tests.py`

2. **文件位置**：所有测试文件必须保存在 `test/` 目录中
   - ✅ 正确：`test/test_paper_search.py`、`test/test_filter.py`
   - ❌ 错误：`scripts/test_paper_search.py`、`tests/test_filter.py`

3. **测试结构**：
   - 模块的单元测试应命名为 `test_<module_name>.py`
   - 示例：`paper_search.py` 的测试 → `test/test_paper_search.py`

**测试目录结构**：
```
test/
├── __init__.py
├── test_intent_parser.py      # scripts/intent_parser.py 的测试
├── test_paper_search.py        # scripts/paper_search.py 的测试
├── test_paper_filter.py        # scripts/paper_filter.py 的测试
├── test_paper_analyzer.py      # scripts/paper_analyzer.py 的测试
├── test_report_generator.py    # scripts/report_generator.py 的测试
├── test_email_sender.py        # scripts/email_sender.py 的测试
└── test_integration.py         # 集成测试
```

**运行测试**：
```bash
# 运行所有测试
pytest test/

# 运行特定测试文件
pytest test/test_paper_search.py

# 运行特定测试函数
pytest test/test_paper_search.py::test_arxiv_search

# 以详细输出运行
pytest test/ -v

# 运行覆盖率测试
pytest test/
```

### Hermes Agent 集成

```bash
# 将技能安装到 Hermes
cp -r academic-report-2.0/academic-report ~/.hermes/skills/academic-report

# 测试技能加载
hermes chat -q "/academic-report 帮助"

# 列出所有技能
/skills
```

### 在 Hermes 中运行

```bash
# 单次搜索模式
hermes chat -q "/academic-report 搜索最近的机器学习论文，生成报告并发送到我的邮箱"

# 定时报告（接受蓝图建议）
hermes chat
/suggestions accept 1
```

## 模块实现优先级

**阶段 1（高优先级）** - 核心搜索和过滤：
1. `paper_search.py` - 实现 ArxivSearcher、SemanticScholarSearcher、PaperSearcher 及并行执行
2. `paper_filter.py` - 实现优先级评分算法、主题分类、去重

**阶段 2（中优先级）** - 分析和报告：
3. `paper_analyzer.py` - 信息提取、APA 第七版格式化、相关论文查找
4. `report_generator.py` - Markdown 生成、PDF 转换（reportlab）、趋势分析

**阶段 3（低优先级）** - 交付和测试：
5. `email_sender.py` - SMTP 集成及重试逻辑
6. `templates/` - 创建 report_template.md（HTML 模板已移除，PDF 现由 reportlab 渲染）

## 数据源集成

### API 限流（由 RateLimiter 处理）

| 数据源 | 限制 | 实现 |
|--------|-------|----------------|
| arXiv | 无限制 | 直接使用 `arxiv` 库 |
| Semantic Scholar | 5000/天 | REST API，可选 API 密钥 |
| OpenAlex | 无限制 | REST API |
| CrossRef | 10/秒 | **预留**（rate_limiter 已配置，Searcher 暂未接入） |
| PubMed | 3/秒 | **预留**（同上） |

### 搜索策略

实现 `paper_search.py` 时：
- 使用 `ThreadPoolExecutor` 进行并行搜索（max_workers=3）
- 在每次 API 调用前调用 `rate_limiter.wait_if_needed(source)`
- 使用 `_deduplicate()` 合并结果（优先保留有 DOI 的论文）
- 优雅地处理异常，记录错误，继续处理其他数据源

## 报告结构

生成的报告遵循 `docs/报告格式设计.md` 的规范（双语中/英，**权威**）。`report_generator.py` 模块 5 和 `templates/report_template.md` 必须符合此规范（PDF 由 reportlab 渲染，不再使用 HTML 模板）。结构：

1. **标题 + 时间** — `{time_range} {field/topic} 报告`（例如，`2023-2025 统计学研究报告`）；小字行显示**报告生成时间**和**报告覆盖时间**（论文发表范围从 `intent.start_date` 到 `end_date`）
2. **一、报告速览** — **按热点**总结（非单篇）：列出报告覆盖的热点 + 每个热点的具体发现（代表性论文的结果/结论）；不要列出每篇论文标题
3. **二、分类论文展示** — 按"热点"（相似/相关方向）分组的论文。每个热点：
   - 热点名称（例如，`热点一：XXXX`）+ 热点主题介绍
   - 每篇论文：标题；作者、发表时间、期刊/会议、引用计数、DOI；**摘要（~150-200 字，浓缩论文的核心成就）**；APA 第七版引用
   - 整体分析（将热点的论文综合为方向级分析）
   - 奠基性参考论文（该方向 1-3 篇最具奠基性/突破性的历史工作）
4. **三、研究趋势** — 约 200 字；未来研究趋势 + 研究缺口，基于收录的论文（避免通用套话）

## 常见问题

### SMTP 认证失败
- Gmail 需要应用密码，而非账户密码
- 检查 `SMTP_PORT`：TLS 用 587，SSL 用 465
- 验证 `SMTP_USER` 与电子邮件地址匹配

### API 限流
- Semantic Scholar：使用 `rate_limiter.get_remaining_requests('semantic_scholar')` 监控剩余请求数
- 在 `rate_limiter.wait_if_needed()` 中实现自动等待
- 开发时考虑缓存结果以避免重复 API 调用

### 模块依赖
所有脚本都从 `utils.py` 导入，确保首先实现它：
- `from utils import Paper, SearchIntent, parse_date_range, format_apa_citation`
- `from config_manager import get_config_manager`
- `from rate_limiter import get_rate_limiter`

## 文件上下文

- **SKILL.md** - 技能定义与使用说明（平台无关；将在 Phase 3 进一步精简，去除历史修改残留）
- **docs/design-init.txt** - 原始中文需求文档（6 个核心模块，2 种模式）
- **docs/academic-report skill实施计划.md** - 详细实施计划（2000+ 行，包含所有 6 个模块的完整代码）
- **docs/报告格式设计.md** - 权威双语（中/英）报告格式规范；模块 5 和报告模板必须符合
- **requirements.txt** - Python 依赖（arxiv、scholarly、pandas、markdown、jinja2、secure-smtplib、python-dateutil、pyyaml）

## 实现说明

### 实现 `paper_search.py` 时：

遵循 `docs/academic-report skill实施计划.md` 实施计划中的模式（第 518+ 行）：

```python
class PaperSearcher:
    def __init__(self):
        self.config = get_config_manager()
        api_keys = self.config.get_api_keys()
        self.searchers = {
            'arxiv': ArxivSearcher(),
            'semantic_scholar': SemanticScholarSearcher(api_keys['semantic_scholar']),
            # 添加其他数据源...
        }
    
    def search(self, intent: SearchIntent) -> List[Paper]:
        # 使用 ThreadPoolExecutor 并行搜索
        # 去重结果
        # 返回合并列表
```

### 实现 `paper_filter.py` 时：

优先级评分算法（来自计划，第 953+ 行）：
- 高被引（≥100 次引用）：+100 分
- 顶级期刊（Nature/Science/Cell）：+90 分
- 顶级会议（NeurIPS/ICML/ICCV）：+80 分
- SCI/EI 索引：+70 分
- 普通期刊：+50 分
- 预印本：+30 分
- 引用计数加分：+min(citation_count, 50)
