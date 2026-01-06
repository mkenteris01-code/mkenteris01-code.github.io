"""
Hybrid search combining semantic and keyword search.
"""

from typing import List, Dict, Any

from core import Neo4jClient
from embeddings import EmbeddingGenerator
from .semantic_search import SemanticSearch
from .keyword_search import KeywordSearch


class HybridSearch:
    """Combines semantic and keyword search with weighted scoring."""

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        embedding_generator: EmbeddingGenerator,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ):
        """
        Initialize hybrid search.

        Args:
            neo4j_client: Neo4j client
            embedding_generator: Embedding generator
            semantic_weight: Weight for semantic search (0.0-1.0)
            keyword_weight: Weight for keyword search (0.0-1.0)
        """
        self.semantic_search = SemanticSearch(neo4j_client, embedding_generator)
        self.keyword_search = KeywordSearch(neo4j_client)
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight

    def search_chunks(self, query: str, k: int = 10, only_latest: bool = True) -> List[Dict[str, Any]]:
        """
        Hybrid search for chunks.

        Args:
            query: Search query
            k: Number of results
            only_latest: If True, only search latest (non-superseded) documents (default: True)

        Returns:
            Combined and reranked results
        """
        # Get semantic results
        semantic_results = self.semantic_search.search_chunks(query, k=k*2, only_latest=only_latest)

        # Get keyword results
        keyword_results = self.keyword_search.search_chunks(query, k=k*2, only_latest=only_latest)

        # Combine and rerank
        combined = self._combine_results(semantic_results, keyword_results)

        # Sort by hybrid score (primary) and ingestion_date (secondary - most recent first)
        combined.sort(key=lambda x: (x.get('hybrid_score', 0), x.get('ingestion_date', '')), reverse=True)
        return combined[:k]

    def _combine_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and rerank results from both searches."""
        # Create score dictionaries
        semantic_scores = {
            r['chunk_id']: r['score']
            for r in semantic_results
            if 'chunk_id' in r
        }
        keyword_scores = {
            r['chunk_id']: r['score']
            for r in keyword_results
            if 'chunk_id' in r
        }

        # Get all unique chunk IDs
        all_chunk_ids = set(semantic_scores.keys()) | set(keyword_scores.keys())

        # Combine scores
        combined = []
        for chunk_id in all_chunk_ids:
            semantic_score = semantic_scores.get(chunk_id, 0.0)
            keyword_score = keyword_scores.get(chunk_id, 0.0)

            hybrid_score = (
                self.semantic_weight * semantic_score +
                self.keyword_weight * keyword_score
            )

            # Find the result data (prefer semantic)
            result_data = None
            for r in semantic_results:
                if r.get('chunk_id') == chunk_id:
                    result_data = r
                    break
            if not result_data:
                for r in keyword_results:
                    if r.get('chunk_id') == chunk_id:
                        result_data = r
                        break

            if result_data:
                result_data['hybrid_score'] = hybrid_score
                result_data['semantic_score'] = semantic_score
                result_data['keyword_score'] = keyword_score
                combined.append(result_data)

        return combined
