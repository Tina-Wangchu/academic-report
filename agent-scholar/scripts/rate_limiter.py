"""
API 限流处理器
处理多个学术数据源的 API 限流问题
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """API 限流器"""

    # 各数据源的限流配置（请求数, 时间窗口秒数）
    RATE_LIMITS = {
        'semantic_scholar': (5000, 86400),    # 5000次/天
        'crossref': (10, 1),                    # 10次/秒
        'openalex': (100, 1),                   # 100次/秒
        'arxiv': (None, None),                  # 无限制
        'pubmed': (3, 1),                       # 3次/秒
    }

    def __init__(self):
        """初始化限流器"""
        self.request_history: Dict[str, list] = defaultdict(list)
        self.blocked_until: Dict[str, datetime] = {}

    def wait_if_needed(self, source: str, max_wait_seconds: int = 3600) -> bool:
        """
        如果达到限流，等待直到可请求

        Args:
            source: 数据源名称
            max_wait_seconds: 最大等待时间（秒）

        Returns:
            bool: True=可以请求, False=超时取消
        """
        # 检查是否在阻塞期
        if source in self.blocked_until:
            wait_time = (self.blocked_until[source] - datetime.now()).total_seconds()
            if wait_time > 0:
                logger.warning(f"{source} 仍在阻塞期，需等待 {wait_time:.1f} 秒")
                if wait_time > max_wait_seconds:
                    logger.error(f"等待时间超过最大限制 {max_wait_seconds} 秒")
                    return False
                time.sleep(wait_time)
            else:
                # 阻塞期已过，清除记录
                del self.blocked_until[source]

        # 检查当前源的限流配置
        if source not in self.RATE_LIMITS:
            logger.warning(f"未配置 {source} 的限流，允许请求")
            return True

        max_requests, window_seconds = self.RATE_LIMITS[source]

        # 无限制
        if max_requests is None:
            return True

        # 清理过期记录
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=window_seconds)
        self.request_history[source] = [
            req_time for req_time in self.request_history[source]
            if req_time > cutoff_time
        ]

        # 检查是否超限
        current_count = len(self.request_history[source])
        if current_count >= max_requests:
            # 计算需要等待的时间
            oldest_request = min(self.request_history[source])
            wait_time = (oldest_request + timedelta(seconds=window_seconds) - now).total_seconds()

            logger.warning(f"{source} 达到限流 ({current_count}/{max_requests} 在 {window_seconds}秒窗口内)")

            if wait_time > max_wait_seconds:
                logger.error(f"等待时间超过最大限制 {max_wait_seconds} 秒")
                # 设置阻塞期，避免频繁检查
                self.blocked_until[source] = oldest_request + timedelta(seconds=window_seconds)
                return False

            logger.info(f"等待 {wait_time:.1f} 秒后继续")
            time.sleep(wait_time)

            # 等待后清理过期记录
            self.request_history[source] = []

        # 记录本次请求
        self.request_history[source].append(now)
        return True

    def get_remaining_requests(self, source: str) -> Optional[int]:
        """
        获取剩余请求数

        Args:
            source: 数据源名称

        Returns:
            剩余请求数，如果无限制则返回 None
        """
        if source not in self.RATE_LIMITS:
            return None

        max_requests, window_seconds = self.RATE_LIMITS[source]
        if max_requests is None:
            return None

        # 清理过期记录
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=window_seconds)
        self.request_history[source] = [
            req_time for req_time in self.request_history[source]
            if req_time > cutoff_time
        ]

        current_count = len(self.request_history[source])
        remaining = max(0, max_requests - current_count)

        return remaining

    def reset(self, source: Optional[str] = None):
        """
        重置限流记录

        Args:
            source: 数据源名称，如果为 None 则重置所有
        """
        if source:
            self.request_history[source] = []
            if source in self.blocked_until:
                del self.blocked_until[source]
            logger.info(f"已重置 {source} 的限流记录")
        else:
            self.request_history.clear()
            self.blocked_until.clear()
            logger.info("已重置所有限流记录")

    def get_status(self) -> Dict:
        """获取各数据源的限流状态"""
        status = {}

        for source, (max_requests, window_seconds) in self.RATE_LIMITS.items():
            remaining = self.get_remaining_requests(source)

            status[source] = {
                'max_requests': max_requests,
                'window_seconds': window_seconds,
                'remaining': remaining,
                'blocked': source in self.blocked_until,
            }

        return status


# 全局限流器实例
_global_limiter = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器实例"""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter()
    return _global_limiter
