# Codebase Concerns

**Analysis Date:** 2026-03-14

## Tech Debt

**Bare Exception Handlers:**
- **Issue:** Three bare `except:` blocks that swallow exceptions without logging or specificity
- **Files:** `app/database.py:378`, `app/database.py:485`, `app/main.py:739`
- **Impact:** Silent failures make debugging difficult; errors are lost without context
- **Fix approach:** Replace with specific exception types (`except json.JSONDecodeError:` in database.py) and log the exception before returning None/default

**JSON Parsing in Database Memory:**
- **Issue:** Line 739 in main.py has bare `except:` when loading JSON metadata from memory
- **Files:** `app/main.py:739` (in `format_rows` function within GET /memory endpoint)
- **Impact:** If malformed JSON is in database, silently returns empty dict without warning user or logging
- **Fix approach:** Catch `json.JSONDecodeError`, log the malfunction with the key, return sensible default with warning

**Implicit Django-Like Setting Pattern:**
- **Issue:** Settings are stored/retrieved from SQLite with string keys (e.g., "tutorial_completed", "n_ctx", etc.) — no type safety
- **Files:** `app/database.py` (get_app_setting, set_app_setting), `app/main.py:476-530`
- **Impact:** Settings conversions (string to int/bool) scattered throughout main.py; easy to introduce type errors when adding new settings
- **Fix approach:** Create a Settings dataclass/pydantic model with typed fields and centralized get/set methods

---

## Known Bugs

**Missing Null Guards in Frontend Event Listener Setup:**
- **Bug:** EventSource and addEventListener calls don't check if elements exist before attaching listeners
- **Symptoms:** If HTML element IDs change or are missing, JS silently fails to attach listeners (no console error, feature just doesn't work)
- **Files:** `app/static/js/app.js:2163-2211` (RAG ingest EventSource), multiple addEventListener calls starting at line 1826
- **Trigger:** Remove an HTML element by ID from index.html, reload page — feature stops working silently
- **Workaround:** Use optional chaining in all listener setup (e.g., `els.element?.addEventListener(...)`)

**EventSource Not Cleaned Up on SSE Errors:**
- **Bug:** In `_showIngestStatus()` at line 2163, EventSource is only closed on `done|error|cancelled` states; if network disconnects silently, EventSource stays open
- **Symptoms:** Memory leak if ingest takes extremely long and network drops mid-stream
- **Files:** `app/static/js/app.js:2163-2211`
- **Trigger:** Start file upload, pull network cable after 5s, reconnect 30s later — EventSource still open
- **Workaround:** Add onerror handler that closes EventSource after max timeout or N consecutive errors

**Console.log Left in Production Code:**
- **Bug:** Multiple `console.log` statements remain in production code paths (not behind debug flag)
- **Symptoms:** Token overhead and log noise; could expose session IDs or internal state if logs are captured
- **Files:** `app/static/js/app.js:46-54` (debug enabled logs), lines 3045, 3080, 3135, 3207, 3317, 3336, 3361, 3383, 3411, 4179, 4980, 6264, 6335
- **Trigger:** Browser console shows logs like `[Logger] Debug logging enabled`, `[RAG] Added visible class`, etc. during normal operation
- **Workaround:** Gate all logging with `if (Logger.debug) { console.log(...) }` or remove entirely before production deployment

---

## Security Considerations

**Path Traversal Prevention Incomplete:**
- **Risk:** RAG upload sanitizes session_id with `_safe_session_id()` but doesn't validate file_id in download/delete endpoints
- **Files:** `app/rag.py:420-427` (sanitizes session_id), but file_id from database is used directly without validation
- **Current mitigation:** file_id is UUID4-generated on server-side, so user cannot inject; however, if database is ever compromised, attacker could craft paths
- **Recommendations:** Add explicit validation that file_id matches UUID4 format before file operations; use Path.resolve() to ensure no breakout

**XSS Protection Inconsistent:**
- **Risk:** `escapeHtml()` is defined and used in some memory display areas (line 987, 998) but not all user-controlled strings are escaped
- **Files:** `app/static/js/app.js:92-100` (escapeHtml definition), scattered usage
- **Current mitigation:** Most user input comes from chat API (controlled by backend); frontend data is trusted
- **Recommendations:** Audit all `.innerHTML` assignments (line 920, 989, 1000, 1002, 1077, 1078, 1090, 1100, 1126, 1128, 1332-1358, etc.) — ensure all dynamic user content is escaped or use `.textContent` instead

**Backend Debug Mode Exposed to Frontend:**
- **Risk:** DEBUG flag from environment is transmitted to frontend via `/app/state` endpoint (line 504 in main.py)
- **Files:** `app/main.py:504` (exposed in JSON), `app/static/js/app.js:6264` (received and used)
- **Current mitigation:** Only enables verbose logging; doesn't expose credentials
- **Recommendations:** Consider removing from frontend response or gating verbose output behind server-side check only; frontend debug mode should not reflect backend DEBUG env var

**Bare HTTP Client Calls in Tools:**
- **Risk:** `httpx` calls in `app/tools.py` don't enforce timeouts or validate SSL in all cases
- **Files:** `app/tools.py` (web search, external API calls)
- **Current mitigation:** Some endpoints have built-in timeout defaults
- **Recommendations:** Set explicit `timeout=10.0` on all httpx calls; validate HTTPS URLs; implement retry-with-backoff for flaky endpoints

---

## Performance Bottlenecks

**Moving Average Window Too Large (Wakeword Detection):**
- **Problem:** WAKEWORD_MAX_CMD defaults to 3.0s but uses adaptive silence detection; if user speaks slowly or has accent, command recording may timeout before STT finishes
- **Files:** `app/wakeword.py:76` (WAKEWORD_MAX_CMD = 3.0), lines 35-37 show troubleshooting but no auto-tuning
- **Cause:** Fixed 3.0s window works for English but may be too short for slower speech or non-English
- **Improvement path:** Add dynamic timeout based on silence duration; increase default to 5.0-8.0s if STT is the bottleneck

**Vector Embedding Cache No Eviction Policy:**
- **Problem:** `_retrieval_cache` in `app/memory_core.py` has MAX_CACHE_SIZE=50 but no LRU or TTL eviction — after 50 queries, old entries are not cleaned
- **Files:** `app/memory_core.py:42-48`
- **Cause:** Cache fills up and subsequent queries do full vector search (slower)
- **Improvement path:** Implement LRU eviction when cache exceeds MAX_CACHE_SIZE; add cache hit/miss metrics

**Database Queries Not Indexed:**
- **Problem:** RAG file searches by session_id + content_sha256 have UNIQUE INDEX, but other searches (e.g., list files by session) may scan full table
- **Files:** `app/rag.py:482` (rag_list_files), `app/database.py:254-258` (only content_sha256 indexed)
- **Cause:** Missing composite indexes on frequently filtered columns
- **Improvement path:** Add indexes on (session_id, status), (session_id, created_at) to speed up list/filter queries

**Frontend DOM Updates During RAG Ingest:**
- **Problem:** Each SSE event triggers full innerHTML replacement on ingest status panel; if ingest has 1000+ chunks, reflow is expensive
- **Files:** `app/static/js/app.js:2240-2295` (renderIngestStatus called on each event)
- **Cause:** renderIngestDetails() rebuilds full HTML instead of updating only changed fields
- **Improvement path:** Use granular DOM updates (update progress bar % only, add new file to list incrementally) instead of full innerHTML replacement

---

## Fragile Areas

**Wakeword WebSocket Auto-Reconnect with Potential Double Stream:**
- **Files:** `app/static/js/app.js:6094-6134` (wakeword reconnect logic)
- **Why fragile:** Line 6098-6100 schedules reconnect if disabled; if page refreshes while reconnect timer is pending, timer fires and opens new stream while old one may still be active
- **Safe modification:** Guard reconnect timer with flag that persists across page unload; test with forced network disconnection scenarios
- **Test coverage:** Manual test — disconnect network, wait 3s, reconnect — should not open duplicate streams

**Memory Tier-A Proposal Flow Lacks Timeout:**
- **Files:** `app/main.py:990-1010` (memory proposal flow), `app/static/js/app.js` (proposal display)
- **Why fragile:** If user never confirms/rejects Tier-A proposal, frontend keeps showing "Proposal pending" indefinitely; no server-side expiry
- **Safe modification:** Add proposal TTL (e.g., 5 minutes) in database; auto-reject stale proposals on router decision
- **Test coverage:** Start a chat, trigger Tier-A proposal, wait 6 minutes, verify proposal is cleared

**RAG Session Isolation Not Enforced in Frontend:**
- **Files:** `app/static/js/app.js:2920-3400` (ragUI module), `app/rag.py` (backend)
- **Why fragile:** Frontend sends session_id with every RAG call, but if session_id is predictable (sequential) or user tampers with it, they could access another session's files
- **Safe modification:** Validate session_id format server-side (matches current session); add session_id to RAG file paths as immutable key
- **Test coverage:** Manual test — open session A, upload file, switch to session B, try to delete file from A via raw API call — should fail

**Model Loader Initialization Race Condition:**
- **Files:** `app/main.py:174-255` (global model init), `app/wakeword.py:217-226` (preload wait with 30s timeout)
- **Why fragile:** Multiple endpoints call `load_model()` concurrently; MODEL_LOCK protects inference but initialization (model download, parsing) can race
- **Safe modification:** Add `_model_loading_lock` to serialize initial load; use double-check locking pattern
- **Test coverage:** Parallel requests to `/api/models/load` endpoint while model is still downloading — should serialize gracefully

**Bare `except:` in Memory Metadata Parsing:**
- **Files:** `app/database.py:378` (JSON parsing), `app/main.py:739` (memory format_rows)
- **Why fragile:** If meta_json in database is corrupted, exception is swallowed; user doesn't know memory is broken
- **Safe modification:** Catch JSONDecodeError, log with context (key, value), return sensible default with user-facing error message
- **Test coverage:** Insert malformed JSON directly into database, request /memory endpoint, verify error is logged and displayed

---

## Scaling Limits

**Global Memory Model Not Partitioned:**
- **Current capacity:** Single global user profile; all memory shared across all sessions
- **Limit:** If user has 10,000+ memory items, vector search becomes slow (O(n) embeddings for every query)
- **Scaling path:** Implement memory TTL (forget old facts after N months); add time-based partitioning or bloom filters for quick rejection of irrelevant facts

**Wakeword Model Preload Blocks Startup:**
- **Current capacity:** Preload happens in background thread on startup; 30s timeout
- **Limit:** If model download fails (network error), wakeword is disabled but app still starts; user has no UI feedback
- **Scaling path:** Add retry logic with exponential backoff; show spinner in UI while wakeword loads; allow user to enable/disable preload

**RAG Index Memory Usage:**
- **Current capacity:** Vector index stored in SQLite using text columns; no pagination
- **Limit:** If session has 50,000+ chunks, loading all vectors into memory for search is expensive (no batching)
- **Scaling path:** Implement chunked vector search (fetch top-k by score in SQL, then re-rank with embeddings); consider separate vector DB (Weaviate, Milvus) for high-scale

**Browser Audio Stream Lifecycle:**
- **Current capacity:** Single WebSocket for wakeword PCM + single getUserMedia for PTT
- **Limit:** If both streams are active (wakeword + manual PTT), audio context memory is tied up
- **Scaling path:** Use AudioWorklet buffer pooling to reduce GC pressure; implement audio stream reuse between wakeword and PTT

---

## Dependencies at Risk

**openwakeword / tflite-runtime Stuck on Python 3.11:**
- **Risk:** Requires separate `.venv-voice` (Python 3.11) because tflite-runtime doesn't build on Python 3.13+
- **Impact:** Maintenance burden; harder to upgrade Python runtime in the future
- **Migration plan:** Monitor openwakeword releases; switch to ONNX-only models (already supported in wakeword.py line 182) and remove tflite dependency entirely; this would allow consolidation to single Python version

**llama-cpp-python Embedded in Process:**
- **Risk:** Current architecture embeds llama.cpp inference in Python process; blocks on MODEL_LOCK during streaming
- **Impact:** Cannot upgrade model independently; memory leaks in llama-cpp could crash entire app
- **Migration plan:** (Already planned in project memory) Replace with standalone llama.cpp server (OpenAI-compatible API); this decouples model lifecycle from app lifecycle

**sentence-transformers / BGE-small for Embeddings:**
- **Risk:** Large model (~100MB) downloaded on first memory query; no fallback if download fails
- **Impact:** First memory query is slow (model download + inference); no caching across restarts
- **Migration plan:** Cache downloaded model in DATA_DIR/models/; add fallback to simpler embeddings (e.g., sparse TF-IDF) if model unavailable

---

## Missing Critical Features

**No User Consent / Privacy Framework:**
- **Problem:** Tier-A vs Tier-B memory distinction exists, but no explicit user consent flow for memory recording
- **Blocks:** GDPR/privacy compliance; users don't know what's being remembered or how to delete it
- **Recommendation:** Add `/api/memory/consent` endpoint; require explicit opt-in for Tier-B auto-learning; add deletion policy (e.g., "forget all memory older than 90 days")

**No Rate Limiting on Chat/Memory APIs:**
- **Problem:** No protection against abuse; user or compromised session can spam requests
- **Blocks:** Cannot safely expose app to untrusted network; vulnerable to DoS
- **Recommendation:** Implement sliding-window rate limiting (requests/minute by session_id); apply stricter limits to memory write endpoints

**No Audit Log for Memory Changes:**
- **Problem:** Memory writes are logged to database but no immutable audit trail for compliance
- **Blocks:** Cannot prove who changed what and when (important for privacy audits)
- **Recommendation:** Add separate immutable audit table; log all memory writes with timestamp, authority, user action, before/after diff

**No Model Versioning or Rollback:**
- **Problem:** When llama-cpp-python is updated, old models may be incompatible; no way to revert
- **Blocks:** Cannot safely update model inference library in production
- **Recommendation:** Store model library version with chat history; warn if chat was generated with different library version

---

## Test Coverage Gaps

**No Unit Tests for Memory System:**
- **What's not tested:** Memory proposal flow, bullet-list merging, authority validation, cache eviction
- **Files:** `app/memory_core.py` (entire module untested), `app/database.py` (memory operations untested)
- **Risk:** Memory corruption bugs (wrong merge, cache collision) won't be caught until production
- **Priority:** High — memory is core to app identity

**No Integration Tests for RAG Upload Pipeline:**
- **What's not tested:** End-to-end file upload → extraction → chunking → indexing; deduplication; session isolation
- **Files:** `app/rag.py`, `app/rag_processing.py`, `app/rag_vector.py` (all untested together)
- **Risk:** Silent data loss (chunks dropped during processing) or cross-session data leak
- **Priority:** High — RAG is security-sensitive

**No E2E Tests for Wakeword → STT → Assist Flow:**
- **What's not tested:** Full voice demo path (wakeword trigger → PTT recording → transcription → tool execution → response)
- **Files:** `app/wakeword.py`, `app/voice.py`, `app/main.py:chat` (workflow untested)
- **Risk:** Critical demo path could break silently (e.g., wakeword detection broken but tests still pass)
- **Priority:** High — demo is primary user experience

**No Frontend Unit Tests:**
- **What's not tested:** ragUI module, wakewordUI module, voiceStatusBar IIFE, memory display formatting
- **Files:** `app/static/js/app.js` (entire frontend untested)
- **Risk:** UI regressions (broken buttons, unresponsive modals) not caught before deployment
- **Priority:** Medium — mostly covered by manual testing, but ragUI SSE handling should have tests

---

## Architecture Decisions with Risk

**Global Memory Shared Across All Sessions:**
- **Design:** All memory (name, interests, etc.) is globally accessible, not per-session
- **Risk:** User context leaks between sessions if frontend is multi-user (unlikely but possible in future)
- **Mitigation:** Explicitly document that Localis is single-user; add validation that only one user session is active at a time

**Synchronous Model Lock for Inference:**
- **Design:** `MODEL_LOCK` (threading.Lock) serializes all inference calls
- **Risk:** One slow request blocks all other requests; no priority queue or timeout
- **Mitigation:** Add inference timeout (e.g., 5 minutes max); implement request queue with max size to fail gracefully under load

**Server-Sent Events for Long-Polling Operations:**
- **Design:** RAG ingest status is streamed via SSE; requires EventSource to stay open
- **Risk:** If client disconnects or refreshes, status is lost (frontend must refresh from database)
- **Mitigation:** Add fallback to poll `/rag/ingest_status/{session_id}` endpoint; close SSE after 10 minutes max

---

*Concerns audit: 2026-03-14*
