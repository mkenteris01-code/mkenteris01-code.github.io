"""
Agentic AI Stack for Stage 1: Technical Evidence Audit
Uses EXISTING GPU RIG instead of Ollama

Project: FL-KG-LLM Convergence Scoping Review
Author: M. Kenteris
Date: 23 December 2025

This script uses your existing GPU rig infrastructure:
- Mistral-7B on port 8100 (192.168.1.150)
- No need to install Ollama or download new models
- Same architecture as HITL-forge project

Architecture:
    - Orchestrator Agent: Coordinates workflow and handles retries
    - PDF Loader Agent: Extracts and chunks text from PDFs
    - Extraction Agent Pool: Specialized agents for different metadata types
    - Validation Agent: Ensures schema compliance and quality
    - CSV Writer Agent: Populates the Data_Extraction_Template_v1.csv

Cost Savings: Uses local GPU rig (Mistral-7B) instead of API calls
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import pandas as pd
import PyPDF2
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ============================================================================

class FLStrategy(str, Enum):
    """Federated Learning Strategy Types"""
    FED_AVG = "FedAvg"
    FED_PER = "FedPer"
    FED_REP = "FedRep"
    P2P = "P2P"
    NOT_REPORTED = "NR"


class PEFTMethod(str, Enum):
    """Parameter-Efficient Fine-Tuning Methods"""
    LORA = "LoRA"
    QLORA = "QLoRA"
    FULL_FT = "Full FT"
    NOT_REPORTED = "NR"


class KGType(str, Enum):
    """Knowledge Graph Types"""
    ONTOLOGY = "Ontology"
    PROPERTY_GRAPH = "Property Graph"
    CONCEPT_NET = "ConceptNet"
    RAG = "RAG"
    NOT_REPORTED = "NR"


class CEFRLevel(str, Enum):
    """CEFR Alignment Levels"""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    NOT_REPORTED = "NR"


class ValidationMetric(str, Enum):
    """Validation Metrics"""
    KGQI = "KGQI"
    ACI = "ACI"
    HITL = "HITL"
    NOT_REPORTED = "NR"


class ExtractedMetadata(BaseModel):
    """Complete metadata schema matching Data_Extraction_Template_v1.csv"""
    study_id: str = Field(description="Unique study identifier")
    author: str = Field(description="First author or lead author")
    year: int = Field(description="Publication year")
    title: str = Field(description="Paper title")
    llm_model_name: str = Field(description="LLM model name (e.g., Llama-3-8B)")
    parameter_count: str = Field(description="Parameter count in millions (e.g., 270M, 7B)")
    slm_feasibility: str = Field(description="Small Language Model feasibility: Yes/No")
    fl_architecture: str = Field(description="FL Architecture: Centralized/Decentralized/PEFT")
    kg_type: KGType = Field(description="Knowledge Graph type")
    cefr_alignment: str = Field(description="CEFR alignment: Dimension 1/Dimension 2")
    privacy_mechanism: str = Field(description="Privacy mechanism used")
    validation_metrics: str = Field(description="Validation metrics: KGQI/ACI/HITL")
    grounding_dimension_1: int = Field(description="Symbolic Control: 0 or 1")
    grounding_dimension_2: int = Field(description="Source Verification: 0 or 1")
    grounding_gap_addressed: str = Field(description="Whether grounding gap is addressed")
    control_gap_addressed: str = Field(description="Whether control gap is addressed")

    # Additional quality tracking fields
    confidence_score: float = Field(default=0.0, description="Extraction confidence 0-1")
    extraction_notes: str = Field(default="", description="Notes on extraction challenges")


# ============================================================================
# AGENT BASE CLASSES
# ============================================================================

@dataclass
class AgentConfig:
    """Configuration for GPU Rig LLM agents"""
    rig_ip: str = "192.168.1.150"
    rig_port: int = 8100
    temperature: float = 0.1  # Low temp for factual extraction
    max_tokens: int = 2048
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0

    @property
    def api_url(self) -> str:
        return f"http://{self.rig_ip}:{self.rig_port}/query"


class BaseAgent:
    """Base class for all agents in the system - uses GPU Rig"""

    def __init__(self, name: str, config: AgentConfig):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"Agent.{name}")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60)
    )
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call GPU Rig LLM with exponential backoff retry logic"""
        try:
            # Mistral format: combine system and user prompts
            full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"

            response = requests.post(
                self.config.api_url,
                json={
                    "prompt": full_prompt,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                },
                timeout=120  # 2 minute timeout for GPU processing
            )
            response.raise_for_status()

            result = response.json()
            # GPU rig returns {"response": "...", "tokens": ...}
            return result['response'].strip()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"GPU Rig API call failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise

    def _call_llm_json(self, prompt: str, system_prompt: str = "") -> Dict:
        """Call LLM and expect JSON response"""
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nReturn ONLY a valid JSON object with quoted string values. Do not include any other text."

        response_text = self._call_llm(json_prompt, system_prompt)

        try:
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            elif "{" in response_text:
                # Find first { and last }
                start = response_text.index("{")
                end = response_text.rindex("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text.strip()

            # Fix unquoted NR values
            json_str = json_str.replace(': NR,', ': "NR",').replace(': NR}', ': "NR"}')

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}\nResponse: {response_text}")
            # Return default structure with NR values
            return self._get_default_response()
        except Exception as e:
            self.logger.error(f"Unexpected error parsing response: {e}")
            return self._get_default_response()

    def _get_default_response(self) -> Dict:
        """Return default response with NR values"""
        return {}


# ============================================================================
# PDF LOADER AGENT
# ============================================================================

class PDFLoaderAgent(BaseAgent):
    """Agent responsible for loading and chunking PDF documents"""

    def __init__(self, config: AgentConfig):
        super().__init__("PDFLoader", config)

    def extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            self.logger.info(f"Extracted {len(text)} characters from {pdf_path.name}")
            return text
        except Exception as e:
            self.logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 3000, overlap: int = 300) -> List[str]:
        """Split text into overlapping chunks for context window management"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        self.logger.info(f"Split text into {len(chunks)} chunks")
        return chunks

    def extract_metadata(self, pdf_path: Path) -> Dict[str, str]:
        """Extract basic metadata from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata or {}

                return {
                    "filename": pdf_path.name,
                    "title": metadata.get('/Title', ''),
                    "author": metadata.get('/Author', ''),
                    "creation_date": metadata.get('/CreationDate', '')
                }
        except Exception as e:
            self.logger.warning(f"Could not extract metadata: {e}")
            return {"filename": pdf_path.name}


# ============================================================================
# SPECIALIZED EXTRACTION AGENTS
# ============================================================================

class TechnicalMetadataExtractor(BaseAgent):
    """Extracts FL, PEFT, and LLM technical parameters"""

    def __init__(self, config: AgentConfig):
        super().__init__("TechnicalExtractor", config)

    def extract(self, text_chunks: List[str], codebook: str) -> Dict[str, Any]:
        """Extract technical metadata from paper text"""

        system_prompt = """You are a technical metadata extraction expert specializing in Federated Learning, Parameter-Efficient Fine-Tuning, and Large Language Models.

Extract ONLY information explicitly stated in the paper. For missing values, use "NR" (Not Reported).

Return valid JSON only."""

        # Use first 2 chunks for technical extraction
        paper_excerpt = ' '.join(text_chunks[:2])[:8000]  # Limit to ~8000 chars

        prompt = f"""Extract technical metadata from this research paper excerpt:

REQUIRED FIELDS (return as JSON):
{{
  "llm_model_name": "Exact model name (e.g., 'Llama-3-8B', 'GPT-4') or 'NR'",
  "parameter_count": "Parameters (e.g., '270M', '7B', '70B') or 'NR'",
  "slm_feasibility": "'Yes' if <1B params, 'No' if >=1B, 'NR' if unknown",
  "fl_architecture": "'Centralized', 'Decentralized', 'PEFT', or 'NR'",
  "fl_strategy": "'FedAvg', 'FedPer', 'FedRep', 'P2P', or 'NR'",
  "peft_method": "'LoRA', 'QLoRA', 'Full FT', or 'NR'",
  "privacy_mechanism": "Privacy technique (e.g., 'Differential Privacy', 'Secure Aggregation') or 'NR'"
}}

PAPER EXCERPT:
{paper_excerpt}

JSON:"""

        response = self._call_llm_json(prompt, system_prompt)

        # Ensure all required keys exist
        defaults = {
            "llm_model_name": "NR",
            "parameter_count": "NR",
            "slm_feasibility": "NR",
            "fl_architecture": "NR",
            "fl_strategy": "NR",
            "peft_method": "NR",
            "privacy_mechanism": "NR"
        }
        return {**defaults, **response}


class PedagogicalMetadataExtractor(BaseAgent):
    """Extracts CEFR alignment and language learning metadata"""

    def __init__(self, config: AgentConfig):
        super().__init__("PedagogicalExtractor", config)

    def extract(self, text_chunks: List[str], codebook: str) -> Dict[str, Any]:
        """Extract pedagogical metadata"""

        system_prompt = """You are a CEFR and language learning assessment expert.

Extract CEFR levels (A1-C2) and pedagogical focus from research papers.

Return valid JSON only."""

        paper_excerpt = ' '.join(text_chunks[:2])[:6000]

        prompt = f"""Extract pedagogical metadata from this paper excerpt:

REQUIRED FIELDS (return as JSON):
{{
  "cefr_alignment": "Explicit CEFR level (A1, A2, B1, B2, C1, C2) or 'Beginner'/'Intermediate'/'Advanced' or 'NR'",
  "skill_focus": "'Productive' (writing/speaking), 'Receptive' (listening/reading), 'Systemic' (grammar/vocab), or 'NR'",
  "cefr_dimension": "'Dimension 1' (symbolic control) or 'Dimension 2' (verification) or 'NR'"
}}

PAPER EXCERPT:
{paper_excerpt}

JSON:"""

        response = self._call_llm_json(prompt, system_prompt)

        defaults = {
            "cefr_alignment": "NR",
            "skill_focus": "NR",
            "cefr_dimension": "NR"
        }
        return {**defaults, **response}


class KGGroundingExtractor(BaseAgent):
    """Extracts Knowledge Graph and grounding mechanism metadata"""

    def __init__(self, config: AgentConfig):
        super().__init__("KGGroundingExtractor", config)

    def extract(self, text_chunks: List[str], codebook: str) -> Dict[str, Any]:
        """Extract KG and grounding metadata"""

        system_prompt = """You are an expert in Knowledge Graphs and LLM grounding mechanisms.

DEFINITIONS:
- Grounding Dimension 1 (Symbolic Control): KG constrains LLM output via grammar/vocabulary rules
- Grounding Dimension 2 (Source Verification): KG verifies factuality via RAG lookup

Return valid JSON only."""

        paper_excerpt = ' '.join(text_chunks[:3])[:8000]

        prompt = f"""Extract Knowledge Graph and grounding metadata:

REQUIRED FIELDS (return as JSON):
{{
  "kg_type": "'Ontology', 'Property Graph', 'ConceptNet', 'RAG', or 'NR'",
  "grounding_dimension_1": 1 if KG controls output (forced grammar/vocab), else 0,
  "grounding_dimension_2": 1 if KG verifies facts (RAG lookup), else 0,
  "validation_metrics": "'KGQI', 'ACI', 'HITL', or 'NR'",
  "grounding_gap_addressed": "'Yes', 'No', 'Partial', or 'NR'",
  "control_gap_addressed": "'Yes', 'No', 'Partial', or 'NR'"
}}

PAPER EXCERPT:
{paper_excerpt}

JSON:"""

        response = self._call_llm_json(prompt, system_prompt)

        defaults = {
            "kg_type": "NR",
            "grounding_dimension_1": 0,
            "grounding_dimension_2": 0,
            "validation_metrics": "NR",
            "grounding_gap_addressed": "NR",
            "control_gap_addressed": "NR"
        }
        result = {**defaults, **response}

        # Normalize kg_type if LLM returns generic "Knowledge Graph"
        if result.get("kg_type") == "Knowledge Graph":
            result["kg_type"] = "NR"

        return result


# ============================================================================
# ORCHESTRATOR AGENT
# ============================================================================

class OrchestratorAgent(BaseAgent):
    """Main coordinator for the extraction pipeline"""

    def __init__(self, config: AgentConfig, codebook_text: str):
        super().__init__("Orchestrator", config)
        self.codebook = codebook_text

        # Initialize sub-agents
        self.pdf_loader = PDFLoaderAgent(config)
        self.tech_extractor = TechnicalMetadataExtractor(config)
        self.pedagogy_extractor = PedagogicalMetadataExtractor(config)
        self.kg_extractor = KGGroundingExtractor(config)

    def process_single_paper(self, pdf_path: Path, study_id: str) -> ExtractedMetadata:
        """Process a single PDF and extract all metadata"""
        self.logger.info(f"Processing {pdf_path.name}...")

        # Step 1: Load PDF
        text = self.pdf_loader.extract_text(pdf_path)
        chunks = self.pdf_loader.chunk_text(text)
        pdf_meta = self.pdf_loader.extract_metadata(pdf_path)

        # Step 2: Parallel extraction (sequential for now, could use threading)
        self.logger.info("Extracting technical metadata...")
        tech_data = self.tech_extractor.extract(chunks, self.codebook)

        self.logger.info("Extracting pedagogical metadata...")
        pedagogy_data = self.pedagogy_extractor.extract(chunks, self.codebook)

        self.logger.info("Extracting KG/grounding metadata...")
        kg_data = self.kg_extractor.extract(chunks, self.codebook)

        # Step 3: Merge all extracted data
        merged_data = {
            "study_id": study_id,
            "author": pdf_meta.get("author", "NR") or "NR",
            "year": self._extract_year(pdf_meta, text),
            "title": pdf_meta.get("title", pdf_path.stem) or pdf_path.stem,
            **tech_data,
            **pedagogy_data,
            **kg_data
        }

        # Step 4: Validate and create structured output
        try:
            metadata = ExtractedMetadata(**merged_data)
            metadata.confidence_score = self._calculate_confidence(merged_data)
            return metadata
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self.logger.error(f"Merged data: {merged_data}")
            raise

    def _extract_year(self, pdf_meta: Dict, text: str) -> int:
        """Extract publication year from metadata or text"""
        # Try PDF metadata first
        date_str = pdf_meta.get("creation_date", "")
        if date_str and len(date_str) >= 4:
            try:
                return int(date_str[:4])
            except ValueError:
                pass

        # Fallback: search text for common year patterns
        import re
        years = re.findall(r'20[012]\d', text[:2000])
        if years:
            return int(years[0])

        return 0  # Will need manual review

    def _calculate_confidence(self, data: Dict) -> float:
        """Calculate confidence score based on NR count"""
        nr_count = sum(1 for v in data.values() if v == "NR" or v == 0)
        total_fields = len(data) - 3  # Exclude study_id, confidence_score, extraction_notes
        return max(0.0, 1.0 - (nr_count / total_fields))

    def process_batch(
        self,
        pdf_dir: Path,
        output_csv: Path,
        start_idx: int = 1,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Process all PDFs in directory and generate CSV"""

        pdf_files = sorted(list(pdf_dir.glob("*.pdf")))
        if limit:
            pdf_files = pdf_files[:limit]

        self.logger.info(f"Found {len(pdf_files)} PDFs to process")
        self.logger.info(f"Using GPU Rig at {self.config.rig_ip}:{self.config.rig_port}")

        results = []
        for idx, pdf_path in enumerate(pdf_files, start=start_idx):
            study_id = f"STUDY_{idx:03d}"

            try:
                metadata = self.process_single_paper(pdf_path, study_id)
                results.append(metadata.model_dump())
                self.logger.info(f"✓ Completed {study_id} - Confidence: {metadata.confidence_score:.2f}")
            except Exception as e:
                self.logger.error(f"✗ Failed {study_id}: {e}")
                # Add minimal entry with NR values
                results.append({
                    "study_id": study_id,
                    "title": pdf_path.stem,
                    "author": "NR",
                    "year": 0,
                    "llm_model_name": "NR",
                    "parameter_count": "NR",
                    "slm_feasibility": "NR",
                    "fl_architecture": "NR",
                    "kg_type": "NR",
                    "cefr_alignment": "NR",
                    "privacy_mechanism": "NR",
                    "validation_metrics": "NR",
                    "grounding_dimension_1": 0,
                    "grounding_dimension_2": 0,
                    "grounding_gap_addressed": "NR",
                    "control_gap_addressed": "NR",
                    "confidence_score": 0.0,
                    "extraction_notes": f"FAILED: {str(e)}"
                })

            # Small delay to avoid overwhelming GPU rig
            time.sleep(1.0)

        # Convert to DataFrame
        df = pd.DataFrame(results)

        # Reorder columns to match template
        template_columns = [
            "study_id", "author", "year", "title",
            "llm_model_name", "parameter_count", "slm_feasibility",
            "fl_architecture", "kg_type", "cefr_alignment",
            "privacy_mechanism", "validation_metrics",
            "grounding_gap_addressed", "control_gap_addressed",
            "confidence_score", "extraction_notes"
        ]

        df = df.reindex(columns=template_columns, fill_value="NR")

        # Save to CSV
        df.to_csv(output_csv, index=False)
        self.logger.info(f"Saved results to {output_csv}")

        return df


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""

    # Configuration - uses your existing GPU rig
    # Port 8000 = Qwen 2.5 7B (Best for technical extraction)
    config = AgentConfig(
        rig_ip="192.168.1.150",
        rig_port=8000,
        temperature=0.1,
        max_tokens=2048
    )

    # Paths
    base_dir = Path(__file__).parent
    pdf_dir = base_dir.parent / "Journal References"

    # Read codebook as text (use the markdown version for now)
    codebook_text = """
Codebook for Data Extraction:
- FL_Strategy: FedAvg, FedPer, FedRep, P2P, NR
- PEFT_Method: LoRA, QLoRA, Full FT, NR
- KG_Type: Ontology, Property Graph, ConceptNet, RAG, NR
- Grounding_Dimension_1: 1 if symbolic control, 0 otherwise
- Grounding_Dimension_2: 1 if source verification, 0 otherwise
"""

    output_csv = base_dir / "Data_Extraction_Results_v1.csv"

    # Test GPU rig connection first
    logger.info("Testing GPU rig connection...")
    try:
        response = requests.post(
            f"http://{config.rig_ip}:{config.rig_port}/query",
            json={"prompt": "test", "max_tokens": 5, "temperature": 0.1},
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"✓ GPU rig responding on port {config.rig_port}")
        else:
            raise Exception(f"Got status code {response.status_code}")
    except Exception as e:
        logger.error(f"✗ Cannot connect to GPU rig at {config.rig_ip}:{config.rig_port}")
        logger.error(f"Error: {e}")
        logger.error("Make sure the inference server is running on the GPU rig.")
        return

    # Create orchestrator
    orchestrator = OrchestratorAgent(config, codebook_text)

    # Process all PDFs
    logger.info("\n" + "="*60)
    logger.info("Starting Stage 1: Technical Evidence Audit")
    logger.info(f"Using GPU Rig: {config.rig_ip}:{config.rig_port} (Mistral-7B)")
    logger.info("="*60 + "\n")

    df = orchestrator.process_batch(
        pdf_dir=pdf_dir,
        output_csv=output_csv,
        start_idx=1,
        limit=None  # Process all 52 papers (set to 5 for testing)
    )

    # Summary statistics
    logger.info("\n" + "="*60)
    logger.info("EXTRACTION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total papers processed: {len(df)}")
    logger.info(f"Average confidence: {df['confidence_score'].mean():.2f}")
    logger.info(f"Papers needing manual review (conf < 0.5): {(df['confidence_score'] < 0.5).sum()}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
