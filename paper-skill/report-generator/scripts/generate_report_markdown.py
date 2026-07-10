#!/usr/bin/env python3
"""
Markdown Report Generator — Generate professional Markdown reports

Features:
- Part 1: Summary with papers table (Title, Published, Authors, Keywords)
- Part 2: Individual paper overview with AI-summarized abstracts (100 words)
- Part 3: Research Trend Analysis (Innovation, Trends, Gaps)

Usage:
    python generate_report_markdown.py --input papers.json --output report.md
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any


class MarkdownReportGenerator:
    """Generate professional Markdown reports with improved structure."""

    def __init__(self, input_data: Dict[str, Any]):
        self.input_data = input_data

    def _extract_keywords_from_title(self, title: str, max_keywords: int = 5) -> str:
        """Extract keywords from paper title."""
        import re

        words = re.findall(r'\b[a-zA-Z]{4,}\b', title)

        stop_words = {'study', 'research', 'analysis', 'approach', 'method', 'based', 'using', 'system', 'model'}
        keywords = [w.capitalize() for w in words if w.lower() not in stop_words]

        return ', '.join(keywords[:max_keywords]) if keywords else 'N/A'

    def _summarize_abstract(self, abstract: str, max_words: int = 100) -> str:
        """Summarize abstract to highlight key findings and methods."""
        if not abstract:
            return "No abstract available."

        abstract = abstract.replace('...', '').replace('\n', ' ').strip()

        if len(abstract.split()) <= max_words:
            return abstract

        # Try to extract key sentences
        sentences = abstract.split('.')
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
            words = abstract.split()
            summary = ' '.join(words[:max_words])

        if len(summary.split()) > max_words:
            summary = ' '.join(summary.split()[:max_words]) + '...'

        return summary

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
            result = innovation_sentences[0]
            return result[:100] + '...' if len(result) > 100 else result
        return "Innovation details in full paper"

    def generate(self, output_path: str) -> bool:
        """Generate the complete Markdown report."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Part 1: Summary Page
                self._add_summary_page(f)

                # Part 2: Paper Overview Pages
                self._add_paper_overview_pages(f)

                # Part 3: Research Trend Analysis
                self._add_research_trend_analysis(f)

            return True
        except Exception as e:
            print(f"Error generating Markdown: {e}", file=sys.stderr)
            return False

    def _add_summary_page(self, f):
        """Part 1: Summary with papers table."""
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
        f.write(f"# {domain} Research Report\n\n")
        f.write(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n")

        # Summary Section
        f.write("## 📊 Report Summary\n\n")

        f.write("| Field | Details |\n")
        f.write("|-------|----------|\n")
        f.write(f"| Research Domain | {domain} |\n")
        f.write(f"| Time Range | {time_display} |\n")
        f.write(f"| Total Papers | {len(papers)} |\n")
        f.write(f"| Data Sources | {', '.join(self.input_data.get('sources_used', ['N/A']))} |\n")
        f.write(f"| Report Date | {datetime.now(timezone.utc).strftime('%Y-%m-%d')} |\n\n")

        # Papers Overview Table
        f.write("## 📚 Papers Overview\n\n")

        f.write("| # | Title | Published | Authors | Keywords |\n")
        f.write("|---|-------|----------|--------|----------|\n")

        for i, paper in enumerate(papers, 1):
            # Extract and format data
            title = paper.get('title', 'N/A')
            if len(title) > 40:
                title = title[:37] + "..."

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

            f.write(f"| {i} | {title} | {published} | {authors_text} | {keywords} |\n")

        f.write("\n")

    def _add_paper_overview_pages(self, f):
        """Part 2: Individual paper overview pages."""
        papers = self.input_data.get('papers', [])

        for i, paper in enumerate(papers, 1):
            f.write(f"\n---\n\n")
            f.write(f"# Paper {i}: {paper.get('title', 'N/A')}\n\n")

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

            # Metadata
            f.write("## 📋 Paper Information\n\n")
            f.write(f"- **Authors:** {authors_text}\n")
            f.write(f"- **Published:** {published}\n")
            f.write(f"- **Source:** {paper.get('source', 'N/A')}\n")

            if paper.get('journal'):
                f.write(f"- **Journal:** {paper.get('journal')}\n")
            if paper.get('doi'):
                f.write(f"- **DOI:** {paper.get('doi')}\n")

            f.write("\n")

            # Summarized abstract
            f.write("## 📝 Abstract Summary\n\n")

            abstract = paper.get('abstract', paper.get('summary', ''))
            if abstract:
                summarized = self._summarize_abstract(abstract, max_words=100)
                f.write(f"{summarized}\n\n")
            else:
                f.write("No abstract available for this paper.\n\n")

    def _add_research_trend_analysis(self, f):
        """Part 3: Research Trend Analysis with innovation, trends, and gaps."""
        f.write("\n---\n\n")
        f.write("# 📈 Research Trend Analysis\n\n")

        papers = self.input_data.get('papers', [])
        if not papers:
            f.write("No papers available for trend analysis.\n")
            return

        # Try to use enhanced analysis
        try:
            from enhanced_analysis import ResearchAnalyzer
            analyzer = ResearchAnalyzer()
            self._add_enhanced_trend_analysis(f, papers, analyzer)
        except ImportError:
            self._add_basic_trend_analysis(f, papers)

    def _add_enhanced_trend_analysis(self, f, papers: List[Dict], analyzer):
        """Add enhanced trend analysis with ResearchAnalyzer."""

        # Part 1: Innovation Points
        f.write("## 🔬 Research Innovation Points\n\n")

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
                f.write(f"### {idx}. {innovation['paper']}\n\n")
                f.write(f"**Category:** {innovation['category'].capitalize()}\n\n")
                f.write(f"**Key Innovation:** {innovation['highlight']}\n\n")
        else:
            f.write("No clear innovation points identified from available abstracts.\n\n")

        # Part 2: Research Trends
        f.write("\n## 📊 Research Trends\n\n")

        trends = analyzer.analyze_research_trends(papers)

        # Hot topics
        hot_topics = trends.get('hot_topics', [])[:5]
        if hot_topics:
            f.write("### 🔥 Research Hotspots\n\n")
            for topic in hot_topics:
                f.write(f"- **{topic['keyword']}** (frequency: {topic['frequency']})\n")
            f.write("\n")

        # Trend insights
        trend_insights = trends.get('trend_insights', [])
        if trend_insights:
            f.write("### 📈 Key Insights\n\n")
            for insight in trend_insights:
                f.write(f"- {insight}\n")
            f.write("\n")

        # Part 3: Research Gaps
        f.write("\n## 🔍 Research Gaps & Opportunities\n\n")

        gaps = analyzer.analyze_research_gaps(papers)

        gap_insights = gaps.get('gap_insights', [])
        if gap_insights:
            for gap in gap_insights:
                f.write(f"- {gap}\n")
        else:
            f.write("No significant gaps identified from current paper set.\n")

    def _add_basic_trend_analysis(self, f, papers: List[Dict]):
        """Add basic trend analysis when enhanced_analysis not available."""
        f.write("## 🔬 Research Innovation\n\n")
        f.write("Enhanced trend analysis requires the enhanced_analysis module.\n\n")
        f.write("### Key Research Areas\n\n")

        # Simple keyword analysis
        import re
        from collections import Counter

        all_words = []
        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', paper.get('summary', '')).lower()
            text = f"{title} {abstract}"

            words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
            all_words.extend(words)

        word_counts = Counter(all_words)
        common_words = word_counts.most_common(10)

        f.write("### High-Frequency Keywords\n\n")
        for word, count in common_words:
            f.write(f"- **{word.capitalize()}** (appears {count} times)\n")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate Markdown reports')
    parser.add_argument('--input', required=True, help='Input JSON file with paper data')
    parser.add_argument('--output', required=True, help='Output Markdown file path')

    args = parser.parse_args()

    # Read input data
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    # Generate report
    generator = MarkdownReportGenerator(input_data)
    success = generator.generate(args.output)

    if success:
        print(f"[OK] Markdown report generated: {args.output}", file=sys.stderr)
        return 0
    else:
        print("[ERROR] Failed to generate Markdown report", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
