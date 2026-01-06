"""
Temporal versioning schema for ScholarGraph.

This module handles the temporal versioning system including:
- Adding temporal properties to existing documents
- Creating SUPERSEDES relationships between document versions
- Managing version chains and latest version tracking

Properties added to Document nodes:
- version: Integer version number (starts at 1)
- is_latest: Boolean flag (default: true for all existing documents)
- superseded_by: Document ID of newer version (null if latest)
- superseded_at: ISO timestamp when document was superseded

Relationships:
- SUPERSEDES: From newer Document to older Document
  Properties: reason (str), timestamp (str)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from core import Neo4jClient


class TemporalSchemaManager:
    """
    Manages temporal versioning schema for ScholarGraph.

    Handles schema updates for document versioning and supersession tracking.
    """

    def __init__(self, client: Neo4jClient):
        """
        Initialize temporal schema manager.

        Args:
            client: Neo4jClient instance
        """
        self.client = client

    def initialize_temporal_schema(self) -> Dict[str, Any]:
        """
        Initialize temporal versioning schema (non-breaking, backwards compatible).

        This method adds new properties to all existing Document nodes with
        safe default values that preserve current behavior.

        Returns:
            Dictionary with initialization results
        """
        results = {
            "properties_added": 0,
            "indexes_created": [],
            "errors": []
        }

        print("Initializing temporal versioning schema...")

        # Phase 1: Add temporal properties to all existing documents
        print("\n1. Adding temporal properties to existing documents...")
        try:
            query = """
            MATCH (d:Document)
            WHERE d.version IS NULL
            SET d.version = 1,
                d.is_latest = true,
                d.superseded_by = null,
                d.superseded_at = null
            RETURN count(d) as updated_count
            """
            result = self.client.execute_write(query)
            if result:
                count = result[0].get('updated_count', 0)
                results["properties_added"] = count
                print(f"  ✓ Added temporal properties to {count} documents")
        except Exception as e:
            error_msg = f"Failed to add temporal properties: {e}"
            results["errors"].append(error_msg)
            print(f"  ✗ {error_msg}")

        # Phase 2: Create index for is_latest filtering
        print("\n2. Creating index for is_latest filtering...")
        try:
            index_query = """
            CREATE INDEX document_is_latest_index IF NOT EXISTS
            FOR (d:Document) ON (d.is_latest)
            """
            self.client.execute_write(index_query)
            results["indexes_created"].append("document_is_latest_index")
            print(f"  ✓ Created index: document_is_latest_index")
        except Exception as e:
            error_msg = f"Failed to create is_latest index: {e}"
            results["errors"].append(error_msg)
            print(f"  ⚠ {error_msg}")

        # Phase 3: Create index for superseded_by
        print("\n3. Creating index for superseded_by...")
        try:
            index_query = """
            CREATE INDEX document_superseded_by_index IF NOT EXISTS
            FOR (d:Document) ON (d.superseded_by)
            """
            self.client.execute_write(index_query)
            results["indexes_created"].append("document_superseded_by_index")
            print(f"  ✓ Created index: document_superseded_by_index")
        except Exception as e:
            error_msg = f"Failed to create superseded_by index: {e}"
            results["errors"].append(error_msg)
            print(f"  ⚠ {error_msg}")

        print("\nTemporal versioning schema initialization complete!")
        return results

    def create_supersedes_relationship(
        self,
        newer_document_id: str,
        older_document_id: str,
        reason: str = "auto_detected",
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Create a SUPERSEDES relationship between documents.

        Args:
            newer_document_id: ID of the newer document
            older_document_id: ID of the older (superseded) document
            reason: Reason for supersession (default: "auto_detected")
            timestamp: ISO timestamp (default: current time)

        Returns:
            True if relationship created successfully
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        query = """
        MATCH (newer:Document {document_id: $newer_id})
        MATCH (older:Document {document_id: $older_id})
        MERGE (newer)-[r:SUPERSEDES]->(older)
        SET r.reason = $reason,
            r.timestamp = $timestamp
        RETURN r
        """

        try:
            result = self.client.execute_write(
                query,
                parameters={
                    "newer_id": newer_document_id,
                    "older_id": older_document_id,
                    "reason": reason,
                    "timestamp": timestamp
                }
            )
            return len(result) > 0
        except Exception as e:
            print(f"Failed to create SUPERSEDES relationship: {e}")
            return False

    def mark_document_superseded(
        self,
        document_id: str,
        superseded_by: str,
        superseded_at: Optional[str] = None
    ) -> bool:
        """
        Mark a document as superseded by another document.

        Args:
            document_id: ID of document to mark as superseded
            superseded_by: ID of newer document
            superseded_at: ISO timestamp (default: current time)

        Returns:
            True if update successful
        """
        if superseded_at is None:
            superseded_at = datetime.now().isoformat()

        query = """
        MATCH (d:Document {document_id: $document_id})
        SET d.is_latest = false,
            d.superseded_by = $superseded_by,
            d.superseded_at = $superseded_at
        RETURN d.document_id
        """

        try:
            result = self.client.execute_write(
                query,
                parameters={
                    "document_id": document_id,
                    "superseded_by": superseded_by,
                    "superseded_at": superseded_at
                }
            )
            return len(result) > 0
        except Exception as e:
            print(f"Failed to mark document as superseded: {e}")
            return False

    def get_document_version_chain(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get the full version chain for a document.

        Args:
            document_id: Starting document ID

        Returns:
            List of documents in version chain, ordered newest to oldest
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        OPTIONAL MATCH (d)-[:SUPERSEDES*]->(older:Document)
        OPTIONAL MATCH (newer:Document)-[:SUPERSEDES*]->(d)
        WITH COLLECT(DISTINCT older) + COLLECT(DISTINCT d) + COLLECT(DISTINCT newer) AS all_docs
        UNWIND all_docs AS doc
        RETURN DISTINCT doc.document_id AS document_id,
               doc.title AS title,
               doc.version AS version,
               doc.is_latest AS is_latest,
               doc.ingestion_date AS ingestion_date,
               doc.superseded_by AS superseded_by,
               doc.superseded_at AS superseded_at
        ORDER BY doc.ingestion_date DESC
        """

        try:
            return self.client.execute_read(query, parameters={"document_id": document_id})
        except Exception as e:
            print(f"Failed to get version chain: {e}")
            return []

    def get_latest_version(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest version of a document based on version chain.

        Args:
            document_id: Any document ID in the version chain

        Returns:
            Latest document properties or None if not found
        """
        query = """
        MATCH (d:Document {document_id: $document_id})
        MATCH (latest:Document)
        WHERE (latest)-[:SUPERSEDES*]->(d) OR latest.document_id = d.document_id
        WHERE latest.is_latest = true
        RETURN latest.document_id AS document_id,
               latest.title AS title,
               latest.version AS version,
               latest.ingestion_date AS ingestion_date
        LIMIT 1
        """

        try:
            result = self.client.execute_read(query, parameters={"document_id": document_id})
            return result[0] if result else None
        except Exception as e:
            print(f"Failed to get latest version: {e}")
            return None

    def get_superseded_documents(self) -> List[Dict[str, Any]]:
        """
        Get all documents that have been superseded.

        Returns:
            List of superseded documents with their newer version info
        """
        query = """
        MATCH (old:Document)
        WHERE old.is_latest = false
        OPTIONAL MATCH (new:Document {document_id: old.superseded_by})
        RETURN old.document_id AS document_id,
               old.title AS title,
               old.version AS version,
               old.superseded_at AS superseded_at,
               new.document_id AS superseded_by_id,
               new.title AS superseded_by_title,
               new.ingestion_date AS newer_ingestion_date
        ORDER BY old.superseded_at DESC
        """

        try:
            return self.client.execute_read(query)
        except Exception as e:
            print(f"Failed to get superseded documents: {e}")
            return []

    def drop_temporal_schema(self) -> Dict[str, Any]:
        """
        Remove temporal versioning properties and indexes.

        Warning: This will remove versioning information but keep documents.

        Returns:
            Dictionary with removal results
        """
        results = {
            "properties_removed": 0,
            "indexes_dropped": [],
            "relationships_removed": 0,
            "errors": []
        }

        print("Dropping temporal versioning schema...")

        # Remove indexes
        for index_name in ["document_is_latest_index", "document_superseded_by_index"]:
            try:
                query = f"DROP INDEX {index_name} IF EXISTS"
                self.client.execute_write(query)
                results["indexes_dropped"].append(index_name)
                print(f"  ✓ Dropped index: {index_name}")
            except Exception as e:
                results["errors"].append(f"Failed to drop {index_name}: {e}")

        # Remove SUPERSEDES relationships
        try:
            query = """
            MATCH ()-[r:SUPERSEDES]-()
            DELETE r
            RETURN count(r) as deleted
            """
            result = self.client.execute_write(query)
            if result:
                results["relationships_removed"] = result[0].get('deleted', 0)
                print(f"  ✓ Deleted {results['relationships_removed']} SUPERSEDES relationships")
        except Exception as e:
            results["errors"].append(f"Failed to delete relationships: {e}")

        # Remove properties from documents
        try:
            query = """
            MATCH (d:Document)
            REMOVE d.version, d.is_latest, d.superseded_by, d.superseded_at
            RETURN count(d) as updated
            """
            result = self.client.execute_write(query)
            if result:
                results["properties_removed"] = result[0].get('updated', 0)
                print(f"  ✓ Removed temporal properties from {results['properties_removed']} documents")
        except Exception as e:
            results["errors"].append(f"Failed to remove properties: {e}")

        print("Temporal versioning schema removal complete!")
        return results


if __name__ == "__main__":
    # Test temporal schema manager
    from core import Neo4jClient

    print("Testing temporal schema manager...")

    with Neo4jClient() as client:
        manager = TemporalSchemaManager(client)

        # Initialize temporal schema
        print("\nInitializing temporal schema...")
        results = manager.initialize_temporal_schema()
        print(f"Results: {results}")

        # Get version chain for a document
        # print("\nGetting version chain...")
        # chain = manager.get_document_version_chain("some_doc_id")
        # print(f"Chain: {chain}")
