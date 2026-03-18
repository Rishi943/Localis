---
phase: 2
slug: financial-advisor
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + manual browser testing (frontend) |
| **Config file** | `tests/` directory |
| **Quick run command** | `python -m pytest tests/ -x -q 2>/dev/null \|\| echo "no tests"` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 02-08-01 | 08 | 1 | FIN-04 | visual | Manual: open Finance panel, confirm 3-column layout | ⬜ pending |
| 02-08-02 | 08 | 1 | FIN-04 | visual | Manual: confirm .fin-budget-sidebar visible with bars | ⬜ pending |
| 02-09-01 | 09 | 1 | FIN-04 | visual | Manual: Chart.js line + donut charts render on data load | ⬜ pending |
| 02-09-02 | 09 | 1 | FIN-04 | visual | Manual: charts update on period change | ⬜ pending |
| 02-10-01 | 10 | 1 | FIN-01 | visual | Manual: onboarding shows all 8 category budget inputs | ⬜ pending |
| 02-10-02 | 10 | 1 | FIN-02 | unit | `grep -r "Health & Fitness\|Government & Fees" app/static/js/app.js` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Frontend-only changes — no new test stubs required
- Existing `tests/` directory covers backend endpoints (already verified)

*Existing infrastructure covers all phase requirements (backend verified; frontend is manual).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 3-column dashboard layout renders | FIN-04 | CSS layout, browser rendering | Open Finance panel → Dashboard tab; confirm budget sidebar left, charts center-top, transactions center-bottom |
| Chart.js line chart shows monthly trend | FIN-04 | Visual rendering, data binding | Upload CSV → open dashboard; confirm line chart with month X-axis |
| Chart.js donut chart shows 8 categories | FIN-04 | Visual rendering, legend | Upload CSV → open dashboard; confirm donut with 8-segment legend |
| Onboarding prompts all 8 categories | FIN-01 | UI flow, step sequence | Clear DB → open Finance panel; walk through onboarding; confirm 8 category budget inputs |
| Month-grouped transactions collapsible | FIN-04 | UI interaction | Upload multi-month CSV; confirm collapsible month headers in transactions list |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
