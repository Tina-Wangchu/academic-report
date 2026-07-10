#!/usr/bin/env python3
"""
Incremental Paper Searcher - 增量式论文搜索引擎

用于周期报告场景，只返回自上次报告以来的新论文：
- 检索上次报告时间以来的新论文
- 过滤已报告的论文
- 自动更新报告状态
"""

import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from paper_search import PaperSearchEngine


class IncrementalPaperSearcher(PaperSearchEngine):
    """
    增量式论文搜索引擎（用于周期报告）

    继承自 PaperSearchEngine，增加状态追踪能力
    """

    def __init__(self, config: Dict[str, Any], user_id: str = None):
        """
        Args:
            config: 搜索配置
            user_id: 用户ID（用于状态追踪）
        """
        super().__init__(config)

        self.user_id = user_id or config.get("user_id", "default_user")

        # 延迟导入状态管理器（避免循环导入）
        try:
            from report_state_manager import get_state_manager
            self.state_manager = get_state_manager()
        except ImportError:
            print("Warning: Report state manager not available", file=sys.stderr)
            self.state_manager = None

    def search_new_papers(self) -> Dict[str, Any]:
        """
        搜索自上次报告以来的新论文（增量模式）

        流程：
        1. 获取上次报告时间
        2. 计算时间范围（从上次报告到现在）
        3. 执行搜索
        4. 过滤已报告的论文
        5. 更新报告状态

        Returns:
            包含新论文的搜索结果
        """
        topic = self.research_topic
        domain = self.domain

        if not self.state_manager:
            # 状态管理器不可用，执行普通搜索
            result = super().search()
            result["note"] = "状态管理不可用，返回所有检索结果"
            return result

        # 步骤1: 获取上次报告时间
        last_report_time = self.state_manager.get_last_report_time(
            self.user_id, topic
        )

        if last_report_time:
            # 步骤2: 计算时间范围
            days_since_last = (datetime.now(timezone.utc) - last_report_time).days

            if days_since_last <= 0:
                # 上次报告是未来的（时钟错误），执行普通搜索
                result = super().search()
                result["note"] = "时间异常，返回所有检索结果"
                return result

            # 设置时间范围（从上次到现在）
            if days_since_last <= 1:
                time_range = "1d"  # 1天
            elif days_since_last <= 7:
                time_range = f"{days_since_last}d"  # N天
            else:
                time_range = f"{days_since_last}d"

            self.config["time_range"] = time_range

            # 步骤3: 执行搜索
            result = super().search()

            if result.get("status") != "success":
                return result

            # 步骤4: 过滤已报告的论文
            reported_ids = self.state_manager.get_reported_paper_ids(
                self.user_id, topic
            )

            original_count = len(result["papers"])
            new_papers = [
                p for p in result["papers"]
                if self._get_paper_id(p) not in reported_ids
            ]

            filtered_count = original_count - len(new_papers)

            # 更新结果
            result["papers"] = new_papers
            result["total_found"] = len(new_papers)
            result["note"] = f"显示自 {last_report_time.strftime('%Y-%m-%d')} 以来新增的论文"

            if filtered_count > 0:
                result["note"] += f"（已过滤 {filtered_count} 篇重复论文）"

            # 步骤5: 更新状态（如果有新论文）
            if new_papers:
                self.state_manager.update_report_state(
                    self.user_id, topic, domain, new_papers
                )
                result["state_updated"] = True
            else:
                result["state_updated"] = False
                result["note"] += " ⚠️ 本周期无新论文"

            return result
        else:
            # 首次报告，执行普通搜索并初始化状态
            result = super().search()

            if result.get("status") == "success" and result.get("papers"):
                # 初始化状态
                self.state_manager.update_report_state(
                    self.user_id, topic, domain, result["papers"]
                )
                result["note"] = "✓ 首次报告 - 已初始化状态追踪"
                result["state_updated"] = True
            else:
                result["note"] = "✗ 检索失败，未初始化状态"
                result["state_updated"] = False

            return result

    def _get_paper_id(self, paper: Dict) -> str:
        """生成论文唯一ID（委托给state_manager）"""
        if self.state_manager:
            return self.state_manager._paper_id(paper)
        else:
            # 降级方案：使用DOI或标题hash
            doi = paper.get("doi", "")
            if doi:
                return f"doi:{doi}"
            title = paper.get("title", "")
            return f"hash:{hash(title)}"


def search_incremental(topic: str, user_id: str, **kwargs) -> Dict[str, Any]:
    """
    增量式搜索的便捷函数

    Args:
        topic: 研究主题
        user_id: 用户ID（用于状态追踪）
        **kwargs: 其他搜索参数

    Returns:
        搜索结果
    """
    config = {
        "research_topic": topic,
        "user_id": user_id,
        **kwargs
    }

    searcher = IncrementalPaperSearcher(config, user_id)
    return searcher.search_new_papers()


if __name__ == "__main__":
    # 测试代码
    result = search_incremental(
        topic="artificial intelligence",
        user_id="test@example.com",
        time_range="7d",
        max_results=5
    )

    print(f"Status: {result.get('status')}")
    print(f"Found: {result.get('total_found')} papers")
    print(f"Note: {result.get('note', 'N/A')}")
