#!/usr/bin/env python3
"""
MCP智能触发功能测试
验证自然语言自动判断MCP搜索的能力
"""

import sys
sys.path.insert(0, r'C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-email-service\scripts')

def test_intelligent_mcp_trigger():
    """测试MCP智能触发功能"""
    print("=" * 70)
    print("MCP智能触发功能测试")
    print("=" * 70)
    print()

    from mcp_trigger import IntelligentMCPTrigger, AdaptiveMCPController

    trigger = IntelligentMCPTrigger()
    controller = AdaptiveMCPController()

    # 测试查询场景
    test_cases = [
        {
            "query": "统计学这一周的最新研究成果",
            "should_enable": True,
            "trigger_type": "realtime",
            "description": "实时性需求 - 应该启用"
        },
        {
            "query": "搜索因果推断的GitHub实现",
            "should_enable": True,
            "trigger_type": "code",
            "description": "代码需求 - 应该启用"
        },
        {
            "query": "给我找一篇关于机器学习的论文",
            "should_enable": False,
            "trigger_type": "normal",
            "description": "普通查询 - 不启用"
        },
        {
            "query": "全面搜索深度学习领域的所有研究",
            "should_enable": True,
            "trigger_type": "comprehensive",
            "description": "全面性需求 - 应该启用"
        },
        {
            "query": "搜索最近发布的AI论文",
            "should_enable": True,
            "trigger_type": "realtime",
            "description": "实时性需求 - 应该启用"
        },
        {
            "query": "查找统计学领域的最新代码实现",
            "should_enable": True,
            "trigger_type": "code",
            "description": "代码需求 - 应该启用"
        },
        {
            "query": "搜索2023年发表的论文",
            "should_enable": False,
            "trigger_type": "normal",
            "description": "普通查询 - 不启用"
        }
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_enable = test_case["should_enable"]

        print(f"[测试 {i}/{len(test_cases)}] '{query}'")
        print("-" * 70)

        # 测试触发判断
        result = trigger.should_enable_mcp_search(query)

        # 验证结果
        if result["should_enable"] == expected_enable:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        print(f"  预期: {'启用' if expected_enable else '不启用'}")
        print(f"  实际: {'启用' if result['should_enable'] else '不启用'}")
        print(f"  触发原因: {result['trigger_reason']}")
        print(f"  置信度: {result['confidence']*100:.0f}%")
        print(f"  建议操作: {result['recommended_action']}")
        print(f"  {status} - {test_case['description']}")
        print()

    # 测试用户通知
    print("=" * 70)
    print("用户通知测试")
    print("=" * 70)
    print()

    notifications = [
        ("统计学这一周的最新研究成果", True),
        ("给我找一篇关于机器学习的论文", False)
    ]

    for query, should_enable in notifications:
        print(f"查询: '{query}'")

        result = trigger.should_enable_mcp_search(query)
        notification = controller.get_user_notification(result)

        print(f"通知: {notification}")
        print()

    # 总结
    print("=" * 70)
    print(f"测试总结: {passed} 通过, {failed} 失败")
    print("=" * 70)

    if failed == 0:
        print("✅ 所有测试通过！MCP智能触发功能正常工作。")
        print()
        print("🎯 现在用户可以用自然语言触发MCP搜索：")
        print("  • '最新' → 自动启用MCP实时搜索")
        print("  • 'GitHub' → 自动搜索代码实现")
        print("  • '全面' → 自动启用全面搜索")
        print()
        return 0
    else:
        print(f"❌ {failed} 个测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    exit_code = test_intelligent_mcp_trigger()
    sys.exit(exit_code)
