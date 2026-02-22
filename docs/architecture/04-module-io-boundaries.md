# Module IO Boundaries

## Cross-Cutting IO Rules

1. Every request carries `correlation_id`.
2. Every external write operation requires an `idempotency_key`.
3. Every external response must be normalized into one of: `success`, `transient_error`, `permanent_error`, `auth_error`, `rate_limit_error`, `data_contract_error`.
4. Fallback execution is mandatory for all integration modules.

## Module Boundaries

| Module | Inputs | Outputs | Responsibility Boundary |
|---|---|---|---|
| Auth/RBAC | credentials, token refresh, role matrix | access decision, session state, audit events | Does not execute domain cargo/fleet logic |
| Fleet | vehicle cards, status updates, tracker bindings | normalized vehicle state, availability, history | Does not calculate profitability |
| Cargo Ingestion | trans.eu credentials, search params, scheduling config | normalized cargo snapshots, ingestion events | Does not rank cargos |
| Cargo Search | filter set, vehicle constraints, pagination | cargo list, sorting, hidden flags | Does not optimize routes |
| Profitability | cargo price, distances, cost params, threshold config | gross and net metrics, status color | Does not manage UI state |
| Route Planning | candidate cargos, available vehicles, route constraints | planned routes, unassigned list, planning summary | Does not control telemetry ingestion |
| GPS Integration | provider credentials, tracker map | positions, odometer deltas, telemetry state | Does not own financial aggregates |
| OSM/OSRM/Nominatim | coordinates, addresses | routes, distances, geocoded locations | Does not make dispatch decisions |
| Google Sheets Integration | order events, column map, sync policy | write results, reconciliation tasks, sync log | Does not override core order source-of-truth |
| Email/Notification | trigger events, recipient set, templates | send status, delivery log, retry tasks | Does not mutate core cargo entities |
| Reporting | planning facts, order facts, telemetry facts | KPI views, exports, deviations | Does not schedule jobs for ingestion |
| Settings | thresholds, integration parameters, tenant config | effective configuration | Does not grant access rights |
| Audit/Observability | module events, security events | immutable audit trail, metrics, alerts | Does not run business workflows |

## Integration-Specific Runtime Contracts

### trans.eu
- Input contract: authenticated scrape request with filter profile and scheduler context.
- Output contract: normalized cargo payload with source lineage fields.
- Timeout/retry: as in `03-module-map.md` trans.eu profile.
- Idempotency: snapshot ingestion key is required.
- Fallback: last valid snapshot plus `stale_data=true`.

### OSRM/Nominatim
- Input contract: normalized waypoint/address query.
- Output contract: distance, duration, route confidence.
- Timeout/retry: as in `03-module-map.md` OSRM/Nominatim profile.
- Idempotency: deterministic key from normalized request.
- Fallback: cache hit with TTL and confidence downgrade.

### GPS providers
- Input contract: tracker pull/push event with provider source metadata.
- Output contract: normalized position record and freshness marker.
- Timeout/retry: as in `03-module-map.md` GPS profile.
- Idempotency: `(provider, tracker_id, event_timestamp)`.
- Fallback: last-known-position with freshness TTL.

### Google Sheets
- Input contract: order sync command with logical version and sheet mapping.
- Output contract: accepted/rejected sync event with conflict classification.
- Timeout/retry: as in `03-module-map.md` Google Sheets profile.
- Idempotency: `(order_id, sheet_id, logical_version)`.
- Fallback: enqueue reconciliation task and keep system priority (`BR-026`).

### SMTP
- Input contract: outbound message request with policy context (rate limits).
- Output contract: accepted/deferred/rejected delivery state.
- Timeout/retry: as in `03-module-map.md` SMTP profile.
- Idempotency: unique send window key per recipient/template/order.
- Fallback: deferred queue with rate-limit policy enforcement.
