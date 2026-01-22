# ScholarGraph Changelog

All notable changes to ScholarGraph will be documented in this file.

## [0.2.0] - 2026-01-22

### Added
- **ARCHITECTURE.md** - Comprehensive system design documentation
  - Data flow pipeline visualization
  - Graph schema details with examples
  - Search architecture explanation
  - RAG query flow diagrams
  - Known issues and optimization strategies
- **content_mode parameter** - Optimized response sizes for MCP tools
  - `preview` mode (default): First 800 characters of content
  - `summary` mode: Only chunk summaries
  - `full` mode: Complete content (original behavior)
- **Compact JSON serialization** - Reduced response size by ~20%
- **New MCP tools**:
  - `check_sessions_ingested` - Fast comparison of directory vs Neo4j
  - `get_recent_sessions` - Recently ingested sessions by date
  - `link_documents` - Create version relationships between documents
- **Python package installation** - `setup.py` for editable pip install

### Changed
- **README.md** restructure:
  - Quick Links section for navigation
  - Added "How It Works" with visual pipeline diagram
  - Simplified Features into Highlights table
  - Condensed technical details (moved to ARCHITECTURE.md)
  - Updated MCP tools table format
- **Response size optimization**: 95% reduction in default search responses
  - Before: ~100,000 characters for 5 results
  - After: ~5,000 characters for 5 results (preview mode)

### Technical Details

#### Search Classes
- `SemanticSearch.search_chunks()` - Added `content_mode` parameter
- `HybridSearch.search_chunks()` - Added `content_mode` parameter
- `VectorIndexManager.vector_search_chunks()` - Added `content_mode` parameter and `_process_content()` method

#### MCP Server
- `server.py`:
  - Added `_to_json()` utility for compact JSON
  - Updated `search_papers` tool schema with `content_mode` parameter
  - Added 3 new tool schemas
  - Updated tool handlers

#### Graph Module
- `graph/__init__.py` - Exported `ContentMode` and `PREVIEW_LENGTH`
- `graph/vector_index.py`:
  - Added `ContentMode` Literal type
  - Added `PREVIEW_LENGTH` constant (800 characters)
  - Added static `_process_content()` method

### Dependencies
- MCP version requirement: >= 0.9.0 (unchanged)
- Neo4j version requirement: 5.13+ (unchanged)
- Python: 3.9+ (unchanged)

### Bug Fixes
- Fixed date parsing in `get_recent_sessions` - moved from Cypher to Python
- Removed duplicate code in `tools.py` after editing

### Migration Notes

**For users:** No breaking changes. Default behavior now returns previews instead of full content.

**For developers:** To get full content, explicitly pass `content_mode="full"` to search functions.

### Files Modified
```
ScholarGraph/
├── README.md                      (restructured)
├── ARCHITECTURE.md                 (new)
├── setup.py                        (new)
├── graph/__init__.py               (added exports)
├── graph/vector_index.py           (added content_mode)
├── search/semantic_search.py       (added content_mode)
├── search/hybrid_search.py          (added content_mode)
├── ingestion/batch_ingester.py     (minor)
├── mcp_server/server.py            (major updates)
├── mcp_server/tools.py              (major updates)
├── mcp_server/run_server.py        (new wrapper)
└── rkg.py                           (minor)
```

---

## [0.1.0] - Previous Release

### Initial Features
- Document ingestion (PDF, Markdown)
- Semantic, keyword, and hybrid search
- GraphRAG architecture
- Temporal versioning with supersession detection
- MCP server for Claude Code integration
- CLI commands (rkg)
- GPU rig embeddings (Qwen 2.5)
