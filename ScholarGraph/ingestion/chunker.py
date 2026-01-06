"""
Text chunking for ScholarGraph document ingestion.

Splits documents into overlapping chunks for embedding and retrieval.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from config import get_settings


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    content: str
    position: int
    start_char: int
    end_char: int
    word_count: int
    char_count: int


class TextChunker:
    """
    Chunks text documents into overlapping segments.

    Uses word-based chunking with configurable size and overlap.
    """

    def __init__(
        self,
        chunk_size_words: int | None = None,
        chunk_overlap_words: int | None = None
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size_words: Size of each chunk in words (default from settings)
            chunk_overlap_words: Overlap between chunks in words (default from settings)
        """
        settings = get_settings()

        self.chunk_size = chunk_size_words or settings.chunk_size_words
        self.chunk_overlap = chunk_overlap_words or settings.chunk_overlap_words

        # Validate parameters
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )

    def chunk_text(self, text: str) -> List[Chunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk

        Returns:
            List of Chunk objects

        Algorithm:
            1. Split text into words
            2. Create chunks of chunk_size words
            3. Overlap by chunk_overlap words between consecutive chunks
            4. Track character positions for each chunk
        """
        if not text.strip():
            return []

        # Split into words while preserving whitespace information
        words = text.split()

        if len(words) <= self.chunk_size:
            # Text is smaller than chunk size, return as single chunk
            return [
                Chunk(
                    content=text,
                    position=0,
                    start_char=0,
                    end_char=len(text),
                    word_count=len(words),
                    char_count=len(text)
                )
            ]

        chunks = []
        position = 0
        current_word_index = 0

        while current_word_index < len(words):
            # Get chunk words
            chunk_words = words[current_word_index:current_word_index + self.chunk_size]

            # Reconstruct chunk text
            chunk_text = " ".join(chunk_words)

            # Calculate character positions in original text
            # Find start character
            start_char = self._find_char_position(text, chunk_words[0], current_word_index)

            # Find end character
            end_char = start_char + len(chunk_text)

            # Create chunk
            chunks.append(
                Chunk(
                    content=chunk_text,
                    position=position,
                    start_char=start_char,
                    end_char=end_char,
                    word_count=len(chunk_words),
                    char_count=len(chunk_text)
                )
            )

            # Move to next chunk position with overlap
            current_word_index += (self.chunk_size - self.chunk_overlap)
            position += 1

        return chunks

    def chunk_text_smart(self, text: str, prefer_paragraph_breaks: bool = True) -> List[Chunk]:
        """
        Smart chunking that attempts to break at paragraph boundaries.

        Args:
            text: Input text
            prefer_paragraph_breaks: Whether to prefer breaking at paragraph boundaries

        Returns:
            List of Chunk objects
        """
        if not prefer_paragraph_breaks:
            return self.chunk_text(text)

        # Split text into paragraphs
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk_words = []
        current_chunk_start = 0
        position = 0

        for para_idx, paragraph in enumerate(paragraphs):
            para_words = paragraph.split()

            # If adding this paragraph would exceed chunk size, create a chunk
            if len(current_chunk_words) + len(para_words) > self.chunk_size and current_chunk_words:
                # Create chunk from accumulated paragraphs
                chunk_text = " ".join(current_chunk_words)
                start_char = self._find_char_position(text, current_chunk_words[0], 0)
                end_char = start_char + len(chunk_text)

                chunks.append(
                    Chunk(
                        content=chunk_text,
                        position=position,
                        start_char=start_char,
                        end_char=end_char,
                        word_count=len(current_chunk_words),
                        char_count=len(chunk_text)
                    )
                )

                # Start new chunk with overlap
                # Keep last chunk_overlap words
                overlap_start = max(0, len(current_chunk_words) - self.chunk_overlap)
                current_chunk_words = current_chunk_words[overlap_start:]
                position += 1

            # Add current paragraph to chunk
            current_chunk_words.extend(para_words)

        # Create final chunk if there are remaining words
        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            start_char = self._find_char_position(text, current_chunk_words[0], 0)
            end_char = start_char + len(chunk_text)

            chunks.append(
                Chunk(
                    content=chunk_text,
                    position=position,
                    start_char=start_char,
                    end_char=end_char,
                    word_count=len(current_chunk_words),
                    char_count=len(chunk_text)
                )
            )

        return chunks if chunks else self.chunk_text(text)

    def _find_char_position(self, text: str, target_word: str, word_index: int) -> int:
        """
        Find character position of a word in text.

        Args:
            text: Full text
            target_word: Word to find
            word_index: Approximate word index

        Returns:
            Character position
        """
        # Simple approach: use word index to estimate position
        words_before = text.split()[:word_index]
        # Rough estimate: words + spaces
        return sum(len(w) + 1 for w in words_before)

    def get_chunk_statistics(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """
        Calculate statistics for a list of chunks.

        Args:
            chunks: List of Chunk objects

        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_words": 0,
                "avg_chars": 0,
                "min_words": 0,
                "max_words": 0
            }

        word_counts = [c.word_count for c in chunks]
        char_counts = [c.char_count for c in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_words": sum(word_counts) / len(word_counts),
            "avg_chars": sum(char_counts) / len(char_counts),
            "min_words": min(word_counts),
            "max_words": max(word_counts),
            "min_chars": min(char_counts),
            "max_chars": max(char_counts),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }


if __name__ == "__main__":
    # Test chunker
    test_text = """
    This is the first paragraph with some content. It contains multiple sentences
    to test the chunking algorithm.

    This is the second paragraph. It also has some content that will be chunked.
    The chunker should handle this properly.

    This is the third paragraph with more test content. We want to ensure that
    the chunker creates appropriate overlapping chunks.

    Fourth paragraph here. More content for testing purposes. The chunker should
    create chunks that respect paragraph boundaries when possible.

    Fifth and final paragraph. This completes our test document for the chunking
    algorithm verification.
    """

    # Test with default settings
    print("Testing TextChunker with default settings...")
    chunker = TextChunker(chunk_size_words=50, chunk_overlap_words=10)

    # Regular chunking
    print("\n1. Regular chunking:")
    chunks = chunker.chunk_text(test_text)
    for chunk in chunks:
        print(f"\nChunk {chunk.position}:")
        print(f"  Words: {chunk.word_count}, Chars: {chunk.char_count}")
        print(f"  Position: {chunk.start_char}-{chunk.end_char}")
        print(f"  Content preview: {chunk.content[:100]}...")

    # Statistics
    stats = chunker.get_chunk_statistics(chunks)
    print(f"\nChunk Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Smart chunking
    print("\n2. Smart chunking (paragraph-aware):")
    smart_chunks = chunker.chunk_text_smart(test_text)
    for chunk in smart_chunks:
        print(f"\nChunk {chunk.position}:")
        print(f"  Words: {chunk.word_count}")
        print(f"  Content preview: {chunk.content[:100]}...")
