#!/usr/bin/env python3
"""
定时任务调度器
负责管理和执行定时任务
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# 添加项目根目录到路径
# scripts/task_scheduler.py -> scripts/ -> paper-email-service/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config_manager import ConfigManager
from workflow_executor import WorkflowExecutor
from utils.formatters import ConfigFormatter
from utils.error_handler import get_error_handler, setup_error_handling


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化任务调度器

        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        self.workflow_executor = WorkflowExecutor(self.config_manager)
        self.error_handler = get_error_handler()

        # 设置日志
        self._setup_logging()

        # 任务执行历史
        self.execution_history = []

    def _setup_logging(self):
        """设置日志系统"""
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / 'scheduler.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)

    def get_all_tasks(self) -> Dict[str, Any]:
        """
        获取所有任务（预设任务 + 自定义任务）

        Returns:
            任务字典
        """
        try:
            all_tasks = {}

            # 获取预设任务
            presets = self.config_manager.get_preset_tasks()
            for task_id, task_config in presets.items():
                all_tasks[task_id] = {
                    'id': task_id,
                    'name': task_config.get('name', task_id),
                    'type': 'preset',
                    'schedule': task_config.get('schedule', ''),
                    'description': task_config.get('description', ''),
                    'enabled': task_config.get('enabled', True),
                    'config': task_config.get('config', {})
                }

            # 获取自定义任务
            custom_tasks = self.config_manager.get_custom_tasks()
            for task in custom_tasks:
                task_id = task.get('id', '')
                if task_id and task_id not in all_tasks:
                    all_tasks[task_id] = {
                        'id': task_id,
                        'name': task.get('name', task_id),
                        'type': 'custom',
                        'schedule': task.get('schedule', ''),
                        'description': task.get('description', ''),
                        'enabled': task.get('enabled', True),
                        'config': task.get('config', {}),
                        'created_at': task.get('created_at', '')
                    }

            return all_tasks

        except Exception as e:
            self.logger.error(f"获取任务列表失败: {str(e)}")
            return {}

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定任务

        Args:
            task_id: 任务ID

        Returns:
            任务配置，如果不存在则返回None
        """
        all_tasks = self.get_all_tasks()
        return all_tasks.get(task_id)

    def validate_task_schedule(self, schedule: str) -> tuple[bool, str]:
        """
        验证任务调度时间

        Args:
            schedule: cron表达式

        Returns:
            (is_valid, error_message)
        """
        try:
            # 基本格式验证
            if not schedule or not schedule.strip():
                return False, "调度时间不能为空"

            schedule = schedule.strip()

            # 简单间隔格式验证
            simple_patterns = {
                r'^(\d+)m$': 'minutes',
                r'^(\d+)h$': 'hours',
                r'^(\d+)d$': 'days'
            }

            import re
            for pattern, unit in simple_patterns.items():
                if re.match(pattern, schedule):
                    value = int(re.search(pattern, schedule).group(1))
                    if value <= 0:
                        return False, f"{unit}数量必须大于0"
                    return True, ""

            # Cron格式验证 (5段式: 分 时 日 月 周)
            cron_parts = schedule.split()
            if len(cron_parts) != 5:
                return False, "Cron表达式必须为5段: 分 时 日 月 周"

            # 验证每一段
            validators = [
                lambda x: self._validate_cron_field(x, 0, 59),    # 分钟
                lambda x: self._validate_cron_field(x, 0, 23),    # 小时
                lambda x: self._validate_cron_field(x, 1, 31),    # 日
                lambda x: self._validate_cron_field(x, 1, 12),    # 月
                lambda x: self._validate_cron_field(x, 0, 7)      # 周
            ]

            for i, part in enumerate(cron_parts):
                if not validators[i](part):
                    return False, f"第{i+1}段格式错误: {part}"

            return True, ""

        except Exception as e:
            return False, f"调度时间验证失败: {str(e)}"

    def _validate_cron_field(self, field: str, min_val: int, max_val: int) -> bool:
        """验证cron字段"""
        if field == '*':
            return True

        # 数字
        if field.isdigit():
            return min_val <= int(field) <= max_val

        # 范围 (如: 1-5)
        if '-' in field:
            try:
                start, end = field.split('-')
                return min_val <= int(start) <= max_val and min_val <= int(end) <= max_val
            except (ValueError, IndexError):
                return False

        # 列表 (如: 1,3,5)
        if ',' in field:
            try:
                values = field.split(',')
                for val in values:
                    if not (min_val <= int(val) <= max_val):
                        return False
                return True
            except (ValueError, IndexError):
                return False

        # 步长 (如: */5, 1-10/2)
        if '/' in field:
            try:
                base, step = field.split('/')
                step_int = int(step)
                if base == '*':
                    return step_int > 0
                else:
                    return self._validate_cron_field(base, min_val, max_val) and step_int > 0
            except (ValueError, IndexError):
                return False

        return False

    def create_task(self, task_id: str, task_name: str, schedule: str,
                  task_config: Dict[str, Any], task_type: str = 'custom') -> Dict[str, Any]:
        """
        创建新任务

        Args:
            task_id: 任务ID
            task_name: 任务名称
            schedule: 调度时间
            task_config: 任务配置
            task_type: 任务类型 ('custom' 或 'preset')

        Returns:
            创建结果
        """
        try:
            self.logger.info(f"创建任务: {task_name} ({task_id})")

            # 验证调度时间
            is_valid, error = self.validate_task_schedule(schedule)
            if not is_valid:
                return {'success': False, 'error': f'调度时间无效: {error}'}

            # 验证任务配置
            from utils.validators import validate_user_input
            is_valid, errors, normalized_config = validate_user_input(task_config)
            if not is_valid:
                return {'success': False, 'error': f'任务配置无效: {", ".join(errors)}'}

            # 创建任务配置
            if task_type == 'custom':
                task_data = {
                    'id': task_id,
                    'name': task_name,
                    'schedule': schedule,
                    'config': normalized_config,
                    'enabled': True,
                    'created_at': datetime.now().isoformat(),
                    'description': task_config.get('description', '')
                }

                # 保存到用户配置
                self.config_manager.create_custom_task(task_name, task_data)

            elif task_type == 'preset':
                # 预设任务需要修改默认配置文件
                return {'success': False, 'error': '预设任务不能直接创建，请使用自定义任务'}

            self.logger.info(f"任务创建成功: {task_id}")
            return {
                'success': True,
                'task_id': task_id,
                'task_name': task_name,
                'schedule': schedule,
                'next_run': self._calculate_next_run(schedule)
            }

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'operation': 'create_task'})
            self.logger.error(f"创建任务失败: {error_info['error_message']}")
            return {'success': False, 'error': error_info['error_message']}

    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        执行指定任务

        Args:
            task_id: 任务ID

        Returns:
            执行结果
        """
        try:
            self.logger.info(f"开始执行任务: {task_id}")
            start_time = datetime.now()

            # 获取任务配置
            task = self.get_task(task_id)
            if not task:
                return {'success': False, 'error': f'任务不存在: {task_id}'}

            if not task.get('enabled', True):
                self.logger.warning(f"任务已禁用: {task_id}")
                return {'success': False, 'error': '任务已禁用'}

            # 准备执行参数
            params = task.get('config', {}).copy()

            # 添加默认收件人
            if 'recipients' not in params or not params['recipients']:
                default_params = self.config_manager.get_default_params()
                params['recipients'] = default_params.get('recipients', [])

            # 执行工作流
            result = self.workflow_executor.execute_complete_workflow(params)

            # 记录执行历史
            execution_record = {
                'task_id': task_id,
                'task_name': task.get('name', task_id),
                'execution_time': start_time.isoformat(),
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'success': result.get('success', False),
                'papers_found': result.get('papers_found', 0),
                'report_generated': result.get('report_generated', False),
                'email_sent': result.get('email_sent', False),
                'errors': result.get('errors', [])
            }

            self.execution_history.append(execution_record)

            # 记录日志
            if result['success']:
                self.logger.info(f"任务执行成功: {task_id}")
            else:
                self.logger.error(f"任务执行失败: {task_id} - {result.get('errors', [])}")

            return {
                'success': result['success'],
                'task_id': task_id,
                'execution_record': execution_record,
                'result': result
            }

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'task_id': task_id})
            self.logger.error(f"执行任务失败: {task_id} - {error_info['error_message']}")

            return {
                'success': False,
                'task_id': task_id,
                'error': error_info['error_message']
            }

    def calculate_next_runs(self, schedule: str, count: int = 5) -> List[str]:
        """
        计算任务的下几次执行时间

        Args:
            schedule: 调度时间
            count: 计算次数

        Returns:
            执行时间列表
        """
        try:
            import croniter

            now = datetime.now()
            cron = croniter.croniter(schedule, now)

            next_runs = []
            for i in range(count):
                next_time = cron.get_next(datetime)
                next_runs.append(next_time.strftime('%Y-%m-%d %H:%M:%S'))

            return next_runs

        except ImportError:
            # 如果没有croniter库，使用简单计算
            return self._calculate_next_runs_simple(schedule, count)
        except Exception as e:
            self.logger.error(f"计算下次执行时间失败: {str(e)}")
            return []

    def _calculate_next_runs_simple(self, schedule: str, count: int) -> List[str]:
        """简单的下次执行时间计算（不依赖croniter）"""
        now = datetime.now()
        next_runs = []

        # 简单间隔格式
        import re
        simple_patterns = {
            r'^(\d+)m$': timedelta(minutes=1),
            r'^(\d+)h$': timedelta(hours=1),
            r'^(\d+)d$': timedelta(days=1)
        }

        for pattern, delta in simple_patterns.items():
            match = re.match(pattern, schedule)
            if match:
                interval = int(match.group(1))
                delta = timedelta(**{delta: interval})

                for i in range(count):
                    next_time = now + delta * (i + 1)
                    next_runs.append(next_time.strftime('%Y-%m-%d %H:%M:%S'))

                return next_runs

        # Cron格式 - 简化处理，返回提示
        return [f"需要安装 croniter 库来计算 cron 表达式的执行时间"]

    def _calculate_next_run(self, schedule: str) -> str:
        """计算下次执行时间"""
        next_runs = self.calculate_next_runs(schedule, 1)
        return next_runs[0] if next_runs else "无法计算"

    def get_execution_history(self, task_id: Optional[str] = None,
                             limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取任务执行历史

        Args:
            task_id: 任务ID（为None时返回所有任务的历史）
            limit: 返回记录数量限制

        Returns:
            执行历史列表
        """
        history = self.execution_history

        if task_id:
            history = [record for record in history if record['task_id'] == task_id]

        # 按时间倒序排列
        history = sorted(history, key=lambda x: x['execution_time'], reverse=True)

        return history[:limit]

    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            统计信息字典
        """
        all_tasks = self.get_all_tasks()
        history = self.execution_history

        total_tasks = len(all_tasks)
        enabled_tasks = sum(1 for task in all_tasks.values() if task.get('enabled', True))
        total_executions = len(history)
        successful_executions = sum(1 for record in history if record['success'])

        # 计算成功率
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0

        # 任务类型分布
        preset_count = sum(1 for task in all_tasks.values() if task.get('type') == 'preset')
        custom_count = sum(1 for task in all_tasks.values() if task.get('type') == 'custom')

        return {
            'total_tasks': total_tasks,
            'enabled_tasks': enabled_tasks,
            'disabled_tasks': total_tasks - enabled_tasks,
            'preset_tasks': preset_count,
            'custom_tasks': custom_count,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': total_executions - successful_executions,
            'success_rate': f'{success_rate:.1f}%'
        }

    def enable_task(self, task_id: str) -> Dict[str, Any]:
        """启用任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                return {'success': False, 'error': f'任务不存在: {task_id}'}

            if task.get('type') == 'custom':
                # 修改自定义任务
                custom_tasks = self.config_manager.get_custom_tasks()
                for task_data in custom_tasks:
                    if task_data.get('id') == task_id:
                        task_data['enabled'] = True
                        break

                # 保存配置
                user_config = self.config_manager._load_user_config()
                user_config['custom_tasks'] = custom_tasks
                self.config_manager.save_user_config(user_config)

            self.logger.info(f"任务已启用: {task_id}")
            return {'success': True, 'task_id': task_id}

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'task_id': task_id})
            return {'success': False, 'error': error_info['error_message']}

    def disable_task(self, task_id: str) -> Dict[str, Any]:
        """禁用任务"""
        try:
            task = self.get_task(task_id)
            if not task:
                return {'success': False, 'error': f'任务不存在: {task_id}'}

            if task.get('type') == 'custom':
                # 修改自定义任务
                custom_tasks = self.config_manager.get_custom_tasks()
                for task_data in custom_tasks:
                    if task_data.get('id') == task_id:
                        task_data['enabled'] = False
                        break

                # 保存配置
                user_config = self.config_manager._load_user_config()
                user_config['custom_tasks'] = custom_tasks
                self.config_manager.save_user_config(user_config)

            self.logger.info(f"任务已禁用: {task_id}")
            return {'success': True, 'task_id': task_id}

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'task_id': task_id})
            return {'success': False, 'error': error_info['error_message']}

    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """删除任务（仅限自定义任务）"""
        try:
            task = self.get_task(task_id)
            if not task:
                return {'success': False, 'error': f'任务不存在: {task_id}'}

            if task.get('type') == 'preset':
                return {'success': False, 'error': '预设任务不能删除，只能禁用'}

            # 删除自定义任务
            custom_tasks = self.config_manager.get_custom_tasks()
            custom_tasks = [task for task in custom_tasks if task.get('id') != task_id]

            # 保存配置
            user_config = self.config_manager._load_user_config()
            user_config['custom_tasks'] = custom_tasks
            self.config_manager.save_user_config(user_config)

            self.logger.info(f"任务已删除: {task_id}")
            return {'success': True, 'task_id': task_id}

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'task_id': task_id})
            return {'success': False, 'error': error_info['error_message']}


# 便捷函数
def get_task_scheduler(config_manager: Optional[ConfigManager] = None) -> TaskScheduler:
    """获取任务调度器实例"""
    return TaskScheduler(config_manager)


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试任务调度器")
    print("=" * 60)

    try:
        # 创建调度器
        scheduler = get_task_scheduler()

        # 获取所有任务
        print("\n1️⃣ 获取所有任务:")
        all_tasks = scheduler.get_all_tasks()
        print(f"找到 {len(all_tasks)} 个任务:")
        for task_id, task in all_tasks.items():
            status = "✓" if task.get('enabled', True) else "✗"
            print(f"  {status} {task_id} - {task.get('name', 'N/A')}")

        # 验证调度时间
        print("\n2️⃣ 验证调度时间:")
        test_schedules = [
            "0 9 * * 1",    # 每周一上午9点
            "0 8 * * *",    # 每天上午8点
            "*/30 * * * *", # 每30分钟
            "1h",           # 每小时
            "invalid"       # 无效
        ]

        for schedule in test_schedules:
            is_valid, error = scheduler.validate_task_schedule(schedule)
            status = "✓" if is_valid else "✗"
            print(f"  {status} {schedule}: {'有效' if is_valid else error}")

        # 计算下次执行时间
        print("\n3️⃣ 计算下次执行时间:")
        valid_schedule = "0 9 * * 1"
        next_runs = scheduler.calculate_next_runs(valid_schedule, 3)
        print(f"  调度: {valid_schedule}")
        for i, next_time in enumerate(next_runs, 1):
            print(f"  第{i}次: {next_time}")

        # 获取统计信息
        print("\n4️⃣ 任务统计:")
        stats = scheduler.get_task_statistics()
        print(f"  总任务数: {stats['total_tasks']}")
        print(f"  启用任务: {stats['enabled_tasks']}")
        print(f"  禁用任务: {stats['disabled_tasks']}")
        print(f"  预设任务: {stats['preset_tasks']}")
        print(f"  自定义任务: {stats['custom_tasks']}")
        print(f"  执行次数: {stats['total_executions']}")
        print(f"  成功率: {stats['success_rate']}")

        print("\n✅ 测试完成!")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()