#!/usr/bin/env python3
"""
统一错误处理模块
提供错误分类、解决方案生成和安全执行包装器
"""

import sys
import traceback
import logging
from typing import Dict, Any, Optional, Callable, Tuple
from functools import wraps
from datetime import datetime


# 设置日志
logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """服务错误基类"""

    def __init__(self, message: str, error_code: str = "SERVICE_ERROR",
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(ServiceError):
    """配置错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", details)


class PaperSearchError(ServiceError):
    """论文检索错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SEARCH_ERROR", details)


class ReportGenerationError(ServiceError):
    """报告生成错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "REPORT_ERROR", details)


class EmailSendError(ServiceError):
    """邮件发送错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EMAIL_ERROR", details)


class NetworkError(ServiceError):
    """网络连接错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NETWORK_ERROR", details)


class ValidationError(ServiceError):
    """输入验证错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class ErrorHandler:
    """统一错误处理器"""

    # 错误分类规则
    ERROR_PATTERNS = {
        'network': [
            'connection', 'timeout', 'network', 'internet', 'proxy',
            'socks', 'smtp', 'ssl', 'certificate', 'dns'
        ],
        'authentication': [
            'authentication', 'password', 'login', 'credential', 'unauthorized',
            'app password', '2fa', 'verification'
        ],
        'configuration': [
            'config', 'setting', 'environment', 'parameter', 'path',
            'file not found', 'directory'
        ],
        'data': [
            'no results', 'empty', 'invalid data', 'parse error',
            'format error', 'encoding'
        ],
        'permission': [
            'permission', 'access denied', 'forbidden', 'authorization',
            'read/write', 'filesystem'
        ],
        'rate_limit': [
            'rate limit', 'too many requests', '429', 'quota',
            'api limit', 'throttle'
        ]
    }

    # 解决方案模板
    SOLUTIONS = {
        'network': [
            "检查网络连接是否正常",
            "验证代理设置是否正确（如需要）",
            "尝试更换网络环境或稍后重试",
            "检查防火墙是否阻止了连接"
        ],
        'authentication': [
            "验证Gmail应用专用密码是否正确",
            "确认环境变量GMAIL_ADDRESS和GMAIL_APP_PASSWORD已设置",
            "检查Google账户是否启用了2步验证",
            "重新生成应用专用密码：https://myaccount.google.com/apppasswords"
        ],
        'configuration': [
            "检查配置文件路径是否正确",
            "验证环境变量是否已正确设置",
            "确认默认配置文件存在",
            "检查用户配置文件格式是否正确"
        ],
        'data': [
            "尝试优化搜索关键词",
            "扩大时间范围或减少搜索条件",
            "检查数据源是否可用",
            "验证输入参数格式是否正确"
        ],
        'permission': [
            "检查文件和目录权限",
            "确认程序有读写临时目录的权限",
            "验证邮件附件大小未超过限制",
            "检查用户账户是否有足够的权限"
        ],
        'rate_limit': [
            "等待一段时间后重试（建议30分钟后）",
            "申请Semantic Scholar API密钥以提高限额",
            "减少并发请求数量",
            "考虑使用缓存避免重复请求"
        ]
    }

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.error_history = []

    def classify_error(self, error: Exception) -> str:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            错误类型字符串
        """
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()

        # 检查已知的错误模式
        for error_category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern in error_message or pattern in error_type:
                    return error_category

        # 特殊错误类型检查
        if isinstance(error, (ConnectionError, TimeoutError)):
            return 'network'
        elif isinstance(error, PermissionError):
            return 'permission'
        elif isinstance(error, FileNotFoundError):
            return 'configuration'
        elif isinstance(error, (ValueError, KeyError)):
            return 'data'

        # 默认分类
        return 'unknown'

    def generate_solutions(self, error: Exception, error_category: str) -> list:
        """
        生成解决方案建议

        Args:
            error: 异常对象
            error_category: 错误分类

        Returns:
            解决方案列表
        """
        solutions = []

        # 基于分类的通用解决方案
        if error_category in self.SOLUTIONS:
            solutions.extend(self.SOLUTIONS[error_category])

        # 基于具体错误信息的定制解决方案
        error_message = str(error).lower()

        if 'gmail' in error_message and 'authentication' in error_message:
            solutions.extend([
                "确认使用的是应用专用密码，而非Gmail登录密码",
                "检查是否开启了'允许不够安全的应用'（如使用旧版应用）",
                "验证Gmail地址格式正确（如：username@gmail.com）"
            ])

        if 'socks' in error_message or 'proxy' in error_message:
            solutions.extend([
                "确认SOCKS5代理地址格式：socks5://127.0.0.1:7890",
                "验证代理服务器是否正在运行",
                "尝试使用不同的代理端口或协议"
            ])

        if 'semantic scholar' in error_message and 'rate limit' in error_message:
            solutions.extend([
                "申请免费的Semantic Scholar API密钥：https://www.semanticscholar.org/product/api#api-key",
                "设置环境变量：SEMANTIC_SCHOLAR_API_KEY=your_key_here",
                "减少请求频率或增加请求间隔"
            ])

        if 'pdf' in error_message and 'generation' in error_message:
            solutions.extend([
                "确认已安装reportlab库：pip install reportlab",
                "检查输入数据格式是否正确",
                "尝试使用Markdown格式替代PDF",
                "验证中文字体是否正确配置"
            ])

        if 'no papers' in error_message or 'no results' in error_message:
            solutions.extend([
                "扩大时间范围（如从1y改为3y）",
                "简化搜索关键词或使用更通用的术语",
                "检查研究领域是否选择正确",
                "参考用户约束保护原则：在约束内优化搜索策略"
            ])

        return solutions

    def format_error_message(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        格式化错误消息

        Args:
            error: 异常对象
            context: 上下文信息

        Returns:
            格式化的错误信息字典
        """
        error_category = self.classify_error(error)
        solutions = self.generate_solutions(error, error_category)

        # 收集错误详情
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'error_category': error_category,
            'timestamp': datetime.now().isoformat(),
            'solutions': solutions,
            'context': context or {}
        }

        # 调试模式下添加详细信息
        if self.debug_mode:
            error_info['traceback'] = traceback.format_exc()
            error_info['debug_info'] = {
                'error_object': error,
                'error_args': error.args if hasattr(error, 'args') else None
            }

        # 记录到历史
        self.error_history.append(error_info)

        return error_info

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                    raise_service_error: bool = False) -> Dict[str, Any]:
        """
        统一错误处理入口

        Args:
            error: 异常对象
            context: 上下文信息
            raise_service_error: 是否抛出ServiceError

        Returns:
            错误信息字典
        """
        error_info = self.format_error_message(error, context)

        # 记录日志
        logger.error(f"Error occurred: {error_info['error_type']} - {error_info['error_message']}")

        # 根据错误类型决定处理策略
        if error_category := error_info['error_category']:
            if error_category == 'network':
                logger.info("Network error detected - will retry with backoff")
            elif error_category == 'authentication':
                logger.error("Authentication error - check credentials")
            elif error_category == 'rate_limit':
                logger.warning("Rate limit hit - implementing exponential backoff")

        if raise_service_error:
            # 转换为相应的ServiceError
            service_error_map = {
                'network': NetworkError,
                'authentication': ConfigurationError,
                'configuration': ConfigurationError,
                'data': ValidationError,
                'permission': ConfigurationError,
                'rate_limit': NetworkError
            }

            error_class = service_error_map.get(error_category, ServiceError)
            raise error_class(
                error_info['error_message'],
                error_info['error_type'],
                error_info
            )

        return error_info


def safe_execute(max_retries: int = 3, backoff_factor: float = 2.0,
                exceptions_to_retry: Optional[Tuple] = None,
                default_return: Any = None):
    """
    安全执行装饰器

    Args:
        max_retries: 最大重试次数
        backoff_factor: 退避因子
        exceptions_to_retry: 需要重试的异常类型元组
        default_return: 失败时的默认返回值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            last_exception = None

            # 默认重试网络相关的错误
            if exceptions_to_retry is None:
                exceptions_to_retry = (ConnectionError, TimeoutError, NetworkError)

            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    retries += 1

                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        break

                    # 计算退避时间
                    wait_time = backoff_factor ** (retries - 1)
                    logger.info(f"Retry {retries}/{max_retries} for {func.__name__} after {wait_time:.1f}s")

                    import time
                    time.sleep(wait_time)

                except Exception as e:
                    # 不重试的错误直接抛出
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    if default_return is not None:
                        return default_return
                    raise

            # 所有重试都失败
            if default_return is not None:
                return default_return

            raise last_exception

        return wrapper
    return decorator


def create_error_response(error_info: Dict[str, Any], include_debug: bool = False) -> str:
    """
    创建用户友好的错误响应消息

    Args:
        error_info: 错误信息字典
        include_debug: 是否包含调试信息

    Returns:
        格式化的错误消息字符串
    """
    lines = []

    # 错误标题
    lines.append(f"❌ {error_info['error_type']}: {error_info['error_message']}")
    lines.append("")

    # 错误分类
    if error_info['error_category'] != 'unknown':
        lines.append(f"🔍 错误类型: {error_info['error_category']}")

    # 解决方案建议
    if error_info.get('solutions'):
        lines.append("💡 建议解决方案:")
        for i, solution in enumerate(error_info['solutions'], 1):
            lines.append(f"  {i}. {solution}")

    lines.append("")

    # 调试信息
    if include_debug and error_info.get('traceback'):
        lines.append("🔧 调试信息:")
        lines.append("```")
        lines.append(error_info['traceback'])
        lines.append("```")

    return "\n".join(lines)


# 全局错误处理器实例
_global_handler = None

def get_error_handler(debug_mode: bool = False) -> ErrorHandler:
    """获取全局错误处理器实例"""
    global _global_handler
    if _global_handler is None:
        _global_handler = ErrorHandler(debug_mode=debug_mode)
    return _global_handler


def setup_error_handling(debug_mode: bool = False) -> None:
    """
    设置全局错误处理

    Args:
        debug_mode: 是否启用调试模式
    """
    global _global_handler
    _global_handler = ErrorHandler(debug_mode=debug_mode)

    # 配置日志
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/error.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


if __name__ == "__main__":
    # 测试代码
    setup_error_handling(debug_mode=True)
    handler = get_error_handler()

    # 模拟各种错误
    test_errors = [
        ConnectionError("Network connection failed"),
        ValueError("Invalid data format"),
        FileNotFoundError("Config file not found"),
        PermissionError("Access denied to /tmp"),
        Exception("Rate limit exceeded (429)")
    ]

    for error in test_errors:
        print("=" * 60)
        error_info = handler.handle_error(error)
        print(create_error_response(error_info, include_debug=True))
        print()