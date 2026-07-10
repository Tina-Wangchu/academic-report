#!/usr/bin/env python3
"""
测试智能查询解析器
"""

import sys
sys.path.insert(0, r'C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-email-service\scripts')

from intelligent_query_parser import IntelligentQueryParser

def test_parser():
    """测试智能解析器的功能"""
    print("=" * 70)
    print("智能查询解析器测试")
    print("=" * 70)
    print()

    parser = IntelligentQueryParser()

    # 测试用例
    test_cases = [
        {
            "query": "统计学这一周的最新研究成果",
            "expected_domain": "statistics",
            "expected_time_range": "7d"
        },
        {
            "query": "人工智能领域的最新研究",
            "expected_domain": "ai",
            "expected_time_range": "1y"
        },
        {
            "query": "搜索最近一个月机器学习的论文",
            "expected_domain": "ai",
            "expected_time_range": "30d"
        },
        {
            "query": "金融统计本周新研究",
            "expected_domain": "finance",
            "expected_time_range": "7d"
        }
    ]

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_domain = test_case["expected_domain"]
        expected_time_range = test_case["expected_time_range"]

        print(f"测试 {i}/{len(test_cases)}: '{query}'")
        print("-" * 70)

        try:
            result = parser.parse_user_query(query, use_cache=False)

            # 验证领域检测
            if result["domain"] == expected_domain:
                print(f"  ✅ 领域检测正确: {result['domain']}")
            else:
                print(f"  ❌ 领域检测错误: 期望 {expected_domain}, 实际 {result['domain']}")
                failed += 1
                continue

            # 验证时间范围检测
            if result["time_range"] == expected_time_range:
                print(f"  ✅ 时间范围正确: {result['time_range']}")
            else:
                print(f"  ❌ 时间范围错误: 期望 {expected_time_range}, 实际 {result['time_range']}")
                failed += 1
                continue

            # 显示详细信息
            print(f"  📊 置信度: {result['confidence']:.2f}")
            print(f"  🔑 主要关键词: {result['primary_keywords']}")
            print(f"  📈 扩展关键词: {result['expanded_keywords'][:3]}...")
            print(f"  🎯 意图识别: {result['detected_intent']}")

            passed += 1
            print("  ✅ 测试通过")
            print()

        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            failed += 1
            print()

    # 总结
    print("=" * 70)
    print(f"测试总结: {passed} 通过, {failed} 失败")
    print("=" * 70)

    if failed == 0:
        print("✅ 所有测试通过！智能解析器工作正常。")
        return 0
    else:
        print(f"⚠️ {failed} 个测试失败，需要修复。")
        return 1

if __name__ == "__main__":
    exit_code = test_parser()
    sys.exit(exit_code)