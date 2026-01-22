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
        only_latest: bool = True,
        content_mode: str = "preview"
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
            content_mode: How to handle content - 'preview' (800 chars), 'summary', or 'full' (default: 'preview')

        Returns:
            Dict with search results and metadata
        """
        try:
            # Validate content_mode
            valid_modes = ["preview", "summary", "full"]
            if content_mode not in valid_modes:
                return {
                    "success": False,
                    "error": f"Invalid content_mode '{content_mode}'. Must be one of: {valid_modes}",
                    "query": query,
                    "mode": mode
                }

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
                results = searcher.search_chunks(query, k=k, only_latest=only_latest, content_mode=content_mode)
            elif mode == "keyword":
                searcher = KeywordSearch(self.neo4j_client)
                results = searcher.search_chunks(query, k=k, only_latest=only_latest)
            else:  # hybrid
                gpu_client = GPURigClient()
                generator = EmbeddingGenerator(gpu_client=gpu_client)
                searcher = HybridSearch(self.neo4j_client, generator)
                results = searcher.search_chunks(query, k=k, only_latest=only_latest, content_mode=content_mode)

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
                "content_mode": content_mode,
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


    async def link_documents(
        self,
        older_doc_id: str,
        newer_doc_id: str,
        reason: str = "manual_link"
    ) -> Dict[str, Any]:
        """
        Link two documents by creating a SUPERSEDES relationship.

        Args:
            older_doc_id: ID of the older (superseded) document
            newer_doc_id: ID of the newer document
            reason: Reason for the link (default: "manual_link")

        Returns:
            Dict with success status and details
        """
        try:
            from graph.temporal_schema import TemporalSchemaManager
            from datetime import datetime

            # Verify both documents exist
            check_query = """
            MATCH (d:Document)
            WHERE d.document_id IN (, )
            RETURN d.document_id as id, d.title as title
            """
            results = self.neo4j_client.execute_query(
                check_query,
                {"older_id": older_doc_id, "newer_id": newer_doc_id}
            )

            if len(results) < 2:
                found_ids = [r['id'] for r in results]
                missing = []
                if older_doc_id not in found_ids:
                    missing.append(f"older_doc_id: {older_doc_id}")
                if newer_doc_id not in found_ids:
                    missing.append(f"newer_doc_id: {newer_doc_id}")
                return {
                    "success": False,
                    "error": f"Documents not found: {', '.join(missing)}"
                }

            # Create the supersession relationship
            temporal_manager = TemporalSchemaManager(self.neo4j_client)

            # Mark older as superseded
            success = temporal_manager.mark_document_superseded(
                document_id=older_doc_id,
                superseded_by=newer_doc_id
            )

            if not success:
                return {
                    "success": False,
                    "error": "Failed to mark document as superseded"
                }

            # Create SUPERSEDES relationship
            success = temporal_manager.create_supersedes_relationship(
                newer_document_id=newer_doc_id,
                older_document_id=older_doc_id,
                reason=reason,
                timestamp=datetime.now().isoformat()
            )

            if success:
                # Get titles for response
                older_title = next((r['title'] for r in results if r['id'] == older_doc_id), "Unknown")
                newer_title = next((r['title'] for r in results if r['id'] == newer_doc_id), "Unknown")

                return {
                    "success": True,
                    "message": f"Linked '{newer_title}' → '{older_title}'",
                    "older_document": {"id": older_doc_id, "title": older_title},
                    "newer_document": {"id": newer_doc_id, "title": newer_title},
                    "relationship": "SUPERSEDES",
                    "reason": reason
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create SUPERSEDES relationship"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def check_sessions_ingested(
        self,
        sessions_dir: str = r"C:\projects\AgenticAIpkg\docs\knowledge\sessions",
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Check which session files are ingested into ScholarGraph.

        Fast comparison between session files in directory and documents in Neo4j.

        Args:
            sessions_dir: Path to sessions directory (default: AgenticAIpkg sessions)
            limit: Maximum number of session files to check (default: 100)

        Returns:
            Dict with ingested, missing, and stats
        """
        import os
        from pathlib import Path

        try:
            # Get session files from directory
            sessions_path = Path(sessions_dir)
            if not sessions_path.exists():
                return {
                    "success": False,
                    "error": f"Sessions directory not found: {sessions_dir}"
                }

            session_files = list(sessions_path.glob("*.md"))
            session_files = sorted(session_files, key=lambda x: x.name, reverse=True)[:limit]

            # Get all file_paths from Neo4j in one query
            query = """
            MATCH (d:Document)
            WHERE d.file_path IS NOT NULL
               AND (d.is_latest = true OR d.is_latest IS NULL)
            RETURN d.file_path as file_path, d.title as title
            """
            results = self.neo4j_client.execute_query(query)

            # Create set of extracted filenames from Neo4j file_paths
            # File paths in Neo4j are like: "...sessions==filename.md"
            ingested_basenames = set()
            for r in results:
                fp = r.get('file_path', '')
                if '==' in fp:
                    # Extract filename after ==
                    basename = fp.split('==')[-1].lower()
                    ingested_basenames.add(basename)
                elif fp:
                    # Fallback: get basename from path
                    basename = Path(fp).name.lower()
                    ingested_basenames.add(basename)

            # Compare
            ingested = []
            missing = []

            for sf in session_files:
                basename = sf.name.lower()
                if basename in ingested_basenames:
                    ingested.append(sf.name)
                else:
                    missing.append(sf.name)

            return {
                "success": True,
                "stats": {
                    "total_sessions": len(session_files),
                    "ingested": len(ingested),
                    "missing": len(missing),
                    "coverage_percent": round(100 * len(ingested) / len(session_files), 1) if session_files else 0
                },
                "ingested": ingested[:50],  # Limit response size
                "ingested_truncated": len(ingested) > 50,
                "missing": missing[:50],
                "missing_truncated": len(missing) > 50,
                "sessions_directory": str(sessions_dir)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_recent_sessions(
        self,
        days: int = 7,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get recently ingested session documents.

        Args:
            days: Number of days to look back (default: 7)
            limit: Maximum results to return (default: 20)

        Returns:
            Dict with recent session documents
        """
        try:
            # Get sessions sorted by ingestion_date, we'll filter in Python
            # This avoids Cypher datetime parsing issues
            query = """
            MATCH (d:Document)
            WHERE d.file_path CONTAINS 'sessions'
               AND (d.is_latest = true OR d.is_latest IS NULL)
               AND d.ingestion_date IS NOT NULL
            RETURN d.title as title,
                   d.file_path as file_path,
                   d.ingestion_date as date,
                   d.document_type as doc_type
            ORDER BY d.ingestion_date DESC
            LIMIT $limit
            """

            results = self.neo4j_client.execute_query(
                query,
                parameters={"limit": limit * 2}  # Get more to account for date filtering
            )

            # Filter by date in Python
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            sessions = []
            for r in results:
                date_str = r.get('date', '')
                try:
                    # Parse the ISO datetime string
                    if '.' in date_str:
                        # Strip microseconds for parsing
                        date_str = date_str.split('.')[0]
                    doc_date = datetime.fromisoformat(date_str)

                    if doc_date > cutoff_date:
                        fp = r.get('file_path', '')
                        if '==' in fp:
                            filename = fp.split('==')[-1]
                        else:
                            filename = fp.split('/')[-1].split('\\')[-1]
                        sessions.append({
                            "filename": filename,
                            "title": r.get('title', '')[:80],
                            "date": r.get('date', ''),
                            "doc_type": r.get('doc_type', '')
                        })
                except (ValueError, TypeError):
                    # Skip if date can't be parsed
                    continue

            return {
                "success": True,
                "days": days,
                "count": len(sessions),
                "sessions": sessions
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def ingest_document(
        self,
        file_path: str,
        document_type: Optional[str] = None,
        force_reingestion: bool = False
    ) -> Dict[str, Any]:
        """
        Ingest a single document into ScholarGraph.

        Supports PDF and Markdown files. Automatically detects type if not specified.
        Handles chunking, embedding generation, and topic extraction.

        Args:
            file_path: Path to the document file (PDF or Markdown)
            document_type: Type of document - 'pdf', 'markdown', or None (auto-detect)
            force_reingestion: If True, re-ingest even if document exists and hasn't changed

        Returns:
            Dict with ingestion status and details
        """
        import os
        from pathlib import Path
        from datetime import datetime
        from .ingestion.batch_ingester import BatchIngester

        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }

            # Auto-detect document type if not specified
            if document_type is None:
                if path.suffix.lower() == '.pdf':
                    document_type = 'pdf'
                elif path.suffix.lower() in ['.md', '.markdown']:
                    document_type = 'markdown'
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported file type: {path.suffix}. Supported: .pdf, .md, .markdown"
                    }

            # Create batch ingester with appropriate settings
            gpu_client = GPURigClient()
            ingester = BatchIngester(
                neo4j_client=self.neo4j_client,
                gpu_client=gpu_client,
                generate_embeddings=True,
                update_existing=True,
                force_reingestion=force_reingestion,
                detect_supersession=True
            )

            # Check if document exists before ingestion
            absolute_path = str(path.absolute())
            existing_doc = ingester.check_existing_document(absolute_path)

            action_taken = "created"
            if existing_doc and not force_reingestion:
                if ingester.should_update_document(absolute_path, existing_doc):
                    action_taken = "updated"
                else:
                    return {
                        "success": True,
                        "message": "Document already exists and is up to date",
                        "document_id": existing_doc['document_id'],
                        "title": existing_doc.get('title', ''),
                        "action": "skipped",
                        "file_path": absolute_path
                    }

            # Ingest the document
            document_id = ingester.ingest_document(str(path), document_type=document_type)

            if document_id:
                stats = ingester.get_statistics()

                # Get the document details
                doc_query = """
                MATCH (d:Document {document_id: $doc_id})
                RETURN d.title as title, d.document_type as doc_type,
                       size((d)-[:CONTAINS]->(:Chunk)) as chunk_count
                """
                doc_info = self.neo4j_client.execute_query(doc_query, {"doc_id": document_id})
                doc_info = doc_info[0] if doc_info else {}

                return {
                    "success": True,
                    "document_id": document_id,
                    "title": doc_info.get('title', path.name),
                    "document_type": doc_info.get('doc_type', document_type),
                    "chunk_count": doc_info.get('chunk_count', 0),
                    "action": action_taken,
                    "file_path": absolute_path,
                    "stats": {
                        "chunks_created": stats.get('chunks_created', 0),
                        "embeddings_generated": stats.get('embeddings_generated', 0),
                        "topics_created": stats.get('topics_created', 0),
                        "documents_superseded": stats.get('documents_superseded', 0)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to ingest document",
                    "file_path": absolute_path,
                    "errors": ingester.stats.get('errors', [])
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    async def ingest_batch(
        self,
        directory: str,
        file_pattern: str = "*.md",
        recursive: bool = False,
        force_reingestion: bool = False,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ingest multiple documents from a directory into ScholarGraph.

        Args:
            directory: Path to directory containing documents
            file_pattern: Glob pattern for files (default: "*.md", also supports "*.pdf")
            recursive: If True, search recursively in subdirectories (default: False)
            force_reingestion: If True, re-ingest all files (default: False)
            limit: Maximum number of files to process (default: all)

        Returns:
            Dict with batch ingestion results and statistics
        """
        from pathlib import Path
        from .ingestion.batch_ingester import BatchIngester

        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory}"
                }

            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {directory}"
                }

            # Find matching files
            if recursive:
                pattern = f"**/{file_pattern}" if not file_pattern.startswith("**") else file_pattern
            else:
                pattern = file_pattern

            all_files = list(dir_path.glob(pattern))
            all_files = [f for f in all_files if f.is_file()]

            # Apply limit if specified
            if limit and limit > 0:
                all_files = all_files[:limit]

            if not all_files:
                return {
                    "success": True,
                    "message": f"No files found matching pattern '{file_pattern}' in {directory}",
                    "files_processed": 0,
                    "results": []
                }

            # Create batch ingester
            gpu_client = GPURigClient()
            ingester = BatchIngester(
                neo4j_client=self.neo4j_client,
                gpu_client=gpu_client,
                generate_embeddings=True,
                update_existing=True,
                force_reingestion=force_reingestion,
                detect_supersession=True
            )

            # Process each file
            results = []
            for file_path in all_files:
                # Determine document type
                if file_path.suffix.lower() == '.pdf':
                    doc_type = 'pdf'
                elif file_path.suffix.lower() in ['.md', '.markdown']:
                    doc_type = 'markdown'
                else:
                    results.append({
                        "file_path": str(file_path),
                        "success": False,
                        "error": f"Unsupported file type: {file_path.suffix}"
                    })
                    continue

                # Check existing
                absolute_path = str(file_path.absolute())
                existing_doc = ingester.check_existing_document(absolute_path)

                action = "skipped"
                if existing_doc and not force_reingestion:
                    if not ingester.should_update_document(absolute_path, existing_doc):
                        results.append({
                            "file_path": str(file_path.name),
                            "document_id": existing_doc['document_id'],
                            "success": True,
                            "action": "skipped",
                            "reason": "Already up to date"
                        })
                        continue

                # Ingest
                document_id = ingester.ingest_document(str(file_path), document_type=doc_type)

                if document_id:
                    # Get doc info
                    doc_query = """
                    MATCH (d:Document {document_id: $doc_id})
                    RETURN d.title as title, size((d)-[:CONTAINS]->(:Chunk)) as chunk_count
                    """
                    doc_info = self.neo4j_client.execute_query(doc_query, {"doc_id": document_id})
                    doc_info = doc_info[0] if doc_info else {}

                    action = "updated" if existing_doc else "created"
                    results.append({
                        "file_path": str(file_path.name),
                        "document_id": document_id,
                        "title": doc_info.get('title', file_path.name),
                        "chunk_count": doc_info.get('chunk_count', 0),
                        "success": True,
                        "action": action
                    })
                else:
                    results.append({
                        "file_path": str(file_path.name),
                        "success": False,
                        "error": "Failed to ingest",
                        "action": "failed"
                    })

            # Compile summary
            stats = ingester.get_statistics()

            return {
                "success": True,
                "directory": str(dir_path),
                "file_pattern": file_pattern,
                "files_found": len(all_files),
                "summary": {
                    "created": stats.get('documents_processed', 0),
                    "updated": stats.get('documents_updated', 0),
                    "skipped": stats.get('documents_skipped', 0),
                    "failed": stats.get('documents_failed', 0),
                    "superseded": stats.get('documents_superseded', 0)
                },
                "details": {
                    "chunks_created": stats.get('chunks_created', 0),
                    "embeddings_generated": stats.get('embeddings_generated', 0),
                    "topics_created": stats.get('topics_created', 0)
                },
                "results": results[:50],  # Limit response size
                "results_truncated": len(results) > 50,
                "errors": stats.get('errors', [])[:10]  # Limit errors shown
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "directory": directory
            }

    async def delete_document(
        self,
        document_id: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a document and all its chunks from ScholarGraph.

        Args:
            document_id: ID of the document to delete
            file_path: Alternative: file path to find and delete document

        Returns:
            Dict with deletion status
        """
        try:
            if not document_id and not file_path:
                return {
                    "success": False,
                    "error": "Either document_id or file_path must be provided"
                }

            # Find document by file_path if document_id not provided
            if file_path and not document_id:
                query = """
                MATCH (d:Document {file_path: $file_path})
                RETURN d.document_id as document_id, d.title as title
                """
                results = self.neo4j_client.execute_query(query, {"file_path": file_path})
                if not results:
                    return {
                        "success": False,
                        "error": f"Document not found with file_path: {file_path}"
                    }
                document_id = results[0]['document_id']
                deleted_title = results[0]['title']
            else:
                # Get title for response
                title_query = """
                MATCH (d:Document {document_id: $doc_id})
                RETURN d.title as title
                """
                title_results = self.neo4j_client.execute_query(title_query, {"doc_id": document_id})
                deleted_title = title_results[0]['title'] if title_results else "Unknown"

            # Delete document and its chunks
            query = """
            MATCH (d:Document {document_id: $document_id})
            OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
            OPTIONAL MATCH (d)-[r:DISCUSSES_TOPIC]->()
            DETACH DELETE c, r, d
            RETURN count(*) as deleted_count
            """
            result = self.neo4j_client.execute_query(query, {"document_id": document_id})

            return {
                "success": True,
                "message": f"Deleted document: {deleted_title}",
                "document_id": document_id,
                "title": deleted_title
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def close(self):
        """Close database connections."""
        self.neo4j_client.close()
