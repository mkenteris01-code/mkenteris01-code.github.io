"""
Neo4j database client with connection pooling and retry logic.
"""

from typing import Any, Optional, List, Dict
from neo4j import GraphDatabase, Driver, Session, Result
from neo4j.exceptions import ServiceUnavailable, AuthError, SessionExpired
from contextlib import contextmanager

from config import get_settings
from .retry_handler import retry_with_exponential_backoff


class Neo4jClient:
    """
    Neo4j database client with connection pooling and automatic retries.

    Attributes:
        driver: Neo4j driver instance
        database: Name of the database to use
    """

    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None,
                 password: Optional[str] = None, database: Optional[str] = None):
        """
        Initialize Neo4j client with credentials from settings.

        Args:
            uri: Neo4j URI (defaults to settings)
            user: Neo4j username (defaults to settings)
            password: Neo4j password (defaults to settings)
            database: Database name (defaults to settings)
        """
        settings = get_settings()

        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database

        self._driver: Optional[Driver] = None

    @property
    def driver(self) -> Driver:
        """
        Get or create the Neo4j driver instance.

        Returns:
            Driver: Neo4j driver instance
        """
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver

    @retry_with_exponential_backoff(max_attempts=3)
    def _create_driver(self) -> Driver:
        """
        Create Neo4j driver with retry logic.

        Returns:
            Driver: Neo4j driver instance

        Raises:
            AuthError: If authentication fails
            ServiceUnavailable: If Neo4j service is unavailable
        """
        try:
            driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=120
            )

            # Verify connectivity
            driver.verify_connectivity()

            print(f"Connected to Neo4j at {self.uri}")
            return driver

        except AuthError as e:
            print(f"Authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            print(f"Neo4j service unavailable: {e}")
            raise

    @contextmanager
    def session(self, **kwargs: Any):
        """
        Context manager for Neo4j sessions.

        Args:
            **kwargs: Additional session parameters

        Yields:
            Session: Neo4j session instance

        Example:
            with client.session() as session:
                result = session.run("MATCH (n) RETURN count(n)")
        """
        session = self.driver.session(database=self.database, **kwargs)
        try:
            yield session
        finally:
            session.close()

    @retry_with_exponential_backoff(max_attempts=3)
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as list of dictionaries.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries

        Example:
            results = client.execute_query(
                "MATCH (n:Document {id: $doc_id}) RETURN n",
                parameters={"doc_id": "123"}
            )
        """
        parameters = parameters or {}

        with self.session() as session:
            result = session.run(query, parameters)
            return [dict(record) for record in result]

    @retry_with_exponential_backoff(max_attempts=3)
    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a write transaction with retry logic.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        parameters = parameters or {}

        with self.session() as session:
            result = session.execute_write(
                lambda tx: list(tx.run(query, parameters))
            )
            return [dict(record) for record in result]

    @retry_with_exponential_backoff(max_attempts=3)
    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a read transaction with retry logic.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries
        """
        parameters = parameters or {}

        with self.session() as session:
            result = session.execute_read(
                lambda tx: list(tx.run(query, parameters))
            )
            return [dict(record) for record in result]

    def verify_connection(self) -> Dict[str, str]:
        """
        Verify database connection and return version info.

        Returns:
            Dictionary with connection status and Neo4j version
        """
        try:
            query = """
            CALL dbms.components()
            YIELD name, versions
            WHERE name='Neo4j'
            RETURN versions[0] AS version
            """

            result = self.execute_query(query)

            if result:
                version = result[0].get('version', 'Unknown')
                return {
                    'status': 'connected',
                    'version': version,
                    'database': self.database
                }
            else:
                return {
                    'status': 'error',
                    'message': 'No version information returned'
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with node counts, relationship counts, etc.
        """
        query = """
        MATCH (n)
        WITH labels(n) AS nodeLabels
        UNWIND nodeLabels AS label
        RETURN label, count(*) AS count
        ORDER BY count DESC
        """

        try:
            results = self.execute_query(query)

            # Also get relationship counts
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) AS relationship, count(r) AS count
            ORDER BY count DESC
            """
            rel_results = self.execute_query(rel_query)

            return {
                'nodes': {r['label']: r['count'] for r in results},
                'relationships': {r['relationship']: r['count'] for r in rel_results}
            }

        except Exception as e:
            return {
                'error': str(e)
            }

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            print("Neo4j connection closed")

    def __enter__(self) -> "Neo4jClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - close connection."""
        self.close()


if __name__ == "__main__":
    # Test Neo4j connection
    print("Testing Neo4j connection...")

    try:
        with Neo4jClient() as client:
            # Verify connection
            status = client.verify_connection()
            print(f"\nConnection Status: {status}")

            # Get database stats
            stats = client.get_database_stats()
            print(f"\nDatabase Statistics:")
            print(f"Nodes: {stats.get('nodes', {})}")
            print(f"Relationships: {stats.get('relationships', {})}")

    except Exception as e:
        print(f"Error: {e}")
