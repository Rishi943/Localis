---
phase: 02-financial-advisor
plan: 04
subsystem: api
tags: [fastapi, sqlite, javascript, finance, iife, dashboard, goals]

# Dependency graph
requires:
  - phase: 02-financial-advisor/02-02
    provides: "app/finance.py module with register_finance(), upload_csv, status endpoints, goals/reset_goals stubs, fin_* tables in database.py"
  - phase: 02-financial-advisor/02-03
    provides: "#finance-panel HTML scaffold with fin-pane-*, .fin-tab, btn-finance, fin-close DOM IDs"

provides:
  - "GET /finance/goals — returns latest saved goals row or {goals: null}"
  - "GET /finance/dashboard_data — 4-key aggregation JSON (categories, budget_actual, trend, transactions)"
  - "GET /finance/dashboard — alias for dashboard_data, same response shape"
  - "POST /finance/goals now DELETE-then-INSERT (single row replace strategy)"
  - "GET /api/settings now includes fin_onboarding_done key"
  - "financeUI IIFE in app.js: open/close/init/_checkOnboarding/_activateTab/_uploadCSV/_loadDashboard"
  - "financeUI.init() called unconditionally in startApp()"

affects:
  - 02-financial-advisor/02-05
  - 02-financial-advisor/02-06

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_run_dashboard_queries() helper function separates SQL from HTTP handler — enables reuse by both /dashboard and /dashboard_data routes"
    - "Single-row replace strategy for goals: DELETE FROM fin_goals before INSERT ensures only one goals row exists at a time"
    - "period_filter=None maps to 'All time' — SQL conditional avoids dynamic query building"

key-files:
  created: []
  modified:
    - app/finance.py
    - app/main.py
    - app/static/js/app.js
    - tests/test_finance_db.py

key-decisions:
  - "Both /finance/dashboard_data and /finance/dashboard added — plan specifies dashboard_data but existing test file calls /finance/dashboard; both share _run_dashboard_queries() helper"
  - "fin_onboarding_done added to GET /api/settings key list so test_finance_onboarding.py can verify flag via settings endpoint"
  - "pytest.approx '>=' comparison bug in test_finance_db.py fixed with plain float subtraction tolerance"

patterns-established:
  - "financeUI IIFE follows voiceStatusBar/ragUI IIFE pattern: private state, public {open,close,init} API"
  - "_checkOnboarding() called on every open() — always reflects server state, no stale client-side cache"

requirements-completed: [FIN-01, FIN-05]

# Metrics
duration: 15min
completed: 2026-03-15
---

# Phase 02 Plan 04: Finance Wiring Summary

**Goals CRUD API (GET /finance/goals, dashboard_data SQL aggregation) + financeUI IIFE (open/close/tabs/onboarding-check/CSV upload) fully wired — Finance panel is now interactive from browser**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-15T23:10:00Z
- **Completed:** 2026-03-15T23:25:00Z
- **Tasks:** 2/2
- **Files modified:** 4

## Accomplishments
- Added `GET /finance/goals` (latest goals row or null), `GET /finance/dashboard_data` and `GET /finance/dashboard` alias running 4 SQL aggregation queries (category breakdown, budget vs actual, monthly trend, transaction list limited to 500 rows newest first)
- Fixed `POST /finance/goals` to DELETE existing row before INSERT (single-row replace pattern per plan spec)
- Added `fin_onboarding_done` to `GET /api/settings` response so tests and frontend can read the onboarding flag
- Added `financeUI` IIFE to `app.js` (192 lines) with `open`, `close`, `init`, `_activateTab`, `_checkOnboarding`, `_loadDashboard` stub, `_startOnboarding` stub, `_uploadCSV`; `financeUI.init()` called unconditionally in `startApp()`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add goals GET, dashboard_data, dashboard endpoints + api/settings exposes fin_onboarding_done** - `0fa7bd5` (feat)
2. **Task 2: Add financeUI IIFE to app.js with open/close/tabs/onboarding-check** - `c3ee18f` (feat)

**Plan metadata:** see final commit below

## Files Created/Modified
- `app/finance.py` — Added `GET /finance/goals`, `GET /finance/dashboard_data`, `GET /finance/dashboard`, `_run_dashboard_queries()` helper; fixed POST /finance/goals to DELETE-then-INSERT
- `app/main.py` — Added `fin_onboarding_done` to `GET /api/settings` key list
- `app/static/js/app.js` — Added `financeUI` IIFE (192 lines) + `financeUI.init()` call in `startApp()`
- `tests/test_finance_db.py` — Fixed `pytest.approx '>='` TypeError (plain float comparison)

## Decisions Made
- Both `/finance/dashboard_data` and `/finance/dashboard` added: the plan spec uses `dashboard_data` but `test_finance_db.py` calls `/finance/dashboard`. Both share the `_run_dashboard_queries()` helper so there's no duplication.
- `fin_onboarding_done` added to `/api/settings` response: `test_finance_onboarding.py` verifies the flag via `GET /api/settings`. Adding the key here is the correct long-term state (frontend settings modal can also read it).
- `pytest.approx` with `>=` operator raises `TypeError` in pytest — this is a known limitation. Fixed by using plain float tolerance (`>= expected - 0.01`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pytest.approx '>=' TypeError in test_finance_db.py**
- **Found during:** Task 1 (TDD test run)
- **Issue:** `assert total_spend >= pytest.approx(83.23)` raises `TypeError: '>=' not supported between instances of 'float' and 'ApproxScalar'` — pytest.approx only supports `==` and `!=` operators when on the right side of a comparison
- **Fix:** Replaced with `assert total_spend >= (5.75 + 18.50 + 15.99 + 42.99) - 0.01` (plain float with tolerance)
- **Files modified:** tests/test_finance_db.py
- **Verification:** Test passes with 4 pass, 0 fail
- **Committed in:** 0fa7bd5 (Task 1 commit)

**2. [Rule 2 - Missing Critical] Added GET /finance/dashboard alias**
- **Found during:** Task 1 (reviewing test_finance_db.py)
- **Issue:** `test_multi_period_aggregation` calls `GET /finance/dashboard` but plan only specified `GET /finance/dashboard_data`
- **Fix:** Added `@router.get("/dashboard")` alias sharing the same `_run_dashboard_queries()` helper
- **Files modified:** app/finance.py
- **Verification:** Test calls `/finance/dashboard`, receives 200 with correct data shape
- **Committed in:** 0fa7bd5 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both necessary for tests to pass. No scope creep.

## Issues Encountered
- `save_goals` endpoint existed from Plan 02 but was missing the DELETE step — fixed as part of Task 1 implementation per plan spec.
- `GET /api/settings` did not expose `fin_onboarding_done` — the test was written expecting it, so added the key to the settings endpoint key list.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Finance panel fully wired: opens on btn-finance click, closes on fin-close click or Escape, tab switching works, CSV upload form wired
- `_checkOnboarding()` calls `GET /finance/status` on every open — shows onboarding or dashboard based on server state
- `_loadDashboard()` and `_startOnboarding()` are stubs ready for Plan 05 implementation
- Dashboard aggregation SQL is complete and tested — Plan 05 can call `GET /finance/dashboard_data` and render the returned JSON as CSS bars

---
*Phase: 02-financial-advisor*
*Completed: 2026-03-15*

## Self-Check: PASSED
- app/finance.py: FOUND
- app/static/js/app.js: FOUND
- 02-04-SUMMARY.md: FOUND
- Commit 0fa7bd5 (Task 1): FOUND
- Commit c3ee18f (Task 2): FOUND
