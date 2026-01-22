# Claude Context for mkenteris01-code

## Neo4j Database Access

When querying Neo4j directly or generating scripts:

**Connection Details:**
- URI: `bolt://127.0.0.1:7687` (Bolt) or `http://localhost:7474` (HTTP)
- Username: `neo4j`
- Password: `neo4jpkg01`

**For curl commands (HTTP API):**
```bash
curl -u "neo4j:neo4jpkg01" -X POST http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"MATCH (n) RETURN n LIMIT 10"}]}'
```

**For Python scripts (neo4j driver):**
```python
from neo4j import GraphDatabase

uri = "bolt://127.0.0.1:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "neo4jpkg01"))
```

**For cypher-shell (CLI):**
```bash
cypher-shell -u neo4j -p neo4jpkg01 "MATCH (n) RETURN count(n)"
```

## ScholarGraph Integration

ScholarGraph is installed as an editable Python package. Use MCP tools when possible:
- `search_papers` - Semantic/hybrid search across documents
- `check_sessions_ingested` - Verify session ingestion status
- `get_database_stats` - Get corpus statistics

For direct Python imports:
```python
import sys
sys.path.insert(0, r'C:\projects\mkenteris01-code\ScholarGraph')
from graph import Neo4jClient, VectorIndexManager
```

## Session Documents Location

Session markdown files are stored at:
```
C:\projects\AgenticAIpkg\docs\knowledge\sessions\
```
