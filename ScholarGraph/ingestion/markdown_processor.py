"""
Markdown document processing for ScholarGraph.

Extracts text and metadata from Markdown files with frontmatter support.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import frontmatter
import re


class MarkdownProcessor:
    """Processes Markdown documents for ingestion into knowledge graph."""

    def __init__(self):
        """Initialize Markdown processor."""
        pass

    def extract_text(self, file_path: str) -> str:
        """
        Extract text content from a Markdown file.

        Args:
            file_path: Path to Markdown file

        Returns:
            Markdown content (without frontmatter)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        try:
            post = frontmatter.load(file_path)
            return post.content

        except Exception as e:
            # Fallback to regular file read if frontmatter parsing fails
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as read_error:
                raise Exception(f"Failed to read {file_path}: {read_error}")

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from Markdown file.

        Looks for YAML frontmatter at the beginning of the file.

        Args:
            file_path: Path to Markdown file

        Returns:
            Dictionary with metadata
        """
        path = Path(file_path)

        metadata = {
            "file_name": path.name,
            "file_path": str(path.absolute()),
            "file_size": path.stat().st_size if path.exists() else 0,
            "document_type": "markdown"
        }

        try:
            post = frontmatter.load(file_path)

            # Extract frontmatter metadata
            if post.metadata:
                # Title
                if 'title' in post.metadata:
                    metadata['title'] = post.metadata['title']

                # Author(s)
                if 'author' in post.metadata:
                    author = post.metadata['author']
                    if isinstance(author, list):
                        metadata['authors'] = author
                    else:
                        metadata['authors'] = [author]
                elif 'authors' in post.metadata:
                    metadata['authors'] = post.metadata['authors']

                # Date
                if 'date' in post.metadata:
                    metadata['date'] = str(post.metadata['date'])

                # Tags/Keywords
                if 'tags' in post.metadata:
                    metadata['keywords'] = post.metadata['tags']
                elif 'keywords' in post.metadata:
                    metadata['keywords'] = post.metadata['keywords']

                # Category
                if 'category' in post.metadata:
                    metadata['category'] = post.metadata['category']

                # Description/Abstract
                if 'description' in post.metadata:
                    metadata['description'] = post.metadata['description']
                elif 'abstract' in post.metadata:
                    metadata['abstract'] = post.metadata['abstract']

                # Custom fields - include all other frontmatter (convert to strings)
                frontmatter_dict = {}
                for key, value in post.metadata.items():
                    # Convert datetime objects to strings
                    if hasattr(value, 'isoformat'):
                        frontmatter_dict[key] = value.isoformat()
                    elif isinstance(value, (list, tuple)):
                        frontmatter_dict[key] = [str(v) for v in value]
                    else:
                        frontmatter_dict[key] = str(value) if not isinstance(value, str) else value
                metadata['frontmatter'] = frontmatter_dict

            # If no title, extract from filename or first heading
            if 'title' not in metadata:
                metadata['title'] = self._extract_title(post.content, path.name)

        except Exception as e:
            print(f"Warning: Could not extract frontmatter from {file_path}: {e}")
            metadata['title'] = self._extract_title_from_filename(path.name)

        return metadata

    def process_markdown(
        self,
        file_path: str,
        extract_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Process Markdown file and extract text and metadata.

        Args:
            file_path: Path to Markdown file
            extract_summary: Whether to extract summary from content

        Returns:
            Dictionary with content, metadata, and optional summary
        """
        # Extract text
        content = self.extract_text(file_path)

        # Extract metadata
        metadata = self.extract_metadata(file_path)

        # Extract summary if requested
        summary = None
        if extract_summary:
            summary = metadata.get('description') or metadata.get('abstract')
            if not summary:
                summary = self._extract_summary(content)

        result = {
            "content": content,
            "metadata": metadata,
            "summary": summary,
            "word_count": len(content.split()),
            "char_count": len(content)
        }

        return result

    def _extract_title(self, content: str, filename: str) -> str:
        """
        Extract title from content or filename.

        Args:
            content: Markdown content
            filename: File name

        Returns:
            Title string
        """
        # Try to find first H1 heading
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Try to find any heading
        heading_match = re.search(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

        # Fallback to filename
        return self._extract_title_from_filename(filename)

    def _extract_title_from_filename(self, filename: str) -> str:
        """
        Extract title from filename.

        Args:
            filename: Markdown filename

        Returns:
            Cleaned title
        """
        # Remove extension
        title = Path(filename).stem

        # Replace underscores and hyphens with spaces
        title = title.replace("_", " ").replace("-", " ")

        # Remove common patterns
        title = re.sub(r'\b\d{4}\b', '', title)  # Remove years
        title = re.sub(r'\s+', ' ', title).strip()  # Normalize whitespace

        return title

    def _extract_summary(self, content: str, max_words: int = 100) -> str:
        """
        Extract summary from content.

        Takes first paragraph or first N words.

        Args:
            content: Markdown content
            max_words: Maximum words in summary

        Returns:
            Summary text
        """
        # Remove markdown formatting for cleaner summary
        text = self._strip_markdown_formatting(content)

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        if paragraphs:
            # Use first substantial paragraph
            for para in paragraphs:
                words = para.split()
                if len(words) >= 10:  # At least 10 words
                    if len(words) > max_words:
                        return " ".join(words[:max_words]) + "..."
                    return para

        # Fallback: First N words
        words = text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."
        return text

    def _strip_markdown_formatting(self, markdown_text: str) -> str:
        """
        Remove Markdown formatting to get plain text.

        Args:
            markdown_text: Markdown content

        Returns:
            Plain text
        """
        text = markdown_text

        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`[^`]+`', '', text)

        # Remove headings
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)

        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        return text.strip()

    def validate_markdown(self, file_path: str) -> bool:
        """
        Validate that a file is a readable Markdown file.

        Args:
            file_path: Path to file

        Returns:
            True if valid Markdown
        """
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            return False

        # Check file extension
        if path.suffix.lower() not in ['.md', '.markdown']:
            return False

        # Try to read the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Very basic validation - file should have some content
                return len(content.strip()) > 0
        except Exception:
            return False


if __name__ == "__main__":
    # Test Markdown processor
    import sys

    if len(sys.argv) > 1:
        md_path = sys.argv[1]

        processor = MarkdownProcessor()

        print(f"Processing Markdown: {md_path}")

        # Validate
        if not processor.validate_markdown(md_path):
            print("Invalid Markdown file!")
            sys.exit(1)

        # Process
        result = processor.process_markdown(md_path)

        print(f"\nMetadata:")
        for key, value in result['metadata'].items():
            if key != 'frontmatter':  # Skip raw frontmatter dict
                print(f"  {key}: {value}")

        print(f"\nText Statistics:")
        print(f"  Word count: {result['word_count']}")
        print(f"  Character count: {result['char_count']}")

        if result['summary']:
            print(f"\nSummary:")
            print(f"  {result['summary'][:200]}...")

        print(f"\nFirst 200 characters of content:")
        print(f"  {result['content'][:200]}...")

    else:
        print("Usage: python markdown_processor.py <path_to_markdown>")
