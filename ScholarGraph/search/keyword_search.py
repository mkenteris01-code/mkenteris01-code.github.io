"""
Keyword-based full-text search for ScholarGraph.
"""

from typing import List, Dict, Any
from core import Neo4jClient


class KeywordSearch:
    """Performs full-text keyword search."""

    def __init__(self, neo4j_client: Neo4jClient):
        """Initialize keyword search."""
        self.neo4j_client = neo4j_client

    def search_chunks(self, query: str, k: int = 10, only_latest: bool = True) -> List[Dict[str, Any]]:
        """
        Full-text search for chunks.

        Args:
            query: Search query
            k: Number of results
            only_latest: If True, only search latest (non-superseded) documents (default: True)

        Returns:
            List of chunks with scores (sorted by relevance then date DESC)
        """
        cypher_query = """
        CALL db.index.fulltext.queryNodes('chunk_content_fulltext', $query)
        YIELD node AS c, score
        MATCH (d:Document)-[:CONTAINS]->(c)
        WHERE $only_latest IS NULL OR d.is_latest = true OR d.is_latest IS NULL
        RETURN c.chunk_id AS chunk_id,
               c.content AS content,
               d.document_id AS document_id,
               d.title AS document_title,
               d.ingestion_date AS ingestion_date,
               score
        ORDER BY score DESC, d.ingestion_date DESC
        LIMIT $k
        """

        try:
            results = self.neo4j_client.execute_read(
                cypher_query,
                parameters={"query": query, "k": k, "only_latest": only_latest}
            )
            return results
        except Exception as e:
            print(f"Keyword search failed: {e}")
            return []

    def search_documents(self, query: str, k: int = 10, only_latest: bool = True) -> List[Dict[str, Any]]:
        """Full-text search for documents (sorted by relevance then date DESC).
        
        Args:
            query: Search query
            k: Number of results
            only_latest: If True, only search latest (non-superseded) documents (default: True)
        """
        cypher_query = """
        CALL db.index.fulltext.queryNodes('document_content_fulltext', $query)
        YIELD node AS d, score
        WHERE $only_latest IS NULL OR d.is_latest = true OR d.is_latest IS NULL
        RETURN d.document_id AS document_id,
               d.title AS title,
               d.abstract AS abstract,
               d.ingestion_date AS ingestion_date,
               score
        ORDER BY score DESC, d.ingestion_date DESC
        LIMIT $k
        """

        try:
            results = self.neo4j_client.execute_read(
                cypher_query,
                parameters={"query": query, "k": k, "only_latest": only_latest}
            )
            return results
        except Exception as e:
            print(f"Document search failed: {e}")
            return []
