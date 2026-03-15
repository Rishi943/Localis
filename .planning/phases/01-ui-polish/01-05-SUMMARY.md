---
phase: 01-ui-polish
plan: 05
subsystem: settings-modal
tags: [ui, settings, profiles, modal, api]
dependency_graph:
  requires: [01-01, 01-02, 01-03, 01-04]
  provides: [settings-modal, profile-sync, api-settings]
  affects: [app/templates/index.html, app/static/css/app.css, app/static/js/app.js, app/main.py]
tech_stack:
  added: []
  patterns: [PROFILE_MAP-singleton, setActiveProfile-bridge, fetch-POST-settings]
key_files:
  created: []
  modified:
    - app/templates/index.html
    - app/static/css/app.css
    - app/static/js/app.js
    - app/main.py
decisions:
  - GET /api/settings did not exist — added from scratch alongside POST /api/settings
  - All 6 settings fields added to POST handler (accent_color, wallpaper_opacity, gpu_layers, context_size, active_profile, custom_profile_prompt)
  - PROFILE_MAP replaces old inline PRESETS dict in RSB chip handler — single source of truth
  - setActiveProfile() bridges RSB chips and settings modal profile chips via shared state.activeProfile
  - btn-top-settings cloned before re-wiring to remove old toggleSettings listener
  - custom_profile_prompt updated in PROFILE_MAP.custom on textarea input so save picks it up
metrics:
  duration: 4 minutes
  completed_date: "2026-03-15"
  tasks_completed: 3
  files_modified: 4
---

# Phase 01 Plan 05: Settings Modal and Profile Sync Summary

Settings modal HTML, CSS, and JavaScript built from scratch; shared 4-profile system prompt system wired so RSB chips and modal Profiles tab stay in sync via a single `PROFILE_MAP` and `setActiveProfile()` function.

## What Was Built

### Task 1 — Settings Modal HTML and CSS

Added the `#settings-overlay` modal to `index.html` immediately before the script tags. The modal uses three tabs (Inference, Appearance, Profiles), each with a `.settings-pane` div. The existing `#system-prompt-modal` was left in place (it is still used by the "Edit System Prompt" sidebar button); only the gear icon buttons now open the new full settings modal.

Added to `app.css`:
- `.settings-modal` — 680px wide glass dialog with flex column layout
- `.settings-tabs` / `.settings-tab` — tab bar with active state
- `.settings-pane` — hidden by default, `display: flex` when `.active`
- `.settings-row` / `.settings-label` / `.settings-select` / `.settings-input` — form row layout
- `.settings-color` / `.settings-file` / `.settings-textarea` — specialised input styles
- `.profile-list` / `.profile-chip` — profile chip row, accent-highlighted when active
- `.btn-primary` — accent-coloured Save button
- Existing `.modal-overlay` and `.modal-dialog` glass recipe applied (no duplication)

### Task 2a — Settings Modal JS

**PROFILE_MAP** added before the RSB chip handler. Four profiles: Default, Custom (user-editable), Creative, Planning. Canonical source of truth for both RSB chips and the modal.

**setActiveProfile(key)** — synchronises both chip sets, fills `#set-sys-prompt` textarea, applies prompt to legacy `#system-prompt-editor` and `#system-prompt-modal-editor`, calls `api.saveSystemPrompt()`, sets `state.activeProfile`.

**renderSettingsProfiles()** — populates `#settings-profile-list` dynamically from PROFILE_MAP; each chip has `data-profile-key` attribute and calls `setActiveProfile()` on click.

**RSB chip handler** — old inline `PRESETS` dict replaced; now delegates to `setActiveProfile(preset)`.

**initSettingsModal() IIFE** — sets up tab switching, open/close functions, backdrop/Escape dismissal, btn-settings-close wire-up, btn-top-settings re-wired to open settings modal (node cloned to remove old listener), custom textarea listener to update `PROFILE_MAP.custom.prompt`.

**saveSettings()** — async fetch POST to `/api/settings` with all 6 fields; applies accent colour immediately on success; closes overlay.

**loadSettings()** — async fetch GET from `/api/settings`; applies accent colour, sets `PROFILE_MAP.custom.prompt`, calls `setActiveProfile()`. Called in `startApp()` for returning users.

### Task 2b — GET and POST /api/settings in main.py

**Status:** GET `/api/settings` did NOT exist before this plan. Added from scratch.

Added `AppSettingsRequest` Pydantic model with 6 optional fields.

`GET /api/settings` — reads `accent_color`, `wallpaper_opacity`, `gpu_layers`, `context_size`, `active_profile`, `custom_profile_prompt` from the `app_settings` table via `database.get_app_setting()`. Returns only keys that have persisted values.

`POST /api/settings` — writes each provided field to `app_settings` via `database.set_app_setting()`. All 6 fields processed. Returns `{status: "ok", updated: [...keys]}`.

## Deviations from Plan

None — plan executed exactly as written with one minor addition:

- `btn-top-settings` DOM node is cloned before re-wiring (deviation Rule 2 — prevents duplicate listener from old `toggleSettings` remaining active). This is a correctness requirement, not a new feature.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| 01-05-SUMMARY.md | FOUND |
| app/templates/index.html | FOUND |
| app/static/css/app.css | FOUND |
| app/static/js/app.js | FOUND |
| app/main.py | FOUND |
| Commit 327e576 (HTML+CSS) | FOUND |
| Commit cce29cc (JS) | FOUND |
| Commit 6de8693 (main.py) | FOUND |
