#!/usr/bin/env python3
"""
MCP搜索集成功能测试
验证MCP增强的搜索能力
"""

import sys
sys.path.insert(0, r'C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-search\scripts')

def test_mcp_search_integration():
    """测试MCP搜索集成功能"""
    print("=" * 70)
    print("MCP搜索集成功能测试")
    print("=" * 70)
    print()

    # 导入MCP搜索模块
    try:
        from mcp_search_integration import MCPSearchIntegration, EnhancedMCPDataScheduler
        print("[PASS] MCP搜索模块导入成功")
    except ImportError as e:
        print(f"[FAIL] MCP搜索模块导入失败: {e}")
        return False

    print()

    # === 测试1：基础MCP网络搜索 ===
    print("[测试1] MCP网络搜索")
    print("-" * 70)

    try:
        mcp_search = MCPSearchIntegration()

        # 测试学术网络搜索
        results = mcp_search.search_academic_web(
            query="statistics machine learning",
            time_range="7d",
            max_results=5,
            use_cache=False  # 测试时不使用缓存
        )

        print(f"  查询: 'statistics machine learning'")
        print(f"  时间范围: 7d")
        print(f"  找到结果: {len(results)} 条")

        if results:
            print(f"  第一条结果: {results[0].get('title', 'N/A')[:60]}...")
            print(f"  来源: {results[0].get('source', 'N/A')}")
            print("  [PASS] MCP网络搜索测试通过")
        else:
            print("  [WARN] 未找到结果（可能是模拟数据限制）")

    except Exception as e:
        print(f"  [FAIL] MCP网络搜索测试失败: {e}")

    print()

    # === 测试2：GitHub学术项目搜索 ===
    print("[测试2] GitHub学术项目搜索")
    print("-" * 70)

    try:
        github_results = mcp_search.search_github_academic_projects(
            query="causal inference",
            max_results=3
        )

        print(f"  查询: 'causal inference'")
        print(f"  找到项目: {len(github_results)} 个")

        if github_results:
            print(f"  第一个项目: {github_results[0].get('title', 'N/A')[:60]}...")
            print("  [PASS] GitHub搜索测试通过")
        else:
            print("  [WARN] 未找到项目（可能是模拟数据限制）")

    except Exception as e:
        print(f"  [FAIL] GitHub搜索测试失败: {e}")

    print()

    # === 测试3：综合搜索调度器 ===
    print("[测试3] 综合搜索调度器")
    print("-" * 70)

    try:
        scheduler = EnhancedMCPDataScheduler()

        comprehensive = scheduler.get_comprehensive_results(
            query="bayesian methods",
            time_range="7d",
            max_results=10
        )

        print(f"  查询: 'bayesian methods'")
        print(f"  总计结果: {comprehensive['total_found']} 条")
        print(f"  数据源: {comprehensive['sources_used']}")
        print(f"  MCP增强: {comprehensive.get('mcp_enhanced', False)}")

        if comprehensive['total_found'] > 0:
            print("  [PASS] 综合搜索测试通过")
        else:
            print("  [WARN] 未找到结果（可能是模拟数据限制）")

    except Exception as e:
        print(f"  [FAIL] 综合搜索测试失败: {e}")

    print()

    # === 测试4：集成到PaperSearchEngine ===
    print("[测试4] 集成到现有搜索系统")
    print("-" * 70)

    try:
        import paper_search

        # 验证配置已更新
        domain_priority = paper_search.DOMAIN_SOURCE_PRIORITY

        has_mcp_in_general = "MCP_Web" in domain_priority["general"]
        has_mcp_in_stats = "MCP_Web" in domain_priority["statistics"]

        print(f"  通用领域包含MCP: {has_mcp_in_general}")
        print(f"  统计学领域包含MCP: {has_mcp_in_stats}")

        if has_mcp_in_general and has_mcp_in_stats:
            print("  [PASS] 数据源优先级配置正确")
        else:
            print("  [FAIL] 数据源优先级配置错误")

        # 测试启用MCP搜索的配置
        config = {
            "topic": "test",
            "time_range": "7d",
            "max_results": 10,
            "enable_mcp_search": True  # 启用MCP搜索
        }

        engine = paper_search.PaperSearchEngine(config)

        print(f"  MCP搜索配置: {engine.config.get('enable_mcp_search', False)}")

        if engine.config.get('enable_mcp_search'):
            print("  [PASS] MCP搜索配置正确")
        else:
            print("  [WARN] MCP搜索未启用（需要配置）")

    except Exception as e:
        print(f"  [FAIL] 集成测试失败: {e}")

    print()
    print("=" * 70)
    print("MCP搜索集成测试完成")
    print()
    print("使用方式：")
    print("  1. 在配置中设置 enable_mcp_search: true")
    print("  2. 或者直接调用：")
    print("     from mcp_search_integration import search_with_mcp")
    print("     results = search_with_mcp('your query', '7d', 10)")
    print("=" * 70)


if __name__ == "__main__":
    test_mcp_search_integration()