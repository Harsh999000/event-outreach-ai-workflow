# Outreach Status Seeder

## 1. Overview

This module initializes the outreach lifecycle for enriched speakers.

It creates a row in `outreach_status` for each speaker who:

- Has a current enrichment profile
- Does not already have an outreach lifecycle record

Default lifecycle state:

pre_event

This module does NOT generate messages and does NOT send anything.

It strictly initializes state.

---

## 2. Architecture Flow

seed_outreach_status()
   ├── get_connection()
   │
   ├── SELECT enriched speakers
   │     └── JOIN speaker_profiles (is_current = 1)
   │
   ├── LEFT JOIN outreach_status
   │     └── Exclude existing rows
   │
   ├── INSERT new rows
   │     └── event_phase = 'pre_event'
   │
   ├── commit()
   └── close()

---

## 3. Eligibility Criteria

A speaker qualifies for lifecycle initialization if:

- speaker_profiles.is_current = 1
- No row exists in outreach_status

SQL logic:

```sql
JOIN speaker_profiles sp
    ON s.speaker_id = sp.speaker_id
    AND sp.is_current = 1

LEFT JOIN outreach_status os
    ON s.speaker_id = os.speaker_id

WHERE os.speaker_id IS NULL
```

---

## 4. Default Lifecycle State

All new rows are initialized with:

```
event_phase = 'pre_event'
```

This means:

The speaker is ready for pre-event outreach.

---

## 5. Idempotency Design

This script is safe to run multiple times.

Because:

- LEFT JOIN excludes speakers already initialized
- No duplicate rows can be inserted
- speaker_id is PRIMARY KEY in outreach_status

Running it again results in:

```
Inserted 0 new outreach_status rows.
```

---

## 6. Transaction Handling

All inserts are wrapped inside:

```
try:
    commit()
except:
    rollback()
```

Ensures:

- No partial lifecycle creation
- Clean database state on failure

---

## 7. System Role

Full GTM Flow:

Raw Ingestion  
→ Canonical Identity  
→ Enrichment  
→ Persona Generation  
→ Outreach Status Seeder  
→ Outreach Message Generator  
→ (Future) Send Engine  

This module marks the beginning of the communication lifecycle.

---

## 8. Design Principles

- State-driven workflow
- Strict separation of concerns
- Idempotent execution
- Deterministic initialization
- Scalable architecture

---

## Conclusion

The Outreach Status Seeder initializes lifecycle state for enriched speakers.

It ensures:

- Clean transition from enrichment to outreach
- Deterministic state tracking
- Controlled communication sequencing

This module forms the foundation of the outreach state machine.