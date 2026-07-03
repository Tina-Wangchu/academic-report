#!/usr/bin/env python3
"""
Report State Manager - 周期报告状态管理系统

用于追踪用户的报告历史，实现增量式论文检索：
- 记录上次报告时间
- 记录已发送的论文ID
- 避免重复发送相同论文
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Set, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ReportState:
    """报告状态追踪"""
    last_report_time: str  # ISO格式时间戳
    last_paper_ids: List[str]  # 已报告的论文ID列表
    user_id: str
    topic: str
    domain: str
    report_count: int = 0  # 报告次数


class ReportStateManager:
    """周期报告状态管理器"""

    def __init__(self, state_file: str = "report_state.json"):
        """
        Args:
            state_file: 状态文件路径（相对于Hermes技能目录）
        """
        # 确定状态文件路径
        skill_dir = os.path.dirname(os.path.abspath(__file__))
        self.state_file = os.path.join(skill_dir, state_file)

        self.states = self._load_states()

    def get_last_report_time(self, user_id: str, topic: str) -> Optional[datetime]:
        """获取上次报告时间"""
        key = self._make_key(user_id, topic)
        state = self.states.get(key)
        if state and state.last_report_time:
            try:
                return datetime.fromisoformat(state.last_report_time)
            except ValueError:
                return None
        return None

    def get_reported_paper_ids(self, user_id: str, topic: str) -> Set[str]:
        """获取已报告的论文ID集合"""
        key = self._make_key(user_id, topic)
        state = self.states.get(key)
        return set(state.last_paper_ids) if state else set()

    def update_report_state(self, user_id: str, topic: str,
                           domain: str, new_papers: List[Dict]):
        """更新报告状态"""
        key = self._make_key(user_id, topic)

        # 获取旧状态
        old_state = self.states.get(key)
        old_paper_ids = old_state.last_paper_ids if old_state else []
        old_count = old_state.report_count if old_state else 0

        # 生成新论文的ID
        new_paper_ids = [self._paper_id(p) for p in new_papers]

        # 合并论文ID（去重）
        all_paper_ids = list(set(old_paper_ids + new_paper_ids))

        # 创建新状态
        new_state = ReportState(
            last_report_time=datetime.now(timezone.utc).isoformat(),
            last_paper_ids=all_paper_ids,
            user_id=user_id,
            topic=topic,
            domain=domain,
            report_count=old_count + 1
        )

        self.states[key] = new_state
        self._save_states()

    def _paper_id(self, paper: Dict) -> str:
        """生成论文唯一ID"""
        # 优先使用DOI
        doi = paper.get("doi", "")
        if doi:
            return f"doi:{doi}"

        # 其次使用标题+第一作者
        title = paper.get("title", "")
        authors = paper.get("authors", [])
        if title and authors:
            first_author = authors[0] if isinstance(authors, list) else str(authors)
            return f"title:{hash((title, first_author))}"

        # 最后使用URL
        url = paper.get("url", "")
        if url:
            return f"url:{hash(url)}"

        # 降级方案：使用标题hash
        return f"hash:{hash(title)}"

    def _make_key(self, user_id: str, topic: str) -> str:
        """生成状态键"""
        # 规范化topic（移除空格和特殊字符，转小写）
        normalized_topic = "".join(c.lower() for c in topic if c.isalnum())
        return f"{user_id}:{normalized_topic}"

    def _load_states(self) -> Dict[str, ReportState]:
        """加载状态文件"""
        if not os.path.exists(self.state_file):
            return {}

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 反序列化
            states = {}
            for key, state_dict in data.items():
                try:
                    states[key] = ReportState(**state_dict)
                except TypeError:
                    continue  # 跳过格式不正确的状态

            return states
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_states(self):
        """保存状态文件"""
        try:
            # 转换为可序列化的格式
            data = {}
            for key, state in self.states.items():
                data[key] = asdict(state)

            # 确保目录存在
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save report state: {e}", file=sys.stderr)


# 全局状态管理器实例
_global_state_manager = None

def get_state_manager() -> ReportStateManager:
    """获取全局状态管理器实例"""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = ReportStateManager()
    return _global_state_manager


if __name__ == "__main__":
    # 测试代码
    manager = ReportStateManager("test_state.json")

    # 测试：更新状态
    test_papers = [
        {"title": "Paper 1", "doi": "10.1234/paper1"},
        {"title": "Paper 2", "doi": "10.1234/paper2"}
    ]

    manager.update_report_state(
        user_id="test@example.com",
        topic="machine learning",
        domain="ai",
        new_papers=test_papers
    )

    # 测试：读取状态
    last_time = manager.get_last_report_time("test@example.com", "machine learning")
    paper_ids = manager.get_reported_paper_ids("test@example.com", "machine learning")

    print(f"Last report time: {last_time}")
    print(f"Reported paper IDs: {paper_ids}")
