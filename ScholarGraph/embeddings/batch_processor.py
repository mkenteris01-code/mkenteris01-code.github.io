"""
Batch embedding processing for ScholarGraph.

Efficiently processes large batches of texts for embedding generation.
"""

from typing import List, Dict, Any, Optional, Tuple
import time

from core import Neo4jClient, GPURigClient
from graph import VectorIndexManager
from .generator import EmbeddingGenerator
from .cache import EmbeddingCache


class BatchEmbeddingProcessor:
    """
    Processes embeddings in batches for efficiency.

    Features:
    - Batch processing with configurable batch size
    - Persistent caching
    - Progress tracking
    - Neo4j integration for storing embeddings
    """

    def __init__(
        self,
        neo4j_client: Optional[Neo4jClient] = None,
        gpu_client: Optional[GPURigClient] = None,
        use_cache: bool = True,
        batch_size: int = 32
    ):
        """
        Initialize batch embedding processor.

        Args:
            neo4j_client: Neo4j client for storing embeddings
            gpu_client: GPU rig client for generation
            use_cache: Whether to use persistent cache
            batch_size: Number of texts to process in each batch
        """
        self.neo4j_client = neo4j_client
        self.batch_size = batch_size

        # Initialize generator and cache
        self.generator = EmbeddingGenerator(
            gpu_client=gpu_client,
            use_cache=use_cache
        )

        self.cache = EmbeddingCache() if use_cache else None

        # Vector index manager (if Neo4j client provided)
        self.vector_manager = (
            VectorIndexManager(neo4j_client)
            if neo4j_client
            else None
        )

        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'time_elapsed': 0.0
        }

    def process_chunks(
        self,
        chunk_ids: List[str],
        chunk_texts: List[str],
        store_in_neo4j: bool = True,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Process embeddings for chunks and optionally store in Neo4j.

        Args:
            chunk_ids: List of chunk IDs
            chunk_texts: List of chunk texts
            store_in_neo4j: Whether to store embeddings in Neo4j
            show_progress: Whether to show progress

        Returns:
            Dictionary with processing statistics
        """
        if len(chunk_ids) != len(chunk_texts):
            raise ValueError("chunk_ids and chunk_texts must have same length")

        if show_progress:
            print(f"\nProcessing {len(chunk_texts)} chunk embeddings...")

        start_time = time.time()

        # Process in batches
        for i in range(0, len(chunk_texts), self.batch_size):
            batch_ids = chunk_ids[i:i + self.batch_size]
            batch_texts = chunk_texts[i:i + self.batch_size]

            if show_progress:
                print(f"  Batch {i // self.batch_size + 1}: Processing {len(batch_texts)} chunks...")

            # Generate embeddings for batch
            for chunk_id, text in zip(batch_ids, batch_texts):
                # Try cache first
                embedding = None
                if self.cache:
                    embedding = self.cache.get(text)
                    if embedding:
                        self.stats['cached'] += 1

                # Generate if not cached
                if not embedding:
                    embedding = self.generator.generate_embedding(text)

                # Store in cache
                if embedding and self.cache:
                    self.cache.set(text, embedding)

                # Store in Neo4j
                if embedding and store_in_neo4j and self.vector_manager:
                    success = self.vector_manager.add_chunk_embedding(
                        chunk_id=chunk_id,
                        embedding=embedding
                    )
                    if success:
                        self.stats['successful'] += 1
                    else:
                        self.stats['failed'] += 1
                else:
                    if embedding:
                        self.stats['successful'] += 1
                    else:
                        self.stats['failed'] += 1

                self.stats['total_processed'] += 1

        elapsed = time.time() - start_time
        self.stats['time_elapsed'] = elapsed

        if show_progress:
            print(f"\n  ✓ Completed in {elapsed:.2f} seconds")
            print(f"  Success rate: {self.stats['successful']}/{self.stats['total_processed']}")

        return self.get_statistics()

    def process_documents(
        self,
        document_ids: List[str],
        document_texts: List[str],
        store_in_neo4j: bool = True,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Process embeddings for documents.

        Args:
            document_ids: List of document IDs
            document_texts: List of document texts (abstracts or full text)
            store_in_neo4j: Whether to store in Neo4j
            show_progress: Whether to show progress

        Returns:
            Dictionary with processing statistics
        """
        if len(document_ids) != len(document_texts):
            raise ValueError("document_ids and document_texts must have same length")

        if show_progress:
            print(f"\nProcessing {len(document_texts)} document embeddings...")

        start_time = time.time()

        for i, (doc_id, text) in enumerate(zip(document_ids, document_texts)):
            if show_progress and (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(document_texts)}")

            # Try cache
            embedding = None
            if self.cache:
                embedding = self.cache.get(text)
                if embedding:
                    self.stats['cached'] += 1

            # Generate if not cached
            if not embedding:
                embedding = self.generator.generate_embedding(text)

            # Store in cache
            if embedding and self.cache:
                self.cache.set(text, embedding)

            # Store in Neo4j
            if embedding and store_in_neo4j and self.vector_manager:
                success = self.vector_manager.add_document_embedding(
                    document_id=doc_id,
                    embedding=embedding
                )
                if success:
                    self.stats['successful'] += 1
                else:
                    self.stats['failed'] += 1
            else:
                if embedding:
                    self.stats['successful'] += 1
                else:
                    self.stats['failed'] += 1

            self.stats['total_processed'] += 1

        elapsed = time.time() - start_time
        self.stats['time_elapsed'] = elapsed

        if show_progress:
            print(f"\n  ✓ Completed in {elapsed:.2f} seconds")

        return self.get_statistics()

    def backfill_embeddings(
        self,
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Backfill embeddings for chunks that don't have them.

        Finds all chunks in Neo4j without embeddings and generates them.

        Args:
            show_progress: Whether to show progress

        Returns:
            Dictionary with processing statistics
        """
        if not self.neo4j_client:
            raise ValueError("Neo4j client required for backfilling")

        if show_progress:
            print("\nBackfilling embeddings for chunks without embeddings...")

        # Find chunks without embeddings
        query = """
        MATCH (c:Chunk)
        WHERE c.embedding IS NULL
        RETURN c.chunk_id AS chunk_id, c.content AS content
        """

        chunks = self.neo4j_client.execute_read(query)

        if not chunks:
            print("  ✓ No chunks need embeddings")
            return self.get_statistics()

        chunk_ids = [c['chunk_id'] for c in chunks]
        chunk_texts = [c['content'] for c in chunks]

        if show_progress:
            print(f"  Found {len(chunks)} chunks without embeddings")

        return self.process_chunks(
            chunk_ids=chunk_ids,
            chunk_texts=chunk_texts,
            store_in_neo4j=True,
            show_progress=show_progress
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()

        # Add generator stats
        gen_stats = self.generator.get_statistics()
        stats['generator'] = gen_stats

        # Add cache stats
        if self.cache:
            cache_stats = self.cache.get_statistics()
            stats['cache'] = cache_stats

        return stats

    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'time_elapsed': 0.0
        }


if __name__ == "__main__":
    # Test batch processor
    print("Testing BatchEmbeddingProcessor...\n")

    # Test data
    test_chunk_ids = [f"chunk_{i}" for i in range(5)]
    test_chunk_texts = [
        "This is about federated learning.",
        "Knowledge graphs are useful for AI.",
        "Large language models need embeddings.",
        "Vector search enables semantic retrieval.",
        "Privacy-preserving machine learning is important."
    ]

    # Create processor (without Neo4j for testing)
    processor = BatchEmbeddingProcessor(
        neo4j_client=None,
        gpu_client=None,
        use_cache=True,
        batch_size=2
    )

    # Process chunks
    stats = processor.process_chunks(
        chunk_ids=test_chunk_ids,
        chunk_texts=test_chunk_texts,
        store_in_neo4j=False,
        show_progress=True
    )

    print(f"\nStatistics: {stats}")
