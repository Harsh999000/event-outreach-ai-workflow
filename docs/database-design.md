# Database Design – event-outreach-ai-workflow

---

# Raw Ingestion Layer

## Table: speakers_raw

### Schema

    CREATE TABLE speakers_raw (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        designation_raw VARCHAR(500),
        event_year INT NOT NULL,
        event_name VARCHAR(100) NOT NULL,
        source_url TEXT NOT NULL,
        ingestion_batch_id VARCHAR(50) NOT NULL,
        data_hash VARCHAR(64) NOT NULL,
        scraped_at DATETIME NOT NULL,
        UNIQUE KEY unique_hash (data_hash)
    );

---

## Column Details

**id**  
Internal primary key used for relational joins.

**name**  
Speaker name exactly as scraped.

**designation_raw**  
Full designation string as displayed on the source website.

**event_year**  
Event edition year (e.g., 2025, 2024).

**event_name**  
Event identifier (currently: TechSparks).

**source_url**  
URL from which data was scraped. Enables traceability.

**ingestion_batch_id**  
Identifier for each scrape execution. Enables batch tracking and controlled reprocessing.

**data_hash**  
SHA256 hash of:  
name + designation_raw + event_year  
Used to enforce unique data and detect data changes.

**scraped_at**  
Timestamp of ingestion.

---

## Design Rationale

- Raw ingestion is isolated from enrichment and workflow layers.
- Duplicate inserts are prevented using UNIQUE(data_hash).
- Hash-based design enables change detection between scrape runs.
- Batch ID allows controlled demo resets and operational traceability.
- Schema supports multi-year ingestion without table duplication.

---

# Canonical Identity Layer

Raw rows represent event appearances.  
Canonical layer represents real-world individuals.

Identity is defined as:

normalized_name + normalized_company

Identity hash:

SHA256(normalized_name + "|" + normalized_company)

## Table: speakers

### Schema

    CREATE TABLE speakers (
        speaker_id BIGINT AUTO_INCREMENT PRIMARY KEY,
        normalized_name VARCHAR(255) NOT NULL,
        normalized_company VARCHAR(255),
        identity_hash CHAR(64) NOT NULL UNIQUE,
        first_seen_year INT NOT NULL,
        last_seen_year INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
            ON UPDATE CURRENT_TIMESTAMP
    );

---

## Canonical Layer Rationale

- Separates raw event appearances from real-world identity.
- Prevents duplicate enrichment across event years.
- Deterministic only — no AI logic.
- Company included to avoid same-name collisions.
- Conservative identity separation (no fuzzy matching at this stage).

---

# Raw-to-Canonical Mapping Layer

## Table: speaker_raw_map

### Schema

    CREATE TABLE speaker_raw_map (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        speaker_id BIGINT NOT NULL,
        raw_id INT NOT NULL,
        event_year INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(raw_id),
        FOREIGN KEY (speaker_id) 
            REFERENCES speakers(speaker_id) ON DELETE CASCADE,
        FOREIGN KEY (raw_id) 
            REFERENCES speakers_raw(id) ON DELETE CASCADE
    );

---

## Mapping Layer Rationale

- Maintains traceability between raw ingestion and canonical identity.
- Ensures raw layer remains immutable.
- Prevents duplicate mappings via UNIQUE(raw_id).
- Enables safe reprocessing.

---

# Enrichment Layer (Versioned)

Enrichment is probabilistic and must be versioned.

## Table: speaker_profiles

### Schema

    CREATE TABLE speaker_profiles (
        profile_id BIGINT AUTO_INCREMENT PRIMARY KEY,
        speaker_id BIGINT NOT NULL,
        linkedin_url TEXT,
        confidence_score DECIMAL(5,2),
        source VARCHAR(100),
        enrichment_version INT NOT NULL,
        is_current TINYINT(1) DEFAULT 1,
        enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (speaker_id) 
            REFERENCES speakers(speaker_id) ON DELETE CASCADE
    );

---

## Enrichment Design Rationale

- Never overwrite enrichment records.
- Insert new version on re-enrichment.
- Preserve historical auditability.
- Confidence scoring required due to probabilistic nature.

---

# Orchestration Layer (Async Jobs)

## Table: enrichment_jobs

### Schema

    CREATE TABLE enrichment_jobs (
        job_id BIGINT AUTO_INCREMENT PRIMARY KEY,
        speaker_id BIGINT NOT NULL,
        job_type VARCHAR(50) NOT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'pending',
        attempt_count INT DEFAULT 0,
        max_attempts INT DEFAULT 5,
        last_error TEXT,
        scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP NULL,
        completed_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (speaker_id) 
            REFERENCES speakers(speaker_id) ON DELETE CASCADE
    );

---

# Outreach Workflow Layer

The outreach layer converts enriched intelligence into structured ABM communication artifacts.

It is fully state-driven and separated from enrichment.

---

## Outreach Lifecycle Table

### Table: outreach_status

### Schema

    CREATE TABLE outreach_status (
        speaker_id BIGINT PRIMARY KEY,
        event_phase ENUM(
            'pre_event',
            'during_event',
            'post_event',
            'closed'
        ) NOT NULL DEFAULT 'pre_event',
        phase_updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (speaker_id)
            REFERENCES speakers(speaker_id) ON DELETE CASCADE
    );

---

### Column Details

**speaker_id**  
Primary key. One lifecycle record per speaker.

**event_phase**  
Current stage in outreach workflow.

**phase_updated_at**  
Timestamp of last lifecycle transition.

---

### Outreach Status Rationale

- State-driven workflow (not date-driven).
- Prevents duplicate outreach per phase.
- Enables deterministic phase transitions.
- Ensures one active lifecycle per speaker.

---

## Outreach Messages Table

### Table: outreach_messages

### Schema

    CREATE TABLE outreach_messages (
        message_id BIGINT AUTO_INCREMENT PRIMARY KEY,
        speaker_id BIGINT NOT NULL,
        channel ENUM('email', 'linkedin') NOT NULL,
        event_phase ENUM(
            'pre_event',
            'during_event',
            'post_event'
        ) NOT NULL,
        subject TEXT NULL,
        body TEXT NOT NULL,
        persona_snapshot JSON NOT NULL,
        generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_sent BOOLEAN NOT NULL DEFAULT FALSE,
        sent_at DATETIME NULL,
        FOREIGN KEY (speaker_id)
            REFERENCES speakers(speaker_id) ON DELETE CASCADE,
        UNIQUE (speaker_id, channel, event_phase),
        INDEX idx_unsent (is_sent),
        INDEX idx_speaker_phase (speaker_id, event_phase)
    );

---

### Column Details

**channel**  
Defines delivery channel: email or linkedin.

**event_phase**  
Determines which stage the message belongs to.

**subject**  
Used only for email channel.

**body**  
Fully personalized message content.

**persona_snapshot**  
JSON copy of persona used during message generation.  
Ensures reproducibility and auditability.

**generated_at**  
Timestamp when message was created.

**is_sent**  
Indicates whether sending logic has executed.

**sent_at**  
Timestamp of send event.

---

### Outreach Message Design Rationale

- Messages are generated once and stored.
- Persona snapshot ensures deterministic evaluation.
- Unique constraint prevents duplicate generation.
- Supports future automation engine.
- Fully decoupled from send mechanism.

---

# Overall Architecture Principles

- Raw ingestion is deterministic and immutable.
- Canonical identity layer is deterministic.
- Enrichment layer is probabilistic and versioned.
- Orchestration layer is asynchronous and retryable.
- Outreach layer is state-driven and audit-safe.
- Facts, inference, and communication are strictly separated.
- Architecture supports scaling from demo (200) to production (2000+).
- Each layer is independently testable and idempotent.

---

## Final System Flow

Raw Ingestion  
→ Canonical Identity  
→ Enrichment Jobs  
→ n8n Intelligence Pipeline  
→ Versioned Profiles  
→ Outreach Status  
→ Outreach Messages  
→ (Future) Sending Engine  

---

This design maintains strict separation between:

- Data collection  
- Identity resolution  
- AI inference  
- Communication generation  
- Delivery execution  

Each stage can scale independently without structural redesign.