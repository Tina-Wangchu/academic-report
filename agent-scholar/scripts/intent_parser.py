"""
用户意图解析器
解析用户的自然语言输入，提取检索参数
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import argparse

from utils import SearchIntent, parse_date_range, schedule_interval

logger = logging.getLogger(__name__)


class IntentParser:
    """用户意图解析器"""

    def __init__(self):
        """初始化解析器"""
        # 研究领域关键词映射
        self.field_keywords = {
            'machine_learning': ['机器学习', 'machine learning', 'ML', '深度学习', 'deep learning'],
            'computer_vision': ['计算机视觉', 'computer vision', 'CV', '图像识别', 'image recognition'],
            'nlp': ['自然语言处理', 'nlp', 'natural language processing', 'NLP', '大语言模型', 'LLM', 'GPT'],
            'robotics': ['机器人', 'robotics', 'robot'],
            'ai': ['人工智能', 'artificial intelligence', 'AI', '人工智能'],
        }

        # 文献类型关键词
        self.paper_type_keywords = {
            'journal': ['期刊', 'journal', '论文'],
            'conference': ['会议', 'conference', '会议论文'],
            'thesis': ['学位论文', 'thesis', 'dissertation'],
        }

        # 筛选条件关键词
        self.filter_keywords = {
            'highly_cited': ['高被引', 'highly cited', '高引用', '热门'],
            'sci_ei': ['SCI', 'EI', 'sci', 'ei'],
            'core_journal': ['核心期刊', 'core journal', '顶刊', '顶级期刊'],
            'latest_research': ['最新', 'latest', 'recent', '前沿'],
        }

    def parse(self, user_input: str) -> SearchIntent:
        """
        解析用户输入

        Args:
            user_input: 用户的自然语言输入

        Returns:
            SearchIntent: 解析后的搜索意图
        """
        logger.info(f"解析用户输入: {user_input}")

        # 提取查询主题
        query = self._extract_query(user_input)

        # 提取关键词
        keywords = self._extract_keywords(user_input)

        # 识别研究领域
        research_field = self._identify_research_field(user_input)

        # 识别语言
        language = self._identify_language(user_input)

        # 定时检测（在时间范围之前，便于给定时输入一个短窗口）
        is_scheduled = self._detect_schedule(user_input)
        schedule = self._extract_schedule(user_input) if is_scheduled else None

        # 提取时间范围
        time_range_text = self._extract_time_range(user_input)
        if is_scheduled and not self._has_explicit_time_range(user_input):
            # 定时输入且无显式「近N」：用周期默认短窗口（而非近3年）
            start_date, end_date = self._schedule_default_window(schedule)
        else:
            start_date, end_date = parse_date_range(time_range_text)

        # 识别文献类型
        paper_types = self._identify_paper_types(user_input)

        # 识别筛选条件
        filters = self._identify_filters(user_input)

        # 创建搜索意图
        intent = SearchIntent(
            query=query,
            keywords=keywords,
            research_field=research_field,
            language=language,
            start_date=start_date,
            end_date=end_date,
            paper_types=paper_types,
            filters=filters,
            is_scheduled=is_scheduled,
            schedule=schedule,
        )

        logger.info(f"解析结果: {intent.to_dict()}")
        return intent

    def _extract_query(self, text: str) -> str:
        """提取搜索查询"""
        # 移除常见的指令词
        text = text.lower()

        instruction_patterns = [
            r'搜索|search|查找|find|找|检索',
            r'论文|papers?|文章|articles?',
            r'关于|about|on',
            r'最新的|recent|latest',
            r'生成报告|generate report',
            r'发送邮件|send email',
            r'发送|send',                         # 定时报告的发送动词
            # 定时/周期短语（从查询里剔除，避免污染检索词与 topic_key）
            r'每\s*周[一二三四五六日天]?',
            r'每\s*个?月|每月',
            r'每\s*两?\s*周',
            r'每\s*[天日]',
            r'每\s*\d+\s*[天日]',
            r'定时|周期|定期|weekly|monthly|daily|biweekly',
            r'every\s+\d+\s+days?',
        ]

        for pattern in instruction_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        query = text.strip()
        return query if query else "人工智能"  # 默认查询

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []

        # 常见学术领域关键词
        academic_terms = [
            '深度学习', 'deep learning', '机器学习', 'machine learning',
            '神经网络', 'neural network',
            '自然语言处理', 'natural language processing', 'NLP',
            '计算机视觉', 'computer vision',
            '强化学习', 'reinforcement learning',
            'GPT', 'Transformer', 'BERT',
            'CNN', 'RNN', 'LSTM',
        ]

        for term in academic_terms:
            if term.lower() in text.lower() and term not in keywords:
                keywords.append(term)

        return keywords

    def _identify_research_field(self, text: str) -> str:
        """识别研究领域"""
        text_lower = text.lower()

        for field, keywords in self.field_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return field

        return "general"  # 默认为通用

    def _identify_language(self, text: str) -> str:
        """识别语种偏好"""
        # 检查是否包含中文
        has_chinese = bool(re.search(r'[一-鿿]', text))

        # 检查语言关键词
        language_patterns = {
            'en': [r'\benglish\b', r'英文', r'英语'],
            'zh': [r'\bchinese\b', r'中文', r'汉语'],
            'bilingual': [r'双语', r'bilingual', r'中英'],
        }

        for lang, patterns in language_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return lang

        # 默认：包含中文返回 zh，否则返回 bilingual
        return 'zh' if has_chinese else 'bilingual'

    def _extract_time_range(self, text: str) -> str:
        """提取时间范围（相对区间 / 绝对日期区间 / 单年 / 不限）。"""
        time_patterns = [
            # 绝对日期区间：2023-01-01至2023-12-31（至/到/~/-/--）
            r'\d{4}-\d{2}-\d{2}\s*[至到~\-—]+\s*\d{4}-\d{2}-\d{2}',
            r'\d{4}\s*年',                       # 单个年份：2024年
            r'近?\s*(\d+)\s*周',
            r'近?\s*(\d+)\s*个?月',
            r'近?\s*(\d+)\s*年',
            r'不\s*限|all',
        ]

        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        # 默认：近3年
        return "近3年"

    # ------------------------- 定时/增量检测 ---------------------------- #

    # 定时触发短语（中英）
    _SCHEDULE_PATTERNS = [
        r'每\s*两?\s*周', r'每\s*周[一二三四五六日天]?', r'每\s*个?月',
        r'每\s*[天日]', r'每\s*(\d+)\s*[天日]',
        r'定时', r'周期', r'定期',
        r'every\s*week', r'every\s*month', r'every\s*day',
        r'every\s*(\d+)\s*days?', r'weekly', r'biweekly', r'monthly', r'daily',
    ]

    def _detect_schedule(self, text: str) -> bool:
        """检测是否为定时任务（每周/每月/每两周/每天/定时/周期 等）。"""
        return any(re.search(p, text, re.IGNORECASE)
                   for p in self._SCHEDULE_PATTERNS)

    def _extract_schedule(self, text: str) -> Optional[str]:
        """
        规范化周期 token：daily / weekly / biweekly / monthly / every-Nd。
        特定词先于通用词；无明确周期但命中「定时/周期」→ 默认 weekly。
        """
        t = text.lower()
        if re.search(r'每\s*两\s*周|biweekly|fortnight', t):
            return "biweekly"
        if re.search(r'每\s*个?月|monthly|every\s*month', t):
            return "monthly"
        if re.search(r'每\s*周|weekly|every\s*week', t):
            return "weekly"
        if re.search(r'每\s*[天日]|daily|every\s*day', t):
            return "daily"
        m = re.search(r'每\s*(\d+)\s*[天日]|every\s*(\d+)\s*days?', t)
        if m:
            n = m.group(1) or m.group(2)
            return f"every-{n}d"
        if re.search(r'定时|周期|定期', t):
            return "weekly"  # 无明确周期 → 默认周
        return None

    def _has_explicit_time_range(self, text: str) -> bool:
        """是否含显式「近N周/月/年/不限」时间范围（区别于定时短语）。"""
        explicit = [r'近?\s*\d+\s*周', r'近?\s*\d+\s*个?月',
                    r'近?\s*\d+\s*年', r'不\s*限|all']
        return any(re.search(p, text, re.IGNORECASE) for p in explicit)

    def _schedule_default_window(self, schedule: Optional[str]
                                 ) -> tuple[Optional[datetime], datetime]:
        """定时模式的默认短窗口 = [now - 周期, now]（首次/展示用，pipeline 会用时间戳覆盖）。"""
        now = datetime.now()
        return now - schedule_interval(schedule), now

    def _identify_paper_types(self, text: str) -> List[str]:
        """识别文献类型"""
        paper_types = []

        for paper_type, keywords in self.paper_type_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    if paper_type not in paper_types:
                        paper_types.append(paper_type)
                    break

        # 默认包含期刊和会议
        return paper_types if paper_types else ['journal', 'conference']

    def _identify_filters(self, text: str) -> Dict[str, bool]:
        """识别筛选条件"""
        filters = {
            'highly_cited': False,
            'sci_ei': False,
            'core_journal': False,
            'latest_research': False,
        }

        text_lower = text.lower()

        for filter_name, keywords in self.filter_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    filters[filter_name] = True
                    break

        return filters


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='解析用户搜索意图')
    parser.add_argument('--input', type=str, required=True, help='用户输入')
    parser.add_argument('--output', type=str, help='输出JSON文件路径')

    args = parser.parse_args()

    # 创建解析器
    intent_parser = IntentParser()

    # 解析意图
    intent = intent_parser.parse(args.input)

    # 输出结果
    result = intent.to_dict()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
