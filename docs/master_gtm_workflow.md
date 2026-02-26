# Master End-to-End GTM Automation Workflow

## 1. Overview

This document describes the complete lifecycle of the GTM AI Automation System — from raw event speaker ingestion to controlled outreach execution.

The system is designed as a layered architecture with strict separation between:

- Raw facts
- Canonical identity
- Enrichment inference
- AI persona intelligence
- Lead routing
- Outreach lifecycle
- Message delivery

Each layer is independent, deterministic, and auditable.

---

## 2. Full System Flow

Event Speaker List  
→ Scraper  
→ Canonical Identity  
→ Enrichment  
→ Persona Generation  
→ Lead Assignment  
→ Outreach Lifecycle  
→ Message Generation  
→ Phase Advancement  
→ Send Engine  

---

## 3. Step-by-Step Breakdown

### 3.1 Event Speaker List

Input:  
150 to 200 speakers from an event website.

This is the only external data source required for the workflow.

---

### 3.2 Scraper – Raw Ingestion Layer

Table: `speakers_raw`

Responsibilities:

- Fetch HTML
- Parse speaker blocks
- Generate ingestion_batch_id
- Generate SHA256 data_hash
- Enforce UNIQUE(data_hash)
- Preserve immutable raw data

Key Principle:
Raw data is never modified.

---

### 3.3 Canonical Identity Layer

Table: `speakers`

Purpose:

- Deduplicate individuals
- Create identity_hash using:
  normalized_name + "|" + normalized_company
- Maintain first_seen_year and last_seen_year

This layer represents real-world identity, not event appearances.

---

### 3.4 Enrichment Layer (Async)

Components:

- Python Dispatcher
- n8n Workflow
- SearXNG Search
- LinkedIn Identity Resolver
- Confidence Scoring
- Versioned speaker_profiles

Process:

1. Create enrichment_jobs
2. Resolve LinkedIn candidate
3. Score confidence
4. Insert versioned profile
5. Maintain is_current flag

Enrichment is probabilistic but version-controlled.

---

### 3.5 AI Persona Generation

Tool: Ollama (local LLM)

Output:

- persona_summary
- context_summary
- personalization_themes (exactly 2)

Safeguards:

- Strict JSON-only prompt
- Temperature 0.2
- UNKNOWN fallback rule

Persona is structured intelligence, not free text.

---

### 3.6 Lead Assignment Logic

Table: `lead_assignments`

Routing Rules:

| Seniority | Assigned Role | Priority |
|------------|---------------|----------|
| C-Level / Founder / VP | AE | HIGH |
| Director / Manager | SDR | MEDIUM |
| Others | SDR | LOW |

Guarantees:

- One owner per speaker
- No duplicate routing
- Escalation for senior profiles

This transforms intelligence into GTM action.

---

### 3.7 Outreach Lifecycle State

Table: `outreach_status`

Phases:

- pre_event
- during_event
- post_event
- closed

Phase advancement is controlled and deterministic.

Each execution moves only one step forward.

---

### 3.8 Message Generation Engine

Table: `outreach_messages`

For each speaker:

- Generate Pre-Event email
- Generate Pre-Event LinkedIn
- Generate During-Event email
- Generate Post-Event email

Messages are:

- Persona-driven
- Template-based
- Stored before sending
- Snapshot of persona included

This ensures auditability and safe preview.

---

### 3.9 Phase Advancement Engine

Script: `advance_outreach_phase.py`

Moves lifecycle:

pre_event → during_event → post_event → closed

No skipping.
No auto-close.
Manual control ensures predictability.

---

### 3.10 Send Engine

Script: `send_outreach_messages.py`

Eligibility:

- is_sent = FALSE
- event_phase matches outreach_status

Channel Logic:

- Email simulated
- LinkedIn simulated
- Max 5 LinkedIn per run

After send:

- is_sent = TRUE
- sent_at timestamp stored

Prevents duplicate outreach.

---

## 4. Architectural Characteristics

### 4.1 Deterministic

- No overwriting enrichment
- No random lifecycle jumps
- Idempotent seeding
- Explicit state transitions

---

### 4.2 Layered

Each stage depends only on the previous layer’s outputs.

Failure in one layer does not corrupt others.

---

### 4.3 Auditable

- Versioned enrichment
- Persona snapshots stored
- Assignment tracking
- Send timestamps recorded
- Lifecycle phase tracked

Every decision can be traced.

---

### 4.4 Scalable

Designed for:

- 200 contacts (demo scale)
- 2,000 contacts (small production scale)

Scaling supported via:

- Indexed tables
- Async enrichment
- Controlled batching
- Stateless lifecycle engine

---

## 5. Separation of Concerns

The system strictly separates:

Facts → Inference → Routing → Lifecycle → Delivery

This prevents:

- AI hallucination corruption
- Duplicate outreach
- Escalation failures
- State drift

---

## 6. Complete Lifecycle Summary

1. Ingest speakers
2. Deduplicate identity
3. Enrich LinkedIn profile
4. Generate persona intelligence
5. Assign lead owner
6. Create structured outreach
7. Advance lifecycle
8. Send phase-aligned messages
9. Close lifecycle

The system moves from raw event list to structured GTM execution in a controlled and repeatable manner.

---

## Conclusion

The Master Workflow demonstrates a complete GTM automation lifecycle that is:

- Structured
- Layered
- Deterministic
- Resilient
- Scalable
- Compliant with platform constraints

It transforms event attendee data into actionable, personalized, and phase-controlled outreach without sacrificing system integrity.