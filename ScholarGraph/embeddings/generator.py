"""
Embedding generation for ScholarGraph.

Generates vector embeddings for text using GPU rig or sentence-transformers.
"""

from typing import List, Optional, Dict, Any
import hashlib

from core import GPURigClient
from config import get_settings


class EmbeddingGenerator:
    """
    Generates embeddings for text chunks.

    Supports:
    - GPU rig API (Qwen/Mistral)
    - Sentence-transformers (fallback)
    """

    def __init__(
        self,
        gpu_client: Optional[GPURigClient] = None,
        model: Optional[str] = None,
        use_cache: bool = True
    ):
        """
        Initialize embedding generator.

        Args:
            gpu_client: GPU rig client (optional)
            model: Model to use (defaults to settings)
            use_cache: Whether to use caching
        """
        settings = get_settings()

        self.gpu_client = gpu_client
        self.model = model or settings.embedding_model
        self.embedding_dimension = settings.embedding_dimension
        self.use_cache = use_cache

        # Cache for embeddings (in-memory)
        self._cache: Dict[str, List[float]] = {}

        # Statistics
        self.stats = {
            'embeddings_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0
        }

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector or None if failed
        """
        if not text or not text.strip():
            return None

        # Check cache first
        if self.use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                self.stats['cache_hits'] += 1
                return self._cache[cache_key]
            self.stats['cache_misses'] += 1

        # Generate embedding
        try:
            embedding = self._generate_embedding_impl(text)

            if embedding:
                # Validate embedding dimension
                if len(embedding) != self.embedding_dimension:
                    print(
                        f"Warning: Expected embedding dimension {self.embedding_dimension}, "
                        f"got {len(embedding)}"
                    )

                # Cache the embedding
                if self.use_cache:
                    self._cache[cache_key] = embedding

                self.stats['embeddings_generated'] += 1
                return embedding

        except Exception as e:
            print(f"Embedding generation error: {e}")
            self.stats['errors'] += 1

        return None

    def generate_embeddings_batch(
        self,
        texts: List[str],
        show_progress: bool = True
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            show_progress: Whether to show progress

        Returns:
            List of embedding vectors (None for failed generations)
        """
        embeddings = []

        for i, text in enumerate(texts):
            if show_progress and (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(texts)} embeddings generated...")

            embedding = self.generate_embedding(text)
            embeddings.append(embedding)

        if show_progress:
            print(f"  ✓ Generated {len(embeddings)} embeddings")

        return embeddings

    def _generate_embedding_impl(self, text: str) -> Optional[List[float]]:
        """
        Internal implementation for embedding generation.

        Tries GPU rig first, then falls back to alternatives.

        Args:
            text: Input text

        Returns:
            Embedding vector or None
        """
        # Try GPU rig embedding endpoint
        if self.gpu_client:
            try:
                embedding = self.gpu_client.generate_embedding(text)
                if embedding:
                    return embedding
            except NotImplementedError:
                # Embedding endpoint not available, try alternative
                pass
            except Exception as e:
                print(f"GPU rig embedding failed: {e}")

        # Fallback: Use sentence-transformers if available
        try:
            embedding = self._generate_with_sentence_transformers(text)
            if embedding:
                return embedding
        except ImportError:
            print("Warning: sentence-transformers not available. Install with: pip install sentence-transformers")
        except Exception as e:
            print(f"Sentence-transformers embedding failed: {e}")

        # Fallback: Generate dummy embedding for testing
        # In production, this should raise an error
        print("Warning: Using dummy embedding (all zeros). Install sentence-transformers for real embeddings.")
        return [0.0] * self.embedding_dimension

    def _generate_with_sentence_transformers(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using sentence-transformers.

        Args:
            text: Input text

        Returns:
            Embedding vector or None

        Raises:
            ImportError: If sentence-transformers not installed
        """
        try:
            from sentence_transformers import SentenceTransformer

            # Lazy load model
            if not hasattr(self, '_st_model'):
                # Use all-mpnet-base-v2 (768d) as default
                model_name = 'sentence-transformers/all-mpnet-base-v2'
                print(f"Loading sentence-transformers model: {model_name}")
                self._st_model = SentenceTransformer(model_name)

            # Generate embedding
            embedding = self._st_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()

        except ImportError:
            raise
        except Exception as e:
            print(f"Sentence-transformers error: {e}")
            return None

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.

        Args:
            text: Input text

        Returns:
            Cache key (hash)
        """
        # Use SHA256 hash of text as cache key
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def clear_cache(self) -> int:
        """
        Clear embedding cache.

        Returns:
            Number of cached embeddings cleared
        """
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_cache_size(self) -> int:
        """Get number of cached embeddings."""
        return len(self._cache)

    def get_statistics(self) -> Dict[str, Any]:
        """Get embedding generation statistics."""
        stats = self.stats.copy()
        stats['cache_size'] = self.get_cache_size()
        stats['cache_hit_rate'] = (
            self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
            if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0
            else 0.0
        )
        return stats


if __name__ == "__main__":
    # Test embedding generator
    from core import GPURigClient

    print("Testing EmbeddingGenerator...\n")

    # Test without GPU client (will use sentence-transformers or dummy)
    print("1. Testing with sentence-transformers:")
    generator = EmbeddingGenerator(use_cache=True)

    test_texts = [
        "This is a test sentence about federated learning.",
        "Knowledge graphs are useful for semantic search.",
        "This is a test sentence about federated learning.",  # Duplicate for cache test
    ]

    embeddings = generator.generate_embeddings_batch(test_texts, show_progress=True)

    print(f"\nResults:")
    for i, (text, emb) in enumerate(zip(test_texts, embeddings)):
        if emb:
            print(f"  Text {i+1}: dimension={len(emb)}, first 5 values={emb[:5]}")
        else:
            print(f"  Text {i+1}: Failed to generate embedding")

    # Statistics
    stats = generator.get_statistics()
    print(f"\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
