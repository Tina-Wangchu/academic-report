"""
实验场景配置（12 个）—— 测试论文搜索 + 报告生成全链路的多参数组合。

每场景字段：
  id          场景编号
  desc        描述
  query       搜索查询（英文，便于 arXiv/S2/OpenAlex 命中）
  field       研究领域（report 标题用）
  lang        报告语言 zh/en/bilingual
  time        时间范围: 1w / 3y / 5y / none
  filters     意图级过滤器 {highly_cited/sci_ei/core_journal: bool}
  max         每源最大结果数
  format      markdown / html
  config_overrides  全局配置覆盖（方法名 -> 返回值），如 is_include_preprints / get_min_citation_count
"""

SCENARIOS = [
    {
        "id": "E1", "desc": "基线-机器学习",
        "query": "machine learning", "field": "机器学习", "lang": "bilingual",
        "time": "3y", "filters": {}, "max": 10, "format": "markdown",
    },
    {
        "id": "E2", "desc": "非AI领域-贝叶斯统计(兜底聚类)",
        "query": "bayesian statistics", "field": "统计学", "lang": "bilingual",
        "time": "3y", "filters": {}, "max": 10, "format": "markdown",
    },
    {
        "id": "E3", "desc": "高被引过滤-计算机视觉",
        "query": "computer vision", "field": "计算机视觉", "lang": "bilingual",
        "time": "5y", "filters": {"highly_cited": True}, "max": 10, "format": "markdown",
    },
    {
        "id": "E4", "desc": "SCI/EI过滤-深度学习",
        "query": "deep learning", "field": "深度学习", "lang": "bilingual",
        "time": "3y", "filters": {"sci_ei": True}, "max": 10, "format": "markdown",
    },
    {
        "id": "E5", "desc": "排除预印本",
        "query": "machine learning", "field": "机器学习", "lang": "bilingual",
        "time": "3y", "filters": {}, "max": 10, "format": "markdown",
        "config_overrides": {"is_include_preprints": False},
    },
    {
        "id": "E6", "desc": "短时间-近1周",
        "query": "artificial intelligence", "field": "AI", "lang": "bilingual",
        "time": "1w", "filters": {}, "max": 10, "format": "markdown",
    },
    {
        "id": "E7", "desc": "纯中文报告",
        "query": "machine learning", "field": "机器学习", "lang": "zh",
        "time": "3y", "filters": {}, "max": 10, "format": "markdown",
    },
    {
        "id": "E8", "desc": "纯英文报告",
        "query": "machine learning", "field": "machine learning", "lang": "en",
        "time": "3y", "filters": {}, "max": 10, "format": "markdown",
    },
    {
        "id": "E9", "desc": "HTML输出",
        "query": "machine learning", "field": "机器学习", "lang": "bilingual",
        "time": "3y", "filters": {}, "max": 10, "format": "html",
    },
    {
        "id": "E10", "desc": "宽泛多热点",
        "query": "artificial intelligence natural language processing computer vision",
        "field": "人工智能", "lang": "bilingual",
        "time": "3y", "filters": {}, "max": 10, "format": "markdown",
    },
    {
        "id": "E11", "desc": "空结果-极窄查询",
        "query": "quantum-bayesian-fusion-xyzqqq", "field": "未知领域", "lang": "bilingual",
        "time": "3y", "filters": {}, "max": 10, "format": "markdown",
    },
    {
        "id": "E12", "desc": "最小引用门槛50",
        "query": "machine learning", "field": "机器学习", "lang": "bilingual",
        "time": "3y", "filters": {}, "max": 10, "format": "markdown",
        "config_overrides": {"get_min_citation_count": 50},
    },
]
