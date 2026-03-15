---
phase: 02-financial-advisor
plan: "01"
subsystem: finance-tests
tags: [tdd, testing, finance, wave-0]
dependency_graph:
  requires: []
  provides: [test-contracts-FIN-01, test-contracts-FIN-02, test-contracts-FIN-03, test-contracts-FIN-05, test-contracts-FIN-06]
  affects: [02-02, 02-03, 02-04, 02-05, 02-06, 02-07]
tech_stack:
  added: [pytest, FastAPI TestClient]
  patterns: [import-guard skip, in-memory SQLite fixture, embedded CSV fixtures]
key_files:
  created:
    - tests/conftest.py
    - tests/test_finance_csv.py
    - tests/test_finance_upload.py
    - tests/test_finance_onboarding.py
    - tests/test_finance_db.py
    - tests/test_finance_chat.py
  modified: []
decisions:
  - "Import guard pattern (try/except ImportError + pytest.skipif) chosen over xfail so the reason is clear at collection time"
  - "fin_db fixture creates all three fin_* tables inline rather than calling init_db() to avoid the production health-check path"
  - "19 tests written covering FIN-01 through FIN-06 — exceeds minimum of 13 from plan"
  - "test_multi_period_aggregation_sql added as a pure SQL unit test independent of HTTP layer for faster feedback"
metrics:
  duration_seconds: 161
  completed_date: "2026-03-15"
  tasks_completed: 1
  files_created: 6
requirements_satisfied: [FIN-01, FIN-02, FIN-03, FIN-05, FIN-06]
---

# Phase 2 Plan 01: Finance Test Scaffold (Wave 0) Summary

**One-liner:** Six pytest files defining the exact interface contract for the Finance Advisor module — all 19 tests RED (SKIPPED) until Wave 1+ implements app/finance.py.

## What Was Built

A complete test scaffold for Phase 2's Finance Advisor feature covering all 5 requirements targeted in this plan.

### Files Created

**tests/conftest.py** — Shared fixtures:
- `fin_db` fixture: in-memory SQLite with all three `fin_*` tables (`fin_uploads`, `fin_transactions`, `fin_goals`) plus `app_settings`. Isolated per test — no disk I/O.
- `client` fixture (session-scoped): FastAPI TestClient wrapping `app.main.app` with `llama_cpp` and `sentence_transformers` stubbed.
- `CHEQUING_CSV_FIXTURE`: 3 debit rows + 1 credit row (embedded string, no file I/O)
- `CREDIT_CARD_CSV_FIXTURE`: 2 spend rows + 1 payment row (embedded string, no file I/O)

**tests/test_finance_csv.py** (10 tests, FIN-02/FIN-03) — Unit tests for:
- Chequing debit/credit row parsing (`parse_chequing_csv`)
- Credit card debit/payment row parsing (`parse_credit_card_csv`)
- Latin-1 encoding tolerance (`parse_csv_bytes`)
- Account type detection by column count (`detect_account_type`)
- Categoriser: Food / Transport / Other fallback (`categorise`)

**tests/test_finance_upload.py** (2 tests, FIN-02) — Integration tests for:
- Upload endpoint `POST /finance/upload_csv` → 200, row_count > 0
- Deduplication: second upload of same CSV → inserted = 0

**tests/test_finance_onboarding.py** (2 tests, FIN-01) — Integration tests for:
- Goals persistence: `POST /finance/goals` → DB row + `fin_onboarding_done=true`
- Reset: `POST /finance/reset_goals` → `fin_onboarding_done=false`

**tests/test_finance_db.py** (2 tests, FIN-05) — Aggregation tests:
- `test_multi_period_aggregation_sql`: direct SQL on `fin_db` fixture, no HTTP
- `test_multi_period_aggregation`: uploads two period batches, verifies `GET /finance/dashboard?period=All+time`

**tests/test_finance_chat.py** (3 tests, FIN-06) — Context injection tests:
- `build_finance_context()` returns a string with "FINANCIAL CONTEXT" header
- Context includes actual transaction data when present
- `POST /finance/chat` endpoint exists and returns structured response

## Verification

```
python -m pytest tests/test_finance*.py -v
# Result: 19 skipped in 0.03s — 0 errors
```

The test suite runs in under 1 second (well within the 15s budget) because all tests skip immediately on `ImportError` from the missing `app.finance` module.

## Deviations from Plan

None — plan executed exactly as written.

The plan specified "at least 13" tests; 19 were written to achieve complete coverage of the specified behaviour cases. The extra tests are:
- `test_encoding_latin1`: Latin-1 decode
- `test_account_type_detection_chequing/credit_card`: both column counts
- `test_finance_context_contains_header` and `test_finance_context_with_transactions`: two separate unit tests for `build_finance_context()` instead of one

## Self-Check: PASSED

Created files exist:
- tests/conftest.py: FOUND
- tests/test_finance_csv.py: FOUND
- tests/test_finance_upload.py: FOUND
- tests/test_finance_onboarding.py: FOUND
- tests/test_finance_db.py: FOUND
- tests/test_finance_chat.py: FOUND

Task commit: ae0f0d1 — FOUND (plus conftest/csv/upload from 9ed2892)
Test count: 19 (minimum required: 13) — PASSED
Error count: 0 — PASSED
