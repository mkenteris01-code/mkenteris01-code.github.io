# ScholarGraph MCP Server - Quick Start

## Installation (5 minutes)

### 1. Install Dependencies
```bash
cd C:\projects\mkenteris01-code\ScholarGraph
pip install -r requirements.txt
```

### 2. Configure Claude Code

Edit `%USERPROFILE%\.claude\config.json` (Windows) or `~/.claude/config.json` (Linux/Mac):

```json
{
  "mcpServers": {
    "scholargraph": {
      "command": "python",
      "args": [
        "C:\\projects\\mkenteris01-code\\ScholarGraph\\mcp_server\\server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\projects\\mkenteris01-code\\ScholarGraph"
      }
    }
  }
}
```

**IMPORTANT:** Adjust paths for your system.

### 3. Restart Claude Code

```bash
exit
claude
```

## Quick Test

In Claude Code:

```
User: Use the list_corpus_papers tool

Claude: [Calls ScholarGraph MCP tool]
[Shows 51 scoping review papers]
```

If it works, you're done! 🎉

## Available Tools

| Tool | What It Does | Example |
|------|--------------|---------|
| `search_papers` | Search papers | "Find papers about FL privacy" |
| `get_paper_details` | Get full paper | "Show me STUDY_029" |
| `list_corpus_papers` | List corpus | "What papers are in my corpus?" |
| `compare_to_corpus_gaps` | Gap analysis | "Should I read this new paper?" |
| `get_database_stats` | DB stats | "How many papers in ScholarGraph?" |

## Available Resources

| Resource | What It Contains |
|----------|------------------|
| `research://papers` | All papers (JSON) |
| `research://corpus` | 51 corpus papers (JSON) |
| `research://gaps` | Research gaps (JSON) |
| `research://schema` | Neo4j schema (JSON) |
| `research://paper/{id}` | Full paper text |

## Common Usage Examples

### Find Papers on Topic
```
User: Find papers about federated learning privacy

Claude: [Calls search_papers]
[Returns top 5 results with citations]
```

### Evaluate New Paper
```
User: I found "FL-KG-LLM: Integrated Architecture". Should I read it?

Claude: [Calls compare_to_corpus_gaps]
HIGHLY RELEVANT - Addresses FL+KG+LLM convergence gap (0% in corpus)
```

### Review Corpus
```
User: What papers are in my scoping review corpus?

Claude: [Calls list_corpus_papers]
51 papers (STUDY_001 to STUDY_051)
```

### Check Research Gaps
```
User: What research gaps did I identify?

Claude: [Reads research://gaps]
- FL+KG+LLM convergence: 0%
- CEFR alignment: 11.8%
- Dimension 2 grounding: 0%
- Validation metrics: 9.8%
```

## Troubleshooting

### Can't Find MCP Module
```bash
pip install mcp uvicorn fastapi
```

### Can't Connect to Neo4j
1. Open Neo4j Desktop
2. Start `pkg.graphrag` database
3. Check `.env` credentials

### Claude Code Doesn't Show Tools
1. Check `~/.claude/config.json` paths are absolute
2. Restart Claude Code completely
3. Run: `python mcp_server/server.py` to check for errors

## Full Documentation

- **Complete Guide:** [docs/MCP_SERVER_GUIDE.md](docs/MCP_SERVER_GUIDE.md)
- **Implementation Details:** [docs/MCP_IMPLEMENTATION_SUMMARY.md](docs/MCP_IMPLEMENTATION_SUMMARY.md)
- **Project README:** [README.md](README.md)

---

**Status:** ✅ Ready to Use
**Setup Time:** ~5 minutes
**Last Updated:** December 25, 2025
