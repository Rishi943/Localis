# Phase 1: UI Polish - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix layout/spacing/navigation inconsistencies, visual cohesion, and branding so the app feels demo-ready and cohesive. Every panel, sidebar, and chat surface should conform to UIUX/DESIGN.md with no visible layout breaks. No new features — clarify and tighten what already exists.

</domain>

<decisions>
## Implementation Decisions

### CSS & Design System Authority

- Claude decides the aesthetic direction for what looks most polished — no strict DESIGN.md vs CSS.md contest; Claude picks what looks amazing
- Background: Strip all colored radial-gradient backgrounds → pure black `#080808` only
- Glass panels: Subtle & dark — near-black translucent panels; content is foreground, not glass
- Glass panels: Subtle directional gradient on each panel (faint linear, lighter at top-left → rim lighting feel)
- Accent: Claude chooses the accent approach (likely `--accent-primary: #5A8CFF` for interactive states; semantic amber/green for status only)
- Typography: Strict — Inter (UI) and JetBrains Mono (code) only. No other fonts.
- Interactive states: Accent blue `#5A8CFF` for focus rings; hover = subtle opacity increase only (no color change)
- Border radius: Consistent scale via CSS variables — small elements: 8px, medium panels: 12px, input pills: 100px

### Sidebar Behavior

- Left sidebar collapsed state: Icons only, no tooltips, 44px width
- Left sidebar footer: Add gear/settings icon pinned to the bottom — visible AND clickable when collapsed (44px state)
- Session history list: Currently broken (sometimes empty, sometimes garbled) — fix rendering and scrolling reliability
- Collapse animation: Smooth slide ~200ms ease (currently has transition, keep and ensure it works)
- Right sidebar: Collapses to ~20px toggle strip at right edge — always accessible, never fully disappears

### Chat Surface

- Thinking/reasoning display: Collapsed under a "Thinking..." pill by default, expandable on click — content never jumps up after think phase ends
- Message distinction: Claude decides the visual treatment; assistant label = "Localis" (not "Jarvis" — see Branding)
- No avatar/icon for assistant messages — name label only ("Localis")
- Date group separators: Messages grouped by "Today", "Yesterday", etc.
- Auto-scroll: Must be fixed — currently broken entirely (no auto-scroll during streaming)
- Input bar: Both pill shape (`border-radius: 100px`) and glass styling broken — fix to match panel aesthetic
- Action chips after assistant messages: Add Copy, Regenerate, Continue chips below each assistant response
- Token estimate: Faint muted token count in input area as user types
- Empty input when no model loaded: Disabled with "Loading model..." placeholder text
- Tool chips (Web, Home, Upload, Remember): Smaller, inlined with input bar as toggle-style buttons — not tab-style separate row

### Voice Status Bar (Wakeword)

- Current issue: Too prominent — looks like a second input row, confused with chat input
- Fix: Faint status line above input pill — very small muted text (~30% opacity), a dot + status text like "Hey Jarvis ready"
- Keep it clearly secondary — background information, not interactive affordance

### Branding

- Rename "Jarvis" → "Localis" in all UI display text (message placeholder, assistant name label, status bar text, settings modal, etc.)
- Wakeword trigger phrase stays "Hey Jarvis" for now — model update is a separate workstream
- Status bar should read: `· Hey Jarvis ready` (trigger phrase) but assistant messages labelled "Localis"

### Layout & Spacing

- Chat message column: Max-width ~720px, centered in main area — prevents ultra-wide lines on large screens
- Responsive: Layout adapts across 1280–1920px range; use `clamp()` for sidebar widths
  - 1080p baseline: left sidebar 216px, right sidebar ~260px
  - 1440p target: left sidebar ~240px, right sidebar ~300px, more breathing room in main
- Spacing consistency: All panels use a consistent padding/margin grid — fix "everything is off" feeling
- Three-column: Fixed desktop baseline, responsive within desktop range (not mobile)

### Right Sidebar

- General: Everything is cramped — give all RSB sections more internal padding and breathing room
- Section dividers: Subtle 1px separator at ~8% white opacity between LIGHTS / STATS / MODEL sections
- System stats: Compact bar + number per metric (CPU, RAM, VRAM) — mini dashboard layout, one row per stat
- Section labels: Small all-caps section headers (LIGHTS, STATS, MODEL) above each section

### Settings Modal

- Issue: Gear icon doesn't reliably open the modal — fix the click handler
- Issue: Visual design doesn't match glass system — rebuild modal styling to match glass panel recipe
- Size: Make it larger — current modal is too small
- Open behavior: Center overlay with backdrop blur over the full app
- System prompt profiles: 4 profiles shared between the settings modal and the right sidebar — they must be synchronized (changing one updates both)
  - Default
  - Custom
  - Creative (for brainstorming)
  - Planning (for implementation and task planning)

### Empty States

- New session (no messages): Centered welcome area with app name/logo + 3-4 quick-start prompt suggestions
- Suggestions disappear when the first message is sent

### Scrollbars

- Current issue: Too heavy/visible in some panels, missing in others (session list, RSB)
- Target: Ghost scrollbar — invisible by default, appears as thin 3px line on hover
- Apply consistently across all scrollable areas: chat message list, session history list, RSB panels

### Claude's Discretion

- Exact visual distinction between user and assistant message bubbles (user decided "you decide")
- Specific accent color system (single vs semantic) and how to apply it across components
- Glass blur/saturation exact values (within "subtle & dark" constraint)
- Exact directional gradient recipe for glass panels

</decisions>

<specifics>
## Specific Ideas

- "Show me visuals if possible via a localhost interactive demo" — user wants to see the result, not just accept a spec
- Screenshot shared: wakeword bar currently looks like a duplicate input row above the tool chips and input pill — this is the most jarring near-input issue
- "It's amazing on 1080p but I have to scale up to 110% on 1440p" — layout is 1080p-native, needs to work natively at 1440p
- Assistant display name is "Localis" — "Jarvis" appeared in UI because the wakeword model is pretrained on "Hey Jarvis"; these are separate concerns
- System prompt profiles need to be the same 4 entries in both settings modal and RSB — currently likely diverged or duplicated without sync

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- `app/static/css/app.css`: Existing CSS variables (`--glass-bg`, `--glass-blur`, `--glass-border`, etc.) — restructure to align with new design decisions; don't rewrite from scratch
- `app/static/js/app.js`: `voiceStatusBar` IIFE — already manages 3-state wakeword/STT/done status; restyle, don't rebuild
- `app/static/js/app.js`: `wakewordUI` and `voiceUI` IIFEs — keep logic, only touch display/styling
- `app/static/js/app.js`: `ragUI` IIFE — tool chip display lives here
- `app/templates/index.html`: SVG icon `<symbol>` defs already inlined — use existing icons before adding new ones

### Established Patterns

- IIFE module pattern for all JS features: `const ModuleName = (() => { ... })();`
- CSS variables used throughout — all visual changes should update variables, not hardcode values
- No build toolchain — plain CSS/JS, changes take effect immediately on page reload
- Glass panel recipe already applied to `.lsb` and `.right-sidebar` — extend consistently to other panels
- `app/static/js/app.js` `els` object — all DOM element references cached here; add new refs to this object

### Integration Points

- `app/templates/index.html` `#voice-status-bar` — wakeword status bar element (restyling target)
- `app/static/js/app.js` `startApp()` — entry point for UI initialization; settings modal wiring goes here
- `app/main.py` `POST /api/settings` — settings persistence endpoint already exists; system prompt profiles saved here
- `app/main.py` startup — reads and applies persisted settings at launch (accent colour, wallpaper); extend for new settings
- `.lsb-footer` in HTML — footer area of left sidebar where gear icon will be added
- Session list rendering — JS logic that builds session history list entries is the target for the reliability fix

</code_context>

<deferred>
## Deferred Ideas

- Custom wakeword phrase (user-configurable "Hey X" instead of "Hey Jarvis") — mentioned as future capability; wakeword model swap is a separate workstream
- Mobile / narrow viewport layout (< 1280px) — not in scope for this phase
- Dynamic wallpaper-aware text colour adaptation — already in v2 requirements backlog

</deferred>

---

*Phase: 01-ui-polish*
*Context gathered: 2026-03-14*
