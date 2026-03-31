---
phase: 01-ui-polish
plan: "04"
subsystem: ui
tags: [css, javascript, html, rsb, branding, date-separators, stats]

requires:
  - phase: 01-01
    provides: CSS foundation variables, rsb-section-label and rsb-divider CSS classes
  - phase: 01-03
    provides: JS message rendering (appendMessage, buildMessageHTML) — serialized to avoid conflict

provides:
  - RSB section labels (Lights, Model, Prompt, Stats) above each content block
  - 1px dividers between RSB sections (8% white opacity)
  - Compact stat rows (CPU/RAM/VRAM each as bar+value, 3px height)
  - Jarvis->Localis rename in all JS-generated sender labels, presets, and profile prompts
  - Date group separators (Today/Yesterday/date) injected during history load
  - LSB gear accessible when sidebar collapsed (already correct, confirmed)

affects:
  - downstream UI polish plans that read JS-generated text
  - 01-05, 01-06 (later plans in wave 3/4)

tech-stack:
  added: []
  patterns:
    - groupMessagesByDate(): date-grouping helper returns separator+message interleaved array
    - setBar(): compact stat-row update helper inside _refreshStats
    - RSB sections now use rsb-section-label + rsb-divider pattern (not just rsb-sec-lbl inline)

key-files:
  created: []
  modified:
    - app/templates/index.html
    - app/static/css/app.css
    - app/static/js/app.js

key-decisions:
  - "Preset chips renamed code->planning and precise->custom to match CONTEXT.md canonical 4 profiles"
  - "Legacy rsb-cpu/ram/vram-bar hidden elements preserved for JS compatibility; new stat-bar-* IDs drive compact rows"
  - "Hey Jarvis wakeword phrases in STATE_MAP kept unchanged — trigger phrase, not assistant name"
  - "groupMessagesByDate only runs on history load (not streaming) — new messages always belong to Today"

patterns-established:
  - "Branding: all JS-generated assistant labels use Localis; only wakeword trigger strings keep Hey Jarvis"
  - "Date separators: injected via DOM createElement, not innerHTML, to keep chat-history structure clean"

requirements-completed:
  - UI-01
  - UI-04

duration: 12min
completed: "2026-03-15"
---

# Phase 01 Plan 04: RSB Polish & Branding Rename Summary

**RSB section labels, 1px dividers, compact stat rows, Jarvis->Localis rename across JS-generated text, and Today/Yesterday date separators on history load**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-15T~10:39Z
- **Completed:** 2026-03-15T~10:51Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added visible "Lights", "Model", "Prompt", "Stats" section labels and 1px dividers to RSB body
- Replaced 3-column stat cards with compact single-row layout (label + 3px bar + value)
- Renamed all assistant name references in JS from "Jarvis" to "Localis" (sender labels, preset prompts, modal profile prompts) while preserving "Hey Jarvis" wakeword trigger phrases
- Added date group separators (Today / Yesterday / Mar 12) that appear between message groups when loading session history

## Task Commits

1. **Task 1: RSB section labels, dividers, compact stats (HTML + CSS)** - `8703e32` (feat)
2. **Task 2: Jarvis->Localis rename and date group separators (JS)** - `4e0ab36` (feat)

## Files Created/Modified

- `app/templates/index.html` - Added 3 rsb-section-label divs, 3 rsb-divider hrs, replaced stats layout with compact stat-row structure, renamed preset chips (code->planning, precise->custom)
- `app/static/css/app.css` - Added stat-row/stat-label/stat-bar-wrap/stat-bar/stat-value CSS, date-separator CSS, lsb.collapsed .lsb-nav-label hide rule
- `app/static/js/app.js` - buildMessageHTML sender label "Localis" (initial "L"), PRESETS planning/custom profiles updated, PROFILES modal prompts all updated to Localis, _refreshStats setBar() helper for compact rows, groupMessagesByDate() function, history load uses date grouping

## Decisions Made

- Preset chips renamed to Default/Creative/Planning/Custom per CONTEXT.md canonical profiles. Old "code" and "precise" presets removed.
- Legacy rsb-cpu/ram/vram-bar hidden elements preserved inline so existing JS references in `els.rsbCpuBar` etc. don't break. New `stat-bar-cpu/ram/vram` IDs drive visible compact rows.
- "Hey Jarvis" in `STATE_MAP` voice status bar labels kept intact — those are trigger phrase strings, not assistant name labels.
- `groupMessagesByDate` only applied during history load, not streaming — streaming messages always belong to "Today" so no separator injection needed there.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Preserved legacy hidden stat elements for JS compatibility**
- **Found during:** Task 1 (HTML restructure)
- **Issue:** `_refreshStats()` references `els.rsbCpuBar`, `els.rsbRamBar`, `els.rsbVramBar` by ID; removing the old stat cards would break those references
- **Fix:** Kept old rsb-cpu/ram/vram-bar elements hidden (display:none) inside the new stats section so JS references remain valid; new stat-bar-* IDs added for the visible compact rows
- **Files modified:** app/templates/index.html, app/static/js/app.js
- **Verification:** grep confirms both old and new IDs present; node --check passes
- **Committed in:** 8703e32 + 4e0ab36

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical compatibility guard)
**Impact on plan:** Necessary to prevent runtime errors. No scope creep.

## Jarvis->Localis Rename Log

All locations changed:

| Location | Old | New |
|----------|-----|-----|
| `buildMessageHTML` displayName | `'Jarvis'` | `'Localis'` |
| `buildMessageHTML` initial | `'J'` | `'L'` |
| RSB PRESETS creative | `You are Jarvis, a creative...` | `You are Localis, a creative...` |
| RSB PRESETS code | `You are Jarvis, a coding...` | (renamed to planning) |
| RSB PRESETS precise | `You are Jarvis, a precise...` | (renamed to custom) |
| Modal PROFILES Home Control | `You are Jarvis, a smart home...` | `You are Localis, a smart home...` |
| Modal PROFILES Hinglish | `You are Jarvis.` | `You are Localis.` |
| Modal PROFILES Night Owl | `You are Jarvis.` | `You are Localis.` |
| Modal PROFILES Tech Mode | `You are Jarvis, a technical...` | `You are Localis, a technical...` |
| Modal PROFILES Coding | `You are Jarvis, a coding...` | `You are Localis, a coding...` |

Preserved (wakeword trigger phrases):
- `STATE_MAP idle.label`: `'Say "Hey Jarvis"'`
- `STATE_MAP recording.label`: `'Hey Jarvis — listening…'`
- `STATE_MAP cooldown.label`: `'Say "Hey Jarvis"'`
- `STATE_MAP disabled.label`: `'Say "Hey Jarvis"'`

## Issues Encountered

None.

## Next Phase Readiness

- RSB structure now has clear section separation with visible labels and dividers
- Stats display upgraded to compact row format with JS-driven bar widths
- Branding consistent throughout all user-visible JS-generated text
- Date separators ready for multi-day chat sessions
- Wave 3 of 01-ui-polish (plans 04-05) now complete

## Self-Check: PASSED

- FOUND: app/templates/index.html
- FOUND: app/static/css/app.css
- FOUND: app/static/js/app.js
- FOUND: .planning/phases/01-ui-polish/01-04-SUMMARY.md
- FOUND commit: 8703e32
- FOUND commit: 4e0ab36

---
*Phase: 01-ui-polish*
*Completed: 2026-03-15*
