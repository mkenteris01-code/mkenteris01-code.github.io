---
title: "Giving AI Memory: A GraphRAG Approach to Persistent Research Context"
date: 2025-12-25 09:00:00 +0200
categories: [GraphRAG, Research, AI, Neo4j]
tags: [graphrag, mcp, neo4j, claude-code, research]
author: Michael Kenteris
excerpt: "How I gave Claude Code a permanent, structured memory using GraphRAG and the Model Context Protocol - moving from searching for information to synthesizing insights."
header:
  overlay_color: "#5e616c"
  overlay_image: /assets/images/ScholarGraph_LinkedIn.png
  caption: "ScholarGraph: A Research Knowledge Graph with GraphRAG"

![ScholarGraph: A Research Knowledge Graph with GraphRAG](/assets/images/ScholarGraph_LinkedIn.png)


## The Problem: AI Has No Long-Term Memory

As a researcher, I hit a wall that many in our field recognize. Despite the power of models like Claude Code, the "context window" remains a bottleneck—not just in size, but in signal-to-noise ratio.

I was drowning in:
- 51 scoping review papers on FL-KG-LLM convergence
- Methodology notes across multiple markdown files
- Complex codebases spanning multiple repositories
- Research gaps identified through months of systematic review

Every time I needed Claude Code to assist with a deep-tier research problem, I had to act as a **manual data entry clerk**, curating snippets and hoping I hadn't missed the one critical connection.

The problem wasn't the AI's intelligence; it was its **recall**.

<!--more-->

## The Solution: GraphRAG with MCP

To solve this, I built a GraphRAG (Retrieval-Augmented Generation) system integrated with Claude Code via the **Model Context Protocol (MCP)**.

Unlike standard RAG—which often relies on flat vector similarity—a Graph-based approach recognizes **relationships between entities**.

### What This Enables

| Before | After |
|--------|-------|
| Manually paste relevant paper sections | Ask: "What does my corpus say about FL privacy?" |
| Claude forgets after a few turns | Persistent context across entire conversation |
| No awareness of my research gaps | Automatic gap analysis when evaluating new papers |
| Generic responses | Answers grounded in my 51-paper corpus |

### The Architecture

```
Claude Code
    │
    ├─ MCP Protocol (stdio)
    │
    └─ ScholarGraph MCP Server
        │
        ├─ Neo4j (Knowledge Graph)
        │   ├─ 51 corpus papers
        │   ├─ Chunks with embeddings
        │   └─ Research gap metadata
        │
        └─ GPU Rig (Qwen 2.5 7B)
            └─ Embedding generation
```

**Key insight:** The MCP server gives Claude Code a **persistent, queryable memory** of my research. It doesn't just retrieve documents—it understands relationships.

## Why This Matters

### For Researchers

> "By giving my AI a memory system, I've moved from 'searching for information' to 'synthesizing insights.'"

The cognitive load of manual retrieval disappears. When I ask about "Dimension 2 grounding," Claude doesn't search the web—it queries **my** knowledge graph, where my 51 corpus papers and methodology notes already live.

### For 2026 and Beyond

This isn't just a complex setup for post-docs; it's **smart architecture**. Whether you are managing:
- Medical literature
- Federated learning protocols
- Legal documentation
- Software codebases

The pattern remains the same: **Knowledge Graphs provide the context that raw tokens cannot.**

## What It Actually Does

### 1. Semantic Search Over My Corpus

```bash
User: "Find papers about federated learning privacy mechanisms"

[Returns ranked results from MY 51 papers, not the internet]
- Tayyeh et al. (2024) - Score: 0.89
- Wei et al. (2019) - Score: 0.82
```

### 2. Gap Analysis

```bash
User: "Should I read this new preprint on KG-LLM integration?"

[Checks against MY identified research gaps]
→ "HIGHLY RELEVANT - Addresses FL+KG+LLM convergence (0% in your corpus)"
```

### 3. Persistent Context

```bash
User: "What did STUDY_029 say about validation?"
[Claude retrieves from graph, no re-pasting needed]

User: "Compare that to STUDY_037"
[Claude uses cached context, synthesizes comparison]
```

## The Research Gaps It Helps Track

My scoping review revealed critical gaps in FL-KG-LLM research:

| Gap | Corpus Coverage | Severity |
|-----|-----------------|----------|
| FL+KG+LLM Convergence | 0% (0/51) | CRITICAL |
| Dimension 2 Grounding | 0% (0/51) | CRITICAL |
| Validation Metrics | 9.8% (5/51) | HIGH |
| CEFR Alignment | 11.8% (6/51) | HIGH |

Now when I find new papers, I can immediately evaluate them against **these specific gaps**—not generic "relevance."

## Technical Highlights

- **Neo4j** for the knowledge graph (structured relationships, not just vectors)
- **MCP (Model Context Protocol)** for native Claude Code integration
- **Local GPU rig** (Qwen 2.5 7B) for embeddings—keeps data private
- **51 scoping review papers** indexed with semantic + keyword search
- **Research gap metadata** encoded in the graph

**Result:** Everything stays local, fast, and domain-specific.

## Reflection

This Christmas, while others were unwrapping physical gifts, I gave my AI something far more valuable:

> **A permanent, structured memory.**

Now when I prompt Claude Code, it doesn't guess. It queries the graph, pulls the exact information required, and ignores the noise.

It is the ultimate productivity gift—the ability to actually use my research at scale.

---

## Links

- **Full LinkedIn Article:** [A Researcher's Christmas Miracle: The Gift of GraphRAG Memory](https://www.linkedin.com/pulse/researchers-christmas-miracle-gift-graphrag-memory-michael-kenteris-ped7f/)
- **Technical Documentation:** [Z_AI_GLM_INTEGRATION.md](/docs/Z_AI_GLM_INTEGRATION.md)
- **ScholarGraph Repository:** [github.com/mkenteris01/ScholarGraph](https://github.com/mkenteris01/ScholarGraph)
- **MCP Protocol:** [github.com/anthropics/mcp](https://github.com/anthropics/mcp)

---

**Merry Christmas to my fellow researchers. May your loss functions be low and your context be ever relevant.**

*— Michael Kenteris*
*University of the Aegean*
