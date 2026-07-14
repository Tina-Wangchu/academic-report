# paper_search.py - Implementation Detail

## 模块概述

**模块名称**: 多数据源论文搜索 (paper_search.py)  
**版本**: 1.0.0  
**完成日期**: 2026-07-11  
**状态**: ✅ 已完成

---

## 功能说明

### 核心功能

本模块实现从多个学术数据源并行检索论文的功能，是整个 Agent Scholar 系统的数据获取层。

**主要能力**:
- 🔍 并行搜索多个数据源（arXiv、Semantic Scholar、OpenAlex）
- ⚡ 处理 API 限流和重试逻辑
- 🔄 自动去重和合并结果
- 📅 基于时间范围过滤论文

### 支持的数据源

| 数据源 | 类 | 搜索器类 | 限流处理 |
|--------|------|----------|----------|
| arXiv | 预印本服务器 | `ArxivSearcher` | 无限制（使用官方库） |
| Semantic Scholar | AI 驱动的学术搜索 | `SemanticScholarSearcher` | 5000次/天 |
| OpenAlex | 开放学术索引 | `OpenAlexSearcher` | 无限制 |

---

## 架构设计

### 类结构

```
PaperSearcher (主协调器)
    ├── ArxivSearcher (arXiv 专用)
    ├── SemanticScholarSearcher (Semantic Scholar 专用)
    └── OpenAlexSearcher (OpenAlex 专用)
```

### 数据流

```
SearchIntent (搜索意图)
    ↓
PaperSearcher.search()
    ↓
并行执行（ThreadPoolExecutor, max_workers=3）
    ├── ArxivSearcher.search() → List[Paper]
    ├── SemanticScholarSearcher.search() → List[Paper]
    └── OpenAlexSearcher.search() → List[Paper]
    ↓
合并结果 → 去重 → 返回唯一论文列表
```

---

## 实现细节

### 1. ArxivSearcher 实现

**依赖**: `arxiv` Python 官方库

**关键特性**:
- 使用 `arxiv.Client` 进行搜索
- 支持日期范围过滤（通过 arXiv 查询语法）
- 自动提取作者、标题、摘要等元数据
- 默认按提交时间倒序排序

**查询构建策略**:
```python
# 基础查询格式
search_query = f'all:"{query}"'

# 日期过滤器格式
submittedDate:[YYYYMMDD0000 TO *]
submittedDate:[* TO YYYYMMDD2359]
```

**数据映射**:
| arXiv 字段 | Paper 字段 | 说明 |
|------------|-----------|------|
| result.title | title | 论文标题 |
| result.authors | authors | 作者列表 |
| result.published | year | 发表年份 |
| result.doi | doi | DOI标识符 |
| result.summary | abstract | 摘要内容 |
| result.entry_id | url | arXiv URL |

### 2. SemanticScholarSearcher 实现

**依赖**: Semantic Scholar REST API v1

**API 端点**: `https://api.semanticscholar.org/graph/v1/paper/search`

**限流处理**:
- 调用 `rate_limiter.wait_if_needed('semantic_scholar')`
- 如果达到限流，记录警告并返回空列表
- 限流: 5000次/天

**请求字段**（`fields` 参数）:
```
paperId,title,authors,year,venue,abstract,citationCount,
externalIds,url,openAccessPdf
```

**期刊分类逻辑**:
- 顶会识别：NeurIPS、ICML、ICLR、CVPR、ICCV等
- 期刊识别：排除 arxiv 和 unknown 的 venue
- 默认为 preprint

### 3. OpenAlexSearcher 实现

**依赖**: OpenAlex REST API

**API 端点**: `https://api.openalex.org/works`

**过滤器构建**:
```
from_publication_date:YYYY-MM-DD
to_publication_date:YYYY-MM-DD
type:article
```

**数据提取**:
- 作者: `authorships[].author.display_name`
- 期刊: `primary_location.source.display_name`
- 类型: `primary_location.source.type`
- DOI: `doi.id` (去除 https://doi.org/ 前缀)

### 4. PaperSearcher 主类实现

**初始化**:
```python
def __init__(self):
    self.config = get_config_manager()  # 获取配置
    api_keys = self.config.get_api_keys()  # 获取API密钥
    # 初始化所有搜索器
```

**并行搜索**:
- 使用 `ThreadPoolExecutor` 并行执行
- `max_workers=3`（并发度）
- 每个数据源独立执行，异常不阻塞其他搜索

**去重策略**:
1. **优先级1**: DOI 去重（更可靠）
2. **优先级2**: 标题去重（小写标准化）
3. 保留有 DOI 的记录

---

## 配置依赖

### 环境变量

| 变量名 | 用途 | 必需/可选 |
|--------|------|----------|
| `SEMANTIC_SCHOLAR_API_KEY` | Semantic Scholar API 密钥 | 可选（提升限流） |

### Hermes 配置

| 配置键 | 默认值 | 用途 |
|--------|--------|------|
| `academic.max_results` | 50 | 每个数据源最大结果数 |
| `academic.default_time_range` | 3y | 默认时间范围 |

### 模块依赖

```python
from utils import Paper, SearchIntent           # 数据模型
from rate_limiter import get_rate_limiter      # 限流处理
from config_manager import get_config_manager  # 配置管理
```

---

## API 限流处理

### 限流配置

在 `rate_limiter.py` 中定义：

```python
RATE_LIMITS = {
    'semantic_scholar': (5000, 86400),  # 5000次/天
    'crossref': (10, 1),                  # 10次/秒
    'openalex': (100, 1),                 # 100次/秒
    'arxiv': (None, None),                 # 无限制
}
```

### 限流机制

**工作原理**:
1. 维护请求历史记录（`request_history`）
2. 检查时间窗口内的请求数
3. 如果超限，计算等待时间
4. 执行等待（`time.sleep()`）
5. 记录本次请求

**示例流程**:
```
Semantic Scholar:
  当前窗口: 24小时
  已用请求: 4998
  剩余请求: 2
  操作: 等待直到窗口重置 → 记录新请求
```

---

## 测试方法

### 单元测试

```bash
# 测试 arXiv 搜索
python3 -c "
from scripts.paper_search import ArxivSearcher
searcher = ArxivSearcher()
papers = searcher.search('machine learning', max_results=5)
print(f'Found {len(papers)} papers')
"

# 测试 Semantic Scholar 搜索
python3 -c "
from scripts.paper_search import SemanticScholarSearcher
searcher = SemanticScholarSearcher()
papers = searcher.search('deep learning', max_results=5)
print(f'Found {len(papers)} papers')
"

# 测试 OpenAlex 搜索
python3 -c "
from scripts.paper_search import OpenAlexSearcher
searcher = OpenAlexSearcher()
papers = searcher.search('neural network', max_results=5)
print(f'Found {len(papers)} papers')
"
```

### 集成测试

```bash
# 测试完整流程
python3 scripts/paper_search.py \
  --query "artificial intelligence" \
  --max-results 10 \
  --output test_papers.json

# 测试带时间范围
python3 scripts/paper_search.py \
  --query "quantum computing" \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --output test_papers_2023.json
```

### Hermes 集成测试

```bash
hermes chat -q "/academic-scholar 搜索最近的深度学习论文"
```

---

## 性能特性

### 并发性能

**并行执行**:
- 3个数据源同时搜索
- 理论加速比: 3x（相比串行）
- 实际加速: 2-2.5x（考虑网络延迟）

**性能数据**（估算）:
- 单次搜索（50篇/源）: 约10-20秒
- arXiv: ~3秒
- Semantic Scholar: ~8秒（受限流）
- OpenAlex: ~5秒

### 内存使用

**估算内存占用**（100篇论文）:
- Paper 对象: ~500 bytes × 100 = 50KB
- 总计（含临时数据）: < 5MB

---

## 已知问题和限制

### 当前限制

1. **Semantic Scholar 限流**
   - 每天5000次请求限制
   - 超限后自动跳过该数据源
   - 建议：缓存结果，避免重复搜索

2. **arXiv 搜索延迟**
   - `delay_seconds=3.0` 固定延迟
   - 频繁搜索会较慢
   - 建议：批量搜索，减少请求数

3. **去重策略简化**
   - 仅基于 DOI 和标题
   - 未考虑作者、摘要相似度
   - 可能漏掉部分重复

### 未来改进

1. **添加更多数据源**
   - CrossRef（已有限流配置）
   - PubMed（生物医学专用）
   - Google Scholar（需注意反爬虫）

2. **增强去重**
   - 基于作者和年份去重
   - 摘要相似度匹配
   - 使用 embedding 向量化

3. **搜索优化**
   - 查询扩展（同义词、缩写）
   - 结果缓存机制
   - 增量搜索支持

---

## 使用示例

### 基础搜索

```python
from scripts.paper_search import PaperSearcher
from scripts.utils import SearchIntent

# 创建搜索意图
intent = SearchIntent(
    query="machine learning",
    keywords=["machine learning", "neural network"],
    research_field="ai",
    language="bilingual",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    max_results=50
)

# 执行搜索
searcher = PaperSearcher()
papers = searcher.search(intent)

print(f"找到 {len(papers)} 篇论文")
```

### 获取配置

```python
from config_manager import get_config_manager

config = get_config_manager()
max_results = config.get_max_results()  # 默认: 50
api_keys = config.get_api_keys()  # 获取API密钥
```

---

## 调试技巧

### 启用调试日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 查看限流状态

```python
from rate_limiter import get_rate_limiter

limiter = get_rate_limiter()
status = limiter.get_status()
print(status['semantic_scholar']['remaining'])  # 查看剩余请求数
```

### 测试单个数据源

```bash
# 只测试 arXiv
python3 -c "
from scripts.paper_search import ArxivSearcher
s = ArxivSearcher()
papers = s.search('AI', max_results=3)
for p in papers:
    print(f'- {p.title} ({p.year})')
"
```

---

## 参考资料

- [arXiv API 文档](https://arxiv.org/help/api)
- [Semantic Scholar API](https://www.semanticscholar.org/product/api)
- [OpenAlex API](https://docs.openalex.org/)
- [Hermes Agent 文档](https://hermes-agent.nousresearch.com/docs/)
- [实施计划](../agent-scholar%20skill实施计划.md)

---

**最后更新**: 2026-07-11  
**维护者**: Agent Scholar Team
