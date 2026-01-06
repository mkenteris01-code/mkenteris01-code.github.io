"""
Metadata extraction for ScholarGraph documents.

Extracts topics, concepts, and keywords from document text.
"""

from typing import List, Dict, Any, Optional, Set
import re
from collections import Counter


class MetadataExtractor:
    """Extracts metadata, topics, and concepts from document text."""

    def __init__(self):
        """Initialize metadata extractor."""
        # Common research topics (can be expanded)
        self.research_topics = {
            'federated learning': ['federated learning', 'fedavg', 'federated optimization', 'fl'],
            'knowledge graphs': ['knowledge graph', 'kg', 'ontology', 'semantic network'],
            'large language models': ['llm', 'large language model', 'gpt', 'bert', 'transformer'],
            'machine learning': ['machine learning', 'ml', 'deep learning', 'neural network'],
            'natural language processing': ['nlp', 'natural language processing', 'text processing'],
            'privacy': ['privacy', 'differential privacy', 'privacy-preserving', 'federated privacy'],
            'embeddings': ['embedding', 'word2vec', 'sentence embedding', 'vector representation'],
            'retrieval': ['retrieval', 'rag', 'retrieval augmented generation', 'information retrieval'],
        }

    def extract_topics(
        self,
        text: str,
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Extract research topics from text.

        Args:
            text: Document text
            min_confidence: Minimum confidence threshold

        Returns:
            List of topics with confidence scores and mention counts
        """
        text_lower = text.lower()
        topics = []

        for topic_name, keywords in self.research_topics.items():
            mentions = 0

            # Count mentions of each keyword
            for keyword in keywords:
                # Word boundary matching
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = re.findall(pattern, text_lower)
                mentions += len(matches)

            if mentions > 0:
                # Calculate confidence based on mention frequency
                # More mentions = higher confidence
                confidence = min(1.0, mentions / 10.0)

                if confidence >= min_confidence:
                    topics.append({
                        'name': topic_name,
                        'mentions': mentions,
                        'confidence': round(confidence, 2)
                    })

        # Sort by confidence and mentions
        topics.sort(key=lambda x: (x['confidence'], x['mentions']), reverse=True)

        return topics

    def extract_keywords(
        self,
        text: str,
        max_keywords: int = 20,
        min_word_length: int = 4
    ) -> List[str]:
        """
        Extract keywords from text using simple frequency analysis.

        Args:
            text: Document text
            max_keywords: Maximum number of keywords to extract
            min_word_length: Minimum word length to consider

        Returns:
            List of keywords sorted by frequency
        """
        # Remove common stop words
        stop_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
            'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which',
            'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
            'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good',
            'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now',
            'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back',
            'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well',
            'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give',
            'day', 'most', 'us', 'is', 'are', 'was', 'were', 'been', 'has',
            'had', 'does', 'did', 'may', 'should', 'such', 'each', 'using',
            'used', 'based', 'shown', 'shows', 'show', 'where', 'while'
        }

        # Extract words
        words = re.findall(r'\b[a-z]+\b', text.lower())

        # Filter words
        filtered_words = [
            word for word in words
            if len(word) >= min_word_length and word not in stop_words
        ]

        # Count frequencies
        word_freq = Counter(filtered_words)

        # Get top keywords
        keywords = [word for word, count in word_freq.most_common(max_keywords)]

        return keywords

    def extract_concepts(
        self,
        text: str,
        min_mentions: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Extract technical concepts from text.

        Identifies capitalized terms, acronyms, and technical phrases.

        Args:
            text: Document text
            min_mentions: Minimum number of mentions to include concept

        Returns:
            List of concepts with mention counts
        """
        concepts = []

        # Find acronyms (2-6 capital letters)
        acronyms = re.findall(r'\b[A-Z]{2,6}\b', text)
        acronym_counts = Counter(acronyms)

        for acronym, count in acronym_counts.items():
            if count >= min_mentions:
                concepts.append({
                    'name': acronym,
                    'type': 'acronym',
                    'mentions': count
                })

        # Find capitalized terms (potential proper nouns/concepts)
        # Match sequences like "Federated Learning" or "Knowledge Graph"
        capitalized_terms = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text)
        term_counts = Counter(capitalized_terms)

        for term, count in term_counts.items():
            if count >= min_mentions:
                concepts.append({
                    'name': term,
                    'type': 'term',
                    'mentions': count
                })

        # Sort by mentions
        concepts.sort(key=lambda x: x['mentions'], reverse=True)

        return concepts

    def extract_authors_from_text(self, text: str) -> Optional[List[str]]:
        """
        Attempt to extract author names from text.

        Looks for common author patterns in academic papers.

        Args:
            text: Document text (usually first page)

        Returns:
            List of author names or None
        """
        # Pattern: Names followed by affiliations or emails
        # This is a simple heuristic and may not work for all papers

        # Take first 2000 characters where authors are usually mentioned
        header_text = text[:2000]

        # Look for patterns like:
        # "Author Name1, Author Name2"
        # "By Author Name"

        patterns = [
            r'(?:Authors?|By):\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:,\s*[A-Z][a-z]+\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:,\s*[A-Z][a-z]+\s+[A-Z][a-z]+){1,5})\s*(?:\n|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, header_text)
            if match:
                author_string = match.group(1)
                # Split by comma and clean
                authors = [name.strip() for name in author_string.split(',')]
                return authors

        return None

    def extract_date_from_text(self, text: str) -> Optional[str]:
        """
        Attempt to extract publication date from text.

        Args:
            text: Document text

        Returns:
            Date string or None
        """
        # Take first 2000 characters
        header_text = text[:2000]

        # Look for year patterns (2000-2099)
        year_pattern = r'\b(20[0-2][0-9])\b'
        years = re.findall(year_pattern, header_text)

        if years:
            # Return the most common year (likely publication year)
            year_counts = Counter(years)
            most_common_year = year_counts.most_common(1)[0][0]
            return most_common_year

        return None

    def extract_all_metadata(
        self,
        text: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract all metadata from document text.

        Args:
            text: Document text
            title: Document title (optional)

        Returns:
            Dictionary with all extracted metadata
        """
        metadata = {}

        # Extract topics
        topics = self.extract_topics(text)
        if topics:
            metadata['topics'] = topics

        # Extract keywords
        keywords = self.extract_keywords(text)
        if keywords:
            metadata['keywords'] = keywords

        # Extract concepts
        concepts = self.extract_concepts(text)
        if concepts:
            metadata['concepts'] = concepts

        # Try to extract authors if not already provided
        authors = self.extract_authors_from_text(text)
        if authors:
            metadata['extracted_authors'] = authors

        # Try to extract date
        date = self.extract_date_from_text(text)
        if date:
            metadata['extracted_date'] = date

        return metadata


if __name__ == "__main__":
    # Test metadata extractor
    test_text = """
    Federated Learning for Knowledge Graph Embeddings

    Authors: John Smith, Jane Doe

    Abstract: This paper presents a novel approach to federated learning (FL) for
    knowledge graph (KG) embeddings. We propose FedKG, a privacy-preserving method
    that enables multiple parties to collaboratively train KG embeddings without
    sharing raw data. Our approach uses differential privacy (DP) to ensure privacy
    guarantees while maintaining model performance.

    We evaluate FedKG on three benchmark datasets and show that it achieves comparable
    performance to centralized training while preserving privacy. The method combines
    techniques from federated learning, knowledge graphs, and natural language processing.

    Published: 2025
    """

    extractor = MetadataExtractor()

    print("Testing MetadataExtractor...\n")

    # Extract topics
    topics = extractor.extract_topics(test_text)
    print(f"Topics ({len(topics)}):")
    for topic in topics:
        print(f"  - {topic['name']}: confidence={topic['confidence']}, mentions={topic['mentions']}")

    # Extract keywords
    keywords = extractor.extract_keywords(test_text, max_keywords=10)
    print(f"\nKeywords ({len(keywords)}):")
    print(f"  {', '.join(keywords)}")

    # Extract concepts
    concepts = extractor.extract_concepts(test_text)
    print(f"\nConcepts ({len(concepts)}):")
    for concept in concepts:
        print(f"  - {concept['name']} ({concept['type']}): {concept['mentions']} mentions")

    # Extract all metadata
    all_metadata = extractor.extract_all_metadata(test_text, title="Test Paper")
    print(f"\nAll Metadata:")
    for key, value in all_metadata.items():
        print(f"  {key}: {value}")
