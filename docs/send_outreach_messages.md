# Outreach Send Engine

## 1. Overview

This module simulates delivery of outreach messages.

It sends messages only when:

- `is_sent = FALSE`
- `event_phase` matches current `outreach_status.event_phase`

It does NOT send real emails.
It does NOT send real LinkedIn messages.

It simulates delivery and updates database state.

---

## 2. Architecture Flow

send_outreach_messages()
   ├── get_connection()
   │
   ├── fetch_pending_messages()
   │     └── JOIN outreach_messages + outreach_status
   │
   ├── Channel Routing
   │     ├── Email → simulate email send
   │     └── LinkedIn → simulate LinkedIn send (max 5)
   │
   ├── mark_message_sent()
   │     └── is_sent = TRUE
   │     └── sent_at = NOW()
   │
   ├── commit()
   └── close()

---

## 3. Eligibility Criteria

A message is eligible to send if:

```sql
om.is_sent = FALSE
AND om.event_phase = os.event_phase
```

This ensures:

- Phase-aligned sending
- No premature sends
- No duplicate sends

---

## 4. LinkedIn Rate Limiting

Constraint:

```
MAX_LINKEDIN_PER_RUN = 5
```

If more than 5 LinkedIn messages are pending:

- Only first 5 are sent
- Remaining stay unsent
- Safe for manual rerun next day

---

## 5. Send Simulation

Email:

- Prints subject
- Prints first 120 characters of body
- Random delay 1–2 seconds

LinkedIn:

- Prints first 120 characters
- Random delay 1–2 seconds

No external API calls.
No real delivery.

---

## 6. State Update

After simulated send:

```sql
UPDATE outreach_messages
SET is_sent = TRUE,
    sent_at = NOW()
```

This ensures:

- Idempotent behavior
- Messages cannot be resent accidentally

---

## 7. Transaction Handling

Wrapped in:

```
try:
    commit()
except:
    rollback()
```

Ensures:

- No partial send state
- Safe recovery on failure

---

## 8. Lifecycle Behavior Example

Initial state: `pre_event`

Run send engine:

→ Sends pre_event email  
→ Sends pre_event LinkedIn  
→ Marks both sent  

Advance phase  

Run again:

→ Sends during_event email  

Advance phase  

Run again:

→ Sends post_event email  

Advance phase  

Run again:

→ Nothing sends  

Closed state produces no further sends.

---

## 9. System Role

Full GTM Workflow:

Raw Ingestion  
→ Canonical Identity  
→ Enrichment  
→ Persona Generation  
→ Outreach Status Seeder  
→ Message Generation  
→ Phase Advancement  
→ Send Engine  

This module operationalizes outreach.

---

## 10. Design Principles

- Phase-controlled delivery
- Idempotent message dispatch
- Manual safety controls
- LinkedIn rate-limit simulation
- Clean database state transitions

---

## Conclusion

The Outreach Send Engine transforms stored communication artifacts into a controlled lifecycle-driven delivery simulation.

It ensures:

- Correct phase sequencing
- Safe LinkedIn throttling
- Deterministic state mutation
- Auditability of sends

This completes the operational outreach pipeline.