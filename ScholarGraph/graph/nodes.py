"""
Node creation and management for ScholarGraph.

Node types:
- Document: Research papers, markdown files
- Chunk: Text segments from documents
- Topic: Research topics and themes
- Concept: Domain concepts and terminology
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
from core import Neo4jClient


class NodeManager:
    """Manages creation and retrieval of graph nodes."""

    def __init__(self, client: Neo4jClient):
        """
        Initialize node manager.

        Args:
            client: Neo4jClient instance
        """
        self.client = client

    def create_document_node(
        self,
        file_path: str,
        title: str,
        document_type: str,
        content: Optional[str] = None,
        abstract: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        authors: Optional[List[str]] = None,
        date: Optional[str] = None,
        doi: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        file_modified_at: Optional[str] = None
    ) -> str:
        """
        Create a Document node.

        Args:
            file_path: Path to the document file
            title: Document title
            document_type: Type (pdf, markdown, etc.)
            content: Full document content (optional)
            abstract: Document abstract
            keywords: List of keywords
            authors: List of authors
            date: Publication date
            doi: Digital Object Identifier
            embedding: Document-level embedding vector
            metadata: Additional metadata
            file_modified_at: File modification timestamp (ISO format)

        Returns:
            document_id: Unique identifier for the document
        """
        # Generate unique document ID from file path
        document_id = self._generate_id(file_path)

        # Prepare node properties
        properties = {
            "document_id": document_id,
            "file_path": file_path,
            "title": title,
            "document_type": document_type,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Add optional properties
        if content:
            properties["content"] = content
        if abstract:
            properties["abstract"] = abstract
        if keywords:
            properties["keywords"] = keywords
        if authors:
            properties["authors"] = authors
        if date:
            properties["date"] = date
        if doi:
            properties["doi"] = doi
        if embedding:
            properties["embedding"] = embedding
        if metadata:
            # Convert metadata to JSON string to avoid nested map issues
            properties["metadata"] = json.dumps(metadata)
        if file_modified_at:
            properties["file_modified_at"] = file_modified_at

        # Create node
        query = """
        MERGE (d:Document {document_id: $document_id})
        SET d += $properties
        RETURN d.document_id AS document_id
        """

        result = self.client.execute_write(
            query,
            parameters={"document_id": document_id, "properties": properties}
        )

        print(f"  ✓ Created Document: {title[:50]}...")
        return document_id

    def create_chunk_node(
        self,
        document_id: str,
        content: str,
        position: int,
        start_char: int,
        end_char: int,
        embedding: Optional[List[float]] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a Chunk node.

        Args:
            document_id: Parent document ID
            content: Chunk text content
            position: Position in document (0-indexed)
            start_char: Starting character position
            end_char: Ending character position
            embedding: Chunk embedding vector
            summary: Optional summary of chunk
            metadata: Additional metadata

        Returns:
            chunk_id: Unique identifier for the chunk
        """
        # Generate unique chunk ID
        chunk_id = self._generate_id(f"{document_id}_{position}")

        # Prepare node properties
        properties = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "content": content,
            "position": position,
            "start_char": start_char,
            "end_char": end_char,
            "word_count": len(content.split()),
            "char_count": len(content),
            "created_at": datetime.now().isoformat(),
        }

        # Add optional properties
        if embedding:
            properties["embedding"] = embedding
        if summary:
            properties["summary"] = summary
        if metadata:
            # Convert metadata to JSON string to avoid nested map issues
            properties["metadata"] = json.dumps(metadata)

        # Create node
        query = """
        MERGE (c:Chunk {chunk_id: $chunk_id})
        SET c += $properties
        RETURN c.chunk_id AS chunk_id
        """

        result = self.client.execute_write(
            query,
            parameters={"chunk_id": chunk_id, "properties": properties}
        )

        return chunk_id

    def create_topic_node(
        self,
        name: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> str:
        """
        Create a Topic node.

        Args:
            name: Topic name
            category: Topic category
            description: Topic description
            keywords: Related keywords

        Returns:
            topic_name: The topic name (used as ID)
        """
        # Prepare node properties
        properties = {
            "name": name,
            "created_at": datetime.now().isoformat(),
        }

        if category:
            properties["category"] = category
        if description:
            properties["description"] = description
        if keywords:
            properties["keywords"] = keywords

        # Create node
        query = """
        MERGE (t:Topic {name: $name})
        SET t += $properties
        RETURN t.name AS name
        """

        result = self.client.execute_write(
            query,
            parameters={"name": name, "properties": properties}
        )

        return name

    def create_concept_node(
        self,
        name: str,
        category: Optional[str] = None,
        definition: Optional[str] = None,
        synonyms: Optional[List[str]] = None
    ) -> str:
        """
        Create a Concept node.

        Args:
            name: Concept name
            category: Concept category
            definition: Concept definition
            synonyms: Alternative names

        Returns:
            concept_name: The concept name (used as ID)
        """
        # Prepare node properties
        properties = {
            "name": name,
            "created_at": datetime.now().isoformat(),
        }

        if category:
            properties["category"] = category
        if definition:
            properties["definition"] = definition
        if synonyms:
            properties["synonyms"] = synonyms

        # Create node
        query = """
        MERGE (c:Concept {name: $name})
        SET c += $properties
        RETURN c.name AS name
        """

        result = self.client.execute_write(
            query,
            parameters={"name": name, "properties": properties}
        )

        return name

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document properties or None if not found
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        RETURN d
        """

        results = self.client.execute_read(query, parameters={"document_id": document_id})

        if results:
            return dict(results[0]['d'])
        return None

    def get_chunks_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a document.

        Args:
            document_id: Document identifier

        Returns:
            List of chunk properties
        """
        query = """
        MATCH (c:Chunk {document_id: $document_id})
        RETURN c
        ORDER BY c.position
        """

        results = self.client.execute_read(query, parameters={"document_id": document_id})

        return [dict(r['c']) for r in results]

    def delete_document_and_chunks(self, document_id: str) -> int:
        """
        Delete a document and all its chunks.

        Args:
            document_id: Document identifier

        Returns:
            Number of nodes deleted
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
        DETACH DELETE d, c
        RETURN count(d) + count(c) AS deleted_count
        """

        result = self.client.execute_write(query, parameters={"document_id": document_id})

        if result:
            deleted = result[0].get('deleted_count', 0)
            print(f"  ✓ Deleted document and {deleted} nodes")
            return deleted
        return 0

    @staticmethod
    def _generate_id(text: str) -> str:
        """
        Generate a unique ID from text using SHA256.

        Args:
            text: Input text

        Returns:
            Hex digest string
        """
        return hashlib.sha256(text.encode()).hexdigest()[:16]


if __name__ == "__main__":
    # Test node creation
    from core import Neo4jClient

    print("Testing node creation...")

    with Neo4jClient() as client:
        manager = NodeManager(client)

        # Create a test document
        doc_id = manager.create_document_node(
            file_path="/test/document.pdf",
            title="Test Document",
            document_type="pdf",
            abstract="This is a test document",
            keywords=["test", "example"],
            authors=["Test Author"]
        )

        print(f"Created document: {doc_id}")

        # Create a test chunk
        chunk_id = manager.create_chunk_node(
            document_id=doc_id,
            content="This is a test chunk of text.",
            position=0,
            start_char=0,
            end_char=30
        )

        print(f"Created chunk: {chunk_id}")

        # Retrieve document
        doc = manager.get_document_by_id(doc_id)
        print(f"Retrieved document: {doc['title']}")

        # Clean up
        deleted = manager.delete_document_and_chunks(doc_id)
        print(f"Cleaned up: {deleted} nodes deleted")
