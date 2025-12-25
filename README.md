---
layout: home
---

# Federated Learning & Knowledge Graphs Research

## Description
This repository contains the codebase for post-doc research focusing on the intersection of Federated Learning (FL) and Knowledge Graphs (KG). 

## Tech Stack
* **Python**: Core logic
* **Neo4j**: Graph database storage
* **Google API**: Integration services

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with your API keys.

---
layout: home
title: Welcome to my Research Blog
---

## Recent Articles

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a> — {{ post.date | date: "%B %d, %Y" }}
    </li>
  {% endfor %}
</ul>
