# CEFR Descriptor Expert Review Guide

**For:** Language teachers, applied linguists, and CEFR experts
**Purpose:** Validate category classifications of CEFR Sociolinguistic Competence descriptors
**Date:** 2025-12-26

---

## Quick Start

1. Open **`CEFR_Validation_Review_Neo4j.xlsx`**
2. Go to the **Summary** sheet for overview
3. Review each level's sheet (A1, A2, B1, etc.)
4. Use the **dropdown menus** to record your decisions
5. Save and return when complete

---

## What You're Reviewing

We extracted **82 CEFR Sociolinguistic Competence descriptors** from the PKG Neo4j database (which faithfully imported the CEFR Companion Volume 2020).

An automated validation system flagged **21 descriptors (25.6%)** that may be in the **wrong category**.

**Your task:** Confirm whether these flags are correct or false positives.

---

## Background: The Category Problem

CEFR descriptors are organized into **activity categories**:

| Category | What It Assesses | Examples |
|----------|------------------|----------|
| **Sociolinguistic** | Social conventions, register, politeness, cultural appropriateness | "Can recognise differences in formality", "Can use appropriate address forms" |
| **Oral Interaction** | Turn-taking, conversation management, speech acts | "Can take turns in conversation", "Can make invitations" |
| **Pragmatic** | Functional language use, discourse coherence | "Can achieve communicative purposes", "Can maintain coherence" |
| **Linguistic** | Vocabulary, grammar, pronunciation knowledge | "Can use X vocabulary", "Can pronounce Y" |

**The issue:** Some descriptors labeled "Sociolinguistic" actually describe Interaction or Linguistic skills.

---

## Review Criteria

For each flagged descriptor, ask:

### 1. What is the PRIMARY skill being assessed?

Ignore the assigned label. Read the descriptor and ask: "What is this really testing?"

**Key questions:**
- Is this about **knowing when/how** to use language appropriately? → Sociolinguistic
- Is this about **managing the flow** of conversation (turns, eye contact)? → Oral Interaction
- Is this about **knowing words/grammar**? → Linguistic
- Is this about **achieving communication goals**? → Pragmatic

### 2. Look at the evidence keywords

The automated system flagged descriptors based on these keywords:

| If you see... | Likely belongs to... |
|---------------|---------------------|
| "acquire the turn", "give the floor", "turn-taking" | **Oral Interaction** |
| "eye contact", "visual feedback", "attract attention" | **Oral Interaction** |
| "socialise", "invitation", "apology", "greeting", "farewell" | **Oral Interaction** (speech acts) |
| "sign", "abbreviation", "vocabulary" | **Linguistic** |
| "register", "polite", "formal", "cultural convention", "appropriate" | **Sociolinguistic** ✓ |

### 3. Consider the CEFR level context

**A-levels (A1, A2):** Basic skills. Turn-taking mechanics (eye contact) may be PHYSICALLY necessary for sign language, not just social conventions.

**B/C-levels:** More advanced. Expect greater nuance between categories.

---

## How to Use the Excel File

### Columns Explained

| Column | What It Means | What to Do |
|--------|---------------|------------|
| **A (#)** | Row number | Reference only |
| **B (ID)** | Descriptor identifier | Reference only |
| **C (Text)** | The CEFR "can do" statement | Read and assess |
| **D (Assigned)** | Current category from CEFR CV | Compare with your assessment |
| **E (Issue?)** | Pre-filled: "YES" = flagged | Leave if correct, change if wrong |
| **F (Issue Type)** | Type of misclassification detected | Reference |
| **G (Evidence)** | Keywords that triggered the flag | Consider these |
| **H (Correct?)** | **YOUR DECISION** | Use dropdown: YES/NO/MAYBE |
| **I (New Category)** | If NO, what should it be? | Use dropdown OR select "CONFIRM" |
| **J (Confidence)** | How sure are you? | 1-5 (5 = very sure) |
| **K (Notes)** | Any comments? | Explain ambiguous cases |

### Dropdown Options

**Column H (Correct?):**
- **YES** = Original category is WRONG (flag is correct)
- **NO** = Original category is CORRECT (flag is false positive)
- **MAYBE** = Ambiguous, needs discussion

**Column I (New Category):**
- **Sociolinguistic** = Should stay in this category
- **Oral Interaction** = Should be moved here
- **Pragmatic** = Should be moved here
- **Linguistic** = Should be moved here
- **CONFIRM** = Same as selecting "Sociolinguistic" (original is correct)
- **NEEDS DISCUSSION** = Cannot decide alone

**Column J (Confidence):**
- **5** = Expert knowledge, no doubt
- **4** = Strong confidence
- **3** = Moderately confident
- **2** = Some uncertainty
- **1** = Very uncertain

---

## Example Decisions

### Example 1: Clear Violation

**Descriptor:** "Can attract attention in order to acquire the turn (e.g. by raising a hand)"

**Assigned:** Sociolinguistic
**Evidence:** "acquire the turn", "eye contact"

**Analysis:** This describes the MECHANICS of turn-taking (how to get the floor), not social conventions. When someone takes a turn vs. knowing HOW to politely ask for a turn.

**Decision:**
- H (Correct?): **YES** (flag is correct)
- I (New Category): **Oral Interaction**
- J (Confidence): **5**

---

### Example 2: False Positive

**Descriptor:** "Can recognise differences in register that the signer expresses manually and non-manually"

**Assigned:** Sociolinguistic
**Evidence:** (none - not flagged)

**Analysis:** This is explicitly about REGISTER (a core sociolinguistic concept).

**Decision:**
- H (Correct?): **NO** (flag is wrong)
- I (New Category): **CONFIRM**
- J (Confidence): **5**

---

### Example 3: Ambiguous Case

**Descriptor:** "Can make and respond to invitations, suggestions, apologies"

**Assigned:** Sociolinguistic
**Evidence:** "invitation", "apologise"

**Analysis:** Speech acts like "invitations" have BOTH:
- Functional aspect (Interaction: being able to invite)
- Social aspect (Sociolinguistic: knowing when it's appropriate)

**Decision:**
- H (Correct?): **MAYBE**
- I (New Category): **NEEDS DISCUSSION**
- J (Confidence): **2**
- K (Notes): "Speech acts have overlap - could be Interaction or Sociolinguistic depending on whether focus is on doing the act or knowing appropriateness"

---

## What Happens Next?

1. Your review will be used to:
   - Calculate the **true category violation rate**
   - Train/improve the automated validator
   - Decide which descriptors need reclassification in the PKG

2. Descriptors with **NEEDS DISCUSSION** will be reviewed by a panel

3. Results will be published in **Paper 2** (Applied Sciences journal)

---

## Questions?

If anything is unclear, please note it in column K (Notes) or contact:

**Researcher:** [Your Name]
**Email:** [Your Email]
**Project:** CEFR Knowledge Graph Validation for LLM Grounding

---

## Summary Statistics (Before Your Review)

| Metric | Value |
|--------|-------|
| Total descriptors | 82 |
| Flagged for review | 21 (25.6%) |
| A-level flags | 8/25 (32%) |
| B-level flags | 5/29 (17%) |
| C-level flags | 5/20 (25%) |

**After your review, we will know the TRUE validation rate.**

Thank you for your expertise!
