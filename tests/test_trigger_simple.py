#!/usr/bin/env python3
"""
MCP智能触发功能简化测试（无emoji版本）
"""

import sys
sys.path.insert(0, r'C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-email-service\scripts')

def test_mcp_trigger():
    """简化测试 - 验证智能触发逻辑"""
    print("=" * 70)
    print("MCP智能触发功能验证")
    print("=" * 70)
    print()

    from mcp_trigger import IntelligentMCPTrigger, AdaptiveMCPController

    trigger = IntelligentMCPTrigger()
    controller = AdaptiveMCPController()

    # 测试关键场景
    tests = [
        ("统计学这一周的最新研究成果", "应该启用（实时需求）"),
        ("搜索因果推断的GitHub实现", "应该启用（代码需求）"),
        ("给我找一篇关于机器学习的论文", "不启用（普通查询）"),
        ("全面搜索深度学习领域的所有研究", "应该启用（全面需求）"),
        ("搜索最近发布的AI论文", "应该启用（实时需求）"),
    ]

    all_pass = True

    for query, expected in tests:
        print(f"查询: '{query}'")
        result = trigger.should_enable_mcp_search(query)

        should_enable = "启用MCP" if result["should_enable"] else "不启用MCP"
        print(f"结果: {should_enable}")
        print(f"原因: {result['trigger_reason']}")
        print(f"预期: {expected}")

        if "应该启用" in expected and result["should_enable"]:
            print("[PASS]")
        elif "不启用" in expected and not result["should_enable"]:
            print("[PASS]")
        else:
            print("[FAIL]")
            all_pass = False

        print()

    # 测试工作流集成
    print("=" * 70)
    print("工作流集成测试")
    print("=" * 70)
    print()

    # 模拟工作流参数
    base_config = {
        "topic": "test",
        "time_range": "1y",
        "max_results": 10,
        "enable_mcp_search": False
    }

    # 测试实时查询
    realtime_query = "统计学这一周的最新研究成果"
    optimized = controller.determine_search_strategy(realtime_query, base_config)

    print(f"查询: '{realtime_query}'")
    print(f"原始配置: enable_mcp_search = False")
    print(f"优化配置: enable_mcp_search = {optimized['enable_mcp_search']}")
    print(f"触发原因: {optimized.get('mcp_trigger_reason', 'N/A')}")

    if optimized['enable_mcp_search']:
        print("[PASS] 实时查询自动启用MCP")
    else:
        print("[FAIL] 实时查询未启用MCP")

    print()

    # 测试普通查询
    normal_query = "搜索2023年发表的论文"
    optimized_normal = controller.determine_search_strategy(normal_query, base_config)

    print(f"查询: '{normal_query}'")
    print(f"原始配置: enable_mcp_search = False")
    print(f"优化配置: enable_mcp_search = {optimized_normal['enable_mcp_search']}")

    if not optimized_normal['enable_mcp_search']:
        print("[PASS] 普通查询保持MCP关闭")
    else:
        print("[FAIL] 普通查询错误启用MCP")

    print()

    # 总结
    print("=" * 70)
    if all_pass:
        print("所有测试通过！")
        print()
        print("MCP智能触发功能已完成：")
        print("  • 用户无需知道MCP是什么")
        print("  • 自然语言自动判断是否启用")
        print("  • 实时需求自动启用MCP搜索")
        print("  • 代码需求自动搜索GitHub")
        print("  • 全面需求自动扩大覆盖")
        print()
        print("用户触发示例：")
        print("  1. '最新论文' → 自动启用MCP实时搜索")
        print("  2. 'GitHub实现' → 自动搜索代码库")
        print("  3. '全面搜索' → 自动扩大覆盖范围")
        print("  4. 普通查询 → 使用快速稳定的传统API")
        print()
        return 0
    else:
        print("部分测试失败")
        return 1


if __name__ == "__main__":
    exit_code = test_mcp_trigger()
    sys.exit(exit_code)