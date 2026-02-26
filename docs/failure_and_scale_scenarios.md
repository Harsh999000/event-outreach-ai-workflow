# Failure & Scale Scenarios

## 1. Overview

This section defines how the GTM automation system handles real-world uncertainty and scaling challenges.

These scenarios are addressed logically without additional build complexity, as per assignment requirements.

---

## 2. LinkedIn Profile Not Found / Ambiguous

### Scenario

- No LinkedIn result found
- Multiple candidates with similar scores
- Low confidence score

### Current Handling

- Identity resolver assigns confidence_score
- confidence_level values:
  - AUTO_ACCEPT
  - REVIEW_REQUIRED
  - LOW_CONFIDENCE

### Logic Response

- If LOW_CONFIDENCE → do not auto-accept
- Enrichment job marked retry_scheduled
- Profile not inserted as current
- Speaker excluded from outreach generation

### Escalation Option

- Flag for manual review queue
- Allow human validation before profile activation

---

## 3. Low Confidence / Generic AI Personalization

### Scenario

- Persona themes are generic
- LLM output lacks relevance
- Missing enriched attributes

### Current Controls

- Strict JSON-only prompt
- Temperature = 0.2
- UNKNOWN fallback rule
- Exactly 2 personalization themes required

### Logical Safeguard

If themes are:

- Missing
- Repetitive
- Too generic

System falls back to:

```
["pricing intelligence", "competitive benchmarking"]
```

This ensures deterministic personalization baseline.

---

## 4. Duplicate Contacts with Minor Variations

### Scenario

- Same person appears twice
- Slight name variation
- Different email formats
- Multiple event years

### Current Protections

- Canonical identity_hash:
  SHA256(normalized_name + "|" + normalized_company)
- UNIQUE(identity_hash)
- speaker_raw_map ensures traceability

### Result

- Single canonical identity
- No duplicate enrichment
- No duplicate assignment
- No duplicate outreach

---

## 5. Duplicate Outreach Prevention

Protections exist at multiple layers:

1. UNIQUE(speaker_id, channel, event_phase)
2. is_sent flag
3. lifecycle phase matching
4. UNIQUE(speaker_id) in lead_assignments

This prevents:

- Duplicate routing
- Duplicate phase emails
- Duplicate LinkedIn outreach

---

## 6. Scaling from 200 → 2,000 Contacts

### Current Architecture Strengths

- BIGINT primary keys
- Indexed foreign keys
- Async enrichment dispatcher
- Versioned enrichment storage
- Stateless phase advancement

### Required Adjustments for 2,000+

1. Increase BATCH_SIZE in dispatcher
2. Add pagination for message sending
3. Add queue-based processing (future)
4. Move send engine to scheduled execution
5. Add monitoring & metrics table

### Not Required Yet

- No need for distributed system
- No need for Kafka
- No need for microservices

System scales comfortably to low thousands.

---

## 7. LinkedIn Platform Safeguards

Automation intentionally does NOT:

- Script LinkedIn login
- Use headless browsers
- Bypass platform protections

LinkedIn constraints respected:

- Max 5 manual reach-outs per run
- No repetitive scripting
- No automation fingerprint behavior

Protects account integrity.

---

## 8. Operational Resilience

Failure handling patterns:

- Retry logic in enrichment_jobs
- Rollback on DB errors
- Idempotent seeding
- Deterministic lifecycle state transitions

No silent failures.

---

## 9. Design Philosophy

System separates:

Facts → Inference → Routing → Lifecycle → Delivery

This layered architecture ensures:

- Failures are isolated
- No cascading corruption
- Safe re-runs
- Predictable recovery

---

## Conclusion

The system handles:

- Missing LinkedIn profiles
- Ambiguous enrichment
- Low-confidence AI outputs
- Duplicate contacts
- Outreach duplication
- Scaling to thousands

It remains deterministic, auditable, and resilient under realistic GTM operating conditions.