# Scraper Design

## 1. Overview

This scraper ingests speaker data from the TechSparks event website into a MySQL database.

It follows a structured ETL architecture:

- **Extract** → Fetch HTML from event website  
- **Transform** → Parse speaker blocks and structure data  
- **Load** → Insert into `speakers_raw` table with idempotency  

Each event year (2024, 2025) may have different HTML structure, but the ingestion logic remains consistent.

---

## 2. Architecture Flow

scrape()
   ├── fetch()
   │     └── requests.get()
   │
   ├── parse_speaker_blocks()
   │     └── BeautifulSoup + CSS selectors
   │
   └── store_speaker_list()
         ├── generate_batch_id()
         ├── generate_hash()
         ├── INSERT ... ON DUPLICATE KEY
         ├── commit()
         └── close()

---

## 3. Configuration

Each scraper defines:

```python
URL
EVENT_YEAR
EVENT_NAME
```

These constants define:

- Source page
- Event context
- Hash uniqueness scope

---

## 4. Batch ID Generation

```python
def generate_batch_id():
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    return f"TS{EVENT_YEAR}_{now_ist.strftime('%Y%m%d%H%M%S')}"
```

### Purpose

- Creates traceable ingestion identifier
- Includes event year
- Uses IST timestamp for demo clarity

Example:

```
TS2025_20260224173512
```

---

## 5. Hash Generation (Idempotency Layer)

```python
def generate_hash(name, designation, year):
    raw_string = f"TS{name}|{designation}|{year}"
    return hashlib.sha256(raw_string.encode()).hexdigest()
```

### Purpose

- Prevent duplicate inserts
- Create deterministic fingerprint of content

Uniqueness definition:

```
Event + Name + Designation + Year
```

If scraper runs multiple times:

- Same data → same hash → duplicate prevented  
- Modified designation → new hash → new row inserted  

---

## 6. ETL Stages

### 6.1 Extract – Fetch HTML

```python
response = requests.get(URL, timeout=15)
response.raise_for_status()
```

**Behavior**

- HTTP request with timeout
- Raises exception on non-200 response
- Returns raw HTML string

---

### 6.2 Transform – Parse HTML

#### 2025 Structure

Container:

```
.ts_speaker
```

Fields:

```
.ts_speaker-title
.ts_speaker-desc
```

#### 2024 Structure

Container:

```
.speaker__cms
```

Fields:

```
.speaker-name
.speaker-des
```

#### Parsing Pattern

```python
soup = BeautifulSoup(html, "html.parser")
speaker_blocks = soup.select("CONTAINER_SELECTOR")

for block in speaker_blocks:
    name_tag = block.select_one("NAME_SELECTOR")
    desc_tag = block.select_one("DESC_SELECTOR")

    name = name_tag.get_text(strip=True) if name_tag else None
    designation = desc_tag.get_text(strip=True) if desc_tag else None
```

**Key Properties**

- Uses CSS selectors
- Structure-specific per year
- Strips whitespace
- Skips rows with missing name
- Does not normalize content (raw ingestion layer)

---

### 6.3 Load – Database Insert

#### Database Connection

```python
connection = create_connection()
cursor = connection.cursor()
```

- Single connection per run
- Single cursor per batch

#### Insert Query

```sql
INSERT INTO speakers_raw (
    name,
    designation_raw,
    event_year,
    event_name,
    source_url,
    ingestion_batch_id,
    data_hash,
    scraped_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    ingestion_batch_id = VALUES(ingestion_batch_id),
    scraped_at = VALUES(scraped_at);
```

**Behavior**

- Parameterized query
- Prevents SQL injection
- Idempotent via UNIQUE(data_hash)
- Updates batch ID + timestamp if duplicate

#### Transaction Handling

```python
connection.commit()
cursor.close()
connection.close()
```

- Single commit at end
- Ensures atomic batch write
- Prevents connection leaks

---

## 7. Design Principles

### 7.1 Raw Ingestion Layer

No:

- Text normalization
- Deduplication by name
- Title cleanup
- Semantic interpretation

Stores exactly what the website publishes.

---

### 7.2 Idempotency

Achieved via:

- SHA256 hash
- UNIQUE constraint on `data_hash`
- ON DUPLICATE KEY UPDATE

Allows:

- Safe re-runs
- Deterministic behavior
- No accidental duplication

---

### 7.3 Batch Tracking

Each run produces:

- Unique batch ID
- Common `scraped_at` timestamp
- Groupable ingestion metadata

---

### 7.4 Year-Based Structural Adaptation

Different years use different HTML structures.

Current approach:

- Separate scraper files per year
- Only selectors differ

Future improvement:

- Parameterize selectors per year
- Unify into single engine

---

## 8. Performance Characteristics

- Single DB connection per run
- Single commit per batch
- O(n) insert operations
- Suitable for batch ETL jobs

---

## 9. Failure Handling Strategy

**Fetch Stage**
- Catches network/HTTP exceptions

**Parse Stage**
- Returns None on structural failure

**Load Stage**
- Relies on DB exception propagation

---

## 10. Future Improvements

- Move fetch/parse/store to top-level reusable functions
- Add retry logic for network failures
- Use `executemany()` for batch inserts
- Replace `print()` with structured logging
- Consolidate multi-year scrapers into parameterized engine
- Add normalization pipeline
- Introduce ORM in enrichment phase

---

## 11. System Status

- 2025 ingestion working  
- 2024 ingestion working  
- Idempotency validated  
- Batch tracking implemented  
- Least-privilege DB user applied  
- Clean ETL separation  

---

## Conclusion

This scraper implements a clean, deterministic ingestion pipeline with:

- Structured ETL design  
- Content-based idempotency  
- Safe re-runs  
- Controlled database interaction  
- Multi-year adaptability  

It forms a strong raw data foundation for future normalization, enrichment, and AI-driven processing layers.