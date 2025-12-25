"""
ScholarGraph MCP Server

Exposes ScholarGraph research knowledge graph to Claude Code via MCP protocol.
Runs locally on port 8100 with access to Neo4j database.
"""

import asyncio
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
# TOOLS: Claude Code can call these directly
# =============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_papers",
            description="Search research papers using semantic, keyword, or hybrid search. "
                       "Supports filtering by scoping review corpus.",
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
            description="List all 51 scoping review corpus papers with their study IDs.",
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
                filter_corpus=arguments.get("filter_corpus")
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
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}

        # Format result as text
        import json
        result_text = json.dumps(result, indent=2)

        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        error_result = {"success": False, "error": str(e)}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


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
            description="The 51 papers from the scoping review corpus",
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
        import json
        return json.dumps({"error": str(e)}, indent=2)


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
