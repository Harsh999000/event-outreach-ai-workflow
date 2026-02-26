# Execute Project

## Overview

The `execute-project.py` script orchestrates the complete GTM automation lifecycle from ingestion to outreach delivery.

It supports two execution modes:

```
python execute-project.py --demo
python execute-project.py --full
```

---

## Execution Modes

### Demo Mode (`--demo`)

- Skips live enrichment dispatcher
- Avoids external API calls
- Deterministic execution
- Optimized for interview demonstration
- Fast runtime

Used when:
- Presenting the system
- Demonstrating architecture
- Avoiding rate limits

---

### Full Mode (`--full`)

- Executes full LinkedIn enrichment
- Calls n8n webhook
- Performs search engine resolution
- Applies rate-limit backoff logic
- Executes entire enrichment lifecycle

Used when:
- Running real enrichment
- Batch processing contacts
- Validating live system behavior

---

## End-to-End Execution Flow

The pipeline executes in the following order:

1. Scrape Event 2024
2. Scrape Event 2025
3. Canonicalize Speakers
4. Seed LinkedIn Enrichment Jobs
5. (Full Mode Only) Run Enrichment Dispatcher
6. Assign Leads
7. Seed Outreach Status
8. Generate Outreach Messages
9. Advance Outreach Phase
10. Send Outreach Messages (Simulation)

---

## Architectural Philosophy

The orchestrator:

- Maintains deterministic sequencing
- Stops execution on failure
- Ensures layer isolation
- Supports environment-aware execution
- Avoids live API dependency during demo

This provides operational reliability and interview-safe behavior.

---

## Why This Design Matters

Without orchestration:

- Scripts must be run manually
- Execution order errors may occur
- Demo reliability decreases

With orchestration:

- One command executes full lifecycle
- Interview flow becomes predictable
- System appears production-ready
- Layer boundaries remain intact

---

## Demo Strategy

Before interview:

- Run `--full` once to enrich sample data
- Keep dispatcher disabled during demo

During interview:

```
python execute-project.py --demo
```

This guarantees:

- Fast execution
- Clean output
- No external dependency failures

---

## Scalability Consideration

Future production upgrades may include:

- Replacing subprocess with internal module calls
- Logging framework integration
- Metrics collection
- Task queue system (Celery/Redis)
- Cron-based scheduling

The current design demonstrates orchestration clarity rather than production optimization.

---

## Conclusion

The execution engine transforms a multi-layer automation architecture into a single-command operational pipeline.

It enhances:

- Demonstration clarity
- Operational reliability
- Lifecycle transparency
- Interview readiness