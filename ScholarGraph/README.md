# ScholarGraph

> **A Personal Knowledge Graph (PKG) system built with GraphRAG for researchers**

A research knowledge graph platform that transforms academic documents into an intelligent, searchable knowledge network using Neo4j, vector embeddings, and GraphRAG methodologies.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.13+-008CC1.svg)](https://neo4j.com/)
[![GraphRAG](https://img.shields.io/badge/GraphRAG-Implemented-brightgreen.svg)](#graphrag-architecture)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What is ScholarGraph?

ScholarGraph is a **Personal Knowledge Graph** designed for researchers who want to:

- **Ingest** research papers (PDF, Markdown) into a graph database
- **Search** using semantic meaning, not just keywords
- **Track** document versions and supersession automatically
- **Query** via CLI, Python API, or Claude Code (MCP integration)
- **Discover** connections between papers through graph traversal

## Highlights

- **Semantic Search** - Vector embeddings capture meaning, not just words
- **Hybrid Retrieval** - 70% semantic + 30% keyword for best results
- **GraphRAG Architecture** - Documents → Chunks → Topics → Concepts graph
- **Temporal Versioning** - Auto-detects when newer papers supersede older ones
- **MCP Server** - Native Claude Code integration for AI-powered research
- **Local GPU** - Qwen/Mistral embeddings via your GPU rig (or cloud fallback)

---

## Features Overview

| Category | Features |
|----------|----------|
| **Ingestion** | PDF & Markdown parsing, metadata extraction, smart chunking |
| **Search** | Semantic, Keyword, Hybrid modes with configurable weights |
| **Graph** | Neo4j native, vector indexes, full-text search, relationship traversal |
| **Versioning** | Temporal schema, supersession detection, version chains |
| **AI Integration** | MCP server for Claude Code, GPU rig embeddings |
| **CLI** | Complete command-line interface for all operations |

---

## GraphRAG Architecture

ScholarGraph implements **GraphRAG** (Retrieval-Augmented Generation with Graph) principles:

```
LAYER 1: Documents     → PDF, Markdown files
LAYER 2: Chunks        → Text segments (~3500 words, 400 overlap)
LAYER 3: Embeddings    → 768-dim vectors, cosine similarity
LAYER 4: Knowledge Graph → Documents, Topics, Concepts, Relationships
```

### Graph Schema

**Node Types:**
- **Document**: Research papers, articles (title, authors, date, doi, `is_latest`, `version`)
- **Chunk**: Text segments (~3500 words) with position tracking
- **Topic**: Research themes with confidence scores
- **Concept**: Domain entities and terminology

**Relationship Types:**
- **CONTAINS**: Document → Chunk
- **NEXT_CHUNK**: Chunk → Chunk (sequential ordering)
- **DISCUSSES_TOPIC**: Document → Topic (with confidence scores)
- **ABOUT_CONCEPT**: Document → Concept
- **SUPERSEDES**: New → Old Document (with reason, timestamp)

---

## Tech Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | Neo4j 5.13+ | Graph DB with native vector search |
| **Language** | Python 3.9+ | Core implementation |
| **Config** | Pydantic Settings | Type-safe configuration |
| **CLI** | Click | Command-line interface |

### GraphRAG Components

| Component | Technology | Implementation |
|-----------|------------|----------------|
| **Vector Search** | Neo4j Native Vector Index | Cosine similarity on 768-dim embeddings |
| **Chunking** | Custom Word-based Algorithm | 3500 words ± 400 overlap |
| **Entity Extraction** | LLM-assisted (Qwen 2.5) | Topics, concepts, keywords |
| **Full-text Search** | Neo4j Full-text Index | BM25-style keyword retrieval |
| **Hybrid Scoring** | Weighted Fusion | 0.7 × semantic + 0.3 × keyword |

### Document Processing

- **PDF Parsing** - PyPDF2, pypdf
- **Markdown** - python-frontmatter, markdown
- **Metadata Extraction** - LLM-assisted

### AI Integration

| Component | Technology |
|-----------|------------|
| **Embeddings** | Qwen/Mistral (GPU rig) or sentence-transformers |
| **MCP Server** | mcp >= 0.9.0, Uvicorn, FastAPI |
| **GPU Backend** | Qwen 2.5 7B @ 192.168.1.150:8000 |

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

## Environment Variables

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

# Temporal versioning
rkg init-temporal                    # initialize versioning
rkg detect-supersessions --dry-run   # preview supersession
rkg supersession-summary             # show version stats
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

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "scholargraph": {
      "command": "python",
      "args": ["/path/to/ScholarGraph/mcp_server/server.py"]
    }
  }
}
```

Available MCP Tools:
- `search_papers` - Semantic/keyword/hybrid search
- `get_superseded_documents` - View superseded versions
- `get_document_versions` - Get all versions of a document
- `list_corpus_papers` - List scoping review corpus
- `get_database_stats` - Database statistics

---

## GraphRAG Technologies Implemented

### 1. Hierarchical Chunking

- Word-based chunking (default: 3500 words)
- Overlapping chunks (default: 400 words)
- Character position tracking for source reference
- Sequential ordering via NEXT_CHUNK relationships

### 2. Vector Index with Neo4j

```cypher
CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
YIELD node, score
MATCH (d:Document)-[:CONTAINS]->(node)
WHERE d.is_latest = true
RETURN node.content, d.title, score
```

### 3. Hybrid Retrieval Fusion

```
hybrid_score = 0.7 * normalized_semantic + 0.3 * normalized_keyword
```

### 4. Entity-Relationship Graph

- Automatic topic extraction
- Concept identification
- Confidence-scored relationships

### 5. Temporal Versioning

- Automatic supersession detection
- Title similarity matching (0.85 threshold)
- Session document pattern recognition
- Version chain traversal

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

## Project Structure

```
ScholarGraph/
├── cli/              # CLI entry points
├── config/           # Configuration (Pydantic)
├── core/             # Neo4j client, GPU rig client
├── embeddings/       # Embedding generation & caching
├── graph/            # Schema, nodes, relationships, vector index
├── ingestion/        # PDF/MD processing, chunking, metadata
├── mcp_server/       # MCP server for Claude Code
├── models/           # Pydantic data models
├── search/           # Semantic, keyword, hybrid search
├── tests/            # Unit tests
├── tools/            # External tools (pandoc)
├── data/             # Data storage
├── rkg.py            # Main CLI
├── requirements.txt  # Python dependencies
└── README.md         # This file
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