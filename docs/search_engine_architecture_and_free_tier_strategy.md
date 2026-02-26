# Search Engine Architecture and Free Tier Strategy

## 1. Overview

The system requires LinkedIn profile discovery without:

- Direct LinkedIn scraping
- Paid APIs
- Premium search access
- Platform violation risk

To achieve this under free-tier constraints, a controlled search proxy architecture was implemented using SearXNG.

This document explains:

- Why this approach was chosen
- How it operates
- How rate limits are handled
- How free-tier constraints are respected

---

## 2. Problem Statement

The assignment requires enrichment of event attendees with LinkedIn URLs.

Constraints:

- No paid LinkedIn API
- No Sales Navigator
- No scraping automation
- No headless browser automation
- Free tools only

Direct LinkedIn scraping:

- Triggers IP blocks
- Violates terms of service
- Requires rotating proxies
- Is unstable at scale

Therefore, a compliant indirect resolution strategy was required.

---

## 3. Solution Architecture

### 3.1 SearXNG as Search Proxy

SearXNG is an open-source meta-search engine.

It:

1. Accepts search queries
2. Forwards them to public search engines
3. Aggregates responses
4. Returns structured JSON

Instead of scraping LinkedIn directly, the system queries:

```
normalized_name + normalized_company + site:linkedin.com/in
```

This leverages public indexing rather than platform scraping.

---

## 4. Why SearXNG Was Chosen

- Free and self-hostable
- No API cost
- JSON output support
- Integrates cleanly with n8n
- Allows engine-level control
- Supports limiter configuration

This satisfies:

- Free-tier requirement
- No-code tool integration
- Automation constraint

---

## 5. Engine Configuration Strategy

To reduce rate limiting:

Only one upstream engine is enabled:

```
duckduckgo
```

Disabled:

- google
- brave
- bing
- startpage
- wikidata

This reduces:

- Parallel upstream requests
- Engine suspension risk
- IP pressure

The server is configured with:

```
limiter: true
public_instance: false
```

This ensures:

- Rate limiting enforcement
- Controlled private usage
- No public abuse risk

---

## 6. Rate Limit Mitigation Strategy

Search engines detect:

- High-frequency automated queries
- Repetitive patterns
- Burst traffic
- No browser fingerprint

To mitigate:

### 6.1 Request Pacing

Dispatcher enforces:

- 20–35 second base delay
- 60–120 second failure backoff

This simulates human-like intervals.

---

### 6.2 Cooldown Retry Logic

Retry jobs only execute if:

```
started_at < NOW() - INTERVAL 5 MINUTE
```

This prevents:

- Hammering blocked engines
- Immediate retry loops
- IP escalation

---

### 6.3 Single-Job Execution

```
BATCH_SIZE = 1
```

No parallel enrichment.

This keeps request patterns predictable and minimal.

---

## 7. Handling Temporary Suspension

If engines return:

- Timeout
- Too many requests
- HTTP errors

System behavior:

- Mark job as retry_scheduled
- Log error in last_error
- Apply extended sleep delay
- Retry later

No silent failures occur.

---

## 8. Ethical and Compliance Considerations

This architecture:

- Does not automate LinkedIn login
- Does not scrape HTML profiles
- Does not bypass authentication
- Does not use rotating proxies
- Does not attempt fingerprint evasion

It relies only on publicly indexed search results.

This maintains compliance posture.

---

## 9. Free Tier Optimization Strategy

Total cost of enrichment layer:

- SearXNG (self-hosted, free)
- DuckDuckGo search (public)
- n8n (free tier)
- Ollama (local, free)
- MySQL (free)

No paid APIs used.

No SaaS dependency.

System can operate entirely on local infrastructure.

---

## 10. Scalability Considerations

For 200 contacts:

- Conservative pacing acceptable
- Batch enrichment manageable

For 2,000 contacts:

- Dispatcher pacing still viable
- Could introduce scheduling
- Could introduce nightly batching

No architectural redesign required.

---

## 11. Design Philosophy

Rather than bypass rate limits, the system:

- Accepts platform guardrails
- Slows down intentionally
- Implements retry logic
- Operates within free-tier boundaries

This produces:

- Stable enrichment
- Compliant automation
- Predictable execution

---

## Conclusion

The search engine architecture was designed to:

- Avoid direct scraping
- Operate within free-tier limits
- Respect search engine rate limits
- Remain compliant
- Maintain structured JSON enrichment output

This approach balances automation depth with platform safety and cost discipline.