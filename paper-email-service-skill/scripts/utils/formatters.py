#!/usr/bin/env python3
"""
格式化工具模块
提供各种数据格式化功能
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class DataFormatter:
    """数据格式化工具类"""

    @staticmethod
    def format_paper_data(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化论文数据，确保字段一致性和完整性

        Args:
            papers: 原始论文数据列表

        Returns:
            格式化后的论文数据列表
        """
        formatted_papers = []

        for paper in papers:
            formatted_paper = {
                'title': paper.get('title', 'Unknown Title'),
                'authors': paper.get('authors', []),
                'year': paper.get('year', 'Unknown'),
                'abstract': paper.get('abstract', 'No abstract available'),
                'venue': paper.get('venue', 'Unknown Venue'),
                'citation_count': paper.get('citation_count', 0),
                'url': paper.get('url', ''),
                'pdf_url': paper.get('pdf_url', ''),
                'keywords': paper.get('keywords', []),
                'doi': paper.get('doi', ''),
                # Fix source field fallback chain: source -> journal -> arXiv -> venue
                'source': (paper.get('source') or
                          paper.get('journal') or
                          paper.get('arXiv') or
                          paper.get('venue', 'Unknown'))
            }

            # 确保作者字段为字符串列表
            if isinstance(formatted_paper['authors'], str):
                formatted_paper['authors'] = [formatted_paper['authors']]
            elif not isinstance(formatted_paper['authors'], list):
                formatted_paper['authors'] = []

            # 确保年份为整数
            try:
                formatted_paper['year'] = int(formatted_paper['year'])
            except (ValueError, TypeError):
                formatted_paper['year'] = 0

            # 确保引用数为整数
            try:
                formatted_paper['citation_count'] = int(formatted_paper['citation_count'])
            except (ValueError, TypeError):
                formatted_paper['citation_count'] = 0

            # 限制摘要长度
            max_abstract_length = 1000
            if len(formatted_paper['abstract']) > max_abstract_length:
                formatted_paper['abstract'] = formatted_paper['abstract'][:max_abstract_length] + '...'

            formatted_papers.append(formatted_paper)

        return formatted_papers

    @staticmethod
    def format_email_subject(template: str, context: Dict[str, Any]) -> str:
        """
        格式化邮件主题

        Args:
            template: 主题模板字符串
            context: 上下文数据

        Returns:
            格式化后的主题字符串
        """
        # 格式化日期
        if '{date}' in template or '{timestamp}' in template:
            date_str = datetime.now().strftime('%Y-%m-%d')
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            template = template.format(date=date_str, timestamp=timestamp_str, **context)

        # 替换其他变量
        template = template.format(**context)

        return template

    @staticmethod
    def format_email_body(template: str, context: Dict[str, Any], papers: List[Dict[str, Any]]) -> str:
        """
        格式化邮件正文

        Args:
            template: 邮件模板字符串
            context: 上下文数据
            papers: 论文数据列表

        Returns:
            格式化后的邮件正文
        """
        # 添加论文统计信息
        if '{papers_count}' in template:
            context['papers_count'] = len(papers)

        # 添加最新论文信息
        if '{latest_papers}' in template:
            latest_papers = papers[:3] if len(papers) > 3 else papers
            latest_papers_text = "\n\n".join([
                f"📄 {paper['title']}\n"
                f"✍️ {', '.join(paper['authors'][:3])}{'等' if len(paper['authors']) > 3 else ''}\n"
                f"📅 {paper['year']} • {paper['venue']}"
                for paper in latest_papers
            ])
            context['latest_papers'] = latest_papers_text

        # 格式化模板
        try:
            body = template.format(**context)
        except KeyError as e:
            # 缺少必需的变量，使用基本模板
            body = f"""
学术论文报告生成完成

📊 检索结果：
- 论文数量：{len(papers)}篇
- 时间范围：{context.get('time_range', '未知')}
- 研究主题：{context.get('topic', '未知')}

📧 报告已作为附件发送，请查收。

此邮件由 Hermes 学术助手自动发送。
"""

        return body

    @staticmethod
    def format_filename(template: str, context: Dict[str, Any], extension: str = 'pdf') -> str:
        """
        格式化文件名

        Args:
            template: 文件名模板
            context: 上下文数据
            extension: 文件扩展名

        Returns:
            格式化后的文件名
        """
        # 清理文件名中的非法字符
        sanitize_pattern = r'[<>:"/\\|?*]'
        template = re.sub(sanitize_pattern, '', template)

        # 限制长度
        max_length = 100
        if len(template) > max_length:
            template = template[:max_length]

        # 添加时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{template}_{timestamp}.{extension}"

        return filename

    @staticmethod
    def format_error_message(error: Dict[str, Any]) -> str:
        """
        格式化错误消息为用户友好的文本

        Args:
            error: 错误信息字典

        Returns:
            格式化的错误消息
        """
        lines = [
            f"❌ {error.get('error_type', 'Error')}: {error.get('error_message', 'Unknown error')}"
        ]

        if error.get('solutions'):
            lines.append("\n💡 建议解决方案:")
            for i, solution in enumerate(error['solutions'], 1):
                lines.append(f"  {i}. {solution}")

        return "\n".join(lines)

    @staticmethod
    def format_progress_message(step: int, total_steps: int, message: str,
                                details: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化进度消息

        Args:
            step: 当前步骤
            total_steps: 总步骤数
            message: 进度消息
            details: 详细信息

        Returns:
            格式化的进度消息
        """
        progress_emoji = ['🔄', '📊', '📧', '✅']
        emoji = progress_emoji[min(step, len(progress_emoji) - 1)]

        lines = [
            f"{emoji} 步骤{step}/{total_steps}: {message}"
        ]

        if details:
            for key, value in details.items():
                if value is not None and value != '':
                    lines.append(f"   {key}: {value}")

        return "\n".join(lines)


class ReportFormatter:
    """报告格式化工具类"""

    @staticmethod
    def generate_summary(papers: List[Dict[str, Any]], topic: str,
                        time_range: str) -> Dict[str, Any]:
        """
        生成报告摘要信息

        Args:
            papers: 论文数据列表
            topic: 研究主题
            time_range: 时间范围

        Returns:
            摘要信息字典
        """
        if not papers:
            return {
                'total_papers': 0,
                'topic': topic,
                'time_range': time_range,
                'message': '未找到相关论文'
            }

        # 统计年份分布
        year_counts = {}
        for paper in papers:
            year = paper.get('year', 0)
            if year > 0:
                year_counts[year] = year_counts.get(year, 0) + 1

        # 统计来源分布
        source_counts = {}
        for paper in papers:
            source = paper.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        # 找出高引用论文
        high_citation_papers = [p for p in papers if p.get('citation_count', 0) > 50]
        high_citation_papers.sort(key=lambda x: x.get('citation_count', 0), reverse=True)

        # 最新论文
        recent_papers = sorted(papers, key=lambda x: x.get('year', 0), reverse=True)[:5]

        return {
            'total_papers': len(papers),
            'topic': topic,
            'time_range': time_range,
            'year_distribution': dict(sorted(year_counts.items(), reverse=True)),
            'source_distribution': source_counts,
            'high_citation_papers': len(high_citation_papers),
            'top_cited_paper': high_citation_papers[0] if high_citation_papers else None,
            'recent_papers': recent_papers,
            'average_citations': sum(p.get('citation_count', 0) for p in papers) / len(papers)
        }

    @staticmethod
    def extract_keywords(papers: List[Dict[str, Any]], top_n: int = 10) -> List[str]:
        """
        提取高频关键词

        Args:
            papers: 论文数据列表
            top_n: 返回前N个关键词

        Returns:
            关键词列表
        """
        keyword_counts = {}

        for paper in papers:
            keywords = paper.get('keywords', [])
            if isinstance(keywords, list):
                for keyword in keywords:
                    keyword_lower = keyword.lower().strip()
                    if keyword_lower:
                        keyword_counts[keyword_lower] = keyword_counts.get(keyword_lower, 0) + 1

        # 排序并返回前N个
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:top_n]]

    @staticmethod
    def generate_insights(papers: List[Dict[str, Any]], topic: str) -> List[str]:
        """
        生成研究洞察

        Args:
            papers: 论文数据列表
            topic: 研究主题

        Returns:
            洞察列表
        """
        insights = []

        if not papers:
            return ["未找到相关论文，无法生成洞察"]

        # 年份趋势
        year_counts = {}
        for paper in papers:
            year = paper.get('year', 0)
            if year > 0:
                year_counts[year] = year_counts.get(year, 0) + 1

        if year_counts:
            latest_year = max(year_counts.keys())
            latest_count = year_counts[latest_year]
            insights.append(f"最新趋势：{latest_year}年有{latest_count}篇相关论文，表明该领域研究活跃")

        # 引用分析
        high_citation_papers = [p for p in papers if p.get('citation_count', 0) > 100]
        if high_citation_papers:
            insights.append(f"高影响力：发现{len(high_citation_papers)}篇高引用论文（>100次），说明该领域有重要基础研究")

        # 来源分析
        source_counts = {}
        for paper in papers:
            source = paper.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        if source_counts:
            top_source = max(source_counts.items(), key=lambda x: x[1])
            insights.append(f"主要来源：{top_source[0]}贡献了{top_source[1]}篇论文，是该领域的主要研究平台")

        # 作者分析
        author_counts = {}
        for paper in papers:
            authors = paper.get('authors', [])
            if isinstance(authors, list):
                for author in authors[:3]:  # 只考虑前三位作者
                    author_counts[author] = author_counts.get(author, 0) + 1

        if author_counts:
            top_author = max(author_counts.items(), key=lambda x: x[1])
            if top_author[1] >= 2:
                insights.append(f"活跃研究者：{top_author[0]}发表了{top_author[1]}篇论文，是该领域的活跃研究者")

        return insights


class ConfigFormatter:
    """配置格式化工具类"""

    @staticmethod
    def format_config_display(config: Dict[str, Any]) -> str:
        """
        格式化配置信息用于显示

        Args:
            config: 配置字典

        Returns:
            格式化的配置文本
        """
        lines = ["📋 当前配置：", ""]

        # 主要配置项
        main_configs = [
            ('研究主题', config.get('topic')),
            ('时间范围', config.get('time_range')),
            ('文献数量', config.get('max_results')),
            ('研究领域', config.get('domain')),
            ('排序方式', config.get('sort_by')),
            ('收件邮箱', config.get('recipients')),
            ('报告格式', config.get('report_format'))
        ]

        for label, value in main_configs:
            if value is not None:
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                lines.append(f"- {label}：{value}")

        return "\n".join(lines)

    @staticmethod
    def format_task_display(task_config: Dict[str, Any]) -> str:
        """
        格式化任务配置用于显示

        Args:
            task_config: 任务配置字典

        Returns:
            格式化的任务配置文本
        """
        lines = ["📅 定时任务配置预览：", ""]

        # 调度信息
        if 'schedule' in task_config:
            lines.append("⏰ 调度信息：")
            lines.append(f"- 执行时间：{task_config['schedule']}")

        # 检索配置
        if 'search_params' in task_config:
            search_params = task_config['search_params']
            lines.append("\n📚 检索配置：")
            lines.append(f"- 主题：{search_params.get('topic', '未设置')}")
            lines.append(f"- 时间范围：{search_params.get('time_range', '未设置')}")
            lines.append(f"- 文献数量：{search_params.get('max_results', '未设置')}")

        # 邮件配置
        if 'email_params' in task_config:
            email_params = task_config['email_params']
            lines.append("\n📧 邮件配置：")
            lines.append(f"- 收件人：{email_params.get('recipients', '未设置')}")
            lines.append(f"- 主题模板：{email_params.get('subject_template', '未设置')}")

        return "\n".join(lines)


class JSONFormatter:
    """JSON格式化工具类"""

    @staticmethod
    def save_json(data: Any, file_path: str, indent: int = 2) -> None:
        """
        保存数据为JSON文件

        Args:
            data: 要保存的数据
            file_path: 文件路径
            indent: 缩进空格数
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    @staticmethod
    def load_json(file_path: str) -> Any:
        """
        从JSON文件加载数据

        Args:
            file_path: 文件路径

        Returns:
            加载的数据
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def format_json_output(data: Any, compact: bool = False) -> str:
        """
        格式化JSON输出

        Args:
            data: 要格式化的数据
            compact: 是否使用紧凑格式

        Returns:
            格式化的JSON字符串
        """
        if compact:
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        else:
            return json.dumps(data, ensure_ascii=False, indent=2)


# 便捷函数
def format_paper_data(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """格式化论文数据的便捷函数"""
    return DataFormatter.format_paper_data(papers)


def generate_report_summary(papers: List[Dict[str, Any]], topic: str,
                           time_range: str) -> Dict[str, Any]:
    """生成报告摘要的便捷函数"""
    return ReportFormatter.generate_summary(papers, topic, time_range)


def format_config_display(config: Dict[str, Any]) -> str:
    """格式化配置显示的便捷函数"""
    return ConfigFormatter.format_config_display(config)


if __name__ == "__main__":
    # 测试代码
    test_papers = [
        {
            'title': 'Test Paper 1',
            'authors': ['Author 1', 'Author 2'],
            'year': 2023,
            'abstract': 'This is a test abstract.',
            'venue': 'Test Journal',
            'citation_count': 100,
            'keywords': ['machine learning', 'AI', 'deep learning'],
            'source': 'arXiv'
        },
        {
            'title': 'Test Paper 2',
            'authors': ['Author 3'],
            'year': 2022,
            'abstract': 'Another test abstract.',
            'venue': 'Test Conference',
            'citation_count': 50,
            'keywords': ['statistics', 'data analysis'],
            'source': 'Semantic Scholar'
        }
    ]

    print("Testing paper data formatting:")
    formatted = DataFormatter.format_paper_data(test_papers)
    print(DataFormatter.format_filename("test_report", {'topic': 'AI'}))
    print("\nTesting summary generation:")
    summary = ReportFormatter.generate_summary(formatted, "AI", "1y")
    print(json.dumps(summary, indent=2, ensure_ascii=False))