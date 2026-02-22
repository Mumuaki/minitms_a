# Requirement Traceability Matrix

## FR Traceability (row-by-row IDs)

| Requirement ID | Module(s) | Future Test IDs | Coverage | Status |
|---|---|---|---|---|
| FR-AUTH-001 | Auth/RBAC | AT-AUTH-001, IT-AUTH-001, E2E-AUTH-001 | Acceptance+Integration+E2E | Covered |
| FR-AUTH-002 | Auth/RBAC | AT-AUTH-002, IT-RBAC-001, SEC-RBAC-001 | Acceptance+Integration+Security | Covered |
| FR-AUTH-003 | Auth/RBAC | AT-AUTH-003, IT-AUTH-LOCK-001, E2E-AUTH-LOCK-001 | Acceptance+Integration+E2E | Covered |
| FR-AUTH-004 | Auth/RBAC | AT-AUTH-004, IT-TOKEN-001, SEC-TOKEN-001 | Acceptance+Integration+Security | Covered |
| FR-AUTH-005 | Auth/RBAC, Audit | AT-AUDIT-001, IT-AUDIT-001, SEC-AUDIT-001 | Acceptance+Integration+Security | Covered |
| FR-FLEET-001 | Fleet | AT-FLEET-001, IT-FLEET-001, E2E-FLEET-001 | Acceptance+Integration+E2E | Covered |
| FR-FLEET-002 | Fleet, GPS Integration | AT-FLEET-002, IT-GPS-001, E2E-FLEET-MAP-001 | Acceptance+Integration+E2E | Covered |
| FR-FLEET-003 | Fleet | AT-FLEET-003, IT-FLEET-STATUS-001, E2E-FLEET-STATUS-001 | Acceptance+Integration+E2E | Covered |
| FR-FLEET-004 | Fleet, Reporting | AT-FLEET-004, IT-FLEET-HISTORY-001, E2E-FLEET-HISTORY-001 | Acceptance+Integration+E2E | Covered |
| FR-FLEET-005 | Fleet, GPS Integration | AT-FLEET-005, IT-GPS-BIND-001, E2E-GPS-BIND-001 | Acceptance+Integration+E2E | Covered |
| FR-FLEET-006 | Fleet, Reporting | AT-FLEET-006, IT-EXPORT-001, E2E-EXPORT-001 | Acceptance+Integration+E2E | Covered |
| FR-SCRAPE-001 | Cargo Ingestion | AT-SCRAPE-001, IT-TRANS-AUTH-001, E2E-SCRAPE-001 | Acceptance+Integration+E2E | Covered |
| FR-SCRAPE-002 | Cargo Ingestion, Cargo Search | AT-SCRAPE-002, IT-TRANS-FILTER-001, E2E-CARGO-SEARCH-001 | Acceptance+Integration+E2E | Covered |
| FR-SCRAPE-003 | Cargo Ingestion, Settings | AT-SCRAPE-003, IT-SCHEDULER-001, E2E-SCHEDULER-001 | Acceptance+Integration+E2E | Covered |
| FR-SCRAPE-004 | Cargo Search, OSM/OSRM/Nominatim | AT-MAP-001, IT-ROUTE-VIS-001, E2E-MAP-001 | Acceptance+Integration+E2E | Covered |
| FR-SCRAPE-005 | Cargo Ingestion | AT-SCRAPE-005, IT-CARGO-SNAPSHOT-001, E2E-CARGO-HISTORY-001 | Acceptance+Integration+E2E | Covered |
| FR-CALC-001 | Profitability, Fleet | AT-PROFIT-001, IT-COMPAT-001, E2E-CARGO-COMPAT-001 | Acceptance+Integration+E2E | Covered |
| FR-CALC-002 | Profitability, OSM/OSRM/Nominatim | AT-PROFIT-002, IT-OSRM-001, PERF-OSRM-001 | Acceptance+Integration+Performance | Covered |
| FR-CALC-003 | Profitability | AT-PROFIT-003, IT-RATE-001, E2E-PROFIT-001 | Acceptance+Integration+E2E | Covered |
| FR-CALC-004 | Profitability, Cargo Search | AT-PROFIT-004, IT-RANKING-001, E2E-RANKING-001 | Acceptance+Integration+E2E | Covered |
| FR-CALC-005 | Profitability, Settings | AT-PROFIT-005, IT-THRESHOLD-001, E2E-THRESHOLD-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-001 | Cargo Search | AT-UI-001, IT-UI-SORT-001, E2E-UI-TABLE-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-002 | Profitability, Cargo Search | AT-UI-002, IT-UI-COLOR-001, E2E-UI-COLOR-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-003 | Cargo Search | AT-UI-003, IT-UI-DETAIL-001, E2E-UI-DETAIL-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-004 | Cargo Search | AT-UI-004, IT-UI-COUNTRY-FILTER-001, E2E-UI-COUNTRY-FILTER-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-005 | Cargo Search, Settings | AT-UI-005, IT-SAVED-FILTER-001, E2E-SAVED-FILTER-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-006 | Cargo Search, OSM/OSRM/Nominatim | AT-UI-006, IT-UI-ROUTE-001, E2E-UI-ROUTE-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-007 | Cargo Search | AT-UI-007, IT-UI-THEME-001, E2E-UI-THEME-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-008 | Cargo Search | AT-UI-008, IT-CONTRACTOR-RATING-001, E2E-RATING-FILTER-001 | Acceptance+Integration+E2E | Covered |
| FR-UI-009 | Cargo Search, Profitability | AT-UI-009, IT-EXCLUSION-001, E2E-EXCLUSION-001 | Acceptance+Integration+E2E | Covered |
| FR-NOTIFY-001 | Email/Notification | AT-NOTIFY-001, IT-PUSH-001, E2E-NOTIFY-001 | Acceptance+Integration+E2E | Covered |
| FR-NOTIFY-002 | Email/Notification | AT-NOTIFY-002, IT-TELEGRAM-001, E2E-TELEGRAM-001 | Acceptance+Integration+E2E | Covered |
| FR-NOTIFY-003 | Email/Notification, Settings | AT-NOTIFY-003, IT-NOTIFY-PREF-001, E2E-NOTIFY-PREF-001 | Acceptance+Integration+E2E | Covered |
| FR-NOTIFY-004 | Email/Notification | AT-NOTIFY-004, IT-NOTIFY-RATE-001, E2E-NOTIFY-RATE-001 | Acceptance+Integration+E2E | Covered |
| FR-SETTINGS-001 | Settings, Cargo Ingestion | AT-SETTINGS-001, IT-TRANS-CRED-001, SEC-CRED-001 | Acceptance+Integration+Security | Covered |
| FR-SETTINGS-002 | Settings, Cargo Ingestion | AT-SETTINGS-002, IT-INTERVAL-001, E2E-INTERVAL-001 | Acceptance+Integration+E2E | Covered |
| FR-SETTINGS-003 | Settings, Profitability | AT-SETTINGS-003, IT-RATE-BOUNDARY-001, E2E-RATE-BOUNDARY-001 | Acceptance+Integration+E2E | Covered |
| FR-SETTINGS-004 | Settings, Cargo Search | AT-SETTINGS-004, IT-DEFAULT-FILTER-001, E2E-DEFAULT-FILTER-001 | Acceptance+Integration+E2E | Covered |
| FR-SETTINGS-005 | Settings | AT-SETTINGS-005, IT-LOCALE-001, E2E-LOCALE-001 | Acceptance+Integration+E2E | Covered |

## BR Traceability (row-by-row IDs)

| Requirement ID | Module(s) | Future Test IDs | Coverage | Status |
|---|---|---|---|---|
| BR-001 | Domain Validation | AT-BR-001, IT-UNITS-001 | Acceptance+Integration | Covered |
| BR-002 | Domain Validation | AT-BR-002, IT-UNITS-002 | Acceptance+Integration | Covered |
| BR-003 | Fleet | AT-BR-003, IT-UNITS-003 | Acceptance+Integration | Covered |
| BR-004 | Fleet, Cargo Search | AT-BR-004, IT-UNITS-004 | Acceptance+Integration | Covered |
| BR-005 | Domain Validation | AT-BR-005, IT-DATE-001 | Acceptance+Integration | Covered |
| BR-006 | Profitability | AT-BR-006, IT-RATE-FORMULA-001 | Acceptance+Integration | Covered |
| BR-007 | Profitability, Fleet | AT-BR-007, IT-COMPAT-002 | Acceptance+Integration | Covered |
| BR-008 | OSM/OSRM/Nominatim, Profitability | AT-BR-008, IT-OSRM-002 | Acceptance+Integration | Covered |
| BR-009 | Profitability | AT-BR-009, IT-MIN-DIST-001 | Acceptance+Integration | Covered |
| BR-010 | Profitability, Cargo Search | AT-BR-010, IT-COLOR-RED-001 | Acceptance+Integration | Covered |
| BR-011 | Profitability, Cargo Search | AT-BR-011, IT-COLOR-GRAY-001 | Acceptance+Integration | Covered |
| BR-012 | Profitability, Cargo Search | AT-BR-012, IT-COLOR-YELLOW-001 | Acceptance+Integration | Covered |
| BR-013 | Profitability, Cargo Search | AT-BR-013, IT-COLOR-GREEN-001 | Acceptance+Integration | Covered |
| BR-014 | Email/Notification | AT-BR-014, IT-NOTIFY-COOLDOWN-001 | Acceptance+Integration | Covered |
| BR-015 | Email/Notification | AT-BR-015, IT-EMAIL-LIMIT-001 | Acceptance+Integration | Covered |
| BR-016 | Email/Notification | AT-BR-016, IT-EMAIL-INTERVAL-001 | Acceptance+Integration | Covered |
| BR-017 | GPS Integration, Reporting | AT-BR-017, IT-ODO-DELTA-001 | Acceptance+Integration | Covered |
| BR-018 | Reporting | AT-BR-018, IT-AVG-RATE-001 | Acceptance+Integration | Covered |
| BR-019 | Reporting | AT-BR-019, IT-DEVIATION-YELLOW-001 | Acceptance+Integration | Covered |
| BR-020 | Reporting | AT-BR-020, IT-DEVIATION-RED-001 | Acceptance+Integration | Covered |
| BR-021 | Reporting, Email/Notification | AT-BR-021, IT-DEVIATION-ALERT-001 | Acceptance+Integration | Covered |
| BR-022 | Google Sheets Integration | AT-BR-022, IT-SHEETS-AUTOFIELDS-001 | Acceptance+Integration | Covered |
| BR-023 | Google Sheets Integration, Profitability | AT-BR-023, IT-SHEETS-EURKM-001 | Acceptance+Integration | Covered |
| BR-024 | Google Sheets Integration | AT-BR-024, IT-SHEETS-DAYS-001 | Acceptance+Integration | Covered |
| BR-025 | Google Sheets Integration | AT-BR-025, IT-SHEETS-REALTIME-001 | Acceptance+Integration | Covered |
| BR-026 | Google Sheets Integration | AT-BR-026, IT-SHEETS-CONFLICT-001 | Acceptance+Integration | Covered |
| BR-027 | Google Sheets Integration | AT-BR-027, IT-SHEETS-RESERVE-001 | Acceptance+Integration | Covered |
| BR-028 | Google Sheets Integration | AT-BR-028, IT-SHEETS-HEADER-001 | Acceptance+Integration | Covered |
| BR-029 | Google Sheets Integration | AT-BR-029, IT-SHEETS-SOURCE-001 | Acceptance+Integration | Covered |

## NFR ID Governance

1. Source document `docs/MiniTMS_Full_Doc_Structure.md` defines NFR statements but does not assign explicit NFR IDs.
2. Governance decision: normalize NFRs into architecture-owned IDs for traceability control.
3. Normalized IDs:
   - `NFR-PERF-001` list load time < 3s.
   - `NFR-PERF-002` profitability for 100 cargos < 5s.
   - `NFR-PERF-003` up to 50 concurrent users.
   - `NFR-PERF-004` API response < 500ms.
   - `NFR-REL-001` availability 99.5%.
   - `NFR-REL-002` auto-recovery after failures.
   - `NFR-REL-003` daily backups.
   - `NFR-SEC-001` encryption in transit and at rest.
   - `NFR-SEC-002` bcrypt password hashing.
   - `NFR-SEC-003` full user action logging.
   - `NFR-SEC-004` GDPR compliance.
   - `NFR-COMP-001` desktop compatibility.
   - `NFR-COMP-002` web browser compatibility.
   - `NFR-COMP-003` mobile compatibility.
4. All normalized NFR IDs are mapped to performance, reliability, security, and compatibility test contracts in phase test plans.
