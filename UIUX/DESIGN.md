# Localis UI Design System

## 1. Product Identity: "Midnight Glass"

Localis uses a high-contrast "Pitch Black" foundation elevated with Apple-esque "Liquid Glass" polish. Pure blacks, thick translucency, and crisp specular highlights (rim lighting) define structure. No flat dark grays.

---

## 2. Typography

| Role | Font | Weight |
|------|------|--------|
| Primary UI | `Inter` | 400 body, 500 labels, 600 headers/active |
| Code / Terminal | `JetBrains Mono` | — |

- **No other fonts.** Remove Space Grotesk, Comic Neue, or any other imported fonts.
- `--text-primary: #ffffff`
- `--text-secondary: #a1a1aa`

---

## 3. CSS Variables (Root)

```css
:root {
    /* Base */
    --bg-app: #000000;

    /* Liquid Glass Panels */
    --bg-sidebar: rgba(10, 10, 10, 0.55);
    --bg-panel:   rgba(15, 15, 15, 0.45);

    /* Blur + Saturation */
    --glass-filter: blur(24px) saturate(180%);

    /* Rim Lighting */
    --border-subtle:    rgba(255, 255, 255, 0.15);
    --border-highlight: rgba(255, 255, 255, 0.05); /* inset box-shadow */

    /* Text */
    --text-primary:   #ffffff;
    --text-secondary: #a1a1aa;
}
```

---

## 4. Glass Panel Recipe

Apply to any major UI pane (sidebar, main chat area, settings card, modals):

```css
background: var(--bg-panel);
backdrop-filter: var(--glass-filter);
-webkit-backdrop-filter: var(--glass-filter);
border: 1px solid var(--border-subtle);
box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 var(--border-highlight);
```

**Approach:** Pure CSS (`backdrop-filter`) — no SVG refraction filters. Performance takes priority since the GPU also runs local LLM inference.

---

## 5. Component Behavior

### Themes
- Remove the multi-theme selector (`#theme-select` in `index.html` and related CSS).
- Localis uses only the Midnight Glass identity. No theme switching.

### User Messages
- High contrast bubble: solid `rgba(255, 255, 255, 0.1)` background, white text, `1px` border.

### Chat Input
- Pill shape: `border-radius: 100px`
- Slightly recessed: subtle inset shadow
- Mirrors the glass effect of surrounding panels

---

## 6. Interaction Patterns

### Hover States
- Do **not** dramatically change background colors on hover.
- Instead: slightly increase background opacity (e.g. `0.05` → `0.1`) and brighten border slightly.

---

## 7. Implementation Rules for Claude Code

1. **Read this file before any UI change.** Update it after if new components or patterns are introduced.
2. **CSS-only polish pass** — do not touch `app.js`, `updater_ui.js`, or setup wizard flows unless the task explicitly requires it.
3. **Clean `index.html`** — remove unused Google font imports, remove the theme selector dropdown from settings.
4. **Update `app.css`** — apply `backdrop-filter` rules to sidebar and main chat container. Ensure `z-index` contexts allow blur to render correctly over background elements.
5. **Never contradict this system** — flag conflicts with user before proceeding.

---

## 8. Chat UI Redesign Components (2026-03-19)

The following components were introduced in the `feature/chat-ui-redesign` branch (Tasks 1–7).

---

### Action Cluster (`.action-cluster`, `.action-group`, `.ac-btn`)

Container row rendered above the input pill, holding two button groups: **TOOLS** (web search, thinking mode, memory toggle) and **VOICE** (mic toggle, wakeword toggle).

- `.action-cluster`: flex row, `gap: 8px`, `padding: 0 4px 6px`
- `.action-group`: flex row with a label above; label is `9px`, `letter-spacing: 0.08em`, `--text-secondary`
- `.ac-btn`: `32px × 32px` circle; default background transparent, hover `rgba(255,255,255,0.06)`, active (`.active`) accent tint + accent border
- **Active color variants by type:**
  - `web`, `think`, `remember` → accent blue (`--accent-primary`)
  - voice mic → green (`#22c55e`)
  - wakeword → amber (`#f59e0b`)

---

### Input Pill (`.input-pill`)

Capsule-shaped input row that replaces the old flat textarea.

- `border-radius: 100px`
- `min-height: 52px`
- Glass panel recipe (see §4): `background: var(--bg-panel)`, `backdrop-filter: var(--glass-filter)`, `border: 1px solid var(--border-subtle)`
- Contains `#prompt` (auto-growing textarea, `resize: none`) and `#send-btn` (circular accent button, `36px`, `border-radius: 50%`)
- Subtle inset shadow to appear slightly recessed

---

### LSB Collapsed State (`.lsb.collapsed`, `#left-rail`)

The left sidebar transitions between expanded (260px) and a collapsed icon strip (64px).

- Width transition: `260px ↔ 64px`, driven by `.collapsed` class via `cubic-bezier(0.4, 0, 0.2, 1)` transition
- `.lsb-body` wrapper holds all expanded content; hidden when collapsed via `opacity: 0`, `pointer-events: none`
- `#left-rail`: absolutely positioned strip shown only when `.collapsed`; contains brand icon, expand button, nav icons (top), and settings icon (bottom footer)
- Rail icons: `44px × 44px` hit target, `28px × 28px` visible icon; hover `rgba(255,255,255,0.08)`, active/current-section tint

---

### RSB Rail (updated — 4 icon spec)

The right sidebar navigation rail contains exactly **4 icons**. Their behaviors differ:

| Icon ID | Label | Behavior |
|---|---|---|
| `#ico-home` | HA Lights | Expand RSB + snap-scroll to lights section |
| `#ico-memory` | Model | Expand RSB + snap-scroll to model section |
| `#ico-finance` | Finance | Open full-screen finance overlay |
| `#icon-notes` | Notes | Open full-screen notes overlay |

Do not add a fifth icon to the RSB rail without updating this table.

---

### Chat Bubbles (`.msg-row`, `.msg-avatar`, `.msg-bubble`)

Messages use asymmetric corner radii to indicate directionality.

**User messages** (`.msg-row.user`):
- Right-aligned row
- `.msg-bubble`: `border-radius: 18px 18px 4px 18px`; background `rgba(255,255,255,0.08)`; `border: 1px solid rgba(255,255,255,0.12)`
- Avatar: 32px circle, blue-to-indigo gradient (`#3b82f6 → #6366f1`), user initial

**AI messages** (`.msg-row.ai`):
- Left-aligned row
- `.msg-bubble`: `border-radius: 4px 18px 18px 18px`; glass panel recipe (see §4)
- Avatar: 32px circle, `rgba(255,255,255,0.08)` background with `1px` border; contains "J" initial

**Message actions** (`.msg-actions`):
- Appear on `.msg-row:hover` via `opacity: 0 → 1` transition
- Three icon buttons: copy, regenerate (AI only), thumbs-up
- `24px × 24px`, same glass hover recipe as `.ac-btn`

---

### Tool Pill + Detail Card (`.tool-pill-wrap`, `.tool-pill`, `.tool-detail`)

Collapsible component rendered inside AI messages to show tool invocation results.

**Pill** (`.tool-pill`):
- Inline flex row: colored status dot + monospace tool label + status text + chevron
- Dot color by tool type: green (`#22c55e`) = HA/home, blue (`#3b82f6`) = memory, amber (`#f59e0b`) = web search
- Click toggles `.expanded` on the `.tool-pill-wrap`

**Detail card** (`.tool-detail`):
- `max-height: 0 → 300px` transition; `overflow: hidden`; revealed when `.tool-pill-wrap.expanded`
- Three layout variants:
  1. **Light control** — entity name + current state badge (on/off/color)
  2. **Memory write** — `key: value` rows in monospace
  3. **Web search** — up to 3 result rows (favicon + title + domain)

---

### Thinking Block (`.thinking-block`, `.thinking-header`, `.thinking-body`)

Collapsible block for model reasoning/think-mode output.

- Collapsed by default; header visible always
- `.thinking-header`: memory icon SVG + "Reasoning" label + duration hint (e.g. "3.2s") + chevron
- Chevron rotates `0° → 180°` on expand (CSS `transition: transform 0.2s`)
- `.thinking-body`: `max-height: 0 → 600px`, `overflow-y: auto`; content is italic, `--text-secondary` color
- Toggled via global JS helper `toggleThinking(btn)` which toggles `.expanded` on the parent `.thinking-block`
- RSB polish (Task 8): model section chevron uses the same rotation pattern; system prompt presets use a **2×2 chip grid** layout
