# Seed Job Design

## 1. Overview

This module seeds LinkedIn enrichment jobs into the MySQL `enrichment_jobs` table.

It ensures controlled, idempotent job creation for speakers who:

- Do not yet have a current LinkedIn profile  
- Do not already have an active enrichment job  

This script acts as the entry point into the asynchronous enrichment pipeline.

It does NOT execute enrichment — it only schedules jobs.

---

## 2. Architecture Flow

seed_linkedin_enrichment_jobs()
   ├── get_connection()
   │     └── mysql.connector.connect()
   │
   ├── INSERT INTO enrichment_jobs
   │     └── SELECT speakers
   │           LEFT JOIN speaker_profiles
   │           LEFT JOIN enrichment_jobs
   │
   ├── commit()
   └── close()

---

## 3. Configuration

The script depends on:

```python
from config.settings import DB_CONFIG
```

This provides:

- Database host
- Port
- Username
- Password
- Database name

Active job statuses are defined as:

```python
ACTIVE_JOB_STATUSES = ("pending", "dispatched", "retry_scheduled")
```

These statuses represent jobs that are already in progress or scheduled.

---

## 4. Seeding Logic Conditions

A new enrichment job is inserted only if:

1. The speaker does NOT have a current LinkedIn profile  
   (`speaker_profiles.is_current = TRUE`)

2. The speaker does NOT have an active enrichment job  
   (status in pending, dispatched, retry_scheduled)

This prevents:

- Duplicate enrichment jobs  
- Parallel execution conflicts  
- Unnecessary API calls  
- Data inconsistency  

---

## 5. SQL Logic

### Insert Query

```sql
INSERT INTO enrichment_jobs (
    speaker_id,
    job_type,
    status,
    attempt_count,
    max_attempts
)
SELECT
    s.speaker_id,
    'linkedin_resolution',
    'pending',
    0,
    5
FROM speakers s
LEFT JOIN speaker_profiles sp
    ON s.speaker_id = sp.speaker_id
    AND sp.is_current = TRUE
LEFT JOIN enrichment_jobs ej
    ON s.speaker_id = ej.speaker_id
    AND ej.status IN ('pending', 'dispatched', 'retry_scheduled')
WHERE sp.speaker_id IS NULL
AND ej.job_id IS NULL
```

### Behavior

- Inserts one job per eligible speaker
- Ensures no current profile exists
- Ensures no active job exists
- Sets:
  - job_type = linkedin_resolution
  - status = pending
  - attempt_count = 0
  - max_attempts = 5

---

## 6. ETL Stage Role

This script operates between:

```
Canonical Speakers → Enrichment Jobs → Dispatcher
```

It does NOT:

- Perform LinkedIn search
- Call n8n
- Generate persona
- Modify speaker profiles

It strictly prepares jobs for downstream execution.

---

## 7. Database Interaction

### Connection Handling

```python
conn = get_connection()
cursor = conn.cursor()
```

- One connection per run
- One cursor per execution

### Transaction Handling

```python
conn.commit()
cursor.close()
conn.close()
```

- Single commit at end
- Ensures atomic insert
- Rollback on exception

---

## 8. Idempotency Design

The script is safe to run multiple times.

Why?

Because:

- Speakers with current profiles are excluded
- Speakers with active jobs are excluded

Running it again results in:

- Zero additional jobs (if none qualify)

This makes the seeder deterministic and repeatable.

---

## 9. Execution

Run directly:

```
python seed_linkedin_enrichment_jobs.py
```

Output:

```
Inserted X new enrichment jobs.
```

If no speakers qualify:

```
Inserted 0 new enrichment jobs.
```

---

## 10. Design Principles

### 10.1 Separation of Concerns

Seeder:
- Creates jobs

Dispatcher:
- Executes jobs

Resolver:
- Enriches data

Profile Table:
- Stores versioned results

Each layer has one responsibility.

---

### 10.2 Controlled Queue Entry

Speakers enter the enrichment pipeline only when:

- They lack enrichment
- They are not already queued

This avoids system overload and race conditions.

---

### 10.3 Retry-Compatible

Jobs are created with:

- attempt_count = 0
- max_attempts = 5

Retry logic is handled by the dispatcher.

Seeder does not manage retry scheduling.

---

## 11. Performance Characteristics

- Single SQL insert-select operation
- No per-row iteration
- Efficient batch scheduling
- Scales linearly with speaker count

---

## 12. Failure Handling Strategy

If an exception occurs:

```python
conn.rollback()
```

Ensures:

- No partial job creation
- No inconsistent queue state

Connection and cursor are always closed in `finally`.

---

## 13. System Role in GTM Automation

This module forms the first step of the enrichment lifecycle:

```
speakers
   ↓
enrichment_jobs (pending)
   ↓
dispatcher.py
   ↓
n8n webhook
   ↓
speaker_profiles (versioned)
```

It guarantees clean, deterministic entry into the LinkedIn resolution pipeline.

---

## Conclusion

The LinkedIn Enrichment Job Seeder implements:

- Controlled job scheduling  
- Strict eligibility rules  
- Idempotent execution  
- Safe transactional behavior  
- Clean separation from execution layer  

It provides a stable foundation for scalable, asynchronous enrichment processing.