# Stack Research — Localis New Features

**Domain:** Local AI assistant — new feature modules (LAB, News RSS, YouTube Music via HA, Financial Advisor, Post+)
**Researched:** 2026-03-14
**Confidence:** HIGH for Features 1–4 (all verified against PyPI/official docs); MEDIUM for Feature 5 (few-shot prompt strategy is well-established but no dedicated library needed)

---

## Existing Stack (Do Not Change)

FastAPI + SQLite + llama-cpp-python + ChromaDB + vanilla JS (no Node, no build toolchain).
All five features must bolt onto this stack via the `register_*()` router pattern.

---

## Feature 1: LAB — LLM Parameter Playground

### What It Is

A UI panel where users can tweak `temperature`, `top_p`, `top_k`, `repeat_penalty`, `frequency_penalty`, `presence_penalty`, `min_p`, `max_tokens`, `seed`, and (on reload) `n_ctx` and `n_gpu_layers`. Parameters persist to DB and apply to the next inference call.

### No New Python Libraries Required

llama-cpp-python already exposes every parameter needed. The `create_chat_completion()` call accepts all sampling parameters directly as keyword arguments.

**Verified parameters available in llama-cpp-python (HIGH confidence — official source):**

| Parameter | Type | Default | Range |
|-----------|------|---------|-------|
| `temperature` | float | 0.8 | 0.0 – 2.0 |
| `top_k` | int | 40 | 0 – vocab_size |
| `top_p` | float | 0.95 | 0.0 – 1.0 |
| `min_p` | float | 0.05 | 0.0 – 1.0 |
| `repeat_penalty` | float | 1.0 | 1.0 – 2.0 |
| `frequency_penalty` | float | 0.0 | -2.0 – 2.0 |
| `presence_penalty` | float | 0.0 | -2.0 – 2.0 |
| `max_tokens` | int | model max | any positive int |
| `seed` | int | -1 (random) | any int |
| `mirostat_mode` | int | 0 | 0, 1, 2 |

`n_ctx` and `n_gpu_layers` require model reload — they are constructor arguments to `Llama(...)`, not per-call. LAB must handle these as "reload required" settings distinct from hot-swappable sampling params.

### What to Add

| Layer | Addition | Purpose |
|-------|----------|---------|
| Backend | New `GET /lab/params` and `POST /lab/params` endpoints in `app/lab.py` | Read/write lab params from SQLite `app_settings` table |
| Backend | Pass lab params as kwargs to `create_chat_completion()` in generator | Apply sampling params per inference call |
| Frontend | Slider + numeric input for each param, grouped into sections | User interaction, no library needed — vanilla JS range inputs |
| Storage | Reuse existing `app_settings` SQLite table | Persist params across sessions |

### What NOT to Use

| Avoid | Why |
|-------|-----|
| Any separate "parameter server" or config management library | Total overkill — SQLite key-value in `app_settings` is sufficient |
| Gradio or Streamlit for the lab UI | Conflicts with the Midnight Glass design system and vanilla JS architecture |
| Storing params in `secret.env` | Environment variables cannot be updated at runtime from the UI |

### Installation

```bash
# No new packages — all parameters are already in llama-cpp-python
```

**Confidence:** HIGH — verified against llama-cpp-python official DeepWiki API reference (March 2026).

---

## Feature 2: News RSS Feed

### What It Is

Aggregate RSS feeds (r/LocalLLaMA + user-configured sources), cache articles in SQLite, show a filterable in-app reader. Polling background job fetches new items periodically.

### Core Technologies

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `fastfeedparser` | 0.5.9 | Parse RSS/Atom/RDF feeds | 25x faster than feedparser, actively maintained (last release March 2026), lxml-based, familiar feedparser-like API, Python 3.7+–3.14 support. Use this instead of feedparser. |
| `APScheduler` | 3.11.2 | Background periodic polling | Battle-tested, has `AsyncIOScheduler` that runs in FastAPI's uvicorn event loop without a thread pool. Last release December 2025. |
| `httpx` | already in stack | Fetch feed URLs | Already used in `app/tools.py` for HA and web search — reuse, no new dep |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `fastfeedparser` | 0.5.9 | Parse feed XML | Always — replaces feedparser for all RSS work |
| `APScheduler` | 3.x (3.11.2) | Cron/interval polling job | Use `AsyncIOScheduler` with FastAPI lifespan events to start/stop |

### RSS Feed URLs (Pre-configured Defaults)

```
https://www.reddit.com/r/LocalLLaMA.rss
https://www.reddit.com/r/MachineLearning.rss
```
Reddit's `.rss` suffix returns a valid Atom feed — no API key required.

### Storage Pattern

Store articles in a new SQLite table `rss_articles` with columns: `guid` (unique, for deduplication), `feed_url`, `title`, `link`, `published_at`, `summary`, `read` (bool), `starred` (bool). GUID-based dedup prevents re-showing seen articles on every poll.

```sql
CREATE TABLE IF NOT EXISTS rss_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    feed_url TEXT,
    title TEXT,
    link TEXT,
    published_at TEXT,
    summary TEXT,
    read INTEGER DEFAULT 0,
    starred INTEGER DEFAULT 0,
    fetched_at TEXT
);
```

### What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `feedparser` 6.0.12 | 25x slower than fastfeedparser, no lxml backend, last updated Sep 2025 but functionally superseded | `fastfeedparser` 0.5.9 |
| `celery` | Heavy Redis/RabbitMQ dependency, completely disproportionate for periodic RSS polling | `APScheduler` AsyncIOScheduler |
| `rss-parser` PyPI package | Minimal user base, no active development signal | `fastfeedparser` |
| External RSS aggregation service | Violates privacy-first principle; Localis makes no cloud calls except user-configured | Self-hosted polling |

### Installation

```bash
pip install fastfeedparser APScheduler
```

**Confidence:** HIGH — fastfeedparser version verified on PyPI (0.5.9, released 2026-03-02). APScheduler 3.11.2 verified on PyPI (released 2025-12-22). Reddit RSS URL format confirmed.

---

## Feature 3: YouTube Music via HA

### What It Is

Voice command "play [song/artist]" triggers HA's `media_player.play_media` service call with a YouTube Music video ID resolved via `ytmusicapi`.

### Architecture

```
Voice input → STT → Localis router LLM extracts intent (artist/song)
→ ytmusicapi.search() → get videoId
→ httpx POST to HA REST API /api/services/media_player/play_media
→ HA Music Assistant media_player entity plays it
```

### Core Technologies

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `ytmusicapi` | 1.11.5 | Search YouTube Music catalog, get videoId | The only maintained Python library for YT Music search. 1.11.5 released January 2026, actively maintained, Python 3.10+. No YouTube Data API key needed — uses cookie/browser auth. |
| `httpx` | already in stack | Call HA REST API | Already used for HA light control in `app/assist.py` — same pattern, no new dep |

### HA Service Call Pattern

```python
# POST http://{HA_URL}/api/services/media_player/play_media
{
    "entity_id": "media_player.your_ma_player",
    "media_content_type": "music",
    "media_content_id": "https://music.youtube.com/watch?v={videoId}"
}
```

The `media_content_id` format depends on whether the user has Music Assistant or the ytube_music_player HACS integration. The recommended setup is Music Assistant (HA official blog, May 2024) which accepts YouTube Music URLs directly.

### Authentication Note (MEDIUM confidence)

As of November 2024, Google removed OAuth token authentication from YouTube Music. Cookie-based authentication is now the primary method. `ytmusicapi` 1.11.5 supports cookie auth via a browser headers file generated by the `ytmusicapi setup` CLI. This is a one-time user setup step.

The alternative — using Music Assistant's own API (`http://{MA_IP}:8095/api/`) — avoids ytmusicapi entirely but requires Music Assistant to be installed, which is user-configured. Recommended approach: try the MA API first if the user has it; fall back to ytmusicapi + HA `play_media`.

### What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| YouTube Data API v3 | Requires Google Cloud project + API key; violates privacy-first principle for a local app | `ytmusicapi` cookie auth |
| `yt-dlp` for stream resolution | Unnecessary — HA's YouTube Music integration handles stream resolution | Let HA/MA handle playback |
| `ytmusicapi` version < 1.10 | Earlier versions used OAuth which Google disabled Nov 2024 | 1.11.5 |

### Installation

```bash
pip install ytmusicapi
# One-time user auth setup:
# ytmusicapi setup  (creates headers_auth.json)
```

**Confidence:** MEDIUM — ytmusicapi 1.11.5 verified on PyPI (released 2026-01-31). OAuth deprecation confirmed via community sources (Nov 2024). HA REST API call format confirmed via official HA developer docs. Music Assistant YouTube Music support confirmed via official MA docs but auth/PO token situation is evolving.

---

## Feature 4: Financial Advisor

### What It Is

Upload bank statement (CSV or OFX), categorise transactions automatically (keyword rules + LLM fallback), show a dashboard with pie/bar charts, and enable RAG chat over the statement data.

### Core Technologies

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pandas` | 2.x (already likely in env) | Parse CSV transactions, apply keyword categorisation rules, aggregate by category/month | Industry standard for tabular financial data; `pd.read_csv()` handles all Indian and Western bank CSV formats. |
| `ofxparse2` | 0.2.2 | Parse OFX/QFX bank statement files | Active fork of ofxparse (last updated April 2025), Python 3.10+–3.13 support. Original `ofxparse` is unmaintained (last release 2021). `ofxtools` is comprehensive but focused on investment accounts; `ofxparse2` is simpler and better for standard bank statements. |
| Chart.js | 4.5.1 (CDN) | Pie chart and bar chart for expense dashboard | Already used pattern in the Midnight Glass design system — load via `<script>` CDN, no build step. Integrates trivially with vanilla JS and FastAPI JSON endpoints. |
| ChromaDB | already in stack | RAG over transactions | Already integrated — index statement rows as text chunks, enable `/chat` queries like "how much did I spend on food last month" |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ofxparse2` | 0.2.2 | OFX file parsing | When user uploads `.ofx` or `.qfx` file |
| `pandas` | 2.x | CSV parsing + categorisation | All transaction processing |
| `python-multipart` | already in stack | File upload endpoint | Already used for RAG uploads — same pattern |

### Categorisation Strategy

Use a two-pass approach:

1. **Keyword dictionary pass** (fast, offline): Map known merchants/keywords to categories via `pd.Series.str.contains()` with a `RULES` dict. Example: `{"amazon": "Shopping", "salary": "Income", "swiggy": "Food"}`. Case-insensitive. No LLM call needed for known merchants.

2. **LLM fallback pass** (for unknowns): Batch uncategorised transactions, send to the router LLM in a single structured prompt: "Categorise these transactions. Return JSON." Use the existing `MODEL_LOCK` inference pipeline.

This avoids calling the LLM for every transaction (slow, expensive in compute) while handling edge cases gracefully.

### Chart.js Integration Pattern

```html
<!-- In index.html — no npm, no build -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"></script>
```

Backend returns aggregated JSON from `/financial/summary?session_id=X`:

```json
{"categories": {"Food": 4200, "Shopping": 8100, "Transport": 1200}}
```

Vanilla JS renders a doughnut chart. Consistent with the existing pattern where Chart.js or similar is intended for stats display (already in CLAUDE.md architecture patterns).

### What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `ofxparse` (original) | Last release May 2021, Python 2.7/3.6 classifiers, unmaintained | `ofxparse2` 0.2.2 |
| `ofxtools` | Oriented toward investment/brokerage OFX with complex type hierarchy; overkill for simple bank statement transactions | `ofxparse2` |
| Plotly / Bokeh / Matplotlib | Heavy dependencies, server-side rendering, incompatible with the Midnight Glass CSS system | Chart.js 4.5.1 via CDN |
| Separate ML categorisation model | Requires additional GPU/CPU budget; keyword rules + local LLM is sufficient and private | Keyword dict + LLM fallback |

### Installation

```bash
pip install ofxparse2 pandas
# pandas may already be installed transitively; verify with pip list
```

**Confidence:** HIGH for pandas/Chart.js (well-established). HIGH for ofxparse2 (PyPI verified, April 2025 release). MEDIUM for categorisation strategy (keyword + LLM fallback is community best practice, not a formal standard).

---

## Feature 5: Post+ — Writing Style Mimicry

### What It Is

User provides writing examples (Reddit posts, LinkedIn posts). Localis generates new posts in the user's style on a given topic. Separate profiles per platform. Soft-warns when fewer than a minimum number of examples are stored.

### No New Python Libraries Required

This feature is entirely a prompt engineering problem. The existing `llama-cpp-python` inference pipeline handles it. No fine-tuning, no separate model, no style-transfer library.

### Strategy

**Few-shot prompting with style extraction (MEDIUM confidence — academic research 2024–2025 confirms effectiveness):**

1. **Store examples** in a new SQLite table `post_plus_examples(id, platform, content, added_at)`. Platform is `reddit` or `linkedin`.

2. **Style extraction at write time**: Build a system prompt that includes 3–8 examples as few-shot demonstrations. Academic research (arxiv 2024–2025) shows zero-shot style mimicry fails (< 7% accuracy); one-shot improves dramatically; 3–8 examples reaches acceptable quality for most authors.

3. **Prompt structure:**
   ```
   System: You are a ghostwriter. Mimic the author's exact writing style, vocabulary,
   tone, sentence length, and formatting patterns. Here are examples of their writing:

   [Example 1: <content>]
   [Example 2: <content>]
   ...

   Now write a [platform] post about: [user topic]
   ```

4. **Minimum example gate**: Soft-warn (not block) when fewer than 3 examples exist. Store this threshold in config, not hardcoded.

5. **Platform-specific system prompt addendum**: Reddit posts get "casual tone, no corporate language, use markdown formatting." LinkedIn gets "professional but conversational, no hashtag spam."

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None — existing stack sufficient | — | — | — |

The only backend additions are:
- `app/post_plus.py` with `register_post_plus()` router
- SQLite table `post_plus_examples`
- Two endpoints: `POST /post_plus/example` (store example), `POST /post_plus/generate` (generate post)

### What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Fine-tuning a separate GGUF | Requires user to have training infra, hours of GPU time, separate model file management. Disproportionate for style mimicry. | Few-shot prompting in the existing inference pipeline |
| LangChain `FewShotPromptTemplate` | Adds LangChain dependency for something that is 20 lines of Python string formatting | Manual prompt construction |
| `llm-few-shot-gen` PyPI package | Thin wrapper with low adoption; adds a dependency for no real gain | Manual prompt construction |
| Storing examples in ChromaDB for retrieval | For style mimicry, you want a curated set of the user's best examples — not similarity-based retrieval. Manual curation + SQLite list is sufficient. | SQLite `post_plus_examples` table |

### Installation

```bash
# No new packages — uses existing llama-cpp-python inference pipeline
```

**Confidence:** MEDIUM — few-shot style mimicry is confirmed effective by arxiv 2024–2025 papers and community practice. Minimum example threshold of 3 is empirically supported. Specific quality varies by model capability.

---

## Master Installation Delta

All new packages to add to `requirements.txt`:

```bash
pip install fastfeedparser APScheduler ofxparse2 ytmusicapi
# pandas: verify if already present (likely pulled by another dep); add explicitly if not
pip install pandas
```

Chart.js 4.5.1 is loaded via CDN `<script>` tag — no npm install.

| Package | Version | Feature |
|---------|---------|---------|
| `fastfeedparser` | 0.5.9 | News RSS Feed |
| `APScheduler` | 3.11.2 | News RSS Feed (background polling) |
| `ofxparse2` | 0.2.2 | Financial Advisor (OFX parsing) |
| `ytmusicapi` | 1.11.5 | YouTube Music via HA |
| `pandas` | 2.x | Financial Advisor (CSV parsing) |

Zero framework migrations. All five features bolt onto the existing FastAPI + SQLite + vanilla JS stack via the `register_*()` pattern.

---

## Alternatives Considered

| Feature | Recommended | Alternative | Why Not |
|---------|-------------|-------------|---------|
| RSS parsing | `fastfeedparser` | `feedparser` 6.0.12 | feedparser is 25x slower; fastfeedparser is its spiritual successor, actively maintained |
| Background jobs | `APScheduler` AsyncIOScheduler | `celery` | Celery needs Redis/RabbitMQ broker; APScheduler is in-process and sufficient |
| OFX parsing | `ofxparse2` | `ofxtools` | ofxtools targets investment accounts with complex hierarchy; ofxparse2 is simpler for retail bank statements |
| Charting | Chart.js 4.5.1 CDN | Plotly | Plotly adds ~3MB JS and server-side rendering; Chart.js CDN is 200KB and no-build |
| Style mimicry | Few-shot prompting | Fine-tuning | Fine-tuning requires training infrastructure and hours of GPU time for minimal gain at this scale |

---

## Version Compatibility

| Package | Python Requirement | Notes |
|---------|-------------------|-------|
| `fastfeedparser` 0.5.9 | 3.7+ | Supports through 3.14 — no conflict with project's Python 3.12 |
| `APScheduler` 3.11.2 | 3.8+ | AsyncIOScheduler tested with uvicorn; use FastAPI lifespan events to start/stop |
| `ofxparse2` 0.2.2 | 3.10+ | Requires 3.10+ — project runs 3.12, OK |
| `ytmusicapi` 1.11.5 | 3.10+ | Requires 3.10+ — project runs 3.12, OK |
| `pandas` 2.x | 3.9+ | No conflict |
| `Chart.js` 4.5.1 | Browser | CDN load, no Python constraint |

All packages are compatible with the project's Python 3.12.12 runtime.

---

## Sources

- fastfeedparser PyPI page — version 0.5.9, released 2026-03-02 (HIGH confidence)
- feedparser PyPI page — version 6.0.12, released 2025-09-10 (HIGH confidence)
- APScheduler PyPI page — version 3.11.2, released 2025-12-22 (HIGH confidence)
- APScheduler docs (apscheduler.readthedocs.io/en/3.x) — AsyncIOScheduler for FastAPI (HIGH confidence)
- ytmusicapi PyPI page — version 1.11.5, released 2026-01-31 (HIGH confidence)
- ytmusicapi docs (ytmusicapi.readthedocs.io) — cookie auth, feature set (HIGH confidence)
- ofxparse2 PyPI page — version 0.2.2, released 2025-04-20 (HIGH confidence)
- ofxparse PyPI page — version 0.21, released 2021-05-31 — confirmed unmaintained (HIGH confidence)
- ofxtools docs (ofxtools.readthedocs.io) — investment focus, OFXv1/v2 support (MEDIUM confidence)
- llama-cpp-python DeepWiki API reference — sampling parameters table (HIGH confidence)
- Chart.js releases (github.com/chartjs/Chart.js) — version 4.5.1 current (HIGH confidence)
- Home Assistant developer docs (developers.home-assistant.io/docs/api/rest) — REST API format (HIGH confidence)
- Music Assistant docs (music-assistant.io/music-providers/youtube-music) — YT Music support, PO token situation (MEDIUM confidence)
- arxiv 2410.03848, arxiv 2509.14543 — few-shot style mimicry research 2024–2025 (MEDIUM confidence)
- Reddit RSS format (reddit.com/r/LocalLLaMA.rss) — confirmed working native Reddit Atom feed (HIGH confidence)
- WebSearch: HA community forums, Python Wiki RSS libraries, GitHub trending — corroborating sources (MEDIUM confidence)

---

*Stack research for: Localis new feature modules (LAB, News RSS, YouTube Music, Financial Advisor, Post+)*
*Researched: 2026-03-14*
