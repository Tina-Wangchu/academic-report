#!/usr/bin/env python3
"""
Test Core Features - 核心功能测试脚本

测试项目：
1. 质量评分系统
2. 代表性论文筛选
3. 增量式周期报告
"""

import sys
import json
from datetime import datetime, timezone

# 添加当前目录到Python路径
sys.path.insert(0, '.')

from quality_scorer import PaperQualityScorer
from representative_selector import RepresentativePaperSelector
from report_state_manager import ReportStateManager
from incremental_search import IncrementalPaperSearcher


def test_quality_scorer():
    """测试质量评分系统"""
    print("=" * 60)
    print("测试1: 质量评分系统")
    print("=" * 60)

    scorer = PaperQualityScorer()

    test_paper = {
        "title": "Deep Learning Breakthrough in Medical Imaging",
        "citationCount": 150,
        "journal": "Nature",
        "authors": ["Geoffrey Hinton", "Yann LeCun"],
        "abstract": "This novel breakthrough presents state-of-the-art results surpassing all previous methods in medical image analysis.",
        "published": "2026-06-01T10:00:00Z"
    }

    score = scorer.score_paper(test_paper)

    print(f"[OK] Paper Title: {test_paper['title']}")
    print(f"[OK] Quality Score: {score}/100")
    print(f"  - Citations: {test_paper['citationCount']}")
    print(f"  - Journal: {test_paper['journal']}")
    print(f"  - Authors: {', '.join(test_paper['authors'])}")
    print()


def test_representative_selector():
    """测试代表性论文筛选"""
    print("=" * 60)
    print("测试2: 代表性论文筛选")
    print("=" * 60)

    selector = RepresentativePaperSelector()

    test_papers = [
        {"title": "Deep Learning for Image Recognition", "quality_score": 85},
        {"title": "Image Recognition using Neural Networks", "quality_score": 80},
        {"title": "Image Classification with CNNs", "quality_score": 75},
        {"title": "Statistical Methods for ML", "quality_score": 90},
        {"title": "Bayesian Inference in High Dimensions", "quality_score": 88},
        {"title": "Machine Learning Theory", "quality_score": 70},
    ]

    print(f"输入: {len(test_papers)} 篇论文")

    selected = selector.select_representative_papers(test_papers, max_count=3)

    print(f"输出: {len(selected)} 篇代表性论文")
    for i, p in enumerate(selected, 1):
        print(f"  {i}. {p['title']} (分数: {p['quality_score']})")
    print()


def test_state_manager():
    """测试状态管理器"""
    print("=" * 60)
    print("测试3: 周期报告状态管理")
    print("=" * 60)

    manager = ReportStateManager("test_state.json")

    user_id = "test@example.com"
    topic = "machine learning"

    # 第一次报告
    print("第一次报告:")
    test_papers_1 = [
        {"title": "Paper 1", "doi": "10.1234/paper1"},
        {"title": "Paper 2", "doi": "10.1234/paper2"}
    ]

    manager.update_report_state(user_id, topic, "ai", test_papers_1)

    last_time = manager.get_last_report_time(user_id, topic)
    paper_ids = manager.get_reported_paper_ids(user_id, topic)

    print(f"  [OK] 上次报告时间: {last_time}")
    print(f"  [OK] 已报告论文数: {len(paper_ids)}")
    print(f"  [OK] 论文ID: {list(paper_ids)}")

    # 第二次报告（模拟）
    print("\n第二次报告（7天后）:")
    test_papers_2 = [
        {"title": "Paper 3", "doi": "10.1234/paper3"},
        {"title": "Paper 4", "doi": "10.1234/paper4"}
    ]

    manager.update_report_state(user_id, topic, "ai", test_papers_2)

    paper_ids_after = manager.get_reported_paper_ids(user_id, topic)

    print(f"  [OK] 已报告论文数: {len(paper_ids_after)}")
    print(f"  [OK] 论文ID: {list(paper_ids_after)}")
    print(f"  [OK] 新增论文: {len(paper_ids_after) - len(paper_ids)} 篇")
    print()


def test_incremental_search():
    """测试增量式搜索"""
    print("=" * 60)
    print("测试4: 增量式周期报告搜索")
    print("=" * 60)

    user_id = "test@example.com"
    topic = "artificial intelligence"

    config = {
        "research_topic": topic,
        "user_id": user_id,
        "time_range": "7d",
        "max_results": 5,
        "domain": "ai"
    }

    searcher = IncrementalPaperSearcher(config, user_id)

    # 第一次搜索（初始化）
    print("第一次搜索（初始化状态）:")
    result1 = searcher.search_new_papers()

    if result1.get("status") == "success":
        print(f"  [OK] 状态: {result1.get('status')}")
        print(f"  [OK] 找到: {result1.get('total_found')} 篇")
        print(f"  [OK] 说明: {result1.get('note', 'N/A')}")
    else:
        print(f"  [X] 搜索失败: {result1.get('error')}")
    print()

    # 第二次搜索（应该显示增量）
    print("第二次搜索（增量模式）:")
    result2 = searcher.search_new_papers()

    if result2.get("status") == "success":
        print(f"  [OK] 状态: {result2.get('status')}")
        print(f"  [OK] 找到: {result2.get('total_found')} 篇")
        print(f"  [OK] 说明: {result2.get('note', 'N/A')}")
    else:
        print(f"  [X] 搜索失败: {result2.get('error')}")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("核心功能测试 - Core Features Test")
    print("=" * 60 + "\n")

    try:
        test_quality_scorer()
        test_representative_selector()
        test_state_manager()
        test_incremental_search()

        print("=" * 60)
        print("[OK] 所有测试完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
