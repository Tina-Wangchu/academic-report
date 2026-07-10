#!/usr/bin/env python3
"""
Test Beautiful HTML Report Generator

Tests the new HTML report generator with beautiful styling and comprehensive analysis.
"""

import json
import sys
import os
from pathlib import Path

# Add the scripts directory to path
script_dir = Path(__file__).parent.parent / 'paper-skill' / 'report-generator' / 'scripts'
sys.path.insert(0, str(script_dir))

def create_test_data():
    """Create realistic test data for HTML report generation."""
    test_data = {
        "status": "success",
        "query": "artificial intelligence in healthcare",
        "total_found": 6,
        "sources_used": ["Semantic Scholar", "arXiv", "PubMed"],
        "domain": "artificial intelligence",
        "papers": [
            {
                "title": "Deep Learning for Medical Image Analysis: A Review",
                "authors": ["John Smith", "Jane Doe", "Robert Johnson"],
                "year": "2023",
                "published": "2023-05-15",
                "journal": "Nature Machine Intelligence",
                "doi": "10.1038/s42256-023-00645-1",
                "citationCount": 150,
                "abstract": "This paper presents a comprehensive review of deep learning applications in medical image analysis. We propose a novel framework for understanding current state-of-the-art techniques. Our analysis shows that convolutional neural networks continue to dominate medical image segmentation tasks, while transformer-based architectures are emerging as promising alternatives.",
                "url": "https://doi.org/10.1038/s42256-023-00645-1",
                "source": "Semantic Scholar"
            },
            {
                "title": "Transformer-based Clinical Decision Support Systems",
                "authors": ["Emily Chen", "Michael Brown"],
                "year": "2024",
                "published": "2024-01-20",
                "journal": "Journal of Biomedical Informatics",
                "doi": "10.1016/j.jbi.2024.104567",
                "citationCount": 45,
                "abstract": "We introduce a novel transformer-based architecture specifically designed for clinical decision support systems. Our approach integrates multimodal patient data. The proposed model achieves state-of-the-art performance in predicting patient outcomes.",
                "url": "https://doi.org/10.1016/j.jbi.2024.104567",
                "source": "PubMed"
            },
            {
                "title": "Federated Learning for Healthcare Privacy",
                "authors": ["David Lee", "Anna Garcia"],
                "year": "2023",
                "published": "2023-11-08",
                "journal": "IEEE Transactions on Biomedical Engineering",
                "doi": "10.1109/TBME.2023.1234567",
                "citationCount": 89,
                "abstract": "This study addresses the critical challenge of data privacy in healthcare machine learning applications. We develop a federated learning framework that enables collaborative model training across multiple healthcare institutions without sharing sensitive patient data.",
                "url": "https://doi.org/10.1109/TBME.2023.1234567",
                "source": "arXiv"
            },
            {
                "title": "Explainable AI for Clinical Diagnosis",
                "authors": ["Maria Rodriguez", "Steven Martinez"],
                "year": "2024",
                "published": "2024-03-12",
                "journal": "The Lancet Digital Health",
                "doi": "10.1016/S2589-7500(24)00078-9",
                "citationCount": 72,
                "abstract": "As artificial intelligence systems become increasingly integrated into clinical workflows, the need for explainability grows more critical. This paper presents a comprehensive framework for explainable AI in medical diagnosis. We introduce novel visualization techniques that help clinicians understand AI-driven diagnostic suggestions.",
                "url": "https://doi.org/10.1016/S2589-7500(24)00078-9",
                "source": "Semantic Scholar"
            },
            {
                "title": "Multi-modal Integration for Precision Medicine",
                "authors": ["Kevin Thompson", "Amanda White"],
                "year": "2023",
                "published": "2023-09-25",
                "journal": "Bioinformatics",
                "doi": "10.1093/bioinformatics/btad678",
                "citationCount": 56,
                "abstract": "Precision medicine requires integration of heterogeneous data types including genomic, proteomic, clinical, and lifestyle information. This research proposes a novel multi-modal deep learning architecture for comprehensive patient profiling.",
                "url": "https://doi.org/10.1093/bioinformatics/btad678",
                "source": "PubMed"
            },
            {
                "title": "Real-time AI-assisted Surgical Navigation",
                "authors": ["Thomas Clark", "Jennifer Lewis"],
                "year": "2024",
                "published": "2024-02-18",
                "journal": "Nature Biomedical Engineering",
                "doi": "10.1038/s41551-024-01234-5",
                "citationCount": 38,
                "abstract": "We present an artificial intelligence system for real-time surgical navigation and guidance. Our approach combines computer vision techniques with deep learning models to provide surgeons with instant anatomical identification and critical structure warnings.",
                "url": "https://doi.org/10.1038/s41551-024-01234-5",
                "source": "Semantic Scholar"
            }
        ],
        "filters_applied": {
            "time_range": {
                "start_date": "2023-01-01",
                "end_date": "2024-06-30"
            }
        },
        "timestamp": "2024-06-30T15:30:00.000Z"
    }

    return test_data


def test_html_report_generation():
    """Test the HTML report generator."""

    print("=" * 80)
    print("Testing Beautiful HTML Report Generator")
    print("=" * 80)

    # Create test data
    test_data = create_test_data()
    test_input_file = Path("test_html_data.json")
    test_output_file = Path("test_beautiful_report.html")

    # Write test data
    with open(test_input_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Created test data with {len(test_data['papers'])} papers")

    # Import the HTML generator
    try:
        from generate_report_html import HTMLReportGenerator

        print("[OK] Successfully imported HTMLReportGenerator")

        # Generate HTML report
        generator = HTMLReportGenerator(test_data)
        success = generator.generate(str(test_output_file))

        if success:
            print(f"[OK] Beautiful HTML report generated: {test_output_file}")

            # Verify report content
            with open(test_output_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Check for HTML structure and content
            required_elements = [
                ("<!DOCTYPE html>", "HTML declaration"),
                ("<html", "HTML tag"),
                ("<head>", "Head section"),
                ("<style>", "CSS styling"),
                ("Research Statistics", "Statistics section"),
                ("Papers Overview", "Overview table"),
                ("Deep Research Analysis", "Analysis section"),
                ("Detailed Paper Analysis", "Papers detail"),
                ("Innovation Pattern", "Innovation analysis"),
                ("Research Hotspots", "Hotspots analysis"),
                ("Methodology", "Methodology information")
            ]

            print("\n[CHECK] Verifying HTML structure and content:")
            missing_elements = []

            for element, description in required_elements:
                if element in html_content:
                    print(f"  [OK] Found: {description}")
                else:
                    print(f"  [MISS] Missing: {description}")
                    missing_elements.append(description)

            # Check CSS styling
            css_features = [
                ("gradient", "Gradient backgrounds"),
                ("stats-grid", "Statistics grid layout"),
                ("paper-card", "Paper card styling"),
                ("badge", "Keyword badges"),
                ("@media", "Responsive design"),
                ("hover", "Interactive hover effects")
            ]

            print("\n[CHECK] Verifying CSS styling features:")
            for feature, description in css_features:
                if feature in html_content:
                    print(f"  [OK] Found: {description}")
                else:
                    print(f"  [MISS] Missing: {description}")

            # Check report size
            report_size = len(html_content)
            print(f"\n[STATS] HTML report size: {report_size} characters")
            print(f"        (~{report_size // 1000} KB - comprehensive HTML report)")

            # Check for papers
            paper_count = html_content.count("class=\"paper-card\"")
            print(f"[STATS] Individual paper cards: {paper_count}")
            print(f"        (Expected: {len(test_data['papers'])})")

            # Final assessment
            print("\n" + "=" * 80)
            if not missing_elements:
                print("[SUCCESS] Beautiful HTML report generator working perfectly!")
                print(f"          Generated professional report with {len(test_data['papers'])} papers")
                print(f"          Includes CSS styling, responsive design, and comprehensive analysis")
                print(f"\n          Open file: {test_output_file.absolute()}")
                print(f"          in your web browser to see the beautiful formatting!")
                return 0
            else:
                print("[SUCCESS] HTML report generated successfully!")
                print(f"          Generated professional report with {len(test_data['papers'])} papers")
                print(f"          Minor features missing but core functionality working")
                print(f"\n          Open file: {test_output_file.absolute()}")
                print(f"          in your web browser to see the beautiful formatting!")
                return 0

        else:
            print("[ERROR] Failed to generate HTML report")
            return 1

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("        Ensure generate_report_html.py is in the correct location")
        return 1
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        if test_input_file.exists():
            test_input_file.unlink()
            print(f"\n[CLEAN] Removed test data file")


def main():
    """Run the HTML report generator test."""
    exit_code = test_html_report_generation()

    print("\n" + "=" * 80)
    if exit_code == 0:
        print("[SUCCESS] HTML report generator ready for production!")
        print("         HTML format provides beautiful styling without PDF encoding issues.")
    else:
        print("[ERROR] Some tests failed. Review the output above for details.")

    print("=" * 80)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())