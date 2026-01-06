"""
PDF document processing for ScholarGraph.

Extracts text and metadata from PDF files using PyPDF2.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import PyPDF2
import re
from datetime import datetime


class PDFProcessor:
    """Processes PDF documents for ingestion into knowledge graph."""

    def __init__(self):
        """Initialize PDF processor."""
        pass

    def extract_text(self, file_path: str) -> str:
        """
        Extract all text from a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text content

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF extraction fails
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            text_content = []

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)

            full_text = "\n\n".join(text_content)

            return full_text

        except Exception as e:
            raise Exception(f"Failed to extract text from {file_path}: {e}")

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with metadata (title, author, creation_date, etc.)
        """
        path = Path(file_path)

        metadata = {
            "file_name": path.name,
            "file_path": str(path.absolute()),
            "file_size": path.stat().st_size if path.exists() else 0,
            "document_type": "pdf"
        }

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                # Extract PDF metadata
                pdf_info = pdf_reader.metadata

                if pdf_info:
                    # Title
                    if pdf_info.title:
                        metadata["title"] = pdf_info.title

                    # Author
                    if pdf_info.author:
                        metadata["authors"] = [pdf_info.author]

                    # Creation date
                    if pdf_info.creation_date:
                        metadata["creation_date"] = str(pdf_info.creation_date)

                    # Subject
                    if pdf_info.subject:
                        metadata["subject"] = pdf_info.subject

                # Page count
                metadata["page_count"] = len(pdf_reader.pages)

                # If no title in metadata, try to extract from filename
                if "title" not in metadata:
                    metadata["title"] = self._extract_title_from_filename(path.name)

        except Exception as e:
            print(f"Warning: Could not extract metadata from {file_path}: {e}")
            # Provide fallback title
            metadata["title"] = self._extract_title_from_filename(path.name)

        return metadata

    def process_pdf(
        self,
        file_path: str,
        extract_abstract: bool = True
    ) -> Dict[str, Any]:
        """
        Process PDF and extract both text and metadata.

        Args:
            file_path: Path to PDF file
            extract_abstract: Whether to attempt abstract extraction

        Returns:
            Dictionary with full_text, metadata, and optional abstract
        """
        # Extract text
        full_text = self.extract_text(file_path)

        # Extract metadata
        metadata = self.extract_metadata(file_path)

        # Try to extract abstract if requested
        abstract = None
        if extract_abstract:
            abstract = self._extract_abstract(full_text)

        result = {
            "full_text": full_text,
            "metadata": metadata,
            "abstract": abstract,
            "word_count": len(full_text.split()),
            "char_count": len(full_text)
        }

        return result

    def _extract_abstract(self, text: str) -> Optional[str]:
        """
        Attempt to extract abstract from PDF text.

        Args:
            text: Full PDF text

        Returns:
            Abstract text or None
        """
        # Common abstract patterns in academic papers
        patterns = [
            r"Abstract\s*\n+(.*?)\n\n",
            r"ABSTRACT\s*\n+(.*?)\n\n",
            r"Abstract[:\-\s]+(.*?)\n\n",
            r"Summary\s*\n+(.*?)\n\n",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # Limit abstract length (typically 200-300 words)
                words = abstract.split()
                if len(words) > 500:
                    # Probably captured too much, skip this match
                    continue
                return abstract

        # Fallback: Use first 500 words as abstract if no pattern matches
        words = text.split()
        if len(words) > 50:
            return " ".join(words[:500])

        return None

    def _extract_title_from_filename(self, filename: str) -> str:
        """
        Extract a title from the PDF filename.

        Args:
            filename: PDF filename

        Returns:
            Cleaned title string
        """
        # Remove extension
        title = Path(filename).stem

        # Replace underscores and hyphens with spaces
        title = title.replace("_", " ").replace("-", " ")

        # Remove common patterns like years, IDs
        title = re.sub(r'\b\d{4}\b', '', title)  # Remove years
        title = re.sub(r'\s+', ' ', title).strip()  # Normalize whitespace

        return title

    def validate_pdf(self, file_path: str) -> bool:
        """
        Validate that a file is a readable PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            True if valid PDF
        """
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            return False

        # Check file extension
        if path.suffix.lower() != '.pdf':
            return False

        # Try to open with PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                # Check if we can read at least one page
                if len(pdf_reader.pages) > 0:
                    return True
        except Exception:
            return False

        return False


if __name__ == "__main__":
    # Test PDF processor
    import sys

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]

        processor = PDFProcessor()

        print(f"Processing PDF: {pdf_path}")

        # Validate
        if not processor.validate_pdf(pdf_path):
            print("Invalid PDF file!")
            sys.exit(1)

        # Process
        result = processor.process_pdf(pdf_path)

        print(f"\nMetadata:")
        for key, value in result['metadata'].items():
            print(f"  {key}: {value}")

        print(f"\nText Statistics:")
        print(f"  Word count: {result['word_count']}")
        print(f"  Character count: {result['char_count']}")

        if result['abstract']:
            print(f"\nAbstract ({len(result['abstract'].split())} words):")
            print(f"  {result['abstract'][:200]}...")

    else:
        print("Usage: python pdf_processor.py <path_to_pdf>")
