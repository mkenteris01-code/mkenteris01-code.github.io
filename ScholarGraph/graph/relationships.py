"""
Relationship creation and management for ScholarGraph.

Relationship types:
- CONTAINS: Document -> Chunk
- NEXT_CHUNK: Chunk -> Chunk (sequential)
- DISCUSSES_TOPIC: Document/Chunk -> Topic
- REFERENCES: Document -> Document (citations)
- IMPLEMENTS: Document -> Concept (technical implementations)
- RELATED_TO: Any -> Any (generic relationship)
"""

from typing import List, Dict, Any, Optional
from core import Neo4jClient


class RelationshipManager:
    """Manages creation and retrieval of graph relationships."""

    def __init__(self, client: Neo4jClient):
        """
        Initialize relationship manager.

        Args:
            client: Neo4jClient instance
        """
        self.client = client

    def create_contains_relationship(
        self,
        document_id: str,
        chunk_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create CONTAINS relationship: Document -> Chunk.

        Args:
            document_id: Parent document ID
            chunk_id: Child chunk ID
            metadata: Additional relationship properties

        Returns:
            True if created successfully
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        MATCH (c:Chunk {chunk_id: $chunk_id})
        MERGE (d)-[r:CONTAINS]->(c)
        SET r += $properties
        RETURN r
        """

        properties = metadata or {}

        result = self.client.execute_write(
            query,
            parameters={
                "document_id": document_id,
                "chunk_id": chunk_id,
                "properties": properties
            }
        )

        return len(result) > 0

    def create_next_chunk_relationship(
        self,
        from_chunk_id: str,
        to_chunk_id: str
    ) -> bool:
        """
        Create NEXT_CHUNK relationship: Chunk -> Chunk (sequential).

        Args:
            from_chunk_id: Source chunk ID
            to_chunk_id: Target chunk ID

        Returns:
            True if created successfully
        """
        query = """
        MATCH (c1:Chunk {chunk_id: $from_chunk_id})
        MATCH (c2:Chunk {chunk_id: $to_chunk_id})
        MERGE (c1)-[r:NEXT_CHUNK]->(c2)
        RETURN r
        """

        result = self.client.execute_write(
            query,
            parameters={
                "from_chunk_id": from_chunk_id,
                "to_chunk_id": to_chunk_id
            }
        )

        return len(result) > 0

    def create_discusses_topic_relationship(
        self,
        node_id: str,
        node_label: str,
        topic_name: str,
        confidence: float = 1.0,
        mentions: int = 1
    ) -> bool:
        """
        Create DISCUSSES_TOPIC relationship: Document/Chunk -> Topic.

        Args:
            node_id: Source node ID
            node_label: Source node label (Document or Chunk)
            topic_name: Target topic name
            confidence: Confidence score (0.0 to 1.0)
            mentions: Number of topic mentions

        Returns:
            True if created successfully
        """
        # Determine ID field based on label
        id_field = "document_id" if node_label == "Document" else "chunk_id"

        query = f"""
        MATCH (n:{node_label} {{{id_field}: $node_id}})
        MERGE (t:Topic {{name: $topic_name}})
        MERGE (n)-[r:DISCUSSES_TOPIC]->(t)
        SET r.confidence = $confidence,
            r.mentions = $mentions
        RETURN r
        """

        result = self.client.execute_write(
            query,
            parameters={
                "node_id": node_id,
                "topic_name": topic_name,
                "confidence": confidence,
                "mentions": mentions
            }
        )

        return len(result) > 0

    def create_references_relationship(
        self,
        from_document_id: str,
        to_document_id: str,
        citation_context: Optional[str] = None
    ) -> bool:
        """
        Create REFERENCES relationship: Document -> Document (citations).

        Args:
            from_document_id: Citing document ID
            to_document_id: Cited document ID
            citation_context: Context of the citation

        Returns:
            True if created successfully
        """
        query = """
        MATCH (d1:Document {document_id: $from_document_id})
        MATCH (d2:Document {document_id: $to_document_id})
        MERGE (d1)-[r:REFERENCES]->(d2)
        SET r.citation_context = $citation_context
        RETURN r
        """

        result = self.client.execute_write(
            query,
            parameters={
                "from_document_id": from_document_id,
                "to_document_id": to_document_id,
                "citation_context": citation_context
            }
        )

        return len(result) > 0

    def create_implements_relationship(
        self,
        document_id: str,
        concept_name: str,
        implementation_type: Optional[str] = None,
        confidence: float = 1.0
    ) -> bool:
        """
        Create IMPLEMENTS relationship: Document -> Concept.

        Args:
            document_id: Document ID
            concept_name: Concept name
            implementation_type: Type of implementation
            confidence: Confidence score

        Returns:
            True if created successfully
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        MERGE (c:Concept {name: $concept_name})
        MERGE (d)-[r:IMPLEMENTS]->(c)
        SET r.implementation_type = $implementation_type,
            r.confidence = $confidence
        RETURN r
        """

        result = self.client.execute_write(
            query,
            parameters={
                "document_id": document_id,
                "concept_name": concept_name,
                "implementation_type": implementation_type,
                "confidence": confidence
            }
        )

        return len(result) > 0

    def create_related_to_relationship(
        self,
        from_id: str,
        from_label: str,
        to_id: str,
        to_label: str,
        relationship_type: str = "RELATED_TO",
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a generic relationship between any two nodes.

        Args:
            from_id: Source node ID
            from_label: Source node label
            to_id: Target node ID
            to_label: Target node label
            relationship_type: Custom relationship type
            properties: Relationship properties

        Returns:
            True if created successfully
        """
        # Determine ID fields
        from_id_field = self._get_id_field(from_label)
        to_id_field = self._get_id_field(to_label)

        query = f"""
        MATCH (n1:{from_label} {{{from_id_field}: $from_id}})
        MATCH (n2:{to_label} {{{to_id_field}: $to_id}})
        MERGE (n1)-[r:{relationship_type}]->(n2)
        SET r += $properties
        RETURN r
        """

        result = self.client.execute_write(
            query,
            parameters={
                "from_id": from_id,
                "to_id": to_id,
                "properties": properties or {}
            }
        )

        return len(result) > 0

    def link_sequential_chunks(self, document_id: str) -> int:
        """
        Create NEXT_CHUNK relationships for all chunks in a document.

        Args:
            document_id: Document ID

        Returns:
            Number of relationships created
        """
        query = """
        MATCH (d:Document {document_id: $document_id})-[:CONTAINS]->(c:Chunk)
        WITH c ORDER BY c.position
        WITH collect(c) AS chunks
        UNWIND range(0, size(chunks)-2) AS i
        WITH chunks[i] AS chunk1, chunks[i+1] AS chunk2
        MERGE (chunk1)-[r:NEXT_CHUNK]->(chunk2)
        RETURN count(r) AS created_count
        """

        result = self.client.execute_write(
            query,
            parameters={"document_id": document_id}
        )

        if result:
            count = result[0].get('created_count', 0)
            print(f"  ✓ Created {count} NEXT_CHUNK relationships")
            return count
        return 0

    def get_document_topics(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all topics discussed in a document.

        Args:
            document_id: Document ID

        Returns:
            List of topics with relationship properties
        """
        query = """
        MATCH (d:Document {document_id: $document_id})-[r:DISCUSSES_TOPIC]->(t:Topic)
        RETURN t.name AS topic, r.confidence AS confidence, r.mentions AS mentions
        ORDER BY r.confidence DESC, r.mentions DESC
        """

        results = self.client.execute_read(
            query,
            parameters={"document_id": document_id}
        )

        return results

    def get_related_documents(
        self,
        document_id: str,
        relationship_type: Optional[str] = None,
        max_depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get documents related to a given document.

        Args:
            document_id: Source document ID
            relationship_type: Specific relationship type to follow
            max_depth: Maximum path depth

        Returns:
            List of related documents
        """
        if relationship_type:
            rel_filter = f":{relationship_type}"
        else:
            rel_filter = ""

        query = f"""
        MATCH path = (d1:Document {{document_id: $document_id}})-[r{rel_filter}*1..{max_depth}]-(d2:Document)
        WHERE d1 <> d2
        RETURN DISTINCT d2.document_id AS document_id,
               d2.title AS title,
               length(path) AS distance
        ORDER BY distance, title
        """

        results = self.client.execute_read(
            query,
            parameters={"document_id": document_id}
        )

        return results

    @staticmethod
    def _get_id_field(label: str) -> str:
        """Get the ID field name for a node label."""
        id_fields = {
            "Document": "document_id",
            "Chunk": "chunk_id",
            "Topic": "name",
            "Concept": "name"
        }
        return id_fields.get(label, "id")


if __name__ == "__main__":
    # Test relationship creation
    from core import Neo4jClient
    from .nodes import NodeManager

    print("Testing relationship creation...")

    with Neo4jClient() as client:
        node_mgr = NodeManager(client)
        rel_mgr = RelationshipManager(client)

        # Create test nodes
        doc_id = node_mgr.create_document_node(
            file_path="/test/doc.pdf",
            title="Test Document",
            document_type="pdf"
        )

        chunk1_id = node_mgr.create_chunk_node(
            document_id=doc_id,
            content="First chunk",
            position=0,
            start_char=0,
            end_char=11
        )

        chunk2_id = node_mgr.create_chunk_node(
            document_id=doc_id,
            content="Second chunk",
            position=1,
            start_char=11,
            end_char=23
        )

        # Create relationships
        rel_mgr.create_contains_relationship(doc_id, chunk1_id)
        rel_mgr.create_contains_relationship(doc_id, chunk2_id)
        rel_mgr.create_next_chunk_relationship(chunk1_id, chunk2_id)

        # Link sequential chunks
        count = rel_mgr.link_sequential_chunks(doc_id)
        print(f"Sequential chunks linked: {count}")

        # Clean up
        node_mgr.delete_document_and_chunks(doc_id)
        print("Test completed!")
