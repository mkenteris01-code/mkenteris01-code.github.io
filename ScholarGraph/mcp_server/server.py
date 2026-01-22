"""
ScholarGraph MCP Server

Exposes ScholarGraph research knowledge graph to Claude Code via MCP protocol.
Runs locally on port 8100 with access to Neo4j database.
"""

import asyncio
import json
import logging
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource

from .tools import ScholarGraphTools
from .resources import ScholarGraphResources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scholargraph-mcp")


# Initialize server
app = Server("scholargraph")

# Initialize tools and resources
tools = ScholarGraphTools()
resources = ScholarGraphResources()


# =============================================================================
# UTILITIES
# =============================================================================
def _to_json(obj: dict, compact: bool = True) -> str:
    """
    Convert dict to JSON with optional compact formatting.

    Args:
        obj: Dictionary to convert
        compact: If True, use compact separators (no whitespace)

    Returns:
        JSON string
    """
    if compact:
        return json.dumps(obj, separators=(',', ':'))
    return json.dumps(obj, indent=2)


# =============================================================================
# TOOLS: Claude Code can call these directly
# =============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_papers",
            description="Search research papers using semantic, keyword, or hybrid search. "
                       "Supports filtering by scoping review corpus and by recency (days_ago). "
                       "Returns optimized content previews by default (800 chars). Use content_mode='full' for complete content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'differential privacy in federated learning')"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["semantic", "keyword", "hybrid"],
                        "description": "Search mode (default: hybrid)",
                        "default": "hybrid"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    },
                    "filter_corpus": {
                        "type": "boolean",
                        "description": "If true, search only corpus papers; if false, exclude corpus",
                        "default": None
                    },
                    "days_ago": {
                        "type": "integer",
                        "description": "Only return documents from the last N days (default: all time). Use 7-30 for recent info.",
                        "default": None
                    },
                    "content_mode": {
                        "type": "string",
                        "enum": ["preview", "summary", "full"],
                        "description": "How much content to return: 'preview' (800 chars, default), 'summary' (chunk summaries only), 'full' (complete content)",
                        "default": "preview"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_paper_details",
            description="Get full details about a specific research paper by title (partial match supported).",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_title": {
                        "type": "string",
                        "description": "Title of the paper (partial match)"
                    }
                },
                "required": ["paper_title"]
            }
        ),
        Tool(
            name="list_corpus_papers",
            description="List all scoping review corpus papers with their study IDs.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="compare_to_corpus_gaps",
            description="Compare a paper against research gaps identified in the scoping review. "
                       "Checks for FL+KG+LLM convergence, CEFR alignment, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_title": {
                        "type": "string",
                        "description": "Title of paper to evaluate"
                    }
                },
                "required": ["paper_title"]
            }
        ),
        Tool(
            name="get_database_stats",
            description="Get ScholarGraph database statistics including node counts, corpus size, etc.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="check_sessions_ingested",
            description="Check which session files from your sessions directory are ingested into ScholarGraph. "
                       "Fast comparison returns stats on ingested vs missing sessions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sessions_dir": {
                        "type": "string",
                        "description": "Path to sessions directory (default: AgenticAIpkg sessions)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of session files to check (default: 100)",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="get_recent_sessions",
            description="Get recently ingested session documents from ScholarGraph. "
                       "Shows sessions added in the last N days.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 7)",
                        "default": 7
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="link_documents",
            description="Link two documents by creating a SUPERSEDES relationship (newer supersedes older).",
            inputSchema={
                "type": "object",
                "properties": {
                    "older_doc_id": {
                        "type": "string",
                        "description": "ID of the older (superseded) document"
                    },
                    "newer_doc_id": {
                        "type": "string",
                        "description": "ID of the newer document"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the link (default: 'manual_link')"
                    }
                },
                "required": ["older_doc_id", "newer_doc_id"]
            }
        ),
        Tool(
            name="ingest_document",
            description="Ingest a single document (PDF or Markdown) into ScholarGraph. "
                       "Automatically detects file type, chunks content, generates embeddings, and extracts topics. "
                       "Use this to add new research papers, session notes, or any documentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Full path to the document file (.pdf, .md, .markdown)"
                    },
                    "document_type": {
                        "type": "string",
                        "enum": ["pdf", "markdown"],
                        "description": "Document type (auto-detected if not specified)"
                    },
                    "force_reingestion": {
                        "type": "boolean",
                        "description": "Force re-ingestion even if document exists and hasn't changed (default: false)",
                        "default": False
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="ingest_batch",
            description="Ingest multiple documents from a directory into ScholarGraph. "
                       "Useful for batch processing session files, papers, or document collections. "
                       "Supports glob patterns and recursive directory search.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Path to directory containing documents"
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Glob pattern for files (default: '*.md', also supports '*.pdf', '*.*')",
                        "default": "*.md"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Search recursively in subdirectories (default: false)",
                        "default": False
                    },
                    "force_reingestion": {
                        "type": "boolean",
                        "description": "Force re-ingestion of all files (default: false)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of files to process (default: all)"
                    }
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="delete_document",
            description="Delete a document and all its chunks from ScholarGraph. "
                       "Use with caution - this cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID of the document to delete"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Alternative: file path to find and delete document"
                    }
                }
            }
        ),
        Tool(
            name="ingest_missing",
            description="Find and ingest missing files from a folder into ScholarGraph. "
                       "Compares folder contents with Neo4j and ingests only missing or updated files. "
                       "Use: 'ingest missing from <folder> by date <YYYY-MM-DD>'",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "description": "Path to folder containing documents (e.g., 'sessions', 'scripts', 'papers')"
                    },
                    "date": {
                        "type": "string",
                        "description": "Filter files by date prefix (e.g., '2026-01-18')"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Files from this date onwards (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Files up to this date (YYYY-MM-DD)"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force re-ingest all files (default: false)",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="search_by_tags",
            description="Find documents by tags/topics. Uses the DISCUSSES_TOPIC relationship to find "
                       "documents that discuss specific topics. Can match ANY tag (default) or ALL tags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of topic/tag names to search for (e.g., ['federated learning', 'privacy'])"
                    },
                    "match_all": {
                        "type": "boolean",
                        "description": "If true, only return documents that match ALL tags. If false, match ANY tag (default)",
                        "default": False
                    },
                    "k": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 20)",
                        "default": 20
                    }
                },
                "required": ["tags"]
            }
        ),
        Tool(
            name="get_document_timeline",
            description="Get a chronological timeline view of documents ordered by ingestion date. "
                       "Useful for understanding the progression of work, research, or project phases.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 30, use 0 for all time)",
                        "default": 30
                    },
                    "document_type": {
                        "type": "string",
                        "description": "Filter by document type ('pdf', 'markdown', or null for all)",
                        "enum": ["pdf", "markdown"]
                    },
                    "include_chunks": {
                        "type": "boolean",
                        "description": "If true, include chunk count for each document (default: false)",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="search_content_keywords",
            description="Full-text keyword search within document content. Searches for keywords within "
                       "document titles, abstracts, and chunk content. More comprehensive than semantic search "
                       "for finding specific terms.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keywords to search for (e.g., ['Neo4j', 'GraphRAG'])"
                    },
                    "match_all": {
                        "type": "boolean",
                        "description": "If true, all keywords must be present. If false, any keyword can match (default)",
                        "default": False
                    },
                    "k": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 20)",
                        "default": 20
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "If true, search is case-sensitive (default: false)",
                        "default": False
                    }
                },
                "required": ["keywords"]
            }
        ),
        Tool(
            name="get_document_network",
            description="Show the document network - related documents connected through relationships. "
                       "Finds documents connected via SUPERSEDES relationships (version history), "
                       "shared topics (DISCUSSES_TOPIC), and shared concepts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID of the central document"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "How many hops to explore (default: 2)",
                        "default": 2
                    },
                    "include_superseded": {
                        "type": "boolean",
                        "description": "Whether to include superseded documents (default: true)",
                        "default": True
                    }
                },
                "required": ["document_id"]
            }
        ),
        Tool(
            name="get_phase_documents",
            description="Get documents related to a specific project phase. Phases are extracted from "
                       "document titles that follow naming conventions like 'Phase-1', 'Phase-2A', 'Phase-3'. "
                       "Returns documents grouped by sub-phase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "description": "Phase identifier (e.g., '1', '2A', '3', or 'Phase-1')"
                    },
                    "include_details": {
                        "type": "boolean",
                        "description": "If true, include chunk counts and metadata (default: true)",
                        "default": True
                    }
                },
                "required": ["phase"]
            }
        ),
        Tool(
            name="summarize_recent_work",
            description="Generate a summary of recent work from session documents. Aggregates recent documents, "
                       "extracts key topics, and provides a structured summary of work done in the specified time period.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 7)",
                        "default": 7
                    },
                    "include_topics": {
                        "type": "boolean",
                        "description": "If true, extract and list topics discussed (default: true)",
                        "default": True
                    },
                    "max_documents": {
                        "type": "integer",
                        "description": "Maximum documents to analyze (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="merge_duplicates",
            description="Find and optionally merge duplicate documents. Identifies documents that may be "
                       "duplicates based on similar titles and file paths. Default is dry_run=True to preview "
                       "before actually merging.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title_similarity": {
                        "type": "number",
                        "description": "Similarity threshold for title matching 0.0-1.0 (default: 0.9)",
                        "default": 0.9
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, only report potential duplicates. If false, actually merge them (default: true)",
                        "default": True
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_papers":
            result = await tools.search_papers(
                query=arguments["query"],
                mode=arguments.get("mode", "hybrid"),
                k=arguments.get("k", 5),
                filter_corpus=arguments.get("filter_corpus"),
                days_ago=arguments.get("days_ago"),
                content_mode=arguments.get("content_mode", "preview")
            )
        elif name == "get_paper_details":
            result = await tools.get_paper_details(
                paper_title=arguments["paper_title"]
            )
        elif name == "list_corpus_papers":
            result = await tools.list_corpus_papers()
        elif name == "compare_to_corpus_gaps":
            result = await tools.compare_to_corpus_gaps(
                paper_title=arguments["paper_title"]
            )
        elif name == "get_database_stats":
            result = await tools.get_database_stats()
        elif name == "check_sessions_ingested":
            result = await tools.check_sessions_ingested(
                sessions_dir=arguments.get("sessions_dir", r"C:\projects\AgenticAIpkg\docs\knowledge\sessions"),
                limit=arguments.get("limit", 100)
            )
        elif name == "get_recent_sessions":
            result = await tools.get_recent_sessions(
                days=arguments.get("days", 7),
                limit=arguments.get("limit", 20)
            )
        elif name == "link_documents":
            result = await tools.link_documents(
                older_doc_id=arguments["older_doc_id"],
                newer_doc_id=arguments["newer_doc_id"],
                reason=arguments.get("reason", "manual_link")
            )
        elif name == "ingest_document":
            result = await tools.ingest_document(
                file_path=arguments["file_path"],
                document_type=arguments.get("document_type"),
                force_reingestion=arguments.get("force_reingestion", False)
            )
        elif name == "ingest_batch":
            result = await tools.ingest_batch(
                directory=arguments["directory"],
                file_pattern=arguments.get("file_pattern", "*.md"),
                recursive=arguments.get("recursive", False),
                force_reingestion=arguments.get("force_reingestion", False),
                limit=arguments.get("limit")
            )
        elif name == "delete_document":
            result = await tools.delete_document(
                document_id=arguments.get("document_id"),
                file_path=arguments.get("file_path")
            )
        elif name == "ingest_missing":
            result = await tools.ingest_missing_sessions(
                sessions_dir=arguments.get("folder", r"C:\projects\AgenticAIpkg\docs\knowledge\sessions"),
                date_prefix=arguments.get("date"),
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
                force_reingestion=arguments.get("force", False)
            )
        elif name == "search_by_tags":
            result = await tools.search_by_tags(
                tags=arguments.get("tags", []),
                match_all=arguments.get("match_all", False),
                k=arguments.get("k", 20)
            )
        elif name == "get_document_timeline":
            result = await tools.get_document_timeline(
                days=arguments.get("days", 30),
                document_type=arguments.get("document_type"),
                include_chunks=arguments.get("include_chunks", False)
            )
        elif name == "search_content_keywords":
            result = await tools.search_content_keywords(
                keywords=arguments.get("keywords", []),
                match_all=arguments.get("match_all", False),
                k=arguments.get("k", 20),
                case_sensitive=arguments.get("case_sensitive", False)
            )
        elif name == "get_document_network":
            result = await tools.get_document_network(
                document_id=arguments.get("document_id", ""),
                depth=arguments.get("depth", 2),
                include_superseded=arguments.get("include_superseded", True)
            )
        elif name == "get_phase_documents":
            result = await tools.get_phase_documents(
                phase=arguments.get("phase", ""),
                include_details=arguments.get("include_details", True)
            )
        elif name == "summarize_recent_work":
            result = await tools.summarize_recent_work(
                days=arguments.get("days", 7),
                include_topics=arguments.get("include_topics", True),
                max_documents=arguments.get("max_documents", 50)
            )
        elif name == "merge_duplicates":
            result = await tools.merge_duplicates(
                title_similarity=arguments.get("title_similarity", 0.9),
                dry_run=arguments.get("dry_run", True)
            )
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}

        # Format result as compact JSON (saves ~20% space)
        result_text = _to_json(result, compact=True)

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        error_result = {"success": False, "error": str(e)}
        return [TextContent(type="text", text=_to_json(error_result, compact=True))]


# =============================================================================
# RESOURCES: Claude Code can browse these like files
# =============================================================================

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="research://papers",
            name="All Research Papers",
            description="List of all papers in ScholarGraph",
            mimeType="application/json"
        ),
        Resource(
            uri="research://corpus",
            name="Scoping Review Corpus",
            description="The papers from the scoping review corpus",
            mimeType="application/json"
        ),
        Resource(
            uri="research://gaps",
            name="Research Gaps",
            description="Identified research gaps from scoping review",
            mimeType="application/json"
        ),
        Resource(
            uri="research://schema",
            name="Database Schema",
            description="Neo4j graph schema (nodes, relationships, indexes)",
            mimeType="application/json"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    try:
        if uri == "research://papers":
            result = await resources.list_all_papers()
        elif uri == "research://corpus":
            result = await resources.list_corpus_papers()
        elif uri == "research://gaps":
            result = await resources.get_research_gaps()
        elif uri == "research://schema":
            result = await resources.get_database_schema()
        elif uri.startswith("research://paper/"):
            document_id = uri.replace("research://paper/", "")
            result = await resources.get_paper_by_id(document_id)
        else:
            result = {
                "uri": uri,
                "mimeType": "text/plain",
                "text": f"Resource not found: {uri}"
            }

        return result.get("text", "")

    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
        return _to_json({"error": str(e)}, compact=False)


# =============================================================================
# SERVER LIFECYCLE
# =============================================================================

async def main():
    """Run the MCP server."""
    logger.info("Starting ScholarGraph MCP Server...")
    logger.info("Connecting to Neo4j at bolt://127.0.0.1:7687...")

    try:
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP Server running on stdio")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down ScholarGraph MCP Server...")
        tools.close()
        resources.close()


if __name__ == "__main__":
    asyncio.run(main())
