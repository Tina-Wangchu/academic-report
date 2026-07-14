"""
时间戳管理器（定时/增量报告模式 / Module 7）

职责：
- 持久化每个「主题」的上次报告时间戳到 `~/.hermes/academic_scholar_timestamps.json`
  （`{topic_key: last_run_iso}`），供增量检索计算 `[上次, 现在]` 窗口。
- topic_key 由 (query, research_field) 确定性生成（可读前缀 + 短 hash 防碰撞）。
- 防御加载（缺失/损坏 JSON → 空）、原子写（tmp + os.replace）。

设计原则：
- 复用 `utils.get_timestamp_file_path()`（既定存储路径）与 `safe_filename()`。
- 单例 `get_timestamp_manager()`，对齐 `get_config_manager()` / `get_rate_limiter()` 模式。
- 绝不因文件问题抛异常——损坏即按空处理（最坏情况：各主题从基线重跑）。
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from utils import get_timestamp_file_path, safe_filename

logger = logging.getLogger(__name__)


class TimestampManager:
    """持久化 {topic_key: last_run_iso}，供增量检索使用。"""

    def __init__(self, file_path: Optional[Path] = None):
        """默认 get_timestamp_file_path()；测试可注入 tmp_path。"""
        self.file_path = Path(file_path) if file_path else get_timestamp_file_path()

    # ----------------------------- keying ------------------------------ #

    @staticmethod
    def topic_key(query: str, research_field: str) -> str:
        """
        确定性 topic key：规范化 query+field → 「可读前缀 + 短 hash」。
        可读段便于人工排查；hash 防碰撞与特殊字符问题。
        """
        norm = f"{(query or '').strip().lower()}|{(research_field or '').strip().lower()}"
        digest = hashlib.md5(norm.encode("utf-8")).hexdigest()[:10]
        readable = safe_filename((query or "topic").strip().lower())[:16] or "topic"
        return f"{readable}_{digest}"

    # ------------------------------ read -------------------------------- #

    def _load(self) -> Dict[str, str]:
        """防御性加载：缺失/损坏 JSON / 非 dict → {}（不抛异常）。"""
        if not self.file_path.exists():
            return {}
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("时间戳文件损坏，按空处理: %s", e)
            return {}

    def get_last_run(self, topic_key: str) -> Optional[datetime]:
        """取该主题上次报告时间；无记录或非法值 → None。"""
        raw = self._load().get(topic_key)
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            logger.warning("时间戳值非法 %s=%r，按无记录处理", topic_key, raw)
            return None

    # ------------------------------ write ------------------------------- #

    def update_last_run(self, topic_key: str,
                        when: Optional[datetime] = None) -> datetime:
        """
        原子写：写临时文件再 os.replace（同盘原子；Windows 亦然）。
        返回写入的时间戳（默认 datetime.now()）。
        """
        when = when or datetime.now()
        data = self._load()
        data[topic_key] = when.isoformat()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)  # ~/.hermes 可能不存在
        tmp = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.file_path)   # 原子覆盖
        return when


# ---------------------------------------------------------------------- #
# 单例
# ---------------------------------------------------------------------- #

_global_tm: Optional[TimestampManager] = None


def get_timestamp_manager() -> TimestampManager:
    """全局 TimestampManager 单例。"""
    global _global_tm
    if _global_tm is None:
        _global_tm = TimestampManager()
    return _global_tm


# ---------------------------------------------------------------------- #
# 命令行入口（查看/重置时间戳）
# ---------------------------------------------------------------------- #

def main() -> int:
    """查看或重置时间戳：python timestamp_manager.py [--reset <topic_key|all>]"""
    import argparse

    parser = argparse.ArgumentParser(description="管理定时报告时间戳")
    parser.add_argument("--reset", metavar="KEY", help="重置指定 topic_key（或 all）的时间戳")
    args = parser.parse_args()

    tm = TimestampManager()
    if args.reset:
        data = tm._load()
        if args.reset == "all":
            data = {}
        else:
            data.pop(args.reset, None)
        tm.file_path.parent.mkdir(parents=True, exist_ok=True)
        tm.file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已重置: {args.reset}")
        return 0

    data = tm._load()
    if not data:
        print(f"（无时间戳记录，文件: {tm.file_path}）")
    else:
        print(f"时间戳记录（{tm.file_path}）:")
        for k, v in data.items():
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
