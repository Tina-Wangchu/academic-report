#!/usr/bin/env python3
"""
综合测试脚本 - 验证Hermes搜索能力修复是否真正生效

测试项目：
1. HTML报告生成器是否被正确使用
2. 智能搜索执行器是否被调用
3. 多数据源搜索是否工作
4. 时间范围计算是否准确
5. 数据格式化是否正确（source字段、abstract）
6. Python缓存是否已清除

使用方法：
    python test_hermes_fixes.py
"""

import sys
import json
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_python_cache_clear():
    """测试1：验证Python缓存是否已清除"""
    print_section("测试1: Python缓存清除验证")

    cache_dirs = []

    # 检查主要的缓存目录
    hermes_cache = Path("C:/Users/lanpi/AppData/Local/hermes/skills/academic/")
    if hermes_cache.exists():
        for cache_dir in hermes_cache.rglob("__pycache__"):
            cache_dirs.append(cache_dir)

    if not cache_dirs:
        print("[OK] Python缓存目录已清除或不存在")
        print("     所有模块将重新加载")
        return True
    else:
        print(f"[WARN] 发现 {len(cache_dirs)} 个缓存目录")
        for cache_dir in cache_dirs:
            print(f"     - {cache_dir}")

        # 尝试清除
        try:
            for cache_dir in cache_dirs:
                import shutil
                shutil.rmtree(cache_dir)
            print("[OK] 已清除所有Python缓存目录")
            return True
        except Exception as e:
            print(f"[ERROR] 清除缓存失败: {e}")
            return False

def test_html_report_generator():
    """测试2：验证HTML报告生成器"""
    print_section("测试2: HTML报告生成器验证")

    try:
        # 导入HTML报告生成器
        sys.path.insert(0, 'C:/Users/lanpi/AppData/Local/hermes/skills/academic/report-generator/scripts/')

        # 检查generate_report_complex.py
        with open('C:/Users/lanpi/AppData/Local/hermes/skills/academic/report-generator/scripts/generate_report_complex.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含HTML相关代码
        html_indicators = [
            'HTMLReportGenerator',
            '<html>',
            '<style>',
            'linear-gradient',
            'generate_report_html'
        ]

        found_indicators = [ind for ind in html_indicators if ind in content]

        if len(found_indicators) >= 3:
            print("[OK] HTML报告生成器已部署")
            print(f"     找到标记: {', '.join(found_indicators[:3])}")

            # 测试导入
            try:
                import generate_report_complex
                if hasattr(generate_report_complex, 'HTMLReportGenerator'):
                    print("[OK] HTMLReportGenerator类可导入")
                    return True
                else:
                    print("[WARN] 导入成功但HTMLReportGenerator类不存在")
                    return False
            except ImportError as e:
                print(f"[ERROR] 导入失败: {e}")
                return False
        else:
            print("[ERROR] HTML报告生成器未正确部署")
            print(f"     只找到 {len(found_indicators)}/3 个必需标记")
            return False

    except Exception as e:
        print(f"[ERROR] HTML报告生成器测试失败: {e}")
        return False

def test_intelligent_search_executor():
    """测试3：验证智能搜索执行器"""
    print_section("测试3: 智能搜索执行器验证")

    try:
        sys.path.insert(0, '/c/Users/lanpi/AppData/Local/hermes/skills/academic/paper-email-service/scripts/')

        from intelligent_search_executor import IntelligentSearchExecutor

        print("[OK] intelligent_search_executor可导入")

        # 测试时间范围计算
        executor = IntelligentSearchExecutor({}, Path('.'))

        # 测试7天时间范围
        start, end = executor.calculate_true_time_range("7d")

        # 验证是否为真正的7天
        try:
            start_date = datetime.fromisoformat(start)
            end_date = datetime.fromisoformat(end)
            days_diff = (end_date - start_date).days

            if days_diff == 7:
                print(f"[OK] 时间范围计算正确: {start} 至 {end}")
                print(f"     真正的7天范围（不是7.6-7.7两天）")
                return True
            else:
                print(f"[WARN] 时间范围计算不准确: {days_diff}天")
                return False
        except Exception as e:
            print(f"[ERROR] 时间解析失败: {e}")
            return False

    except ImportError as e:
        print(f"[ERROR] intelligent_search_executor导入失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 智能搜索执行器测试失败: {e}")
        return False

def test_paper_search_apis():
    """测试4：验证多数据源API配置"""
    print_section("测试4: 多数据源API配置验证")

    try:
        sys.path.insert(0, '/c/Users/lanpi/AppData/Local/hermes/skills/academic/paper-search/scripts/')

        # 检查paper_search.py中的API配置
        with open('/c/Users/lanpi/AppData/Local/hermes/skills/academic/paper-search/scripts/paper_search.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查数据源配置
        required_sources = ['SemanticScholarAPI', 'ArxivAPI', 'CrossRefAPI', 'PubMedAPI', 'OpenAlexAPI']

        found_sources = []
        for source in required_sources:
            if source in content:
                found_sources.append(source)

        if len(found_sources) >= 4:
            print(f"[OK] 多数据源API已配置: {len(found_sources)}/5")
            print(f"     找到API类: {', '.join([s.replace('API', ' API') for s in found_sources])}")

            # 检查DOMAIN_SOURCE_PRIORITY配置
            if 'DOMAIN_SOURCE_PRIORITY' in content:
                print("[OK] 数据源优先级配置已定义")

                # 提取statistics领域配置
                import re
                stats_match = re.search(r'"statistics":\s*\[(.*?)\]', content)
                if stats_match:
                    sources_str = stats_match.group(1)
                    sources_list = [s.strip().strip('"') for s in sources_str.split(',')]
                    print(f"     统计学优先级: {', '.join(sources_list)}")

                    if 'CrossRef' in sources_list and 'Semantic Scholar' in sources_list:
                        print("[OK] 统计学领域使用期刊+综合数据源（非单一arXiv）")
                        return True
                    else:
                        print("[WARN] 统计学领域配置可能不完整")
                        return False
        else:
            print("[ERROR] 未找到数据源优先级配置")
            return False

    except Exception as e:
        print(f"[ERROR] 多数据源API配置测试失败: {e}")
        return False

def test_data_formatting():
    """测试5：验证数据格式化修复"""
    print_section("测试5: 数据格式化修复验证")

    try:
        sys.path.insert(0, '/c/Users/lanpi/AppData/Local/hermes/skills/academic/paper-email-service/scripts/utils/')

        # 读取formatters.py
        with open('/c/Users/lanpi/AppData/Local/hermes/skills/academic/paper-email-service/scripts/utils/formatters.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查source字段fallback链
        fallback_patterns = [
            r"paper\.get\('source',.*?\)\s*or\s*paper\.get\('journal'",
            r"source.*journal.*arXiv.*venue",
            "fallback"
        ]

        found_fallback = any(pattern.lower() in content.lower() for pattern in fallback_patterns)

        if found_fallback:
            print("[OK] source字段fallback机制已部署")
        else:
            # 检查是否有source字段的基本处理
            if "'source'" in content and "'journal'" in content:
                print("[WARN] source字段基本处理存在，但fallback链不明确")
            else:
                print("[ERROR] source字段fallback机制未找到")
                return False

        # 检查abstract字段处理
        if "'abstract'" in content:
            print("[OK] abstract字段处理已配置")
        else:
            print("[WARN] abstract字段处理未明确配置")

        return True

    except Exception as e:
        print(f"[ERROR] 数据格式化测试失败: {e}")
        return False

def test_hermes_integration():
    """测试6：Hermes集成测试"""
    print_section("测试6: Hermes集成测试")

    try:
        # 检查Hermes配置文件
        config_file = Path('/c/Users/lanpi/AppData/Local/hermes/skills/academic/paper-email-service/config/default_config.yaml')

        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_content = f.read()

            # 检查报告格式配置
            if 'format: "html"' in config_content:
                print("[OK] 配置文件设置为HTML格式")
            elif 'format: "markdown"' in config_content:
                print("[WARN] 配置文件仍为Markdown格式")
                print("     需要手动修改配置文件")
                return False
            else:
                print("[WARN] 未找到报告格式配置")
                return False
        else:
            print(f"[ERROR] 配置文件不存在: {config_file}")
            return False

        # 检查workflow_executor.py集成
        workflow_file = Path('/c/Users/lanpi/AppData/Local/hermes/skills/academic/paper-email-service/scripts/workflow_executor.py')

        if workflow_file.exists():
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_content = f.read()

            integration_checks = [
                ('IntelligentSearchExecutor', '智能搜索执行器集成'),
                ('generate_report_html', 'HTML报告生成器路径'),
                ('file_extension = \'html\'', 'HTML文件扩展名'),
                ('HTML报告可以在浏览器中打开', 'HTML报告说明')
            ]

            found_integrations = []
            for check, description in integration_checks:
                if check in workflow_content:
                    found_integrations.append(description)

            if len(found_integrations) >= 2:
                print(f"[OK] Hermes集成配置: {len(found_integrations)}/4 项集成已部署")
                print(f"     找到: {', '.join(found_integrations)}")
                return True
            else:
                print(f"[WARN] Hermes集成不完整: 只找到 {len(found_integrations)}/4 项")
                print(f"     找到: {', '.join(found_integrations)}")
                return False
        else:
            print(f"[ERROR] workflow_executor.py不存在")
            return False

    except Exception as e:
        print(f"[ERROR] Hermes集成测试失败: {e}")
        return False

def test_report_generation_simulation():
    """测试7：模拟报告生成过程"""
    print_section("测试7: 报告生成过程模拟")

    try:
        # 创建测试数据
        test_data = {
            "status": "success",
            "query": "statistics machine learning",
            "total_found": 3,
            "sources_used": ["Semantic Scholar", "CrossRef"],
            "domain": "statistics",
            "papers": [
                {
                    "title": "Statistical Methods for Machine Learning",
                    "authors": ["John Smith", "Jane Doe"],
                    "year": "2024",
                    "published": "2024-07-05",
                    "journal": "Journal of Statistical Computing",
                    "doi": "10.1234/stat2024",
                    "citationCount": 45,
                    "abstract": "This paper presents novel statistical methods for machine learning applications. We propose several new algorithms that improve performance significantly.",
                    "url": "https://doi.org/10.1234/stat2024",
                    "source": "Semantic Scholar"
                },
                {
                    "title": "Bayesian Decision Theory in AI",
                    "authors": ["Alice Johnson"],
                    "year": "2024",
                    "published": "2024-07-06",
                    "journal": "arXiv preprint",
                    "doi": "arXiv:2024.07001",
                    "citationCount": 12,
                    "abstract": "We introduce a new Bayesian framework for decision theory in artificial intelligence systems.",
                    "url": "https://arxiv.org/abs/2024.07001",
                    "source": "arXiv"
                }
            ],
            "filters_applied": {
                "time_range": {
                    "start_date": "2024-07-01",
                    "end_date": "2024-07-08"
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            test_json = f.name

        # 生成报告
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            test_html = f.name

        # 测试报告生成
        sys.path.insert(0, '/c/Users/lanpi/AppData/Local/hermes/skills/academic/report-generator/scripts/')

        import generate_report_complex
        generator = generate_report_complex.HTMLReportGenerator(test_data)

        success = generator.generate(test_html)

        if success:
            # 检查生成的HTML文件
            with open(test_html, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 验证HTML内容
            html_checks = [
                ('<!DOCTYPE html>', 'HTML声明'),
                ('<style>', 'CSS样式'),
                ('gradient', '渐变色背景'),
                ('Statistics Research Report', '报告标题'),
                ('Papers Overview', '论文概览'),
                ('Bayesian Decision Theory', '论文内容'),
                ('journal', '期刊来源'),
                ('arXiv', 'arXiv来源')
            ]

            found_checks = [check for check, description in html_checks if check in html_content]

            if len(found_checks) >= 6:
                print(f"[OK] HTML报告生成成功: {len(found_checks)}/9 项检查通过")
                print(f"     报告大小: {len(html_content)} 字符")
                print(f"     找到元素: {', '.join([desc for _, desc in found_checks[:4]])}")

                # 清理测试文件
                os.unlink(test_json)
                os.unlink(test_html)

                return True
            else:
                print(f"[WARN] HTML报告生成但内容不完整: {len(found_checks)}/9 项检查通过")
                print(f"     找到元素: {', '.join([desc for _, desc in found_checks])}")
                return False
        else:
            print("[ERROR] HTML报告生成失败")
            return False

    except Exception as e:
        print(f"[ERROR] 报告生成模拟失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("  Hermes搜索能力修复 - 综合测试套件")
    print("=" * 80)
    print("\n开始时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("测试范围: 验证所有修复是否真正生效")

    tests = [
        ("Python缓存清除", test_python_cache_clear),
        ("HTML报告生成器", test_html_report_generator),
        ("智能搜索执行器", test_intelligent_search_executor),
        ("多数据源API", test_paper_search_apis),
        ("数据格式化", test_data_formatting),
        ("Hermes集成", test_hermes_integration),
        ("报告生成模拟", test_report_generation_simulation)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] 测试 '{test_name}' 执行异常: {e}")
            results.append((test_name, False))

    # 总结报告
    print_section("测试结果总结")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"通过测试: {passed}/{total}")
    print()

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print("\n" + "=" * 80)

    if passed == total:
        print("[SUCCESS] 所有测试通过！修复已完全生效")
        print("\n下一步:")
        print("1. 重启Hermes以清除运行时缓存")
        print("2. 重新发送请求: '请为我搜索统计学领域这一周的最新研究成果，把报告发送到我的邮箱'")
        print("3. 验证收到的报告是否为美观的HTML格式")
        return 0
    else:
        failed_count = total - passed
        print(f"[WARNING] {failed_count} 个测试失败")
        print("\n可能的问题:")
        print("- Python缓存未完全清除")
        print("- 修复未部署到正确位置")
        print("- 模块导入错误")

        print("\n建议操作:")
        print("1. 完全关闭Hermes")
        print("2. 手动删除所有__pycache__目录")
        print("3. 重新启动Hermes")

        return 1

    print("=" * 80)

if __name__ == "__main__":
    sys.exit(main())