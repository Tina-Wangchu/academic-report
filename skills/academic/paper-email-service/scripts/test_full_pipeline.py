#!/usr/bin/env python3
"""
完整4步流水线测试脚本 — 搜索 → AI分析 → HTML报告 → 邮件发送

与之前版本的区别：
  - 新增步骤2：调用 Claude API 进行 AI 深度分析（分类、亮点、趋势、空白）
  - 步骤3不再使用 generate_report_complex.py（只是个简单格式化器），
    改为在脚本内直接生成包含 AI 分析的专业 HTML 报告
  - 搜索使用更大时间范围确保多源命中

用法：
    python test_full_pipeline.py                                    # 默认
    python test_full_pipeline.py --topic "deep learning" --time-range 30d
    python test_full_pipeline.py --skip-email                        # 不发邮件
    python test_full_pipeline.py --recipient other@gmail.com        # 指定收件人
    python test_full_pipeline.py --skip-analysis                    # 跳过AI分析（快速测试）
"""

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import quote, urlencode

# Windows GBK 编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ==================== 路径配置 ====================

HERMES_SKILLS = Path(os.environ.get(
    'HERMES_SKILLS_DIR',
    r'C:\Users\lanpi\AppData\Local\hermes\skills\academic'
))
PYTHON = sys.executable

SCRIPTS = {
    'paper_search': HERMES_SKILLS / 'paper-search' / 'scripts' / 'paper_search.py',
    'email_sender': HERMES_SKILLS / 'email-sender' / 'scripts' / 'send_email.py',
}

# ==================== 环境变量 ====================

def load_env(env_file: Path):
    if not env_file.exists():
        return
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

def setup_environment():
    for p in [HERMES_SKILLS / '.env',
              HERMES_SKILLS / 'paper-email-service' / '.env',
              HERMES_SKILLS / 'paper-search' / '.env']:
        load_env(p)

    email_set = os.environ.get('GMAIL_ADDRESS') or os.environ.get('QQ_EMAIL_ADDRESS')
    proxy_set = os.environ.get('SMTP_SOCKS_PROXY') or os.environ.get('ALL_PROXY')
    api_token = os.environ.get('ANTHROPIC_AUTH_TOKEN')
    api_base = os.environ.get('ANTHROPIC_BASE_URL', '')
    api_model = os.environ.get('ANTHROPIC_DEFAULT_SONNET_MODEL', '')

    if email_set:
        print(f"  ✓ 邮箱: {email_set[:5]}***")
    if proxy_set:
        print(f"  ✓ 代理: {proxy_set}")
    if api_token:
        print(f"  ✓ LLM API: {api_base.split('//')[-1]} (model={api_model})")
    else:
        print("  ⚠️ 未检测到 API token，AI 分析将跳过")

    return bool(api_token)


# ==================== 步骤1: 多源论文搜索 ====================

def search_semantic_scholar_direct(query: str, start_date: str, end_date: str,
                                   max_results: int = 20) -> list:
    """直接调用 Semantic Scholar API（带 abstract）"""
    import ssl
    ctx = ssl._create_unverified_context()

    # 计算年份过滤
    year_from = start_date[:4]

    url = f"https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": "paperId,title,abstract,authors,year,publicationDate,journal,citationCount,doi,url,openAccessPdf",
        "year": year_from + "-",
    }

    full_url = url + "?" + urlencode(params)

    try:
        req = Request(full_url)
        req.add_header("User-Agent", "Hermes-Test/1.0")
        resp = urlopen(req, timeout=60, context=ctx)
        data = json.loads(resp.read().decode('utf-8'))
        papers = []
        for item in data.get('data', []):
            abstract = item.get('abstract') or ''
            if abstract and len(abstract) > 30:
                papers.append({
                    'title': item.get('title', ''),
                    'abstract': abstract,
                    'authors': [a.get('name', '') for a in (item.get('authors') or [])],
                    'year': item.get('year', ''),
                    'published': item.get('publicationDate', ''),
                    'journal': (item.get('journal') or {}).get('name', ''),
                    'doi': item.get('doi', ''),
                    'url': item.get('url', ''),
                    'citationCount': item.get('citationCount', 0),
                    'source': 'Semantic Scholar',
                })
        return papers
    except Exception as e:
        print(f"    ⚠️ Semantic Scholar 直接调用失败: {e}")
        return []


def search_arxiv_direct(query: str, max_results: int = 20) -> list:
    """直接调用 arXiv API（带 abstract）"""
    import xml.etree.ElementTree as ET

    url = f"http://export.arxiv.org/api/query?search_query=all:{quote(query)}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

    try:
        resp = urlopen(Request(url), timeout=60)
        root = ET.fromstring(resp.read())

        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary_el = entry.find('atom:summary', ns)
            abstract = summary_el.text.strip() if summary_el is not None else ''
            authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]

            # 提取日期
            published = ''
            pub_el = entry.find('atom:published', ns)
            if pub_el is not None:
                published = pub_el.text[:10]

            # 提取 DOI
            doi = ''
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'doi':
                    doi = link.get('href', '')

            # 提取 arXiv ID 作为 URL
            arxiv_id = ''
            for link in entry.findall('atom:link', ns):
                href = link.get('href', '')
                if 'arxiv.org/abs/' in href:
                    arxiv_id = href

            if abstract and len(abstract) > 30:
                papers.append({
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'year': published[:4] if published else '',
                    'published': published,
                    'journal': 'arXiv',
                    'doi': doi,
                    'url': arxiv_id,
                    'source': 'arXiv',
                })
        return papers
    except Exception as e:
        print(f"    ⚠️ arXiv 直接调用失败: {e}")
        return []


def run_paper_search(topic: str, time_range: str, max_results: int,
                     domain: str = 'general', output_file: Path = None) -> dict:
    """
    执行多源论文搜索（直接调用 API，确保有 abstract）

    不依赖 paper_search.py（避免 429 限流 + GBK 编码 + 无 abstract 的连环问题）
    """
    print(f"\n{'='*60}")
    print(f"步骤 1/4: 多源论文搜索（直接 API）")
    print(f"{'='*60}")
    print(f"  主题: {topic}")
    print(f"  时间范围: {time_range}")
    print(f"  最大结果: {max_results}")
    print(f"  领域: {domain}")

    # 计算日期范围
    now = datetime.now(timezone.utc)
    if time_range.endswith('d'):
        days = int(time_range[:-1])
        start_date = (now - timedelta(days=days)).strftime('%Y-%m-%d')
    elif time_range.endswith('m'):
        months = int(time_range[:-1])
        start_date = (now - timedelta(days=months * 30)).strftime('%Y-%m-%d')
    elif time_range.endswith('y'):
        years = int(time_range[:-1])
        start_date = (now - timedelta(days=years * 365)).strftime('%Y-%m-%d')
    else:
        start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')

    print(f"  日期: {start_date} 至 {end_date}")

    all_papers = []
    sources_used = []

    # 1. Semantic Scholar（最佳 abstract 质量）
    print(f"\n  🔍 搜索 Semantic Scholar...")
    s2_papers = search_semantic_scholar_direct(topic, start_date, end_date, max_results)
    if s2_papers:
        all_papers.extend(s2_papers)
        sources_used.append('Semantic Scholar')
        print(f"    ✓ 找到 {len(s2_papers)} 篇（含摘要）")
    else:
        print(f"    ⚠️ 无结果（可能限流），尝试其他源...")

    # 2. arXiv（预印本，通常有 abstract）
    print(f"\n  🔍 搜索 arXiv...")
    arxiv_papers = search_arxiv_direct(topic, max_results)
    if arxiv_papers:
        # 按 DOI 去重
        existing_dois = {p.get('doi', '').lower() for p in all_papers}
        new_papers = [p for p in arxiv_papers
                      if p.get('doi', '').lower() not in existing_dois
                      and p.get('title', '').lower() not in {pp.get('title', '').lower() for pp in all_papers}]
        all_papers.extend(new_papers)
        sources_used.append('arXiv')
        print(f"    ✓ 找到 {len(arxiv_papers)} 篇（新增 {len(new_papers)} 篇去重后）")
    else:
        print(f"    ⚠️ 无结果")

    # 过滤：只要有 abstract 的论文
    valid_papers = [p for p in all_papers
                     if p.get('abstract') and len(p.get('abstract', '')) > 30]
    no_abstract = len(all_papers) - len(valid_papers)

    print(f"\n✅ 搜索完成!")
    print(f"   总计: {len(all_papers)} 篇")
    print(f"   有效（有摘要）: {len(valid_papers)} 篇")
    print(f"   数据源: {sources_used}")
    if no_abstract:
        print(f"   ⚠️ {no_abstract} 篇无摘要已过滤")

    if valid_papers:
        print(f"\n   📄 论文列表:")
        for i, p in enumerate(valid_papers[:max_results], 1):
            title = p.get('title', 'Untitled')
            src = p.get('source', '?')
            abstract_len = len(p.get('abstract', ''))
            year = p.get('year', '')
            print(f"   {i}. [{src}] [{year}] {title[:55]}{'...' if len(title)>55 else ''} ({abstract_len}字)")

    # 限制数量
    final_papers = valid_papers[:max_results]

    if output_file:
        report_input = {
            'papers': final_papers,
            'domain': domain,
            'filters_applied': {'time_range': {'range': time_range}, 'topic': topic},
            'sources_used': sources_used,
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_input, f, ensure_ascii=False, indent=2)
        print(f"\n   💾 搜索结果已保存: {output_file}")

    if not final_papers:
        return {'status': 'error', 'papers': [], 'sources_used': sources_used}
    return {'status': 'success', 'papers': final_papers, 'sources_used': sources_used}


# ==================== 步骤2: AI 深度分析（Claude API） ====================

def run_ai_analysis(papers: list, topic: str, domain: str) -> dict:
    """
    调用 Claude API 对论文进行 AI 深度分析

    分析内容：
    1. 报告摘要（编号要点）
    2. 按研究方向分类
    3. 每篇论文的亮点分析
    4. 研究热点与代表性研究
    5. 研究空白与未来方向
    """
    print(f"\n{'='*60}")
    print(f"步骤 2/4: AI 深度分析（Claude API）")
    print(f"{'='*60}")

    api_token = os.environ.get('ANTHROPIC_AUTH_TOKEN')
    if not api_token:
        print("  ⚠️ 无 API token，跳过 AI 分析")
        return {'status': 'skipped', 'analysis': None}

    # 使用 Hermes Agent 的 API 配置（可能是智谱 GLM 等兼容端点）
    api_url = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
    model = os.environ.get('ANTHROPIC_DEFAULT_SONNET_MODEL', 'claude-sonnet-4-20250514')
    api_url = f"{api_url.rstrip('/')}/v1/messages"

    # 构建 prompt
    papers_text = ""
    for i, p in enumerate(papers, 1):
        title = p.get('title', 'Untitled')
        abstract = p.get('abstract', 'No abstract available')
        authors = p.get('authors', [])
        authors_str = ', '.join(str(a) for a in authors[:3])
        if len(authors) > 3:
            authors_str += ' et al.'
        year = p.get('year', '')
        source = p.get('source', p.get('journal', ''))
        doi = p.get('doi', '')
        url = p.get('url', '')

        papers_text += f"\n【论文{i}】\n"
        papers_text += f"标题: {title}\n"
        papers_text += f"作者: {authors_str}\n"
        papers_text += f"年份: {year}\n"
        papers_text += f"来源: {source}\n"
        if doi:
            papers_text += f"DOI: {doi}\n"
        papers_text += f"摘要: {abstract}\n"

    prompt = f"""你是一位资深的学术研究分析师。请对以下 {len(papers)} 篇关于「{topic}」领域的最新论文进行深度分析。

## 输入论文
{papers_text}

## 要求输出格式（严格遵守，输出纯JSON，不要有其他文字）：

```json
{{{{
  "report_summary": [
    "1. 《论文标题》的关键发现描述...",
    "2. 《论文标题》的关键发现描述...",
    "3. 该领域本周最重要的2-3个研究突破..."
  ],
  "categories": [
    {{{{
      "name": "研究方向名称",
      "hot_topic": "该方向近期的核心研究主题和突破点描述",
      "representative_research": "该方向上知名的、高概括性的代表性研究（如DeepMind/OpenAI的XX工作奠定了基础...）",
      "research_gap": "基于《论文A》和《论文B》发现的缺口描述",
      "future_direction": "未来可能的研究方向",
      "papers": [0, 1, 2]
    }}}},
    ...
  ],
  "paper_analyses": [
    {{{{
      "index": 0,
      "highlights": {{
        "research_goal": "研究目标",
        "core_method": "核心方法",
        "key_innovation": "关键创新",
        "main_finding": "主要发现",
        "significance": "研究意义"
      }}
    }}}},
    ...
  ]
}}}}
```

## 分析规则（必须遵守）：
- 所有分析中必须引用具体论文标题（如"《KRCA》系统在XX方面实现了..."），禁止"多个研究"等模糊表述
- 研究空白必须指出基于哪几篇论文发现的缺口
- 每个分类至少分析1篇论文的亮点
- 如果某篇论文无摘要，基于标题做合理推断并标注"（基于标题推断）"
- report_summary 中的要点要高度概括，让读者30秒内掌握全貌"""

    # 计算 token 限制
    max_input_tokens = min(len(prompt), 150000)  # Claude 支持最大 200K
    if len(prompt) > max_input_tokens:
        prompt = prompt[:max_input_tokens] + "\n\n[论文数据被截断]"

    print(f"  分析 {len(papers)} 篇论文")
    print(f"  Prompt 长度: {len(prompt)} 字符")

    # 调用 LLM API
    headers = {
        "x-api-key": api_token,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 8000,
        "messages": [{"role": "user", "content": prompt}],
    }

    print(f"  调用 API ({api_url}, model={model})...")

    try:
        req = Request(api_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        response = urlopen(req, timeout=120)
        resp_data = json.loads(response.read().decode('utf-8'))

        # 提取文本内容
        content_blocks = resp_data.get('content', [])
        analysis_text = ''
        for block in content_blocks:
            if block.get('type') == 'text':
                analysis_text += block.get('text', '')

        if not analysis_text:
            print("  ❌ Claude API 返回空内容")
            return {'status': 'error', 'analysis': None}

        # 提取 JSON（可能被 ```json ``` 包裹）
        text = analysis_text.strip()
        if text.startswith('```'):
            # 去掉 markdown 代码块标记
            lines = text.split('\n')
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith('```'):
                    if in_block:
                        break
                    in_block = True
                    continue
                if in_block:
                    json_lines.append(line)
            text = '\n'.join(json_lines)

        # 如果仍然不是 JSON 开头，尝试找到第一个 {
        if not text.startswith('{'):
            brace_pos = text.find('{')
            if brace_pos >= 0:
                text = text[brace_pos:]
            last_brace = text.rfind('}')
            if last_brace > 0:
                text = text[:last_brace + 1]

        analysis = json.loads(text)

        print(f"\n  ✅ AI 分析完成!")
        print(f"  📊 报告摘要: {len(analysis.get('report_summary', []))} 条要点")
        print(f"  📂 研究分类: {len(analysis.get('categories', []))} 个方向")
        print(f"  📄 论文亮点: {len(analysis.get('paper_analyses', []))} 篇")

        # 保存分析结果
        return {'status': 'success', 'analysis': analysis}

    except HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace') if e.fp else ''
        print(f"\n  ❌ API 请求失败: HTTP {e.code}")
        print(f"  错误: {error_body[:300]}")
        return {'status': 'error', 'analysis': None}
    except json.JSONDecodeError as e:
        print(f"\n  ❌ 解析 AI 分析结果失败: {e}")
        # 保存原始文本用于调试
        debug_file = Path(tempfile.gettempdir()) / 'ai_analysis_raw.txt'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(analysis_text)
        print(f"  💾 原始输出已保存: {debug_file}")
        return {'status': 'parse_error', 'analysis': None}
    except Exception as e:
        print(f"\n  ❌ AI 分析异常: {e}")
        return {'status': 'error', 'analysis': None}


# ==================== 步骤3: HTML 报告生成（含 AI 分析） ====================

def generate_html_report(papers: list, analysis: dict, topic: str, domain: str,
                          time_range: str, sources_used: list, output_file: Path) -> dict:
    """
    生成包含 AI 深度分析的专业 HTML 报告
    """
    print(f"\n{'='*60}")
    print(f"步骤 3/4: 生成 HTML 报告")
    print(f"{'='*60}")

    now = datetime.now(timezone.utc)
    date_str = now.strftime('%Y-%m-%d')

    try:
        html = build_html_content(papers, analysis, topic, domain, time_range, sources_used, now)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        file_size = output_file.stat().st_size / 1024
        print(f"\n  ✅ 报告生成成功!")
        print(f"  文件: {output_file}")
        print(f"  大小: {file_size:.1f} KB")

        return {'status': 'success', 'report_path': str(output_file), 'file_size_kb': file_size}

    except Exception as e:
        print(f"\n  ❌ 报告生成异常: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'report_path': '', 'file_size_kb': 0}


def build_html_content(papers, analysis, topic, domain, time_range, sources_used, now) -> str:
    """构建完整的 HTML 报告内容"""

    date_str = now.strftime('%Y-%m-%d')

    # ===== 1. 报告摘要 =====
    summary_html = ""
    if analysis and analysis.get('report_summary'):
        summary_items = analysis['report_summary']
        summary_html = f"""
    <div class="section">
        <h2 class="section-title">📋 报告摘要 ⭐</h2>
        <div class="summary-box">
            <p>本报告覆盖 <strong>{len(papers)}</strong> 篇 {topic} 领域核心论文，以下是关键发现：</p>
            <ol>"""
        for item in summary_items:
            summary_html += f"\n                <li>{item}</li>"
        summary_html += f"""
            </ol>
        </div>
    </div>"""
    else:
        summary_html = f"""
    <div class="section">
        <h2 class="section-title">📋 报告摘要 ⭐</h2>
        <div class="summary-box">
            <p>本报告覆盖 <strong>{len(papers)}</strong> 篇 {topic} 领域核心论文。</p>
        </div>
    </div>"""

    # ===== 2. 领域综合分析（按分类） =====
    analysis_html = ""
    if analysis and analysis.get('categories'):
        categories = analysis['categories']
        analysis_html = f"""
    <div class="section">
        <h2 class="section-title">🔬 领域综合分析（按研究方向分类） ⭐ 核心章节</h2>"""

        for cat in categories:
            cat_name = cat.get('name', '未分类')
            hot = cat.get('hot_topic', '')
            representative = cat.get('representative_research', '')
            gap = cat.get('research_gap', '')
            future = cat.get('future_direction', '')
            paper_indices = cat.get('papers', [])

            analysis_html += f"""
        <div class="category-card">
            <h3 class="category-title">📂 {cat_name}</h3>"""

            if hot:
                analysis_html += f"""
            <div class="analysis-item">
                <strong>🔥 研究热点：</strong>{hot}
            </div>"""
            if representative:
                analysis_html += f"""
            <div class="analysis-item">
                <strong>🏆 代表性研究：</strong>{representative}
            </div>"""

            # 该分类下的论文
            for idx in paper_indices:
                if 0 <= idx < len(papers):
                    p = papers[idx]
                    # 找到对应的 AI 分析
                    paper_highlight = None
                    if analysis.get('paper_analyses'):
                        for pa in analysis['paper_analyses']:
                            if pa.get('index') == idx:
                                paper_highlight = pa.get('highlights', {})
                                break

                    analysis_html += render_paper_card(p, paper_highlight, idx + 1)

            if gap:
                analysis_html += f"""
            <div class="gap-box">
                <strong>🔍 研究空白：</strong>{gap}
            </div>"""
            if future:
                analysis_html += f"""
            <div class="future-box">
                <strong>🚀 未来方向：</strong>{future}
            </div>"""

            analysis_html += """
        </div>"""

        analysis_html += """
    </div>"""

    # 如果没有分类分析，但有关联分析，按顺序显示
    elif analysis and analysis.get('paper_analyses'):
        analysis_html = f"""
    <div class="section">
        <h2 class="section-title">🔬 论文深度分析</h2>"""
        for i, p in enumerate(papers, 1):
            paper_highlight = None
            for pa in analysis['paper_analyses']:
                if pa.get('index') == i - 1:
                    paper_highlight = pa.get('highlights', {})
                    break
            analysis_html += render_paper_card(p, paper_highlight, i)
        analysis_html += """
    </div>"""
    else:
        # 无 AI 分析时，简单列出
        analysis_html = f"""
    <div class="section">
        <h2 class="section-title">📄 论文列表</h2>"""
        for i, p in enumerate(papers, 1):
            analysis_html += render_paper_card(p, None, i)
        analysis_html += """
    </div>"""

    # ===== 3. 检索概况 =====
    sources_text = ', '.join(sources_used) if sources_used else 'N/A'
    search_overview = f"""
    <div class="section">
        <h2 class="section-title">📊 检索概况</h2>
        <table class="info-table">
            <tr><td><strong>检索主题</strong></td><td>{topic}</td></tr>
            <tr><td><strong>时间范围</strong></td><td>{time_range}</td></tr>
            <tr><td><strong>研究领域</strong></td><td>{domain}</td></tr>
            <tr><td><strong>数据源</strong></td><td>{sources_text}</td></tr>
            <tr><td><strong>论文数量</strong></td><td>{len(papers)} 篇</td></tr>
            <tr><td><strong>生成时间</strong></td><td>{now.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
        </table>
    </div>"""

    # ===== 4. 参考文献 =====
    refs_html = """    <div class="section">
        <h2 class="section-title">📚 参考文献</h2>
        <ol class="references">"""
    for i, p in enumerate(papers, 1):
        title = p.get('title', 'Untitled')
        authors = p.get('authors', [])
        authors_str = ', '.join(str(a) for a in authors[:3])
        if len(authors) > 3:
            authors_str += ', et al.'
        year = p.get('year', '')
        source = p.get('source', p.get('journal', ''))
        doi = p.get('doi', '')
        url = p.get('url', '')

        ref_str = f"{authors_str}. {title}. {source}, {year}."
        if doi:
            ref_str += f" DOI: <a href=\"https://doi.org/{doi}\" target=\"_blank\">{doi}</a>"
        elif url:
            ref_str += f" <a href=\"{url}\" target=\"_blank\">[链接]</a>"

        refs_html += f"\n            <li>{ref_str}</li>"
    refs_html += """
        </ol>
    </div>"""

    # ===== 组装完整 HTML =====
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} 学术研究报告 - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7; color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1100px; margin: 0 auto;
            background: white; border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 40px; text-align: center;
        }}
        .header h1 {{ font-size: 2.2em; margin-bottom: 10px; }}
        .header .subtitle {{ font-size: 1.1em; opacity: 0.9; }}
        .header .meta {{ margin-top: 15px; font-size: 0.9em; opacity: 0.8; }}
        .content {{ padding: 40px; }}
        .section {{ margin-bottom: 40px; }}
        .section-title {{
            font-size: 1.6em; color: #667eea;
            margin-bottom: 20px; padding-bottom: 10px;
            border-bottom: 3px solid #667eea; font-weight: 600;
        }}
        .summary-box {{
            background: #eef2ff; border-left: 4px solid #667eea;
            padding: 20px 25px; border-radius: 4px;
            font-size: 1.05em;
        }}
        .summary-box ol {{ padding-left: 25px; margin-top: 10px; }}
        .summary-box li {{ margin: 8px 0; line-height: 1.6; }}
        .category-card {{
            background: #f8f9ff; border: 1px solid #e0e4f0;
            border-radius: 8px; padding: 25px; margin: 20px 0;
        }}
        .category-title {{
            font-size: 1.3em; color: #5b5fc7;
            margin-bottom: 15px; font-weight: 600;
        }}
        .analysis-item {{
            margin: 12px 0; padding: 10px 15px;
            background: white; border-radius: 6px;
            border-left: 3px solid #667eea;
        }}
        .paper-card {{
            background: white; border-left: 4px solid #764ba2;
            padding: 20px; margin: 15px 0; border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .paper-title {{
            font-size: 1.1em; color: #5b5fc7;
            margin-bottom: 8px; font-weight: 600;
        }}
        .paper-meta {{ color: #666; font-size: 0.9em; margin-bottom: 12px; }}
        .paper-abstract {{
            background: #f5f5f5; padding: 12px 15px;
            border-radius: 4px; margin: 10px 0;
            font-size: 0.95em; color: #444;
        }}
        .paper-abstract strong {{ color: #333; }}
        .highlights-grid {{
            display: grid; grid-template-columns: 1fr 1fr;
            gap: 8px; margin: 12px 0;
        }}
        .highlight-item {{
            background: #fef9e7; padding: 8px 12px;
            border-radius: 4px; font-size: 0.9em;
        }}
        .highlight-item strong {{ color: #d4a017; }}
        .gap-box {{
            background: #fff3f3; border-left: 3px solid #e74c3c;
            padding: 10px 15px; margin: 10px 0; border-radius: 4px;
            font-size: 0.95em;
        }}
        .future-box {{
            background: #f0fff4; border-left: 3px solid #27ae60;
            padding: 10px 15px; margin: 10px 0; border-radius: 4px;
            font-size: 0.95em;
        }}
        .info-table {{
            width: 100%; border-collapse: collapse;
            background: #f8f9ff; border-radius: 8px; overflow: hidden;
        }}
        .info-table td {{
            padding: 12px 20px; border-bottom: 1px solid #e0e4f0;
        }}
        .info-table td:first-child {{ font-weight: 600; width: 150px; color: #555; }}
        .references {{ padding-left: 25px; }}
        .references li {{ margin: 10px 0; line-height: 1.6; }}
        .references a {{ color: #667eea; text-decoration: none; }}
        .references a:hover {{ text-decoration: underline; }}
        .footer {{
            background: #f8f9fa; padding: 25px; text-align: center;
            color: #888; border-top: 1px solid #eee; font-size: 0.9em;
        }}
        .no-abstract {{ color: #999; font-style: italic; }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; }}
            .section {{ page-break-inside: avoid; }}
        }}
        @media (max-width: 768px) {{
            .highlights-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 {topic} 学术研究报告</h1>
            <div class="subtitle">AI-Powered Deep Analysis Research Report</div>
            <div class="meta">
                <span>📅 {date_str}</span> &nbsp;|&nbsp;
                <span>📄 {len(papers)} 篇论文</span> &nbsp;|&nbsp;
                <span>📊 {sources_text}</span>
            </div>
        </div>

        <div class="content">
{summary_html}
{analysis_html}
{search_overview}
{refs_html}
        </div>

        <div class="footer">
            <p>Generated by <strong>Hermes Academic Research Assistant</strong> with Claude AI Analysis</p>
            <p>Report generated on {now.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
    </div>
</body>
</html>"""
    return full_html


def render_paper_card(paper: dict, highlights: dict, index: int) -> str:
    """渲染单篇论文卡片"""
    title = paper.get('title', 'Untitled')
    authors = paper.get('authors', [])
    authors_str = ', '.join(str(a) for a in authors[:5])
    if len(authors) > 5:
        authors_str += ' et al.'
    year = paper.get('year', '')
    source = paper.get('source', paper.get('journal', ''))
    doi = paper.get('doi', '')
    url = paper.get('url', '')
    abstract = paper.get('abstract', '')

    html = f"""
            <div class="paper-card">
                <div class="paper-title">{index}. {title}</div>
                <div class="paper-meta">
                    <strong>作者：</strong>{authors_str} &nbsp;|&nbsp;
                    <strong>年份：</strong>{year} &nbsp;|&nbsp;
                    <strong>来源：</strong>{source}"""

    if doi:
        html += f' &nbsp;|&nbsp; <strong>DOI：</strong><a href="https://doi.org/{doi}" target="_blank">{doi}</a>'
    elif url:
        html += f' &nbsp;|&nbsp; <a href="{url}" target="_blank">[原文链接]</a>'

    html += "\n                </div>"

    # Abstract
    if abstract and abstract != 'No abstract available' and len(abstract) > 50:
        html += f"""
                <div class="paper-abstract">
                    <strong>Abstract：</strong>{abstract}
                </div>"""
    else:
        html += """
                <div class="paper-abstract no-abstract">
                    <strong>Abstract：</strong>暂无摘要
                </div>"""

    # AI 亮点分析
    if highlights:
        html += """
                <div class="highlights-grid">"""
        labels = {
            'research_goal': '🎯 研究目标',
            'core_method': '⚙️ 核心方法',
            'key_innovation': '💡 关键创新',
            'main_finding': '📊 主要发现',
            'significance': '🌟 研究意义',
        }
        for key, label in labels.items():
            val = highlights.get(key, '')
            if val:
                html += f"""
                    <div class="highlight-item"><strong>{label}：</strong>{val}</div>"""
        html += """
                </div>"""

    html += "\n            </div>"
    return html


# ==================== 步骤4: 邮件发送 ====================

def send_email(report_path: str, topic: str, recipient: str = None) -> dict:
    print(f"\n{'='*60}")
    print(f"步骤 4/4: 发送邮件")
    print(f"{'='*60}")

    if not SCRIPTS['email_sender'].exists():
        print(f"❌ 邮件脚本不存在: {SCRIPTS['email_sender']}")
        return {'status': 'error', 'message': '脚本不存在'}

    recipient = recipient or os.environ.get('GMAIL_ADDRESS') or os.environ.get('QQ_EMAIL_ADDRESS')
    if not recipient:
        print("❌ 无收件人")
        return {'status': 'error', 'message': '无收件人'}

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    email_body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;">
<div style="max-width:700px;margin:0 auto;padding:20px;">
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px;border-radius:8px;text-align:center;">
        <h2>📚 {topic} 学术研究报告</h2>
        <p>生成时间: {timestamp}</p>
    </div>
    <div style="padding:20px;">
        <p>您好，</p>
        <p>您关注的 <strong>{topic}</strong> 领域最新研究报告已生成。</p>
        <p>报告包含 <strong>AI 深度分析</strong>：报告摘要、按方向分类的研究热点与代表性研究、每篇论文的完整摘要与亮点分析、研究空白与未来方向。</p>
        <p>📎 HTML 报告已作为附件发送，请在浏览器中打开查看。</p>
        <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
        <p style="color:#999;font-size:12px;">本报告由 Hermes 学术助手 + Claude AI 分析 自动生成</p>
    </div>
</div>
</body></html>"""

    body_file = Path(tempfile.gettempdir()) / 'test_email_body.html'
    with open(body_file, 'w', encoding='utf-8') as f:
        f.write(email_body)

    date_str = datetime.now().strftime('%Y-%m-%d')
    subject = f"📚 {topic} 学术研究报告 - {date_str}"

    cmd = [
        PYTHON, str(SCRIPTS['email_sender']),
        '--to', recipient,
        '--subject', subject,
        '--body-file', str(body_file),
        '--body-type', 'html',
        '--attach', report_path,
    ]

    print(f"  收件人: {recipient}")
    print(f"  主题: {subject}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace',
        )
        if result.returncode != 0:
            print(f"\n  ❌ 发送失败: {result.stderr[:300]}")
            return {'status': 'error', 'message': result.stderr}

        print(f"\n  ✅ 邮件发送成功!")
        print(f"  📧 请检查收件箱: {recipient}")
        try:
            body_file.unlink()
        except:
            pass
        return {'status': 'success', 'message': f'邮件已发送至 {recipient}'}

    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'message': '发送超时'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# ==================== 主流程 ====================

def main():
    parser = argparse.ArgumentParser(
        description='完整4步流水线: 搜索 → AI分析 → HTML报告 → 邮件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python test_full_pipeline.py                                    # 默认
  python test_full_pipeline.py --topic "deep learning" --time-range 30d
  python test_full_pipeline.py --skip-email                        # 不发邮件
  python test_full_pipeline.py --skip-analysis                    # 跳过AI分析
  python test_full_pipeline.py --recipient other@gmail.com
        """
    )

    parser.add_argument('--topic', '-t', default='statistics',
                        help='搜索主题 (默认: statistics)')
    parser.add_argument('--time-range', default='30d',
                        help='时间范围: 7d/30d/1y/3y (默认: 30d，更大范围确保多源命中)')
    parser.add_argument('--max-results', '-n', type=int, default=15,
                        help='搜索论文数 (默认: 15，AI分析后会筛选)')
    parser.add_argument('--domain', '-d', default='statistics',
                        help='领域: general/ai/statistics/finance')
    parser.add_argument('--recipient', '-r', help='收件邮箱')
    parser.add_argument('--skip-email', action='store_true', help='跳过邮件')
    parser.add_argument('--skip-analysis', action='store_true', help='跳过AI分析')
    parser.add_argument('--output-dir', help='输出目录')

    args = parser.parse_args()

    print()
    print("╔" + "═" * 58 + "╗")
    print("║   📚 Hermes 学术论文服务 — 完整4步流水线测试       ║")
    print("╚" + "═" * 58 + "╝")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    has_api = setup_environment()

    # 验证脚本
    missing = [n for n, p in SCRIPTS.items() if not p.exists()]
    if missing:
        print(f"\n❌ 缺少脚本: {missing}")
        sys.exit(1)
    print(f"\n  ✓ 脚本就绪: paper_search, email_sender")

    output_dir = Path(args.output_dir) if args.output_dir else Path(tempfile.gettempdir()) / 'hermes_test_output'
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  📁 输出: {output_dir}")

    # ===== 步骤1: 搜索 =====
    papers_file = output_dir / 'papers.json'
    search_result = run_paper_search(
        topic=args.topic,
        time_range=args.time_range,
        max_results=args.max_results,
        domain=args.domain,
        output_file=papers_file,
    )

    if not search_result['papers']:
        print("\n❌ 未找到论文，流程终止")
        sys.exit(1)

    papers = search_result['papers']
    sources_used = search_result.get('sources_used', [])

    # ===== 步骤2: AI 分析 =====
    if args.skip_analysis or not has_api:
        analysis_result = {'status': 'skipped', 'analysis': None}
    else:
        analysis_result = run_ai_analysis(papers, args.topic, args.domain)

    # ===== 步骤3: 生成报告 =====
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    topic_slug = '_'.join(args.topic.split()[:3])[:30]
    report_file = output_dir / f"{topic_slug}_report_{timestamp}.html"

    report_result = generate_html_report(
        papers=papers,
        analysis=analysis_result.get('analysis'),
        topic=args.topic,
        domain=args.domain,
        time_range=args.time_range,
        sources_used=sources_used,
        output_file=report_file,
    )

    if report_result['status'] == 'success':
        try:
            os.startfile(str(report_file).replace('/', '\\'))
        except:
            pass

    # ===== 步骤4: 邮件 =====
    if not args.skip_email:
        email_result = send_email(
            report_path=str(report_file),
            topic=args.topic,
            recipient=args.recipient,
        )
    else:
        email_result = {'status': 'skipped', 'message': '跳过'}

    # ===== 汇总 =====
    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")

    steps = [
        ("搜索", search_result['status'], f"{len(papers)} 篇论文"),
        ("AI分析", analysis_result['status'],
         f"{len(analysis_result.get('analysis', {}).get('categories', []))} 个分类" if analysis_result.get('analysis') else "跳过"),
        ("报告", report_result['status'],
         f"{report_result.get('file_size_kb', 0):.1f}KB" if report_result.get('file_size_kb') else "失败"),
        ("邮件", email_result['status'], ""),
    ]

    for name, status, detail in steps:
        if status == 'success':
            icon = "✅"
        elif status == 'skipped':
            icon = "⏭️"
        else:
            icon = "❌"
        detail_str = f" ({detail})" if detail else ""
        print(f"  {icon} {name}: {status}{detail_str}")

    print(f"\n  📁 输出: {output_dir}")
    print(f"  ⏰ 完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_ok = all(s['status'] in ('success', 'skipped') for s in [search_result, analysis_result, report_result, email_result])
    if all_ok:
        print("🎉 所有步骤完成!")
        return 0
    else:
        print("⚠️ 部分步骤失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
