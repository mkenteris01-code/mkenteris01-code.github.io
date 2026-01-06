"""
Neo4j schema initialization for ScholarGraph.

Defines:
- Node labels: Document, Chunk, Topic, Concept
- Relationships: CONTAINS, NEXT_CHUNK, DISCUSSES_TOPIC, REFERENCES, IMPLEMENTS
- Indexes: Vector (embeddings), Full-text (content), Property (IDs, dates)
"""

from typing import List, Dict, Any
from core import Neo4jClient


class SchemaManager:
    """Manages Neo4j database schema initialization and updates."""

    def __init__(self, client: Neo4jClient):
        """
        Initialize schema manager.

        Args:
            client: Neo4jClient instance
        """
        self.client = client

    def initialize_schema(self, vector_dimension: int = 768) -> Dict[str, Any]:
        """
        Initialize complete database schema.

        Args:
            vector_dimension: Dimension of embedding vectors (768 or 4096)

        Returns:
            Dictionary with initialization results
        """
        results = {}

        print("Initializing ScholarGraph schema...")

        # Create constraints
        print("\n1. Creating constraints...")
        results["constraints"] = self._create_constraints()

        # Create property indexes
        print("\n2. Creating property indexes...")
        results["property_indexes"] = self._create_property_indexes()

        # Create full-text indexes
        print("\n3. Creating full-text indexes...")
        results["fulltext_indexes"] = self._create_fulltext_indexes()

        # Create vector indexes
        print(f"\n4. Creating vector indexes (dimension: {vector_dimension})...")
        results["vector_indexes"] = self._create_vector_indexes(vector_dimension)

        print("\nSchema initialization complete!")
        return results

    def _create_constraints(self) -> List[str]:
        """Create uniqueness constraints for node IDs."""
        constraints = [
            # Document constraints
            """
            CREATE CONSTRAINT document_id_unique IF NOT EXISTS
            FOR (d:Document) REQUIRE d.document_id IS UNIQUE
            """,

            # Chunk constraints
            """
            CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
            FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
            """,

            # Topic constraints
            """
            CREATE CONSTRAINT topic_name_unique IF NOT EXISTS
            FOR (t:Topic) REQUIRE t.name IS UNIQUE
            """,

            # Concept constraints
            """
            CREATE CONSTRAINT concept_name_unique IF NOT EXISTS
            FOR (c:Concept) REQUIRE c.name IS UNIQUE
            """,
        ]

        created = []
        for constraint in constraints:
            try:
                self.client.execute_write(constraint.strip())
                constraint_name = constraint.split("FOR")[0].split("CONSTRAINT")[1].strip().split()[0]
                created.append(constraint_name)
                print(f"  ✓ Created constraint: {constraint_name}")
            except Exception as e:
                print(f"  ⚠ Constraint creation warning: {e}")

        return created

    def _create_property_indexes(self) -> List[str]:
        """Create property indexes for efficient lookups."""
        indexes = [
            # Document indexes
            """
            CREATE INDEX document_type_index IF NOT EXISTS
            FOR (d:Document) ON (d.document_type)
            """,

            """
            CREATE INDEX document_date_index IF NOT EXISTS
            FOR (d:Document) ON (d.date)
            """,

            # Chunk indexes
            """
            CREATE INDEX chunk_position_index IF NOT EXISTS
            FOR (c:Chunk) ON (c.position)
            """,

            """
            CREATE INDEX chunk_document_id_index IF NOT EXISTS
            FOR (c:Chunk) ON (c.document_id)
            """,

            # Topic indexes
            """
            CREATE INDEX topic_category_index IF NOT EXISTS
            FOR (t:Topic) ON (t.category)
            """,
        ]

        created = []
        for index in indexes:
            try:
                self.client.execute_write(index.strip())
                index_name = index.split("CREATE INDEX")[1].split("IF NOT EXISTS")[0].strip()
                created.append(index_name)
                print(f"  ✓ Created index: {index_name}")
            except Exception as e:
                print(f"  ⚠ Index creation warning: {e}")

        return created

    def _create_fulltext_indexes(self) -> List[str]:
        """Create full-text indexes for keyword search."""
        indexes = [
            # Document content full-text search
            """
            CREATE FULLTEXT INDEX document_content_fulltext IF NOT EXISTS
            FOR (d:Document) ON EACH [d.title, d.abstract, d.keywords]
            """,

            # Chunk content full-text search
            """
            CREATE FULLTEXT INDEX chunk_content_fulltext IF NOT EXISTS
            FOR (c:Chunk) ON EACH [c.content, c.summary]
            """,

            # Topic full-text search
            """
            CREATE FULLTEXT INDEX topic_fulltext IF NOT EXISTS
            FOR (t:Topic) ON EACH [t.name, t.description]
            """,
        ]

        created = []
        for index in indexes:
            try:
                self.client.execute_write(index.strip())
                index_name = index.split("CREATE FULLTEXT INDEX")[1].split("IF NOT EXISTS")[0].strip()
                created.append(index_name)
                print(f"  ✓ Created full-text index: {index_name}")
            except Exception as e:
                print(f"  ⚠ Full-text index warning: {e}")

        return created

    def _create_vector_indexes(self, dimension: int) -> List[str]:
        """
        Create vector indexes for semantic search.

        Args:
            dimension: Embedding vector dimension

        Note:
            Neo4j 5.13+ supports native vector indexes.
            Requires: CREATE VECTOR INDEX syntax
        """
        indexes = [
            # Chunk embeddings vector index
            f"""
            CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {{
              indexConfig: {{
                `vector.dimensions`: {dimension},
                `vector.similarity_function`: 'cosine'
              }}
            }}
            """,

            # Document embeddings vector index (optional)
            f"""
            CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
            FOR (d:Document) ON (d.embedding)
            OPTIONS {{
              indexConfig: {{
                `vector.dimensions`: {dimension},
                `vector.similarity_function`: 'cosine'
              }}
            }}
            """,
        ]

        created = []
        for index in indexes:
            try:
                self.client.execute_write(index.strip())
                index_name = index.split("CREATE VECTOR INDEX")[1].split("IF NOT EXISTS")[0].strip()
                created.append(index_name)
                print(f"  ✓ Created vector index: {index_name}")
            except Exception as e:
                error_msg = str(e)
                if "vector" in error_msg.lower():
                    print(f"  ⚠ Vector index not supported. Neo4j 5.13+ required. Error: {error_msg}")
                else:
                    print(f"  ⚠ Vector index warning: {e}")

        return created

    def drop_all_indexes(self) -> None:
        """Drop all indexes. Use with caution!"""
        print("⚠ WARNING: Dropping all indexes...")

        # Get all indexes
        query = "SHOW INDEXES"
        indexes = self.client.execute_query(query)

        for index in indexes:
            index_name = index.get('name', '')
            if index_name:
                try:
                    drop_query = f"DROP INDEX {index_name} IF EXISTS"
                    self.client.execute_write(drop_query)
                    print(f"  ✓ Dropped index: {index_name}")
                except Exception as e:
                    print(f"  ✗ Failed to drop {index_name}: {e}")

    def drop_all_constraints(self) -> None:
        """Drop all constraints. Use with caution!"""
        print("⚠ WARNING: Dropping all constraints...")

        # Get all constraints
        query = "SHOW CONSTRAINTS"
        constraints = self.client.execute_query(query)

        for constraint in constraints:
            constraint_name = constraint.get('name', '')
            if constraint_name:
                try:
                    drop_query = f"DROP CONSTRAINT {constraint_name} IF EXISTS"
                    self.client.execute_write(drop_query)
                    print(f"  ✓ Dropped constraint: {constraint_name}")
                except Exception as e:
                    print(f"  ✗ Failed to drop {constraint_name}: {e}")

    def reset_schema(self, vector_dimension: int = 768) -> Dict[str, Any]:
        """
        Reset schema by dropping and recreating all indexes/constraints.

        Args:
            vector_dimension: Dimension of embedding vectors

        Returns:
            Dictionary with reset results
        """
        print("="*60)
        print("RESETTING SCHEMA")
        print("="*60)

        self.drop_all_indexes()
        self.drop_all_constraints()

        print("\nRecreating schema...")
        return self.initialize_schema(vector_dimension)

    def show_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Display current schema information.

        Returns:
            Dictionary with constraints, indexes, and statistics
        """
        # Get constraints
        constraints = self.client.execute_query("SHOW CONSTRAINTS")

        # Get indexes
        indexes = self.client.execute_query("SHOW INDEXES")

        # Get node counts
        stats = self.client.get_database_stats()

        return {
            "constraints": constraints,
            "indexes": indexes,
            "statistics": stats
        }


if __name__ == "__main__":
    # Test schema initialization
    from config import get_settings

    settings = get_settings()

    print("Testing schema initialization...")

    with Neo4jClient() as client:
        manager = SchemaManager(client)

        # Show current schema
        print("\nCurrent schema:")
        schema_info = manager.show_schema()
        print(f"Constraints: {len(schema_info['constraints'])}")
        print(f"Indexes: {len(schema_info['indexes'])}")
        print(f"Statistics: {schema_info['statistics']}")

        # Initialize schema
        print("\nInitializing schema...")
        results = manager.initialize_schema(
            vector_dimension=settings.embedding_dimension
        )
        print(f"\nInitialization results: {results}")
