# Module Map And Integration Contracts

## Module Dependency Map

1. `Auth/RBAC` is a cross-cutting dependency for all business modules.
2. `Fleet` depends on `Auth/RBAC`, `Settings`, `Audit`.
3. `Cargo Ingestion (trans.eu)` depends on `Settings`, `Audit`.
4. `Cargo Search` depends on `Cargo Ingestion`, `Fleet`, `Profitability`, `Settings`.
5. `Profitability Engine` depends on `OSRM/Nominatim`, `Fleet`, `Settings`.
6. `Route Planning` depends on `Cargo Search`, `Fleet`, `Profitability`, `OSRM/Nominatim`.
7. `GPS Integration` depends on `Fleet`, `Settings`, `Audit`.
8. `Google Sheets Integration` depends on `Orders`, `Profitability`, `Settings`, `Audit`.
9. `Email/Notification` depends on `Orders`, `Settings`, `Auth/RBAC`, `Audit`.
10. `Reporting` depends on `Orders`, `Fleet`, `GPS Integration`, `Profitability`.
11. `Audit/Observability` is consumed by all modules.

## Integration Reliability Contract Profiles

### trans.eu scraping profile
- Timeout: connect 10s, read 30s, total operation 60s.
- Retry: 3 attempts, exponential backoff 2s/4s/8s, retry only transient classes.
- Idempotency: ingestion key `(source, external_id, snapshot_time_bucket)`.
- Error taxonomy mapping:
  - `TRANSIENT`: network timeout, remote 5xx.
  - `AUTH`: invalid credentials or expired session.
  - `RATE_LIMIT`: explicit throttling or anti-bot challenge.
  - `DATA_CONTRACT`: response shape changed.
  - `PERMANENT`: forbidden flow not recoverable by retry.
- Fallback: use last successful snapshot with `stale_data=true`, keep previous ranking frozen.

### OSRM/Nominatim profile
- Timeout: connect 3s, read 5s, total operation 8s.
- Retry: 2 attempts, backoff 1s/2s, transient only.
- Idempotency: route/geocode key hash of normalized points or address.
- Error taxonomy mapping: `TRANSIENT`, `RATE_LIMIT`, `DATA_CONTRACT`, `PERMANENT`.
- Fallback: cached distance/geocode within TTL, mark confidence level.

### GPS provider profile
- Timeout: connect 5s, read 10s, total operation 20s.
- Retry: 3 attempts, backoff 2s/4s/8s.
- Idempotency: telemetry event key `(provider, tracker_id, event_timestamp)`.
- Error taxonomy mapping: `TRANSIENT`, `AUTH`, `RATE_LIMIT`, `DATA_CONTRACT`, `PERMANENT`.
- Fallback: last known position with TTL 15 minutes, vehicle status not auto-promoted on stale data.

### Google Sheets profile
- Timeout: connect 5s, read/write 15s, total operation 30s.
- Retry: 3 attempts, backoff 2s/4s/8s, write operations require idempotency key.
- Idempotency: sync key `(order_id, sheet_id, logical_version)`.
- Error taxonomy mapping: `TRANSIENT`, `AUTH`, `RATE_LIMIT`, `DATA_CONTRACT`, `PERMANENT`.
- Fallback: enqueue reconciliation task, preserve local system as source of truth per `BR-026`.

### SMTP profile
- Timeout: connect 5s, send 10s, total operation 20s.
- Retry: 2 attempts for transient delivery failure.
- Idempotency: message key `(order_id, template_id, recipient, logical_send_window)`.
- Error taxonomy mapping: `TRANSIENT`, `AUTH`, `RATE_LIMIT`, `PERMANENT`.
- Fallback: queue delayed retry while enforcing `BR-015` and `BR-016`.
