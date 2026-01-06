#!/usr/bin/env python
"""
ScholarGraph CLI - Research Knowledge Graph tool

Usage:
    rkg init                                 # Initialize database schema
    rkg ingest <path>                        # Ingest documents
    rkg search "<query>" [--mode MODE]       # Search knowledge graph
    rkg stats                                # Show database statistics
"""

import sys
import io

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import click
import json
from pathlib import Path

from core import Neo4jClient, GPURigClient
from graph import SchemaManager, QueryExecutor
from ingestion import BatchIngester
from embeddings import EmbeddingGenerator
from search import SemanticSearch, KeywordSearch, HybridSearch
from config import get_settings


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """ScholarGraph - Research Knowledge Graph CLI"""
    pass


@cli.command()
@click.option('--dimension', default=768, help='Vector embedding dimension')
def init(dimension):
    """Initialize database schema with indexes"""
    click.echo(f"Initializing ScholarGraph schema (dimension={dimension})...")

    try:
        with Neo4jClient() as client:
            manager = SchemaManager(client)
            results = manager.initialize_schema(vector_dimension=dimension)

            click.echo("✓ Schema initialized successfully!")
            click.echo(f"  Constraints: {len(results.get('constraints', []))}")
            click.echo(f"  Indexes: {len(results.get('property_indexes', []))}")
            click.echo(f"  Full-text indexes: {len(results.get('fulltext_indexes', []))}")
            click.echo(f"  Vector indexes: {len(results.get('vector_indexes', []))}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--embeddings/--no-embeddings', default=False, help='Generate embeddings')
@click.option('--update/--no-update', default=True, help='Update existing documents if modified (default: True)')
@click.option('--force', is_flag=True, default=False, help='Force re-ingestion of all documents')
def ingest(path, embeddings, update, force):
    """Ingest documents from a file or directory

    By default, existing documents are skipped unless modified.
    Use --force to re-ingest all documents regardless of modification time.
    Use --no-update to skip all existing documents without checking modification time.
    """
    path_obj = Path(path)

    click.echo(f"Ingesting: {path}")
    click.echo(f"Generate embeddings: {embeddings}")
    click.echo(f"Update existing: {update}")
    click.echo(f"Force re-ingestion: {force}")

    try:
        with Neo4jClient() as client:
            # Create ingester
            gpu_client = None
            if embeddings:
                try:
                    gpu_client = GPURigClient()
                except Exception as e:
                    click.echo(f"Warning: GPU client unavailable: {e}")

            ingester = BatchIngester(
                neo4j_client=client,
                gpu_client=gpu_client,
                generate_embeddings=embeddings,
                update_existing=update,
                force_reingestion=force
            )

            # Ingest single file or directory
            if path_obj.is_file():
                result = ingester.ingest_document(str(path_obj))
                if result:
                    click.echo(f"✓ Successfully ingested document")
                else:
                    click.echo(f"✗ Failed to ingest document", err=True)
            else:
                stats = ingester.ingest_directory(str(path_obj))
                click.echo(f"\n✓ Ingestion complete!")
                click.echo(f"  Processed: {stats['documents_processed']}")
                click.echo(f"  Updated: {stats['documents_updated']}")
                click.echo(f"  Skipped: {stats['documents_skipped']}")
                click.echo(f"  Failed: {stats['documents_failed']}")
                click.echo(f"  Chunks: {stats['chunks_created']}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('query')
@click.option('--mode', type=click.Choice(['semantic', 'keyword', 'hybrid']), default='hybrid')
@click.option('--k', default=10, help='Number of results')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text')
@click.option('--days-ago', type=int, default=None, help='Only return documents from last N days (default: all)')
@click.option('--all-versions', 'all_versions', is_flag=True, default=False, help='Include superseded document versions in results')
def search(query, mode, k, output_format, days_ago, all_versions):
    """Search the knowledge graph. Use --days-ago 7-30 for recent information to avoid outdated results."""
    try:
        with Neo4jClient() as client:
            # Create search instance based on mode
            if mode == 'semantic':
                # Use GPU rig for embeddings
                gpu_client = None
                try:
                    gpu_client = GPURigClient()
                except Exception as e:
                    click.echo(f"Warning: GPU client unavailable: {e}")
                generator = EmbeddingGenerator(gpu_client=gpu_client)
                searcher = SemanticSearch(client, generator)
                results = searcher.search_chunks(query, k=k)
            elif mode == 'keyword':
                searcher = KeywordSearch(client)
                results = searcher.search_chunks(query, k=k)
            else:  # hybrid
                # Use GPU rig for embeddings
                gpu_client = None
                try:
                    gpu_client = GPURigClient()
                except Exception as e:
                    click.echo(f"Warning: GPU client unavailable: {e}")
                generator = EmbeddingGenerator(gpu_client=gpu_client)
                searcher = HybridSearch(client, generator)
                results = searcher.search_chunks(query, k=k)

            # Apply date filter if specified
            if days_ago is not None:
                filtered_results = []
                cutoff_date = f"date() - duration('P{days_ago}D')"
                for result in results:
                    doc_id = result.get('document_id')
                    if doc_id:
                        check_query = f"""
                        MATCH (d:Document {{document_id: $doc_id}})
                        WHERE date(datetime({{d.ingestion_date}})) > {cutoff_date}
                        RETURN d.document_id as id, d.title as title, d.ingestion_date as date
                        """
                        match = client.execute_query(check_query, {'doc_id': doc_id})
                        if match:
                            filtered_results.append(result)
                results = filtered_results[:k]
                if k - len(results) > 0:
                    click.echo(f"Note: Found {len(filtered_results)} results from last {days_ago} days (requested {k})", err=True)

            # Output results
            if output_format == 'json':
                click.echo(json.dumps(results, indent=2))
            else:
                click.echo(f"\nSearch Results ({mode} mode): {len(results)} chunks\n")
                click.echo("=" * 80)

                for i, result in enumerate(results, 1):
                    score = result.get('score', result.get('hybrid_score', 0))
                    content = result.get('content', '')[:200]
                    doc_title = result.get('document_title', 'Unknown')

                    click.echo(f"\n{i}. Score: {score:.3f}")
                    click.echo(f"   Document: {doc_title}")
                    click.echo(f"   Content: {content}...")
                    click.echo("-" * 80)

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text')
@click.option('--type', 'doc_type', help='Filter by document type (pdf, markdown)')
def list(output_format, doc_type):
    """List all ingested documents"""
    try:
        with Neo4jClient() as client:
            # Query all documents
            if doc_type:
                query = """
                MATCH (d:Document {document_type: $doc_type})
                OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
                WITH d, count(c) AS chunk_count
                RETURN d.document_id AS id,
                       d.title AS title,
                       d.document_type AS type,
                       d.file_path AS path,
                       d.date AS date,
                       d.authors AS authors,
                       chunk_count,
                       d.created_at AS created
                ORDER BY d.created_at DESC
                """
                params = {"doc_type": doc_type}
            else:
                query = """
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[:CONTAINS]->(c:Chunk)
                WITH d, count(c) AS chunk_count
                RETURN d.document_id AS id,
                       d.title AS title,
                       d.document_type AS type,
                       d.file_path AS path,
                       d.date AS date,
                       d.authors AS authors,
                       chunk_count,
                       d.created_at AS created
                ORDER BY d.created_at DESC
                """
                params = {}

            results = client.execute_read(query, parameters=params)

            if output_format == 'json':
                click.echo(json.dumps(results, indent=2))
            else:
                click.echo(f"\n{'='*80}")
                click.echo(f"Ingested Documents ({len(results)} total)")
                click.echo(f"{'='*80}\n")

                for i, doc in enumerate(results, 1):
                    click.echo(f"{i}. {doc.get('title', 'Untitled')}")
                    click.echo(f"   Type: {doc.get('type', 'unknown')}")
                    click.echo(f"   Chunks: {doc.get('chunk_count', 0)}")
                    if doc.get('date'):
                        click.echo(f"   Date: {doc.get('date')}")
                    if doc.get('authors'):
                        click.echo(f"   Authors: {', '.join(doc.get('authors', []))}")
                    click.echo(f"   Path: {doc.get('path', 'N/A')}")
                    click.echo(f"   Ingested: {doc.get('created', 'N/A')[:10]}")
                    click.echo("-" * 80)

                if len(results) == 0:
                    click.echo("No documents found. Use 'rkg ingest <path>' to add documents.")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
def stats():
    """Show database statistics"""
    try:
        with Neo4jClient() as client:
            executor = QueryExecutor(client)
            stats = executor.get_database_statistics()

            click.echo("\n" + "=" * 80)
            click.echo("ScholarGraph Database Statistics")
            click.echo("=" * 80)

            # Nodes
            click.echo("\nNodes:")
            for label, count in stats.get('nodes', {}).items():
                click.echo(f"  {label}: {count}")

            # Relationships
            click.echo("\nRelationships:")
            for rel_type, count in stats.get('relationships', {}).items():
                click.echo(f"  {rel_type}: {count}")

            # Documents
            doc_stats = stats.get('documents', {})
            if doc_stats:
                click.echo("\nDocument Statistics:")
                for key, value in doc_stats.items():
                    click.echo(f"  {key}: {value}")

            # Chunks
            chunk_stats = stats.get('chunks', {})
            if chunk_stats:
                click.echo("\nChunk Statistics:")
                for key, value in chunk_stats.items():
                    if isinstance(value, float):
                        click.echo(f"  {key}: {value:.1f}")
                    else:
                        click.echo(f"  {key}: {value}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()



@cli.command()
def supersession_summary():
    """Show summary of document supersession status."""
    try:
        with Neo4jClient() as client:
            from ingestion.supersession_detector import SupersessionDetector
            
            detector = SupersessionDetector(client)
            summary = detector.get_supersession_summary()

            click.echo("\n" + "=" * 60)            
            click.echo("Document Supersession Summary")
            click.echo("=" * 60)
            click.echo(f"Total documents: {summary.get('total_documents', 0)}")
            click.echo(f"Latest versions: {summary.get('latest_versions', 0)}")
            click.echo(f"Superseded versions: {summary.get('superseded_versions', 0)}")
            click.echo("=" * 60)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option('--dry-run', is_flag=True, help='Preview changes without applying them')
def detect_supersessions(dry_run):
    """Retroactively detect supersession relationships among existing documents."""
    try:
        with Neo4jClient() as client:
            from ingestion.supersession_detector import SupersessionDetector
            
            detector = SupersessionDetector(client)
            click.echo("Scanning documents for supersession relationships...")
            results = detector.retroactively_detect_supersessions(dry_run=dry_run)
            
            click.echo("\n" + "=" * 60)
            click.echo(f"\nDocuments checked:{results['documents_checked']}")
            click.echo(f"Supersessions found:{results['supersessions_found']}")

            if results['superseded_documents']:
                click.echo("\nSuperseded documents:")
                for s in results['superseded_documents'][:10]:
                    click.echo(f"  - '{s['older']}' superseded by '{s['newer']}' ({s['reason']})")

            if dry_run:
                click.echo("\n[DRY RUN]")
            else:
                click.echo("\n[Changes applied]")          
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument('older_doc_id')
@click.argument('newer_doc_id')
@click.option('--reason', default='manual', help='Reason for supersession')
def mark_superseded(older_doc_id, newer_doc_id, reason):
    """Manually mark a document as superseded by another."""
    try:
        with Neo4jClient() as client:
            from graph.temporal_schema import TemporalSchemaManager
            
            manager = TemporalSchemaManager(client)
            success = manager.mark_document_superseded(
                document_id=older_doc_id,
                superseded_by=newer_doc_id
            )
            manager.create_supersedes_relationship(
                newer_document_id=newer_doc_id,
                older_document_id=older_doc_id,
                reason=reason
            )
            
            if success:
                click.echo(f"Document marked as superseded")
            else:
                click.echo("Failed to mark supersession", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
def init_temporal():
    """Initialize temporal versioning schema."""
    try:
        with Neo4jClient() as client:
            from graph.temporal_schema import TemporalSchemaManager
            
            manager = TemporalSchemaManager(client)
            results = manager.initialize_temporal_schema()
            
            click.echo("Temporal schema initialized:")
            click.echo(f"  Properties added to {results['properties_added']} documents")
            click.echo(f"  Indexes created: {results['indexes_created']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == '__main__':
    cli()
