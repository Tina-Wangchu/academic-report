#!/usr/bin/env python3
"""
配置管理模块
提供配置文件的加载、合并、验证和管理功能
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from utils.validators import InputValidator
from utils.error_handler import ConfigurationError, get_error_handler


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录路径
        """
        if config_dir is None:
            # 默认配置目录为技能目录下的config文件夹
            # scripts/config_manager.py -> scripts/ -> paper-email-service/
            skill_dir = Path(__file__).parent.parent
            config_dir = skill_dir / 'config'

        self.config_dir = Path(config_dir)
        self.default_config_path = self.config_dir / 'default_config.yaml'
        self.user_config_path = self.config_dir / 'user_config.yaml'

        self.config_cache = {}
        self.error_handler = get_error_handler()

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self, config_type: str = 'merged') -> Dict[str, Any]:
        """
        加载配置

        Args:
            config_type: 配置类型 ('default', 'user', 'merged', 'preset')

        Returns:
            配置字典
        """
        try:
            if config_type == 'default':
                return self._load_default_config()
            elif config_type == 'user':
                return self._load_user_config()
            elif config_type == 'merged':
                return self._load_merged_config()
            elif config_type == 'preset':
                return self._load_preset_config()
            else:
                raise ConfigurationError(f"未知的配置类型: {config_type}")

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'config_type': config_type})
            raise ConfigurationError(f"加载配置失败: {error_info['error_message']}")

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        if not self.default_config_path.exists():
            raise ConfigurationError(f"默认配置文件不存在: {self.default_config_path}")

        with open(self.default_config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _load_user_config(self) -> Dict[str, Any]:
        """加载用户配置"""
        if not self.user_config_path.exists():
            # 用户配置不存在，返回空配置
            return {}

        with open(self.user_config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _load_merged_config(self) -> Dict[str, Any]:
        """
        加载合并后的配置

        优先级：用户配置 > 默认配置 > 硬编码默认值
        """
        default_config = self._load_default_config()
        user_config = self._load_user_config()

        # 递归合并配置
        merged_config = self._deep_merge_configs(default_config, user_config)

        # 添加环境变量覆盖
        self._apply_env_overrides(merged_config)

        return merged_config

    def _load_preset_config(self, preset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        加载预设配置

        Args:
            preset_name: 预设名称，如果为None则返回所有预设
        """
        merged_config = self._load_merged_config()
        presets = merged_config.get('presets', {})

        if preset_name is None:
            return presets

        if preset_name not in presets:
            available_presets = list(presets.keys())
            raise ConfigurationError(
                f"预设任务不存在: {preset_name}",
                {'available_presets': available_presets}
            )

        return presets[preset_name]

    def _deep_merge_configs(self, default_config: Dict[str, Any],
                          user_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个配置字典

        Args:
            default_config: 默认配置
            user_config: 用户配置

        Returns:
            合并后的配置
        """
        merged = default_config.copy()

        for key, user_value in user_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(user_value, dict):
                # 递归合并嵌套字典
                merged[key] = self._deep_merge_configs(merged[key], user_value)
            else:
                # 用户配置覆盖默认配置
                merged[key] = user_value

        return merged

    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """
        应用环境变量覆盖

        Args:
            config: 配置字典
        """
        # Gmail相关环境变量
        if 'GMAIL_ADDRESS' in os.environ:
            if 'email_defaults' not in config:
                config['email_defaults'] = {}
            config['email_defaults']['from_address'] = os.environ['GMAIL_ADDRESS']

        if 'GMAIL_APP_PASSWORD' in os.environ:
            # 应用专用密码不存储在配置文件中，只验证存在性
            config['email_defaults']['auth_configured'] = True

        # 代理设置
        if 'SMTP_SOCKS_PROXY' in os.environ:
            if 'email_defaults' not in config:
                config['email_defaults'] = {}
            config['email_defaults']['proxy'] = os.environ['SMTP_SOCKS_PROXY']

        # API密钥
        if 'SEMANTIC_SCHOLAR_API_KEY' in os.environ:
            if 'search_defaults' not in config:
                config['search_defaults'] = {}
            config['search_defaults']['api_key'] = os.environ['SEMANTIC_SCHOLAR_API_KEY']

    def save_user_config(self, config: Dict[str, Any]) -> None:
        """
        保存用户配置

        Args:
            config: 用户配置字典
        """
        try:
            # 验证配置
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                raise ConfigurationError(
                    f"配置验证失败: {', '.join(errors)}",
                    {'validation_errors': errors}
                )

            # 保存配置
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, allow_unicode=True, default_flow_style=False)

            # 清除缓存
            self.config_cache.clear()

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'operation': 'save_user_config'})
            raise ConfigurationError(f"保存用户配置失败: {error_info['error_message']}")

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证配置

        Args:
            config: 配置字典

        Returns:
            (is_valid, error_messages)
        """
        errors = []
        validator = InputValidator()

        # 验证服务配置
        if 'service' in config:
            service_config = config['service']
            if 'name' not in service_config:
                errors.append("服务配置缺少name字段")

        # 验证搜索默认配置
        if 'search_defaults' in config:
            search_config = config['search_defaults']
            is_valid, error = validator.validate_time_range(search_config.get('time_range', ''))
            if not is_valid:
                errors.append(f"时间范围配置错误: {error}")

            is_valid, error = validator.validate_max_results(search_config.get('max_results', 10))
            if not is_valid:
                errors.append(f"最大结果数配置错误: {error}")

        # 验证邮件配置
        if 'email_defaults' in config:
            email_config = config['email_defaults']
            if 'from_address' in email_config:
                is_valid, error = validator.validate_email(email_config['from_address'])
                if not is_valid:
                    errors.append(f"发件人地址错误: {error}")

        # 验证环境变量
        is_configured, missing_creds = validator.validate_credentials_present()
        if not is_configured:
            errors.append(f"缺少必需的环境变量: {', '.join(missing_creds)}")

        return (len(errors) == 0, errors)

    def get_default_params(self) -> Dict[str, Any]:
        """
        获取默认参数

        Returns:
            默认参数字典
        """
        merged_config = self._load_merged_config()

        defaults = {}

        # 搜索默认参数
        if 'search_defaults' in merged_config:
            search_defaults = merged_config['search_defaults']
            defaults.update({
                'time_range': search_defaults.get('time_range', '1y'),
                'max_results': search_defaults.get('max_results', 10),
                'domain': search_defaults.get('domain', 'general'),
                'sort_by': search_defaults.get('sort_by', 'citation_count'),
                'output_format': search_defaults.get('output_format', 'json'),
                'language': search_defaults.get('language', 'bilingual')
            })

        # 报告默认参数
        if 'report_defaults' in merged_config:
            report_defaults = merged_config['report_defaults']
            defaults.update({
                'report_format': report_defaults.get('format', 'pdf'),
                'include_analysis': report_defaults.get('include_analysis', True),
                'include_references': report_defaults.get('include_references', True)
            })

        # 邮件默认参数
        if 'email_defaults' in merged_config:
            email_defaults = merged_config['email_defaults']
            defaults.update({
                'email_body_type': email_defaults.get('body_type', 'html'),
                'email_subject_template': email_defaults.get('subject_template', ''),
                'from_name': email_defaults.get('from_name', 'Hermes 学术助手')
            })

        # 默认收件人
        if 'default_recipient' in merged_config:
            recipient = merged_config['default_recipient']
            defaults['recipients'] = [recipient.get('email', '')]

        return defaults

    def get_preset_tasks(self) -> Dict[str, Any]:
        """
        获取所有预设任务

        Returns:
            预设任务字典
        """
        merged_config = self._load_merged_config()
        return merged_config.get('presets', {})

    def get_preset_task(self, preset_name: str) -> Dict[str, Any]:
        """
        获取指定预设任务

        Args:
            preset_name: 预设名称

        Returns:
            预设任务配置
        """
        presets = self.get_preset_tasks()

        if preset_name not in presets:
            available = list(presets.keys())
            raise ConfigurationError(
                f"预设任务 '{preset_name}' 不存在",
                {'available_presets': available}
            )

        return presets[preset_name]

    def create_custom_task(self, task_name: str, task_config: Dict[str, Any]) -> None:
        """
        创建自定义任务

        Args:
            task_name: 任务名称
            task_config: 任务配置
        """
        try:
            # 加载用户配置
            user_config = self._load_user_config()

            # 确保custom_tasks字段存在
            if 'custom_tasks' not in user_config:
                user_config['custom_tasks'] = []

            # 添加任务
            task_config['id'] = task_name.lower().replace(' ', '_')
            task_config['name'] = task_name
            task_config['created_at'] = datetime.now().isoformat()
            task_config['enabled'] = task_config.get('enabled', True)

            user_config['custom_tasks'].append(task_config)

            # 保存配置
            self.save_user_config(user_config)

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'task_name': task_name})
            raise ConfigurationError(f"创建自定义任务失败: {error_info['error_message']}")

    def get_custom_tasks(self) -> List[Dict[str, Any]]:
        """
        获取所有自定义任务

        Returns:
            自定义任务列表
        """
        user_config = self._load_user_config()
        return user_config.get('custom_tasks', [])

    def get_task_config(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定任务配置

        Args:
            task_id: 任务ID

        Returns:
            任务配置，如果不存在则返回None
        """
        # 首先在预设任务中查找
        try:
            preset_task = self.get_preset_task(task_id)
            return preset_task
        except ConfigurationError:
            pass

        # 然后在自定义任务中查找
        custom_tasks = self.get_custom_tasks()
        for task in custom_tasks:
            if task.get('id') == task_id:
                return task

        return None

    def update_default_recipient(self, email: str, name: Optional[str] = None) -> None:
        """
        更新默认收件人

        Args:
            email: 邮箱地址
            name: 收件人姓名（可选）
        """
        try:
            # 验证邮箱
            validator = InputValidator()
            is_valid, error = validator.validate_email(email)
            if not is_valid:
                raise ConfigurationError(f"邮箱地址无效: {error}")

            # 加载用户配置
            user_config = self._load_user_config()

            # 更新默认收件人
            if 'default_recipient' not in user_config:
                user_config['default_recipient'] = {}

            user_config['default_recipient']['email'] = email
            if name:
                user_config['default_recipient']['name'] = name

            # 保存配置
            self.save_user_config(user_config)

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'email': email})
            raise ConfigurationError(f"更新默认收件人失败: {error_info['error_message']}")

    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key_path: 配置键路径，支持点分隔的路径 (如 'search_defaults.max_results')
            default: 默认值

        Returns:
            配置值，如果不存在则返回默认值
        """
        try:
            merged_config = self._load_merged_config()
            keys = key_path.split('.')

            value = merged_config
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

        except Exception:
            return default

    def set_config_value(self, key_path: str, value: Any) -> None:
        """
        设置配置值（只影响内存中的配置）

        Args:
            key_path: 配置键路径
            value: 要设置的值
        """
        merged_config = self._load_merged_config()
        keys = key_path.split('.')

        config = merged_config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

        # 缓存配置
        self.config_cache['merged'] = merged_config


class ConfigBuilder:
    """配置构建器，用于构建任务配置"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config = {}

    def with_topic(self, topic: str) -> 'ConfigBuilder':
        """设置研究主题"""
        self.config['topic'] = topic
        return self

    def with_time_range(self, time_range: str) -> 'ConfigBuilder':
        """设置时间范围"""
        self.config['time_range'] = time_range
        return self

    def with_max_results(self, max_results: int) -> 'ConfigBuilder':
        """设置最大结果数"""
        self.config['max_results'] = max_results
        return self

    def with_domain(self, domain: str) -> 'ConfigBuilder':
        """设置研究领域"""
        self.config['domain'] = domain
        return self

    def with_recipients(self, recipients: List[str]) -> 'ConfigBuilder':
        """设置收件人列表"""
        self.config['recipients'] = recipients
        return self

    def with_schedule(self, schedule: str) -> 'ConfigBuilder':
        """设置调度时间"""
        self.config['schedule'] = schedule
        return self

    def with_keywords(self, keywords: str) -> 'ConfigBuilder':
        """设置关键词"""
        self.config['keywords'] = keywords
        return self

    def with_preset(self, preset_name: str) -> 'ConfigBuilder':
        """基于预设配置构建"""
        preset_config = self.config_manager.get_preset_task(preset_name)
        self.config.update(preset_config.get('config', {}))
        self.config['schedule'] = preset_config.get('schedule', '')
        return self

    def build(self) -> Dict[str, Any]:
        """
        构建最终配置

        Returns:
            合并后的配置字典
        """
        # 合并默认参数
        default_params = self.config_manager.get_default_params()
        final_config = default_params.copy()
        final_config.update(self.config)

        return final_config


# 便捷函数
def get_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """获取配置管理器实例"""
    return ConfigManager(config_dir)


def load_config(config_type: str = 'merged') -> Dict[str, Any]:
    """加载配置的便捷函数"""
    manager = get_config_manager()
    return manager.load_config(config_type)


if __name__ == "__main__":
    # 测试代码
    try:
        manager = get_config_manager()

        print("Testing config loading:")
        config = manager.load_config('default')
        print(json.dumps(config, indent=2, ensure_ascii=False))

        print("\nTesting default params:")
        defaults = manager.get_default_params()
        print(json.dumps(defaults, indent=2, ensure_ascii=False))

        print("\nTesting preset tasks:")
        presets = manager.get_preset_tasks()
        print(json.dumps(presets, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}")