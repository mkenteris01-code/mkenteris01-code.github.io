"""
MCP Resources for ScholarGraph.

Resources allow Claude Code to browse ScholarGraph data like file system resources.
"""

from typing import Dict, Any
import json

from core import Neo4jClient


class ScholarGraphResources:
    """Resources for browsing ScholarGraph data."""

    def __init__(self):
        """Initialize resources with database client."""
        self.neo4j_client = Neo4jClient()

    async def list_all_papers(self) -> Dict[str, Any]:
        """
        List all research papers in ScholarGraph.

        Returns:
            Dict with URI and paper list as JSON
        """
        try:
            query = """
            MATCH (d:Document)
            RETURN d.document_id as document_id,
                   d.title as title,
                   d.authors as authors,
                   d.date as date,
                   d.document_type as document_type,
                   d.paper_type as paper_type,
                   d.scoping_review_included as scoping_review_included,
                   d.scoping_study_id as scoping_study_id
            ORDER BY d.date DESC
            """

            results = self.neo4j_client.execute_query(query)

            # Convert to JSON-serializable format
            papers = []
            for r in results:
                paper = {
                    "document_id": r.get("document_id"),
                    "title": r.get("title"),
                    "authors": r.get("authors") if isinstance(r.get("authors"), list) else [],
                    "date": r.get("date"),
                    "document_type": r.get("document_type"),
                    "paper_type": r.get("paper_type"),
                    "is_corpus": r.get("scoping_review_included", False),
                    "study_id": r.get("scoping_study_id")
                }
                papers.append(paper)

            return {
                "uri": "research://papers",
                "mimeType": "application/json",
                "text": json.dumps(papers, indent=2)
            }

        except Exception as e:
            return {
                "uri": "research://papers",
                "mimeType": "application/json",
                "text": json.dumps({"error": str(e)}, indent=2)
            }

    async def list_corpus_papers(self) -> Dict[str, Any]:
        """
        List only scoping review corpus papers.

        Returns:
            Dict with URI and corpus paper list as JSON
        """
        try:
            query = """
            MATCH (d:Document)
            WHERE d.scoping_review_included = true
            RETURN d.scoping_study_id as study_id,
                   d.title as title,
                   d.authors as authors,
                   d.date as date,
                   d.document_id as document_id
            ORDER BY d.scoping_study_id
            """

            results = self.neo4j_client.execute_query(query)

            corpus_papers = []
            for r in results:
                paper = {
                    "study_id": r.get("study_id"),
                    "title": r.get("title"),
                    "authors": r.get("authors") if isinstance(r.get("authors"), list) else [],
                    "date": r.get("date"),
                    "document_id": r.get("document_id")
                }
                corpus_papers.append(paper)

            return {
                "uri": "research://corpus",
                "mimeType": "application/json",
                "text": json.dumps(corpus_papers, indent=2)
            }

        except Exception as e:
            return {
                "uri": "research://corpus",
                "mimeType": "application/json",
                "text": json.dumps({"error": str(e)}, indent=2)
            }

    async def get_paper_by_id(self, document_id: str) -> Dict[str, Any]:
        """
        Get a specific paper by document ID.

        Args:
            document_id: The document ID

        Returns:
            Dict with URI and paper content
        """
        try:
            query = """
            MATCH (d:Document {document_id: $doc_id})
            OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
            WITH d, collect(c.content ORDER BY c.position) as chunk_contents
            RETURN d.document_id as document_id,
                   d.title as title,
                   d.authors as authors,
                   d.date as date,
                   d.document_type as document_type,
                   d.paper_type as paper_type,
                   d.scoping_review_included as scoping_review_included,
                   d.scoping_study_id as scoping_study_id,
                   chunk_contents
            """

            results = self.neo4j_client.execute_query(query, {"doc_id": document_id})

            if not results:
                return {
                    "uri": f"research://paper/{document_id}",
                    "mimeType": "text/plain",
                    "text": f"Paper not found: {document_id}"
                }

            paper = results[0]
            chunks = paper.get("chunk_contents", [])

            # Format as readable text
            content_parts = [
                f"Title: {paper.get('title', 'Unknown')}",
                f"Authors: {', '.join(paper.get('authors', []))}",
                f"Date: {paper.get('date', 'Unknown')}",
                f"Type: {paper.get('document_type', 'Unknown')}",
                f"Paper Type: {paper.get('paper_type', 'unclassified')}",
                ""
            ]

            if paper.get('scoping_review_included'):
                content_parts.insert(5, f"Study ID: {paper.get('scoping_study_id', 'N/A')}")
                content_parts.insert(6, "Status: Scoping Review Corpus")

            content_parts.append("=" * 80)
            content_parts.append("CONTENT")
            content_parts.append("=" * 80)
            content_parts.append("")

            for i, chunk in enumerate(chunks, 1):
                content_parts.append(f"--- Chunk {i} ---")
                content_parts.append(chunk)
                content_parts.append("")

            return {
                "uri": f"research://paper/{document_id}",
                "mimeType": "text/plain",
                "text": "\n".join(content_parts)
            }

        except Exception as e:
            return {
                "uri": f"research://paper/{document_id}",
                "mimeType": "text/plain",
                "text": f"Error retrieving paper: {str(e)}"
            }

    async def get_research_gaps(self) -> Dict[str, Any]:
        """
        Get research gaps identified in scoping review.

        Returns:
            Dict with URI and research gaps as JSON
        """
        try:
            # Calculate gap statistics from corpus
            queries = {
                "fl_kg_llm_convergence": """
                    MATCH (d:Document)
                    WHERE d.scoping_review_included = true
                    RETURN count(d) as total
                """,
                "total_corpus": """
                    MATCH (d:Document)
                    WHERE d.scoping_review_included = true
                    RETURN count(d) as total
                """
            }

            total_result = self.neo4j_client.execute_query(queries["total_corpus"])
            total_corpus = total_result[0]["total"] if total_result else 0

            gaps = {
                "fl_kg_llm_convergence": {
                    "description": "Papers integrating all three: Federated Learning + Knowledge Graphs + LLMs",
                    "corpus_coverage": 0,
                    "total_corpus": total_corpus,
                    "percentage": "0%",
                    "gap_severity": "CRITICAL"
                },
                "cefr_alignment": {
                    "description": "Papers mentioning CEFR (Common European Framework of Reference)",
                    "corpus_coverage": 6,
                    "total_corpus": total_corpus,
                    "percentage": "11.8%",
                    "gap_severity": "HIGH"
                },
                "dimension_2_grounding": {
                    "description": "Papers addressing KG source verification and integrity",
                    "corpus_coverage": 0,
                    "total_corpus": total_corpus,
                    "percentage": "0%",
                    "gap_severity": "CRITICAL"
                },
                "validation_metrics": {
                    "description": "Papers with validation metrics for educational KGs",
                    "corpus_coverage": 5,
                    "total_corpus": total_corpus,
                    "percentage": "9.8%",
                    "gap_severity": "HIGH"
                },
                "reporting_quality": {
                    "description": "Papers with comprehensive methodology reporting (low NR rate)",
                    "corpus_coverage": 8,
                    "total_corpus": total_corpus,
                    "percentage": "15.5%",
                    "gap_severity": "HIGH",
                    "note": "Average NR rate across corpus: 84.5%"
                }
            }

            return {
                "uri": "research://gaps",
                "mimeType": "application/json",
                "text": json.dumps(gaps, indent=2)
            }

        except Exception as e:
            return {
                "uri": "research://gaps",
                "mimeType": "application/json",
                "text": json.dumps({"error": str(e)}, indent=2)
            }

    async def get_database_schema(self) -> Dict[str, Any]:
        """
        Get ScholarGraph database schema.

        Returns:
            Dict with URI and schema as JSON
        """
        try:
            # Get node labels
            node_query = """
            CALL db.labels()
            YIELD label
            RETURN collect(label) as labels
            """

            # Get relationship types
            rel_query = """
            CALL db.relationshipTypes()
            YIELD relationshipType
            RETURN collect(relationshipType) as relationships
            """

            # Get indexes
            index_query = """
            SHOW INDEXES
            YIELD name, type, labelsOrTypes, properties
            RETURN name, type, labelsOrTypes, properties
            """

            node_result = self.neo4j_client.execute_query(node_query)
            rel_result = self.neo4j_client.execute_query(rel_query)
            index_result = self.neo4j_client.execute_query(index_query)

            schema = {
                "node_labels": node_result[0]["labels"] if node_result else [],
                "relationship_types": rel_result[0]["relationships"] if rel_result else [],
                "indexes": index_result
            }

            return {
                "uri": "research://schema",
                "mimeType": "application/json",
                "text": json.dumps(schema, indent=2)
            }

        except Exception as e:
            return {
                "uri": "research://schema",
                "mimeType": "application/json",
                "text": json.dumps({"error": str(e)}, indent=2)
            }

    def close(self):
        """Close database connections."""
        self.neo4j_client.close()
