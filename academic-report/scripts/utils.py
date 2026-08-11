"""
工具函数库
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Paper:
    """论文数据模型"""
    title: str
    authors: List[str]
    venue: str              # 期刊/会议名称
    year: int
    doi: str
    abstract: str
    keywords: List[str]
    citation_count: int
    venue_type: str         # journal/conference/preprint
    ranking: str            # SCI/EI/核心/普通
    published_date: Optional[date] = None   # 精确发表日（日级，增量过滤用）；缺失回退 year
    research_content: str = ""  # 核心研究内容
    innovations: str = ""       # 创新点
    conclusions: str = ""        # 核心结论
    value_application: str = ""  # 研究价值与应用场景
    condensed_abstract: str = ""  # 浓缩摘要（report 显示用，由 AbstractSummarizer 填充）
    tldr: str = ""               # Semantic Scholar 自动生成的 TL;DR（学术概括）
    # 四要素摘录（从摘要中抽取，由 StructuredExtractor 填充；单篇块按此展示）
    problem: str = ""                 # 解决的问题
    existing_approaches: str = ""     # 现有方案（引用先前工作）
    new_approach: str = ""            # 新方案
    results_limitations: str = ""     # 效果及局限性
    analysis_source: str = ""         # 四要素来源："llm" | "rule"（便于评测/调试）
    title_zh: str = ""                # 中文标题翻译（四要素 LLM 同步生成；双语/zh 模式显示用）
    related_papers: List[str] = None  # 相关论文
    url: str = ""
    source: str = ""         # 数据来源
    pdf_url: str = ""        # 开放获取 PDF/全文 URL（无摘要时用于全文分析）

    def __post_init__(self):
        if self.related_papers is None:
            self.related_papers = []

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Paper':
        """从字典创建对象"""
        return cls(**data)


@dataclass
class SearchIntent:
    """搜索意图数据模型"""
    query: str                   # 搜索查询
    keywords: List[str]         # 关键词
    research_field: str          # 研究领域
    language: str               # en/zh/bilingual
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    paper_types: List[str] = None  # journal/conference/thesis
    filters: Dict[str, bool] = None  # 筛选条件
    max_results: int = 50

    def __post_init__(self):
        if self.paper_types is None:
            self.paper_types = ["journal", "conference"]
        if self.filters is None:
            self.filters = {
                "highly_cited": False,
                "sci_ei": False,
                "core_journal": False,
                "latest_research": False
            }

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        # 转换 datetime 对象
        if self.start_date:
            data['start_date'] = self.start_date.isoformat()
        if self.end_date:
            data['end_date'] = self.end_date.isoformat()
        return data


def load_json(file_path: str) -> Dict:
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, file_path: str) -> None:
    """保存到 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_skill_dir() -> Path:
    """获取技能目录路径"""
    return Path(__file__).parent.parent


def get_skill_data_dir() -> Path:
    """
    获取 skill 配置/数据目录（唯一路径：项目内 academic-report/assets/）。

    所有配置与运行期数据统一存放于此（不读取任何其它路径）：
      - .env                              用户配置（唯一配置来源，由 .env.example 复制而来）
      - llm_cache_four_element.json       LLM 四要素缓存（程序自动生成）
      - email_sends.jsonl                 邮件发送日志（程序自动生成）
      - email_send_cooldown.json          邮件冷却状态（程序自动生成）

    目录可能尚不存在，由调用方按需 mkdir(parents=True)。
    """
    return get_skill_dir() / 'assets'


def get_config_path() -> Path:
    """获取配置文件路径（唯一路径：assets/config.yaml）"""
    return get_skill_data_dir() / 'config.yaml'


def get_timestamp_file_path() -> Path:
    """获取时间戳文件路径（唯一路径：assets/academic_scholar_timestamps.json）"""
    return get_skill_data_dir() / 'academic_scholar_timestamps.json'


def parse_date_range(text: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    解析时间范围文本 → (start, end)。支持：
    - 绝对区间："2023-01-01至2023-12-31"（至/到/~/-/--）
    - 单年："2024年" → 当年 1-1 ~ 12-31
    - 相对："近1年/3年/1月/1周/不限"（月/年用日历精确 relativedelta）
    """
    if not text:
        return None, None
    t = text.strip().lower()

    # 1) 绝对日期区间：YYYY-MM-DD [至到~—-]+ YYYY-MM-DD
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s*[至到~\-—]+\s*(\d{4}-\d{2}-\d{2})", t)
    if m:
        try:
            s = datetime.strptime(m.group(1), "%Y-%m-%d")
            e = datetime.strptime(m.group(2), "%Y-%m-%d")
            return s, e
        except ValueError:
            pass

    # 2) 单个年份："2024年" → 当年全年（不含"近"以免与相对冲突）
    m = re.search(r"(\d{4})\s*年", t)
    if m and "近" not in t:
        y = int(m.group(1))
        try:
            return datetime(y, 1, 1), datetime(y, 12, 31, 23, 59)
        except ValueError:
            pass

    end_date = datetime.now()
    # 3) 相对范围（月/年用日历精确 relativedelta，缺失则回退 timedelta 近似）
    try:
        from dateutil.relativedelta import relativedelta
        def rel(months=0, years=0, weeks=0, days=0):
            return end_date - relativedelta(months=months, years=years,
                                            weeks=weeks, days=days)
    except ImportError:
        def rel(months=0, years=0, weeks=0, days=0):
            return end_date - timedelta(days=months * 30 + years * 365
                                        + weeks * 7 + days)

    time_patterns = {
        # 中文：年 / 月 / 周
        r"近?\s*(\d+)\s*年": lambda m: rel(years=int(m.group(1))),
        r"近?\s*(\d+)\s*个?月": lambda m: rel(months=int(m.group(1))),
        r"近?\s*(\d+)\s*周": lambda m: rel(weeks=int(m.group(1))),
        # 英文缩写：y / mo / w（与 .env DEFAULT_TIME_RANGE、--time 参数一致）
        r"近?\s*(\d+)\s*y(?:ears?)?": lambda m: rel(years=int(m.group(1))),
        r"近?\s*(\d+)\s*mo(?:nths?)?": lambda m: rel(months=int(m.group(1))),
        r"近?\s*(\d+)\s*w(?:eeks?)?": lambda m: rel(weeks=int(m.group(1))),
        r"不限?|all": lambda m: None,
    }
    for pattern, calc_start in time_patterns.items():
        match = re.search(pattern, t)
        if match:
            return calc_start(match), end_date

    return None, None


def normalize_author_name(name: str) -> str:
    """规范化作者姓名"""
    # 移除多余空格
    name = ' '.join(name.split())
    return name


def clean_doi(doi: str) -> str:
    """清理 DOI"""
    if not doi:
        return ""
    # 移除 DOI 前缀
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi)
    return doi.strip()


def format_apa_citation(paper: Paper) -> str:
    """
    生成 APA 7th 格式引用（参考列表规则）。
    - ≤20 位作者：全部列出，最后一位前用 ", & "（Oxford 逗号）。
    - >20 位作者：列前 19 位 + "..." + 最后 1 位。
    Author, A. A., & Author, B. B. (Year). Title. *Venue*. https://doi.org/...
    """
    authors_list = [a for a in (paper.authors or []) if a]
    if not authors_list:
        authors_str = ""
    elif len(authors_list) == 1:
        authors_str = authors_list[0]
    elif len(authors_list) <= 20:
        authors_str = ", ".join(authors_list[:-1]) + ", & " + authors_list[-1]
    else:  # >20：前 19 + ... + 最后 1（APA 7th）
        authors_str = ", ".join(authors_list[:19]) + ", ... " + authors_list[-1]

    # 期刊/会议名称（斜体，在 markdown 中用 * 包围）
    venue = f"*{paper.venue}*" if paper.venue else ""

    # 构建 APA 引用
    citation = f"{authors_str} ({paper.year}). {paper.title}."
    if venue:
        citation += f" {venue}"
    # 添加 DOI（如果有）
    if paper.doi:
        citation += f". https://doi.org/{clean_doi(paper.doi)}"
    return citation.strip()


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def safe_filename(filename: str) -> str:
    """生成安全的文件名"""
    # 移除或替换不安全的字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def create_backup(file_path: Path) -> Optional[Path]:
    """创建文件备份"""
    if not file_path.exists():
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"

    import shutil
    shutil.copy2(file_path, backup_path)
    return backup_path
