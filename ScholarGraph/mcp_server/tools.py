"""
MCP Tools for ScholarGraph.

These tools allow Claude Code to search and query the research knowledge graph.
"""

from typing import Dict, Any, List, Optional
import json

from core import Neo4jClient, GPURigClient
from embeddings import EmbeddingGenerator
from search import SemanticSearch, KeywordSearch, HybridSearch


class ScholarGraphTools:
    """Tools for interacting with ScholarGraph via MCP."""

    def __init__(self):
        """Initialize tools with database client."""
        self.neo4j_client = Neo4jClient()

    async def search_papers(
        self,
        query: str,
        mode: str = "hybrid",
        k: int = 5,
        filter_corpus: Optional[bool] = None,
        days_ago: Optional[int] = None,
        only_latest: bool = True
    ) -> Dict[str, Any]:
        """
        Search research papers in ScholarGraph.

        Args:
            query: Search query (e.g., "differential privacy in federated learning")
            mode: Search mode - "semantic", "keyword", or "hybrid"
            k: Number of results to return
            filter_corpus: If True, only search scoping review corpus; if False, exclude corpus
            days_ago: If specified, only return documents from last N days (default: all time)
            only_latest: If True, only search latest (non-superseded) documents (default: True)

        Returns:
            Dict with search results and metadata
        """
        try:
            # Build filter clause if needed
            filter_clause = ""
            if filter_corpus is True:
                filter_clause = "AND d.scoping_review_included = true"
            elif filter_corpus is False:
                filter_clause = "AND (d.scoping_review_included IS NULL OR d.scoping_review_included = false)"

            # Date filter for recency
            date_filter_clause = ""
            if days_ago is not None:
                date_filter_clause = f"AND date(datetime({{d.ingestion_date}})) > date() - duration('P{days_ago}D')"

            if mode == "semantic":
                gpu_client = GPURigClient()
                generator = EmbeddingGenerator(gpu_client=gpu_client)
                searcher = SemanticSearch(self.neo4j_client, generator)
                results = searcher.search_chunks(query, k=k, only_latest=only_latest)
            elif mode == "keyword":
                searcher = KeywordSearch(self.neo4j_client)
                results = searcher.search_chunks(query, k=k, only_latest=only_latest)
            else:  # hybrid
                gpu_client = GPURigClient()
                generator = EmbeddingGenerator(gpu_client=gpu_client)
                searcher = HybridSearch(self.neo4j_client, generator)
                results = searcher.search_chunks(query, k=k, only_latest=only_latest)

            # Apply corpus and date filters if needed
            if filter_clause or date_filter_clause:
                filtered_results = []
                for result in results:
                    doc_id = result.get('document_id')
                    if doc_id:
                        # Check if document matches filters
                        check_query = f"""
                        MATCH (d:Document {{document_id: $doc_id}})
                        WHERE 1=1 {filter_clause} {date_filter_clause}
                        RETURN d.document_id as id, d.title as title, d.ingestion_date as date
                        """
                        match = self.neo4j_client.execute_query(
                            check_query,
                            {'doc_id': doc_id}
                        )
                        if match:
                            filtered_results.append(result)
                results = filtered_results[:k]

            return {
                "success": True,
                "query": query,
                "mode": mode,
                "count": len(results),
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "mode": mode
            }

    async def get_paper_details(self, paper_title: str) -> Dict[str, Any]:
        """
        Get full details about a specific research paper.

        Args:
            paper_title: Title of the paper (partial match supported)

        Returns:
            Dict with paper metadata and chunks
        """
        try:
            query = """
            MATCH (d:Document)
            WHERE toLower(d.title) CONTAINS toLower($title)
            OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
            WITH d, collect({
                content: c.content,
                position: c.position,
                word_count: c.word_count
            }) as chunks
            RETURN d.document_id as document_id,
                   d.title as title,
                   d.authors as authors,
                   d.date as date,
                   d.document_type as document_type,
                   d.file_path as file_path,
                   d.paper_type as paper_type,
                   d.scoping_review_included as scoping_review_included,
                   d.scoping_study_id as scoping_study_id,
                   chunks
            ORDER BY size(chunks) DESC
            LIMIT 1
            """

            results = self.neo4j_client.execute_query(query, {"title": paper_title})

            if not results:
                return {
                    "success": False,
                    "error": f"Paper not found: {paper_title}"
                }

            paper = results[0]

            return {
                "success": True,
                "paper": paper
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def list_corpus_papers(self) -> Dict[str, Any]:
        """
        List all scoping review corpus papers.

        Returns:
            Dict with list of corpus papers
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

            return {
                "success": True,
                "count": len(results),
                "papers": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def compare_to_corpus_gaps(self, paper_title: str) -> Dict[str, Any]:
        """
        Compare a paper against research gaps identified in scoping review corpus.

        Args:
            paper_title: Title of paper to evaluate

        Returns:
            Dict with gap analysis results
        """
        try:
            # First, find the paper
            paper_query = """
            MATCH (d:Document)
            WHERE toLower(d.title) CONTAINS toLower($title)
            RETURN d.document_id as document_id,
                   d.title as title,
                   d.content as content
            LIMIT 1
            """

            paper_result = self.neo4j_client.execute_query(
                paper_query,
                {"title": paper_title}
            )

            if not paper_result:
                return {
                    "success": False,
                    "error": f"Paper not found: {paper_title}"
                }

            paper = paper_result[0]
            content = paper.get('content', '').lower()

            # Check for key research gaps
            gaps_addressed = {
                "fl_kg_llm_convergence": all([
                    "federated" in content or "fl" in content,
                    "knowledge graph" in content or "kg" in content,
                    "llm" in content or "language model" in content
                ]),
                "cefr_alignment": "cefr" in content or "common european framework" in content,
                "dimension_2_grounding": any([
                    "source verification" in content,
                    "kg integrity" in content,
                    "provenance" in content
                ]),
                "validation_metrics": any([
                    "validation" in content and "metric" in content,
                    "evaluation" in content
                ])
            }

            # Get corpus stats for comparison
            corpus_query = """
            MATCH (d:Document)
            WHERE d.scoping_review_included = true
            RETURN count(d) as total_corpus_papers
            """

            corpus_stats = self.neo4j_client.execute_query(corpus_query)

            return {
                "success": True,
                "paper": paper['title'],
                "gaps_addressed": gaps_addressed,
                "corpus_size": corpus_stats[0]['total_corpus_papers'] if corpus_stats else 0,
                "recommendation": self._generate_gap_recommendation(gaps_addressed)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get ScholarGraph database statistics.

        Returns:
            Dict with database stats
        """
        try:
            stats = self.neo4j_client.get_database_stats()

            # Add corpus-specific stats
            corpus_query = """
            MATCH (d:Document)
            WHERE d.scoping_review_included = true
            RETURN count(d) as corpus_papers,
                   count(DISTINCT d.scoping_study_id) as unique_study_ids
            """

            corpus_stats = self.neo4j_client.execute_query(corpus_query)

            if corpus_stats:
                stats['corpus'] = corpus_stats[0]

            return {
                "success": True,
                "stats": stats
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_gap_recommendation(self, gaps_addressed: Dict[str, bool]) -> str:
        """Generate recommendation based on which gaps are addressed."""
        if gaps_addressed.get("fl_kg_llm_convergence"):
            return "HIGHLY RELEVANT - Addresses FL+KG+LLM convergence gap (0% in corpus)"

        addressed_count = sum(1 for v in gaps_addressed.values() if v)

        if addressed_count >= 2:
            return "RELEVANT - Addresses multiple research gaps"
        elif addressed_count == 1:
            return "MODERATELY RELEVANT - Addresses one research gap"
        else:
            return "LIMITED RELEVANCE - Does not address identified research gaps"

    async def get_superseded_documents(self) -> Dict[str, Any]:
        """
        Get all superseded documents with their newer versions.

        Returns:
            Dict with list of superseded documents
        """
        try:
            query = """
            MATCH (old:Document)
            WHERE old.is_latest = false
            OPTIONAL MATCH (new:Document {document_id: old.superseded_by})
            RETURN old.document_id AS document_id,
                   old.title AS title,
                   old.superseded_at AS superseded_at,
                   new.document_id AS superseded_by_id,
                   new.title AS superseded_by_title,
                   new.ingestion_date AS newer_ingestion_date
            ORDER BY old.superseded_at DESC
            """

            results = self.neo4j_client.execute_query(query)

            return {
                "success": True,
                "count": len(results),
                "superseded": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_document_versions(self, document_title: str) -> Dict[str, Any]:
        """
        Get all versions of a document (superseded and current).

        Args:
            document_title: Title or partial title of document

        Returns:
            Dict with version chain
        """
        try:
            query = """
            MATCH (d:Document)
            WHERE toLower(d.title) CONTAINS toLower($title)
            MATCH (d)-[:SUPERSEDES*0..]-(version:Document)
            WITH DISTINCT version
            RETURN version.document_id AS document_id,
                   version.title AS title,
                   version.is_latest AS is_latest,
                   version.ingestion_date AS ingestion_date,
                   version.superseded_by AS superseded_by,
                   version.superseded_at AS superseded_at
            ORDER BY version.ingestion_date DESC
            """

            results = self.neo4j_client.execute_query(query, {"title": document_title})

            if not results:
                return {
                    "success": False,
                    "error": f"No versions found for: {document_title}"
                }

            return {
                "success": True,
                "count": len(results),
                "versions": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def close(self):
        """Close database connections."""
        self.neo4j_client.close()
