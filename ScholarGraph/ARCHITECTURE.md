# ScholarGraph Architecture & Design

> A deep dive into how ScholarGraph works under the hood

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Flow Pipeline](#data-flow-pipeline)
3. [Graph Schema Deep Dive](#graph-schema-deep-dive)
4. [Search Architecture](#search-architecture)
5. [How RAG Works](#how-rag-works)
6. [MCP Integration](#mcp-integration)
7. [Known Issues & Optimizations](#known-issues--optimizations)

---

## System Overview

ScholarGraph is a **GraphRAG** (Graph Retrieval-Augmented Generation) system. This means it combines:

1. **Knowledge Graph** - Structured relationships between entities
2. **Vector Search** - Semantic similarity via embeddings
3. **RAG** - Using retrieved context to augment LLM responses

### The Core Idea

```
Traditional Search:  Query → Keywords → Documents
Vector Search:      Query → Embedding → Similar Documents
GraphRAG:           Query → Embedding + Graph Traversal → Context → LLM Response
```

---

## Data Flow Pipeline

### Phase 1: Document Ingestion

```
┌─────────────┐
│  PDF / MD   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  PyPDF2 / Frontmatter Parser    │
│  - Extract text                 │
│  - Extract metadata             │
│  - Detect abstract              │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  TextChunker                    │
│  - Split into ~3500 word chunks │
│  - 400 word overlap             │
│  - Track character positions    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  EmbeddingGenerator             │
│  - Call GPU rig (Qwen 2.5)      │
│  - Generate 768-dim vectors     │
│  - Cache with SHA256 keys       │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Graph Builder                  │
│  - Create Document node         │
│  - Create Chunk nodes           │
│  - Extract Topics/Concepts      │
│  - Create relationships         │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Neo4j Database                 │
│  - Store nodes & relationships  │
│  - Build vector indexes         │
└─────────────────────────────────┘
```

### Key Files in Ingestion

| File | Responsibility |
|------|----------------|
| [ingestion/batch_ingester.py](ingestion/batch_ingester.py) | Orchestrates ingestion pipeline |
| [ingestion/chunker.py](ingestion/chunker.py) | Splits documents into chunks |
| [ingestion/document_processor.py](ingestion/document_processor.py) | Extracts metadata from PDF/MD |
| [embeddings/generator.py](embeddings/generator.py) | Generates embeddings via GPU/CPU |
| [graph/schema.py](graph/schema.py) | Creates Neo4j constraints and indexes |

---

## Graph Schema Deep Dive

### Node Types

#### Document Node

```cypher
(:Document {
  document_id: "doc_sha256",      // Unique identifier
  title: "Paper Title",
  authors: ["Author 1", "Author 2"],
  date: "2024-01-15",
  doi: "10.xxxx/xxxxx",
  abstract: "Paper abstract...",
  file_path: "/path/to/paper.pdf",
  document_type: "pdf",
  is_latest: true,                 // Versioning flag
  version: 1,                      // Version number
  superseded_by: null,             // ID of newer version
  ingestion_date: "2024-01-20",
  scoping_review_included: false   // Corpus flag
})
```

#### Chunk Node

```cypher
(:Chunk {
  chunk_id: "chunk_sha256",
  content: "Full text content (~3500 words)",
  position: 0,                     // Sequence in document
  start_char: 0,                   // Character offset start
  end_char: 18500,                 // Character offset end
  word_count: 3500,
  char_count: 18500,
  summary: "Optional LLM summary", // If generated
  embedding: [0.1, 0.2, ...]       // 768-dim vector
})
```

#### Topic Node

```cypher
(:Topic {
  name: "federated learning",
  category: "machine-learning",
  confidence: 0.9,                 // Calculated from mentions
  mention_count: 15
})
```

#### Concept Node

```cypher
(:Concept {
  name: "FL",
  type: "acronym",                 // or "term"
  mention_count: 42
})
```

### Relationship Types

| Relationship | From → To | Properties | Purpose |
|--------------|-----------|------------|---------|
| `CONTAINS` | Document → Chunk | - | Document membership |
| `NEXT_CHUNK` | Chunk → Chunk | - | Sequential ordering |
| `DISCUSSES_TOPIC` | Document/Chunk → Topic | `confidence`, `mentions` | Topic relevance |
| `ABOUT_CONCEPT` | Document → Concept | - | Concept extraction |
| `REFERENCES` | Document → Document | `citation_context` | Citation graph |
| `SUPERSEDES` | New → Old | `reason`, `timestamp` | Version tracking |

### Visual Graph Structure

```
     ┌──────────────┐
     │  :Document   │
     │  "Paper A"   │
     └───────┬──────┘
             │ CONTAINS
             ▼
     ┌───────────────────────────────────┐
     │ :Chunk (pos 0) :Chunk (pos 1) ... │
     └─────┬─────────────────────────────┘
           │ DISCUSSES_TOPIC
           ▼
     ┌──────────────┐
     │   :Topic     │
     │ "federated   │
     │  learning"   │
     └──────────────┘
```

---

## Search Architecture

### Three Search Modes

#### 1. Semantic Search ([search/semantic_search.py](search/semantic_search.py))

```
Query → Embedding → Vector Index → Similar Chunks
```

```cypher
CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
YIELD node, score
```

**Pros**: Finds semantically similar content even without exact keywords
**Cons**: May miss specific technical terms

#### 2. Keyword Search ([search/keyword_search.py](search/keyword_search.py))

```
Query → Full-text Index → Matching Chunks
```

```cypher
CALL db.index.fulltext.queryNodes('chunk_content_fulltext', $query)
YIELD node, score
```

**Pros**: Exact term matching, good for acronyms/specific terms
**Cons**: Misses synonyms and related concepts

#### 3. Hybrid Search ([search/hybrid_search.py](search/hybrid_search.py))

```
Query → Semantic + Keyword → Combined/Reranked Results
```

```python
hybrid_score = 0.7 * semantic_score + 0.3 * keyword_score
```

**Why this ratio?**
- 70% semantic captures meaning and context
- 30% keyword ensures technical precision
- Empirically tested for academic search

### Search Flow Diagram

```
                    User Query
                         │
                         ▼
              ┌──────────────────────┐
              │   EmbeddingGenerator │
              │   (Qwen 2.5 @ GPU)   │
              └──────────┬───────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │                                │
        ▼                                ▼
┌───────────────┐              ┌─────────────────┐
│ SemanticSearch│              │ KeywordSearch   │
│ (Vector Index)│              │ (Full-text)     │
└───────┬───────┘              └────────┬────────┘
        │                               │
        │    k*2 results each           │
        └───────────────┬───────────────┘
                        ▼
              ┌─────────────────┐
              │  Score Fusion   │
              │  + Deduplication│
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Top-k Results  │
              │  (sorted by     │
              │   hybrid_score) │
              └─────────────────┘
```

---

## How RAG Works

### The RAG Query Flow

When you (or an AI) ask a question:

```
1. Query: "How does federated learning preserve privacy?"

2. Search:
   - Generate query embedding
   - Find top-k relevant chunks (k=5 by default)
   - Each chunk contains ~3500 words of context

3. Context Assembly:
   {
     "query": "How does federated learning preserve privacy?",
     "results": [
       {
         "content": "...3500 words from relevant paper...",
         "document_title": "Privacy-Preserving Federated Learning",
         "score": 0.89
       },
       ... 4 more results
     ]
   }

4. LLM Augmentation:
   The retrieved context is passed to the LLM along with the
   original query. The LLM uses this context to generate an
   informed, grounded answer.

5. Response:
   "According to the retrieved papers, federated learning preserves
   privacy through three main mechanisms: [detailed answer with
   citations to specific papers]"
```

### Why This Works Better Than Plain Search

| Plain Search | GraphRAG |
|--------------|----------|
| Returns document titles | Returns relevant passages |
| You must read each paper | Context pre-extracted |
| No connection between papers | Graph shows relationships |
| Static results | Version-aware (latest only) |

---

## MCP Integration

### What is MCP?

**MCP** (Model Context Protocol) is Anthropic's standard for AI tools to access external data.

### ScholarGraph MCP Server

Located at: [mcp_server/server.py](mcp_server/server.py)

#### Available Tools

| Tool | Purpose | Parameters |
|------|---------|------------|
| `search_papers` | Search the knowledge graph | query, mode, k, filter_corpus, days_ago |
| `get_paper_details` | Get full paper metadata | paper_title |
| `list_corpus_papers` | List all corpus papers | - |
| `compare_to_corpus_gaps` | Check research gap relevance | paper_title |
| `get_database_stats` | Get graph statistics | - |
| `link_documents` | Create version relationships | older_doc_id, newer_doc_id, reason |

#### Configuration (Claude Desktop)

```json
{
  "mcpServers": {
    "scholargraph": {
      "command": "python",
      "args": ["C:/projects/mkenteris01-code/ScholarGraph/mcp_server/server.py"]
    }
  }
}
```

### How Claude Uses ScholarGraph

```
User Question (in Claude)
        │
        ▼
Claude decides it needs research context
        │
        ▼
Calls MCP tool: search_papers(query="...", k=5)
        │
        ▼
ScholarGraph MCP Server
        │
        ├─► Generates embedding
        ├─► Queries Neo4j
        ├─► Returns chunks + metadata
        │
        ▼
Claude receives context
        │
        ▼
Claude generates informed answer
```

---

## Known Issues & Optimizations

### Current Issue: Large Response Size

**Problem**: When `k=5`, responses contain:
- 5 chunks × ~3,500 words = 17,500 words
- Plus JSON metadata
- Formatted with indentation
- Total: ~100,000+ characters

**Why this happens**:
1. Chunks are large (3,500 words) for accurate retrieval
2. Full content is returned for every result
3. JSON is pretty-printed (`indent=2`)

**Impact**:
- Claude struggles to process large responses
- Context window fills up quickly
- Slower response times

### Planned Optimization

**Solution**: Add `content_mode` parameter to search tools

```python
# Options:
content_mode = "preview"   # First 800 chars (default for AI)
            = "summary"    # Just chunk.summary field
            = "full"       # Complete content (current behavior)
```

**Benefits**:
| Mode | Response Size | Use Case |
|------|---------------|----------|
| `preview` | ~20,000 chars | AI queries, initial search |
| `summary` | ~5,000 chars | Quick relevance checks |
| `full` | ~100,000 chars | Detailed analysis |

### Additional Optimizations

1. **Compact JSON**: Use `separators=(',', ':')` instead of `indent=2`
2. **Reduce default k**: Change from 5 to 3 for smaller default responses
3. **Streaming**: Return results incrementally (future enhancement)

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Semantic Search | < 50ms | Native Neo4j vector index |
| Keyword Search | < 30ms | Full-text index |
| Hybrid Search | < 100ms | Both indexes + fusion |
| Embedding Generation | 200-500ms | GPU rig (network call) |
| Document Ingestion | 30-60 sec/doc | With embeddings |
| Chunk Retrieval | < 10ms | Direct ID lookup |

---

## Extension Points

Want to extend ScholarGraph? Here are the key extension points:

| Component | File | How to Extend |
|-----------|------|---------------|
| Search modes | [search/](search/) | Add new search class (e.g., `CitationSearch`) |
| Node types | [graph/nodes.py](graph/nodes.py) | Add new node creation methods |
| Relationships | [graph/relationships.py](graph/relationships.py) | Add new relationship types |
| Metadata extraction | [ingestion/document_processor.py](ingestion/document_processor.py) | Add new extraction patterns |
| Embedding models | [embeddings/generator.py](embeddings/generator.py) | Add new embedding backend |

---

## Summary

ScholarGraph transforms academic documents into a queryable knowledge graph by:

1. **Ingesting** PDFs/Markdown and extracting metadata
2. **Chunking** content into ~3500-word segments with overlap
3. **Embedding** chunks as 768-dimensional vectors
4. **Building** a graph with Documents, Chunks, Topics, Concepts
5. **Indexing** with Neo4j's vector and full-text indexes
6. **Searching** via semantic, keyword, or hybrid modes
7. **Retrieving** relevant context for RAG-augmented AI responses

The result: An intelligent research assistant that understands your literature collection and can answer questions grounded in actual paper content.
