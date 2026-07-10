#!/usr/bin/env python3
"""
API限流检查工具 - 检查各个数据源API的限流策略和连接状态

检查的API：
1. Semantic Scholar - 学术论文数据库
2. arXiv - 预印本服务器
3. CrossRef - DOI注册机构
4. PubMed - 生物医学数据库
5. OpenAlex - 开放学术数据库

使用方法：
    python test_api_rate_limits.py
"""

import sys
import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_semantic_scholar():
    """测试Semantic Scholar API"""
    print_section("测试1: Semantic Scholar API")

    api_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": "statistics machine learning",
        "fields": "paperId,title,authors,year,abstract,journal,citationCount",
        "limit": 5
    }
    headers = {
        "User-Agent": "Hermes-Agent-Paper-Search/1.0"
    }

    try:
        print("发送测试请求...")
        response = requests.get(api_url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            papers = data.get("data", [])

            if papers:
                print(f"[OK] Semantic Scholar API工作正常")
                print(f"     状态码: {response.status_code}")
                print(f"     返回论文数: {len(papers)}")
                print(f"     限流策略: 请求限制未明确（但建议<100请求/5分钟）")
                return {"status": "success", "papers": len(papers), "rate_limit": "推荐<100req/5min"}
            else:
                print(f"[WARN] API返回成功但无数据")
                return {"status": "no_data", "rate_limit": "推荐<100req/5min"}
        elif response.status_code == 429:
            print(f"[ERROR] API限流 (429 Too Many Requests)")
            print("     限流信息: 请求过于频繁")
            return {"status": "rate_limited", "rate_limit": "已触发限流"}
        else:
            print(f"[ERROR] API返回错误状态: {response.status_code}")
            return {"status": "error", "rate_limit": "未知"}

    except requests.exceptions.Timeout:
        print(f"[ERROR] API请求超时")
        return {"status": "timeout", "rate_limit": "连接问题"}
    except Exception as e:
        print(f"[ERROR] API请求失败: {e}")
        return {"status": "failed", "rate_limit": "连接失败"}

def test_arxiv():
    """测试arXiv API"""
    print_section("测试2: arXiv API")

    api_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "all:statistics",
        "start": 0,
        "max_results": 5
    }

    try:
        print("发送测试请求...")
        response = requests.get(api_url, params=params, timeout=15)

        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')

            if entries:
                print(f"[OK] arXiv API工作正常")
                print(f"     状态码: {response.status_code}")
                print(f"     返回论文数: {len(entries)}")
                print(f"     限流策略: 每3秒1次请求（官方推荐）")
                return {"status": "success", "papers": len(entries), "rate_limit": "1req/3sec"}
            else:
                print(f"[WARN] API返回成功但无数据")
                return {"status": "no_data", "rate_limit": "1req/3sec"}
        else:
            print(f"[ERROR] API返回错误状态: {response.status_code}")
            return {"status": "error", "rate_limit": "未知"}

    except requests.exceptions.Timeout:
        print(f"[ERROR] API请求超时")
        return {"status": "timeout", "rate_limit": "连接问题"}
    except Exception as e:
        print(f"[ERROR] API请求失败: {e}")
        return {"status": "failed", "rate_limit": "连接失败"}

def test_crossref():
    """测试CrossRef API"""
    print_section("测试3: CrossRef API")

    api_url = "https://api.crossref.org/works"
    params = {
        "query": "statistics",
        "rows": 5,
        "sort": "published"
    }
    headers = {
        "User-Agent": "Hermes-Agent-Paper-Search/1.0 (mailto: user@example.com)"
    }

    try:
        print("发送测试请求...")
        response = requests.get(api_url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            items = data.get("message", {}).get("items", [])

            if items:
                print(f"[OK] CrossRef API工作正常")
                print(f"     状态码: {response.status_code}")
                print(f"     返回论文数: {len(items)}")
                print(f"     限流策略: 无明确限制（建议<50请求/秒）")
                return {"status": "success", "papers": len(items), "rate_limit": "推荐<50req/sec"}
            else:
                print(f"[WARN] API返回成功但无数据")
                return {"status": "no_data", "rate_limit": "推荐<50req/sec"}
        elif response.status_code == 429:
            print(f"[ERROR] API限流 (429 Too Many Requests)")
            return {"status": "rate_limited", "rate_limit": "已触发限流"}
        else:
            print(f"[ERROR] API返回错误状态: {response.status_code}")
            return {"status": "error", "rate_limit": "未知"}

    except requests.exceptions.Timeout:
        print(f"[ERROR] API请求超时")
        return {"status": "timeout", "rate_limit": "连接问题"}
    except Exception as e:
        print(f"[ERROR] API请求失败: {e}")
        return {"status": "failed", "rate_limit": "连接失败"}

def test_pubmed():
    """测试PubMed API"""
    print_section("测试4: PubMed API")

    eutils_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": "statistics",
        "retmax": 5,
        "datetype": "recent"
    }

    try:
        print("发送测试请求...")
        response = requests.get(eutils_url, params=params, timeout=10)

        if response.status_code == 200:
            # PubMed返回文本格式
            result_count = response.text.strip()
            if result_count.isdigit():
                count = int(result_count)
                if count > 0:
                    print(f"[OK] PubMed API工作正常")
                    print(f"     状态码: {response.status_code}")
                    print(f"     找到结果数: {count}")
                    print(f"     限流策略: <3请求/秒（无API key）")
                    return {"status": "success", "papers": count, "rate_limit": "<3req/sec"}
                else:
                    print(f"[WARN] API返回成功但无结果")
                    return {"status": "no_data", "rate_limit": "<3req/sec"}
            else:
                print(f"[WARN] API返回格式异常")
                return {"status": "format_error", "rate_limit": "<3req/sec"}
        else:
            print(f"[ERROR] API返回错误状态: {response.status_code}")
            return {"status": "error", "rate_limit": "未知"}

    except requests.exceptions.Timeout:
        print(f"[ERROR] API请求超时")
        return {"status": "timeout", "rate_limit": "连接问题"}
    except Exception as e:
        print(f"[ERROR] API请求失败: {e}")
        return {"status": "failed", "rate_limit": "连接失败"}

def test_openalex():
    """测试OpenAlex API"""
    print_section("测试5: OpenAlex API")

    api_url = "https://api.openalex.org/works"
    params = {
        "search": "statistics",
        "filter": "from_publication_date:2024-07-01",
        "per_page": 5
    }

    try:
        print("发送测试请求...")
        response = requests.get(api_url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            if results:
                print(f"[OK] OpenAlex API工作正常")
                print(f"     状态码: {response.status_code}")
                print(f"     返回论文数: {len(results)}")
                print(f"     限流策略: 无限制（推荐polite爬取）")
                return {"status": "success", "papers": len(results), "rate_limit": "无限制"}
            else:
                print(f"[WARN] API返回成功但无数据")
                return {"status": "no_data", "rate_limit": "无限制"}
        else:
            print(f"[ERROR] API返回错误状态: {response.status_code}")
            return {"status": "error", "rate_limit": "未知"}

    except requests.exceptions.Timeout:
        print(f"[ERROR] API请求超时")
        return {"status": "timeout", "rate_limit": "连接问题"}
    except Exception as e:
        print(f"[ERROR] API请求失败: {e}")
        return {"status": "failed", "rate_limit": "连接失败"}

def analyze_rate_limits(results: Dict[str, Any]):
    """分析API限流结果"""
    print_section("API限流分析总结")

    working_apis = [name for name, result in results.items() if result.get("status") == "success"]
    failed_apis = [name for name, result in results.items() if result.get("status") in ["error", "timeout", "failed"]]
    rate_limited = [name for name, result in results.items() if result.get("status") == "rate_limited"]
    no_data = [name for name, result in results.items() if result.get("status") == "no_data"]

    print(f"测试的API数量: {len(results)}")
    print(f"✅ 工作正常: {len(working_apis)} ({', '.join(working_apis) if working_apis else '无'})")
    print(f"⚠️  无数据返回: {len(no_data)} ({', '.join(no_data) if no_data else '无'})")
    print(f"❌ 连接失败: {len(failed_apis)} ({', '.join(failed_apis) if failed_apis else '无'})")
    print(f"🚫  限流触发: {len(rate_limited)} ({', '.join(rate_limited) if rate_limited else '无'})")

    # 推荐的安全频率
    print("\n📊 推荐的安全请求频率:")
    for name, result in results.items():
        rate_limit = result.get("rate_limit", "未知")
        print(f"  {name}: {rate_limit}")

    # 问题诊断
    print("\n🔍 问题诊断:")

    if rate_limited:
        print("  ❌ 检测到API限流！")
        print("  → 这可能解释了为什么Hermes使用降级搜索")
        print("  → 建议: 增加请求间隔，使用API key提高限额")

    if failed_apis:
        print(f"  ⚠️  {len(failed_apis)}个API连接失败")
        print("  → 可能原因: 网络问题、API服务不稳定")
        print("  → 建议: 检查网络连接，重试API调用")

    if len(no_data) >= 3:
        print("  ⚠️ 多个API返回无数据")
        print("  → 可能原因: 查询参数不匹配，时间范围过窄")
        print("  → 建议: 使用更广泛的关键词，扩大时间范围")

def provide_solutions(results: Dict[str, Any]):
    """提供API限流解决方案"""
    print_section("API限流解决方案")

    print("解决方案1: 请求频率控制")
    print("-----------------------------------")
    print("在每个API调用之间增加延迟:")
    print("- Semantic Scholar: 1秒延迟")
    print("- CrossRef: 1秒延迟")
    print("- arXiv: 3秒延迟（官方推荐）")
    print("- PubMed: 2秒延迟")
    print("- OpenAlex: 1秒延迟")

    print("\n解决方案2: 智能重试机制")
    print("-----------------------------------")
    print("- 指数退避重试（1s → 2s → 4s）")
    print("- 最多重试3次")
    print("- 捕获异常并记录日志")

    print("\n解决方案3: 降级策略")
    print("-----------------------------------")
    print("- 主API失败时自动切换到备用数据源")
    print("- 优先级: Semantic Scholar → CrossRef → arXiv → PubMed")
    print("- 最后手段: 手动浏览器导航（当前方案）")

    print("\n解决方案4: API密钥升级")
    print("-----------------------------------")
    print("- Semantic Scholar: 可申请API密钥提高限额")
    print("- CrossRef: 可使用邮箱认证提高限额")
    print("- PubMed: 申请API密钥（免费）提高限额到3req/sec")
    print("- OpenAlex: 使用polite爬取参数")

    print("\n解决方案5: 查询参数优化")
    print("-----------------------------------")
    print("- 使用更广泛的关键词")
    print("- 扩大时间范围（如7d → 30d → 1y）")
    print("- 减少每次请求的结果数量")
    print("- 添加更灵活的过滤器")

def main():
    """主函数"""
    print("=" * 80)
    print("  API限流检查工具")
    print("  检查各个学术数据源API的限流策略和连接状态")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试各个API
    results = {
        "Semantic Scholar": test_semantic_scholar(),
        "arXiv": test_arxiv(),
        "CrossRef": test_crossref(),
        "PubMed": test_pubmed(),
        "OpenAlex": test_openalex()
    }

    # 分析结果
    analyze_rate_limits(results)

    # 提供解决方案
    provide_solutions(results)

    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)

    # 总结建议
    print("\n💡 建议:")
    if any(r.get("status") == "success" for r in results.values()):
        print("1. ✅ 至少一个API工作正常，可以继续使用")
        print("2. ⚠️ 如遇限流，建议增加请求间隔到3-5秒")
        print("3. 🔧 重启Hermes后再测试搜索功能")
    else:
        print("1. ❌ 所有API都有问题，需要网络检查")
        print("2. 🔍 检查代理设置和防火墙")
        print("3. 🌐 验证互联网连接")

    print("\n下一步: 重启Hermes并测试实际搜索功能")

if __name__ == "__main__":
    main()