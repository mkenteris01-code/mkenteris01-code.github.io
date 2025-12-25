# ScholarGraph

Research Knowledge Graph for semantic search over academic papers and markdown documents using Neo4j and local GPU embeddings.

## Features

- Neo4j-based knowledge graph with vector indexes
- PDF and Markdown document ingestion
- **Smart duplicate detection** - automatically updates only modified files
- Semantic, keyword, and hybrid search
- Local GPU rig integration (Qwen 2.5 7B / Mistral 7B)
- Sentence-transformers fallback for embeddings
- **MCP Server** - Native Claude Code integration with persistent context
- CLI interface for easy querying from Claude Code

## Requirements

- Python 3.9+
- Neo4j 5.13+ (for vector indexes)
- GPU rig running Qwen 2.5 7B at 192.168.1.150:8000 (optional)

## Installation

```bash
# Clone repository
cd C:/projects/mkenteris01-code/ScholarGraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Neo4j credentials
```

## Configuration

Edit `.env` file:

```env
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=pkg.graphrag

GPU_RIG_QWEN_URL=http://192.168.1.150:8000
EMBEDDING_MODEL=qwen
EMBEDDING_DIMENSION=768

CHUNK_SIZE_WORDS=3500
CHUNK_OVERLAP_WORDS=400
```

## Usage

### Initialize Database Schema

```bash
python rkg.py init --dimension 768
```

### Ingest Documents

```bash
# Ingest a single PDF
python rkg.py ingest path/to/paper.pdf

# Ingest a directory of documents
python rkg.py ingest path/to/documents/

# Ingest with embeddings (requires GPU rig or sentence-transformers)
python rkg.py ingest path/to/documents/ --embeddings

# Skip duplicates (fast, only adds new files)
python rkg.py ingest path/to/documents/ --no-update

# Force re-ingest everything
python rkg.py ingest path/to/documents/ --force
```

**Note:** Duplicate detection is automatic! ScholarGraph checks file modification times and only updates changed files.

### Search

```bash
# Hybrid search (default)
python rkg.py search "federated learning" --k 10

# Semantic search only
python rkg.py search "knowledge graphs" --mode semantic

# Keyword search only
python rkg.py search "neural networks" --mode keyword

# JSON output for programmatic use
python rkg.py search "transformers" --format json
```

### Database Statistics

```bash
python rkg.py stats
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `rkg init` | Initialize Neo4j schema with vector indexes |
| `rkg ingest <path>` | Ingest documents from file or directory |
| `rkg list` | List all ingested documents |
| `rkg search "<query>"` | Search knowledge graph |
| `rkg stats` | Show database statistics |

**Guides:**
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** - CLI usage examples
- **[MCP_SERVER_GUIDE.md](docs/MCP_SERVER_GUIDE.md)** - MCP server setup and usage

## Search Modes

- **semantic**: Vector similarity search using embeddings
- **keyword**: Full-text search using Neo4j indexes
- **hybrid**: Weighted combination (0.7 semantic + 0.3 keyword)

## Architecture

```
ScholarGraph/
├── config/         # Configuration management
├── core/           # Neo4j and GPU rig clients
├── graph/          # Schema, nodes, relationships
├── ingestion/      # PDF/Markdown processing
├── embeddings/     # Embedding generation
├── search/         # Search implementations
└── rkg.py          # CLI entry point
```

## Document Processing Pipeline

1. **Extract** text and metadata (PDF/Markdown)
2. **Chunk** text (3500 words with 400 word overlap)
3. **Extract** topics, keywords, concepts
4. **Generate** embeddings (optional)
5. **Store** in Neo4j graph
6. **Link** relationships (CONTAINS, NEXT_CHUNK, DISCUSSES_TOPIC)

## Graph Schema

### Nodes
- **Document**: Research papers, markdown files
- **Chunk**: Text segments from documents
- **Topic**: Research topics and themes
- **Concept**: Domain concepts and terminology

### Relationships
- **CONTAINS**: Document → Chunk
- **NEXT_CHUNK**: Chunk → Chunk (sequential)
- **DISCUSSES_TOPIC**: Document/Chunk → Topic (with confidence scores)
- **REFERENCES**: Document → Document (citations)
- **IMPLEMENTS**: Document → Concept

## Embedding Generation

**GPU Rig** (preferred):
- Qwen 2.5 7B at http://192.168.1.150:8000
- Mistral 7B at http://192.168.1.150:8001

**Fallback** (sentence-transformers):
```bash
pip install sentence-transformers
```

Uses `all-mpnet-base-v2` (768 dimensions) for embeddings.

## Use with Claude Code

### Method 1: MCP Server (Recommended)

ScholarGraph includes a Model Context Protocol (MCP) server for native integration with Claude Code. This provides:
- Persistent tool context (no "forgetting")
- Native tool calls (faster than Bash)
- Resource browsing (browse papers like files)

**Setup:**

```bash
# Install MCP dependencies
pip install -r requirements.txt

# Configure Claude Code
# Add to ~/.claude/config.json:
{
  "mcpServers": {
    "scholargraph": {
      "command": "python",
      "args": ["C:\\projects\\mkenteris01-code\\ScholarGraph\\mcp_server\\server.py"],
      "env": {"PYTHONPATH": "C:\\projects\\mkenteris01-code\\ScholarGraph"}
    }
  }
}

# Restart Claude Code
```

**Available Tools:**
- `search_papers` - Search with semantic/keyword/hybrid modes
- `get_paper_details` - Get full paper content
- `list_corpus_papers` - List scoping review corpus
- `compare_to_corpus_gaps` - Evaluate papers against research gaps
- `get_database_stats` - Database statistics

**See [MCP_SERVER_GUIDE.md](docs/MCP_SERVER_GUIDE.md) for full documentation.**

### Method 2: Direct Bash (Fallback)

```bash
# Search for relevant chunks
python rkg.py search "vLLM quantization" --format json --k 5

# Get database stats
python rkg.py stats

# Ingest new documents
python rkg.py ingest /path/to/new/paper.pdf
```

## Example Workflow

```bash
# 1. Initialize
python rkg.py init

# 2. Ingest research papers
python rkg.py ingest ~/research/papers/ --embeddings

# 3. Search
python rkg.py search "federated learning privacy" --k 10

# 4. Check stats
python rkg.py stats
```

## Development

```bash
# Run tests
pytest tests/

# Format code
black .

# Type checking
mypy .
```

## Troubleshooting

**Vector search not working:**
- Ensure Neo4j 5.13+ is installed
- Check vector indexes: `SHOW INDEXES` in Neo4j Browser
- Verify embedding dimension matches index (default: 768)

**GPU rig connection fails:**
- Check GPU rig is running at 192.168.1.150
- Test connection: `curl http://192.168.1.150:8000/query`
- Fallback to sentence-transformers will be used

**Slow ingestion:**
- Disable embeddings for faster ingestion: `--no-embeddings`
- Generate embeddings later with batch processor
- Use persistent cache to avoid recomputation

## License

MIT License - See [LICENSE](LICENSE) file

## Contact

- **Author:** M. Kenteris
- **Institution:** Aegean University
- **Email:** mkenteris@aegean.gr

## Acknowledgments

- Neo4j for graph database and vector search
- Qwen 2.5 7B (Alibaba Cloud) for embeddings
- HITL-forge project for GPU infrastructure
- Claude Code for AI-assisted development

---

**Last Updated:** December 24, 2025
