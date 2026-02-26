# Database Interaction and Data Flow Diagram

## 1. Overview

This document describes how data moves through the database across all layers of the GTM Automation System.

It focuses strictly on:

- Table interactions
- Insert vs Update behavior
- Foreign key relationships
- State transitions

This represents the structural backbone of the system.

---

## 2. Core Database Tables

### Raw Layer
- speakers_raw

### Canonical Layer
- speakers
- speaker_raw_map

### Enrichment Layer
- enrichment_jobs
- speaker_profiles
- speaker_personas

### GTM Execution Layer
- lead_assignments
- outreach_status
- outreach_messages

---

## 3. End-to-End Data Flow

### Step 1 – Raw Ingestion

Script: Scraper

INSERT INTO:
- speakers_raw

Key properties:
- Immutable
- UNIQUE(data_hash)
- Batch tracked

No updates allowed except timestamp refresh.

---

### Step 2 – Canonical Identity Resolution

Process:

1. Normalize name and company
2. Compute identity_hash

INSERT INTO:
- speakers (if not exists)

INSERT INTO:
- speaker_raw_map

Behavior:
- Prevent duplicate identity
- Preserve raw-to-canonical traceability

---

### Step 3 – Enrichment Orchestration

Script: seed_linkedin_enrichment_jobs.py

INSERT INTO:
- enrichment_jobs

Script: dispatcher.py

UPDATE:
- enrichment_jobs (status lifecycle)

INSERT INTO:
- speaker_profiles (versioned)

UPDATE:
- previous speaker_profiles (is_current = 0)

Enrichment never overwrites. It versions.

---

### Step 4 – Persona Generation

Process:

LLM generates structured JSON.

INSERT INTO:
- speaker_personas

This table stores:
- persona_summary
- context_summary
- personalization_themes
- seniority
- function
- industry

Persona is tied to canonical speaker_id.

---

### Step 5 – Lead Assignment

Script: lead_assignment.py

INSERT INTO:
- lead_assignments

UNIQUE(speaker_id) ensures:
- One owner per lead
- No duplicate routing

---

### Step 6 – Outreach Lifecycle Initialization

Script: seed_outreach_status.py

INSERT INTO:
- outreach_status

Initial state:
- pre_event

---

### Step 7 – Message Generation

Script: generate_outreach_messages.py

INSERT INTO:
- outreach_messages

For each speaker:
- Pre-event email
- Pre-event LinkedIn
- During-event email
- Post-event email

Messages stored BEFORE sending.

---

### Step 8 – Lifecycle Advancement

Script: advance_outreach_phase.py

UPDATE:
- outreach_status.event_phase
- phase_updated_at

Deterministic single-step advancement.

---

### Step 9 – Send Engine

Script: send_outreach_messages.py

SELECT:
- outreach_messages
JOIN outreach_status

UPDATE:
- outreach_messages.is_sent = TRUE
- sent_at timestamp

LinkedIn limited to 5 per run.

---

## 4. Foreign Key Relationships

speakers_raw → speaker_raw_map → speakers  
speakers → enrichment_jobs  
speakers → speaker_profiles  
speakers → speaker_personas  
speakers → lead_assignments  
speakers → outreach_status  
speakers → outreach_messages  

All operational layers depend on canonical speaker_id.

This ensures:

- Central identity control
- No cross-layer duplication
- Clean relational integrity

---

## 5. Insert vs Update Philosophy

INSERT:
- speakers_raw
- speakers (first seen only)
- speaker_raw_map
- enrichment_jobs
- speaker_profiles (always new version)
- speaker_personas
- lead_assignments
- outreach_status
- outreach_messages

UPDATE:
- enrichment_jobs status
- speaker_profiles.is_current
- outreach_status.event_phase
- outreach_messages.is_sent

Facts are inserted.
State is updated.
Inference is versioned.

---

## 6. Data Integrity Guarantees

- UNIQUE(data_hash)
- UNIQUE(identity_hash)
- UNIQUE(speaker_id) in assignments
- Phase-aligned send filtering
- is_sent guardrail
- Versioned enrichment

The system prevents:

- Duplicate enrichment
- Duplicate routing
- Duplicate outreach
- Identity drift
- State corruption

---

## 7. Architectural Strength

This database flow ensures:

- Deterministic transitions
- Clear layer separation
- Safe reprocessing
- Auditability at every step
- Scalability to thousands of contacts

Data is never overwritten blindly.

Each mutation is intentional.

---

## Conclusion

The database interaction model forms the structural backbone of the GTM Automation System.

It enables:

- Clean ingestion
- Controlled enrichment
- Intelligent routing
- Lifecycle-managed outreach
- Auditable delivery tracking

All state changes are explicit, relational, and traceable.