# ScholarGraph

> **A Personal Knowledge Graph (PKG) system built with GraphRAG for researchers**

A research knowledge graph platform that transforms academic documents into an intelligent, searchable knowledge network using Neo4j, vector embeddings, and GraphRAG methodologies.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.13+-008CC1.svg)](https://neo4j.com/)
[![GraphRAG](https://img.shields.io/badge/GraphRAG-Implemented-brightgreen.svg)](#how-it-works)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Quick Links

- [How It Works](#how-it-works) - Understand the GraphRAG pipeline
- [Installation](#installation) - Get up and running
- [Usage](#usage) - CLI, Python API, and MCP integration
- [ARCHITECTURE.md](ARCHITECTURE.md) - Deep dive into system design

---

## What is ScholarGraph?

ScholarGraph is a **Personal Knowledge Graph** designed for researchers who want to:

- **Ingest** research papers (PDF, Markdown) into a graph database
- **Search** using semantic meaning, not just keywords
- **Track** document versions and supersession automatically
- **Query** via CLI, Python API, or Claude Code (MCP integration)
- **Discover** connections between papers through graph traversal

### Highlights

| Feature | Description |
|---------|-------------|
| **Semantic Search** | Vector embeddings capture meaning, not just words |
| **Hybrid Retrieval** | 70% semantic + 30% keyword for best results |
| **GraphRAG** | Documents → Chunks → Topics → Concepts graph |
| **Temporal Versioning** | Auto-detects when newer papers supersede older ones |
| **MCP Server** | Native Claude Code integration for AI-powered research |
| **Local GPU** | Qwen/Mistral embeddings via your GPU rig (or cloud fallback) |

---

## How It Works

ScholarGraph implements **GraphRAG** (Retrieval-Augmented Generation with Graph) to transform static documents into an intelligent knowledge network.

### The Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PDF / MD   │ -> │   Chunks    │ -> │  Embeddings │ -> │   Graph     │
│  Documents  │    │  ~3500 words│    │   768-dim   │    │  Database   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

1. **Ingest**: Parse PDFs and Markdown files, extract metadata
2. **Chunk**: Split into ~3500-word segments with 400-word overlap
3. **Embed**: Generate 768-dimensional vectors (Qwen 2.5 via GPU or sentence-transformers)
4. **Graph**: Store in Neo4j with Documents, Chunks, Topics, Concepts, and relationships
5. **Search**: Query via semantic, keyword, or hybrid search
6. **Retrieve**: Return relevant passages for RAG-augmented AI responses

### Graph Schema

**Nodes:**
- `Document` - Papers with title, authors, version tracking
- `Chunk` - Text segments with embeddings
- `Topic` - Research themes with confidence scores
- `Concept` - Domain entities and terminology

**Relationships:**
- `CONTAINS` - Document → Chunk
- `NEXT_CHUNK` - Chunk → Chunk (sequential)
- `DISCUSSES_TOPIC` - Document/Chunk → Topic
- `SUPERSEDES` - New → Old (version tracking)

> **For detailed architecture, data flow, and design decisions, see [ARCHITECTURE.md](ARCHITECTURE.md)**

---

## Installation

```bash
# Clone repository
git clone https://github.com/mkenteris01-code/ScholarGraph.git
cd ScholarGraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Neo4j credentials
```

### Environment Variables

Create `.env` in project root:

```bash
# Neo4j Database
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=pkg.graphrag

# GPU Rig (optional - for embeddings)
GPU_RIG_QWEN_URL=http://192.168.1.150:8000
GPU_RIG_MISTRAL_URL=http://192.168.1.150:8001
GPU_RIG_EMBEDDING_URL=http://192.168.1.150:8005

# Embedding Configuration
EMBEDDING_MODEL=qwen
EMBEDDING_DIMENSION=768

# Chunking Configuration
CHUNK_SIZE_WORDS=3500
CHUNK_OVERLAP_WORDS=400
```

---

## Usage

### CLI Commands

```bash
# Initialize database schema with vector indexes
rkg init

# Ingest documents
rkg ingest path/to/papers/
rkg ingest path/to/papers/ --embeddings    # with embeddings
rkg ingest path/to/papers/ --force         # re-ingest all

# Search knowledge graph
rkg search "federated learning" --mode hybrid --k 10
rkg search "knowledge graphs" --mode semantic
rkg search "neural networks" --mode keyword

# List documents
rkg list

# Database statistics
rkg stats

# Link documents (create SUPERSEDES relationship)
rkg link <older_doc_id> <newer_doc_id>           # link newer → older
rkg link <older> <newer> --reason "updated_data"  # with reason

# Temporal versioning
rkg init-temporal                    # initialize versioning
rkg detect-supersessions --dry-run   # preview supersession
rkg supersession-summary             # show version stats
rkg mark-superseded <older> <newer>  # alternative to link command
```

### Python API

```python
from core import Neo4jClient
from ingestion import BatchIngester
from search import HybridSearch
from embeddings import EmbeddingGenerator

# Initialize
client = Neo4jClient()

# Ingest documents
ingester = BatchIngester(client, generate_embeddings=True)
ingester.ingest_directory("papers/")

# Hybrid search
generator = EmbeddingGenerator()
searcher = HybridSearch(client, generator)
results = searcher.search_chunks("machine learning", k=10)
```

### MCP Server (Claude Code)

Configure in Claude Desktop settings (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "scholargraph": {
      "command": "python",
      "args": ["C:/path/to/ScholarGraph/mcp_server/server.py"]
    }
  }
}
```

**Available MCP Tools:**

| Tool | Purpose |
|------|---------|
| `search_papers` | Semantic/keyword/hybrid search with corpus & recency filters |
| `get_paper_details` | Get full paper metadata by title (partial match) |
| `list_corpus_papers` | List scoping review corpus papers |
| `compare_to_corpus_gaps` | Check if paper addresses research gaps |
| `get_database_stats` | Node counts, corpus size, etc. |
| `link_documents` | Link two documents (creates SUPERSEDES relationship) |

---

## Performance

| Metric | Value |
|--------|-------|
| Vector Search | < 50ms |
| Keyword Search | < 30ms |
| Hybrid Search | < 100ms |
| Ingestion Speed | ~100-500 docs/hr (with embeddings) |
| Embedding Dimension | 768 (Qwen) |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Database** | Neo4j 5.13+ (native vector search) |
| **Language** | Python 3.9+ |
| **Embeddings** | Qwen 2.5 (GPU rig) or sentence-transformers |
| **Config** | Pydantic Settings |
| **CLI** | Click |
| **MCP** | mcp >= 0.9.0 |

---

## Project Structure

```
ScholarGraph/
├── ARCHITECTURE.md    # Deep dive into system design
├── cli/               # CLI entry points
├── config/            # Configuration (Pydantic)
├── core/              # Neo4j client, GPU rig client
├── embeddings/        # Embedding generation & caching
├── graph/             # Schema, nodes, relationships, vector index
├── ingestion/         # PDF/MD processing, chunking, metadata
├── mcp_server/        # MCP server for Claude Code
├── models/            # Pydantic data models
├── search/            # Semantic, keyword, hybrid search
├── tests/             # Unit tests
├── tools/             # External tools (pandoc)
├── rkg.py             # Main CLI
└── requirements.txt   # Python dependencies
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Author

M. Kenteris
- GitHub: https://github.com/mkenteris01-code

## Acknowledgments

- Neo4j - Graph database with native vector search
- Qwen 2.5 (Alibaba) - Embedding generation
- MCP (Anthropic) - Model Context Protocol for AI integration
- GraphRAG (Microsoft) - Retrieval-Augmented Generation principles

---

Built for researchers who want to transform their document library into an intelligent knowledge graph.
