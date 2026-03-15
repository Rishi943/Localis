---
phase: 2
slug: financial-advisor
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/conftest.py` (Wave 0 creates) |
| **Quick run command** | `python -m pytest tests/test_finance*.py -x -q` |
| **Full suite command** | `python -m pytest tests/test_finance*.py -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_finance*.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/test_finance*.py -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | FIN-02 | unit | `pytest tests/test_finance_csv.py -k "test_parse_chequing"` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 0 | FIN-02 | unit | `pytest tests/test_finance_csv.py -k "test_parse_credit_card"` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 0 | FIN-03 | unit | `pytest tests/test_finance_csv.py -k "test_categorise"` | ❌ W0 | ⬜ pending |
| 2-01-04 | 01 | 1 | FIN-02 | integration | `pytest tests/test_finance_upload.py -k "test_upload_endpoint"` | ❌ W0 | ⬜ pending |
| 2-01-05 | 01 | 1 | FIN-02 | integration | `pytest tests/test_finance_upload.py -k "test_dedup"` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | FIN-01 | integration | `pytest tests/test_finance_onboarding.py -k "test_goals_persist"` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 2 | FIN-04 | manual | — | N/A | ⬜ pending |
| 2-03-02 | 03 | 2 | FIN-05 | integration | `pytest tests/test_finance_db.py -k "test_multi_period_aggregation"` | ❌ W0 | ⬜ pending |
| 2-04-01 | 04 | 2 | FIN-06 | integration | `pytest tests/test_finance_chat.py -k "test_sql_context_injection"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_finance_csv.py` — stubs for FIN-02, FIN-03 (CSV parsing, categorisation)
- [ ] `tests/test_finance_upload.py` — stubs for FIN-02 (upload endpoint, dedup)
- [ ] `tests/test_finance_onboarding.py` — stubs for FIN-01 (goals persistence)
- [ ] `tests/test_finance_db.py` — stubs for FIN-05 (multi-period aggregation)
- [ ] `tests/test_finance_chat.py` — stubs for FIN-06 (SQL context injection)
- [ ] `tests/conftest.py` — shared fixtures (in-memory SQLite, test app client)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard glass CSS charts render correctly | FIN-04 | Visual rendering cannot be automated | Open Finance panel → upload CSV → check Dashboard tab: category bars, budget vs actual bars, monthly trend, transaction list all visible and styled |
| Onboarding conversational flow feels natural | FIN-01 | UX quality is subjective | Open Finance panel fresh → complete onboarding → verify tone is warm, questions flow naturally, skip button works |
| Finance panel accessible without model loaded | FIN-04 | Requires model state setup | Kill model process → open Finance panel → verify Dashboard loads with SQL data only |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
