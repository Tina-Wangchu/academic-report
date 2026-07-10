#!/usr/bin/env python3
"""
简化测试脚本 - 验证Hermes修复状态
"""

import sys
import os
from pathlib import Path

def test_fixes():
    """测试修复状态"""
    print("=" * 80)
    print("Hermes修复状态验证")
    print("=" * 80)
    print()

    # 检查关键文件
    files_to_check = [
        ("HTML报告生成器", "C:/Users/lanpi/AppData/Local/hermes/skills/academic/report-generator/scripts/generate_report_complex.py"),
        ("智能搜索执行器", "C:/Users/lanpi/AppData/Local/hermes/skills/academic/paper-email-service/scripts/intelligent_search_executor.py"),
        ("Paper搜索", "C:/Users/lanpi/AppData/Local/hermes/skills/academic/paper-search/scripts/paper_search.py"),
        ("配置文件", "C:/Users/lanpi/AppData/Local/hermes/skills/academic/paper-email-service/config/default_config.yaml")
    ]

    print("文件存在性检查:")
    print()

    for name, path in files_to_check:
        if Path(path).exists():
            print(f"[OK] {name}: 存在")

            # 检查文件内容
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "html" in path.lower():
                    if "HTMLReportGenerator" in content or "<html>" in content:
                        print(f"     └─ 包含HTML生成代码")
                    elif "format: \"html\"" in content:
                        print(f"     └─ 配置为HTML格式")
                    else:
                        print(f"     └─ 但未找到HTML相关代码")

                if "workflow_executor" in name.lower() or "intelligent" in name.lower():
                    if "IntelligentSearchExecutor" in content:
                        print(f"     └─ 集成智能搜索执行器")
                    else:
                        print(f"     └─ 检查中...")

            except Exception as e:
                print(f"     └─ 无法读取内容: {e}")

        else:
            print(f"[MISS] {name}: 不存在")
            print(f"     路径: {path}")

    print()
    print("=" * 80)
    print("操作建议:")
    print("1. 如果文件存在性检查通过，重启Hermes")
    print("2. 如果文件缺失，需要重新部署修复")
    print("3. 重启后重新测试您的请求")
    print("=" * 80)

if __name__ == "__main__":
    test_fixes()