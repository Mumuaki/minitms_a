# MiniTMS Spec Compliance Matrix

Date: 2026-02-13
Source specs:
- `docs/MiniTMS_Full_Doc_Structure.md`
- `docs/New_Features_Documentation.md`

Validation artifacts:
- pytest markers `@pytest.mark.requirement_id("...")` in `tests/` and `backend/tests/`
- phase traceability and contracts:
  - `phases/phase-1-desktop-mvp/test-contract.md`
  - `phases/phase-2-web/traceability.md`
  - `phases/phase-2-web/test-contract.md`
  - `phases/phase-3-mobile/traceability.md`
  - `phases/phase-3-mobile/test-contract.md`

## Executive Summary

| Metric | Value |
|---|---:|
| Requirement IDs found in base specs | 116 |
| Covered by automated tests (`requirement_id` markers) | 34 |
| Planned in phase traceability/contracts (no direct test marker yet) | 20 |
| Unmapped (not found in tests or phase traceability/contracts) | 62 |

Project test gate (current): `123 passed` via `.\venv\Scripts\python.exe -m pytest -q`.

Conclusion:
- TDD contract for implemented scopes (Desktop MVP, Web slices, Mobile slices) is green.
- Full base-spec compliance is partial at this stage because a large set of requirements is still not mapped to tests.

## Covered by Tests (34 IDs)

Status legend:
- `Covered`: requirement ID exists in executable tests via `requirement_id`.

| Requirement ID | Status | Evidence (tests) |
|---|---|---|
| BR-006 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `backend/tests/unit/application/test_search_profitability_phase2_slice.py` |
| BR-007 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `backend/tests/unit/application/test_search_profitability_phase2_slice.py` |
| BR-008 | Covered | `tests/phase1/integration/test_auth_fleet_scrape_integration_phase1.py`, `backend/tests/unit/application/test_search_profitability_phase2_slice.py` |
| BR-009 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `backend/tests/unit/application/test_search_profitability_phase2_slice.py` |
| BR-010 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `tests/phase1/e2e/test_desktop_phase1_workflows.py` |
| BR-011 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `backend/tests/unit/domain/test_phase2_slice2_profitability_thresholds.py` |
| BR-012 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `backend/tests/unit/domain/test_phase2_slice2_profitability_thresholds.py` |
| BR-013 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `tests/phase1/e2e/test_desktop_phase1_workflows.py` |
| BR-014 | Covered | `backend/tests/unit/application/test_phase3_mobile_slice1_push_antispam.py` |
| BR-015 | Covered | `backend/tests/unit/infrastructure/test_phase2_slice2_email_client.py`, `backend/tests/integration/test_phase2_slice2_contracts.py` |
| BR-016 | Covered | `backend/tests/unit/infrastructure/test_phase2_slice2_email_client.py` |
| BR-022 | Covered | `backend/tests/unit/application/test_phase2_slice2_use_case_validations.py`, `backend/tests/integration/test_phase2_slice2_contracts.py` |
| FR-AUTH-001 | Covered | `tests/phase1/unit/test_auth_phase1.py`, `backend/tests/unit/security/test_auth_rbac_phase2_slice.py`, `backend/tests/unit/application/test_phase3_mobile_slice1_auth_session.py` |
| FR-AUTH-002 | Covered | `tests/phase1/unit/test_auth_phase1.py`, `backend/tests/unit/security/test_auth_rbac_phase2_slice.py` |
| FR-AUTH-003 | Covered | `tests/phase1/integration/test_auth_fleet_scrape_integration_phase1.py` |
| FR-AUTH-004 | Covered | `tests/phase1/unit/test_auth_phase1.py`, `backend/tests/unit/application/test_phase3_mobile_slice1_auth_session.py` |
| FR-AUTH-005 | Covered | `tests/phase1/integration/test_auth_fleet_scrape_integration_phase1.py`, `tests/phase1/e2e/test_desktop_phase1_workflows.py` |
| FR-CALC-001 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `backend/tests/unit/application/test_search_profitability_phase2_slice.py` |
| FR-CALC-002 | Covered | `tests/phase1/integration/test_auth_fleet_scrape_integration_phase1.py`, `backend/tests/integration/test_phase2_slice2_osrm_adapter.py` |
| FR-CALC-003 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `backend/tests/unit/application/test_search_profitability_phase2_slice.py` |
| FR-CALC-004 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `tests/phase1/e2e/test_desktop_phase1_workflows.py`, `backend/tests/unit/domain/test_phase2_slice3_ranking.py` |
| FR-CALC-005 | Covered | `tests/phase1/unit/test_profitability_phase1.py`, `backend/tests/unit/infrastructure/test_phase2_slice3_settings_threshold.py`, `backend/tests/integration/test_phase3_mobile_slice6_settings_roundtrip_behavior.py` |
| FR-FLEET-001 | Covered | `tests/phase1/integration/test_auth_fleet_scrape_integration_phase1.py`, `tests/phase1/e2e/test_desktop_phase1_workflows.py` |
| FR-FLEET-002 | Covered | `tests/phase1/integration/test_auth_fleet_scrape_integration_phase1.py`, `backend/tests/unit/application/test_phase3_mobile_slice2_gps_freshness.py`, `backend/tests/integration/test_phase3_mobile_slice6_gps_adapter_behavior.py` |
| FR-FLEET-003 | Covered | `tests/phase1/unit/test_fleet_and_scrape_unit_phase1.py`, `backend/tests/unit/application/test_phase2_slice2_use_case_validations.py`, `backend/tests/integration/test_phase2_slice2_contracts.py` |
| FR-NOTIFY-003 | Covered | `backend/tests/unit/application/test_phase3_mobile_slice2_notification_preferences.py` |
| FR-NOTIFY-004 | Covered | `backend/tests/unit/application/test_phase3_mobile_slice1_push_antispam.py` |
| FR-SCRAPE-001 | Covered | `tests/phase1/integration/test_auth_fleet_scrape_integration_phase1.py` |
| FR-SCRAPE-002 | Covered | `tests/phase1/integration/test_auth_fleet_scrape_integration_phase1.py`, `tests/phase1/e2e/test_desktop_phase1_workflows.py`, `backend/tests/unit/application/test_search_profitability_phase2_slice.py` |
| FR-SCRAPE-003 | Covered | `tests/phase1/unit/test_fleet_and_scrape_unit_phase1.py`, `tests/phase1/e2e/test_desktop_phase1_workflows.py` |
| FR-SCRAPE-004 | Covered | `backend/tests/unit/application/test_phase3_mobile_slice3_map_markers.py`, `backend/tests/integration/test_phase3_mobile_slice6_marker_adapter_behavior.py` |
| FR-SETTINGS-003 | Covered | `backend/tests/unit/application/test_phase3_mobile_slice3_settings_threshold.py`, `backend/tests/e2e/test_phase3_mobile_slice6_threshold_update_behavior.py` |
| FR-UI-001 | Covered | `backend/tests/unit/application/test_search_profitability_phase2_slice.py` |
| FR-UI-006 | Covered | `backend/tests/unit/application/test_phase3_mobile_slice2_route_view.py`, `backend/tests/e2e/test_phase3_mobile_slice6_login_list_map_behavior.py` |

## Planned in Phase Contracts/Traceability (20 IDs)

Status legend:
- `Planned`: ID exists in phase traceability/test-contract docs, but no current direct `requirement_id` marker in tests.

IDs:
- BR-023, BR-024, BR-025, BR-026, BR-027, BR-028, BR-029
- FR-FLEET-005
- FR-NOTIFY-001
- FR-SCRAPE-005
- FR-SETTINGS-001, FR-SETTINGS-002, FR-SETTINGS-004
- FR-UI-002, FR-UI-003, FR-UI-004, FR-UI-005, FR-UI-007, FR-UI-008, FR-UI-009

## Unmapped IDs (62)

Status legend:
- `Unmapped`: ID not found in current tests nor in phase traceability/test-contract files.

IDs:
- BR-001, BR-002, BR-003, BR-004, BR-005
- BR-017, BR-018, BR-019, BR-020, BR-021
- FR-EMAIL-001, FR-EMAIL-002, FR-EMAIL-003, FR-EMAIL-004, FR-EMAIL-005, FR-EMAIL-006, FR-EMAIL-007, FR-EMAIL-008, FR-EMAIL-009, FR-EMAIL-010
- FR-FLEET-004, FR-FLEET-006
- FR-GPS-001, FR-GPS-002, FR-GPS-003, FR-GPS-004
- FR-GSHEET-001, FR-GSHEET-002, FR-GSHEET-003, FR-GSHEET-004, FR-GSHEET-005, FR-GSHEET-006, FR-GSHEET-007, FR-GSHEET-008, FR-GSHEET-009, FR-GSHEET-010, FR-GSHEET-011, FR-GSHEET-012, FR-GSHEET-013, FR-GSHEET-014
- FR-LOC-001, FR-LOC-002, FR-LOC-003
- FR-NOTIFY-002
- FR-PLAN-001, FR-PLAN-002, FR-PLAN-003, FR-PLAN-004, FR-PLAN-005, FR-PLAN-006, FR-PLAN-007, FR-PLAN-008, FR-PLAN-009, FR-PLAN-010, FR-PLAN-011, FR-PLAN-012
- FR-REPORT-001, FR-REPORT-002, FR-REPORT-003, FR-REPORT-004
- FR-SETTINGS-005, FR-SETTINGS-006

## Orchestrator Verdict

Current answer to "выполнены ли требования основной спецификации":
- For accepted implemented scopes and active TDD contracts: `YES`.
- For full base-spec (all 116 IDs): `NO, not yet` (34/116 test-covered, 20 planned-only, 62 unmapped).

Recommended next scope:
1. Convert `Unmapped` IDs into phase-level traceability and test-contract entries.
2. Prioritize critical IDs first: `FR-EMAIL-006`, `FR-EMAIL-007`, `FR-EMAIL-009`, `FR-PLAN-001..004`, `FR-GSHEET-001..003`.
3. Add executable tests with `requirement_id` markers and close the gap iteratively.
