# Dispatcher

## Overview

The enrichment dispatcher is designed to operate under real-world rate limiting constraints imposed by search engines.

This document explains how resilience is implemented.

---

## 1. Controlled Request Rate

Each enrichment job:

- Executes individually (BATCH_SIZE = 1)
- Introduces base pacing delay (20 to 35 seconds)
- Avoids burst traffic patterns

This reduces upstream detection risk.

---

## 2. Retry Backoff Logic

If a job fails:

- Status updated to retry_scheduled
- Error logged in last_error
- Failure delay introduced (60 to 120 seconds)

This prevents hammering during temporary blocks.

---

## 3. Cooldown Window

Retry jobs are only fetched if:

started_at < NOW() - INTERVAL 5 MINUTE

This ensures cooling period before reattempt.

---

## 4. Deterministic State Management

State transitions:

pending → running → complete  
pending → running → retry_scheduled  

No silent failure states.

---

## 5. Compliance Philosophy

The system:

- Does not scrape LinkedIn directly
- Uses search engine resolution
- Limits request frequency
- Avoids high-volume bursts
- Accepts temporary suspension as normal behavior

This aligns with platform safety boundaries.

---

## Conclusion

The dispatcher is built to:

- Respect rate limits
- Recover gracefully
- Prevent IP hammering
- Maintain auditability
- Operate safely at small-scale enrichment volumes