# Phase 2: Financial Advisor - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

A Finance panel accessible from a new RSB icon that opens a full-panel view with two tabs: **Dashboard** (glass CSS charts from deterministic SQL) and **Chat** (LLM conversation with SQL-injected context). Users upload CIBC bank statement CSVs (chequing and credit card), parsed into SQLite. LLM is used in two places only: (1) a fresh purpose-built goal-setting onboarding conversation (chat-style, skippable), and (2) natural language Q&A in the Chat tab. No cloud, no RAG over raw CSV, no LLM categorisation. All numbers come from SQL.

</domain>

<decisions>
## Implementation Decisions

### Entry point and layout
- New icon in the RSB icon strip opens the Finance panel
- Full-panel overlay replacing the main chat area (similar to how tutorial overlays work)
- Two tabs: **Dashboard** (default after onboarding) and **Chat**
- Finance panel accessible without model loaded (dashboard is SQL-only)

### Onboarding flow
- Fresh purpose-built conversational onboarding — NOT the FRT/Narrator state machine (build new)
- Same concept as FRT: chat-style, step by step, warm reflective tone
- **Skippable** — user can skip straight to Dashboard at any time; skip shows empty state with subtle "Set up your goals" prompt
- **Re-runnable** — "Reset goals" button in the panel resets `fin_goals` and re-triggers onboarding
- Questions (conversational, not a form):
  1. Primary goal: save money / invest / mix / not sure yet
  2. Life events they're planning toward: vacation, wedding, house, emergency fund, none/unsure
  3. Monthly budget per category (Food, Transport, Shopping, Utilities, Entertainment, Other) — can enter 0 or skip any
  4. Time horizon: months or years (open-ended)
- Tone: reflective, not prescriptive — "What are you saving toward?" not "Set your savings target"
- Completion flag stored in `app_settings` as `fin_onboarding_done`
- All answers persist to `fin_goals` SQLite table

### CSV formats (exact, no headers in either file)

**CIBC Chequing — 4 columns (tab/comma separated, all amounts positive):**
`Date | Description | Debit | Credit`
- Debit = money out (spending)
- Credit = money in (income, transfers, refunds)
- Empty Debit cell = Credit transaction; empty Credit cell = Debit transaction

**CIBC Credit Card — 5 columns (no headers, all amounts positive):**
`Date | Description (includes foreign currency inline e.g. "399.00 INR @ .015187") | CAD Amount | [blank] | Masked card number`
- All non-blank rows are spending (debits); credits = card payments (show in list, don't count toward spend totals)
- Foreign currency transactions: parse CAD amount only (column 3); foreign details are in description text

### CSV upload and parsing
- Both CIBC chequing and CIBC credit card CSVs supported
- Parser detects account type by column count (4 = chequing, 5 = credit card)
- User specifies the time period label on upload (free text: "Jan 2026", "Q1 2026", etc.)
- Parsed into `fin_transactions` with: date, description, amount, type (debit/credit), category, period_label, account_type
- Multiple uploads accumulate; each tagged with period label
- Deduplication: unique constraint on (date, description, amount, account_type) — silent skip on duplicate

### Categorisation
- Predefined fixed categories: Food, Transport, Shopping, Utilities, Entertainment, Other
- Fully deterministic keyword/merchant matching on Description field — no LLM
- Rules in a Python dict (Claude's discretion on exact merchant list — aim for common Canadian merchants)
- Unmatched → "Other"
- No user re-categorisation in v1

### Dashboard — period selector and charts
- **Period selector dropdown** at top of Dashboard: options are all uploaded period labels + "All time"
- Default view: "All time" aggregate OR latest upload if only one exists
- Pure CSS charts — no Chart.js or external library
- Midnight Glass aesthetic: `backdrop-filter`, glass bars, `--accent-primary: #5A8CFF`, CSS transitions on bar fill, subtle accent glow on dominant bar
- Chart types:
  1. **Category breakdown** — horizontal glass bars, % and $ per category (debits only)
  2. **Budget vs actual** — side-by-side bars per category; if no budgets set, show actual only with a subtle "Set budgets →" ghost button
  3. **Monthly trend** — sparkline-style horizontal bars, one per uploaded period
  4. **Transaction list** — scrollable table, ghost scrollbar, alternating glass row tint; all transactions shown (debits AND credits); credits labeled green with "↑ Credit" tag

### No-budget state
- If user skipped onboarding (no budgets in `fin_goals`): budget vs actual chart shows actual spend bars only
- Subtle ghost prompt: "Set up your goals to see budget tracking →" — not a blocking banner

### LLM Chat tab
- Reuses existing chat rendering pipeline (`buildMessageHTML`, `appendMessage`)
- LLM receives SQL-generated context injected into system prompt:
  - Spend per category for the period the user mentioned (SQL filtered by period)
  - Top 5 merchants for that period
  - Budget vs actual summary (if goals set)
  - User's stated goals and life events from `fin_goals`
- Raw transaction rows NOT passed to LLM — aggregated summaries only
- When user mentions a specific period ("last month", "January"), SQL context is filtered to that period
- Uses main inference model

### Data model
- `fin_goals` — goal_type, life_events (JSON array), budgets (JSON dict: category→amount), horizon, created_at
- `fin_transactions` — date, description, amount, type (debit/credit), category, period_label, account_type, upload_id
- `fin_uploads` — id, filename, period_label, account_type, uploaded_at, row_count

### Claude's Discretion
- Exact Python keyword/merchant rules for categorisation
- SQL queries for each dashboard metric
- Finance onboarding conversation script (questions, responses, branching)
- System prompt template for finance chat context injection
- Panel open/close animation (slide or fade)
- Exact deduplication behaviour on overlapping period uploads

</decisions>

<specifics>
## Specific Ideas

- "All numbers are SQL" is a hard constraint — not negotiable
- Onboarding is a fresh build, not FRT reuse — more polished, purpose-built for finance
- Dashboard feels like a premium personal finance app — glass bars with glow, not plain tables
- Credit card CSV: foreign currency details are in the description string — only parse the CAD amount column
- Chequing: detect debit vs credit by which of the two amount columns is non-empty
- User confirmed they have both chequing and credit card CSVs to share for testing

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app_settings` + `get_app_setting`/`set_app_setting` — onboarding completion flag (`fin_onboarding_done`)
- `register_*()` pattern — `app/finance.py` with `register_finance(app, db_path)`
- Chat rendering pipeline — Chat tab reuses `buildMessageHTML`, `appendMessage`
- Glass CSS variables — Dashboard uses `--bg-panel`, `--glass-filter`, `--border-highlight`, `--accent-primary` directly
- Ghost scrollbar CSS — transaction list reuses existing ghost scrollbar recipe
- SSE pattern — reuse for CSV parse progress feedback if file is large

### Established Patterns
- IIFE module in `app.js`: `const financeUI = (function() { ... })()`
- `init_db()` in `database.py`: add `fin_*` tables with `CREATE TABLE IF NOT EXISTS`
- FastAPI router: prefix `/finance`, tag `finance`
- All DB ops use `database.DB_NAME`

### Integration Points
- RSB icon strip: new Finance SVG `<symbol>` + click → `financeUI.open()`
- `startApp()`: call `financeUI.init()` unconditionally (no model needed for dashboard)
- `init_db()`: create `fin_transactions`, `fin_goals`, `fin_uploads`
- Main content area: Finance panel overlays `#chat-zone` (z-index or display toggle)

</code_context>

<deferred>
## Deferred Ideas

- OFX / QFX format support — v2
- PDF bank statement support — v2
- User re-categorisation of individual transactions — v2
- Export dashboard as PDF/image — post-v1
- Multiple bank accounts tracked separately — post-v1
- Month-over-month % change trend — post-v1

</deferred>

---

*Phase: 02-financial-advisor*
*Context gathered: 2026-03-15 (updated after assumptions review)*
