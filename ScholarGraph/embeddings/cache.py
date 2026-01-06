"""
Persistent embedding cache for ScholarGraph.

Provides disk-based caching of embeddings to avoid recomputation.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import hashlib
import pickle


class EmbeddingCache:
    """
    Persistent cache for embeddings.

    Stores embeddings on disk to avoid recomputation.
    """

    def __init__(self, cache_dir: str = "./embeddings/cache"):
        """
        Initialize embedding cache.

        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0
        }

    def get(self, text: str) -> Optional[List[float]]:
        """
        Get embedding from cache.

        Args:
            text: Input text

        Returns:
            Cached embedding or None if not found
        """
        cache_key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    embedding = pickle.load(f)
                self.stats['hits'] += 1
                return embedding
            except Exception as e:
                print(f"Cache read error: {e}")

        self.stats['misses'] += 1
        return None

    def set(self, text: str, embedding: List[float]) -> bool:
        """
        Store embedding in cache.

        Args:
            text: Input text
            embedding: Embedding vector

        Returns:
            True if successfully cached
        """
        cache_key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
            self.stats['writes'] += 1
            return True
        except Exception as e:
            print(f"Cache write error: {e}")
            return False

    def delete(self, text: str) -> bool:
        """
        Delete embedding from cache.

        Args:
            text: Input text

        Returns:
            True if deleted
        """
        cache_key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            try:
                cache_file.unlink()
                return True
            except Exception as e:
                print(f"Cache delete error: {e}")

        return False

    def clear(self) -> int:
        """
        Clear all cached embeddings.

        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                print(f"Error deleting {cache_file}: {e}")

        return count

    def get_size(self) -> int:
        """
        Get number of cached embeddings.

        Returns:
            Number of cache files
        """
        return len(list(self.cache_dir.glob("*.pkl")))

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.stats.copy()
        stats['cache_size'] = self.get_size()
        stats['hit_rate'] = (
            self.stats['hits'] / (self.stats['hits'] + self.stats['misses'])
            if (self.stats['hits'] + self.stats['misses']) > 0
            else 0.0
        )
        return stats

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.

        Args:
            text: Input text

        Returns:
            Cache key (hash)
        """
        return hashlib.sha256(text.encode()).hexdigest()


if __name__ == "__main__":
    # Test embedding cache
    print("Testing EmbeddingCache...\n")

    cache = EmbeddingCache(cache_dir="./test_cache")

    # Test data
    test_text = "This is a test sentence for caching."
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

    # Test set
    print("1. Setting cache...")
    success = cache.set(test_text, test_embedding)
    print(f"   Set successful: {success}")

    # Test get
    print("\n2. Getting from cache...")
    cached_embedding = cache.get(test_text)
    print(f"   Retrieved: {cached_embedding}")
    print(f"   Match: {cached_embedding == test_embedding}")

    # Test miss
    print("\n3. Testing cache miss...")
    miss_result = cache.get("Non-existent text")
    print(f"   Miss result: {miss_result}")

    # Statistics
    print("\n4. Statistics:")
    stats = cache.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Clean up
    print("\n5. Clearing cache...")
    deleted = cache.clear()
    print(f"   Deleted {deleted} cache files")
