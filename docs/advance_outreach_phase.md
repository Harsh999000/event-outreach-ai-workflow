# Outreach Phase Advancement Engine

## 1. Overview

This module advances the outreach lifecycle state for speakers.

It moves each speaker forward exactly ONE lifecycle step per execution.

Lifecycle progression:

pre_event → during_event → post_event → closed

The script does NOT generate messages and does NOT send messages.

It strictly manages lifecycle state.

---

## 2. Architecture Flow

advance_outreach_phase()
   ├── get_connection()
   │
   ├── UPDATE outreach_status
   │     └── CASE-based state transition
   │
   ├── phase_updated_at = NOW()
   │
   ├── commit()
   └── close()

---

## 3. Lifecycle State Machine

State transitions:

| Current Phase | Next Phase   |
|---------------|--------------|
| pre_event     | during_event |
| during_event  | post_event   |
| post_event    | closed       |
| closed        | closed       |

Closed state is terminal.

---

## 4. Advancement Logic

Single SQL statement:

```sql
UPDATE outreach_status
SET event_phase =
    CASE
        WHEN event_phase = 'pre_event' THEN 'during_event'
        WHEN event_phase = 'during_event' THEN 'post_event'
        WHEN event_phase = 'post_event' THEN 'closed'
        ELSE event_phase
    END,
    phase_updated_at = NOW()
WHERE event_phase IN ('pre_event', 'during_event', 'post_event');
```

This guarantees:

- One-step advancement only
- No skipping states
- Closed records remain unchanged

---

## 5. Idempotency & Safety

The script is safe to run multiple times.

Behavior:

Run 1 → All records move one stage  
Run 2 → All records move next stage  
Run 3 → All records move to closed  
Run 4 → No records move  

Closed records are unaffected.

---

## 6. Transaction Handling

Wrapped in:

```
try:
    commit()
except:
    rollback()
```

Ensures:

- No partial lifecycle transitions
- Clean state on failure

---

## 7. System Role

Full GTM Pipeline:

Raw Ingestion  
→ Canonical Identity  
→ Enrichment  
→ Persona Generation  
→ Outreach Status Seeder  
→ Outreach Message Generator  
→ Outreach Phase Advancement  
→ (Future) Send Engine  

This module is the state machine controller.

---

## 8. Design Principles

- Explicit lifecycle management
- Deterministic state transitions
- No implicit time-based logic
- Manual control over progression
- Scalable to large datasets

---

## Conclusion

The Outreach Phase Advancement Engine transforms the outreach system from static message storage into a dynamic lifecycle state machine.

It ensures controlled, predictable, and auditable progression across event phases.