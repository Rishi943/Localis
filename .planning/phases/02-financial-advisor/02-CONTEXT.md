# Phase 2: Financial Advisor - Context

**Gathered:** 2026-03-15 (updated 2026-03-18 — V2 redesign)
**Status:** Ready for replanning

<domain>
## Phase Boundary

A Finance tab accessible from the RSB icon strip. Full 3-column dashboard layout matching the Notion "Simple Finance Tracker" reference: left sidebar (Budgets), center-top (line chart + donut chart via Chart.js), center-bottom (Expenses list grouped by month), top bar (period selector, refresh button, upload). Users upload CIBC CSV bank statements; Localis parses, categorises, deduplicates, and visualises. LLM used only in (1) the goal-setting onboarding conversation and (2) the Chat tab Q&A. All numbers from SQL. No cloud, no data leaves device.

This is a V2 rework of existing Phase 2 code. The V1 implementation (plans 02-01 through 02-06) is replaced wholesale. All fin_* tables are dropped and recreated.

</domain>

<decisions>
## Implementation Decisions

### Data model migration
- Drop and recreate all fin_* tables (`fin_transactions`, `fin_uploads`, `fin_goals`) on V2 deploy
- No migration of existing data — user re-uploads CSVs after upgrade
- `period_label` column removed entirely from both `fin_transactions` and `fin_uploads`
- `account_label` replaces it (e.g. "CIBC Chequing", "CIBC Credit")
- Periods are derived from transaction `date` column via SQL: `strftime('%Y-%m', date)` — never user-entered
- `fin_goals` also dropped and recreated — user re-runs onboarding to set budgets for all 8 categories

### Deduplication
- Unique constraint on `(date, description, amount, account_label)` — prevents re-upload duplicates per account
- Upload response: `"✓ 34 new transactions added to CIBC Chequing (53 skipped — already imported)"` — single skip count, not broken down by reason

### Schema — fin_transactions
```
date TEXT, description TEXT, amount REAL,
type TEXT (debit/credit), category TEXT,
account_label TEXT, account_type TEXT (chequing/credit_card),
upload_id TEXT
```
Unique constraint: `(date, description, amount, account_label)`

### Schema — fin_uploads
```
id TEXT, filename TEXT, account_label TEXT,
account_type TEXT, uploaded_at TEXT, row_count INTEGER
```
(No period_label)

### Schema — fin_goals
Unchanged structure. Budgets JSON dict now covers all 8 categories.

### Categories — 8 total
```
Food, Transport, Shopping, Utilities, Entertainment,
Health & Fitness, Government & Fees, Other
```
Specific keywords to add (beyond existing rules):
- `Health & Fitness`: ANYTIME FITNESS, GYM, FITNESS, PHARMA, SHOPPERS DRUG, REXALL, LIFE LABS, PHYSIO, DENTAL, OPTICIAN, MEDICAL
- `Government & Fees`: IMMIGRATION, IRCC, SERVICE CANADA, CRA, MINISTRY, GOVERNMENT, MUNICIPAL, COURT, CUSTOMS, CBSA, LICENCE, LICENSE FEE, PASSPORT

### Categorisation logic
- Case-insensitive substring match: `keyword.lower() in description.lower()`
- Replaces previous exact-match logic — catches e.g. "ANYTIME FITNESS TORONTO" with keyword "ANYTIME FITNESS"
- Only runs on new uploads — no background re-categorisation on startup
- Rules hardcoded in `CATEGORY_RULES` dict in `finance.py` — not user-editable in V1

### Budget sidebar (left column)
- Pulled from `fin_goals` (most recent row), `budgets` JSON field
- Shows all 8 category rows always
- For categories with a budget set: name, budget amount, spent this period, progress bar (green <85%, amber 85–100%, red >100%)
- For categories with NO budget set: show row with actual spend + dashed/ghost progress bar + "No budget" label — still shows spend
- Read-only — edit only via onboarding reset (no edit button on dashboard)
- Progress bar and spend amounts respond to period selector

### Period selector
- `GET /finance/periods` returns: `SELECT DISTINCT strftime('%Y-%m', date) FROM fin_transactions ORDER BY 1 ASC`
- Frontend formats YYYY-MM as "Mar 2026" (strftime/Date formatting)
- Dropdown: "All time" first, then months in chronological order (oldest → newest)
- Period selector change → re-fetch summary + transactions
- All panels in sync: charts, budget sidebar, expenses list all reflect selected period

### Chart.js sourcing
- Bundle locally: `app/static/js/chart.umd.min.js` (Chart.js v4 UMD build)
- Served from `/static` — works offline, no external requests
- Added as `<script src="/static/js/chart.umd.min.js">` in index.html before Finance tab scripts

### Charts — line + donut
- Layout: always side-by-side in the center-top area (line chart left, donut right); no responsive stacking
- **Line chart**: `type: 'line'`, smooth curve, single dataset, x-axis = distinct months with transaction data (no gap-filling for months with no data), y-axis = total debit per month
- **Donut chart**: `type: 'doughnut'`, shows spending by category for selected period, legend on right or below
- Colors: `--accent-primary` (#5A8CFF) as base + 7 opacity/hue-shifted tints in the same blue family — not Chart.js defaults
- Both charts respond to period selector
- **Empty state**: empty canvas with ghost placeholder text "No data yet — upload a statement to get started" — charts stay in layout

### Upload modal / panel
- Account label text input (required) — e.g. "CIBC Chequing"
- Datalist suggestions for existing account labels (fetch from `GET /finance/accounts`)
- Account type (chequing / credit_card) auto-detected from column count — no user input
- Success feedback: `"✓ 34 new transactions added to CIBC Chequing (53 skipped — already imported)"`

### Expenses list (center-bottom)
- Transactions grouped by month, newest first
- Each month group: collapsible (▼/▶), header shows month name + total debit for that month
- Transaction row: Date (formatted "Mar 17, 2026"), Description, Source tag, Category tag, Amount
- Source tag: "Bank" (green pill) for chequing, "Credit Card" (blue pill) for credit_card
- Category tag: muted pill
- Debits: normal amount text; Credits: green +$X.XX inline in same list (NOT a separate section)
- Credits and debits shown together — credits visually distinct by green colour and + prefix

### Refresh button
- Always visible in Finance tab header
- On click: re-calls `/finance/summary`, `/finance/transactions`, `/finance/periods` with current period selection
- Brief spinner on button while fetching

### LLM Chat tab
- Unchanged from V1 CONTEXT.md decisions — reuses existing chat rendering pipeline
- SQL-generated context injected into system prompt (aggregates only, no raw CSV)
- Uses main inference model

### Onboarding
- Fresh conversational flow — NOT the FRT/Narrator state machine
- Asks monthly budget for all 8 categories (user can enter 0 or skip any)
- Skippable — shows empty state with "Set up your goals" prompt
- Re-runnable via "Reset goals" button

### Claude's Discretion
- Exact keyword lists for Health & Fitness and Government & Fees beyond the spec examples above
- SQL queries for each dashboard metric
- Finance onboarding conversation script (questions, responses, branching for 8 categories)
- System prompt template for finance chat context injection
- Panel open/close animation
- Chart.js configuration details (padding, gridlines, font size, tooltip formatting)
- Exact CSS for ghost progress bar (no-budget state)

</decisions>

<specifics>
## Specific Ideas

- "All numbers are SQL" — hard constraint, not negotiable
- Notion "Simple Finance Tracker" is the reference for the 3-column layout
- ANYTIME FITNESS → "Health & Fitness", IMMIGRATION CANADA → "Government & Fees", SOULED STORE → "Shopping" (not "Other") — these are the key test cases for expanded categorisation
- Drop-recreate is acceptable — this is a personal daily-driver app, re-uploading CSVs is trivial
- The spec's verification list is the acceptance criteria: upload with account label, dedup skip count, period selector from DB, month-grouped expenses, green credits, source tags, budget sidebar colours, refresh button, ANYTIME FITNESS/IMMIGRATION/SOULED STORE categorised correctly, line + donut charts render

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### V2 spec (primary)
- `docs/superpowers/plans/2026-03-11-palette-and-settings.md` — check if relevant for chart colour tokens
- `UIUX/DESIGN.md` — Midnight Glass design system; all new UI must conform (glass recipe, CSS vars, font stack)

### Existing implementation to replace
- `.planning/phases/02-financial-advisor/02-RESEARCH.md` — original research (partially superseded by V2 spec)
- `.planning/phases/02-financial-advisor/02-UI-SPEC.md` — original UI spec (superseded by 3-column layout in this context)

### No external specs
Requirements are fully captured in decisions above and the inline layout spec in the V2 design document provided by the user.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/finance.py` — existing module; `CATEGORY_RULES`, `PAYMENT_KEYWORDS`, `normalize_date()`, `parse_chequing_rows()`, `parse_credit_rows()` all reusable with updates
- `register_finance()` pattern — keep, update endpoints
- `app_settings` + `get_app_setting`/`set_app_setting` — onboarding completion flag (`fin_onboarding_done`)
- Chat rendering pipeline — Chat tab reuses `buildMessageHTML`, `appendMessage`
- Glass CSS variables — `--bg-panel`, `--glass-filter`, `--border-highlight`, `--accent-primary: #5A8CFF`
- Ghost scrollbar CSS — transaction list reuses existing recipe
- `financeUI` IIFE in `app.js` — existing module; needs significant rework for V2 layout

### Established Patterns
- IIFE module in `app.js`: `const financeUI = (function() { ... })()`
- `init_db()` in `database.py`: add `fin_*` tables with `CREATE TABLE IF NOT EXISTS` (but V2 drops first)
- FastAPI router: prefix `/finance`, tag `finance`
- All DB ops use `database.DB_NAME`
- SSE pattern available for upload progress if needed

### Integration Points
- RSB icon strip: existing Finance SVG `<symbol>` + click → `financeUI.open()`
- `startApp()`: call `financeUI.init()` unconditionally (no model needed for dashboard)
- `init_db()` in `database.py`: DROP + CREATE fin_* tables on V2 startup
- Chart.js: add `<script src="/static/js/chart.umd.min.js">` to index.html

### V1 Plans to Replace
Plans 02-01 through 02-06 are superseded. Plan 02-07 (verification checkpoint) remains relevant.
The V2 replan should produce new plans covering:
1. Schema migration (drop + recreate fin_* tables, update `init_db()`)
2. Backend: account_label model, expanded categories, improved dedup, new endpoints (`/finance/periods`, `/finance/accounts`)
3. Chart.js integration (bundle file, HTML script tag)
4. Frontend: 3-column layout HTML + CSS
5. Frontend: JS wiring — period selector, refresh, upload modal, expenses list renderer
6. Frontend: Chart.js chart renderers (line + donut)
7. Verification checkpoint

</code_context>

<deferred>
## Deferred Ideas

- OFX / QFX format support — v2
- PDF bank statement support — v2
- User re-categorisation of individual transactions — v2
- Export dashboard as PDF/image — post-v1
- Multiple bank accounts tracked separately with account-level switching — post-v1
- Month-over-month % change trend — post-v1
- Income/Cashflow chart tabs — removed from V2 spec (no income data modelled); revisit if income tracking added
- User-extensible category rules (in-app keyword editor) — v2
- A/B preset system for model parameters — v2

</deferred>

---

*Phase: 02-financial-advisor*
*Context gathered: 2026-03-15 (updated 2026-03-18 — V2 redesign spec captured)*
