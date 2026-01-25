---
title: "Home"
layout: home
---

![Michael Kenteris - AI Research & Education](/assets/images/home-cover.jpg)

# Welcome

This is the code and research portfolio of **Michael Kenteris**, Postdoctoral Researcher at the University of the Aegean.

## Affiliation

**[Intelligent Systems Laboratory (i-lab)](https://i-lab.aegean.gr/)**
**[Semantic Web of Things (SWoT) Group](https://i-lab.aegean.gr/swot/)**
Department of Information & Communication Systems Engineering
University of the Aegean

---

## Notice

⚠️ **Pre-publication Code** - This repository contains unpublished research.

**Copyright © 2025 University of the Aegean. All Rights Reserved.**

Do NOT use, copy, modify, distribute, or cite without explicit permission from the author.

---

## Featured Projects

### [ScholarGraph](ScholarGraph/) - Research Knowledge Graph with GraphRAG

A GraphRAG system that gives Claude Code persistent memory of research literature.

- 51-paper scoping review corpus indexed
- Neo4j knowledge graph with semantic search
- MCP server integration with Claude Code
- Local-first, privacy-preserving architecture

[Read more →](ScholarGraph/)

### [CEFR Validation Tool](teacherassessment/) - Educational Standards Validation

A triangulated validation framework for CEFR descriptors using keyword analysis, LLM ensembles, and expert review.

- Discovered 7.3% true misclassification rate
- Web-based expert review interface
- Multi-method validation approach
- Implications for LLM-grounded educational systems

### [FL-KG-LLM Scoping Review](fl-kg-llm-scoping-review/)

Systematic review of Federated Learning, Knowledge Graphs, and Large Language Models convergence in language education.

- Identifies critical research gaps
- Proposes neurosymbolic framework
- CEFR-aligned pedagogical grounding

## Posts

{% for post in site.posts limit:5 %}
### [{{ post.title }}]({{ post.url }})
*{{ post.date | date: "%b %d, %Y" }}*

{{ post.excerpt }}
{% endfor %}

## Contact

- **Email:** mkenteris@aegean.gr
- **GitHub:** [mkenteris01](https://github.com/mkenteris01)
- **LinkedIn:** [Michael Kenteris](https://www.linkedin.com/in/kenteris/)
- **Institution:** University of the Aegean, Department of Cultural Technology and Communication
