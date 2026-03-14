# Architecture

**Analysis Date:** 2026-03-14

## Pattern Overview

**Overall:** FastAPI-based streaming chat application with a Router-Generator pattern for inference and a two-tier memory system for persistent user identity and learned facts.

**Key Characteristics:**
- Thread-safe GPU model access via global `MODEL_LOCK` protecting llama-cpp-python instance
- Streaming response delivery using Server-Sent Events (SSE) for real-time token output
- Pluggable tool/feature system via router registration pattern (`register_*` functions)
- Two-tier persistent memory: Tier-A (core identity requiring explicit confirmation) and Tier-B (auto-learned preferences)
- Session-scoped chat history with global user memory
- Multi-modal input: text, voice (STT via faster-whisper), wakeword detection (openwakeword), and text-to-speech (Piper)

## Layers

**Presentation Layer (Frontend):**
- Purpose: Interactive chat UI, model controls, memory management, voice interface
- Location: `app/static/js/app.js` (6346 lines), `app/templates/index.html`, `app/static/css/app.css`
- Contains: React-like modules (ragUI, FRT, RPG, voiceUI, wakewordUI), event listeners, streaming response handlers, Midnight Glass visual system
- Depends on: REST API (`/chat`, `/settings`, `/voice`, `/models`, etc.), WebSocket connections (`/voice/wakeword/ws`)
- Used by: Browser, directly invoked by user actions

**API Route Layer (FastAPI):**
- Purpose: Request validation, session management, route dispatching to lower layers
- Location: `app/main.py` (1907 lines) - contains all main app routes
- Contains: HTTP endpoints for chat, model loading, settings, memory, sessions, voice, debug
- Depends on: Database layer, memory core, tools, voice/wakeword modules, assist service
- Used by: Frontend (HTTP/SSE), voice endpoints, tutorial system

**Inference Pipeline (Router-Generator):**
- Purpose: Coordinate tool execution and LLM response generation
- Location: `app/main.py` lines 893-1488 (chat_endpoint function)
- Pattern:
  1. **Router Phase** (under MODEL_LOCK): LLM analyzes message, decides which tools to invoke
  2. **Tool Execution Phase**: Runs 0-3 tools in parallel (web search, RAG retrieve, memory write/retrieve)
  3. **Context Building Phase**: Assembles system prompt with Tier-A identity + tool results
  4. **Generator Phase** (under MODEL_LOCK): LLM streams response token-by-token
- Constraints: Maximum 3 concurrent tools, hard cap to prevent resource exhaustion

**Memory System (Two-Tier):**
- Purpose: Persistent user identity and learned facts
- Location: `app/memory_core.py` (792 lines)
- Tier-A (Core Identity): preferred_name, location, timezone, language_preferences
  - Requires explicit user confirmation (`/confirm key=value` command)
  - Authority: `user_explicit` only
  - Stored in `user_memory` and `user_memory_meta` tables
- Tier-B (Extended): interests, projects, goals, habits_routines, media_preferences, traits, misc
  - Can be written by assistant (authority: `assistant_inferred`)
  - Bullet-list merging for collection-type keys (deduplication + append)
  - Stored in `user_memory` and `vector_memory` (for embeddings)
- Global scope: Memory is shared across all sessions, not session-isolated
- Retrieval: Hybrid (vector similarity via BAAI/bge-small-en-v1.5 + keyword scoring)

**Database Layer (SQLite):**
- Purpose: Persistent storage of chat history, memory, app settings, RAG metadata
- Location: `app/database.py` (961 lines)
- Key tables:
  - `sessions` (id, title, created_at) - chat session metadata
  - `messages` (id, session_id, role, content, tokens, timestamp) - chat history
  - `user_memory` (key, value, category, last_updated) - memory KV store
  - `user_memory_meta` (key, meta_json, created_at, last_updated) - memory authority/intent
  - `vector_memory` (id, content, embedding, meta_json) - vector embeddings for memory retrieval
  - `memory_events` (ts, session_id, event, payload_json) - audit log for memory changes
  - `app_settings` (key, value) - persistent UI/inference settings
  - `rag_files` (session_id, file_id, file_name, status, created_at) - RAG document metadata
- Path: Configurable via `LOCALIS_DB_PATH` or `LOCALIS_DATA_DIR`, defaults to `~/.local/share/localis/chat_history.db`
- Schema health checks on startup (legacy db detection + automatic backup)

**Feature Modules (Router Pattern):**
- Purpose: Encapsulate domain-specific functionality
- Pattern: Each feature defines `register_feature(app, config)` function that stores config on `app.state` and includes a FastAPI `APIRouter`
- Modules:
  - `app/setup_wizard.py` - First-run model download and tutorial (registers `register_setup_wizard`)
  - `app/updater.py` - Git-based self-update mechanism (registers `register_updater`)
  - `app/rag.py` - Document upload and vector search (registers `register_rag`)
  - `app/assist.py` - Home Assistant smart-home control (registers `register_assist`)
  - `app/voice.py` - STT (faster-whisper) and TTS (Piper) (registers `register_voice`)
  - `app/wakeword.py` - Wakeword detection via WebSocket (registers `register_wakeword`)

**Tool System:**
- Purpose: External integrations (web search, RAG retrieval, memory operations)
- Location: `app/tools.py` (implements web_search), `app/rag_vector.py` (implements RAG vector retrieval)
- Tools invoked from `chat_endpoint`:
  - `web_search` - Multi-provider support (Brave, Tavily, custom endpoint)
  - `rag_retrieve` - Vector search over session-scoped uploaded documents
  - `memory_retrieve` - Hybrid vector + keyword search of learned facts
  - `memory_write` - Tier-B writes (auto-learned preferences)
- Execution: Concurrent async, hard-capped at 3 tools per request

## Data Flow

**Standard Chat Request:**

1. User sends message via UI (HTTP POST `/chat`)
2. Route handler validates `ChatRequest` pydantic model
3. User message logged to `messages` table (role: "user")
4. Auto-title session if new (first message becomes title)
5. Parse slash commands (`/remember`, `/confirm`, `/forget`, `/reject`)
   - If matched: Execute command, return response, skip to step 12
6. If not slash command, collect tool actions:
   - Frontend-specified tools (from UI controls)
   - Auto-inject memory retrieval if memory_mode="auto"
   - Auto-inject RAG retrieval if session has indexed files
7. Execute tools in parallel (max 3):
   - Web search: Call `tools.web_search()` with provider chain
   - RAG retrieve: Call `rag_vector.query()`, build context block
   - Memory retrieve: Call `memory_core.retrieve()` via tool interface
   - Memory write: Queue proposal for later (in generator phase)
8. Build conversation history (last 20 messages from DB)
9. Assemble system prompt:
   - Core identity (Tier-A) from memory
   - Tool results formatted as system messages
   - Optional: explicit `system_prompt` from request
10. **Acquire MODEL_LOCK** → Router phase:
    - Call llama-cpp-python with router prompt (analyzes which tools to invoke in full pipeline)
    - Parse JSON response to finalize tool list
11. **Release MODEL_LOCK** → Execute any router-initiated tools
12. **Re-acquire MODEL_LOCK** → Generator phase:
    - Call llama-cpp-python with final system prompt + tool results
    - Stream tokens via SSE (each token in `data: {...}` line)
    - Collect full response text in-memory
13. **Release MODEL_LOCK**
14. Store assistant response to `messages` table
15. If memory proposals were generated, log events to `memory_events`
16. Return final SSE event with `"stop": true`

**Assist Mode (Home Assistant Control) - Bypass:**
- Assist requests skip entire chat pipeline
- Takes "light banda kar" → Calls FunctionGemma-based routing
- Executes Home Assistant service call (light on/off, brightness, color)
- Returns tool result directly
- Still logs user message and response to `messages` table

**State Management:**
- **Global State**:
  - `current_model` (Llama instance), `current_model_name` (str)
  - `MODEL_LOCK` (threading.Lock) - protects concurrent access
  - `tutorial_prompts` (Dict[session_id, prompt_text]) - in-memory store
- **Session State**:
  - Session ID (UUID) passed in every request
  - Session title auto-derived from first message
  - Chat history per session stored in DB
- **User State** (Global):
  - Memory (Tier-A + Tier-B) global across all sessions
  - App settings (model preference, context size, accent color, etc.) global

## Key Abstractions

**Message:**
- Purpose: Represents a single message in conversation
- Schema: `{id, session_id, role ("user"|"assistant"), content, tokens, timestamp}`
- Pattern: Immutable; stored to DB immediately after generation

**MemoryItem:**
- Purpose: Represents a single piece of learned knowledge
- Fields: `content`, `intent` (identity|preference|task_state|factual_knowledge|reference_note), `authority` (user_explicit|user_implicit|assistant_inferred|imported), `source` (user|assistant|agent|import), `created_at`, `key`, `origin_session_id`
- Examples: `{content: "I work in Berlin", intent: "identity", authority: "user_explicit", source: "user"}`

**MemoryProposal:**
- Purpose: Represents an unapproved memory write (Tier-A changes)
- Fields: `content`, `intent`, `authority`, `source`, `target` ("tier_a"|"tier_b"), `confidence`, `reason`, `should_write`, `key`, `valid_until`
- Lifecycle: Proposed by router → Returned to frontend → User confirms/rejects via `/confirm` or `/reject`

**ChatRequest:**
- Purpose: Main chat endpoint request schema
- Fields: `message`, `session_id`, `system_prompt`, `temperature`, `max_tokens`, `top_p`, `web_search_mode` ("off"|"enabled"|"auto"), `memory_mode` ("off"|"auto"), `think_mode`, `tool_actions` (array), `assist_mode`, `input_mode` ("text"|"voice")

**ToolResult:**
- Purpose: Result of executing a single tool
- Format: `{tool_name, message (system message to inject), success, error}`
- Pattern: Merged into system prompt for LLM context

**RAG File Metadata:**
- Purpose: Track uploaded documents and processing status
- Fields: `session_id`, `file_id` (uuid), `file_name`, `status` ("uploaded"|"extracted"|"chunked"|"indexed"), `mime_type`, `size_bytes`, `chunk_count`, `created_at`, `updated_at`
- Lifecycle: Upload → Extract → Chunk → Index (progressive)

## Entry Points

**HTTP Server Entry:**
- Location: `app/main.py` (module-level)
- Triggers: `uvicorn app.main:app --reload` (development) or production ASGI server
- Responsibilities:
  - Set up logging (file + console)
  - Resolve DATA_DIR and load secret.env
  - Seed static assets from bundled resources
  - Initialize database schema
  - Preload embedding model (warm up)
  - Register feature modules
  - Startup model auto-load (if tutorial completed)

**Chat Endpoint:**
- Route: `POST /chat`
- Handler: `chat_endpoint(req: ChatRequest)` at line 893
- Triggers: User sends message from UI, voice STT transcript, or voice command parsing
- Responsibilities: Full chat pipeline (tools → inference → stream → persist)

**Tutorial Endpoint:**
- Route: `POST /tutorial/chat`
- Handler: `tutorial_chat_endpoint()` at line 1491
- Triggers: First-run questionnaire flow
- Responsibilities: Stateless RPG questionnaire generation, system prompt assembly for demo

**Voice WebSocket Entry:**
- Route: `GET /voice/wakeword/ws`
- Handler: `wakeword_ws_endpoint()` in `app/wakeword.py`
- Triggers: Browser WebSocket connection
- Responsibilities: Receive PCM audio stream, run openwakeword model, emit detection events

**Tutorial Commit Entry:**
- Route: `POST /tutorial/commit`
- Handler: `tutorial_commit_endpoint()` at line 1617
- Triggers: User completes tutorial questionnaire
- Responsibilities: Atomic transaction (Tier-A identity + Tier-B facts + app settings → DB)

## Error Handling

**Strategy:** Defensive error recovery with detailed logging; frontend receives SSE error payloads for graceful UI state transitions.

**Patterns:**

**Model Loading Errors:**
- File not found: `HTTPException(status_code=404, detail="Model file not found")`
- GPU unavailable: Warning logged, inference degrades to CPU automatically
- Load failure: `HTTPException(status_code=500)`, detailed error logged

**Chat Stream Errors:**
- Model not loaded: `HTTPException(status_code=503, detail="No model loaded...")`
- Tool execution failure: Tool error captured, context injected as `[TOOL RESULT: {tool_name}]\nError: ...`
- Database write failure: Logged, request succeeds but message not persisted (best-effort)

**Database Errors:**
- Schema mismatch detected on startup: Legacy DB automatically backed up with timestamp, fresh schema created
- Connection failures: Retried with `_connect_db()` helper
- Constraint violations: Logged, operations skipped

**Validation Errors:**
- Pydantic model validation fails: `HTTPException(status_code=422)` with validation details
- Unsafe user inputs: HTML-escaped in frontend (`escapeHtml()` utility)
- Path traversal: RAG file paths sanitized with `_safe_session_id()`

**Voice Errors:**
- Whisper model loading fails: Logged as warning, transcription endpoint returns 500
- Piper not found in PATH: Warning logged at startup, TTS endpoint returns 503 if accessed
- WebSocket disconnect: Clean reconnection; browser-side retry logic handles resumption

## Cross-Cutting Concerns

**Logging:**
- Framework: Python `logging` module
- Levels: DEBUG (controlled by LOCALIS_DEBUG env var), INFO, WARNING, ERROR
- Output: Console + rotating file (`~/.local/share/localis/logs/localis.log`)
- Format: `[LEVEL] ComponentName message` (stdout), `timestamp [LEVEL] message` (file)
- Silenced libs: httpx, sentence-transformers, chromadb, uvicorn.access (set to WARNING)
- Token logging: Disabled in production (LOCALIS_DEBUG=0)

**Validation:**
- Request level: Pydantic models (`ChatRequest`, `TutorialChatRequest`, etc.)
- Memory keys: `database._safe_key()` normalizes; allowlist checked (`ALLOWED_AUTO_MEMORY_KEYS`, `TIER_A_KEYS`)
- File paths: `_safe_session_id()` in RAG module sanitizes session IDs to prevent directory traversal
- Model context: UI limits context size to 8192 max; LLM enforces at load time

**Authentication:**
- Status: None (localhost-only by default)
- LAN access: Optional `LOCALIS_VOICE_KEY` for voice endpoints (injected into UI at runtime)
- Voice endpoint check: `_verify_voice_key()` validates optional key header

**Concurrency:**
- Model access: Global `MODEL_LOCK` (threading.Lock) protects all llama-cpp-python calls (router + generator)
- Tool execution: Asyncio concurrency, hard-capped at 3 tools per request
- Database: SQLite (file-level locking; no concurrent writer protection required at app level)
- Independent locks for voice modules: `VOICE_STT_LOCK`, `VOICE_TTS_LOCK`, `ASSIST_MODEL_LOCK` (never interact with MODEL_LOCK)
- RAG job state: `_jobs_lock` (threading.Lock) protects `_jobs` and `_ingest_jobs` dicts

**Resource Management:**
- Memory: Old model unloaded via `del current_model; gc.collect()` before loading new one
- Database connections: Created per-operation via `_connect_db()`, closed explicitly
- File handles: UploadFile objects auto-closed by FastAPI; custom files closed with context managers
- WebSocket: Browser auto-closes on disconnect; server-side cleanup via try/finally blocks

**Streaming Pattern (SSE):**
- Token output: Each token wrapped as `data: {"content": token, "stop": false}\n\n`
- Final event: `data: {"content": "", "stop": true}\n\n`
- On error: `data: {"error": "message", "stop": true}\n\n`
- Frontend SSE handler: `readSSE(response, onData)` utility parses multi-line JSON payloads

**Frontend State Machine:**
- Chat UI: Message submission → Loading state → Stream handler → Render markdown on completion
- Voice: Idle → Listening (wakeword active) → Processing → Response streaming
- Settings: Modal opened → Form state updated → POST /api/settings → Persist to DB

---

*Architecture analysis: 2026-03-14*
