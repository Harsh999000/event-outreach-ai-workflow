# AI GTM Automation System

An end-to-end AI-powered Go-To-Market (GTM) automation pipeline that transforms event speaker lists into enriched profiles, structured personas, routed lead assignments, and lifecycle-managed outreach workflows — built entirely using free, self-hosted tools.

---

## Overview

This project demonstrates a layered GTM automation architecture that:

1. Ingests event speaker data  
2. Deduplicates canonical identities  
3. Enriches LinkedIn profiles via search proxy  
4. Generates structured AI personas  
5. Assigns leads based on seniority  
6. Creates multi-phase outreach sequences  
7. Controls lifecycle progression  
8. Simulates compliant outreach delivery  

The system is deterministic, versioned, auditable, and rate-limit aware.

---

## Architecture Layers

### 1. Raw Ingestion Layer
- Scrapes event speaker list
- Stores immutable raw data
- Enforces hash-based idempotency

Tables:
- `speakers_raw`

---

### 2. Canonical Identity Layer
- Deduplicates individuals
- Maintains identity hash
- Separates event appearances from real-world identity

Tables:
- `speakers`
- `speaker_raw_map`

---

### 3. Enrichment Layer (Async)
- Uses SearXNG search proxy
- Resolves LinkedIn URLs
- Applies confidence scoring
- Versions enrichment data

Tables:
- `enrichment_jobs`
- `speaker_profiles`

---

### 4. AI Persona Generation
- Uses local LLM (Ollama)
- Generates structured JSON personas
- Produces:
  - persona_summary
  - context_summary
  - personalization_themes

Table:
- `speaker_personas`

---

### 5. Lead Assignment Logic
- Routes leads based on seniority
- Escalates strategic profiles to AE
- Assigns others to SDR
- Enforces one owner per speaker

Table:
- `lead_assignments`

---

### 6. Outreach Lifecycle Engine
Manages deterministic state transitions:

```
pre_event → during_event → post_event → closed
```

Table:
- `outreach_status`

---

### 7. Message Generation Engine
- Persona-driven email templates
- Pre / During / Post event sequences
- Messages stored before sending

Table:
- `outreach_messages`

---

### 8. Send Engine
- Sends only phase-aligned messages
- LinkedIn capped at 5 per run
- Tracks `is_sent` and timestamps
- No real external sending (safe simulation)

---

## Search Engine Strategy

To remain compliant and free-tier:

- Uses self-hosted SearXNG
- Only DuckDuckGo enabled
- No direct LinkedIn scraping
- No headless browser automation
- Rate-limited with adaptive backoff
- Retry logic with cooldown window

The system respects platform guardrails rather than bypassing them.

---

## Technology Stack

- Python (orchestration)
- MySQL (relational integrity)
- n8n (no-code workflow automation)
- SearXNG (search proxy)
- Ollama (local LLM)
- Draw.io (architecture diagrams)

All tools operate within free-tier constraints.

---

## Design Principles

- Immutable raw ingestion
- Deterministic canonical identity
- Versioned enrichment
- Structured AI output
- Explicit lifecycle states
- Idempotent execution
- Rate-limit aware search strategy
- Separation of facts and inference

---

## Scalability

Designed to scale from:

- 200 demo contacts  
to  
- 2,000+ small production batches  

Using:

- Indexed relational tables
- Async enrichment dispatcher
- Controlled request pacing
- Stateless lifecycle progression

---

## Compliance Philosophy

The system:

- Does not automate LinkedIn login
- Does not scrape protected pages
- Does not bypass rate limits
- Uses only publicly indexed search results
- Operates within responsible automation boundaries

---

## Repository Structure (High Level)

```
/scraper
/enrichment
/outreach
/config
/docs
```

Each layer is modular and independently testable.

---

## Project Goal

This repository demonstrates how to design a structured, AI-enhanced GTM automation engine that balances:

- Intelligence
- Determinism
- Compliance
- Cost control
- Operational resilience

It is designed as an architectural showcase rather than a spam automation tool.

---

## Author

Built as part of an AI GTM Automation exercise demonstrating system design, automation strategy, and lifecycle-based outreach logic.