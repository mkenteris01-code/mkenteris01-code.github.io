---
title: "CEFR Validation: How I Discovered 25% of Educational Standards Were Misclassified"
date: 2025-12-26 14:00:00 +0200
categories: [CEFR, Validation, Education, NLP]
tags: [cefr, validation, llm, knowledge-graphs, education]
author: Michael Kenteris
excerpt: "Using keyword analysis, LLM ensembles, and expert review to validate CEFR descriptor classifications—revealing significant misclassification rates in educational standards used for LLM grounding."
---

## The Problem: Educational Knowledge Graphs Need Validation

When building knowledge graphs for educational purposes, we often assume that authoritative sources are correct. The **CEFR (Common European Framework of Reference for Languages)** is the gold standard for language proficiency assessment—used across Europe and beyond.

But what happens when we import these standards into knowledge graphs that will be used to ground LLMs?

**I discovered that up to 25.6% of descriptors might be misclassified**—with significant implications for AI-powered language learning systems.

<!--more-->

## The Context: Why This Matters

Language learning applications increasingly use LLMs grounded in educational knowledge graphs. When a student asks:

> "What sociolinguistic skills should I practice for A1 level?"

The AI retrieves descriptors from the knowledge graph. If those descriptors are **wrongly categorized**, the student gets misaligned content.

### The Four CEFR Competencies

| Competence | What It Assesses | Example |
|------------|------------------|---------|
| **Sociolinguistic** | Social conventions, register, politeness | "Can recognise differences in formality" |
| **Oral Interaction** | Turn-taking, conversation management | "Can take turns in conversation" |
| **Pragmatic** | Functional language use, discourse coherence | "Can achieve communicative purposes" |
| **Linguistic** | Vocabulary, grammar, pronunciation | "Can use X vocabulary" |

**The issue:** Some descriptors labeled "Sociolinguistic" actually describe Interaction or Linguistic skills.

## The Validation Framework

I developed a **triangulated validation approach** using three methods:

### 1. Keyword-Based Validation

A systematic approach checking for indicator words:
- "acquire the turn", "eye contact" → Interaction
- "sign", "abbreviation", "vocabulary" → Linguistic
- "function", "coherence" → Pragmatic
- "register", "polite", "appropriate" → Sociolinguistic

**Result:** 21 violations (25.6%)

### 2. LLM Ensemble Validation

Using 4 models on my local GPU rig:
- Qwen2.5-7B
- Mistral-7B
- OpenHermes
- FunctionGemma-270M

Each model classified descriptors, with consensus determining the final category.

**Result:** 5 violations (6.1%)

### 3. Expert Review (Human-in-the-Loop)

A web application I built for expert validation, allowing teachers to:
- Confirm or reject automated flags
- Reclassify descriptors
- Add confidence ratings and notes

**Result:** 6 violations confirmed (7.3%)

## Key Findings

### Method Comparison

| Method | Violations | Precision | Recall |
|--------|------------|-----------|--------|
| Keyword-based | 21 (25.6%) | 28.6% | 100% |
| LLM Ensemble | 5 (6.1%) | 40.0% | 33.3% |
| Expert Review | 6 (7.3%) | 100% | 100% |

**Critical insight:** The keyword system **over-flags** (catches everything but has false positives), while LLMs are **too conservative** (miss real violations).

### All Three Methods Agree On Only 2 Descriptors

| ID | Descriptor | Assigned | Should Be |
|----|------------|----------|-----------|
| A2+_SOC_17 | "perform and respond to basic language functions" | Sociolinguistic | Pragmatic |
| B2+_SOC_52 | "recognise whether a text contains all information necessary" | Sociolinguistic | Linguistic |

These are the **strongest violations**—where all methods converge.

### The Multi-Category Problem

Many descriptors genuinely belong to **multiple categories**:

> *"Can establish basic social contact by using polite forms of greetings and farewells"* (A1)

This involves:
- **Sociolinguistic:** Knowing polite forms
- **Interaction:** Performing greetings/farewells
- **Pragmatic:** Achieving social contact

**Solution:** Multi-label classification in knowledge graphs, not forced single categories.

## The Web Tool

I built a Flask-based web application for expert review:

![CEFR Teacher Assessment Interface](/teacherassessment/screenshot.png)

**Features:**
- Direct Excel integration (reads/writes `.xlsx` files)
- Progress tracking (12/13 completed)
- Flagged-only filtering
- Confidence scoring (1-5)
- Expert notes field

**Tech Stack:**
- Python/Flask (backend)
- Vanilla JavaScript (frontend)
- openpyxl (Excel manipulation)
- pandas (data handling)

The tool enabled efficient expert review—completing validation of 82 descriptors in a single session.

## Implications for LLM Grounding

### The Risk

When an LLM queries "What sociolinguistic skills should A1 learners practice?", an unvalidated KG returns:

❌ "Can maintain eye contact" (Interaction, not Sociolinguistic)
❌ "Can acquire the turn" (Interaction mechanics)
❌ "Can use fingerspelling" (Linguistic vocabulary)

### The Solution

1. **Pre-deployment validation** of educational KGs
2. **Multi-method triangulation** (keyword + LLM + expert)
3. **Multi-label categories** for ambiguous descriptors
4. **KGQI scoring** with deployment thresholds

## What This Means for Educational AI

This isn't just about CEFR. The same issues exist in:

- Medical education KGs (procedural vs. conceptual knowledge)
- Programming taxonomies (syntax vs. algorithms)
- Historical reasoning frameworks (causation vs. correlation)

**Bottom line:** Authoritative sources are not infallible. When importing educational standards into knowledge graphs for LLM grounding, **systematic validation is essential.**

## The Numbers

| Level | Descriptors | Violations Confirmed |
|-------|-------------|----------------------|
| A1 | 10 | 0 (0%) |
| A2 | 7 | 0 (0%) |
| A2+ | 7 | 2 (29%) |
| B1 | 8 | 0 (0%) |
| B1+ | 5 | 0 (0%) |
| B2 | 10 | 0 (0%) |
| B2+ | 11 | 1 (9%) |
| C1 | 17 | 1 (6%) |
| C2 | 7 | 2 (29%) |

**Overall: 6/82 violations (7.3%)**

## Links

- **GitHub Repository:** [mkenteris01-code/cefr-validation-tool](https://github.com/mkenteris01-code/cefr-validation-tool)
- **Related Work:** [ScholarGraph](https://github.com/mkenteris01-code/ScholarGraph) - GraphRAG for research memory

---

*— Michael Kenteris*
*University of the Aegean*
