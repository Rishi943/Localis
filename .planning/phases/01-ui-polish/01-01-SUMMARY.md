---
phase: 01-ui-polish
plan: 01
subsystem: ui
tags: [css, design-system, glass, variables, scrollbar, responsive]

# Dependency graph
requires: []
provides:
  - Canonical CSS variable set (--bg-app, --accent-primary, --glass-filter, --panel-gradient, --border-*, --status-*, --r-*, etc.)
  - Glass panel recipe applied to .lsb, .rsb using new variable set
  - Responsive sidebar widths via clamp() for 1080p-1440p range
  - Ghost scrollbar recipe (invisible at rest, visible on container hover)
  - RSB section label (.rsb-section-label) and divider (.rsb-divider) classes
  - Wave 0 assertion script (tests/test_ui_polish_assertions.sh)
affects: [01-02, 01-03, 01-04, 01-05, 01-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CSS variable naming: --{scope}-{property} (e.g. --bg-app, --accent-primary, --glass-filter)"
    - "Glass panel recipe: var(--panel-gradient), var(--bg-panel/sidebar) + backdrop-filter + border + box-shadow"
    - "Ghost scrollbar: transparent at rest, rgba(255,255,255,.08) on :hover of scrollable container"
    - "ID-only CSS for unique elements: #voice-status-bar instead of .voice-status-bar"

key-files:
  created:
    - tests/test_ui_polish_assertions.sh
  modified:
    - app/static/css/app.css

key-decisions:
  - "ID selectors only for #voice-status-bar — element is unique in DOM, class selectors removed to satisfy assertion 4 and avoid selector ambiguity"
  - "Ghost scrollbar uses container :hover descendant targeting, not element :hover — prevents scrollbar flash when thumb itself is hovered"
  - "rsb-section-label added alongside existing rsb-sec-lbl for downstream plans that use the new naming convention"

patterns-established:
  - "All CSS variables use DESIGN.md canonical set — no --indigo or --glass-* legacy names allowed"
  - "Body/html background: var(--bg-app) (#080808) with no radial-gradient coloring"
  - "Sidebar widths: clamp(200px, 15vw, 260px) for .lsb, clamp(250px, 18vw, 320px) for .rsb"
  - "Chat column: max-width: clamp(560px, 55vw, 720px) centered via margin:0 auto"

requirements-completed: [UI-01, UI-04]

# Metrics
duration: 25min
completed: 2026-03-15
---

# Phase 01 Plan 01: CSS Foundation Summary

**Canonical DESIGN.md variable set established in app.css, glass panel recipe applied, clamp() responsive widths, ghost scrollbar, and Wave 0 assertion script — all legacy --indigo/--glass-* names removed**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-15T00:00:00Z
- **Completed:** 2026-03-15T00:25:00Z
- **Tasks:** 3 (Task 0, Task 1, Task 2)
- **Files modified:** 2

## Accomplishments
- Created `tests/test_ui_polish_assertions.sh` with 8 structural assertions (Wave 0 regression guard for all plans in this phase)
- Replaced split/legacy CSS variable system with canonical DESIGN.md set: 25 new variables, 9 legacy names removed (--indigo, --indigo-soft, --indigo-border, --glass-bg, --glass-blur, --glass-border, --glass-border-top, --glass-shadow-old, --bg-dark)
- Applied glass panel recipe to .lsb and .rsb using new variable set; clamp() responsive widths for sidebars and chat column; ghost scrollbar visible only on container hover; RSB section label/divider classes added
- Converted all `.voice-status-bar` class selectors to `#voice-status-bar` ID selectors — assertion 4 now passes alongside assertions 1, 2, 3

## Task Commits

Each task was committed atomically:

1. **Task 0: Create Wave 0 test script** - `cbf0da2` (chore) — from prior session
2. **Task 1: Consolidate CSS variables and strip legacy names** - `1637fc5` (feat)
3. **Task 2: Apply glass recipe, responsive widths, ghost scrollbar, RSB labels** - `67ff224` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified
- `tests/test_ui_polish_assertions.sh` - 8-assertion Wave 0 structural test script; assertions 1-4 pass after this plan
- `app/static/css/app.css` - Full :root canonical variable set; glass panel recipe on .lsb/.rsb; clamp() responsive widths; ghost scrollbar; #voice-status-bar ID selectors; .rsb-section-label and .rsb-divider

## Decisions Made
- ID selectors only for `#voice-status-bar`: The element is unique in the DOM — using class selectors was redundant and violated the Wave 0 assertion. Converted all 10 class selector rules to ID form.
- Ghost scrollbar uses container `:hover` descendant targeting (`.sess-list:hover ::-webkit-scrollbar-thumb`) rather than element `:hover` on the thumb — prevents the flicker where scrollbar disappears as the user moves cursor to grab it.
- Added `.rsb-section-label` alongside existing `.rsb-sec-lbl` — downstream plans (01-02 onwards) reference the new naming convention in their HTML additions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] .voice-status-bar class selectors violated Wave 0 assertion 4**
- **Found during:** Task 2 (running assertion script)
- **Issue:** Assertion 4 requires `count = 0` for `.voice-status-bar` class selectors. The existing CSS block at lines 246-315 used class form; a separate `#voice-status-bar` ID block was a duplicate.
- **Fix:** Converted all `.voice-status-bar.*` selectors to `#voice-status-bar.*` ID form; removed duplicate block; updated dot/tag colors to use CSS vars (--status-amber, --status-green)
- **Files modified:** app/static/css/app.css
- **Verification:** Assertion 4 PASS (grep count = 0)
- **Committed in:** `67ff224` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug/inconsistency)
**Impact on plan:** Required change to make the assertion script pass. The structural fix also improves selector specificity consistency.

## Issues Encountered
- Task 0 (test script) was already committed from a prior session (`cbf0da2`). Task 1 CSS variable work was already in the working directory (uncommitted). Committed each task separately as required by protocol.
- `python -c "import app.main"` fails without the venv — verified with `.venv/bin/python` instead; imports cleanly with only a pynvml deprecation warning (unrelated to our changes).

## Next Phase Readiness
- CSS foundation is stable. All downstream plans (01-02 through 01-06) can reference: `--bg-app`, `--accent-primary`, `--glass-filter`, `--panel-gradient`, `--border-subtle`, `--border-highlight`, `--r-sm`, `--r-md`, `--r-pill`, `--text-primary`, `--text-secondary`, `--text-muted`, `--status-green`, `--status-amber`, `--status-red`
- Wave 0 assertion script is ready — Plan 01-06 checkpoint will run it to verify all plans maintained the CSS contracts
- Assertions 5-8 require HTML/JS changes from plans 01-02 through 01-05

---
*Phase: 01-ui-polish*
*Completed: 2026-03-15*
