"""Document ingestion pipeline for ScholarGraph."""

from .pdf_processor import PDFProcessor
from .markdown_processor import MarkdownProcessor
from .chunker import TextChunker, Chunk
from .metadata_extractor import MetadataExtractor
from .batch_ingester import BatchIngester
from .supersession_detector import SupersessionDetector

__all__ = [
    "PDFProcessor",
    "MarkdownProcessor",
    "TextChunker",
    "Chunk",
    "MetadataExtractor",
    "BatchIngester",
    "SupersessionDetector",
]
