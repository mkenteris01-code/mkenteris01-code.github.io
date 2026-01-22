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
