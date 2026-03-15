# Architecture Research

**Domain:** Feature integration into existing FastAPI + SQLite + llama-cpp-python + vanilla JS app
**Researched:** 2026-03-14
**Confidence:** HIGH (based directly on codebase analysis — no speculation required)

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser (Vanilla JS)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  labUI   │ │  newsUI  │ │ musicUI  │ │  finUI   │ │ postUI   │  │
│  │  (NEW)   │ │  (NEW)   │ │  (NEW)   │ │  (NEW)   │ │  (NEW)   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │             │         │
│  ┌────▼────────────▼────────────▼────────────▼─────────────▼──────┐ │
│  │       Existing IIFE Modules: ragUI, voiceUI, wakewordUI, etc.   │ │
│  └──────────────────────────────────┬──────────────────────────────┘ │
└─────────────────────────────────────│──────────────────────────────┘
                                       │ HTTP / SSE / WebSocket
┌─────────────────────────────────────▼──────────────────────────────┐
│                      FastAPI Route Layer (main.py)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │/lab      │ │/news     │ │/assist   │ │/finance  │ │/postplus │  │
│  │(NEW)     │ │(NEW)     │ │(EXTEND)  │ │(NEW)     │ │(NEW)     │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
└───────│────────────│────────────│────────────│─────────────│────────┘
        │            │            │            │             │
┌───────▼────────────▼────────────▼────────────▼─────────────▼────────┐
│            Feature Modules (register_* pattern, separate files)       │
│  lab.py    news.py      assist.py (ext)   finance.py   postplus.py   │
└───────────────────────────────────┬──────────────────────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────────────────────┐
│                      SQLite (database.py / init_db)                   │
│  sessions  messages  user_memory  app_settings  rag_files  + 5 NEW   │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | New or Existing |
|-----------|----------------|-----------------|
| `app/lab.py` | LAB parameter store, param injection into ChatRequest | NEW |
| `app/news.py` | RSS poll scheduler, feed item storage, filtered read | NEW |
| `app/assist.py` | HA service calls — extend with media_player entity | EXTEND |
| `app/finance.py` | CSV/OFX parser, chart data API, finance RAG pipeline | NEW |
| `app/postplus.py` | Example storage, style context builder, platform profiles | NEW |
| `app/database.py` | Schema for all new tables via `init_db()` additions | EXTEND |
| `app/main.py` | ChatRequest extension for LAB params, register_* calls | EXTEND |
| `app.js` | New IIFE modules: labUI, newsUI, musicUI, finUI, postUI | EXTEND |

---

## Feature-by-Feature Integration Analysis

### Feature 1: LAB — LLM Parameter Playground

**What it touches:**
- `ChatRequest` pydantic model in `main.py` — add `lab_temperature`, `lab_top_p`, `lab_repeat_penalty`, `lab_max_tokens` optional fields (all default to None, meaning "use saved preset")
- `app/lab.py` (NEW) — stores named presets in `app_settings` table as JSON blobs; exposes `GET /lab/presets`, `POST /lab/presets`, `DELETE /lab/presets/{name}`
- `app.js` — `labUI` IIFE: param sliders, preset picker, live preview of what values will be used
- `app.css` — LAB panel styles (right sidebar or modal)

**Data flow:**

```
User adjusts slider in labUI
    → labUI stores params in local state (not persisted yet)
    → On send, labUI merges params into ChatRequest payload
    → chat_endpoint() receives non-None lab_* fields
    → Generator phase passes them to llama-cpp-python create_chat_completion()
    → No MODEL_LOCK change needed — params are per-call arguments
```

**New SQLite tables:**

None required. Presets stored as JSON in existing `app_settings` table:
```
key = "lab_preset_<name>", value = '{"temperature":0.7,"top_p":0.9,...}'
key = "lab_default_preset", value = "balanced"
```

**Component boundary:**

LAB is purely a parameter-injection concern. It never touches MODEL_LOCK, never runs inference itself, and has no background workers. The backend module is thin — mostly CRUD on `app_settings`. The real complexity is the frontend slider UI.

**Frontend module:**

```javascript
const labUI = (() => {
    let _params = { temperature: null, top_p: null, repeat_penalty: null };
    return {
        init() { /* bind sliders, load saved preset */ },
        getParams() { return { ...active params or nulls } },
        // labUI.getParams() called by api.chat() before building payload
    };
})();
```

**Integration point with existing code:**

`api.chat()` function in `app.js` already constructs the `ChatRequest` payload. Add `...labUI.getParams()` spread into that payload construction. No changes to the chat pipeline logic.

**Dependencies:** None — can be built completely independently.

---

### Feature 2: News RSS Feed

**What it touches:**
- `app/news.py` (NEW) — background polling task (asyncio periodic or APScheduler), RSS parsing (feedparser), storage in new `rss_items` table
- `app/database.py` — add `rss_feeds` and `rss_items` tables
- `app.js` — `newsUI` IIFE: feed list, item reader panel, source manager
- `app.css` — news reader panel (right sidebar section or dedicated view)
- `app/main.py` — `register_news(app, ...)` call

**Data flow:**

```
Startup → news.py starts background asyncio.Task polling each feed URL every N minutes
    → feedparser.parse(url) → new items filtered by guid/link dedup
    → Items written to rss_items table (feed_id, guid, title, url, summary, published_at, read)
    → Frontend polls GET /news/items?feed=all&unread=true every 60s (or on tab focus)
    → newsUI renders item list; click → GET /news/items/{id}/content or open URL
    → Mark-read via PATCH /news/items/{id}/read
```

**New SQLite tables:**

```sql
CREATE TABLE IF NOT EXISTS rss_feeds (
    id TEXT PRIMARY KEY,          -- uuid
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    last_polled_at TEXT,
    poll_interval_minutes INTEGER NOT NULL DEFAULT 30,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rss_items (
    id TEXT PRIMARY KEY,          -- uuid
    feed_id TEXT NOT NULL REFERENCES rss_feeds(id),
    guid TEXT NOT NULL,
    title TEXT,
    url TEXT,
    summary TEXT,                 -- truncated description from RSS
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    read INTEGER NOT NULL DEFAULT 0,
    UNIQUE(feed_id, guid)
);
```

**Background task pattern:**

Use `asyncio.create_task()` inside `@app.on_event("startup")` in `main.py`. The task runs an infinite loop with `asyncio.sleep(poll_interval)`. This is the same pattern to use as the wakeword preload — lightweight, no new process needed.

```python
# In register_news(app, ...)
@app.on_event("startup")
async def _start_news_poller():
    asyncio.create_task(_poll_loop())
```

**Privacy note:** RSS polling is an outbound network call. Document in `secret.env` that feeds must be user-configured. Default: no feeds configured, poller is a no-op.

**Dependencies:** None — fully independent of all other new features. Only depends on existing `database.py` and adding feedparser to `requirements.txt`.

---

### Feature 3: YouTube Music via HA

**What it touches:**
- `app/assist.py` (EXTEND) — add `media_player` entity config and service calls (`media_player.play_media`, `media_player.media_pause`, etc.)
- `app/wakeword.py` / voice pipeline — "play [song]" intent routing (if voice-triggered)
- `app.js` — `musicUI` IIFE in right sidebar: now-playing display, play/pause/skip controls
- Right sidebar (`#right-sidebar`) — add music control card below lights card

**Data flow:**

```
Voice: "Hey Jarvis, play Bohemian Rhapsody"
    → wakeword detects → STT transcribes → assist_mode=true chat request
    → assist.py route_intent() → classifies as media_player action
    → ha_call_service("media_player", "play_media", {
          entity_id: _media_entity,
          media_content_id: "Bohemian Rhapsody",
          media_content_type: "music"
      })
    → HA executes via YouTube Music integration

Manual: User clicks play button in right sidebar
    → musicUI → POST /assist/media/play { query: "..." }
    → Same HA service call path
```

**New SQLite tables:** None. Config stored in `app_settings`:
```
key = "ha_media_entity", value = "media_player.bedroom_speaker"
```

**Component boundary:**

This is an extension of `assist.py`. The existing `_ha_configured()` check pattern should be replicated: `_media_configured()` checks `_media_entity` is set. Add `_media_entity: str = ""` module-level variable populated by `register_assist()` from new env var `LOCALIS_HA_MEDIA_ENTITY`.

New endpoints in `assist.py`:
- `POST /assist/media/play` — play by search query
- `POST /assist/media/pause`
- `POST /assist/media/next`
- `GET /assist/media/state` — returns current playing track (for now-playing card)

**Intent routing:** The existing FunctionGemma-based router in `assist.py` needs a new tool definition for `media_player.play_media`. This is the most complex part: the LLM must extract "what to play" from free-form commands. Consider adding a simple regex pre-pass for "play {query}" before invoking FunctionGemma to avoid inference overhead on obvious commands.

**Dependencies:** Depends on existing HA integration working (lights). Build after lights are stable (already done). Independent of all other new features.

---

### Feature 4: Financial Advisor

**What it touches:**
- `app/finance.py` (NEW) — CSV/OFX parser, category classifier, chart data endpoints, finance-specific RAG pipeline
- `app/database.py` — new tables for transactions and categories
- `app/rag.py` / `app/rag_vector.py` — finance uses the existing RAG pipeline but with a dedicated ChromaDB collection
- `app.js` — `finUI` IIFE: upload panel, expense dashboard (pie charts via Chart.js or Canvas API), chat-over-statements interface
- `app/templates/index.html` — finance view (either a new panel or dedicated route)
- `app.css` — dashboard layout, chart containers

**Data flow:**

```
Upload: User drops CSV/OFX file
    → POST /finance/upload (multipart)
    → finance.py parses file: extract rows as transactions
    → Transactions stored in finance_transactions table
    → Each transaction also chunked + embedded into ChromaDB collection "finance_{session_id}"
    → SSE progress stream back to finUI (reuse ingest_status pattern from rag.py)

Dashboard: User opens finance view
    → GET /finance/summary?session_id=X
    → Returns aggregated totals by category as JSON
    → finUI renders pie chart using native Canvas API (no Chart.js dependency — avoid bloat)

Chat: User asks "what did I spend on food last month?"
    → Normal /chat request with tool_actions: ["rag_retrieve"]
    → RAG retrieve targets finance collection
    → LLM answers from transaction context
```

**New SQLite tables:**

```sql
CREATE TABLE IF NOT EXISTS finance_transactions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    file_id TEXT NOT NULL,        -- links to rag_files
    date TEXT,
    description TEXT,
    amount REAL,
    currency TEXT DEFAULT 'INR',
    category TEXT,                -- auto-classified
    raw_row TEXT,                 -- original CSV row as JSON
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_uploads (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_type TEXT NOT NULL,      -- 'csv' | 'ofx'
    row_count INTEGER,
    date_range_start TEXT,
    date_range_end TEXT,
    status TEXT NOT NULL,         -- 'parsing' | 'ready' | 'error'
    created_at TEXT NOT NULL
);
```

**Categorization approach:** Use a keyword-match ruleset first (fast, zero-inference cost). Fallback to asking the LLM for ambiguous transactions. Store category in the `finance_transactions` table. Do not run LLM on every transaction — it would exhaust MODEL_LOCK.

**Chart rendering:** Use native Canvas API with a lightweight hand-rolled pie chart (30 lines of JS). Avoid adding Chart.js — unnecessary dependency for one chart type.

**OFX parsing:** `ofxparse` library (pure Python, lightweight). Add to `requirements.txt`. CSV is stdlib `csv` module.

**Dependencies:** Depends on the existing RAG pipeline (ChromaDB + `rag_vector.py`). The finance module reuses that infrastructure with a named collection. Build after RAG is confirmed stable (it is already shipped).

---

### Feature 5: Post+ (Reddit + LinkedIn Style)

**What it touches:**
- `app/postplus.py` (NEW) — example CRUD, style context assembler, platform profile endpoints
- `app/database.py` — new tables for examples and platform profiles
- `app.js` — `postUI` IIFE: example manager, platform selector, style preview, post editor
- `app/main.py` — `register_postplus()` call; Post+ injects style context into system prompt via a new tool or via direct chat request field
- `app.css` — post editor panel, example chips

**Data flow:**

```
Setup: User pastes example posts
    → POST /postplus/examples { platform: "reddit", content: "...", subreddit: "..." }
    → Stored in postplus_examples table
    → Count checked: if < 3 for platform, soft-warn returned in response
    → Example embedded into vector_memory for semantic retrieval (or separate collection)

Generation: User asks "write a reddit post about X"
    → chat_endpoint() detects postplus_mode flag in ChatRequest
    → OR LLM router recognizes intent and calls postplus_retrieve tool
    → postplus.py assembles style context: top-3 similar examples by embedding similarity
    → Style context injected into system prompt: "Match the following writing style:\n{examples}"
    → Generator produces post in user's style
```

**New SQLite tables:**

```sql
CREATE TABLE IF NOT EXISTS postplus_examples (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,       -- 'reddit' | 'linkedin'
    subreddit TEXT,               -- Reddit only, nullable
    content TEXT NOT NULL,
    embedding BLOB,               -- bge-small embedding for similarity search
    char_count INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS postplus_profiles (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL UNIQUE,
    display_name TEXT,
    tone_notes TEXT,              -- user-written style notes (optional)
    min_examples INTEGER NOT NULL DEFAULT 3,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
```

**Style context retrieval:** Embed the user's prompt with bge-small-en-v1.5 (already loaded via `memory_core.get_embedder()`). Cosine-compare against stored example embeddings. Return top-3. This reuses the existing embedding infrastructure — no new model required.

**Soft-warn mechanism:** `GET /postplus/examples/count?platform=reddit` returns `{ count: 2, min: 3, warning: true }`. Frontend `postUI` shows a yellow banner if `warning: true`. Feature remains fully functional — this is advisory only.

**Platform profiles are independent:** Reddit and LinkedIn get separate example pools. The platform selector in `postUI` switches which pool is used for retrieval and which profile's tone notes are injected.

**Dependencies:** Depends on `memory_core.get_embedder()` being available (existing — always warm after startup). Independent of all other new features. Can be built in any order.

---

## Recommended Project Structure (New Files)

```
app/
├── lab.py              # NEW — parameter preset CRUD
├── news.py             # NEW — RSS polling, feed + item endpoints
├── finance.py          # NEW — CSV/OFX parser, transaction storage, chart data
├── postplus.py         # NEW — example storage, style context builder
├── assist.py           # EXTEND — add media_player entity + endpoints
├── database.py         # EXTEND — new tables for all 5 features
└── main.py             # EXTEND — register_* calls, ChatRequest fields for LAB

app/static/js/
└── app.js              # EXTEND — 5 new IIFE modules appended to existing file
```

No new separate JS files are needed. Following the existing pattern (monolithic `app.js` with IIFE submodules) keeps the structure consistent and avoids build toolchain for a single HTML file app.

---

## Architectural Patterns

### Pattern 1: Register-and-Forget Module Registration

**What:** Each new feature lives in its own `app/feature.py` file. A `register_feature(app, ...)` function stores config on `app.state` and calls `app.include_router(router)`. Called once in `main.py` at startup.

**When to use:** All 5 new features. This is the established pattern — do not deviate.

**Example:**
```python
# app/news.py
router = APIRouter(prefix="/news", tags=["news"])
_db_path: str = ""

def register_news(app, data_dir: Path):
    global _db_path
    _db_path = str(data_dir / "chat_history.db")
    app.include_router(router)

    @app.on_event("startup")
    async def _start_poller():
        asyncio.create_task(_poll_loop())
```

### Pattern 2: IIFE Frontend Modules

**What:** Each new UI feature is a JavaScript IIFE assigned to a PascalCase constant. It exposes `init()`, optional `refresh()`, and feature-specific methods. All DOM references go through the shared `els` object.

**When to use:** All 5 new frontend modules.

**Example:**
```javascript
const labUI = (() => {
    let _presets = [];
    let _active = { temperature: null, top_p: null };

    async function _loadPresets() { /* GET /lab/presets */ }

    return {
        init() { _loadPresets(); /* bind sliders */ },
        getParams() { return { ..._active }; },
        // Called by api.chat() before request construction
    };
})();
```

### Pattern 3: SSE for Long-Running Operations

**What:** File parsing and indexing operations stream progress via SSE using the established `ingest_status` event schema. Finance upload reuses the exact same event schema as RAG ingest.

**When to use:** Finance CSV/OFX upload + indexing pipeline. Do not invent a new event schema — reuse the existing one defined in CLAUDE.md.

**Example event sequence:**
```
data: {"event_type":"ingest_status","state":"running","phase":"upload","message":"Parsing transactions...",...}
data: {"event_type":"ingest_status","state":"running","phase":"index","message":"Embedding 342 transactions...",...}
data: {"event_type":"ingest_status","state":"done","phase":"index","message":"Ready — 342 transactions indexed",...}
```

### Pattern 4: Tool Injection into Chat Pipeline

**What:** Features that need to augment LLM context (Post+ style examples) inject their data as a tool result. The chat pipeline already has a `ToolResult` abstraction — use it rather than building a separate inference path.

**When to use:** Post+ style context injection. Finance RAG already handled by existing `rag_retrieve` tool pointing at a named collection.

**Data flow:**
```
ChatRequest with postplus_mode=true
    → chat_endpoint() detects flag
    → Calls postplus.retrieve_style_context(user_msg)
    → Returns ToolResult: { tool_name: "postplus", message: "Style context:\n{examples}" }
    → Merged into system prompt by existing context builder
    → Generator sees style examples without any pipeline changes
```

---

## Data Flow Summary

### LAB Parameter Flow

```
labUI slider change → local state
labUI.getParams() called in api.chat() → merged into ChatRequest payload
chat_endpoint() receives lab_temperature etc. → passed to create_chat_completion()
```

### News Feed Flow

```
Startup asyncio.Task → feedparser.parse(url) every N min
    → INSERT INTO rss_items (dedup by guid)
Frontend polls GET /news/items → newsUI renders list
User reads item → PATCH /news/items/{id}/read
```

### YouTube Music Flow

```
Voice command → STT → assist_mode=true → assist.py intent router
    → media_player.play_media service call to HA
    → HA executes via YouTube Music integration
GET /assist/media/state → musicUI polls every 10s for now-playing display
```

### Finance Flow

```
CSV upload → POST /finance/upload → parse transactions → store in DB
    → embed all transactions → ChromaDB "finance_{session_id}"
    → SSE progress stream
GET /finance/summary → aggregated by category → Canvas pie chart
/chat with rag_retrieve → finance collection → LLM answers queries
```

### Post+ Flow

```
User pastes example → POST /postplus/examples → store + embed
Chat with postplus_mode → retrieve top-3 similar examples by embedding
    → inject as tool result → Generator sees style context
```

---

## Build Order Implications

### Dependency Graph

```
LAB       ─ no deps ──────────────────────────────── build anytime
News      ─ no deps ──────────────────────────────── build anytime
Music     ─ depends on existing HA (lights) ───────── build after Phase 1 confirm
Finance   ─ depends on existing RAG pipeline ──────── build after Music or in parallel
Post+     ─ depends on embedder (always ready) ──────  build anytime
```

### Recommended Phase Order

**Phase 1 — LAB** (lowest risk, highest frequency of use)
- Pure frontend + thin backend CRUD
- No background workers, no MODEL_LOCK changes, no new tables
- Unblocks the student use case immediately

**Phase 2 — Post+** (no external dependencies)
- New tables + embedding retrieval + new UI panel
- All dependencies already exist in codebase
- Validates the "tool injection" pattern before Finance uses similar approach

**Phase 3 — News RSS** (independent but has background worker risk)
- Background asyncio polling is new territory in this codebase
- Build after simpler features to have more confidence in the system
- feedparser is well-understood; the async polling loop needs careful error handling

**Phase 4 — YouTube Music** (extends HA, must validate first)
- Validate lights integration is stable before adding media_player
- Intent routing for "play X" is the primary complexity
- Right sidebar now-playing card is purely additive

**Phase 5 — Financial Advisor** (most complex, most dependencies)
- CSV/OFX parsing + finance RAG pipeline + chart rendering + new tables
- Should be last — benefits from all patterns being proven in earlier phases
- The RAG reuse pattern will be confirmed stable by Phase 2 Post+

---

## Integration Points with Existing Code

| Feature | Existing File Modified | Why |
|---------|----------------------|-----|
| LAB | `app/main.py` — `ChatRequest` | Add optional lab_* fields |
| LAB | `app/main.py` — generator call | Pass lab_* to create_chat_completion() |
| LAB | `app/static/js/app.js` — `api.chat()` | Spread labUI.getParams() into payload |
| Music | `app/assist.py` | Add media_player entity + service call endpoints |
| Music | `app/static/js/app.js` — right sidebar | Add now-playing card + controls |
| Finance | `app/rag_vector.py` | Accept named collection parameter |
| Finance | `app/database.py` | Add 2 new tables |
| Post+ | `app/main.py` — `ChatRequest` | Add optional postplus_mode field |
| Post+ | `app/main.py` — `chat_endpoint()` | Detect flag, call postplus context retriever |
| Post+ | `app/database.py` | Add 2 new tables |
| News | `app/main.py` — `_startup()` | Start asyncio polling task |
| All | `app/database.py` — `init_db()` | New CREATE TABLE statements |
| All | `app/static/css/app.css` | New component styles |
| All | `app/templates/index.html` | New DOM elements for each module |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Finance Running LLM on Every Transaction

**What people do:** Call the main LLM via MODEL_LOCK to categorize each of 500 transactions at upload time.

**Why it's wrong:** MODEL_LOCK is a global mutex. 500 sequential LLM calls would block the entire app (no chat responses, no voice) for potentially minutes.

**Do this instead:** Keyword-match categorization ruleset first. Only call LLM for ambiguous transactions, batched (5-10 per call) and deferred to a background task — or let the user trigger categorization manually.

### Anti-Pattern 2: Post+ Building a Separate Embedding Model

**What people do:** Load a second sentence-transformers model specifically for Post+ example similarity.

**Why it's wrong:** `memory_core.get_embedder()` already loads bge-small-en-v1.5 at startup and keeps it warm. A second model wastes ~200MB RAM and startup time.

**Do this instead:** Import and call `memory_core.embed_text(content)` for all Post+ embedding operations. The embedder is not behind MODEL_LOCK — it runs on CPU concurrently with inference.

### Anti-Pattern 3: News Polling Blocking the Event Loop

**What people do:** Use `requests.get()` (synchronous) inside the asyncio poll loop.

**Why it's wrong:** Blocks the entire FastAPI event loop during network I/O. Every request stalls while a slow RSS feed is fetched.

**Do this instead:** Use `httpx.AsyncClient` (already in requirements) for async HTTP. feedparser's `parse()` is sync — wrap with `asyncio.to_thread()` or use `feedparser.http.get()` then parse the response. The existing `tools.py` already uses httpx async for web search — follow that pattern.

### Anti-Pattern 4: Adding New Global Locks for Feature Modules

**What people do:** Create `NEWS_LOCK`, `FINANCE_LOCK`, `POSTPLUS_LOCK` for thread safety "just in case."

**Why it's wrong:** SQLite handles concurrent reads. The only reason `MODEL_LOCK` exists is that llama-cpp-python instances are not thread-safe. New features do not call llama-cpp-python directly — they use the existing chat endpoint.

**Do this instead:** Use no locks for DB operations (SQLite handles it). Use `_jobs_lock` pattern from `rag.py` only if you have in-memory job state dictionaries that are mutated across async contexts (finance upload jobs qualify; RSS polling does not).

### Anti-Pattern 5: Separate HTML Pages for New Features

**What people do:** Add `/lab`, `/finance`, `/postplus` as separate FastAPI routes returning new HTML pages.

**Why it's wrong:** Localis is a single-page app. All UI lives in `index.html`. Separate pages break the session model, the model lock, and the voice status bar state.

**Do this instead:** All new feature UIs are panels/sections within the existing `index.html` — controlled by CSS `display:none/block` toggled by JS modules. This is how ragUI, voiceUI, and wakewordUI already work.

---

## Scaling Considerations

This app is single-user local software. "Scaling" means handling feature growth without making the codebase unmaintainable.

| Scale | Architecture Adjustment |
|-------|------------------------|
| 5 new features | Current monolith (`main.py`) is at 1907 lines. Each register_* call adds ~0 lines to main.py. Feature logic lives in feature modules — this is sustainable. |
| app.js at 6346 lines + 5 new modules | At ~1000 lines per new IIFE module, app.js approaches 11K lines. Consider splitting into `lab.js`, `news.js` etc. at that point — but this is cosmetic, not functional. |
| RSS feed volume | SQLite UNIQUE constraint on `(feed_id, guid)` prevents duplicates. Add index on `rss_items(feed_id, read, published_at)` for efficient unread queries. |
| Finance transaction volume | Index `finance_transactions(session_id, date, category)` at creation time. No pagination needed for typical bank statement sizes (< 10K rows). |

---

## Sources

All analysis derived directly from codebase inspection:
- `/home/rishi/Rishi/AI/Localis/app/main.py` (1907 lines) — inference pipeline, registration pattern
- `/home/rishi/Rishi/AI/Localis/app/database.py` (961 lines) — schema, migration pattern
- `/home/rishi/Rishi/AI/Localis/app/rag.py` — SSE ingest pattern, job state management
- `/home/rishi/Rishi/AI/Localis/app/assist.py` — HA integration pattern, module-level state
- `/home/rishi/Rishi/AI/Localis/app/memory_core.py` — embedder reuse, retrieval patterns
- `/home/rishi/Rishi/AI/Localis/.planning/codebase/ARCHITECTURE.md` — architecture analysis
- `/home/rishi/Rishi/AI/Localis/.planning/codebase/STRUCTURE.md` — file structure analysis
- `/home/rishi/Rishi/AI/Localis/.planning/PROJECT.md` — feature requirements

Confidence: HIGH — no external sources required; all decisions grounded in existing code patterns.

---

*Architecture research for: Localis feature integration (LAB, News, Music, Finance, Post+)*
*Researched: 2026-03-14*
