# UI Redesign — Design Spec

> **For agentic workers:** Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this spec.

**Goal:** Redesign the Localis frontend with a Midnight Glass visual identity, a minimal chrome layout, inline action cards, and a quick-controls right sidebar — replacing the current wide config panel and plain chat bubbles.

**Reference mockups:** `.superpowers/brainstorm/18519-1773247506/` (hidden dir at repo root) — `shell-v2.html`, `sidebar-redesign.html`, `message-refined.html`

---

## 1. Layout

**Three-column shell:** Left sidebar (collapsible) · Main chat area · Right sidebar (collapsible)

### Top bar
- Online status dot + model name + session title (left)
- Spacer
- ⚙ settings icon button (right) — opens settings modal

### Left sidebar (session history)
- **Expanded (216px):** Toggle chevron button · "Localis" title · New Chat button (icon: `localis-new-chat.svg`) · Session list with date groups · Status footer (green dot + "Online · model-name")
- **Collapsed (44px):** Toggle chevron button · New Chat icon button · Status dot
- Collapse/expand toggle uses left/right chevron SVG symbols (`ico-left` / `ico-right`), **not** the new-chat icon

### Right sidebar (quick controls)
- **Expanded (252px):** See section 4
- **Collapsed (44px):** Icon rail — model, temperature, memory, settings icons stacked vertically
- Collapse toggle uses chevron icons

### Main area
- Top bar (fixed)
- Chat scroll zone — centred, `max-width: 600px`
- Input zone — centred, `max-width: 600px`, pinned to bottom

---

## 2. Chat Messages

**No speech bubbles.** Prose layout with avatars and name labels.

### Message row structure
```
[avatar] [name label]
         [message text]
```
- User messages: row-reversed (avatar + name on right), text right-aligned
- AI messages: normal (avatar + name on left), text left-aligned
- Avatar: 22px circle. User initial = first letter of Tier-A `name` key (uppercase); fallback "U". AI initial always "J".
  - User avatar: `rgba(255,255,255,0.1)` background, white border
  - AI avatar: `rgba(99,102,241,0.2)` background, indigo border
- Name label: 8px, uppercase, 600 weight, letter-spacing 0.05em
  - User: `rgba(255,255,255,0.2)`
  - AI: `rgba(99,102,241,0.5)`
- Message text: 13px, line-height 1.5
  - User: `rgba(255,255,255,0.9)`
  - AI: `rgba(255,255,255,0.7)`

### Action cards (tool results)
Rendered inline in the chat stream, between the triggering user message and the AI response.

```
[left accent border] [icon] [title]
                             [subtitle]
```

- Left border: 3px solid, border-radius `0 8px 8px 0`
- **Home control:** green accent `#10b981`, background `rgba(16,185,129,0.07)`, icon `localis-home-assistant.svg`
- **Memory save:** indigo accent `#6366f1`, background `rgba(99,102,241,0.07)`, icon `localis-memory.svg`
- Title: 11px, 600 weight
- Subtitle: 9px, `rgba(255,255,255,0.3)`

---

## 3. Input Area

Stacked vertically inside `max-width: 600px` container:

1. **Voice status bar** — visual restyle only. Preserve existing element ID `#voice-status-bar` and CSS class hooks `.amber` / `.green` exactly — the wakeword JS pipeline in `app.js` sets these classes directly. Do not change the element structure, only update visual styles to match the liquid glass theme.
   - States: gray idle → amber active ("Listening…") → green done ("Got it")
   - Text: "Say 'Hey Jarvis'" / "Listening…" / last command
   - Tag label (right): "wakeword" / "listening" / "done"

2. **Mode pill toggles** (row) — replace the existing `toolsUI` chip row. Each pill maps to an existing send-path flag:

   | Pill | Old `toolsUI` key | Send-path field in `ChatRequest` |
   |---|---|---|
   | Web | `web_search` | `web_search_mode: true` |
   | Home | `assist_mode` | `assist_mode: true` (used as `isAssistMode` in `api.chat()`) |
   | Upload | RAG file picker (no mode flag) | triggers file input, no payload change |
   | Remember | `memory_write` | included in `selected_tools` array |

   The send-message path at `app.js ~line 4150` reads `toolsUI.selectedTools` and `toolsUI.stickyTools`. Replace that read with pill state. Pill state must be reflected in the same fields so `main.py`'s router receives identical data. The tutorial gate on the right sidebar (`frt-allow-right-sidebar`, `frt-right-sidebar-unlocked` CSS classes at `app.js ~lines 768–790, 3052–3072`) must remain untouched — the tutorial flow is out of scope.

   - Inactive pill: `rgba(255,255,255,0.03)` bg, `rgba(255,255,255,0.08)` border, `rgba(255,255,255,0.3)` text
   - Active pill: `rgba(245,158,11,0.12)` bg, `rgba(245,158,11,0.3)` border, `#fcd34d` text + icon
   - Icons: `localis-web-search.svg`, `localis-home-assistant.svg`, `localis-from-file.svg`, `localis-memory.svg`

3. **Input row** (pill-shaped bar)
   - Left: voice mic button (26px circle, `localis-voice.svg`)
   - Centre: placeholder text "Message Jarvis…"
   - Right: SEND button (pill)

---

## 4. Right Sidebar — Quick Controls

Five sections, stacked, separated by 1px dividers.

### Section 1: Lights
- Section label: "LIGHTS" with `localis-home-assistant.svg`
- Entity row: entity name (left) + on/off toggle (right, amber when on)
- Brightness percentage (large, centred, tabular nums)
- Timestamp ("N seconds ago", small, muted)
- Bulb visual:
  - 78×130px rounded rectangle (`border-radius: 22px`)
  - Dark background `#0c0c0c`
  - Fill div (`position: absolute; bottom: 0`) with amber gradient, height = brightness %
  - Indicator line at fill boundary
  - Amber border + outer glow when on
- Control buttons row (4 × 32px circles): Power · Brightness · Colour · Kelvin
  - Active button (Brightness by default): amber tint + glow
- Colour swatches: **two rows of 4** × 17px circles (flex-wrap):
  - Row 1: orange `#f97316`, peach `#fdba74`, cream `#fde8d3`, white `#f5f5f5`
  - Row 2: indigo `#6366f1`, purple `#a855f7`, pink `#ec4899`, red `#ef4444`
  - Selected swatch has white border ring

**Live state:** Poll `GET /assist/light_state` every 5 seconds while the sidebar is open. See backend spec in section 8.

### Section 2: Model
- Section label: "MODEL" with `localis-model.svg`
- Dropdown pill: current model name + "● ONLINE" sub-label + ▾ arrow
- Quick-switch chips row: up to 4 model chips (current highlighted indigo) + "+ More"

### Section 3: System Prompt
- Section label: "SYSTEM PROMPT"
- 4 preset pills: Default (active) · Creative · Code · Precise
- "Edit System Prompt →" button — opens System Prompt Modal

### Section 4: System Stats
- Section label: "SYSTEM"
- 3-column grid of stat cards:
  - **CPU** — percentage value, green gradient bar
  - **RAM** — GB used value, indigo gradient bar
  - **VRAM** — GB used value, amber gradient bar (warns visually at >80%)
- Each card: label (7px caps) · large value (17px, tabular nums) · 2px progress bar
- Poll `GET /api/system-stats` every 3 seconds while sidebar is open. See backend spec in section 8.

### Section 5: Context Window
- Section label: "CONTEXT WINDOW"
- ASCII block progress bar: `████████████░░░░░░░░` (JetBrains Mono, 12px, indigo glow)
- Meta row: "N,NNN / N,NNN tokens" (left) + "NN%" (right, indigo)
- Token count: maintained in JS as messages are appended using the existing approximation `Math.ceil(totalChars / 4)` — consistent with `main.py`'s router budget. Max context from `state.nCtx` (already tracked in app state).

---

## 5. System Prompt Modal

**Replaces** the existing `#system-prompt-modal` in `index.html`. Preserve these element IDs so existing JS wiring in `app.js` continues to function: `#btn-open-prompt-modal`, `#btn-modal-save-prompt`, `#modal-system-prompt`, `#system-prompt-text` (the textarea). Update only the surrounding HTML structure and visual styles.

Triggered by "Edit System Prompt →" in the right sidebar (replaces the existing trigger button).

- Overlay: `rgba(0,0,0,0.55)` + `backdrop-filter: blur(6px)`
- Modal: 460px wide, liquid glass (`backdrop-filter: blur(44px) saturate(180%)`)
- Header: "System Prompt" title + subtitle "Define Jarvis's personality & behavior" + ✕ close
- Body (top to bottom):
  1. **Prompt textarea** (`#system-prompt-text`) — monospace (JetBrains Mono), 10px, ~6 visible lines, dark inset bg
  2. **"Load from profile" label** (section header, small caps)
  3. **Auto-generated profile tags** — pills generated from user memory (`memory_core.py` Tier-B keys). Examples: "🏠 Home Control", "हि Hinglish", "🌙 Night Owl", "⚡ Tech Mode", "💻 Coding". Active tag highlighted indigo. Clicking a tag populates the textarea with a matching preset prompt.
- Footer: "Changes apply this session only unless saved as default" note + Cancel + **Save Prompt** (`#btn-modal-save-prompt`, indigo gradient button)

---

## 6. Visual Identity — Liquid Glass

All panels, cards, and modals share this treatment:

### Glass panel recipe (sidebars)
```css
background: linear-gradient(160deg, rgba(255,255,255,.07) 0%, rgba(255,255,255,.03) 100%);
backdrop-filter: blur(28px) saturate(160%);
border: 1px solid rgba(255,255,255,.12);
border-top-color: rgba(255,255,255,.22);   /* rim light */
border-left-color: rgba(255,255,255,.15);
box-shadow:
  0 32px 80px rgba(0,0,0,.75),
  inset 0 1px 0 rgba(255,255,255,.18),   /* top specular */
  inset 1px 0 0 rgba(255,255,255,.08);   /* left rim */
```

### Glass panel recipe (modals)
```css
background: linear-gradient(160deg, rgba(255,255,255,.07) 0%, rgba(255,255,255,.02) 100%);
backdrop-filter: blur(44px) saturate(180%);
border: 1px solid rgba(255,255,255,.14);
border-top-color: rgba(255,255,255,.28);
box-shadow:
  0 40px 100px rgba(0,0,0,.8),
  inset 0 1px 0 rgba(255,255,255,.22);
```

### Cards within panels
```css
background: rgba(255,255,255,.05);
border: 1px solid rgba(255,255,255,.08);
border-top-color: rgba(255,255,255,.14);
box-shadow: inset 0 1px 0 rgba(255,255,255,.10);
border-radius: 8px;
```

### Active / selected states
- Indigo glow: `box-shadow: 0 0 8px rgba(99,102,241,.15)` + indigo border
- Amber glow (lights on): `box-shadow: 0 0 10px rgba(249,168,77,.2)` + amber border

### Typography
- UI labels: Inter 400/500/600
- Monospace (context bar, prompt textarea): JetBrains Mono
- Section labels: 7.5px, 700, uppercase, letter-spacing 0.1em, `rgba(255,255,255,.25)`

### Page background
```css
background:
  radial-gradient(ellipse at 12% 20%, rgba(99,102,241,.09) 0%, transparent 55%),
  radial-gradient(ellipse at 82% 72%, rgba(16,185,129,.06) 0%, transparent 50%),
  radial-gradient(ellipse at 55% 45%, rgba(249,115,22,.05) 0%, transparent 55%),
  #080808;
```

---

## 7. Icons

Source: `UIUX/icons/` (at repo root — not served by FastAPI). Delivery method: read each SVG file and inline its `<svg>` content as a `<symbol id="ico-name">` inside a hidden `<svg style="display:none">` block at the top of `index.html`. No build step or static copy required — the symbols are embedded directly in the HTML. All icons listed in the table below use `currentColor` for stroke/fill and respond to CSS `color`. (`localis.svg` is a branded logomark with hardcoded fills — do not inline it as a themed symbol.)

| Symbol ID | Source file | Usage |
|---|---|---|
| `ico-model` | `localis-model.svg` | Sidebar rail, model section label |
| `ico-temp` | `localis-temperature.svg` | Sidebar collapsed rail |
| `ico-memory` | `localis-memory.svg` | Sidebar rail, Remember pill |
| `ico-settings` | `localis-settings.svg` | Sidebar rail, top bar |
| `ico-voice` | `localis-voice.svg` | Input bar mic button |
| `ico-newchat` | `localis-new-chat.svg` | Left sidebar New Chat button |
| `ico-web` | `localis-web-search.svg` | Web pill |
| `ico-home` | `localis-home-assistant.svg` | Lights section, Home pill, action cards |
| `ico-file` | `localis-from-file.svg` | Upload pill |
| `ico-left` | inline chevron | Left sidebar collapse toggle |
| `ico-right` | inline chevron | Left/right sidebar expand toggle |

---

## 8. Files Affected

### `app/templates/index.html`
Full structural rewrite: new three-column shell, sidebar HTML, icon `<symbol>` defs, updated element IDs per section 5.

### `app/static/css/app.css`
Full visual rewrite: liquid glass styles, new component styles, remove old bubble/config-panel CSS. Keep `.amber` / `.green` / `#voice-status-bar` rules (restyle only, preserve class names).

### `app/static/js/app.js`
- Replace `toolsUI` chip row with mode pill state (Web/Home/Upload/Remember). Pill state feeds the same `ChatRequest` fields as before — see pill-to-flag mapping in section 3.
- Do **not** touch tutorial gate logic (`frt-*` CSS class assignments at lines ~768–790, ~3052–3072).
- Wire right sidebar sections: lights (poll `/assist/light_state`), model chips (reuse existing model load/unload logic), stats (poll `/api/system-stats`), context bar (track `state.conversationHistory` char count).
- System prompt modal: update open/close trigger to new "Edit System Prompt →" button. Preserve all existing `#btn-modal-save-prompt` / `#system-prompt-text` wiring.
- Context token count: on each message append, recalculate `totalChars = conversationHistory.join('').length`, then `tokenEstimate = Math.ceil(totalChars / 4)`. Update ASCII bar and meta row.

### `app/main.py`
New endpoint:
```python
GET /api/system-stats
# Response:
{
  "cpu_pct": 34.2,          # float, psutil.cpu_percent(interval=None)
  "ram_used_gb": 11.4,      # float, psutil.virtual_memory().used / 1e9
  "ram_total_gb": 16.0,     # float
  "vram_used_gb": 8.1,      # float, pynvml or 0.0 if no GPU
  "vram_total_gb": 10.0     # float, or 0.0 if no GPU
}
```
Dependencies: add `psutil` and `pynvml` to `requirements.txt`. VRAM query must be wrapped in try/except — return `0.0` if `pynvml` is unavailable or no NVIDIA GPU is present (CPU-only machines).

### `app/assist.py`
New endpoint:
```python
GET /assist/light_state
# Response:
{
  "entity_id": "light.rishi_room_light",
  "state": "on",            # "on" | "off"
  "brightness_pct": 60,     # int 0–100, derived from HA brightness 0–255
  "color_temp_k": 3000,     # int kelvin, or null
  "rgb": [255, 200, 100],   # list[int] or null
  "last_changed": "2026-03-11T14:32:01Z"  # ISO 8601
}
```
Implementation: call the existing Home Assistant REST API (`/api/states/<entity_id>`) using the module-level `_ha_url` and `_ha_token` variables already initialised by `register_assist()` in `assist.py` (lines ~31–52). Do **not** look for these on `app.state` — they are private module globals. Return a 503 with `{"error": "HA unavailable"}` if the request fails so the sidebar can show a graceful "unavailable" state.

---

## 9. Out of Scope

- Onboarding / tutorial flow (tutorial gate JS logic must be left untouched)
- Setup wizard
- RAG upload backend (only the pill toggle replaces the old chip UI)
- Memory system backend
- Voice / STT / wakeword backend — frontend status bar indicators were implemented in the demo-path phase (commit `754b3d2`, 2026-03-11); backend is unchanged
- Mobile / responsive layout
