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

from utils import SearchIntent, parse_date_range
from config_manager import get_config_manager

logger = logging.getLogger(__name__)


class IntentParser:
    """用户意图解析器"""

    def __init__(self):
        """初始化解析器"""
        # 默认值统一来自 .env（config_manager），脚本内不再硬编码默认
        self.config = get_config_manager()
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

        # 提取时间范围（默认来自 .env DEFAULT_TIME_RANGE）
        time_range_text = self._extract_time_range(user_input)
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
        ]

        for pattern in instruction_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        query = text.strip()
        return query if query else self.config.get_default_query()  # 默认查询（来自 .env）

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
        # 检查语言关键词（用户显式说"中文/英文/双语"时用对应语种）
        language_patterns = {
            'en': [r'\benglish\b', r'英文', r'英语'],
            'zh': [r'\bchinese\b', r'中文', r'汉语'],
            'bilingual': [r'双语', r'bilingual', r'中英'],
        }

        for lang, patterns in language_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return lang

        # 未识别到关键词 → 用 .env 的 DEFAULT_LANGUAGE（不再凭"是否含中文"猜测）
        return self.config.get_default_language()

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

        # 默认时间范围来自 .env（DEFAULT_TIME_RANGE，如 3y / 近3年 / 1y / all）
        return self.config.get_default_time_range()

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
