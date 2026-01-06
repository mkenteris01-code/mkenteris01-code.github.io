"""
Vector index operations for semantic search in ScholarGraph.

Requires Neo4j 5.13+ for native vector index support.
"""

from typing import List, Dict, Any, Optional
from core import Neo4jClient


class VectorIndexManager:
    """Manages vector index operations for semantic search."""

    def __init__(self, client: Neo4jClient):
        """
        Initialize vector index manager.

        Args:
            client: Neo4jClient instance
        """
        self.client = client

    def vector_search_chunks(
        self,
        embedding: List[float],
        k: int = 10,
        min_score: float = 0.0,
        only_latest: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for chunks using vector similarity.

        Args:
            embedding: Query embedding vector
            k: Number of results to return
            min_score: Minimum similarity score (0.0 to 1.0)
            only_latest: If True, only search latest (non-superseded) documents (default: True)

        Returns:
            List of chunks with similarity scores

        Example:
            results = manager.vector_search_chunks(
                embedding=[0.1, 0.2, ...],
                k=10,
                min_score=0.7
            )
        """
        query = """
        CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
        YIELD node AS c, score
        WHERE score >= $min_score
        MATCH (d:Document)-[:CONTAINS]->(c)
        WHERE $only_latest IS NULL OR d.is_latest = true OR d.is_latest IS NULL
        RETURN c.chunk_id AS chunk_id,
               c.content AS content,
               c.position AS position,
               c.summary AS summary,
               d.document_id AS document_id,
               d.title AS document_title,
               d.ingestion_date AS ingestion_date,
               score
        ORDER BY score DESC, d.ingestion_date DESC
        """

        try:
            results = self.client.execute_read(
                query,
                parameters={
                    "embedding": embedding,
                    "k": k,
                    "min_score": min_score,
                    "only_latest": only_latest
                }
            )
            return results

        except Exception as e:
            error_msg = str(e)
            if "vector" in error_msg.lower() or "procedure" in error_msg.lower():
                raise RuntimeError(
                    "Vector search not supported. "
                    "Requires Neo4j 5.13+ with vector index enabled. "
                    f"Error: {error_msg}"
                )
            raise

    def vector_search_documents(
        self,
        embedding: List[float],
        k: int = 10,
        min_score: float = 0.0,
        only_latest: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for documents using vector similarity.

        Args:
            embedding: Query embedding vector
            k: Number of results to return
            min_score: Minimum similarity score
            only_latest: If True, only search latest (non-superseded) documents (default: True)

        Returns:
            List of documents with similarity scores
        """
        query = """
        CALL db.index.vector.queryNodes('document_embeddings', $k, $embedding)
        YIELD node AS d, score
        WHERE score >= $min_score
        WHERE $only_latest IS NULL OR d.is_latest = true OR d.is_latest IS NULL
        RETURN d.document_id AS document_id,
               d.title AS title,
               d.abstract AS abstract,
               d.document_type AS document_type,
               d.date AS date,
               d.ingestion_date AS ingestion_date,
               score
        ORDER BY score DESC, d.ingestion_date DESC
        """

        try:
            results = self.client.execute_read(
                query,
                parameters={
                    "embedding": embedding,
                    "k": k,
                    "min_score": min_score,
                    "only_latest": only_latest
                }
            )
            return results

        except Exception as e:
            error_msg = str(e)
            if "vector" in error_msg.lower() or "not found" in error_msg.lower():
                # Document embeddings might not exist
                return []
            raise

    def hybrid_search_chunks(
        self,
        embedding: List[float],
        text_query: str,
        k: int = 10,
        vector_weight: float = 0.7,
        text_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity and full-text search.

        Args:
            embedding: Query embedding vector
            text_query: Text query for full-text search
            k: Number of results to return
            vector_weight: Weight for vector similarity (0.0 to 1.0)
            text_weight: Weight for text search (0.0 to 1.0)

        Returns:
            List of chunks with combined scores

        Note:
            vector_weight + text_weight should equal 1.0 for normalized scores
        """
        query = """
        // Vector search
        CALL db.index.vector.queryNodes('chunk_embeddings', $k * 2, $embedding)
        YIELD node AS c_vector, score AS vector_score

        // Full-text search
        WITH collect({chunk: c_vector, score: vector_score}) AS vector_results
        CALL db.index.fulltext.queryNodes('chunk_content_fulltext', $text_query)
        YIELD node AS c_text, score AS text_score

        // Combine results
        WITH vector_results, collect({chunk: c_text, score: text_score}) AS text_results
        UNWIND vector_results AS v_result
        UNWIND text_results AS t_result

        // Match when same chunk appears in both
        WITH v_result, t_result
        WHERE v_result.chunk = t_result.chunk

        // Calculate hybrid score
        WITH v_result.chunk AS c,
             ($vector_weight * v_result.score + $text_weight * t_result.score) AS hybrid_score
        MATCH (d:Document)-[:CONTAINS]->(c)

        RETURN c.chunk_id AS chunk_id,
               c.content AS content,
               c.position AS position,
               d.document_id AS document_id,
               d.title AS document_title,
               hybrid_score AS score
        ORDER BY hybrid_score DESC
        LIMIT $k
        """

        try:
            results = self.client.execute_read(
                query,
                parameters={
                    "embedding": embedding,
                    "text_query": text_query,
                    "k": k,
                    "vector_weight": vector_weight,
                    "text_weight": text_weight
                }
            )
            return results

        except Exception as e:
            # Fallback to vector-only search if hybrid fails
            print(f"Hybrid search failed, falling back to vector search: {e}")
            return self.vector_search_chunks(embedding, k)

    def add_chunk_embedding(
        self,
        chunk_id: str,
        embedding: List[float]
    ) -> bool:
        """
        Add or update embedding for a chunk.

        Args:
            chunk_id: Chunk identifier
            embedding: Embedding vector

        Returns:
            True if successful
        """
        query = """
        MATCH (c:Chunk {chunk_id: $chunk_id})
        SET c.embedding = $embedding
        RETURN c
        """

        result = self.client.execute_write(
            query,
            parameters={
                "chunk_id": chunk_id,
                "embedding": embedding
            }
        )

        return len(result) > 0

    def add_document_embedding(
        self,
        document_id: str,
        embedding: List[float]
    ) -> bool:
        """
        Add or update embedding for a document.

        Args:
            document_id: Document identifier
            embedding: Embedding vector

        Returns:
            True if successful
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        SET d.embedding = $embedding
        RETURN d
        """

        result = self.client.execute_write(
            query,
            parameters={
                "document_id": document_id,
                "embedding": embedding
            }
        )

        return len(result) > 0

    def check_vector_index_exists(self, index_name: str) -> bool:
        """
        Check if a vector index exists.

        Args:
            index_name: Name of the index

        Returns:
            True if index exists
        """
        query = "SHOW INDEXES YIELD name, type WHERE type = 'VECTOR'"

        results = self.client.execute_read(query)
        index_names = [r['name'] for r in results]

        return index_name in index_names

    def get_vector_index_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all vector indexes.

        Returns:
            List of vector index details
        """
        query = """
        SHOW INDEXES
        YIELD name, type, entityType, labelsOrTypes, properties, options
        WHERE type = 'VECTOR'
        RETURN name, entityType, labelsOrTypes, properties, options
        """

        try:
            results = self.client.execute_read(query)
            return results
        except Exception as e:
            print(f"Could not retrieve vector index info: {e}")
            return []


if __name__ == "__main__":
    # Test vector index manager
    from core import Neo4jClient

    print("Testing vector index manager...")

    with Neo4jClient() as client:
        manager = VectorIndexManager(client)

        # Check if vector indexes exist
        chunk_index_exists = manager.check_vector_index_exists('chunk_embeddings')
        doc_index_exists = manager.check_vector_index_exists('document_embeddings')

        print(f"\nChunk embeddings index exists: {chunk_index_exists}")
        print(f"Document embeddings index exists: {doc_index_exists}")

        # Get vector index info
        vector_indexes = manager.get_vector_index_info()
        print(f"\nVector indexes: {len(vector_indexes)}")
        for idx in vector_indexes:
            print(f"  - {idx['name']}: {idx['labelsOrTypes']} on {idx['properties']}")
