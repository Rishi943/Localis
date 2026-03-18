---
phase: quick
plan: 260318-qay
subsystem: finance-ui
tags: [ui-polish, copywriting, error-handling, ux]
dependency_graph:
  requires: []
  provides: [spec-compliant-onboarding-copy, friendly-upload-errors, inline-reset-confirmation]
  affects: [app/static/js/app.js, app/finance.py]
tech_stack:
  added: []
  patterns: [inline-confirmation-ui, contract-copy-error-mapping]
key_files:
  created: []
  modified:
    - app/static/js/app.js
    - app/finance.py
decisions:
  - "Wrap both parse_*_csv() call paths in try/except in upload_csv() to ensure all parse failures return contract copy, not raw 500 exceptions"
  - "Inline confirmation uses innerHTML for prompt text (safe — no user data interpolated) and btn.textContent = 'Reset goals' to restore (XSS-safe)"
metrics:
  duration: "~2 minutes"
  completed: "2026-03-18"
  tasks_completed: 2
  files_modified: 2
---

# Quick Task 260318-qay: UI Polish Fixes (UI-REVIEW Gap Closure) Summary

**One-liner:** Three spec-compliance fixes closing UI-REVIEW audit gaps: onboarding copy, upload error message, and inline reset confirmation replacing browser dialog.

## What Was Done

Applied three targeted fixes from the Phase 02 UI-REVIEW audit (21/24 → 23-24/24):

### Task 1 — Onboarding copy + upload network error (app.js)

**Fix A — Onboarding completion message (line 2314):**
Replaced CIBC-prescriptive off-spec message with spec-required copy:
- Before: `"Perfect — I've saved your goals! You can always reset them with the "Reset goals" button. Let's take a look at your Dashboard now. Upload a CIBC bank statement CSV using the button at the top to get started."`
- After: `"Got it. Head to your Dashboard when you're ready to upload your first bank statement."`

**Fix B — Upload network error (line 2483):**
Replaced raw `e.message` exposure with friendly contract copy:
- Before: `'Upload error: ' + e.message`
- After: `'Upload failed. Check your connection and try again.'`

### Task 2 — Backend parse error + inline reset confirmation (finance.py, app.js)

**Part A — finance.py parse error mapping:**
Two paths now return contract-copy 422 for unreadable CSV:
1. Empty CSV check: replaced generic "CSV file is empty or contains no valid rows" with "Couldn't read that file. Make sure it's a CIBC chequing or credit card CSV export."
2. Wrapped `parse_credit_card_csv()`/`parse_chequing_csv()` calls in try/except — any parser exception now returns same contract copy instead of bubbling as 500.

**Part B — Inline reset goals confirmation (app.js):**
Replaced `browser confirm()` dialog with spec-required inline two-link UI:
- Button click now renders: `Reset goals? Yes, reset · Keep goals` inline within the button element
- "Yes, reset" (red, `var(--status-red)`) executes reset then restores button text
- "Keep goals" cancels and restores button text
- No browser dialog; no page navigation; both links use `ev.stopPropagation()` to prevent event bubbling

## Deviations from Plan

None — plan executed exactly as written.

## Verification

| Check | Result |
|-------|--------|
| Onboarding completion message matches spec copy | PASS (line 2314) |
| Upload network error: "Upload failed. Check your connection and try again." | PASS (line 2497) |
| finance.py returns contract copy for empty CSV | PASS (line 354) |
| finance.py wraps parser in try/except with contract copy | PASS (line 365) |
| Reset goals shows inline "Yes, reset" / "Keep goals" links | PASS (lines 2383, 2385) |
| No raw `e.message` in upload error path | PASS (0 matches) |
| No browser `confirm()` in financeUI reset handler | PASS (0 matches) |
| finance.py syntax valid (ast.parse) | PASS |

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 858427f | fix(260318-qay): apply onboarding completion copy and upload network error message |
| Task 2 | 9e611dc | fix(260318-qay): backend parse error contract copy + inline reset goals confirmation |

## Self-Check: PASSED

- `app/static/js/app.js` modified — confirmed by grep matches
- `app/finance.py` modified — confirmed by grep matches + ast.parse valid
- Both commits present in git log
