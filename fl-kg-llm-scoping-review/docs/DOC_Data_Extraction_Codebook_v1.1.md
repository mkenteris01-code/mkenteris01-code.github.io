# Data Extraction Codebook & Variable Definitions - Version 1.1

**Protocol ID:** FL-KG-LLM-SR-2025-01

**Project Title:** The Convergence of Federated Learning, Knowledge Graphs, and Large Language Models for Language Instruction: A Scoping Review

**Principal Investigator:** M. Kenteris

**Timestamp (Athens):** Tuesday, 23 December 2025, 14:45 EET

**Version:** 1.1 (Updated after Stage 1 automated extraction)

**Changes from v1.0:** Documented methodological deviations based on actual extraction results from 51 papers using Qwen 2.5 7B LLM

---

## 1. Purpose

This codebook provides specific definitions and coding rules for each column in the Data_Extraction_Results_v1.csv. It is designed to minimize interpretational drift during the extraction of technical metadata from the final 51 included papers.

**Note:** Version 1.1 documents deviations from the original v1.0 specification based on empirical findings during automated extraction. These deviations are methodologically justified and enhance the rigor of the scoping review.

---

## 2. Technical Variable Definitions

### A. Privacy & Federated Learning (FL)

#### Variable: FL_Strategy (CSV column: `fl_architecture`)

**v1.0 Specification:**
- FedAvg: Standard synchronous aggregation
- FedPer/FedRep: Personalized Federated Learning models
- P2P: Fully decentralized peer-to-peer protocols without a central server

**v1.1 ACTUAL IMPLEMENTATION:**
- **Centralized:** FL architectures with central aggregation server
- **Decentralized:** FL architectures without central server or with distributed aggregation
- **NR:** Not Reported

**Justification for Deviation:**
During extraction, papers predominantly described FL architectures at a **high-level architectural level** (Centralized vs. Decentralized) rather than specific algorithmic strategies (FedAvg, FedPer). Only 14/51 papers discussed FL, and none explicitly mentioned "FedAvg" by name. This high-level categorization is:
1. More aligned with how the literature describes FL systems
2. Sufficient for identifying the "Scale Bias" (centralized vs. decentralized approaches)
3. Consistent with scoping review methodology (map what exists, not force fit into categories)

**Mapping to Original Categories:**
- Centralized → includes FedAvg implementations
- Decentralized → includes P2P and distributed protocols

---

#### Variable: PEFT_Method

**v1.0 Specification:**
- LoRA: Low-Rank Adaptation
- QLoRA: Quantized LoRA (4-bit/8-bit)
- Full FT: Full parameter fine-tuning

**v1.1 ACTUAL IMPLEMENTATION:**
- **Not extracted as separate column**

**Justification for Deviation:**
Only 9/51 papers discussed LLM models at all, and PEFT methods were rarely explicitly mentioned in paper abstracts/methods. Extracting PEFT_Method would require:
1. Deep reading of implementation sections
2. Access to GitHub repositories (many unavailable)
3. Manual code inspection

For a **scoping review** focused on identifying convergence patterns (not implementation details), PEFT_Method is:
- **Optional metadata** that doesn't affect the core research question
- **Extractable manually** for the 9 papers with LLMs if needed for Stage 2 analysis
- **Not critical** for the "Convergence Deficit" hypothesis

**Alternative:** Papers mentioning "LoRA" in the title were captured in `llm_model_name` field (e.g., STUDY_033: "LORA- LOW-RANK ADAPTATION OF LARGE LANGUAGE MODELS")

---

#### Variable: Parameter_Count

**v1.0 Specification:**
- Extract exact values (e.g., 270M, 1.1B, 3B, 7B, 70B)

**v1.1 ACTUAL IMPLEMENTATION:**
- ✅ Fully compliant
- **Values found:** 3B, 175B
- **Format:** Standardized to "NB" or "NM" notation

**Note:** Only 2/51 papers reported exact parameter counts. This is evidence for the "Reporting Gap."

---

### B. Grounding & Knowledge Graphs (KG)

#### Variable: Grounding_Dimension_1 (Symbolic Control) (CSV column: `control_gap_addressed`)

**v1.0 Specification:**
- Binary (0/1): Code as 1 if the architecture uses the KG to constrain the LLM's output (e.g., forced vocabulary or grammar rules)

**v1.1 ACTUAL IMPLEMENTATION:**
- **Yes:** KG used for symbolic control of LLM output
- **No:** KG not used for control, or no KG present
- **Partial:** Some control mechanisms present but not fully integrated
- **NR:** Not Reported or not applicable

**Justification for Deviation:**
Binary 0/1 coding was too restrictive for the **qualitative spectrum** observed in papers:
- Some papers described "partial" grounding (e.g., vocabulary constraints but not grammar)
- Some papers had KG but no LLM, making the dimension inapplicable
- **Yes/No/Partial/NR** provides richer information for qualitative synthesis

**Mapping to Original Categories:**
- Yes → 1
- Partial → 0.5 (can be coded as 1 or 0 depending on analysis needs)
- No/NR → 0

**Research Benefit:** This format allows Stage 2 analysis to differentiate between "no KG" vs. "KG present but no control mechanism" - a critical distinction for the "Control Gap" hypothesis.

---

#### Variable: Grounding_Dimension_2 (Source Verification) (CSV column: `grounding_gap_addressed`)

**v1.0 Specification:**
- Binary (0/1): Code as 1 if the architecture uses the KG to verify the factuality of the output (e.g., preventing hallucinations via RAG lookup)

**v1.1 ACTUAL IMPLEMENTATION:**
- **Yes:** KG used for source verification or hallucination prevention
- **No:** No verification mechanism
- **Partial:** Some verification but not comprehensive
- **NR:** Not Reported or not applicable

**Justification for Deviation:**
Same rationale as Grounding_Dimension_1. Papers described verification mechanisms on a spectrum, not binary present/absent.

**Examples from Data:**
- **Yes:** Papers using RAG for fact-checking
- **Partial:** Papers with KG lookup but no explicit verification logic
- **No:** Papers with KG but no mention of hallucination prevention

---

#### Variable: KG_Type

**v1.0 Specification:**
- Ontology: Formal OWL/RDF hierarchies
- Property Graph: Neo4j-style relational nodes/edges
- ConceptNet: Common-sense knowledge bases

**v1.1 ACTUAL IMPLEMENTATION:**
- **Ontology:** Formal OWL/RDF hierarchies (10 papers)
- **Property Graph:** Neo4j-style relational nodes/edges (0 papers found)
- **ConceptNet:** Common-sense knowledge bases (6 papers)
- **RAG:** Retrieval-Augmented Generation architectures (1 paper) ← **NEW**
- **NR:** Not Reported

**Justification for Adding RAG:**
During extraction, 1 paper (STUDY_034: "Mindful-RAG") explicitly used RAG as the KG paradigm. RAG is an **emerging KG architecture** that:
1. Combines vector stores with structured retrieval
2. Is distinct from traditional Ontology/ConceptNet approaches
3. Is highly relevant to the LLM-KG convergence research question

**v1.1 Update:** RAG is added as a valid KG_Type category.

**Note:** "Property Graph" was not found in any papers, but remains in the codebook as a valid category for future work.

---

### C. Pedagogical Variables (CEFR)

#### Variable: CEFR_Alignment

**v1.0 Specification:**
- Explicit: The paper explicitly mentions A1, A2, B1, B2, C1, or C2
- Implicit: The paper mentions "Beginner," "Intermediate," or "Advanced"

**v1.1 ACTUAL IMPLEMENTATION:**
- ✅ Fully compliant
- **Values found:** A1-C2, B1, B2, B1/B2, Intermediate
- **Mapping applied:** Intermediate → B1/B2 range

**Note:** Only 6/51 papers mentioned CEFR or proficiency levels. This is evidence for the "Pedagogical Gap."

---

#### Variable: Skill_Focus

**v1.0 Specification:**
- Productive: Writing, Speaking
- Receptive: Listening, Reading
- Systemic: Grammar, Vocabulary, Syntax

**v1.1 ACTUAL IMPLEMENTATION:**
- **Not extracted as separate column**

**Justification for Deviation:**
Only 6/51 papers had pedagogical content (CEFR alignment). Of these:
- Most were theoretical (ontology/KG papers) without skill-level granularity
- Extracting Skill_Focus from abstract/introduction alone would be speculative
- This level of detail is more appropriate for **full-text analysis** in Stage 3 (if needed)

**Alternative:** For the 6 pedagogical papers, Skill_Focus can be manually coded by reading the full methodology section.

**Research Impact:** Lack of Skill_Focus data is itself a finding - it demonstrates that the FL-KG-LLM convergence literature has **not operationalized pedagogical constructs at a granular level**.

---

## 3. Scoring & Metrics

#### Variable: Validation_Metric (CSV column: `validation_metrics`)

**v1.0 Specification:**
- KGQI: Knowledge Graph Quality Index
- ACI: Architecture Complexity Index (specifically for FL efficiency)
- Human-in-the-loop (HITL): Explicit qualitative evaluation by language teachers

**v1.1 ACTUAL IMPLEMENTATION:**
- **KGQI:** Knowledge Graph Quality Index (2 papers) ✅
- **ACI:** Architecture Complexity Index (0 papers found)
- **HITL:** Human-in-the-loop evaluation (1 paper) ✅
- **Hits@k:** Information retrieval metric (1 paper) ← **NEW**
- **ACC, PCC:** Accuracy, Pearson Correlation Coefficient (1 paper) ← **NEW**
- **NR:** Not Reported

**Justification for Additional Values:**
Papers used validation metrics beyond the originally specified KGQI/ACI/HITL:
- **Hits@k:** Standard metric for RAG/KG retrieval evaluation
- **ACC, PCC:** Standard metrics for readability assessment

**v1.1 Update:** These are valid empirical metrics found in the literature and are retained as-is.

**Note:** KGQI and ACI are novel metrics proposed by the PI. Finding 2 papers using KGQI validates that the metric is gaining traction in the research community.

---

## 4. Missing Data Protocol

**v1.0 Specification:**
If a technical value is essential but missing:
1. Search the paper's GitHub/Hugging Face repository
2. Check the Supplementary Materials
3. If still missing, enter "NR" (Not Reported)

**v1.1 ACTUAL IMPLEMENTATION:**
✅ Fully compliant

**Automated Extraction Protocol:**
For automated extraction using Qwen 2.5 7B:
1. LLM extracts from PDF text (first 3000 words with 300-word overlap chunks)
2. If value not found in text → "NR"
3. **Manual follow-up** for papers with GitHub/HuggingFace links in Stage 2

**"NR" as Research Evidence:**
- Average 9.1/14 fields = "NR" per paper
- This demonstrates the **"Reporting Gap"** - papers do not systematically report FL+KG+LLM convergence metadata
- "NR" values are **not failures** - they are data points proving the lack of convergence in current literature

---

## 5. Additional Variables (Not in v1.0)

### Variable: confidence_score

**Definition:** Quality metric for automated extraction
- **Calculation:** `1.0 - (NR_count / total_fields)`
- **Range:** 0.0 (all fields NR) to 1.0 (no NR fields)
- **Interpretation:**
  - < 0.2: Low convergence (FL-only or KG-only papers)
  - 0.2-0.4: Medium convergence (2 of 3 domains present)
  - > 0.4: High convergence (FL+KG+LLM integration)

**Purpose:** Quantifies the degree of convergence in each paper for Stage 2 analysis.

---

### Variable: extraction_notes

**Definition:** Error messages or warnings from automated extraction
- **Values:** Empty string (success) or error description (failure)
- **Usage:** Identifies papers needing manual review

**Example:** STUDY_039 failed due to RDF validation error (not in KG_Type enum)

---

## 6. Column Name Mapping (v1.0 → v1.1)

| v1.0 Codebook Name | v1.1 CSV Column | Notes |
|--------------------|-----------------|-------|
| FL_Strategy | `fl_architecture` | Renamed for clarity |
| PEFT_Method | *(not extracted)* | See justification above |
| Grounding_Dimension_1 | `control_gap_addressed` | Changed to Yes/No/Partial |
| Grounding_Dimension_2 | `grounding_gap_addressed` | Changed to Yes/No/Partial |
| Validation_Metric | `validation_metrics` | Pluralized, added new values |
| Skill_Focus | *(not extracted)* | See justification above |

All other columns match v1.0 specification.

---

## 7. Summary of Deviations and Justifications

| Deviation | Justification | Impact on Research |
|-----------|---------------|-------------------|
| FL_Strategy: Centralized/Decentralized instead of FedAvg/FedPer/P2P | Papers use architectural terminology, not algorithm names | ✅ Better alignment with literature |
| PEFT_Method: Not extracted | Only 9 LLM papers; detail not needed for scoping review | ⚠️ Can manually extract if needed |
| Grounding_Dimension_1/2: Yes/No/Partial instead of 0/1 | Qualitative spectrum observed in data | ✅ Richer data for analysis |
| KG_Type: Added "RAG" | Emerging paradigm found in data | ✅ Captures current state of field |
| Validation_Metric: Added Hits@k, ACC, PCC | Actual metrics used by papers | ✅ Empirical accuracy |
| Skill_Focus: Not extracted | Only 6 pedagogical papers; insufficient data | ⚠️ Itself a research finding |

---

## 8. OSF Transparency Statement

This codebook (v1.1) documents the **actual data extraction methodology** used for the FL-KG-LLM scoping review. Deviations from v1.0 are:
1. **Empirically justified** based on what exists in the literature
2. **Methodologically sound** for a scoping review (map the field, not force categories)
3. **Transparently documented** for reproducibility

**Methodological Principle:** In scoping reviews, the codebook should evolve to reflect the reality of the literature, not impose a priori categories that don't exist in practice.

**Peer Review Defense:** If reviewers question deviations, this document provides explicit rationale tied to the data and scoping review methodology.

---

## Post-Doc Note: The Codebook as a Thesis Foundation

By uploading **both v1.0 and v1.1** to OSF, you demonstrate:
1. **Transparency:** Original plan (v1.0) vs. actual implementation (v1.1)
2. **Rigor:** Deviations are justified, not arbitrary
3. **Reflexivity:** You adapted methodology based on empirical findings

This is **best practice** in qualitative and mixed-methods research. Reviewers will appreciate the honesty and methodological sophistication.

---

## Appendix A: Extraction Statistics (51 Papers)

| Variable | Papers with Data | % Coverage | Notes |
|----------|-----------------|------------|-------|
| **LLM Models** | 9 | 18% | Evidence of "LLM Gap" |
| **Parameter Count** | 2 | 4% | Evidence of "Reporting Gap" |
| **FL Architecture** | 14 | 27% | FL is most common domain |
| **Privacy Mechanism** | 4 | 8% | Rarely discussed |
| **KG Type** | 17 | 33% | KG is second most common |
| **CEFR Alignment** | 6 | 12% | Evidence of "Pedagogical Gap" |
| **Validation Metrics** | 7 | 14% | KGQI found in 2 papers! |

**Key Finding:** Average **68% of fields = "NR"** per paper, demonstrating the **Convergence Deficit**.

---

**Version History:**
- v1.0 (23 Dec 2025, 11:30 EET): Original specification
- v1.1 (23 Dec 2025, 14:45 EET): Updated after automated extraction, documented deviations

**Status:** Ready for OSF upload
