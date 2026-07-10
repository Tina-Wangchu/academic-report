#!/usr/bin/env python3
"""
Paper Email Service - 论文邮件服务主入口
提供CLI接口和主要服务功能
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到路径
# scripts/paper_email_service.py -> scripts/ -> paper-email-service/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config_manager import ConfigManager, ConfigBuilder
from workflow_executor import WorkflowExecutor
from utils.validators import validate_user_input
from utils.formatters import ConfigFormatter, DataFormatter
from utils.error_handler import setup_error_handling, get_error_handler


class PaperEmailService:
    """论文邮件服务主类"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化服务

        Args:
            config_dir: 配置目录路径
        """
        self.config_manager = ConfigManager(config_dir)
        self.error_handler = get_error_handler()
        self.workflow_executor = WorkflowExecutor(self.config_manager)

    def collect_user_requirements(self) -> Dict[str, Any]:
        """
        收集用户需求（用于交互式对话）

        Returns:
            用户需求字典
        """
        print("📚 欢迎使用论文邮件服务")
        print("=" * 60)
        print("请提供以下信息来生成您的学术报告：")
        print()

        requirements = {}

        # 收集必需参数
        requirements['topic'] = input("📖 研究主题 (必需): ").strip()

        # 收集可选参数
        time_range = input("⏰ 时间范围 (可选，默认1y): ").strip() or "1y"
        requirements['time_range'] = time_range

        max_results = input("📊 文献数量 (可选，默认10): ").strip() or "10"
        requirements['max_results'] = int(max_results)

        domain = input("🔬 研究领域 (可选，默认general): ").strip() or "general"
        requirements['domain'] = domain

        # 收集邮件信息
        print("\n📧 邮件配置:")
        recipients_input = input("收件邮箱 (多个邮箱用逗号分隔，默认使用配置文件): ").strip()

        if recipients_input:
            requirements['recipients'] = [email.strip() for email in recipients_input.split(',')]
        else:
            # 使用默认收件人
            default_params = self.config_manager.get_default_params()
            requirements['recipients'] = default_params.get('recipients', [])

        # 其他配置
        requirements['report_format'] = 'pdf'
        requirements['email_body_type'] = 'html'

        return requirements

    def confirm_execution(self, params: Dict[str, Any]) -> bool:
        """
        确认执行参数

        Args:
            params: 参数字典

        Returns:
            用户是否确认
        """
        print("\n📋 执行参数确认:")
        print("-" * 60)

        # 显示配置
        display_text = ConfigFormatter.format_config_display(params)
        print(display_text)

        # 确认
        print("-" * 60)
        response = input("\n❓ 需要调整参数吗？(输入'确认'开始执行，或说明需要修改的部分): ").strip()

        return response.lower() in ['确认', 'yes', 'y', 'ok', '开始']

    def execute_single_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单次运行

        Args:
            params: 执行参数

        Returns:
            执行结果
        """
        try:
            print(f"\n🔄 开始执行工作流...")
            print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # 验证参数
            is_valid, errors, normalized_params = validate_user_input(params)

            if not is_valid:
                print("❌ 参数验证失败:")
                for error in errors:
                    print(f"  - {error}")
                return {'success': False, 'errors': errors}

            # 执行工作流
            result = self.workflow_executor.execute_complete_workflow(normalized_params)

            return result

        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断执行")
            return {'success': False, 'errors': ['用户中断执行']}
        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'operation': 'single_run'})
            print(f"\n❌ 执行失败: {error_info['error_message']}")

            if error_info.get('solutions'):
                print("\n💡 建议解决方案:")
                for i, solution in enumerate(error_info['solutions'], 1):
                    print(f"  {i}. {solution}")

            return {'success': False, 'errors': [error_info['error_message']]}

    def create_scheduled_task(self, task_name: str, schedule: str,
                            params: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建定时任务

        Args:
            task_name: 任务名称
            schedule: 调度表达式
            params: 任务参数

        Returns:
            创建结果
        """
        try:
            print(f"\n📅 创建定时任务: {task_name}")
            print(f"⏰ 调度时间: {schedule}")
            print()

            # 验证参数
            is_valid, errors, normalized_params = validate_user_input(params)

            if not is_valid:
                return {'success': False, 'errors': errors}

            # 保存任务配置
            task_config = {
                'schedule': schedule,
                'config': normalized_params,
                'enabled': True,
                'created_at': datetime.now().isoformat()
            }

            self.config_manager.create_custom_task(task_name, task_config)

            print(f"✅ 定时任务创建成功!")
            print(f"📋 任务名称: {task_name}")
            print(f"⏰ 调度: {schedule}")
            print(f"🔧 参数: {normalized_params.get('topic')}")

            return {'success': True, 'task_id': task_name, 'task_config': task_config}

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'operation': 'create_scheduled_task'})
            return {'success': False, 'errors': [error_info['error_message']]}

    def list_available_presets(self) -> List[str]:
        """
        列出可用的预设任务

        Returns:
            预设任务名称列表
        """
        presets = self.config_manager.get_preset_tasks()
        return list(presets.keys())

    def show_preset_details(self, preset_name: str) -> None:
        """
        显示预设任务详情

        Args:
            preset_name: 预设名称
        """
        try:
            preset_config = self.config_manager.get_preset_task(preset_name)

            print(f"\n📋 预设任务: {preset_name}")
            print("=" * 60)

            if 'description' in preset_config:
                print(f"📝 描述: {preset_config['description']}")

            if 'schedule' in preset_config:
                print(f"⏰ 调度: {preset_config['schedule']}")

            if 'config' in preset_config:
                print("⚙️ 配置:")
                config = preset_config['config']
                print(f"  - 主题: {config.get('topic', 'N/A')}")
                print(f"  - 时间范围: {config.get('time_range', 'N/A')}")
                print(f"  - 文献数量: {config.get('max_results', 'N/A')}")
                print(f"  - 领域: {config.get('domain', 'N/A')}")

        except Exception as e:
            print(f"❌ 获取预设任务失败: {str(e)}")

    def show_service_status(self) -> Dict[str, Any]:
        """
        显示服务状态

        Returns:
            服务状态字典
        """
        try:
            status = {
                'service_name': 'Paper Email Service',
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat(),
                'config_loaded': False,
                'environment_ok': False,
                'custom_tasks_count': 0,
                'available_presets': []
            }

            # 检查配置
            try:
                config = self.config_manager.load_config('merged')
                status['config_loaded'] = True
            except Exception as e:
                status['config_error'] = str(e)

            # 检查环境
            from utils.validators import InputValidator
            is_configured, missing_creds = InputValidator.validate_credentials_present()
            status['environment_ok'] = is_configured
            status['missing_credentials'] = missing_creds

            # 统计任务
            status['custom_tasks_count'] = len(self.config_manager.get_custom_tasks())
            status['available_presets'] = self.list_available_presets()

            return status

        except Exception as e:
            return {'error': str(e), 'success': False}


def setup_cli() -> argparse.ArgumentParser:
    """
    设置命令行接口

    Returns:
        参数解析器
    """
    parser = argparse.ArgumentParser(
        description='Paper Email Service - 学术论文邮件服务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:

1. 交互式单次执行:
   python paper_email_service.py --interactive

2. 命令行单次执行:
   python paper_email_service.py --topic "machine learning" --recipients user@example.com

3. 创建定时任务:
   python paper_email_service.py --create-task "AI周报" --schedule "0 9 * * 1" --topic "AI"

4. 列出预设任务:
   python paper_email_service.py --list-presets

5. 显示服务状态:
   python paper_email_service.py --status
        """
    )

    # 主要操作模式
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--interactive', '-i', action='store_true',
                           help='交互式模式')
    mode_group.add_argument('--single', '-s', action='store_true',
                           help='单次执行模式')
    mode_group.add_argument('--create-task', '-c', metavar='NAME',
                           help='创建定时任务')
    mode_group.add_argument('--list-presets', '-l', action='store_true',
                           help='列出预设任务')
    mode_group.add_argument('--show-preset', metavar='NAME',
                           help='显示预设任务详情')
    mode_group.add_argument('--status', action='store_true',
                           help='显示服务状态')
    mode_group.add_argument('--test-mode', action='store_true',
                           help='测试模式（不实际发送邮件）')

    # 执行参数
    parser.add_argument('--topic', '-t', metavar='TOPIC',
                       help='研究主题')
    parser.add_argument('--time-range', metavar='RANGE',
                       help='时间范围 (如: 1y, 3y, unlimited)')
    parser.add_argument('--max-results', type=int, metavar='NUM',
                       help='最大文献数量')
    parser.add_argument('--domain', '-d', metavar='DOMAIN',
                       help='研究领域 (general/ai/statistics/finance)')
    parser.add_argument('--recipients', '-r', metavar='EMAILS',
                       help='收件邮箱 (多个邮箱用逗号分隔)')
    parser.add_argument('--keywords', metavar='KEYWORDS',
                       help='搜索关键词')
    parser.add_argument('--schedule', metavar='CRON',
                       help='定时任务调度表达式')

    # 配置选项
    parser.add_argument('--config-dir', metavar='PATH',
                       help='配置目录路径')
    parser.add_argument('--debug', action='store_true',
                       help='调试模式')

    return parser


def main():
    """主函数"""
    # 设置UTF-8编码输出（Windows兼容性）
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 解析命令行参数
    parser = setup_cli()
    args = parser.parse_args()

    # 设置错误处理
    setup_error_handling(debug_mode=args.debug)

    # 创建服务实例
    service = PaperEmailService(args.config_dir)

    try:
        # 显示服务状态
        if args.status:
            status = service.show_service_status()
            print("服务状态:")
            print(json.dumps(status, indent=2, ensure_ascii=False))
            return 0

        # 列出预设任务
        if args.list_presets:
            presets = service.list_available_presets()
            print("📋 可用的预设任务:")
            for preset in presets:
                print(f"  - {preset}")
            return 0

        # 显示预设任务详情
        if args.show_preset:
            service.show_preset_details(args.show_preset)
            return 0

        # 创建定时任务
        if args.create_task:
            if not args.schedule:
                print("❌ 创建定时任务需要指定 --schedule 参数")
                return 1

            params = {}
            if args.topic:
                params['topic'] = args.topic
            else:
                print("❌ 创建定时任务需要指定 --topic 参数")
                return 1

            # 可选参数
            if args.time_range:
                params['time_range'] = args.time_range
            if args.max_results:
                params['max_results'] = args.max_results
            if args.domain:
                params['domain'] = args.domain
            if args.recipients:
                params['recipients'] = [r.strip() for r in args.recipients.split(',')]
            if args.keywords:
                params['keywords'] = args.keywords

            result = service.create_scheduled_task(args.create_task, args.schedule, params)

            if result['success']:
                return 0
            else:
                print(f"❌ 创建任务失败: {result['errors']}")
                return 1

        # 交互式模式
        if args.interactive:
            params = service.collect_user_requirements()

            if service.confirm_execution(params):
                result = service.execute_single_run(params)

                if result['success']:
                    print(f"\n✅ 任务执行成功!")
                    return 0
                else:
                    print(f"\n❌ 任务执行失败!")
                    if result['errors']:
                        print("错误信息:")
                        for error in result['errors']:
                            print(f"  - {error}")
                    return 1
            else:
                print("\n⚠️ 用户取消执行")
                return 1

        # 单次执行模式
        if args.single:
            if not args.topic:
                print("❌ 单次执行需要指定 --topic 参数")
                return 1

            params = {'topic': args.topic}

            # 可选参数
            if args.time_range:
                params['time_range'] = args.time_range
            if args.max_results:
                params['max_results'] = args.max_results
            if args.domain:
                params['domain'] = args.domain
            if args.recipients:
                params['recipients'] = [r.strip() for r in args.recipients.split(',')]
            if args.keywords:
                params['keywords'] = args.keywords

            result = service.execute_single_run(params)

            if result['success']:
                return 0
            else:
                print(f"❌ 执行失败!")
                if result['errors']:
                    print("错误信息:")
                    for error in result['errors']:
                        print(f"  - {error}")
                return 1

        # 测试模式
        if args.test_mode:
            print("🧪 测试模式 - 不实际发送邮件")
            test_params = {
                'topic': args.topic or 'test topic',
                'time_range': args.time_range or '1y',
                'max_results': args.max_results or 3,
                'domain': args.domain or 'general',
                'recipients': args.recipients.split(',') if args.recipients else ['test@example.com']
            }

            # 只执行检索和报告生成，不发送邮件
            print("🔍 测试论文检索...")
            papers = service.workflow_executor.execute_paper_search(test_params)
            print(f"✓ 检索到 {len(papers)} 篇论文")

            if papers:
                print("📊 测试报告生成...")
                report_path = service.workflow_executor.execute_report_generation(papers, test_params)
                print(f"✓ 报告生成: {report_path}")

            return 0

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断执行")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())