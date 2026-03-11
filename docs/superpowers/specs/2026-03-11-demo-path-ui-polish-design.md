# Demo Path UI Polish — Design Spec
**Date:** 2026-03-11
**Scope:** `app/static/css/app.css`, `app/templates/index.html`, `app/static/js/app.js`
**Out of scope:** Tutorial/onboarding, setup wizard, RAG panel, memory system UI, backend changes

---

## Goal

Make the 30–60s demo feel smooth and intentional:
```
App launch → clean UI → "Hey Jarvis" → STT → "light banda kar"
→ router → HA tool → light off → clear success shown
```

---

## Phase 1 — Midnight Glass CSS Pass

### Files
- `app/templates/index.html` (HTML cleanup only)
- `app/static/css/app.css` (CSS variables + panel styles)

### HTML Cleanup (`index.html`)
- **Font import:** Trim the existing combined `<link>` (which imports Space Grotesk, Fira Code, Comic Neue, VT323, etc.) to retain **only** `Inter` and `JetBrains Mono`. Do NOT add a new `<link>` tag.
- **Theme selector:** Remove `<select id="theme-select">` and its `<option>` elements. Also remove the entire `<div class="setting-group" id="grp-theme">` wrapper. Also remove the Appearance rail button (`#btn-rail-appearance`) from the right-rail nav — it deep-links to `#grp-theme` which will no longer exist.

### CSS Variables (`app.css` `:root`)

**Intent:** The values below intentionally replace existing live values — this is a global visual change affecting ~20 selectors. Every surface using these variables will shift from near-opaque solid panels to translucent glass. This is the desired outcome.

Replace existing values:
```css
--bg-sidebar:    rgba(10, 10, 10, 0.55);   /* was rgba(8,8,10,0.95) — now glass */
--bg-panel:      rgba(15, 15, 15, 0.45);   /* was #020202 solid — now glass */
--border-subtle: rgba(255, 255, 255, 0.15); /* was rgba(255,255,255,0.08) */
--text-primary:  #ffffff;                   /* was #f4f4f5 */
```

Add as new variables (do not already exist):
```css
--glass-filter:      blur(24px) saturate(180%);
--border-highlight:  rgba(255, 255, 255, 0.05);
--text-secondary:    #a1a1aa;
```

### Glass Panel Recipe
Apply to: sidebar, main chat container, settings card, modals:
```css
background: var(--bg-panel);
backdrop-filter: var(--glass-filter);
-webkit-backdrop-filter: var(--glass-filter);
border: 1px solid var(--border-subtle);
box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 var(--border-highlight);
```

### Typography
- Body/UI font: `Inter`, weights 400/500/600
- Code font: `JetBrains Mono`
- No other fonts anywhere in the UI

### Component Updates
- **User message bubble:** `rgba(255,255,255,0.1)` background, white text, `1px` border using `--border-subtle`
- **Chat input:** `border-radius: 100px`, recessed inset shadow, glass background
- **Hover states:** Opacity bump only (e.g. `0.05` → `0.1` on background), no color swaps

### Constraints
- Do NOT touch `app.js`, `updater_ui.js`, or setup wizard files
- Do NOT rename any element IDs or CSS class names used by JS
- `els.themeSelect` in `app.js` will be `null` after this change — this is safe, `updateTheme()` is null-guarded and no-ops silently
- After removing VT323 from the font `<link>`, the CSS variable `--font-pixel: 'VT323', monospace` will silently fall back to `monospace`. This is intentional — no TUI/pixel-font styling in the Midnight Glass identity. Leave the variable declaration as-is.

---

## Phase 2 — Voice Status Bar

### Files
- `app/templates/index.html` — add status bar element
- `app/static/css/app.css` — status bar styles + state classes
- `app/static/js/app.js` — add callback hooks to `wakewordUI` and `voiceUI`, wire status bar

### Element
Insert as the **first child of `.input-wrapper`**, above `#tools-chip-row` and `.input-container`:

```html
<div id="voice-status-bar" class="voice-status-bar hidden">
  <div class="voice-status-dot"></div>
  <span class="voice-status-label"></span>
  <span class="voice-status-tag"></span>
</div>
```

### States, Colors & Labels

Map from **actual state machine values** to status bar display:

| Source | State machine value | Bar color | Label | Tag |
|--------|-------------------|-----------|-------|-----|
| wakewordUI active, idle | `idle` | Gray `#3f3f46` | Say "Hey Jarvis" | wakeword |
| wakewordUI | `recording` | Amber `#f59e0b` | Hey Jarvis — listening… | triggered |
| voiceUI | `listening` | Amber `#f59e0b` | Listening… | recording |
| voiceUI | `transcribing` | Amber `#f59e0b` | Transcribing… | stt |
| voiceUI | `confirming` / `waiting` | Amber `#f59e0b` | Processing… | thinking |
| on completion | *(see below)* | Green `#10b981` | Done | success |

**Color rule:** Gray (idle) → Amber (all active states) → Green (done) → fade back to Gray after 2s.

### Visibility
- Bar is **hidden** (`display:none`) when wakeword is disabled
- Bar **shows** (fade in via `opacity` transition) when wakeword is enabled via `wakewordUI.enable()`
- After `done`, use a `setTimeout` (2000ms) to reset back to idle gray state

### JS Wiring Strategy

**Architecture:** Both `wakewordUI` and `voiceUI` expose their state changes only through private closure functions (`_setStateLabel`, `_setState`). The correct approach is to add a lightweight `onStateChange(cb)` registration to each module's return object. This is additive — existing logic is not modified, only the return statement gains a new export.

#### Step 1 — Add `onStateChange` to `wakewordUI`
Inside the `wakewordUI` IIFE, before the `return` statement:
```javascript
const _stateChangeCallbacks = [];
function onStateChange(cb) { _stateChangeCallbacks.push(cb); }
```
At the top of `_setStateLabel(state)`, add:
```javascript
_stateChangeCallbacks.forEach(cb => cb(state));
```
Add `onStateChange` to the return object.

#### Step 2 — Add `onStateChange` to `voiceUI`
Same pattern inside `voiceUI` IIFE. At the top of `_setState(newState)`, fire callbacks:
```javascript
_stateChangeCallbacks.forEach(cb => cb(newState));
```

#### Step 3 — Add `done` trigger to chat completion
In `api.chat()`, `isAssistMode` is a local `const` declared early in the function (around line 4135). The stream ends when `await readSSE(res, ...)` returns (around line 4231) — there is no SSE `done` event. The correct insertion point is inside the `try` block, after `await readSSE` returns and before `state.isGenerating = false` (around line 4307). Add:
```javascript
if (isAssistMode) voiceStatusBar.setDone();
```
This fires `done` only on Home Control commands, not regular chat.

#### Step 4 — Wire `voiceStatusBar` module
Add to `els` object:
```javascript
voiceStatusBar: document.getElementById('voice-status-bar'),
voiceStatusLabel: document.querySelector('#voice-status-bar .voice-status-label'),
voiceStatusTag: document.querySelector('#voice-status-bar .voice-status-tag'),
voiceStatusDot: document.querySelector('#voice-status-bar .voice-status-dot'),
```

Create a `voiceStatusBar` module:
```javascript
const voiceStatusBar = {
  show() { els.voiceStatusBar?.classList.remove('hidden'); },
  hide() { els.voiceStatusBar?.classList.add('hidden'); },
  setState(state) { /* update dot color, label, tag, CSS classes */ },
  setDone() {
    voiceStatusBar.setState('done');
    setTimeout(() => voiceStatusBar.setState('idle'), 2000);
  },
  init() {
    wakewordUI.onStateChange(state => voiceStatusBar.setState(state));
    voiceUI.onStateChange(state => voiceStatusBar.setState(state));
  }
};
```

Call `voiceStatusBar.show()` from within `wakewordUI.enable()` and `voiceStatusBar.hide()` from `wakewordUI.disable()`.

### CSS Classes
```css
.voice-status-bar          /* base: glass pill, flex row, gap */
.voice-status-bar.hidden   /* display: none — add this rule explicitly; do NOT rely on the global .hidden class */
.voice-status-bar.amber    /* amber border + glow: border-color #f59e0b, box-shadow amber */
.voice-status-bar.green    /* green border + glow: border-color #10b981, box-shadow green */
.voice-status-dot          /* 7px circle, background driven by parent class */
```

Transition: `opacity 0.2s ease` on show/hide, `border-color 0.15s ease` on state change.

---

## Acceptance Criteria

### Phase 1
- [ ] App renders with Inter font throughout, no other fonts visible
- [ ] Sidebar and chat panels have visible glass/blur effect
- [ ] Theme selector and Appearance rail button are gone
- [ ] No unused font `<link>` imports in `<head>`
- [ ] User message bubbles are high-contrast pills
- [ ] Chat input is rounded pill shape
- [ ] No JS console errors on page load

### Phase 2
- [ ] Status bar hidden on page load (wakeword off)
- [ ] Status bar appears (fades in) when wakeword is enabled
- [ ] Bar shows gray "Say Hey Jarvis" when wakeword idle
- [ ] Saying "Hey Jarvis" turns bar amber and cycles through correct labels per state
- [ ] Bar turns green with "Done" after command completes
- [ ] Bar resets to gray idle 2s after Done
- [ ] Existing mic button and wakeword toggle still work unchanged
- [ ] No new console errors introduced

### Regression Smoke Test (Phase 2)
1. Enable wakeword → status bar appears
2. Click mic button manually (PTT) → bar shows amber Listening → Transcribing → Processing
3. Submit a normal chat message (non-voice) → bar stays idle/hidden, no interference
4. Disable wakeword → status bar hides
