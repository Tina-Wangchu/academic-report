#!/usr/bin/env python3
"""
工作流执行器
负责协调论文检索、报告生成和邮件发送的完整流程
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# 添加项目根目录到路径
# scripts/workflow_executor.py -> scripts/ -> paper-email-service/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.validators import InputValidator
from utils.formatters import DataFormatter, ReportFormatter
from utils.error_handler import (
    PaperSearchError, ReportGenerationError, EmailSendError,
    get_error_handler, safe_execute
)
from config_manager import ConfigManager


class WorkflowExecutor:
    """工作流执行器"""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化工作流执行器

        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        self.error_handler = get_error_handler()
        self.validator = InputValidator()

        # 设置临时目录
        self.temp_dir = self._setup_temp_dir()

        # 获取相关技能的路径
        self.skill_paths = self._locate_skill_paths()

    def _setup_temp_dir(self) -> Path:
        """设置临时目录"""
        temp_base = Path(tempfile.gettempdir()) / 'paper_email_service'
        temp_base.mkdir(parents=True, exist_ok=True)
        return temp_base

    def _locate_skill_paths(self) -> Dict[str, Path]:
        """
        定位相关技能的路径

        Returns:
            技能路径字典
        """
        skills_base = self.config_manager.config_dir.parent.parent  # skills目录

        return {
            'paper_search': skills_base / 'paper-search' / 'scripts' / 'paper_search.py',
            'report_generator': skills_base / 'report-generator' / 'scripts' / 'generate_report.py',
            'email_sender': skills_base / 'email-sender' / 'scripts' / 'send_email.py'
        }

    def validate_workflow_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证工作流参数

        Args:
            params: 参数字典

        Returns:
            (is_valid, error_messages)
        """
        return self.validator.validate_complete_params(params)

    @safe_execute(max_retries=3, exceptions_to_retry=(PaperSearchError,))
    def execute_paper_search(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行智能论文检索（解决搜索能力低下问题）

        修复4个核心问题：
        1. 多数据源（同行评审期刊、会议报告、顶会顶刊）
        2. 智能筛选（多维度、去重、保留最突破创新）
        3. 真实时间范围（真正7天综合考量）
        4. 标准搜索优先（避免降级搜索）

        Args:
            params: 检索参数

        Returns:
            高质量论文数据列表
        """
        print("🔍 步骤1/3: 执行智能多数据源检索...")

        try:
            # 导入智能搜索执行器
            from intelligent_search_executor import IntelligentSearchExecutor

            executor = IntelligentSearchExecutor(self.skill_paths, self.temp_dir)

            # 执行智能搜索（不使用降级）
            papers = executor.execute_multi_source_search(params)

            if not papers:
                raise PaperSearchError("智能搜索未找到相关论文")

            # 格式化论文数据
            formatted_papers = DataFormatter.format_paper_data(papers)

            print(f"   ✓ 最终结果: {len(formatted_papers)} 篇高质量论文")

            # 显示检索统计
            if formatted_papers:
                years = [p.get('year', 0) for p in formatted_papers if p.get('year', 0) > 0]
                if years:
                    print(f"   ✓ 时间跨度: {min(years)} - {max(years)}")

                sources = {}
                for paper in formatted_papers:
                    source = paper.get('source', 'Unknown')
                    sources[source] = sources.get(source, 0) + 1

                print(f"   ✓ 数据源分布: {dict(sources)}")

                # 显示质量指标
                citation_papers = [p for p in formatted_papers if p.get('citation_count', 0) > 10]
                recent_papers = [p for p in formatted_papers if p.get('year', 0) >= 2023]

                print(f"   ✓ 质量指标: {len(citation_papers)} 篇高引用, {len(recent_papers)} 篇最新研究")

            return formatted_papers

        except ImportError:
            # 如果智能执行器不可用，回退到原始方法
            print("   ⚠️ 智能执行器不可用，使用标准搜索")
            return self.execute_standard_paper_search(params)
        except subprocess.TimeoutExpired:
            raise PaperSearchError("论文检索超时（5分钟），请检查网络连接")
        except json.JSONDecodeError as e:
            raise PaperSearchError(f"解析检索结果失败: {str(e)}")
        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'step': 'paper_search'})
            raise PaperSearchError(error_info['error_message'])

    def execute_standard_paper_search(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行标准论文检索（备用方法）

        Args:
            params: 检索参数

        Returns:
            论文数据列表
        """
        print("   执行标准检索...")

        try:
            # 构建检索命令
            search_script = self.skill_paths['paper_search']

            if not search_script.exists():
                raise PaperSearchError(f"检索脚本不存在: {search_script}")

            # 准备命令参数
            cmd = [
                sys.executable, str(search_script),
                '--topic', params['topic'],
                '--time-range', params.get('time_range', '7d'),  # 默认7天
                '--max-results', str(params.get('max_results', 30)),  # 获取更多结果
                '--domain', params.get('domain', 'general'),
                '--sort-by', 'publication_date',  # 按时间排序
                '--output-format', 'json'
            ]

            # 添加可选参数
            if 'keywords' in params and params['keywords']:
                cmd.extend(['--keywords', params['keywords']])

            # 执行检索
            print(f"   执行命令: {' '.join(cmd[:5])}...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8'
            )

            if result.returncode != 0:
                error_msg = result.stderr or "论文检索失败"
                raise PaperSearchError(f"检索脚本执行失败: {error_msg}")

            # 解析结果
            papers = json.loads(result.stdout)

            # 格式化论文数据
            formatted_papers = DataFormatter.format_paper_data(papers)

            print(f"   ✓ 找到 {len(formatted_papers)} 篇相关论文")

            return formatted_papers

        except Exception as e:
            raise PaperSearchError(f"标准检索失败: {str(e)}")

    @safe_execute(max_retries=2, exceptions_to_retry=(ReportGenerationError,))
    def execute_report_generation(self, papers: List[Dict[str, Any]], params: Dict[str, Any]) -> str:
        """
        执行报告生成

        Args:
            papers: 论文数据列表
            params: 生成参数

        Returns:
            生成的报告文件路径
        """
        print("📊 步骤2/3: 正在生成PDF报告...")

        try:
            # 准备论文数据文件
            papers_file = self.temp_dir / 'papers.json'
            with open(papers_file, 'w', encoding='utf-8') as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)

            # 构建报告文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            topic_slug = '_'.join(params['topic'].split()[:3]).lower()[:30]
            report_filename = f"{topic_slug}_report_{timestamp}.pdf"
            report_path = self.temp_dir / report_filename

            # 构建生成命令
            report_script = self.skill_paths['report_generator']

            if not report_script.exists():
                raise ReportGenerationError(f"报告生成脚本不存在: {report_script}")

            cmd = [
                sys.executable, str(report_script),
                '--input', str(papers_file),
                '--output', str(report_path),
                '--format', params.get('report_format', 'pdf'),
                '--title', params.get('topic', 'Academic Report')
            ]

            # 添加可选参数
            if params.get('include_analysis', True):
                cmd.append('--include-analysis')

            if params.get('include_references', True):
                cmd.append('--include-references')

            # 执行报告生成
            print(f"   执行命令: {' '.join(cmd[:5])}...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3分钟超时
                encoding='utf-8'
            )

            if result.returncode != 0:
                error_msg = result.stderr or "报告生成失败"
                raise ReportGenerationError(f"报告生成脚本执行失败: {error_msg}")

            # 验证文件生成
            if not report_path.exists():
                raise ReportGenerationError(f"报告文件未生成: {report_path}")

            file_size = report_path.stat().st_size / (1024 * 1024)  # MB
            print(f"   ✓ 报告生成完成")
            print(f"   ✓ 文件大小: {file_size:.1f}MB")

            return str(report_path)

        except subprocess.TimeoutExpired:
            raise ReportGenerationError("报告生成超时（3分钟）")
        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'step': 'report_generation'})
            raise ReportGenerationError(error_info['error_message'])

    @safe_execute(max_retries=2, exceptions_to_retry=(EmailSendError,))
    def execute_email_sending(self, report_path: str, params: Dict[str, Any],
                              papers: List[Dict[str, Any]]) -> bool:
        """
        执行邮件发送

        Args:
            report_path: 报告文件路径
            params: 发送参数
            papers: 论文数据（用于生成邮件正文）

        Returns:
            发送是否成功
        """
        print("📧 步骤3/3: 正在发送邮件...")

        try:
            # 准备邮件主题
            timestamp = datetime.now().strftime('%Y-%m-%d')
            subject_template = params.get('email_subject_template',
                                        '📚 {topic} 学术报告 - {date}')
            subject = subject_template.format(topic=params['topic'], date=timestamp)

            # 准备邮件正文
            email_body = self._generate_email_body(params, papers)

            # 准备邮件正文文件
            email_body_file = self.temp_dir / 'email_body.txt'
            with open(email_body_file, 'w', encoding='utf-8') as f:
                f.write(email_body)

            # 构建发送命令
            email_script = self.skill_paths['email_sender']

            if not email_script.exists():
                raise EmailSendError(f"邮件发送脚本不存在: {email_script}")

            # 准备收件人列表
            recipients = params.get('recipients', [])
            if not recipients:
                raise EmailSendError("未指定收件人")

            cmd = [
                sys.executable, str(email_script),
                '--to', ','.join(recipients),
                '--subject', subject,
                '--body-file', str(email_body_file),
                '--attachment', report_path,
                '--body-type', params.get('email_body_type', 'html')
            ]

            # 执行邮件发送
            print(f"   收件人: {', '.join(recipients)}")
            print(f"   附件: {Path(report_path).name}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2分钟超时
                encoding='utf-8'
            )

            if result.returncode != 0:
                error_msg = result.stderr or "邮件发送失败"
                raise EmailSendError(f"邮件发送脚本执行失败: {error_msg}")

            print("   ✓ 邮件发送成功")

            return True

        except subprocess.TimeoutExpired:
            raise EmailSendError("邮件发送超时（2分钟）")
        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'step': 'email_sending'})
            raise EmailSendError(error_info['error_message'])

    def _generate_email_body(self, params: Dict[str, Any], papers: List[Dict[str, Any]]) -> str:
        """
        生成邮件正文

        Args:
            params: 参数字典
            papers: 论文数据列表

        Returns:
            邮件正文内容
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 生成报告摘要
        summary = ReportFormatter.generate_summary(
            papers, params['topic'], params.get('time_range', '1y')
        )

        # 构建HTML邮件正文
        if params.get('email_body_type', 'html') == 'html':
            return self._generate_html_email(params, papers, summary, timestamp)
        else:
            return self._generate_plain_email(params, papers, summary, timestamp)

    def _generate_html_email(self, params: Dict[str, Any], papers: List[Dict[str, Any]],
                            summary: Dict[str, Any], timestamp: str) -> str:
        """生成HTML格式邮件正文"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f4f4f4; padding: 15px; text-align: center; }}
        .summary {{ background-color: #e9f7fe; padding: 15px; margin: 15px 0; border-left: 4px solid #2196F3; }}
        .stats {{ display: flex; justify-content: space-around; margin: 15px 0; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
        .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #777; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📚 {params['topic']} 学术报告</h2>
            <p>生成时间: {timestamp}</p>
        </div>

        <div class="summary">
            <h3>📊 报告摘要</h3>
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{summary.get('total_papers', 0)}</div>
                    <div>论文总数</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{params.get('time_range', '1y')}</div>
                    <div>时间范围</div>
                </div>
            </div>
"""

        # 添加统计信息
        if summary.get('year_distribution'):
            html_content += "<h4>年份分布:</h4><ul>"
            for year, count in list(summary['year_distribution'].items())[:5]:
                html_content += f"<li>{year}: {count}篇</li>"
            html_content += "</ul>"

        # 添加来源信息
        if summary.get('source_distribution'):
            html_content += "<h4>来源分布:</h4><ul>"
            for source, count in summary['source_distribution'].items():
                html_content += f"<li>{source}: {count}篇</li>"
            html_content += "</ul>"

        html_content += """
        </div>

        <div class="footer">
            <p>📧 本报告由 <strong>Hermes 学术助手</strong> 自动生成并发送</p>
            <p>📎 报告PDF已作为附件发送，请查收</p>
            <p>⚙️ 配置参数: 主题={params['topic']}, 时间范围={params.get('time_range', '1y')}, 文献数量={params.get('max_results', 10)}篇</p>
        </div>
    </div>
</body>
</html>
"""

        return html_content

    def _generate_plain_email(self, params: Dict[str, Any], papers: List[Dict[str, Any]],
                            summary: Dict[str, Any], timestamp: str) -> str:
        """生成纯文本格式邮件正文"""
        lines = [
            f"📚 {params['topic']} 学术报告",
            f"生成时间: {timestamp}",
            "",
            "📊 报告摘要",
            f"- 论文总数: {summary.get('total_papers', 0)}篇",
            f"- 时间范围: {params.get('time_range', '1y')}",
            ""
        ]

        # 添加年份分布
        if summary.get('year_distribution'):
            lines.extend(["年份分布:"])
            for year, count in list(summary['year_distribution'].items())[:5]:
                lines.append(f"- {year}: {count}篇")
            lines.append("")

        # 添加来源信息
        if summary.get('source_distribution'):
            lines.extend(["来源分布:"])
            for source, count in summary['source_distribution'].items():
                lines.append(f"- {source}: {count}篇")
            lines.append("")

        # 添加结尾信息
        lines.extend([
            "",
            "📧 本报告由 Hermes 学术助手 自动生成并发送",
            "📎 报告PDF已作为附件发送，请查收",
            "",
            f"⚙️ 配置参数: 主题={params['topic']}, 时间范围={params.get('time_range', '1y')}, 文献数量={params.get('max_results', 10)}篇"
        ])

        return "\n".join(lines)

    def execute_complete_workflow(self, params: Dict[str, Any],
                                 cleanup_temp: bool = True) -> Dict[str, Any]:
        """
        执行完整工作流

        Args:
            params: 工作流参数
            cleanup_temp: 是否清理临时文件

        Returns:
            执行结果字典
        """
        result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'params': params.copy(),
            'papers_found': 0,
            'report_generated': False,
            'email_sent': False,
            'errors': []
        }

        try:
            print("🔄 开始执行完整工作流...")
            print(f"⏰ 开始时间: {result['timestamp']}")
            print("")

            # 验证参数
            is_valid, errors = self.validate_workflow_params(params)
            if not is_valid:
                result['errors'] = errors
                return result

            # 步骤1: 论文检索
            papers = self.execute_paper_search(params)
            result['papers_found'] = len(papers)

            if not papers:
                print("⚠️ 未找到相关论文，工作流终止")
                result['errors'].append("未找到相关论文")
                return result

            # 步骤2: 报告生成
            report_path = self.execute_report_generation(papers, params)
            result['report_generated'] = True
            result['report_path'] = report_path

            # 步骤3: 邮件发送
            email_sent = self.execute_email_sending(report_path, params, papers)
            result['email_sent'] = email_sent

            # 清理临时文件
            if cleanup_temp and self.temp_dir.exists():
                try:
                    shutil.rmtree(self.temp_dir)
                    print("✓ 临时文件已清理")
                except Exception as e:
                    print(f"⚠️ 清理临时文件失败: {str(e)}")

            result['success'] = True

            print("")
            print("✅ 工作流执行完成!")
            print(f"📊 执行摘要:")
            print(f"- 论文数量: {result['papers_found']}篇")
            print(f"- 报告生成: {'成功' if result['report_generated'] else '失败'}")
            print(f"- 邮件发送: {'成功' if result['email_sent'] else '失败'}")

            return result

        except Exception as e:
            error_info = self.error_handler.handle_error(e, {'workflow': 'complete'})
            result['errors'].append(error_info['error_message'])
            result['error_details'] = error_info

            print(f"❌ 工作流执行失败: {error_info['error_message']}")

            # 如果有错误，保留临时文件用于调试
            if self.temp_dir.exists():
                print(f"🔧 临时文件已保留在: {self.temp_dir}")

            return result

    def execute_single_step(self, step: str, params: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> Any:
        """
        执行单个步骤

        Args:
            step: 步骤名称 ('search', 'report', 'email')
            params: 参数字典
            context: 上下文数据（包含前序步骤的结果）

        Returns:
            步骤执行结果
        """
        if step == 'search':
            return self.execute_paper_search(params)
        elif step == 'report':
            if not context or 'papers' not in context:
                raise ValueError("报告生成需要论文数据")
            return self.execute_report_generation(context['papers'], params)
        elif step == 'email':
            if not context or 'report_path' not in context:
                raise ValueError("邮件发送需要报告文件路径")
            return self.execute_email_sending(context['report_path'], params,
                                             context.get('papers', []))
        else:
            raise ValueError(f"未知的步骤: {step}")


# 便捷函数
def execute_workflow(params: Dict[str, Any],
                    config_manager: Optional[ConfigManager] = None) -> Dict[str, Any]:
    """
    执行完整工作流的便捷函数

    Args:
        params: 工作流参数
        config_manager: 配置管理器

    Returns:
        执行结果
    """
    executor = WorkflowExecutor(config_manager)
    return executor.execute_complete_workflow(params)


if __name__ == "__main__":
    # 测试代码
    import sys

    # 创建测试参数
    test_params = {
        'topic': 'machine learning',
        'time_range': '1y',
        'max_results': 5,
        'domain': 'ai',
        'recipients': ['test@example.com'],
        'report_format': 'pdf',
        'email_body_type': 'html'
    }

    print("🧪 测试工作流执行器")
    print("=" * 60)

    # 验证参数
    print("\n1️⃣ 验证参数...")
    from utils.validators import validate_user_input
    is_valid, errors, normalized = validate_user_input(test_params)

    if is_valid:
        print("✓ 参数验证通过")
    else:
        print("❌ 参数验证失败:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # 执行工作流
    print("\n2️⃣ 执行工作流...")
    try:
        result = execute_workflow(normalized)
        print("\n3️⃣ 工作流结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result['success']:
            print("\n✅ 测试成功!")
        else:
            print("\n❌ 测试失败!")
            if result['errors']:
                print("错误信息:")
                for error in result['errors']:
                    print(f"  - {error}")

    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()