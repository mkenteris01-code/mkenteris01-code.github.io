# ScholarGraph Changelog

All notable changes to ScholarGraph will be documented in this file.

## [0.3.0] - 2026-01-22

### Added
- **Document Discovery & Analysis Tools** - 7 new MCP tools for advanced document operations
  - `search_by_tags` - Find documents by tags/topics (match ANY or ALL)
  - `get_document_timeline` - Chronological view of documents with date filtering
  - `search_content_keywords` - Full-text keyword search in titles, abstracts, content
  - `get_document_network` - Show related documents via shared topics/concepts/versions
  - `get_phase_documents` - Get documents by project phase (Phase-1, Phase-2A, etc.)
  - `summarize_recent_work` - AI summary of recent work with topics and phases
  - `merge_duplicates` - Find and merge duplicate documents (with dry-run mode)
- **Windows UTF-8 Encoding Fix** - Fixed encoding issues in batch_ingester.py
  - Automatic stdout/stderr reconfiguration for Windows platforms
  - Resolves `'charmap' codec can't encode character` errors

### Changed
- **`ingest_missing_sessions` renamed to `ingest_missing`**
  - Now works with any folder (not just sessions)
  - Simplified parameters: `folder`, `date`, `date_from`, `date_to`, `force`
- **Total MCP tools**: 18 (was 11)

### Migration Notes

**For users:**
- Use `ingest_missing folder="sessions" date="2026-01-18"` to ingest missing files from any folder
- Restart Claude CLI to see new tools (MCP servers don't auto-reload)

**For developers:**
- New tools use existing graph relationships (DISCUSSES_TOPIC, MENTIONS, SUPERSEDES)
- All new tools are async and follow existing error handling patterns

### Files Modified
```
ScholarGraph/
├── ingestion/batch_ingester.py     (added UTF-8 fix)
├── mcp_server/tools.py              (added 7 new tools, renamed ingest_missing)
└── mcp_server/server.py             (added 7 tool schemas and handlers)
```

---

## [0.2.1] - 2026-01-22

### Added
- **MCP Ingestion Tools** - Direct document ingestion via MCP protocol
  - `ingest_document` - Ingest single PDF or Markdown file with auto-detection
  - `ingest_batch` - Batch ingest from directory with glob patterns
  - `delete_document` - Remove documents by ID or file path
- **Project-level CLAUDE.md** - Context documentation for Claude Code CLI
  - Neo4j credentials and connection details
  - ScholarGraph import patterns
  - MCP usage examples

### Changed
- **MCP Server now supports full CRUD operations**
  - Previously: Search/query only (read-only)
  - Now: Create, read, update, delete via MCP tools
- **Total MCP tools**: 11 (was 8)

### Migration Notes

**For users:** Claude Code CLI can now ingest documents directly through MCP without creating scripts.

**For developers:** Use `ingest_document` for single files, `ingest_batch` for directories.

### Files Modified
```
ScholarGraph/
├── .claude/CLAUDE.md                (new)
├── mcp_server/tools.py              (added ingest_document, ingest_batch, delete_document)
└── mcp_server/server.py             (added 3 new tool schemas and handlers)
```

---

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
