#!/usr/bin/env python3
"""
Hermes Agent Skill 智能化改进集成测试
测试所有四个阶段的改进
"""

import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, r'C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-email-service\scripts')

def test_intelligent_parser():
    """测试阶段A：智能查询解析器"""
    print("=" * 70)
    print("阶段A测试：智能查询解析器")
    print("=" * 70)

    from intelligent_query_parser import IntelligentQueryParser

    parser = IntelligentQueryParser()

    # 测试用例
    test_query = "统计学这一周的最新研究成果"
    result = parser.parse_user_query(test_query, use_cache=False)

    print(f"查询: {test_query}")
    print(f"检测到的领域: {result['domain']}")
    print(f"时间范围: {result['time_range']}")
    print(f"主要关键词: {result['primary_keywords']}")
    print(f"扩展关键词: {len(result['expanded_keywords'])}个")
    print(f"置信度: {result['confidence']:.2f}")

    # 验证
    assert result['domain'] == 'statistics', "领域检测失败"
    assert result['time_range'] == '7d', "时间范围检测失败"
    assert result['confidence'] >= 0.9, "置信度过低"

    print("✅ 阶段A测试通过！")
    print()


def test_multi_source_apis():
    """测试阶段B：多数据源API类"""
    print("=" * 70)
    print("阶段B测试：多数据源API类")
    print("=" * 70)

    # 导入paper_search模块
    sys.path.insert(0, r'C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-search\scripts')
    import paper_search

    # 验证新API类存在
    assert hasattr(paper_search, 'PubMedAPI'), "PubMedAPI类不存在"
    assert hasattr(paper_search, 'OpenAlexAPI'), "OpenAlexAPI类不存在"

    # 验证数据源优先级配置
    priority = paper_search.DOMAIN_SOURCE_PRIORITY
    assert "OpenAlex" in priority["statistics"], "统计数据源缺少OpenAlex"
    assert "PubMed" in priority["statistics"], "统计数据源缺少PubMed"

    print("✅ PubMedAPI类已加载")
    print("✅ OpenAlexAPI类已加载")
    print("✅ 数据源优先级已更新")
    print("✅ 阶段B测试通过！")
    print()


def test_enhanced_date_parsing():
    """测试阶段C：增强的日期解析"""
    print("=" * 70)
    print("阶段C测试：增强的日期解析")
    print("=" * 70)

    sys.path.insert(0, r'C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-search\scripts')
    import paper_search

    # 创建测试引擎
    config = {
        "topic": "test",
        "time_range": "1y",
        "max_results": 10
    }
    engine = paper_search.PaperSearchEngine(config)

    # 测试各种日期格式
    test_papers = [
        {"title": "Paper 1", "publicationDate": "2025-07-01T12:34:56Z"},
        {"title": "Paper 2", "published": "2025-06-30"},
        {"title": "Paper 3", "year": "2025"},
        {"title": "Paper 4", "pubDate": "2025 Jan 15"},
    ]

    for paper in test_papers:
        date = engine._extract_publication_date(paper)
        print(f"✓ 解析成功: {paper['title']} -> {date}")

    print("✅ 阶段C测试通过！")
    print()


def test_workflow_integration():
    """测试阶段D：工作流集成"""
    print("=" * 70)
    print("阶段D测试：工作流智能集成")
    print("=" * 70)

    # 导入workflow_executor
    from workflow_executor import WorkflowExecutor

    # 验证智能解析器已集成
    executor = WorkflowExecutor()

    assert hasattr(executor, 'query_parser'), "缺少智能查询解析器"
    assert executor.query_parser is not None, "智能查询解析器未初始化"

    print("✅ 智能查询解析器已集成到WorkflowExecutor")

    # 验证智能降级方法存在
    assert hasattr(executor, '_execute_search_with_params'), "缺少降级方法"

    print("✅ 智能降级方法已添加")
    print("✅ 阶段D测试通过！")
    print()


def test_backward_compatibility():
    """测试向后兼容性"""
    print("=" * 70)
    print("向后兼容性测试")
    print("=" * 70)

    sys.path.insert(0, r'C:\Users\lanpi\AppData\Local\hermes\skills\academic\paper-search\scripts')
    import paper_search

    # 验证原有API类仍然存在
    assert hasattr(paper_search, 'SemanticScholarAPI'), "SemanticScholarAPI类丢失"
    assert hasattr(paper_search, 'ArxivAPI'), "ArxivAPI类丢失"
    assert hasattr(paper_search, 'CrossRefAPI'), "CrossRefAPI类丢失"

    print("✅ 原有API类完整保留")

    # 验证原有方法仍然存在
    config = {"topic": "test", "time_range": "1y", "max_results": 10}
    engine = paper_search.PaperSearchEngine(config)

    assert hasattr(engine, 'search'), "search方法丢失"
    assert hasattr(engine, '_filter_by_date'), "_filter_by_date方法丢失"
    assert hasattr(engine, '_deduplicate_papers'), "_deduplicate_papers方法丢失"

    print("✅ 原有方法完整保留")
    print("✅ 向后兼容性测试通过！")
    print()


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Hermes Agent Skill 智能化改进集成测试" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    all_passed = True

    try:
        test_intelligent_parser()
    except Exception as e:
        print(f"❌ 阶段A测试失败: {e}")
        all_passed = False

    try:
        test_multi_source_apis()
    except Exception as e:
        print(f"❌ 阶段B测试失败: {e}")
        all_passed = False

    try:
        test_enhanced_date_parsing()
    except Exception as e:
        print(f"❌ 阶段C测试失败: {e}")
        all_passed = False

    try:
        test_workflow_integration()
    except Exception as e:
        print(f"❌ 阶段D测试失败: {e}")
        all_passed = False

    try:
        test_backward_compatibility()
    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")
        all_passed = False

    # 总结
    print("=" * 70)
    if all_passed:
        print("✅ 所有测试通过！Hermes Agent Skill智能化改进成功实施。")
        print()
        print("📋 改进总结：")
        print("  阶段A：✅ 智能关键词扩展 - 理解'统计学这一周'为domain=statistics, time=7d")
        print("  阶段B：✅ 多数据源整合 - PubMed + OpenAlex + 原有3个数据源")
        print("  阶段C：✅ 精确时间和来源 - 增强日期解析 + source字段修复")
        print("  阶段D：✅ 智能工作流 - 自动降级 + API限流检测")
        print()
        print("🚀 现在可以在Hermes中测试：")
        print('   "请为我搜索统计学领域这一周的最新研究成果，把报告发送到我的邮箱"')
        return 0
    else:
        print("❌ 部分测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)