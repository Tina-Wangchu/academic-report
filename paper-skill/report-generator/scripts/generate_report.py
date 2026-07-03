#!/usr/bin/env python3
"""
Report Generator — Generate PDF reports from paper search results.

Usage:
    python generate_report.py --input papers.json --output report.pdf

Features:
    - Reads JSON output from paper_search.py
    - Generates professional academic PDF report
    - Includes cover page, table of contents, paper list, and analysis
    - Supports Chinese and English content

Requirements:
    - reportlab (PDF generation): pip install reportlab
    - matplotlib (charts): pip install matplotlib
    - Python 3.8+

For Chinese support, ensure you have Chinese fonts installed:
    - Windows: SimSun, SimHei, Microsoft YaHei
    - Linux: WenQuanYi, Noto Sans CJK
    - macOS: PingFang, STHeiti
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# ==================== PDF Generation Configuration ====================

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.platypus import KeepTogether
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation disabled.", file=sys.stderr)
    print("Install with: pip install reportlab", file=sys.stderr)


class PDFReportGenerator:
    """Generate professional academic PDF reports from paper search results."""

    def __init__(self, input_data: Dict[str, Any], config: Dict[str, Any] = None):
        self.input_data = input_data
        self.config = config or {}
        self.styles = self._create_styles()
        self.story = []

    def _create_styles(self):
        """Create custom paragraph styles for the report."""
        if not REPORTLAB_AVAILABLE:
            return None

        styles = getSampleStyleSheet()

        # Custom styles for academic report
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C5F8D'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2C5F8D'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2C5F8D'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT
        ))

        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            spaceAfter=8,
            leading=16,
            fontName='Helvetica'
        ))

        styles.add(ParagraphStyle(
            name='CustomMeta',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=6,
            fontName='Helvetica'
        ))

        return styles

    def _add_cover_page(self):
        """Generate cover page with report metadata."""
        if not REPORTLAB_AVAILABLE:
            return

        # Title
        title = f"{self.input_data.get('query', 'Paper Search Results')} Research Report"
        self.story.append(Paragraph(title, self.styles['CustomTitle']))
        self.story.append(Spacer(1, 2*cm))

        # Metadata
        meta_data = [
            f"<b>Research Topic:</b> {self.input_data.get('query', 'N/A')}",
            f"<b>Generated:</b> {self.input_data.get('timestamp', 'N/A')}",
            f"<b>Total Papers:</b> {self.input_data.get('total_found', 0)}",
            f"<b>Data Sources:</b> {', '.join(self.input_data.get('sources_used', []))}",
        ]

        # Add time range if available
        filters = self.input_data.get('filters_applied', {})
        if filters.get('time_range'):
            time_range = filters['time_range']
            meta_data.append(
                f"<b>Time Range:</b> {time_range.get('start_date', 'N/A')} to {time_range.get('end_date', 'N/A')}"
            )

        for meta in meta_data:
            self.story.append(Paragraph(meta, self.styles['CustomBody']))
            self.story.append(Spacer(1, 0.3*cm))

        # Footer
        self.story.append(Spacer(1, 2*cm))
        self.story.append(Paragraph(
            "Generated by Hermes Agent Academic Paper Search System",
            self.styles['CustomMeta']
        ))

    def _add_summary_section(self):
        """Add search summary section."""
        if not REPORTLAB_AVAILABLE:
            return

        self.story.append(PageBreak())
        self.story.append(Paragraph("Search Summary", self.styles['CustomHeading1']))

        summary_data = [
            ["<b>Parameter</b>", "<b>Value</b>"],
            ["Search Query", self.input_data.get('query', 'N/A')],
            ["Total Papers Found", str(self.input_data.get('total_found', 0))],
            ["Data Sources Used", ', '.join(self.input_data.get('sources_used', []))],
            ["Search Timestamp", self.input_data.get('timestamp', 'N/A')],
        ]

        # Add filter information
        filters = self.input_data.get('filters_applied', {})
        if filters.get('time_range'):
            time_range = filters['time_range']
            summary_data.append([
                "Time Range",
                f"{time_range.get('start_date', 'N/A')} to {time_range.get('end_date', 'N/A')}"
            ])

        # Create table
        table = Table(summary_data, colWidths=[5*cm, 10*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        self.story.append(table)
        self.story.append(Spacer(1, 1*cm))

    def _add_papers_section(self):
        """Add papers list section."""
        if not REPORTLAB_AVAILABLE:
            return

        self.story.append(PageBreak())
        self.story.append(Paragraph("Core Papers List", self.styles['CustomHeading1']))

        papers = self.input_data.get('papers', [])
        for i, paper in enumerate(papers, 1):
            # Paper number and title
            self.story.append(Paragraph(f"Paper #{i}", self.styles['CustomHeading2']))

            # Title
            title = paper.get('title', 'N/A')
            self.story.append(Paragraph(f"<b>Title:</b> {title}", self.styles['CustomBody']))

            # Authors
            authors = paper.get('authors', [])
            if authors:
                author_list = ', '.join(str(a) for a in authors[:5])
                if len(authors) > 5:
                    author_list += f" et al. ({len(authors)} authors)"
                self.story.append(Paragraph(f"<b>Authors:</b> {author_list}", self.styles['CustomBody']))

            # Year
            year = paper.get('year') or (paper.get('published', '')[:4] if paper.get('published') else 'N/A')
            self.story.append(Paragraph(f"<b>Year:</b> {year}", self.styles['CustomBody']))

            # Journal/Source
            if paper.get('journal'):
                self.story.append(Paragraph(f"<b>Journal:</b> {paper.get('journal')}", self.styles['CustomBody']))

            # DOI
            if paper.get('doi'):
                doi = paper.get('doi')
                self.story.append(Paragraph(
                    f'<b>DOI:</b> <link href="https://doi.org/{doi}">{doi}</link>',
                    self.styles['CustomBody']
                ))

            # Citation count
            if paper.get('citationCount'):
                self.story.append(Paragraph(
                    f"<b>Citations:</b> {paper.get('citationCount')}",
                    self.styles['CustomBody']
                ))

            # Abstract (truncated)
            if paper.get('summary') or paper.get('abstract'):
                abstract = (paper.get('summary') or paper.get('abstract', '')).strip()
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                self.story.append(Paragraph(f"<b>Abstract:</b> {abstract}", self.styles['CustomBody']))

            # URL
            if paper.get('url'):
                self.story.append(Paragraph(
                    f'<b>URL:</b> <link href="{paper.get("url")}">{paper.get("url")}</link>',
                    self.styles['CustomBody']
                ))

            # Source
            if paper.get('source'):
                self.story.append(Paragraph(
                    f"<b>Source:</b> {paper.get('source')}",
                    self.styles['CustomMeta']
                ))

            self.story.append(Spacer(1, 0.8*cm))

            # Add separator
            self.story.append(Paragraph("_" * 80, self.styles['CustomMeta']))
            self.story.append(Spacer(1, 0.5*cm))

    def _add_analysis_section(self):
        """Add enhanced research trend and gap analysis section."""
        if not REPORTLAB_AVAILABLE:
            return

        self.story.append(PageBreak())
        self.story.append(Paragraph("Research Trend Analysis", self.styles['CustomHeading1']))

        papers = self.input_data.get('papers', [])

        if not papers:
            self.story.append(Paragraph("No papers available for analysis.", self.styles['CustomBody']))
            return

        # 导入增强分析模块
        try:
            from enhanced_analysis import ResearchAnalyzer
            analyzer = ResearchAnalyzer()
            enhanced_analysis = True
        except ImportError:
            enhanced_analysis = False
            print("Warning: Enhanced analysis module not available. Using basic analysis.", file=sys.stderr)

        # ==================== 第一部分：研究趋势分析 ====================
        self.story.append(Paragraph("Part 1: Research Trends", self.styles['CustomHeading2']))

        # 1. 年度发文量趋势
        year_counts = {}
        for paper in papers:
            year = paper.get('year') or (paper.get('published', '')[:4] if paper.get('published') else 'Unknown')
            if year and year != 'Unknown':
                year_counts[year] = year_counts.get(year, 0) + 1

        # 1.1 数据源分布
        source_counts = {}
        for paper in papers:
            source = paper.get('source', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        if year_counts:
            self.story.append(Paragraph("Publication Year Trend", self.styles['CustomHeading3']))

            year_data = [["<b>Year</b>", "<b>Papers</b>", "<b>Trend</b>"]]
            sorted_years = sorted(year_counts.keys(), reverse=True)
            for i, year in enumerate(sorted_years):
                count = year_counts[year]
                # 计算趋势
                if i < len(sorted_years) - 1:
                    prev_count = year_counts[sorted_years[i + 1]]
                    if count > prev_count * 1.2:
                        trend = "📈"
                    elif count < prev_count * 0.8:
                        trend = "📉"
                    else:
                        trend = "➡️"
                else:
                    trend = ""

                year_data.append([year, str(count), trend])

            year_table = Table(year_data, colWidths=[4*cm, 4*cm, 2*cm])
            year_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ]))

            self.story.append(year_table)
            self.story.append(Spacer(1, 1*cm))

            # 年份范围
            year_range = f"{min(year_counts.keys())}-{max(year_counts.keys())}"
            self.story.append(Paragraph(f"Analysis Period: {year_range}", self.styles['CustomBody']))

        # 2. 研究热点（高频关键词）
        if enhanced_analysis:
            trends = analyzer.analyze_research_trends(papers)
            hot_topics = trends.get('hot_topics', [])[:10]

            if hot_topics:
                self.story.append(Paragraph("Research Hotspots", self.styles['CustomHeading3']))

                topic_data = [["<b>Rank</b>", "<b>Keyword</b>", "<b>Frequency</b>"]]
                for i, topic in enumerate(hot_topics[:10], 1):
                    topic_data.append([str(i), topic['keyword'], str(topic['frequency'])])

                topic_table = Table(topic_data, colWidths=[1*cm, 6*cm, 3*cm])
                topic_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ]))

                self.story.append(topic_table)
                self.story.append(Spacer(1, 1*cm))

                # 趋势洞察
                trend_insights = trends.get('trend_insights', [])
                if trend_insights:
                    self.story.append(Paragraph("Key Insights", self.styles['CustomHeading3']))
                    for insight in trend_insights:
                        self.story.append(Paragraph(f"• {insight}", self.styles['CustomBody']))
                    self.story.append(Spacer(1, 0.5*cm))

        # 3. 引用量分析
        if enhanced_analysis:
            citation_analysis = trends.get('citation_analysis', {})
            if citation_analysis and citation_analysis.get('total_papers_with_citations', 0) > 0:
                self.story.append(Paragraph("Citation Impact Analysis", self.styles['CustomHeading3']))

                avg_citations = citation_analysis.get('average_citations', 0)
                max_citations = citation_analysis.get('max_citations', 0)

                impact_data = [
                    ["<b>Metric</b>", "<b>Value</b>"],
                    ["Average Citations", f"{avg_citations:.1f}"],
                    ["Max Citations", str(max_citations)],
                    ["High Impact Papers (100+)", str(citation_analysis.get('impact_ranges', {}).get('high_impact', 0))],
                    ["Moderate Impact (50-99)", str(citation_analysis.get('impact_ranges', {}).get('moderate_impact', 0))],
                    ["Emerging (1-49)", str(citation_analysis.get('impact_ranges', {}).get('emerging', 0))]
                ]

                impact_table = Table(impact_data, colWidths=[4*cm, 4*cm])
                impact_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ]))

                self.story.append(impact_table)
                self.story.append(Spacer(1, 1*cm))

        # ==================== 第二部分：研究缺口分析 ====================
        self.story.append(PageBreak())
        self.story.append(Paragraph("Part 2: Research Gaps & Opportunities", self.styles['CustomHeading1']))

        if enhanced_analysis:
            gaps = analyzer.analyze_research_gaps(papers)

            # 时间缺口
            time_gaps = gaps.get('time_gaps', [])
            if time_gaps:
                self.story.append(Paragraph("Time Gaps (Under-represented Years)", self.styles['CustomHeading2']))

                gap_data = [["<b>Year</b>", "<b>Papers</b>", "<b>Gap Analysis</b>"]]
                for gap in time_gaps[:5]:
                    gap_data.append([
                        gap['year'],
                        str(gap['count']),
                        f"{gap['percentage_below_average']} below average"
                    ])

                gap_table = Table(gap_data, colWidths=[3*cm, 3*cm, 5*cm])
                gap_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ]))

                self.story.append(gap_table)
                self.story.append(Spacer(1, 1*cm))

            # 主题缺口
            topic_gaps = gaps.get('topic_gaps', [])
            if topic_gaps:
                self.story.append(Paragraph("Topic Gaps (Under-represented Directions)", self.styles['CustomHeading2']))

                topic_data = [["<b>Topic</b>", "<b>Papers</b>", "<b>Opportunity</b>"]]
                for gap in topic_gaps[:5]:
                    topic_data.append([
                        gap['topic'],
                        str(gap['count']),
                        gap['opportunity_level'].capitalize()
                    ])

                topic_table = Table(topic_data, colWidths=[5*cm, 3*cm, 3*cm])
                topic_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ]))

                self.story.append(topic_table)
                self.story.append(Spacer(1, 1*cm))

            # 方法缺口
            method_gaps = gaps.get('method_gaps', [])
            if method_gaps:
                self.story.append(Paragraph("Method Gaps (Under-utilized Methods)", self.styles['CustomHeading2']))

                method_data = [["<b>Method</b>", "<b>Papers</b>", "<b>Opportunity</b>"]]
                for gap in method_gaps[:5]:
                    method_data.append([
                        gap['method'].title(),
                        str(gap['count']),
                        gap['opportunity'].capitalize()
                    ])

                method_table = Table(method_data, colWidths=[5*cm, 3*cm, 3*cm])
                method_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ]))

                self.story.append(method_table)
                self.story.append(Spacer(1, 1*cm))

            # 跨学科机会
            interdisciplinary_opportunities = gaps.get('interdisciplinary_opportunities', [])
            if interdisciplinary_opportunities:
                self.story.append(Paragraph("Interdisciplinary Opportunities", self.styles['CustomHeading2']))

                for opportunity in interdisciplinary_opportunities[:5]:
                    self.story.append(Paragraph(f"• {opportunity}", self.styles['CustomBody']))

                self.story.append(Spacer(1, 1*cm))

            # 综合缺口洞察
            gap_insights = gaps.get('gap_insights', [])
            if gap_insights:
                self.story.append(Paragraph("Gap Insights", self.styles['CustomHeading3']))
                for insight in gap_insights:
                    self.story.append(Paragraph(f"• {insight}", self.styles['CustomBody']))

        else:
            # 基础分析（如果没有增强模块）
            self.story.append(Paragraph("Publication Year Distribution", self.styles['CustomHeading2']))

            year_data = [["<b>Year</b>", "<b>Papers</b>"]]
            for year in sorted(year_counts.keys(), reverse=True):
                year_data.append([year, str(year_counts[year])])

            year_table = Table(year_data, colWidths=[4*cm, 4*cm])
            year_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ]))

            self.story.append(year_table)
            self.story.append(Spacer(1, 1*cm))

        # 基础研究洞察
        self.story.append(Paragraph("Research Insights", self.styles['CustomHeading3']))

        insights = []
        if len(papers) > 0:
            insights.append(f"• Total of {len(papers)} papers found matching the search criteria.")
            if year_counts:
                latest_year = max(year_counts.keys())
                insights.append(f"• Most recent publications from {latest_year}.")
                if len(year_counts) > 1:
                    years = sorted(year_counts.keys(), reverse=True)[:2]
                    insights.append(f"• Research spans {years[-1]} to {years[0]}.")
            if source_counts:
                top_source = max(source_counts, key=source_counts.get)
                insights.append(f"• Primary data source: {top_source} ({source_counts[top_source]} papers).")
        else:
            insights.append("• No papers found. Consider adjusting search parameters.")

        for insight in insights:
            self.story.append(Paragraph(insight, self.styles['CustomBody']))

    def _add_references_section(self):
        """Add references section in GB/T 7714 format."""
        if not REPORTLAB_AVAILABLE:
            return

        self.story.append(PageBreak())
        self.story.append(Paragraph("References", self.styles['CustomHeading1']))

        papers = self.input_data.get('papers', [])
        for i, paper in enumerate(papers, 1):
            ref_parts = []

            # Authors
            authors = paper.get('authors', [])
            if authors:
                author_names = ', '.join(str(a) for a in authors[:3])
                if len(authors) > 3:
                    author_names += ', et al.'
                ref_parts.append(author_names)

            # Title
            ref_parts.append(paper.get('title', 'N/A'))

            # Journal/Source
            if paper.get('journal'):
                ref_parts.append(paper.get('journal'))

            # Year
            year = paper.get('year') or (paper.get('published', '')[:4] if paper.get('published') else '')
            if year:
                ref_parts.append(year)

            # DOI
            if paper.get('doi'):
                ref_parts.append(f"DOI: {paper.get('doi')}")

            reference = f"[{i}] " + '. '.join(ref_parts) + '.'
            self.story.append(Paragraph(reference, self.styles['CustomBody']))
            self.story.append(Spacer(1, 0.3*cm))

    def generate(self, output_path: str) -> bool:
        """Generate the complete PDF report."""
        if not REPORTLAB_AVAILABLE:
            print("Error: reportlab not installed. Cannot generate PDF.", file=sys.stderr)
            return False

        try:
            # Build document content
            self._add_cover_page()
            self._add_summary_section()
            self._add_papers_section()
            self._add_analysis_section()
            self._add_references_section()

            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # Build PDF
            doc.build(self.story)
            return True

        except Exception as e:
            print(f"Error generating PDF: {e}", file=sys.stderr)
            return False


# ==================== Utility Functions ====================

def load_input_data(input_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON data from paper_search.py output."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data.get('status') != 'success':
            print(f"Error: Input data indicates failed search: {data.get('error', 'Unknown error')}", file=sys.stderr)
            return None

        return data
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error loading input data: {e}", file=sys.stderr)
        return None


def generate_markdown_report(input_data: Dict[str, Any], output_path: str) -> bool:
    """Generate a Markdown report as fallback when PDF generation unavailable."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Title
            f.write(f"# {input_data.get('query', 'Paper Search Results')} Research Report\n\n")

            # Metadata
            f.write("## Search Metadata\n\n")
            f.write(f"- **Research Topic:** {input_data.get('query', 'N/A')}\n")
            f.write(f"- **Generated:** {input_data.get('timestamp', 'N/A')}\n")
            f.write(f"- **Total Papers:** {input_data.get('total_found', 0)}\n")
            f.write(f"- **Data Sources:** {', '.join(input_data.get('sources_used', []))}\n\n")

            # Papers
            f.write("## Core Papers List\n\n")
            papers = input_data.get('papers', [])
            for i, paper in enumerate(papers, 1):
                f.write(f"### Paper #{i}\n\n")
                f.write(f"**Title:** {paper.get('title', 'N/A')}\n\n")

                authors = paper.get('authors', [])
                if authors:
                    author_list = ', '.join(str(a) for a in authors[:5])
                    if len(authors) > 5:
                        author_list += f" et al. ({len(authors)} authors)"
                    f.write(f"**Authors:** {author_list}\n\n")

                year = paper.get('year') or (paper.get('published', '')[:4] if paper.get('published') else 'N/A')
                f.write(f"**Year:** {year}\n\n")

                if paper.get('journal'):
                    f.write(f"**Journal:** {paper.get('journal')}\n\n")

                if paper.get('doi'):
                    f.write(f"**DOI:** [{paper.get('doi')}](https://doi.org/{paper.get('doi')})\n\n")

                if paper.get('citationCount'):
                    f.write(f"**Citations:** {paper.get('citationCount')}\n\n")

                abstract = paper.get('summary') or paper.get('abstract', '')
                if abstract:
                    abstract_text = abstract[:500] + "..." if len(abstract) > 500 else abstract
                    f.write(f"**Abstract:** {abstract_text}\n\n")

                f.write("---\n\n")

            # Analysis
            f.write("## Research Trend Analysis\n\n")
            f.write("This report was generated by Hermes Agent Academic Paper Search System.\n")

        return True
    except Exception as e:
        print(f"Error generating Markdown report: {e}", file=sys.stderr)
        return False


# ==================== CLI Interface ====================

def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF reports from paper search results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate PDF report from JSON
  python generate_report.py --input papers.json --output report.pdf

  # Generate Markdown report
  python generate_report.py --input papers.json --output report.md --format markdown
        """
    )

    parser.add_argument("--input", required=True, help="Input JSON file from paper_search.py")
    parser.add_argument("--output", required=True, help="Output report file path")
    parser.add_argument("--format", default="pdf", choices=["pdf", "markdown"],
                       help="Output format (default: pdf)")

    args = parser.parse_args()

    # Load input data
    input_data = load_input_data(args.input)
    if not input_data:
        return 1

    # Generate report
    if args.format == "pdf":
        generator = PDFReportGenerator(input_data)
        success = generator.generate(args.output)
        if success:
            print(f"[OK] PDF report generated successfully: {args.output}")
            return 0
        else:
            print("❌ Failed to generate PDF report", file=sys.stderr)
            return 1
    else:  # markdown
        success = generate_markdown_report(input_data, args.output)
        if success:
            print(f"[OK] Markdown report generated successfully: {args.output}")
            return 0
        else:
            print("❌ Failed to generate Markdown report", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
