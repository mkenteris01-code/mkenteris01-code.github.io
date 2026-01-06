"""
Semantic search for ScholarGraph using vector similarity.
"""

from typing import List, Dict, Any, Optional

from core import Neo4jClient
from graph import VectorIndexManager
from embeddings import EmbeddingGenerator


class SemanticSearch:
    """
    Performs semantic search using vector embeddings.
    """

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        embedding_generator: EmbeddingGenerator
    ):
        """
        Initialize semantic search.

        Args:
            neo4j_client: Neo4j client instance
            embedding_generator: Embedding generator for query encoding
        """
        self.neo4j_client = neo4j_client
        self.embedding_generator = embedding_generator
        self.vector_manager = VectorIndexManager(neo4j_client)

    def search_chunks(
        self,
        query: str,
        k: int = 10,
        min_score: float = 0.0,
        only_latest: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for chunks.

        Args:
            query: Search query text
            k: Number of results
            min_score: Minimum similarity score
            only_latest: If True, only search latest (non-superseded) documents (default: True)

        Returns:
            List of chunks with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)

        if not query_embedding:
            print("Failed to generate query embedding")
            return []

        # Perform vector search
        results = self.vector_manager.vector_search_chunks(
            embedding=query_embedding,
            k=k,
            min_score=min_score,
            only_latest=only_latest
        )

        return results

    def search_documents(
        self,
        query: str,
        k: int = 10,
        min_score: float = 0.0,
        only_latest: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for documents.

        Args:
            query: Search query
            k: Number of results
            min_score: Minimum score
            only_latest: If True, only search latest (non-superseded) documents (default: True)

        Returns:
            List of documents with scores
        """
        query_embedding = self.embedding_generator.generate_embedding(query)

        if not query_embedding:
            return []

        results = self.vector_manager.vector_search_documents(
            embedding=query_embedding,
            k=k,
            min_score=min_score,
            only_latest=only_latest
        )

        return results


if __name__ == "__main__":
    # Test semantic search
    from core import Neo4jClient
    from embeddings import EmbeddingGenerator

    with Neo4jClient() as client:
        generator = EmbeddingGenerator()
        search = SemanticSearch(client, generator)

        results = search.search_chunks("federated learning", k=5)
        print(f"Found {len(results)} results")
        for r in results:
            print(f"  - {r.get('content', '')[:100]}... (score: {r.get('score', 0)})")
