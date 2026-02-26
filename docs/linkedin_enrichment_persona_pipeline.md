# n8n LinkedIn Enrichment & Persona Pipeline

## 1. Overview

This n8n workflow handles the full LinkedIn enrichment and AI persona generation process.

It is triggered by the dispatcher via webhook and performs:

- LinkedIn search using SearXNG
- Candidate scoring and identity resolution
- Role, seniority, and industry inference
- Persona prompt generation
- Local LLM call (Ollama)
- JSON persona parsing
- Structured response back to dispatcher

This workflow forms the intelligence layer of the enrichment engine.

---

## 2. Architecture Flow

Webhook (POST)
   ├── SearXNG - Search
   │
   ├── LinkedIn Identity Resolver
   │
   ├── Enrichment Parser
   │
   ├── Persona Prompt Builder
   │
   ├── Build Persona (Ollama API)
   │
   ├── Parse Persona JSON
   │
   ├── Merge Data
   │
   ├── Final Formatter
   │
   └── Respond to Webhook

---

## 3. Trigger

### Webhook Node

Path:

```
/webhook/linkedin-resolution
```

Method:

```
POST
```

Expected Payload:

```json
{
  "job_id": 42,
  "speaker_id": 194,
  "normalized_name": "aneesh dhawan",
  "normalized_company": "sales, india and saarc, commvault"
}
```

This input originates from `dispatcher.py`.

---

## 4. LinkedIn Search Layer

### Node: SearXNG - Search

Endpoint:

```
http://localhost:8080/search
```

Query format:

```
{name} {company} site:linkedin.com/in
```

Returns:

- Search results in JSON
- Candidate LinkedIn profile URLs
- Titles and snippets

---

## 5. LinkedIn Identity Resolver

### Purpose

Select the best LinkedIn candidate using a scoring algorithm.

### Scoring Logic

Factors:

- Name token match (max 40 pts)
- Company match in title (40 pts)
- Company match in snippet (20 pts)
- Slug match bonus (10 pts)
- Numeric slug penalty (-30 pts)

Confidence Levels:

- AUTO_ACCEPT
- REVIEW_REQUIRED
- LOW_CONFIDENCE

Final Output:

```json
{
  "best_candidate": "linkedin_url",
  "confidence_score": 85,
  "confidence_level": "AUTO_ACCEPT"
}
```

---

## 6. Enrichment Parser

### Purpose

Extract structured role intelligence from metadata.

Extracted Fields:

- parsed_role
- parsed_company
- seniority
- function_type
- industry_signal

### Seniority Detection

Examples:

- CEO / Chief → C_LEVEL
- VP → VP_LEVEL
- Director → DIRECTOR
- Manager → MANAGER
- Founder → FOUNDER

### Function Detection

Examples:

- Engineering / CTO → ENGINEERING
- Marketing → MARKETING
- Sales → SALES
- Product → PRODUCT
- Finance → FINANCE

### Industry Signals

Derived from:

- Company name
- Snippet keywords
- Title keywords

---

## 7. Persona Prompt Builder

### Purpose

Construct a strict JSON-only prompt for Ollama.

Constraints:

- Output must be JSON only
- Exactly 2 personalization themes
- No commentary
- No extra text
- No hallucinated context

Prompt includes:

- Name
- Company
- Role
- Seniority
- Function
- Industry

---

## 8. Persona Generation (Ollama)

### Node: Build Persona call to Ollama

Endpoint:

```
http://192.168.0.194:11434/api/generate
```

Model:

```
mistral
```

Parameters:

- temperature: 0.2
- stream: false

Low temperature ensures deterministic persona generation.

---

## 9. Persona Parsing

### Node: Parse Persona JSON

Parses:

```json
{
  "persona_summary": "",
  "context_summary": "",
  "personalization_themes": ["", ""]
}
```

Ensures structured storage.

---

## 10. Data Merge & Final Output

All data is merged into final structured response:

```json
{
  "job_id": 42,
  "speaker_id": 194,
  "linkedin_url": "...",
  "confidence_score": 90,
  "confidence_level": "AUTO_ACCEPT",
  "parsed_role": "...",
  "seniority": "...",
  "function_type": "...",
  "industry_signal": "...",
  "persona": {
    "persona_summary": "...",
    "context_summary": "...",
    "personalization_themes": ["", ""]
  }
}
```

---

## 11. Respond to Webhook

Final structured JSON is returned to:

```
dispatcher.py
```

Dispatcher then:

- Inserts versioned profile
- Stores confidence score
- Marks enrichment job complete

---

## 12. Design Principles

### 12.1 Deterministic Scoring

No LLM used for identity resolution.
Pure rule-based scoring.

### 12.2 Strict Persona Guardrails

- JSON-only output
- Fixed number of themes
- Temperature control
- No hallucinated facts

### 12.3 Separation of Concerns

Identity resolution ≠ Persona generation.

Each stage has independent logic.

### 12.4 Human Review Support

Confidence levels allow:

- Auto accept
- Manual review queue
- Low confidence filtering

---

## 13. Failure Handling

Potential failure points:

- SearXNG timeout
- No LinkedIn candidates
- Low confidence match
- Ollama failure
- JSON parsing error

System Response:

- Webhook returns error
- Dispatcher schedules retry
- attempt_count incremented

---

## 14. System Role in GTM Automation

Full Flow:

```
Seeder
   ↓
Dispatcher
   ↓
n8n Workflow (This Layer)
   ↓
speaker_profiles (versioned)
   ↓
Persona-driven Outreach Engine
```

This workflow transforms raw identity data into structured, AI-ready persona intelligence.

---

## Conclusion

This n8n workflow implements:

- Deterministic LinkedIn identity resolution
- Structured enrichment parsing
- Controlled AI persona generation
- Confidence-based decision logic
- Clean webhook response architecture

It serves as the intelligence core of the GTM enrichment engine.