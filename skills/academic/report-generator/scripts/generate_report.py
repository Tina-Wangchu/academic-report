#!/usr/bin/env python3
"""
Enhanced Report Generator — Generate professional PDF reports with improved structure

Features:
- Page 1: Summary with papers table (Title, Published, Authors, Keywords)
- Page 2+: Individual paper overview with AI-summarized abstracts (100 words)
- Final section: Research Trend Analysis (Innovation, Trends, Gaps)

Usage:
    python generate_report_enhanced.py --input papers.json --output report.pdf
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
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Error: reportlab not installed.", file=sys.stderr)
    print("Install with: pip install reportlab", file=sys.stderr)
    sys.exit(1)

# ==================== Register Chinese Fonts ====================
CHINESE_FONT_AVAILABLE = False
if REPORTLAB_AVAILABLE:
    try:
        import platform
        system = platform.system()

        if system == 'Windows':
            font_paths = [
                ('C:/Windows/Fonts/simhei.ttf', 'SimHei'),
                ('C:/Windows/Fonts/msyh.ttc', 'Microsoft YaHei'),
                ('C:/Windows/Fonts/simsun.ttc', 'SimSun'),
            ]
        elif system == 'Darwin':
            font_paths = [
                ('/System/Library/Fonts/PingFang.ttc', 'PingFang'),
                ('/System/Library/Fonts/STHeiti Medium.ttc', 'STHeiti'),
            ]
        else:
            font_paths = [
                ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 'WQY Zenhei'),
                ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'Noto Sans CJK'),
            ]

        for font_path, font_name in font_paths:
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                CHINESE_FONT_AVAILABLE = True
                CHINESE_FONT_NAME = font_name
                break
            except (FileNotFoundError, OSError):
                continue

        if not CHINESE_FONT_AVAILABLE:
            CHINESE_FONT_NAME = 'Helvetica'
    except Exception as e:
        CHINESE_FONT_NAME = 'Helvetica'
else:
    CHINESE_FONT_NAME = 'Helvetica'


class EnhancedPDFReportGenerator:
    """Generate enhanced academic PDF reports with improved structure."""

    def __init__(self, input_data: Dict[str, Any]):
        self.input_data = input_data
        self.styles = self._create_styles()
        self.story = []

    def _create_styles(self):
        """Create custom paragraph styles."""
        styles = getSampleStyleSheet()

        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#2C5F8D'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=CHINESE_FONT_NAME,
            leading=28
        ))

        # Heading 1
        styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2C5F8D'),
            spaceAfter=12,
            spaceBefore=15,
            fontName=CHINESE_FONT_NAME,
            leading=20
        ))

        # Heading 2
        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=10,
            spaceBefore=12,
            fontName=CHINESE_FONT_NAME,
            leading=16
        ))

        # Heading 3
        styles.add(ParagraphStyle(
            name='CustomHeading3',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=8,
            spaceBefore=10,
            fontName=CHINESE_FONT_NAME,
            leading=14
        ))

        # Body text
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            spaceAfter=6,
            leading=14,
            fontName=CHINESE_FONT_NAME
        ))

        # Meta text
        styles.add(ParagraphStyle(
            name='CustomMeta',
            parent=styles['BodyText'],
            fontSize=9,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=4,
            fontName=CHINESE_FONT_NAME
        ))

        return styles

    def _extract_keywords_from_title(self, title: str, max_keywords: int = 5) -> str:
        """Extract keywords from paper title."""
        import re

        # Simple keyword extraction - split by common words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', title)

        # Filter out common words
        stop_words = {'study', 'research', 'analysis', 'approach', 'method', 'based', 'using', 'system', 'model'}
        keywords = [w.capitalize() for w in words if w.lower() not in stop_words]

        # Return top keywords
        return ', '.join(keywords[:max_keywords]) if keywords else 'N/A'

    def _summarize_abstract(self, abstract: str, max_words: int = 100) -> str:
        """Summarize abstract to highlight key findings and methods."""
        if not abstract:
            return "No abstract available."

        # Clean up abstract
        abstract = abstract.replace('...', '').replace('\n', ' ').strip()

        # If abstract is already short, return as is
        if len(abstract.split()) <= max_words:
            return abstract

        # Try to extract key sentences
        sentences = abstract.split('.')

        # Look for sentences with key indicators
        key_indicators = ['propose', 'present', 'show', 'demonstrate', 'achieve', 'develop', 'introduce', 'prove']

        key_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in key_indicators):
                key_sentences.append(sentence)
                if len(' '.join(key_sentences).split()) >= max_words:
                    break

        if key_sentences:
            summary = ' '.join(key_sentences)
        else:
            # Fallback: take first meaningful sentences
            words = abstract.split()
            summary = ' '.join(words[:max_words])

        # Ensure it ends cleanly
        if len(summary.split()) > max_words:
            summary = ' '.join(summary.split()[:max_words]) + '...'

        return summary

    def _add_summary_page(self):
        """Page 1: Summary with papers table."""
        papers = self.input_data.get('papers', [])
        filters = self.input_data.get('filters_applied', {})
        time_range = filters.get('time_range', {})

        # Extract domain
        domain = self.input_data.get('domain', 'General')
        domain = domain.capitalize()

        # Calculate time range
        start_date = time_range.get('start_date', 'N/A')
        end_date = time_range.get('end_date', 'N/A')

        if start_date != 'N/A' and end_date != 'N/A':
            time_display = f"{start_date} to {end_date}"
        else:
            # Extract from papers
            if papers:
                years = []
                for p in papers:
                    if p.get('year'):
                        years.append(p['year'])
                    elif p.get('published'):
                        try:
                            years.append(p['published'][:4])
                        except:
                            pass
                if years:
                    time_display = f"{min(years)}-{max(years)}"
                else:
                    time_display = "N/A"
            else:
                time_display = "N/A"

        # Title
        title = f"{domain} Research Report"
        self.story.append(Paragraph(title, self.styles['CustomTitle']))
        self.story.append(Spacer(1, 0.5*cm))

        # Summary Table
        self.story.append(Paragraph("📊 Report Summary", self.styles['CustomHeading1']))

        summary_data = [
            ["<b>Field</b>", "<b>Details</b>"],
            ["Research Domain", domain],
            ["Time Range", time_display],
            ["Total Papers", str(len(papers))],
            ["Data Sources", ', '.join(self.input_data.get('sources_used', ['N/A']))],
            ["Report Date", datetime.now(timezone.utc).strftime('%Y-%m-%d')]
        ]

        summary_table = Table(summary_data, colWidths=[5*cm, 8*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT_NAME),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        self.story.append(summary_table)
        self.story.append(Spacer(1, 0.8*cm))

        # Papers Overview Table
        self.story.append(Paragraph("📚 Papers Overview", self.styles['CustomHeading1']))
        self.story.append(Spacer(1, 0.3*cm))

        table_data = [["<b>Title</b>", "<b>Published</b>", "<b>Authors</b>", "<b>Keywords</b>"]]

        for paper in papers:
            # Extract and format data
            title = paper.get('title', 'N/A')
            if len(title) > 50:
                title = title[:47] + "..."

            # Get publication date
            published = paper.get('published', paper.get('year', 'N/A'))
            if published and len(str(published)) > 10:
                published = str(published)[:10]

            # Get authors
            authors = paper.get('authors', [])
            if authors and isinstance(authors, list):
                if len(authors) > 2:
                    authors_text = ', '.join(str(a).split()[0] if ' ' in str(a) else str(a) for a in authors[:2]) + ' et al.'
                else:
                    authors_text = ', '.join(str(a).split()[0] if ' ' in str(a) else str(a) for a in authors)
            else:
                authors_text = 'N/A'

            # Extract keywords
            keywords = self._extract_keywords_from_title(title)

            table_data.append([title, published, authors_text, keywords])

        papers_table = Table(table_data, colWidths=[5.5*cm, 2*cm, 3.5*cm, 4*cm])
        papers_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5F8D')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        self.story.append(papers_table)

    def _add_paper_overview_pages(self):
        """Part 2: Individual paper overview pages."""
        papers = self.input_data.get('papers', [])

        for i, paper in enumerate(papers, 1):
            self.story.append(PageBreak())

            # Paper title
            title = paper.get('title', 'N/A')
            self.story.append(Paragraph(f"Paper {i}: {title}", self.styles['CustomHeading1']))
            self.story.append(Spacer(1, 0.5*cm))

            # Paper metadata
            authors = paper.get('authors', [])
            if authors and isinstance(authors, list):
                if len(authors) > 5:
                    authors_text = ', '.join(str(a) for a in authors[:5]) + ' et al.'
                else:
                    authors_text = ', '.join(str(a) for a in authors)
            else:
                authors_text = 'N/A'

            published = paper.get('published', paper.get('year', 'N/A'))
            if published and len(str(published)) > 10:
                published = str(published)[:10]

            # Metadata table
            meta_data = [
                ["<b>Authors:</b>", authors_text],
                ["<b>Published:</b>", str(published)],
                ["<b>Source:</b>", paper.get('source', 'N/A')]
            ]

            for meta_label, meta_value in meta_data:
                self.story.append(Paragraph(f"{meta_label} {meta_value}", self.styles['CustomBody']))

            self.story.append(Spacer(1, 0.8*cm))

            # Summarized abstract
            self.story.append(Paragraph("📝 Abstract Summary", self.styles['CustomHeading2']))

            abstract = paper.get('abstract', paper.get('summary', ''))
            if abstract:
                summarized = self._summarize_abstract(abstract, max_words=100)
                self.story.append(Paragraph(summarized, self.styles['CustomBody']))
            else:
                self.story.append(Paragraph("No abstract available for this paper.", self.styles['CustomBody']))

            # Additional info if available
            if paper.get('journal'):
                self.story.append(Spacer(1, 0.5*cm))
                self.story.append(Paragraph(f"<b>Journal:</b> {paper.get('journal')}", self.styles['CustomMeta']))

            if paper.get('doi'):
                self.story.append(Paragraph(f"<b>DOI:</b> {paper.get('doi')}", self.styles['CustomMeta']))

    def _add_research_trend_analysis(self):
        """Part 3: Research Trend Analysis with innovation, trends, and gaps."""
        self.story.append(PageBreak())
        self.story.append(Paragraph("📈 Research Trend Analysis", self.styles['CustomHeading1']))

        papers = self.input_data.get('papers', [])
        if not papers:
            self.story.append(Paragraph("No papers available for trend analysis.", self.styles['CustomBody']))
            return

        # Import enhanced analysis if available
        try:
            from enhanced_analysis import ResearchAnalyzer
            analyzer = ResearchAnalyzer()
            enhanced_analysis = True
        except ImportError:
            enhanced_analysis = False

        if enhanced_analysis:
            self._add_enhanced_trend_analysis(papers, analyzer)
        else:
            self._add_basic_trend_analysis(papers)

    def _add_enhanced_trend_analysis(self, papers: List[Dict], analyzer):
        """Add enhanced trend analysis with ResearchAnalyzer."""
        # Part 1: Innovation Points
        self.story.append(Paragraph("🔬 Research Innovation Points", self.styles['CustomHeading2']))

        # Analyze innovation from abstracts
        innovation_keywords = {
            'novel': ['novel', 'new', 'first', 'innovative'],
            'method': ['method', 'approach', 'technique', 'algorithm'],
            'performance': ['improve', 'outperform', 'exceed', 'achieve'],
            'theory': ['theory', 'framework', 'model', 'formalism']
        }

        innovations = []
        for paper in papers:
            abstract = paper.get('abstract', paper.get('summary', '')).lower()
            title = paper.get('title', '').lower()

            for category, keywords in innovation_keywords.items():
                if any(kw in abstract or kw in title for kw in keywords):
                    innovations.append({
                        'category': category,
                        'paper': paper.get('title', 'N/A'),
                        'highlight': self._extract_innovation_phrase(abstract)
                    })
                    break

        if innovations:
            for idx, innovation in enumerate(innovations[:5], 1):
                self.story.append(Paragraph(f"{idx}. {innovation['paper']}", self.styles['CustomHeading3']))
                self.story.append(Paragraph(f"Category: {innovation['category'].capitalize()} | {innovation['highlight']}",
                                             self.styles['CustomBody']))
                self.story.append(Spacer(1, 0.3*cm))
        else:
            self.story.append(Paragraph("No clear innovation points identified from available abstracts.", self.styles['CustomBody']))

        self.story.append(Spacer(1, 0.5*cm))

        # Part 2: Research Trends
        trends = analyzer.analyze_research_trends(papers)
        self.story.append(Paragraph("📊 Research Trends", self.styles['CustomHeading2']))

        # Hot topics
        hot_topics = trends.get('hot_topics', [])[:5]
        if hot_topics:
            self.story.append(Paragraph("🔥 Research Hotspots:", self.styles['CustomHeading3']))
            for topic in hot_topics:
                self.story.append(Paragraph(f"• {topic['keyword']} (frequency: {topic['frequency']})",
                                             self.styles['CustomBody']))
            self.story.append(Spacer(1, 0.3*cm))

        # Trend insights
        trend_insights = trends.get('trend_insights', [])
        if trend_insights:
            self.story.append(Paragraph("📈 Key Insights:", self.styles['CustomHeading3']))
            for insight in trend_insights:
                self.story.append(Paragraph(f"• {insight}", self.styles['CustomBody']))

        self.story.append(Spacer(1, 0.5*cm))

        # Part 3: Research Gaps
        gaps = analyzer.analyze_research_gaps(papers)
        self.story.append(Paragraph("🔍 Research Gaps & Opportunities", self.styles['CustomHeading2']))

        gap_insights = gaps.get('gap_insights', [])
        if gap_insights:
            for gap in gap_insights:
                self.story.append(Paragraph(f"• {gap}", self.styles['CustomBody']))
        else:
            self.story.append(Paragraph("No significant gaps identified from current paper set.", self.styles['CustomBody']))

    def _add_basic_trend_analysis(self, papers: List[Dict]):
        """Add basic trend analysis when enhanced_analysis not available."""
        self.story.append(Paragraph("🔬 Research Innovation", self.styles['CustomHeading2']))
        self.story.append(Paragraph("Enhanced trend analysis requires the enhanced_analysis module.", self.styles['CustomBody']))
        self.story.append(Paragraph("Key research areas observed from titles and abstracts:", self.styles['CustomBody']))

        # Simple keyword analysis
        all_words = []
        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', paper.get('summary', '')).lower()
            text = f"{title} {abstract}"

            import re
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
            all_words.extend(words)

        from collections import Counter
        word_counts = Counter(all_words)
        common_words = word_counts.most_common(10)

        self.story.append(Spacer(1, 0.5*cm))
        for word, count in common_words:
            self.story.append(Paragraph(f"• {word.capitalize()} (appears {count} times)", self.styles['CustomBody']))

    def _extract_innovation_phrase(self, text: str) -> str:
        """Extract key innovation phrase from text."""
        sentences = text.split('.')

        innovation_sentences = []
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['propose', 'present', 'introduce', 'develop', 'novel']):
                innovation_sentences.append(sentence.strip())
                if len(innovation_sentences) >= 2:
                    break

        if innovation_sentences:
            return innovation_sentences[0][:100] + '...' if len(innovation_sentences[0]) > 100 else innovation_sentences[0]
        return "Innovation details in full paper"

    def generate(self, output_path: str) -> bool:
        """Generate the complete PDF report."""
        if not REPORTLAB_AVAILABLE:
            return False

        try:
            # Page 1: Summary
            self._add_summary_page()

            # Pages 2+: Paper overviews
            self._add_paper_overview_pages()

            # Final section: Research trends
            self._add_research_trend_analysis()

            # Build PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            doc.build(self.story)
            return True

        except Exception as e:
            print(f"Error generating PDF: {e}", file=sys.stderr)
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate enhanced PDF reports')
    parser.add_argument('--input', required=True, help='Input JSON file with paper data')
    parser.add_argument('--output', required=True, help='Output PDF file path')

    args = parser.parse_args()

    # Read input data
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    # Generate report
    generator = EnhancedPDFReportGenerator(input_data)
    success = generator.generate(args.output)

    if success:
        print(f"[OK] Enhanced PDF report generated: {args.output}", file=sys.stderr)
        return 0
    else:
        print("[ERROR] Failed to generate PDF report", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
