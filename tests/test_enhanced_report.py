#!/usr/bin/env python3
"""
Test Enhanced Markdown Report Generator

Tests the new enhanced report generator with deep trend analysis capabilities.
"""

import json
import sys
import os
from pathlib import Path

# Add the scripts directory to path
script_dir = Path(__file__).parent.parent / 'paper-skill' / 'report-generator' / 'scripts'
sys.path.insert(0, str(script_dir))

def create_test_data():
    """Create realistic test data for enhanced report generation."""
    test_data = {
        "status": "success",
        "query": "machine learning in healthcare applications",
        "total_found": 8,
        "sources_used": ["Semantic Scholar", "arXiv", "PubMed"],
        "domain": "machine learning",
        "papers": [
            {
                "title": "Deep Learning for Medical Image Analysis: A Comprehensive Review",
                "authors": ["John Smith", "Jane Doe", "Robert Johnson"],
                "year": "2023",
                "published": "2023-05-15",
                "journal": "Nature Machine Intelligence",
                "doi": "10.1038/s42256-023-00645-1",
                "citationCount": 150,
                "abstract": "This paper presents a comprehensive review of deep learning applications in medical image analysis. We propose a novel framework for understanding the current state-of-the-art techniques and identify key challenges in the field. Our analysis shows that convolutional neural networks continue to dominate medical image segmentation tasks, while transformer-based architectures are emerging as promising alternatives for multimodal data integration. The study demonstrates significant improvements in diagnostic accuracy across various medical imaging modalities, including MRI, CT scans, and X-ray images. We also discuss the critical importance of interpretability and clinical validation in deploying these systems.",
                "url": "https://doi.org/10.1038/s42256-023-00645-1",
                "source": "Semantic Scholar"
            },
            {
                "title": "Transformer-based Models for Clinical Decision Support Systems",
                "authors": ["Emily Chen", "Michael Brown", "Sarah Williams"],
                "year": "2024",
                "published": "2024-01-20",
                "journal": "Journal of Biomedical Informatics",
                "doi": "10.1016/j.jbi.2024.104567",
                "citationCount": 45,
                "abstract": "We introduce a novel transformer-based architecture specifically designed for clinical decision support systems. Our approach integrates multimodal patient data, including electronic health records, medical images, and genomic information. The proposed model achieves state-of-the-art performance in predicting patient outcomes and recommending treatment protocols. Experimental results on three large-scale clinical datasets demonstrate superior accuracy compared to traditional machine learning methods. The system also provides interpretable attention maps that help clinicians understand the model's decision-making process.",
                "url": "https://doi.org/10.1016/j.jbi.2024.104567",
                "source": "PubMed"
            },
            {
                "title": "Federated Learning for Privacy-Preserving Healthcare Analytics",
                "authors": ["David Lee", "Anna Garcia", "James Wilson"],
                "year": "2023",
                "published": "2023-11-08",
                "journal": "IEEE Transactions on Biomedical Engineering",
                "doi": "10.1109/TBME.2023.1234567",
                "citationCount": 89,
                "abstract": "This study addresses the critical challenge of data privacy in healthcare machine learning applications. We develop a federated learning framework that enables collaborative model training across multiple healthcare institutions without sharing sensitive patient data. Our methodology incorporates differential privacy techniques and secure aggregation protocols to protect patient information while maintaining high model accuracy. Extensive experiments on medical prediction tasks show that our federated approach achieves comparable performance to centralized training while ensuring strict privacy guarantees.",
                "url": "https://doi.org/10.1109/TBME.2023.1234567",
                "source": "arXiv"
            },
            {
                "title": "Explainable AI for Clinical Diagnosis: Methods and Applications",
                "authors": ["Maria Rodriguez", "Steven Martinez", "Lisa Anderson"],
                "year": "2024",
                "published": "2024-03-12",
                "journal": "The Lancet Digital Health",
                "doi": "10.1016/S2589-7500(24)00078-9",
                "citationCount": 72,
                "abstract": "As artificial intelligence systems become increasingly integrated into clinical workflows, the need for explainability and interpretability grows more critical. This paper presents a comprehensive framework for explainable AI in medical diagnosis. We introduce novel visualization techniques that help clinicians understand AI-driven diagnostic suggestions and identify potential biases or limitations. Our approach combines gradient-based attribution methods with counterfactual explanations to provide both local and global interpretability. Clinical validation studies show that our explainable AI system improves physician trust and adoption while maintaining high diagnostic accuracy.",
                "url": "https://doi.org/10.1016/S2589-7500(24)00078-9",
                "source": "Semantic Scholar"
            },
            {
                "title": "Multi-modal Integration for Precision Medicine",
                "authors": ["Kevin Thompson", "Amanda White", "Christopher Harris"],
                "year": "2023",
                "published": "2023-09-25",
                "journal": "Bioinformatics",
                "doi": "10.1093/bioinformatics/btad678",
                "citationCount": 56,
                "abstract": "Precision medicine requires integration of heterogeneous data types including genomic, proteomic, clinical, and lifestyle information. This research proposes a novel multi-modal deep learning architecture for comprehensive patient profiling. Our method effectively combines different data modalities through attention-based fusion mechanisms that learn the relative importance of each data type for specific clinical predictions. Experimental results demonstrate superior performance in predicting drug response and disease prognosis compared to single-modality approaches.",
                "url": "https://doi.org/10.1093/bioinformatics/btad678",
                "source": "PubMed"
            },
            {
                "title": "Real-time AI-assisted Surgical Navigation Systems",
                "authors": ["Thomas Clark", "Jennifer Lewis", "Daniel Walker"],
                "year": "2024",
                "published": "2024-02-18",
                "journal": "Nature Biomedical Engineering",
                "doi": "10.1038/s41551-024-01234-5",
                "citationCount": 38,
                "abstract": "We present an artificial intelligence system for real-time surgical navigation and guidance. Our approach combines computer vision techniques with deep learning models to provide surgeons with instant anatomical identification and critical structure warnings. The system processes endoscopic video streams in real-time, highlighting important anatomical structures and potential risks. Clinical trials show that the AI-assisted navigation reduces surgical complications and shortens procedure times while maintaining safety standards.",
                "url": "https://doi.org/10.1038/s41551-024-01234-5",
                "source": "Semantic Scholar"
            },
            {
                "title": "Natural Language Processing for Clinical Text Analysis",
                "authors": ["Michelle Young", "Robert King", "Patricia Wright"],
                "year": "2023",
                "published": "2023-12-05",
                "journal": "JAMIA",
                "doi": "10.1093/jamia/ocad234",
                "citationCount": 64,
                "abstract": "Electronic health records contain valuable clinical information in unstructured text format. This study develops advanced natural language processing models for extracting meaningful insights from clinical notes. Our transformer-based models achieve state-of-the-art performance in clinical concept extraction, medication reconciliation, and disease phenotype identification. The processed information can be used for clinical decision support, quality improvement, and research purposes while maintaining patient privacy through de-identification techniques.",
                "url": "https://doi.org/10.1093/jamia/ocad234",
                "source": "PubMed"
            },
            {
                "title": "Automated Drug Discovery Using Graph Neural Networks",
                "authors": ["Daniel Green", "Susan Baker", "Matthew Adams"],
                "year": "2024",
                "published": "2024-04-30",
                "journal": "Science Advances",
                "doi": "10.1126/sciadv.adf1234",
                "citationCount": 28,
                "abstract": "Drug discovery is a time-consuming and expensive process that can benefit from artificial intelligence acceleration. This paper introduces a graph neural network approach for molecular property prediction and drug candidate screening. Our models learn to predict molecular properties, binding affinities, and potential side effects directly from molecular structures. We demonstrate that our AI system can identify promising drug candidates significantly faster than traditional methods while maintaining high accuracy. The approach shows particular promise for rare diseases and personalized medicine applications.",
                "url": "https://doi.org/10.1126/sciadv.adf1234",
                "source": "arXiv"
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


def test_enhanced_report_generation():
    """Test the enhanced report generator with comprehensive checks."""

    print("=" * 80)
    print("Testing Enhanced Markdown Report Generator")
    print("=" * 80)

    # Create test data
    test_data = create_test_data()
    test_input_file = Path("test_enhanced_data.json")
    test_output_file = Path("test_enhanced_report.md")

    # Write test data
    with open(test_input_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Created test data with {len(test_data['papers'])} papers")

    # Import the enhanced generator
    try:
        from generate_report_enhanced import EnhancedMarkdownReportGenerator

        print("[OK] Successfully imported EnhancedMarkdownReportGenerator")

        # Generate report
        generator = EnhancedMarkdownReportGenerator(test_data)
        success = generator.generate(str(test_output_file))

        if success:
            print(f"[OK] Enhanced report generated: {test_output_file}")

            # Verify report content
            with open(test_output_file, 'r', encoding='utf-8') as f:
                report_content = f.read()

            # Check for essential analysis sections
            required_sections = [
                "Comprehensive Research Summary",  # Summary
                "Papers Overview",  # Papers table
                "Deep Research Trend Analysis",  # Deep analysis
                "Innovation Pattern Analysis",  # Innovation
                "Research Hotspots",  # Hotspots
                "Temporal Research Evolution",  # Evolution
                "Research Gaps",  # Gaps
                "Future Research Directions",  # Future
                "References"  # References
            ]

            print("\n[CHECK] Verifying report structure:")
            missing_sections = []

            for section in required_sections:
                if section in report_content:
                    print(f"  [OK] Found: {section}")
                else:
                    print(f"  [MISS] Missing: {section}")
                    missing_sections.append(section)

            # Check for title (any # heading with Research Report)
            has_title = "Research Report" in report_content and "# " in report_content[:500]
            if has_title:
                print(f"  [OK] Found: Research Report title")
            else:
                print(f"  [MISS] Missing: Research Report title")

            # Check for deep analysis features
            analysis_features = [
                ("Innovation Type Distribution", "Innovation Type Distribution" in report_content),
                ("Research Clusters", "Research Clusters" in report_content or "Top Research Clusters" in report_content),
                ("Temporal Evolution", "Temporal Research Evolution" in report_content or "Temporal Evolution" in report_content),
                ("Methodological Analysis", "Methodological" in report_content or "methodology" in report_content.lower()),
                ("Cross-domain Analysis", "Cross-Domain" in report_content or "Interdisciplinary" in report_content),
                ("Future Directions", "Future Research Directions" in report_content or "Future Directions" in report_content)
            ]

            print("\n[CHECK] Verifying analysis features:")
            for feature_name, found in analysis_features:
                status = "[OK]" if found else "[MISS]"
                print(f"  {status} {feature_name}")

            # Count papers in report
            paper_count = report_content.count("# Paper")
            print(f"\n[STATS] Individual paper analyses: {paper_count}")
            print(f"        (Expected: {len(test_data['papers'])})")

            # Check report size
            report_size = len(report_content)
            print(f"\n[STATS] Report size: {report_size} characters")
            print(f"        (~{report_size // 1000} KB - comprehensive analysis)")

            # Final assessment
            print("\n" + "=" * 80)
            if not missing_sections and all(found for _, found in analysis_features):
                print("[SUCCESS] Enhanced report generator working perfectly!")
                print(f"          Generated comprehensive report with {len(test_data['papers'])} papers")
                print(f"          All deep analysis features present and functional")
                return 0
            else:
                print("[PARTIAL] Report generated but some features missing")
                if missing_sections:
                    print(f"          Missing sections: {len(missing_sections)}")
                missing_features = [name for name, found in analysis_features if not found]
                if missing_features:
                    print(f"          Missing features: {missing_features}")
                return 1

        else:
            print("[ERROR] Failed to generate enhanced report")
            return 1

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("        Ensure generate_report_enhanced.py is in the correct location")
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
    """Run the enhanced report generator test."""
    exit_code = test_enhanced_report_generation()

    print("\n" + "=" * 80)
    if exit_code == 0:
        print("[SUCCESS] All tests passed! Enhanced report generator is ready for production.")
    else:
        print("[ERROR] Some tests failed. Review the output above for details.")

    print("=" * 80)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())