---
title: "Small but Mighty: How I Built an AI That Actually Understands CEFR Levels"
date: 2026-01-02 09:00:00 +0200
categories: [Small Language Models, Education, iCALL, Federated Learning]
tags: [smollm2, edtech, cefr, lora, qlora, federated-learning, open-source, teacher-validation]
author: Michael Kenteris
excerpt: "Over the past month, I've built a system that validates AI outputs against a pedagogical knowledge graph before they reach teachers. Here's what worked, what failed, and why small models outperform commercial AI for educational content."
---

# Local Fine-Tuning with SmolLM2 — Complete Results & Lessons Learned

**The problem:** Teachers worldwide use ChatGPT for lesson planning—but it generates content that sounds polished yet is pedagogically wrong. A C1 activity marked for advanced learners contains A2 vocabulary. Grammar exercises ignore the proficiency framework that defines what students *should* know at each level. And there's no way to see *why* the AI made these choices.

**The solution:** Over the past month, I've built a system that validates AI outputs against a pedagogical knowledge graph before they reach teachers. Here's what worked, what failed spectacularly, and why I'm moving toward federated learning that respects privacy while improving collectively.

---

## Why This Matters (Beyond the Tech)

I spent years running an English language school in Mytilene. I've watched intelligent teachers waste time editing AI-generated lessons because they couldn't trust the pedagogy. I've also watched education budgets shrink while subscription costs to ChatGPT and Copilot grow. This project is my answer: **What if teachers could run better AI locally, understand its reasoning, and maintain full control?**

Here's the surprising discovery: **you don't need GPT-4 to do this. A 1.7B parameter model—small enough to run on consumer hardware—actually outperforms commercial AI on pedagogical tasks.**

---

## The Architecture: Three Key Ingredients

Instead of technical jargon, here's what I actually built:

**1. A Small, Efficient Model (SmolLM2-1.7B)**
Think of this like choosing a responsive small-town librarian over a distant encyclopedia database. SmolLM2 has 1.7 billion parameters—roughly 4x smaller than industry-standard models—but it's been trained on high-quality educational data. With 4-bit quantization (a compression technique), it runs on ~3GB of GPU memory. Most teachers' old gaming computers could run this.

**2. A Training Shortcut (QLoRA)**
Full fine-tuning a model is like repainting an entire house. LoRA (Low-Rank Adaptation) is like changing the accent wall—you only adjust about 1% of the model's weights (~18M out of 1.7B parameters). This means:
- Training happens 4x faster
- The fine-tuned adapter is only ~8 MB (fits on a USB stick)
- Federated learning becomes practical (more on this later)

**3. A Pedagogical Referee (Knowledge Graph)**
This is the innovation I'm most excited about. Instead of hoping an AI produces good lessons and crossing your fingers, I built a Neo4j knowledge graph that acts as an automated quality checker. It contains:
- CEFR-aligned vocabulary for levels Pre-A1 through C1
- Grammar constructions mapped to proficiency levels
- Real-time alignment scoring (ACI: Alignment Consistency Index)

Before any activity reaches a teacher, the system validates it: *Does this activity use vocabulary appropriate for B1? Does it include grammar structures that B1 students should know?* This is the difference between black-box AI and glass-box AI—teachers can see *why* something was generated.

---

## Phase 1: Baseline Testing — Proving Model Size Doesn't Matter

I compared five models on standardized CEFR validation prompts:

| Model             | Pedagogical Accuracy | Parameters | Type  |
|-------------------|----------------------|------------|-------|
| Qwen-7B           | 96.7%                | 7B         | Local |
| SmolLM2-1.7B      | 95.6%                | 1.7B       | Local |
| Mistral-7B        | 95.6%                | 7B         | Local |
| Claude 3.5 Sonnet | 93.3%                | Proprietary| API   |
| OpenHermes-7B     | 91.1%                | 7B         | Local |

**What this means in plain English:** SmolLM2 achieves 98.6% of Qwen's accuracy while being **4x smaller**. It even outperforms Claude 3.5 Sonnet on educational validation.

This single finding destroys the assumption that bigger equals better. For educational content generation specifically, this isn't true. Model size matters far less than having the right training data and pedagogical grounding.

---

## Phase 2: Generating Real Activities with Teacher Validation

Instead of generating activities in isolation, I worked directly with English teachers. The workflow:

1. Generate 160 pedagogical activities across CEFR levels
2. Have real teachers validate each one
3. Capture their feedback for training data

**Generation across proficiency levels:**

| Level  | Activities |
|--------|------------|
| Pre-A1 | 15         |
| A1     | 44         |
| A2     | 32         |
| B1     | 21         |
| B2     | 26         |
| C1     | 22         |

**Teacher validation results:**

| Status   | Count | Percentage |
|----------|-------|------------|
| Accepted | 133   | 83%        |
| Rejected | 22    | 14%        |
| Modified | 5     | 3%         |

**Why this matters:** Every rejection included structured teacher feedback:
- "Activity requires external resources not included"
- "Too complex for target level"
- "Vocabulary inappropriate for CEFR level"

Those 22 rejections with reasons? They become training data for Direct Preference Optimization (DPO)—a technique that teaches the model what *not* to do. The 5 modified activities show the specific deltas between what the AI generated and what teachers actually need.

This is the opposite of purely automated evaluation. Real humans make the calls.

---

## Phase 2A: Fine-Tuning Comparison—A Surprising Discovery

I trained two versions of SmolLM2 to compare approaches:

**Version 1: Base Model** (trained on pure completion data)
**Version 2: Instruct Model** (trained on structured chat-format data)

| Metric        | Base Model  | Instruct Model | Winner          |
|---------------|-------------|----------------|-----------------|
| Final Loss    | 0.0896      | 0.077          | Instruct (-14%) |
| Training Time | ~32 min     | ~32 min        | Tie             |
| A1-A2 Quality | Good        | Good           | Tie             |
| B1-B2 Quality | Good        | Good           | Tie             |
| C1 Quality    | Poor        | Poor           | **Both fail**    |

In plain terms: both versions work equally well for beginner and intermediate levels (A1-B2), but **both struggle with advanced learners (C1).** The real issue wasn't the training approach—it was the training data itself.

---

## What Actually Worked Well

### 1. The 6-Tier Prompt Structure Changed Everything

Early attempts used simple prompts (~500 characters). Loss: **15.97**. Terrible.

Then I examined the production prompts actually stored in Neo4j. They were structured differently—7000+ characters organized into six clear tiers:

1. **CRITICAL OUTPUT RULES** (max 400 words, stop cleanly)
2. **TASK DEFINITION** (what to create, what type of activity)
3. **CRITICAL CONSTRAINTS** (detailed CEFR level parameters)
4. **STRATEGIC GUIDELINES** (tone, difficulty progression, pacing)
5. **PEDAGOGICAL REASONING** (why this activity matters, learning outcomes)
6. **AVOIDANCE PATTERNS** (10+ specific things NOT to do)

Switching to this structured format brought training loss from **15.97 → 0.0896**.

**The insight:** Prompt complexity matters more than raw model size. A small model with a crystalline, well-structured prompt outperforms a large model with vague instructions. This has implications for how we think about prompt engineering in education.

### 2. The Knowledge Graph Prevents Hallucination

This is why I built the PKG (Pedagogical Knowledge Graph) in the first place. LLMs have a fundamental weakness: they generate plausible-sounding but factually incorrect content—a problem known as "hallucination" in the field.

By querying the knowledge graph for vocabulary constraints and grammar rules *before* generation, the system avoids this fundamental problem. After generation, real-time ACI (Alignment Consistency Index) scoring audits the output.

Across 16 SmolLM2-generated activities validated against the PKG: **average ACI score of 0.9873/1.0**

In practical terms: 98.7% of generated content aligns with pedagogical standards.

### 3. Teacher-in-the-Loop Validation Creates a Virtuous Cycle

The 83% acceptance rate from teachers provides three types of training data:
- **Positive examples** (133 accepted activities) → for supervised fine-tuning
- **Negative examples** (22 rejected activities with reasons) → for preference optimization
- **Correction deltas** (5 modified activities) → for targeted special training

This creates improvement in a way pure automation can't. Teachers aren't just evaluating—they're training the next version of the model with their feedback.

---

## What Failed (And Why It Matters)

### The C1 Diversity Problem — A Humbling Discovery

Both fine-tuned models fail on C1 holdout examples. The culprit? **Data, not architecture.**

Looking at the C1 training data:

```
21 Total C1 Examples:
├── Argue multiple perspectives (×11) ← 52% — Severely overrepresented
├── Synthesis task (×2)
├── Analysis task (×2)
└── Other scattered topics (×6)
```

The model learned: **"C1 = generate perspective arguments"**

When asked to generate a C1 activity, it dutifully generates... another perspective-arguing activity. Same structure, different content. This isn't a format problem. It's not a model architecture problem. **It's a data coverage problem.**

The solution wasn't technical—it was pedagogical. I generated 22 new C1 activities covering:
- **9 different activity types**: Writing, Discussion, Debate, Oral Presentation, Negotiation, Analysis, Synthesis, Research, Creative Production
- **18 diverse topics**: Technology, Environment, Philosophy, Business, Psychology, Politics, Ethics, Culture, Science, Education, Healthcare, Economics, Sustainability, Law, History, Linguistics, Art, Media
- **6 different formats**: Individual work, Small group, Whole class, Team debate, Peer review, Self-reflection

Currently 8 of 22 are validated and loaded into Neo4j. 14 remaining.

**The lesson:** Data diversity beats model size. A 1.7B parameter model with comprehensive, diverse training data will outperform a 70B model trained on repetitive data.

### Format Inconsistency — A False Alarm

Early on, I noticed a mismatch:
- System prompts specify: `## Title:`
- Teacher outputs use: `**Activity Title:**`

I spent time investigating whether this format inconsistency was breaking training. Then I realized: **both model architectures show identical failure patterns.** The format wasn't the issue.

This was actually a valuable insight: the models learned that multiple presentation styles are valid. Real teachers use different formats. The AI reflecting this diversity is actually *correct behavior*, not a bug.

**The meta-lesson:** Sometimes debugging means discovering that the "problem" wasn't actually a problem. Automation often masks the real issue.

### SmolLM2 Timeout Issues — Why Redundancy Matters

During batch generation of those 22 C1 activities, SmolLM2 (running on port 8004) experienced timeouts on 4 of 22 requests—an 18% failure rate. Rather than switching models, I kept SmolLM2 as the primary system and built reliability around it.

This highlighted the need for:
- Graceful timeout handling with user feedback
- Retry logic with exponential backoff
- Multiple model fallbacks (if Model A times out, try Model B)

For production systems serving teachers, reliability matters more than absolute peak performance.

---

## The Real Innovation: PKG as Pedagogical Loss Function

This is what I'm most excited about, and it's genuinely novel in the educational AI space.

Typical approach: Train a model on educational data, hope it produces good lessons, deploy it.

**My approach:** Use the knowledge graph as a pedagogical loss function.

Instead of training models blindly, the PKG provides:
- **Hard constraints**: Vocabulary MUST match the target CEFR level
- **Soft guidance**: Grammar SHOULD include specific constructions
- **Real-time feedback**: ACI score as a reward signal during training

This is symbolic-neural synthesis: the knowledge graph (symbolic, interpretable layer) audits the LLM (neural, statistical layer) before content is delivered to teachers.

For technical readers: This is the foundation for knowledge-guided reinforcement learning in education. The PKG doesn't replace the neural model—it guides it.

For non-technical readers: Think of it as peer review, but automated and instant. Every activity gets checked against pedagogical standards before a teacher ever sees it.

---

## Next Steps: Federated Learning with Privacy Preservation

The next research phase addresses a critical constraint: schools want to improve their AI models with their own curriculum data, but GDPR, FERPA, and privacy regulations prevent sharing raw student data. Current commercial solutions force an uncomfortable choice: maintain privacy or enable improvement.

**The research direction:** Federated learning with LoRA adapters offers a path forward.

**The federated approach:**

```
Classroom A (Greece) ──┐
Classroom B (Spain) ───┤→ Aggregator → Global model update
Classroom C (Japan) ───┘

(Each school trains locally)
```

Using FLoRA (Federated LoRA with heterogeneous ranks), each school:
1. Keeps SmolLM2-1.7B on their local server
2. Fine-tunes it with their own curriculum and student data
3. Shares only the LoRA adapter (~8 MB) for aggregation
4. Never shares raw data, model weights, or student information

**The benefits:**

| Actor | Benefit |
|-------|---------|
| Teachers | Models improve based on real pedagogy from their school |
| Schools | GDPR-compliant by design; raw data never leaves servers |
| Researchers | Access to real-world educational data with full consent |
| Students | Privacy preserved; no data sold to tech companies |

This is AI Act compliant, GDPR-safe, and actually aligns with how education *should* work: teacher expertise driving system improvement.

---

## Key Takeaways

**For educators evaluating AI tools:**
1. Ask: *Can I see why this tool suggested this activity?* If the answer is no, it probably shouldn't control your pedagogy.
2. Small, transparent models that teachers understand often outperform large black-box systems.
3. Real teachers validating AI outputs creates better training data than any automated metric.

**For developers building educational AI:**
1. You don't need a 70B model — SmolLM2-1.7B with proper fine-tuning achieves 98.6% of larger model accuracy for pedagogical tasks
2. Data diversity beats model size — C1 failures came from repetitive training data, not architectural limits
3. Prompt complexity matters — 7000-character structured prompts outperformed 500-character simple prompts by **17x in training loss**
4. Teacher validation is irreplaceable — 83% acceptance rate with structured rejection feedback creates better training data than automation alone
5. Local deployment is viable — With QLoRA, you can fine-tune state-of-the-art small models on consumer hardware (4-6 GB VRAM)
6. Privacy is achievable — Federated learning with LoRA enables collaborative improvement without any data sharing

**For researchers:**
This work bridges symbolic and neural AI in education. The PKG-guided approach opens possibilities for knowledge-grounded reinforcement learning, where domain expertise (pedagogy) directly constrains and guides neural model behavior.

---

## What I'm Building Toward

- **Complete 22 diverse C1 activities** (currently 8/22 teacher-validated)
- **Retrain models** with expanded C1 coverage and validate improvement metrics
- **Implement FLoRA federated aggregation** with proper loss weighting for heterogeneous client data
- **Deploy federated learning pilot** with 2-3 schools (Greece, Spain, Japan) in Q2 2026
- **Publish academic results** on pedagogical viability of PKG-grounded small language models for education

---

## References & Methods

| Method/Framework | Source | Application |
|------------------|--------|-------------|
| LoRA | Hu et al. (Microsoft) | Low-rank parameter-efficient fine-tuning |
| QLoRA | Dettmers et al. | 4-bit quantization for memory efficiency |
| FLoRA | Wang et al. (UMD) | Federated LoRA with heterogeneous ranks |
| SLoRA | Babakniya et al. | Sparse federated fine-tuning optimization |
| DPO | Rafailov et al. (Stanford) / TRL Library | Direct Preference Optimization for teacher feedback |
| 6-Tier Prompts | Custom (derived from Neo4j PKG) | Structured pedagogical prompt engineering |
| PKG | Custom | Neo4j-based CEFR vocabulary + grammar constraints |
| ACI (Alignment Consistency Index) | Custom | Real-time pedagogical alignment scoring |

---

## Connect If You're Working on This

If you're a teacher frustrated with generic AI tools... a developer building transparent educational systems... or a researcher working on federated learning, privacy-preserving AI, or knowledge-grounded neural models... I'd like to hear what problems you're solving.

The intersection of pedagogy, transparency, and federated learning is where the most interesting work is happening. Let's connect.

---

**Location:** University of the Aegean, Department of Cultural Informatics
**Project:** The Pedagogical Forge — Hybrid Neuro-Symbolic AI for Intelligent Computer-Assisted Language Learning
**Current Phase:** Phase 2A complete, federated learning architecture design underway
