# FL-KG-LLM Scoping Review - Data Extraction Pipeline

Automated data extraction pipeline for the scoping review: "The Convergence of Federated Learning, Knowledge Graphs, and Large Language Models for Language Instruction"

**OSF Registration:** [Add OSF DOI after submission]
**Protocol ID:** FL-KG-LLM-SR-2025-01
**Date:** December 2025

## Overview

This repository contains reproducible code for extracting metadata from 51 papers using Qwen 2.5 7B LLM and automated data extraction.

## Key Features

- ✅ Automated extraction using local GPU (Qwen 2.5 7B)
- ✅ Pydantic schema validation
- ✅ Confidence scoring for data quality
- ✅ Full reproducibility with provided codebook
- ✅ Transparent methodological documentation

## Requirements

- Python 3.9+
- GPU server running Qwen 2.5 7B (or modify for other LLMs)
- Dependencies: PyPDF2, Pydantic, requests, pandas

## Installation

```bash
git clone https://github.com/mkenteris01-code/mkenteris01-code.git
cd fl-kg-llm-scoping-review
pip install -r requirements_rig.txt
```

## Usage

### Basic Extraction

```bash
python agentic_extraction_rig.py
```

The script will:
1. Process PDFs from the configured directory
2. Extract metadata according to codebook schema
3. Generate `Data_Extraction_Results_v1.csv`

### Validation

```bash
# Check codebook compliance
python scripts/codebook_compliance_check.py

# Analyze extraction results
python scripts/analyze_results.py
```

## Data

**Extraction results** (Data_Extraction_Results_v1.csv) are available on OSF: [Add link after upload]

**PDFs** are not included due to copyright. DOIs are provided in the CSV for institutional access.

## Documentation

- **Codebook:** [`docs/DOC_Data_Extraction_Codebook_v1.1.md`](docs/DOC_Data_Extraction_Codebook_v1.1.md) - Full extraction schema
- **Methodological Deviations:** [`docs/DOC_Methodological_Deviations_Stage1.md`](docs/DOC_Methodological_Deviations_Stage1.md) - Transparency document
- **Implementation:** [`docs/IMPLEMENTATION_SUMMARY.md`](docs/IMPLEMENTATION_SUMMARY.md) - Technical details

## Reproducibility

All code, schemas, and methodological decisions are fully documented to enable:
- ✅ Verification of extraction accuracy
- ✅ Replication with different papers
- ✅ Adaptation for other scoping reviews

## Methodology

This scoping review followed PRISMA-ScR guidelines with:
- **Search:** November-December 2025 (IEEE, ACM, Scopus, arXiv, Google Scholar)
- **Screening:** Manual by primary researcher (51 papers from ~660 initial hits)
- **Extraction:** Automated using Qwen 2.5 7B (December 23, 2025)
- **Validation:** Pydantic schema + confidence scoring

## Citation

```
[To be added after publication]
Kenteris, M. (2025). The Convergence of Federated Learning, Knowledge Graphs,
and Large Language Models for Language Instruction: A Scoping Review.
OSF Registration: [DOI]
```

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contact

- **Author:** M. Kenteris
- **Institution:** [Add institution]
- **Email:** [Add contact email]

## Acknowledgments

- GPU infrastructure: HITL-forge project
- LLM model: Qwen 2.5 7B (Alibaba Cloud)
- Framework: PRISMA-ScR guidelines

---

**Last Updated:** December 24, 2025
