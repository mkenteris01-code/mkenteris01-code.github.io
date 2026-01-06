"""
Common Cypher query templates for ScholarGraph.

Provides reusable queries for:
- Finding documents and chunks
- Searching by content
- Traversing relationships
- Aggregating statistics
"""

from typing import List, Dict, Any, Optional
from core import Neo4jClient


class QueryTemplates:
    """Collection of common Cypher query templates."""

    # Document queries
    FIND_DOCUMENT_BY_TITLE = """
    MATCH (d:Document)
    WHERE toLower(d.title) CONTAINS toLower($title)
    RETURN d
    ORDER BY d.date DESC
    """

    FIND_DOCUMENTS_BY_TYPE = """
    MATCH (d:Document {document_type: $document_type})
    RETURN d
    ORDER BY d.date DESC
    LIMIT $limit
    """

    FIND_DOCUMENTS_BY_DATE_RANGE = """
    MATCH (d:Document)
    WHERE d.date >= $start_date AND d.date <= $end_date
    RETURN d
    ORDER BY d.date DESC
    """

    # Chunk queries
    GET_CHUNKS_WITH_CONTEXT = """
    MATCH (d:Document {document_id: $document_id})-[:CONTAINS]->(c:Chunk {chunk_id: $chunk_id})
    OPTIONAL MATCH (c)<-[:NEXT_CHUNK]-(prev:Chunk)
    OPTIONAL MATCH (c)-[:NEXT_CHUNK]->(next:Chunk)
    RETURN d, c, prev, next
    """

    FIND_CHUNKS_BY_CONTENT = """
    CALL db.index.fulltext.queryNodes('chunk_content_fulltext', $query)
    YIELD node AS c, score
    MATCH (d:Document)-[:CONTAINS]->(c)
    RETURN c, d, score
    ORDER BY score DESC
    LIMIT $limit
    """

    # Topic queries
    GET_DOCUMENTS_BY_TOPIC = """
    MATCH (d:Document)-[r:DISCUSSES_TOPIC]->(t:Topic {name: $topic_name})
    RETURN d, r.confidence AS confidence
    ORDER BY r.confidence DESC, r.mentions DESC
    """

    GET_TOPICS_BY_DOCUMENT = """
    MATCH (d:Document {document_id: $document_id})-[r:DISCUSSES_TOPIC]->(t:Topic)
    RETURN t.name AS topic, t.category AS category,
           r.confidence AS confidence, r.mentions AS mentions
    ORDER BY r.confidence DESC
    """

    FIND_RELATED_TOPICS = """
    MATCH (t1:Topic {name: $topic_name})<-[:DISCUSSES_TOPIC]-(d:Document)-[:DISCUSSES_TOPIC]->(t2:Topic)
    WHERE t1 <> t2
    WITH t2, count(DISTINCT d) AS shared_documents
    RETURN t2.name AS related_topic, shared_documents
    ORDER BY shared_documents DESC
    LIMIT $limit
    """

    # Citation/Reference queries
    GET_CITATIONS = """
    MATCH (d1:Document {document_id: $document_id})-[r:REFERENCES]->(d2:Document)
    RETURN d2, r.citation_context AS context
    """

    GET_CITED_BY = """
    MATCH (d1:Document)-[r:REFERENCES]->(d2:Document {document_id: $document_id})
    RETURN d1, r.citation_context AS context
    """

    # Traversal queries
    FIND_RELATED_DOCUMENTS = """
    MATCH path = (d1:Document {document_id: $document_id})-[*1..$max_depth]-(d2:Document)
    WHERE d1 <> d2
    WITH d2, min(length(path)) AS distance
    RETURN d2.document_id AS document_id,
           d2.title AS title,
           distance
    ORDER BY distance, d2.date DESC
    LIMIT $limit
    """

    # Statistics queries
    COUNT_NODES_BY_LABEL = """
    MATCH (n)
    WITH labels(n) AS labels
    UNWIND labels AS label
    RETURN label, count(*) AS count
    ORDER BY count DESC
    """

    COUNT_RELATIONSHIPS = """
    MATCH ()-[r]->()
    RETURN type(r) AS relationship_type, count(r) AS count
    ORDER BY count DESC
    """

    GET_DOCUMENT_STATS = """
    MATCH (d:Document)
    RETURN count(d) AS total_documents,
           collect(DISTINCT d.document_type) AS document_types,
           min(d.date) AS earliest_date,
           max(d.date) AS latest_date
    """

    GET_CHUNK_STATS = """
    MATCH (c:Chunk)
    RETURN count(c) AS total_chunks,
           avg(c.word_count) AS avg_words,
           min(c.word_count) AS min_words,
           max(c.word_count) AS max_words
    """


class QueryExecutor:
    """Helper class for executing common queries."""

    def __init__(self, client: Neo4jClient):
        """
        Initialize query executor.

        Args:
            client: Neo4jClient instance
        """
        self.client = client
        self.templates = QueryTemplates()

    def find_documents_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Find documents by title substring match."""
        results = self.client.execute_read(
            self.templates.FIND_DOCUMENT_BY_TITLE,
            parameters={"title": title}
        )
        return [dict(r['d']) for r in results]

    def find_documents_by_type(
        self,
        document_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Find documents by type."""
        results = self.client.execute_read(
            self.templates.FIND_DOCUMENTS_BY_TYPE,
            parameters={"document_type": document_type, "limit": limit}
        )
        return [dict(r['d']) for r in results]

    def get_chunks_with_context(
        self,
        document_id: str,
        chunk_id: str
    ) -> Dict[str, Any]:
        """Get a chunk with its previous and next chunks."""
        results = self.client.execute_read(
            self.templates.GET_CHUNKS_WITH_CONTEXT,
            parameters={"document_id": document_id, "chunk_id": chunk_id}
        )

        if results:
            result = results[0]
            return {
                "document": dict(result.get('d', {})),
                "chunk": dict(result.get('c', {})),
                "previous": dict(result.get('prev', {})) if result.get('prev') else None,
                "next": dict(result.get('next', {})) if result.get('next') else None,
            }
        return {}

    def find_chunks_by_content(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Full-text search for chunks."""
        results = self.client.execute_read(
            self.templates.FIND_CHUNKS_BY_CONTENT,
            parameters={"query": query, "limit": limit}
        )

        return [
            {
                "chunk": dict(r['c']),
                "document": dict(r['d']),
                "score": r['score']
            }
            for r in results
        ]

    def get_documents_by_topic(self, topic_name: str) -> List[Dict[str, Any]]:
        """Get all documents discussing a topic."""
        results = self.client.execute_read(
            self.templates.GET_DOCUMENTS_BY_TOPIC,
            parameters={"topic_name": topic_name}
        )

        return [
            {
                "document": dict(r['d']),
                "confidence": r['confidence']
            }
            for r in results
        ]

    def get_topics_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all topics discussed in a document."""
        return self.client.execute_read(
            self.templates.GET_TOPICS_BY_DOCUMENT,
            parameters={"document_id": document_id}
        )

    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        # Node counts
        node_results = self.client.execute_read(self.templates.COUNT_NODES_BY_LABEL)
        nodes = {r['label']: r['count'] for r in node_results}

        # Relationship counts
        rel_results = self.client.execute_read(self.templates.COUNT_RELATIONSHIPS)
        relationships = {r['relationship_type']: r['count'] for r in rel_results}

        # Document stats
        doc_stats = self.client.execute_read(self.templates.GET_DOCUMENT_STATS)
        document_stats = doc_stats[0] if doc_stats else {}

        # Chunk stats
        chunk_stats = self.client.execute_read(self.templates.GET_CHUNK_STATS)
        chunk_statistics = chunk_stats[0] if chunk_stats else {}

        return {
            "nodes": nodes,
            "relationships": relationships,
            "documents": document_stats,
            "chunks": chunk_statistics
        }


if __name__ == "__main__":
    # Test query executor
    from core import Neo4jClient

    print("Testing query executor...")

    with Neo4jClient() as client:
        executor = QueryExecutor(client)

        # Get statistics
        stats = executor.get_database_statistics()
        print(f"\nDatabase Statistics:")
        print(f"Nodes: {stats['nodes']}")
        print(f"Relationships: {stats['relationships']}")
        print(f"Documents: {stats.get('documents', {})}")
        print(f"Chunks: {stats.get('chunks', {})}")
