# Canonicalization Design

## 1. Overview

The canonicalization layer converts raw speaker records into stable real-world identities.

It separates event appearances from individuals.

It implements a deterministic ETL pipeline with strict identity constraints:

- Extract → Fetch unmapped raw rows
- Transform → Normalize name + extract company
- Load → Insert or update canonical identity
- Map → Link raw record to canonical speaker

No AI is used in this layer.

This ensures reproducibility, idempotency, and structural stability.

---

## 2. Architecture Flow

    canonicalize()
   ├── fetch_unmapped_rows()
   │
   ├── normalize_name()
   │
   ├── extract_company()
   │
   ├── generate_identity_hash()
   │
   ├── upsert_speaker()
   │     ├── INSERT (if new)
   │     └── UPDATE last_seen_year (if exists)
   │
   ├── insert_mapping()
   │
   ├── commit()
   │
   └── close()

---

## 3. Identity Definition

Canonical identity is defined as:

normalized_name + normalized_company

Identity hash:

SHA256(normalized_name + "|" + normalized_company)

This hash is stored in:

speakers.identity_hash

Enforced via:

UNIQUE(identity_hash)

---

## 4. Why Not Name Alone?

Multiple individuals may share identical names.

Example:

- Vishal Gupta (Founder)
- Vishal Gupta (CTO)
- Vishal Gupta (Investor)

Using name alone would incorrectly merge identities.

Including normalized_company reduces false merges.

---

## 5. Deterministic Design Rules

This layer must:

- Never use AI
- Never use fuzzy matching
- Never reorder names
- Never guess middle names
- Never infer career transitions

It must remain conservative.

If identity is ambiguous → keep separate.

Probabilistic reconciliation belongs in enrichment.

---

## 6. Normalization Rules

### 6.1 Name Normalization

Steps:

1. Convert to lowercase
2. Remove punctuation (., ')
3. Remove honorifics:
   - mr
   - ms
   - mrs
   - dr
   - prof
   - shri
   - honble
   - hon'ble
   - minister
4. Collapse multiple spaces
5. Trim whitespace

Example:

"Hon'ble Minister Shri Kinjarapu Rammohan Naidu"

Becomes:

kinjarapu rammohan naidu

---

### 6.2 Company Extraction

Company is deterministically extracted from designation_raw.

Rules applied in order:

1. Split on " at "
2. Split on "|"
3. Split on "-"
4. Split on ","

If no pattern matches → company = NULL.

Examples:

"CEO at Ola Electric" → ola electric  
"Founder | Snapdeal" → snapdeal  
"Managing Director - Accenture" → accenture

No guessing. No inference.

---

## 7. ETL Stages

### 7.1 Extract – Fetch Unmapped Rows

Query logic:

    SELECT r.id, r.name, r.designation_raw, r.event_year
    FROM speakers_raw r
    LEFT JOIN speaker_raw_map m ON r.id = m.raw_id
    WHERE m.raw_id IS NULL;

Behavior:

- Only processes unmapped rows
- Ensures idempotency
- Safe to re-run

---

### 7.2 Transform – Normalize + Hash

For each raw row:

    normalized_name = normalize_name(name)
    normalized_company = extract_company(designation_raw)
    identity_hash = SHA256(name + "|" + company)

All transformations are deterministic.

---

### 7.3 Load – Upsert Identity

If identity exists:

    UPDATE last_seen_year if newer

If identity does not exist:

    INSERT new row

Identity uniqueness enforced via:

UNIQUE(identity_hash)

---

### 7.4 Map – Link Raw to Canonical

Insert mapping row:

    INSERT INTO speaker_raw_map (speaker_id, raw_id, event_year)

raw_id is UNIQUE to prevent duplicate mapping.

---

## 8. Idempotency Guarantees

The process is safe to re-run because:

- Only unmapped raw rows are selected
- identity_hash is UNIQUE
- raw_id is UNIQUE in speaker_raw_map

Re-running canonicalization does not duplicate records.

---

## 9. Conservative Identity Strategy

If the same person changes company across years:

They will appear as separate canonical identities.

This is intentional.

Deterministic layer does not assume career transitions.

Probabilistic reconciliation can merge identities later using LinkedIn resolution.

---

## 10. Failure Handling Strategy

If canonicalization fails mid-run:

- Transaction rollback prevents partial state corruption
- Process can safely be re-run
- No duplicate identities are created

---

## 11. Performance Characteristics

- Single DB connection per run
- Single commit per batch
- O(n) operations
- Suitable for 200–2000 contact batches

---

## 12. Design Benefits

- Prevents duplicate enrichment jobs
- Preserves traceability from raw → identity
- Keeps identity logic deterministic
- Enables clean separation between data and inference
- Supports scaling

---

## Conclusion

Canonicalization is the stability layer of the system.

It ensures:

Facts remain facts.  
Identities remain deterministic.  
Enrichment remains probabilistic.  

This separation protects the system from silent corruption and identity drift.