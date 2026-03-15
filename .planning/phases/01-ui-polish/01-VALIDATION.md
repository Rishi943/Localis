---
phase: 1
slug: ui-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual browser verification (no automated JS test suite) |
| **Config file** | none — UI changes verified via browser at localhost:8000 |
| **Quick run command** | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| **Full suite command** | `bash scripts/voice_verify.sh` (voice/backend tests only) |
| **Estimated runtime** | ~5 seconds (server start) |

---

## Sampling Rate

- **After every task commit:** Reload browser, verify changed component visually
- **After every plan wave:** Full visual review across all three columns (LSB, main, RSB)
- **Before `/gsd:verify-work`:** Full suite must be green + manual UI walkthrough complete
- **Max feedback latency:** 10 seconds (server reload + browser refresh)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-css-01 | CSS | 1 | UI-04 | manual | browser reload | ✅ | ⬜ pending |
| 1-css-02 | CSS | 1 | UI-04 | manual | browser reload | ✅ | ⬜ pending |
| 1-lsb-01 | Sidebar | 1 | UI-02 | manual | browser reload | ✅ | ⬜ pending |
| 1-lsb-02 | Sidebar | 1 | UI-02 | manual | browser reload | ✅ | ⬜ pending |
| 1-chat-01 | Chat | 2 | UI-03 | manual | browser reload | ✅ | ⬜ pending |
| 1-chat-02 | Chat | 2 | UI-03 | manual | browser reload | ✅ | ⬜ pending |
| 1-layout-01 | Layout | 2 | UI-01 | manual | browser reload | ✅ | ⬜ pending |
| 1-rsb-01 | RSB | 2 | UI-01 | manual | browser reload | ✅ | ⬜ pending |
| 1-settings-01 | Settings | 3 | UI-02 | manual | browser reload | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. This is a pure frontend polish phase — no new test files needed. Backend voice/assist tests (`bash scripts/voice_verify.sh`) should remain green throughout.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Glass panel visual quality | UI-04 | CSS visual effects can't be automated | Check backdrop-filter blur on sidebar at localhost:8000 |
| Responsive layout at 1440p | UI-01 | Requires physical display at that resolution | Set browser viewport to 1440×900, verify no 110% zoom needed |
| Session list renders correctly | UI-02 | DOM rendering consistency | Load app with existing sessions, verify list shows and is scrollable |
| Sidebar collapse/expand animation | UI-02 | Animation smoothness | Click collapse toggle, verify smooth 200ms slide |
| Auto-scroll during streaming | UI-03 | Requires live LLM stream | Send message, verify chat scrolls as tokens arrive |
| Thinking block collapses | UI-03 | Requires model with thinking | Send reasoning-triggering prompt, verify "Thinking..." pill appears collapsed |
| Wakeword bar is faint | UI-03 | Visual judgment | Enable wakeword, verify status bar is clearly secondary to input pill |
| Settings modal opens reliably | UI-02 | Click handler reliability | Click gear icon 5 times, verify modal opens every time |
| System prompt profiles sync | UI-04 | Two-way sync between RSB and modal | Change profile in RSB, verify modal reflects change |
| 1440p layout without zoom | UI-01 | Resolution-specific | View at native 1440p, no zoom required |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
