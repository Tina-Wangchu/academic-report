#!/usr/bin/env python3
"""
输入验证工具模块
提供各种输入验证函数
"""

import re
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class InputValidator:
    """输入验证器"""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        验证邮箱地址格式

        Args:
            email: 待验证的邮箱地址

        Returns:
            (is_valid, error_message)
        """
        if not email:
            return False, "邮箱地址不能为空"

        email = email.strip()

        # 基本的邮箱格式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, f"邮箱地址格式不正确: {email}"

        # 检查常用邮箱域
        common_domains = ['gmail', 'outlook', 'yahoo', 'hotmail', 'qq', '163', '126', 'foxmail']
        domain = email.split('@')[-1].split('.')[0].lower()

        return True, ""

    @staticmethod
    def validate_time_range(time_range: str) -> Tuple[bool, str]:
        """
        验证时间范围参数

        Args:
            time_range: 时间范围字符串 (如 "1y", "3y", "unlimited", "2020-2023")

        Returns:
            (is_valid, error_message)
        """
        if not time_range:
            return True, "使用默认时间范围"  # 空值是允许的，会使用默认值

        time_range = time_range.strip().lower()

        # 相对时间格式
        relative_patterns = {
            r'^(\d+)y$': 'years',
            r'^(\d+)m$': 'months',
            r'^(\d+)d$': 'days',
            r'^(\d+)w$': 'weeks',
            r'^(\d+)h$': 'hours'
        }

        for pattern, unit in relative_patterns.items():
            if re.match(pattern, time_range):
                value = int(re.search(pattern, time_range).group(1))
                if value <= 0:
                    return False, f"{unit}数量必须大于0"
                return True, ""

        # 特殊值
        if time_range in ['unlimited', 'all', 'none', '']:
            return True, ""

        # 年份范围格式 (2020-2023)
        year_range_pattern = r'^(\d{4})-(\d{4})$'
        if re.match(year_range_pattern, time_range):
            start_year, end_year = map(int, re.search(year_range_pattern, time_range).groups())
            if start_year >= end_year:
                return False, f"起始年份必须小于结束年份: {start_year} >= {end_year}"
            return True, ""

        # 精确日期范围 (2020-01-01:2023-06-30)
        date_range_pattern = r'^(\d{4}-\d{2}-\d{2}):(\d{4}-\d{2}-\d{2})$'
        if re.match(date_range_pattern, time_range):
            # 这里可以添加更复杂的日期验证
            return True, ""

        return False, f"不支持的时间范围格式: {time_range}。支持的格式: 1y/3y/5y/10y/unlimited/YYYY-MM-DD:YYYY-MM-DD"

    @staticmethod
    def validate_max_results(max_results: Any) -> Tuple[bool, str]:
        """
        验证最大结果数

        Args:
            max_results: 最大结果数

        Returns:
            (is_valid, error_message)
        """
        try:
            max_results = int(max_results)
            if max_results < 1:
                return False, "文献数量必须至少为1"
            if max_results > 100:
                return False, "文献数量建议不超过100，过多会影响处理速度"
            if max_results > 50:
                return True, "⚠️ 文献数量较多（>50），可能会影响邮件发送"
            return True, ""
        except (ValueError, TypeError):
            return False, f"文献数量必须是数字: {max_results}"

    @staticmethod
    def validate_topic(topic: str) -> Tuple[bool, str]:
        """
        验证研究主题

        Args:
            topic: 研究主题

        Returns:
            (is_valid, error_message)
        """
        if not topic or not topic.strip():
            return False, "研究主题不能为空"

        topic = topic.strip()
        if len(topic) < 3:
            return False, "研究主题太短，请提供更具体的描述"
        if len(topic) > 500:
            return False, "研究主题太长，请简化到500字符以内"

        return True, ""

    @staticmethod
    def validate_domain(domain: str) -> Tuple[bool, str]:
        """
        验证研究领域

        Args:
            domain: 研究领域

        Returns:
            (is_valid, error_message)
        """
        valid_domains = ['general', 'ai', 'statistics', 'finance', 'cs', 'physics', 'biology', 'medicine']

        if not domain:
            return True, "使用默认领域 (general)"  # 空值允许，会使用默认值

        domain = domain.strip().lower()

        if domain not in valid_domains:
            # 检查是否是有效的域别名
            domain_aliases = {
                'artificial intelligence': 'ai',
                'machine learning': 'ai',
                'ml': 'ai',
                'stat': 'statistics',
                'stats': 'statistics',
                'computer science': 'cs',
                'comp sci': 'cs',
                'financial': 'finance',
                'economics': 'finance',
                'physical': 'physics',
                'bio': 'biology',
                'medical': 'medicine'
            }

            domain = domain_aliases.get(domain, domain)
            if domain in valid_domains:
                return True, ""

            return False, f"未知的研究领域: {domain}。支持的领域: {', '.join(valid_domains)}"

        return True, ""

    @staticmethod
    def validate_sort_by(sort_by: str) -> Tuple[bool, str]:
        """
        验证排序方式

        Args:
            sort_by: 排序方式

        Returns:
            (is_valid, error_message)
        """
        valid_sort_methods = ['relevance', 'citation_count', 'publish_date']

        if not sort_by:
            return True, "使用默认排序 (relevance)"

        sort_by = sort_by.strip().lower()

        if sort_by not in valid_sort_methods:
            return False, f"不支持的排序方式: {sort_by}。支持的排序: {', '.join(valid_sort_methods)}"

        return True, ""

    @staticmethod
    def validate_schedule_format(schedule: str) -> Tuple[bool, str]:
        """
        验证定时任务调度格式

        Args:
            schedule: cron表达式或简单间隔

        Returns:
            (is_valid, error_message)
        """
        if not schedule:
            return False, "调度时间不能为空"

        schedule = schedule.strip()

        # 简单间隔格式 (30m, 2h, 1d)
        simple_patterns = {
            r'^(\d+)m$': 'minutes',
            r'^(\d+)h$': 'hours',
            r'^(\d+)d$': 'days'
        }

        for pattern, unit in simple_patterns.items():
            if re.match(pattern, schedule):
                value = int(re.search(pattern, schedule).group(1))
                if value <= 0:
                    return False, f"{unit}数量必须大于0"

                # 检查合理性
                if unit == 'minutes' and value < 30:
                    return False, "分钟间隔建议至少30分钟，避免过于频繁"
                if unit == 'hours' and value > 720:
                    return False, "小时间隔建议不超过720小时（30天）"
                if unit == 'days' and value > 365:
                    return False, "天数间隔建议不超过365天"

                return True, ""

        # Cron格式 (分 时 日 月 周)
        cron_pattern = r'^(\*|[0-5]|[0-9\-*/\*|[0-9\*/\*|[0-9\*/\*|[0-9\*/\*\/\*|[0-9\-/\*])$'
        if re.match(cron_pattern, schedule):
            return True, ""

        return False, f"不支持的调度格式: {schedule}。支持简单间隔(如30m/2h/1d)或cron表达式"

    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        验证文件路径是否存在

        Args:
            file_path: 文件路径

        Returns:
            (is_valid, error_message)
        """
        if not file_path:
            return True, "文件路径为空（可选参数）"

        file_path = file_path.strip()

        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"

        # 如果是文件，检查是否可读
        if os.path.isfile(file_path):
            if not os.access(file_path, os.R_OK):
                return False, f"文件无法读取: {file_path}"

        return True, ""

    @staticmethod
    def validate_credentials_present() -> Tuple[bool, List[str]]:
        """
        验证必需的凭据是否配置

        Returns:
            (is_configured, missing_credentials)
        """
        required_creds = {
            'GMAIL_ADDRESS': 'Gmail邮箱地址',
            'GMAIL_APP_PASSWORD': 'Gmail应用专用密码'
        }

        missing = []
        for cred_name, cred_desc in required_creds.items():
            if not os.environ.get(cred_name):
                missing.append(f"{cred_desc} (环境变量 {cred_name})")

        if missing:
            return False, missing

        # 验证Gmail地址格式
        gmail_address = os.environ.get('GMAIL_ADDRESS', '')
        is_valid, error = InputValidator.validate_email(gmail_address)
        if not is_valid:
            return False, [f"Gmail地址格式错误: {error}"]

        return True, []

    @staticmethod
    def validate_complete_params(params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证完整的参数集

        Args:
            params: 参数字典

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # 验证主题
        if 'topic' in params:
            is_valid, error = InputValidator.validate_topic(params['topic'])
            if not is_valid:
                errors.append(f"主题验证失败: {error}")

        # 验证邮箱
        if 'recipients' in params:
            if not params['recipients']:
                errors.append("收件人列表不能为空")
            else:
                for recipient in params['recipients']:
                    is_valid, error = InputValidator.validate_email(recipient)
                    if not is_valid:
                        errors.append(f"收件人邮箱错误: {error}")

        # 验证时间范围
        if 'time_range' in params:
            is_valid, error = InputValidator.validate_time_range(params['time_range'])
            if not is_valid:
                errors.append(f"时间范围错误: {error}")

        # 验证最大结果数
        if 'max_results' in params:
            is_valid, error = InputValidator.validate_max_results(params['max_results'])
            if not is_valid:
                errors.append(f"文献数量错误: {error}")

        # 验证领域
        if 'domain' in params:
            is_valid, error = InputValidator.validate_domain(params['domain'])
            if not is_valid:
                errors.append(f"领域错误: {error}")

        # 验证排序方式
        if 'sort_by' in params:
            is_valid, error = InputValidator.validate_sort_by(params['sort_by'])
            if not is_valid:
                errors.append(f"排序方式错误: {error}")

        return (len(errors) == 0, errors)


def validate_user_input(user_input: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    验证用户输入并返回规范化参数

    Args:
        user_input: 原始用户输入

    Returns:
        (is_valid, errors, normalized_params)
    """
    validator = InputValidator()
    errors = []
    normalized = user_input.copy()

    # 应用默认值
    defaults = {
        'time_range': '1y',
        'max_results': 10,
        'domain': 'general',
        'sort_by': 'citation_count',
        'language': 'bilingual',
        'output_format': 'json',
        'report_format': 'pdf',
        'email_body_type': 'html'
    }

    # 应用默认值
    for key, default_value in defaults.items():
        if key not in normalized or not normalized[key]:
            normalized[key] = default_value

    # 验证主题
    if 'topic' in normalized:
        is_valid, error = validator.validate_topic(normalized['topic'])
        if not is_valid:
            errors.append(error)

    # 验证邮箱
    if 'recipients' in normalized and normalized['recipients']:
        if not normalized['recipients']:
            errors.append("收件人列表不能为空")
        else:
            valid_recipients = []
            for recipient in normalized['recipients']:
                is_valid, error = validator.validate_email(recipient)
                if is_valid:
                    valid_recipients.append(recipient)
                else:
                    errors.append(f"收件人邮箱验证失败: {error}")
            normalized['recipients'] = valid_recipients

    # 验证其他参数
    validation_methods = [
        ('time_range', validator.validate_time_range),
        ('max_results', validator.validate_max_results),
        ('domain', validator.validate_domain),
        ('sort_by', validator.validate_sort_by)
    ]

    for param, validator_method in validation_methods:
        if param in normalized:
            is_valid, error = validator_method(normalized[param])
            if not is_valid:
                errors.append(error)

    return (len(errors) == 0, errors, normalized)