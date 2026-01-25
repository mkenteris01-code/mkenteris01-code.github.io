---
title: "From \"Trust Me\" to \"Show Me\": Context Graphs for AI Governance in Schools"
date: 2026-01-25 09:00:00 +0200
categories: [AI Governance, Education, Context Graphs]
tags: [ai-governance, education, context-graphs, teacher-workload, student-safety, responsible-ai]
author: Michael Kenteris
excerpt: "How can schools use AI safely without increasing teacher workload? Context graphs—think of them as AI receipts—shift us from trust me AI to show me AI, making visible what the system did, why, and who approved it."
---

![Context Graphs for AI Governance in Schools](/assets/images/context-graphs-schools.png)

## The Problem at Hand

In my postdoc research right now, I'm focused on a simple question: **how can schools use AI safely, consistently, and usefully—without increasing teacher workload?**

That problem is **AI governance**. It's not just a policy document. It's the practical way a school answers:
- What AI is allowed?
- What "aligned" means?
- Who approves classroom use?
- What happens when the tool gets it wrong?

<!--more-->

## Two Very Real Risks Schools Must Manage

### Risk 1: Quiet Pedagogical Drift

AI content can sound fluent but be:
- The wrong level for the student
- Off-objective from the learning goal
- Subtly biased in framing or perspective

This drift happens silently. A worksheet looks professional. The text flows well. But underneath, the AI may have drifted from curriculum alignment, from inclusive language practices, from the specific learning outcome intended.

### Risk 2: Student Safety and Privacy

The more visible risk includes:
- Data leaks
- Accidental sharing of personal information
- Unsafe handling of student work
- Biased or harmful content generation

Both risks require oversight. But teachers already carry huge cognitive load doing quality checks in their heads. AI shouldn't add another layer of "AI auditing."

## The Current Problem: "Trust Me" AI

Most AI systems in education operate on a "trust me" basis:
- The system generates content
- The output looks reasonable
- Teachers and students are asked to trust that it's appropriate
- When questions arise, there's no way to inspect what happened

This is the "black box" problem. We're asking schools to adopt AI while being unable to see inside the box.

## The Solution: "Show Me" AI with Context Graphs

We need **teachers-in-the-loop for final judgment**, but we should also shift routine checking and traceability onto the system.

That's why I'm working with the idea of **context graphs**—think of them as "AI receipts."

### What is a Context Graph?

A context graph is a structured record that captures:
- What standards the AI was meant to follow
- What constraints were applied
- What evidence the AI used
- What validation checks ran
- What the teacher approved
- How the output was generated

### From Black Box to Transparent Process

Instead of only showing the final worksheet or activity, the system keeps a complete, inspectable record:

```
┌─────────────────────────────────────────────────────┐
│  CONTEXT GRAPH: Grade 4 Science Worksheet          │
├─────────────────────────────────────────────────────┤
│  Standard: NGSS 4-LS1-1                             │
│  Constraints:                                       │
│    - Reading Level: 4th grade                       │
│    - Length: 200-300 words                          │
│    - Language: Inclusive, gender-neutral            │
│                                                      │
│  Evidence Sources:                                   │
│    - Curriculum Framework v2.3                      │
│    - Prior Student Work: Photosynthesis unit        │
│                                                      │
│  Validation Checks:                                  │
│    ✓ Reading level verified                         │
│    ✓ Bias scan passed                               │
│    ✓ Privacy check passed                           │
│    ✓ Content alignment verified                     │
│                                                      │
│  Teacher Approval: Dr. Chen - Oct 15, 2025          │
│  Used With: Class 4B (23 students)                  │
└─────────────────────────────────────────────────────┘
```

### The Network Graph Visual

The context graph above can be visualized as a network of connected nodes—each representing a decision point, a data source, a constraint, or an approval. This network:

- **Shows connections** between curriculum standards and generated content
- **Traces the lineage** of any AI-generated material
- **Makes visible** the constraints and safeguards in place
- **Provides accountability** at every step

When something looks off—or a privacy question comes up—you don't guess. You can inspect what happened.

## Three Key Benefits

### 1. Teachers-in-the-Loop

Teachers remain the final arbiters of appropriate content. But instead of auditing from scratch, they review a structured record showing what the AI did and why. This empowers meaningful oversight without constant starting-from-scratch review.

### 2. Student Safety

When questions arise about data handling, content appropriateness, or privacy, the context graph provides an audit trail. Schools can demonstrate compliance, identify issues, and improve safeguards based on actual usage data.

### 3. Less Cognitive Load

Rather than holding all quality checks in their heads, teachers can rely on systematized validation. The context graph surfaces what matters most—alignment, safety, quality—without requiring manual reconstruction of what the AI "was thinking."

## The Shift

This is the fundamental shift:

| Before: "Trust Me" | After: "Show Me" |
|-------------------|------------------|
| Black box AI | Transparent context graphs |
| Blind trust | Inspectable records |
| Manual auditing | Systematized traceability |
| Reactive problem-solving | Proactive governance |
| Increased teacher workload | Supported teacher decision-making |

## Why This Matters Now

Schools are under pressure to adopt AI. Teachers are under pressure to use AI wisely. Students are already using AI—sometimes appropriately, sometimes not.

Context graphs offer a path forward:
- **Practical**: Works with existing AI tools
- **Principled**: Built on transparency and accountability
- **Pedagogical**: Keeps teachers at the center of instructional decisions
- **Protective**: Provides real oversight for student safety

## Looking Forward

The goal isn't perfect AI. The goal is **governable AI**—AI that schools can adopt with confidence, use with clarity, and improve with evidence.

From "trust me" to "show me"—keeping students safe and making AI easier for teachers to use responsibly.

---

*This post reflects ongoing research into AI governance frameworks for educational contexts. For questions or collaboration opportunities, feel free to reach out.*
