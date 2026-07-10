#!/usr/bin/env python3
"""
Professional HTML Report Generator — Beautiful Academic Research Reports

Features:
- Modern, professional design with CSS styling
- Comprehensive research summary and analysis
- Innovation patterns, research hotspots, temporal evolution
- Research gaps and future directions
- Print-friendly and email-compatible
- No encoding issues (unlike PDF)

Usage:
    python generate_report_html.py --input papers.json --output report.html
"""

import argparse
import json
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import Counter, defaultdict
import math


class HTMLReportGenerator:
    """Generate professional HTML reports with beautiful styling."""

    def __init__(self, input_data: Dict[str, Any]):
        self.input_data = input_data
        self.papers = input_data.get('papers', [])
        self.domain = input_data.get('domain', 'General')
        self.filters = input_data.get('filters_applied', {})

    def _extract_keywords_from_title(self, title: str, max_keywords: int = 8) -> List[str]:
        """Extract meaningful keywords from paper title."""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())

        stop_words = {
            'study', 'research', 'analysis', 'approach', 'method', 'based', 'using',
            'system', 'model', 'paper', 'work', 'result', 'discuss', 'present',
            'propose', 'develop', 'design', 'implement', 'evaluate', 'test', 'application'
        }

        keywords = [w for w in words if w.lower() not in stop_words]
        return list(set(keywords))[:max_keywords]

    def _extract_methodology(self, abstract: str) -> Dict[str, Any]:
        """Extract methodology information from abstract."""
        if not abstract:
            return {'type': 'Unknown', 'tools': [], 'approach': ''}

        abstract_lower = abstract.lower()

        method_types = {
            'theoretical': ['theory', 'theoretical', 'framework', 'mathematical', 'formal'],
            'experimental': ['experiment', 'empirical', 'measurement', 'observation', 'trial'],
            'computational': ['simulation', 'algorithm', 'computational', 'numerical', 'optimization'],
            'statistical': ['statistical', 'analysis', 'regression', 'inference', 'bayesian'],
            'machine learning': ['neural', 'network', 'learning', 'training', 'deep learning'],
            'survey': ['survey', 'review', 'overview', 'synthesis', 'literature']
        }

        detected_type = 'general'
        for method_type, keywords in method_types.items():
            if any(kw in abstract_lower for kw in keywords):
                detected_type = method_type
                break

        tool_patterns = [
            r'(?:using|with|via|employing)\s+([A-Z][a-zA-Z]+)',
            r'(?:based on|using)\s+([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+)',
        ]

        tools = []
        for pattern in tool_patterns:
            matches = re.findall(pattern, abstract)
            tools.extend(matches)

        return {
            'type': detected_type,
            'tools': list(set(tools[:3])),
            'approach': abstract[:150] + '...' if len(abstract) > 150 else abstract
        }

    def _analyze_innovation_patterns(self) -> Dict[str, Any]:
        """Deep analysis of innovation patterns across papers."""
        innovation_keywords = {
            'novelty': ['novel', 'new', 'first', 'innovative', 'pioneering', 'groundbreaking'],
            'theoretical': ['theory', 'framework', 'model', 'formalism', 'axiom', 'theorem'],
            'methodological': ['method', 'approach', 'technique', 'algorithm', 'procedure'],
            'performance': ['improve', 'outperform', 'exceed', 'achieve', 'optimize', 'enhance'],
            'application': ['application', 'implement', 'deploy', 'apply', 'use case'],
            'integration': ['integrate', 'combine', 'fusion', 'hybrid', 'synthesis']
        }

        innovation_scores = defaultdict(int)
        innovation_examples = defaultdict(list)

        for paper in self.papers:
            abstract = paper.get('abstract', paper.get('summary', '')).lower()
            title = paper.get('title', '').lower()
            combined_text = f"{title} {abstract}"

            for category, keywords in innovation_keywords.items():
                matches = [kw for kw in keywords if kw in combined_text]
                if matches:
                    innovation_scores[category] += len(matches)
                    if len(innovation_examples[category]) < 3:
                        innovation_examples[category].append({
                            'paper': paper.get('title', 'N/A'),
                            'matches': matches
                        })

        return {
            'scores': dict(innovation_scores),
            'examples': dict(innovation_examples),
            'dominant_type': max(innovation_scores.items(), key=lambda x: x[1])[0] if innovation_scores else 'none'
        }

    def _identify_research_hotspots(self) -> List[Dict[str, Any]]:
        """Identify research hotspots with clustering analysis."""
        all_keywords = []
        papers_keywords = []

        for paper in self.papers:
            keywords = self._extract_keywords_from_title(paper.get('title', ''))
            abstract = paper.get('abstract', paper.get('summary', '')).lower()

            abstract_words = re.findall(r'\b[a-zA-Z]{5,}\b', abstract)
            abstract_keywords = [w for w in abstract_words if w not in
                                 ['research', 'study', 'analysis', 'approach', 'method', 'paper']]

            combined_keywords = list(set(keywords + abstract_keywords[:5]))
            all_keywords.extend(combined_keywords)
            papers_keywords.append(combined_keywords)

        keyword_frequency = Counter(all_keywords)

        hotspots = []
        top_keywords = keyword_frequency.most_common(15)

        for keyword, freq in top_keywords:
            if freq < 2:
                continue

            related_papers = []
            for i, paper_keywords in enumerate(papers_keywords):
                if keyword in paper_keywords:
                    related_papers.append(self.papers[i])

            if len(related_papers) >= 2:
                hotspot_papers = related_papers[:5]

                hotspots.append({
                    'keyword': keyword,
                    'frequency': freq,
                    'paper_count': len(related_papers),
                    'representative_papers': [p.get('title', 'N/A') for p in hotspot_papers],
                    'year_distribution': Counter([p.get('year', '2024')[:4] if p.get('year') else '2024'
                                                for p in related_papers]),
                    'recent_growth': len([p for p in related_papers if p.get('year', '2024').startswith('202')])
                })

        return sorted(hotspots, key=lambda x: x['frequency'], reverse=True)[:10]

    def _analyze_temporal_evolution(self) -> Dict[str, Any]:
        """Analyze research evolution over time."""
        yearly_data = defaultdict(lambda: {'papers': [], 'keywords': [], 'methods': []})

        for paper in self.papers:
            year = paper.get('year', paper.get('published', '2024')[:4] if paper.get('published') else '2024')

            yearly_data[year]['papers'].append(paper)

            keywords = self._extract_keywords_from_title(paper.get('title', ''))
            yearly_data[year]['keywords'].extend(keywords)

            abstract = paper.get('abstract', paper.get('summary', ''))
            if abstract:
                methodology = self._extract_methodology(abstract)
                yearly_data[year]['methods'].append(methodology['type'])

        years = sorted(yearly_data.keys())
        evolution_trends = []

        for i, year in enumerate(years):
            if i == 0:
                continue

            prev_year = years[i-1]
            current_papers = len(yearly_data[year]['papers'])
            prev_papers = len(yearly_data[prev_year]['papers'])

            growth_rate = ((current_papers - prev_papers) / prev_papers * 100) if prev_papers > 0 else 0

            current_keywords = Counter(yearly_data[year]['keywords']).most_common(5)
            prev_keywords = Counter(yearly_data[prev_year]['keywords']).most_common(5)

            evolution_trends.append({
                'year': year,
                'paper_count': current_papers,
                'growth_rate': growth_rate,
                'emerging_keywords': [kw for kw, _ in current_keywords if kw not in dict(prev_keywords)],
                'dominant_methods': Counter(yearly_data[year]['methods']).most_common(3)
            })

        return {
            'yearly_data': dict(yearly_data),
            'evolution_trends': evolution_trends,
            'total_years': len(years)
        }

    def _analyze_research_gaps(self) -> List[Dict[str, Any]]:
        """Analyze research gaps and opportunities."""
        method_distribution = Counter()
        application_areas = Counter()

        for paper in self.papers:
            abstract = paper.get('abstract', paper.get('summary', ''))
            if abstract:
                methodology = self._extract_methodology(abstract)
                method_distribution[methodology['type']] += 1

                app_patterns = [
                    r'(?:in|for|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)',
                    r'(?:application|domain|field)\s+(?:of|in)\s+([A-Z][a-zA-Z]+)'
                ]

                for pattern in app_patterns:
                    matches = re.findall(pattern, abstract)
                    application_areas.update(matches)

        total_papers = len(self.papers)
        gaps = []

        for method, count in method_distribution.items():
            if count < total_papers * 0.15:
                gaps.append({
                    'type': 'methodological',
                    'description': f'Underutilization of {method} methods',
                    'current_usage': f'{count}/{total_papers} papers',
                    'opportunity': f'Increased {method} research could yield novel insights'
                })

        for domain, count in application_areas.most_common():
            if count < total_papers * 0.10:
                gaps.append({
                    'type': 'application',
                    'description': f'Limited research in {domain} domain',
                    'current_usage': f'{count}/{total_papers} papers',
                    'opportunity': f'Expansion into {domain} applications'
                })

        return gaps

    def _get_html_header(self) -> str:
        """Generate HTML header with CSS styling."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Academic Research Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            margin-top: 10px;
        }

        .header .meta {
            margin-top: 20px;
            font-size: 0.9em;
            opacity: 0.8;
        }

        .content {
            padding: 40px;
        }

        .section {
            margin-bottom: 40px;
        }

        .section-title {
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-weight: 600;
        }

        .subsection-title {
            font-size: 1.3em;
            color: #764ba2;
            margin: 25px 0 15px 0;
            font-weight: 600;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .stat-card .label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }

        td {
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }

        tbody tr:hover {
            background-color: #f5f5f5;
        }

        tbody tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        .paper-card {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .paper-title {
            font-size: 1.2em;
            color: #667eea;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .paper-meta {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }

        .paper-abstract {
            margin: 15px 0;
            line-height: 1.7;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 0.85em;
            margin: 2px;
        }

        .badge-secondary {
            background: #764ba2;
        }

        .badge-success {
            background: #28a745;
        }

        .analysis-box {
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #e17055;
        }

        .insight-list {
            list-style: none;
            padding: 0;
        }

        .insight-list li {
            padding: 10px 0;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }

        .insight-list li:last-child {
            border-bottom: none;
        }

        .insight-list li:before {
            content: "💡 ";
            margin-right: 8px;
        }

        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }

            .container {
                box-shadow: none;
            }

            .section {
                page-break-inside: avoid;
            }
        }

        @media (max-width: 768px) {
            .content {
                padding: 20px;
            }

            .header {
                padding: 30px 20px;
            }

            .header h1 {
                font-size: 1.8em;
            }

            table {
                font-size: 0.9em;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>'''

    def _get_html_footer(self) -> str:
        """Generate HTML footer."""
        return '''    <div class="footer">
        <p>Generated by Hermes Academic Research Assistant</p>
        <p>Report generated on ''' + datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') + '''</p>
        <p>This report provides comprehensive analysis of academic research papers with advanced trend identification and research gap analysis.</p>
    </div>
</body>
</html>'''

    def generate(self, output_path: str) -> bool:
        """Generate the complete HTML report."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # HTML Header
                f.write(self._get_html_header())
                f.write('<div class="container">')

                # Header Section
                f.write('<div class="header">')
                f.write(f'<h1>{self.domain.capitalize()} Research Report</h1>')
                f.write('<div class="subtitle">Comprehensive Academic Analysis with Deep Research Insights</div>')

                # Statistics
                time_range = self.filters.get('time_range', {})
                time_display = f"{time_range.get('start_date', 'N/A')} to {time_range.get('end_date', 'N/A')}"

                f.write(f'<div class="meta">')
                f.write(f'<span>Papers: {len(self.papers)}</span> | ')
                f.write(f'<span>Time Range: {time_display}</span> | ')
                f.write(f'<span>Sources: {", ".join(self.input_data.get("sources_used", ["N/A"]))}</span>')
                f.write('</div>')
                f.write('</div>')  # End header

                f.write('<div class="content">')

                # Research Statistics
                self._add_research_statistics(f)

                # Papers Overview
                self._add_papers_overview(f)

                # Deep Analysis
                self._add_deep_analysis(f)

                # Research Papers Detail
                self._add_papers_detail(f)

                f.write('</div>')  # End content
                f.write('</div>')  # End container

                # HTML Footer
                f.write(self._get_html_footer())

            return True

        except Exception as e:
            print(f"Error generating HTML report: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False

    def _add_research_statistics(self, f) -> None:
        """Add research statistics section."""
        f.write('<div class="section">')
        f.write('<h2 class="section-title">📊 Research Statistics</h2>')

        f.write('<div class="stats-grid">')
        f.write(f'<div class="stat-card"><div class="label">Total Papers</div><div class="value">{len(self.papers)}</div></div>')

        # Calculate recent papers
        recent_papers = len([p for p in self.papers if p.get('year', '2024').startswith('202')])
        f.write(f'<div class="stat-card"><div class="label">Recent (2023-2024)</div><div class="value">{recent_papers}</div></div>')

        # Calculate abstract availability
        abstracts_available = len([p for p in self.papers if p.get('abstract')])
        f.write(f'<div class="stat-card"><div class="label">With Abstracts</div><div class="value">{abstracts_available}</div></div>')

        # Calculate sources
        unique_sources = len(set(p.get('source', p.get('journal', 'Unknown')) for p in self.papers))
        f.write(f'<div class="stat-card"><div class="label">Data Sources</div><div class="value">{unique_sources}</div></div>')

        f.write('</div>')  # End stats-grid
        f.write('</div>')  # End section

    def _add_papers_overview(self, f) -> None:
        """Add papers overview table."""
        f.write('<div class="section">')
        f.write('<h2 class="section-title">📚 Papers Overview</h2>')

        f.write('<table>')
        f.write('<thead>')
        f.write('<tr><th>#</th><th>Title</th><th>Published</th><th>Authors</th><th>Source</th><th>Keywords</th></tr>')
        f.write('</thead>')
        f.write('<tbody>')

        for i, paper in enumerate(self.papers, 1):
            title = paper.get('title', 'N/A')
            if len(title) > 60:
                title = title[:57] + "..."

            published = paper.get('published', paper.get('year', 'N/A'))
            if published and len(str(published)) > 10:
                published = str(published)[:10]

            authors = paper.get('authors', [])
            if authors and isinstance(authors, list):
                if len(authors) > 2:
                    authors_text = ', '.join(str(a).split()[0] if ' ' in str(a) else str(a) for a in authors[:2]) + ' et al.'
                else:
                    authors_text = ', '.join(str(a).split()[0] if ' ' in str(a) else str(a) for a in authors)
            else:
                authors_text = 'N/A'

            source = paper.get('source', paper.get('journal', 'N/A'))
            keywords = ', '.join(self._extract_keywords_from_title(paper.get('title', ''))[:4])

            f.write(f'<tr><td>{i}</td><td>{title}</td><td>{published}</td><td>{authors_text}</td><td>{source}</td><td>{keywords}</td></tr>')

        f.write('</tbody>')
        f.write('</table>')
        f.write('</div>')

    def _add_deep_analysis(self, f) -> None:
        """Add deep research analysis section."""
        f.write('<div class="section">')
        f.write('<h2 class="section-title">🔬 Deep Research Analysis</h2>')

        # Innovation Patterns
        innovation_analysis = self._analyze_innovation_patterns()
        if innovation_analysis['scores']:
            f.write('<h3 class="subsection-title">🚀 Innovation Pattern Analysis</h3>')

            f.write('<table>')
            f.write('<thead><tr><th>Innovation Type</th><th>Frequency</th><th>Percentage</th><th>Example Papers</th></tr></thead>')
            f.write('<tbody>')

            total_innovation = sum(innovation_analysis['scores'].values())
            for innovation_type, score in sorted(innovation_analysis['scores'].items(), key=lambda x: x[1], reverse=True):
                percentage = (score / total_innovation * 100) if total_innovation > 0 else 0
                examples = innovation_analysis['examples'].get(innovation_type, [])
                example_titles = ', '.join([ex['paper'][:40] + '...' for ex in examples[:2]])

                f.write(f'<tr><td>{innovation_type.capitalize()}</td><td>{score}</td><td>{percentage:.1f}%</td><td>{example_titles}</td></tr>')

            f.write('</tbody></table>')

        # Research Hotspots
        hotspots = self._identify_research_hotspots()
        if hotspots:
            f.write('<h3 class="subsection-title">🔥 Research Hotspots & Clusters</h3>')

            f.write('<table>')
            f.write('<thead><tr><th>Hotspot</th><th>Frequency</th><th>Papers</th><th>Recent Growth</th><th>Representative Papers</th></tr></thead>')
            f.write('<tbody>')

            for hotspot in hotspots[:8]:
                recent_growth = '✓ Yes' if hotspot['recent_growth'] > 0 else '✗ No'
                papers = ', '.join([p[:30] + '...' for p in hotspot['representative_papers'][:2]])

                f.write(f'<tr><td>{hotspot["keyword"].capitalize()}</td><td>{hotspot["frequency"]}</td><td>{hotspot["paper_count"]}</td><td>{recent_growth}</td><td>{papers}</td></tr>')

            f.write('</tbody></table>')

        # Research Gaps
        gaps = self._analyze_research_gaps()
        if gaps:
            f.write('<h3 class="subsection-title">🔍 Research Gaps & Opportunities</h3>')

            f.write('<div class="analysis-box">')
            f.write('<ul class="insight-list">')

            for gap in gaps[:5]:
                f.write(f'<li><strong>{gap["type"].capitalize()} Gap:</strong> {gap["opportunity"]}')
                f.write(f'<br><small>Current: {gap["current_usage"]}</small></li>')

            f.write('</ul>')
            f.write('</div>')

        f.write('</div>')

    def _add_papers_detail(self, f) -> None:
        """Add detailed papers section."""
        f.write('<div class="section">')
        f.write('<h2 class="section-title">📄 Detailed Paper Analysis</h2>')

        for i, paper in enumerate(self.papers, 1):
            f.write(f'<div class="paper-card">')

            # Paper title
            f.write(f'<div class="paper-title">{i}. {paper.get("title", "N/A")}</div>')

            # Metadata
            authors = paper.get('authors', [])
            if authors and isinstance(authors, list):
                authors_text = ', '.join(str(a) for a in authors[:5]) + (' et al.' if len(authors) > 5 else '')
            else:
                authors_text = 'N/A'

            published = paper.get('published', paper.get('year', 'N/A'))
            if published and len(str(published)) > 10:
                published = str(published)[:10]

            source = paper.get('source', paper.get('journal', 'N/A'))

            f.write(f'<div class="paper-meta">')
            f.write(f'<strong>Authors:</strong> {authors_text}<br>')
            f.write(f'<strong>Published:</strong> {published}<br>')
            f.write(f'<strong>Source:</strong> {source}')

            if paper.get('doi'):
                f.write(f' | <strong>DOI:</strong> <a href="https://doi.org/{paper.get("doi")}" target="_blank">{paper.get("doi")}</a>')

            f.write('</div>')  # End paper-meta

            # Keywords
            keywords = self._extract_keywords_from_title(paper.get('title', ''))
            if keywords:
                f.write('<div>')
                for keyword in keywords[:5]:
                    f.write(f'<span class="badge">{keyword.capitalize()}</span>')
                f.write('</div>')

            # Abstract
            abstract = paper.get('abstract', paper.get('summary', ''))
            if abstract:
                # Smart summarization
                key_sentences = []
                sentences = abstract.split('.')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if any(word in sentence.lower() for word in ['propose', 'present', 'show', 'demonstrate', 'achieve', 'develop']):
                        key_sentences.append(sentence)
                    if len(key_sentences) >= 2:
                        break

                if key_sentences:
                    summarized = '. '.join(key_sentences) + '.'
                else:
                    summarized = abstract[:600] + '...' if len(abstract) > 600 else abstract

                f.write(f'<div class="paper-abstract"><strong>Abstract:</strong> {summarized}</div>')

            # Methodology badge
            if abstract:
                methodology = self._extract_methodology(abstract)
                f.write(f'<div><span class="badge badge-secondary">Methodology: {methodology["type"].capitalize()}</span>')
                if methodology['tools']:
                    for tool in methodology['tools'][:2]:
                        f.write(f'<span class="badge badge-success">Tool: {tool}</span>')
                f.write('</div>')

            f.write('</div>')  # End paper-card

        f.write('</div>')  # End section


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate beautiful HTML reports with deep analysis')
    parser.add_argument('--input', required=True, help='Input JSON file with paper data')
    parser.add_argument('--output', required=True, help='Output HTML file path')

    args = parser.parse_args()

    # Read input data
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    # Generate HTML report
    generator = HTMLReportGenerator(input_data)
    success = generator.generate(args.output)

    if success:
        print(f"[OK] Beautiful HTML report generated: {args.output}", file=sys.stderr)
        print(f"[INFO] You can open the report in any modern web browser", file=sys.stderr)
        return 0
    else:
        print("[ERROR] Failed to generate HTML report", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())