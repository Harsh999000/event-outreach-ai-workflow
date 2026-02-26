# Enrichment Layer Specification

Component: LinkedIn URL Resolution  
Version: 1.0  
Status: Locked  
Layer: Probabilistic (Async + Versioned)

---

## 1. Purpose

Resolve LinkedIn URLs for canonical `speakers` using an asynchronous, retryable, and versioned enrichment architecture.

Layer Separation:

- Raw Layer → Deterministic & Immutable  
- Canonical Layer → Deterministic Identity Resolution  
- Enrichment Layer → Probabilistic, Async, Versioned  

This layer must never overwrite history and must remain fully observable.

---

## 2. Job Type

job_type = linkedin_resolution

Future-compatible job types:

- job_history_enrichment  
- seniority_inference  
- signal_extraction  

Backbone remains identical.

---

## 3. Enrichment Job States

States are stored in `enrichment_jobs.status`.

- pending
- dispatched
- search_completed
- validation_failed
- low_confidence
- completed
- retry_scheduled
- max_attempts_reached

These states form a strict state machine. No implicit transitions allowed.

---

## 4. State Definitions

### pending
Job created but not yet dispatched to n8n.

Owner: Python

---

### dispatched
Job payload sent to n8n webhook.

Owner: Python

---

### search_completed
n8n returned candidate LinkedIn URLs.

Owner: n8n → triggers Python validation

---

### validation_failed
Search returned no usable result OR validation score < 50.

Owner: Python

---

### low_confidence
Validation score between 50–69.

Owner: Python

Result found but insufficient confidence for automatic acceptance.

---

### completed
Validation score ≥ 70 and profile inserted into `speaker_profiles`.

Owner: Python

Side Effects:
- Insert new version row
- Mark previous profile rows as is_current = false
- Mark new row is_current = true

---

### retry_scheduled
Job marked for retry because attempt_count < max_attempts.

Owner: Python

---

### max_attempts_reached
Terminal failure state when attempt_count ≥ max_attempts.

Owner: Python

---

## 5. State Transitions

Primary Flow:

pending  
→ dispatched  
→ search_completed  
→ (completed | low_confidence | validation_failed)

Retry Flow:

validation_failed OR low_confidence  
→ if attempt_count < max_attempts  
    → retry_scheduled → pending  
→ else  
    → max_attempts_reached  

No other transitions are allowed.

---

## 6. Ownership of Transitions

Python owns:
- Job creation
- Dispatch to n8n
- Scoring logic
- State updates
- Retry logic
- Profile insertion and versioning

n8n owns:
- HTTP search orchestration
- Returning structured search results

n8n does NOT:
- Perform scoring
- Update database state
- Make acceptance decisions

n8n is an executor, not a decision engine.

---

## 7. Retry Policy

- max_attempts = 3
- attempt_count increments on each dispatch
- Retry allowed for:
  - No results
  - Ambiguous results
  - Parsing errors
- No retry for:
  - Deterministic mismatch (score < 50 with clear non-match)

Future enhancement:
Exponential backoff scheduling.

---

## 8. Confidence Scoring Contract

Exact normalized full name match → +40  
Company match → +40  
Slug similarity → +20  

Maximum score = 100

Acceptance thresholds:

- ≥ 70 → completed
- 50–69 → low_confidence
- < 50 → validation_failed

Scoring must be deterministic.  
No AI inference.  
No fuzzy matching.

---

## 9. Profile Insert Rules

When score ≥ 70:

Insert new row into `speaker_profiles` with:

- speaker_id
- linkedin_url
- confidence_score
- source = 'duckduckgo'
- enrichment_version = 1
- is_current = true
- enriched_at = NOW()

Before insert:
Set previous `speaker_profiles` rows for that speaker to is_current = false.

History is never overwritten.

---

## 10. Job Creation Rules

Create job ONLY if:

- Speaker has no `speaker_profiles` row where is_current = true
- No active job exists in:
  - pending
  - dispatched
  - retry_scheduled

Inserted Job Fields:

- job_type = 'linkedin_resolution'
- status = 'pending'
- attempt_count = 0
- max_attempts = 3
- created_at = NOW()

System must be idempotent and safe to re-run.

---

## 11. Architectural Principles

- Never mix deterministic and probabilistic layers.
- Enrichment must be async and versioned.
- Jobs must be observable and measurable.
- Database remains source of truth.
- System must scale from 200 → 2000 contacts without redesign.