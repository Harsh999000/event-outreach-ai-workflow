# Lead Assignment Logic

## 1. Overview

This module assigns enriched speakers to the appropriate outreach owner.

Assignment is based on persona seniority and ensures:

- Clear ownership
- Escalation for senior contacts
- No duplicate lead assignments
- Deterministic routing

This module does NOT send messages.
It only defines ownership and priority.

---

## 2. Architecture Flow

assign_leads()
   ├── get_connection()
   │
   ├── fetch_unassigned_speakers()
   │     └── JOIN speaker_personas
   │     └── LEFT JOIN lead_assignments
   │
   ├── classify_assignment()
   │     └── Determine role + priority
   │
   ├── INSERT INTO lead_assignments
   │
   ├── commit()
   └── close()

---

## 3. Routing Rules

Assignment logic based on persona seniority:

| Seniority                | Assigned Role | Priority |
|--------------------------|--------------|----------|
| C_LEVEL                  | AE           | HIGH     |
| FOUNDER                  | AE           | HIGH     |
| VP_LEVEL                 | AE           | HIGH     |
| DIRECTOR                 | SDR          | MEDIUM   |
| MANAGER                  | SDR          | MEDIUM   |
| UNKNOWN / Others         | SDR          | LOW      |

---

## 4. Escalation Logic

Strategic personas (C-Level / Founder / VP):

- Assigned to AE
- Marked HIGH priority
- Suitable for leadership-level outreach

Functional personas:

- Assigned to SDR
- Medium priority

Operators / Unknown:

- Assigned to SDR
- Lower priority queue

---

## 5. Duplicate Prevention

Enforced via:

```
UNIQUE (speaker_id)
```

Each speaker can only have one assignment.

Script uses:

```
LEFT JOIN lead_assignments
WHERE la.speaker_id IS NULL
```

This ensures idempotent execution.

---

## 6. Assignment Table Design

Table: `lead_assignments`

Fields:

- speaker_id
- assigned_to
- role (SDR / AE / LEADERSHIP)
- priority (HIGH / MEDIUM / LOW)
- assigned_at

Purpose:

- Ownership tracking
- Reporting
- Duplicate prevention
- Escalation visibility

---

## 7. System Role

Full GTM Workflow:

Raw Ingestion  
→ Enrichment  
→ Persona Generation  
→ Lead Assignment  
→ Outreach Status  
→ Message Generation  
→ Phase Advancement  
→ Send Engine  

Lead Assignment sits between intelligence and outreach execution.

---

## 8. Design Principles

- Deterministic routing
- Seniority-driven escalation
- Idempotent execution
- Clear ownership mapping
- Extendable for future rules (geo, company size, industry)

---

## Conclusion

The Lead Assignment module ensures that:

- Strategic accounts receive AE attention
- Mid-level contacts route to SDR
- Ownership is enforced
- No duplicate outreach occurs

It transforms enrichment intelligence into actionable GTM workflow.