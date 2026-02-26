# Outreach Message Generation Engine

## 1. Overview

This module generates personalized outreach messages for enriched speakers.

It creates structured ABM communication artifacts across:

- Pre Event
- During Event
- Post Event

Messages are:

- Persona-driven
- Deterministic
- Stored in database
- Not sent automatically

This layer converts enrichment intelligence into structured communication records.

---

## 2. Architecture Flow

generate_outreach_messages()
   ├── get_connection()
   │
   ├── fetch_eligible_speakers()
   │     └── JOIN speakers + speaker_profiles + speaker_personas
   │
   ├── classify_persona()
   │
   ├── Generate Phase Messages
   │     ├── Pre Event (Email)
   │     ├── Pre Event (LinkedIn)
   │     ├── During Event (Email)
   │     └── Post Event (Email)
   │
   ├── INSERT INTO outreach_messages
   │
   ├── commit()
   └── close()

---

## 3. Eligibility Criteria

A speaker is eligible if:

- Has current enrichment profile (`is_current = 1`)
- Has persona stored in `speaker_personas`
- Does NOT already have outreach messages

SQL condition:

```sql
WHERE sp.is_current = 1
AND s.speaker_id NOT IN (
    SELECT speaker_id FROM outreach_messages
)
```

This ensures idempotent generation.

---

## 4. Persona Classification Logic

Persona type is derived deterministically from seniority.

### Strategic

- C_LEVEL
- FOUNDER
- VP_LEVEL

### Functional

- DIRECTOR
- MANAGER

### Operator

- All others or unknown

This classification controls tone and subject framing.

No LLM is used at this stage.

---

## 5. Message Generation Logic

Each eligible speaker receives:

### Pre Event

- 1 Email
- 1 LinkedIn Message

### During Event

- 1 Email

### Post Event

- 1 Email

Total per speaker: 4 messages

---

## 6. Personalization Inputs

Messages are built using:

- normalized_name
- normalized_company
- personalization_themes[0]
- personalization_themes[1]
- seniority-based persona_type

If themes are missing:

Fallback:

```
["pricing intelligence", "competitive benchmarking"]
```

---

## 7. Message Storage

All messages are inserted into:

### Table: outreach_messages

Fields used:

- speaker_id
- channel
- event_phase
- subject
- body
- persona_snapshot (JSON)
- generated_at (default)
- is_sent (default FALSE)

Persona snapshot ensures:

- Auditability
- Deterministic reproduction
- No regeneration drift

---

## 8. Idempotency Design

Messages are inserted only if speaker_id does not already exist in outreach_messages.

Additionally:

Database enforces:

```
UNIQUE (speaker_id, channel, event_phase)
```

This prevents duplicate phase generation.

---

## 9. Transaction Handling

All inserts occur inside:

```
try:
    ...
    conn.commit()
except:
    conn.rollback()
```

Ensures:

- No partial inserts
- Clean rollback on error
- Atomic generation per run

---

## 10. Execution

Run:

```
python generate_outreach_messages.py
```

Console Output:

```
Found X eligible speakers.
Generated outreach messages for speaker_id ...
Outreach message generation complete.
```

---

## 11. System Role

Full Flow:

Raw Ingestion  
→ Canonical Identity  
→ Enrichment  
→ Persona Generation  
→ Outreach Message Generation  
→ (Future) Send Engine  

This module is the first communication layer in the GTM system.

---

## 12. Design Principles

- Separation of concerns (generation ≠ sending)
- Persona-driven ABM structure
- Deterministic templates
- Structured audit trail
- Phase-based lifecycle
- Scalable architecture

---

## Conclusion

The Outreach Message Generation Engine transforms enriched speaker intelligence into:

- Structured, phase-based ABM messages
- Database-stored communication artifacts
- Fully auditable personalization
- Deterministic and idempotent message creation

It forms the foundation of the GTM Outreach Workflow layer.