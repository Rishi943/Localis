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
