# External Integrations

**Analysis Date:** 2026-03-14

## APIs & External Services

**Web Search:**
- Brave Search - Real-time web search integration
  - SDK/Client: `httpx` async HTTP client
  - Endpoint: `https://api.search.brave.com/res/v1/web/search`
  - Auth: `BRAVE_API_KEY` (bearer token in X-Subscription-Token header)
  - Implementation: `app/tools.py:web_search()` with fallback chain
  - Response format: JSON with `web.results[]` array (title, description, url)

- Tavily Search - Fallback web search provider
  - SDK/Client: `httpx` async HTTP client
  - Endpoint: `https://api.tavily.com/search` (POST)
  - Auth: `TAVILY_API_KEY` (embedded in request body)
  - Implementation: `app/tools.py:web_search()` as fallback when Brave disabled/fails
  - Response format: JSON with `results[]` array (title, content, url)

- Custom Search Provider - Pluggable endpoint for custom search backends
  - Protocol: GET request with `q` query parameter
  - Auth: Optional `api_key` parameter
  - Response format: JSON with `results[]` array (title, snippet, url)

**Home Assistant Integration:**
- Smart home device control via HA REST API
  - Base URL: `LOCALIS_HA_URL` (e.g., `http://192.168.1.100:8123`)
  - Auth: `LOCALIS_HA_TOKEN` (Bearer token in Authorization header)
  - Light entity ID: `LOCALIS_LIGHT_ENTITY` (default: `light.rishi_room_light`, configurable)
  - Implementation: `app/assist.py` (FunctionGemma-based smart home model)
  - SDK/Client: `httpx` async HTTP client
  - Supported endpoints:
    - `POST /api/services/{domain}/{service}` - Call service (toggle, turn_on, brightness, color, color_temp)
    - `GET /api/states/{entity_id}` - Query light state (color, brightness, state)
  - Service calls: `light.toggle`, `light.turn_on` with params (brightness 0-255, rgb_color [r,g,b], color_temp_kelvin 1000-10000)

**Model Downloads:**
- HuggingFace Hub - Model repository for tutorial model and voice models
  - Tool: `huggingface-hub` Python package
  - CLI: `huggingface-cli download {repo_id} {filename}` used by setup wizard
  - Tutorial model: `johnhaul/Qwen3-0.6B-Q4_K_M-GGUF` (Qwen 0.6B, lightweight, ~350MB)
  - Default assist model: `distil-labs/distil-home-assistant-functiongemma-gguf` (function-calling for HA)
  - Voice models: Piper ONNX models from `rhasspy/piper-voices` (manual download + config)

## Data Storage

**Databases:**
- SQLite 3 - Primary persistent storage
  - Connection: `chat_history.db` (path: `LOCALIS_DATA_DIR/chat_history.db`)
  - Client: Python built-in `sqlite3` module
  - Tables: sessions, messages, user_memory, user_memory_meta, vector_memory, memory_events, rag_files, app_settings
  - Schema version: Auto-versioned with health checks on startup

**File Storage:**
- Local filesystem - RAG uploads and static assets
  - Location: `LOCALIS_DATA_DIR/rag/sessions/{session_id}/uploads/{file_id}.{ext}`
  - Supported formats: PDF, TXT, MD, DOCX, CSV (whitelist enforced)
  - Max file size: 100MB per file, 500MB per session
  - Chunking: Stored as JSONL in `{file_id}.chunks.jsonl`

**Vector Storage:**
- ChromaDB - Persistent vector database for RAG
  - Location: `LOCALIS_DATA_DIR/chroma/` (persistent directory)
  - Collections: One per session (sanitized session ID)
  - Embeddings: BAAI/bge-small-en-v1.5 (384-dim vectors via sentence-transformers)
  - Distance metric: Cosine distance (default Chroma metric)
  - Threshold: 1.2 (RAG_DISTANCE_THRESHOLD in `app/rag_vector.py`)

**Caching:**
- Memory retrieval cache - In-process TTL cache
  - Implementation: Module-level dict in `app/memory_core.py`
  - TTL: 10 seconds per query
  - Max size: 50 cached entries

## Authentication & Identity

**Auth Provider:**
- None (local-first, no account system)
- Identity model: Device-local + optional Home Assistant integration
  - Implementation: Tier-A identity keys stored in SQLite with `user_explicit` authority
  - Tier-A keys: preferred_name, location, timezone, language_preferences
  - Confirmation workflow: Router proposes changes, user confirms via `/confirm` command

**Home Assistant Auth:**
- Bearer token authentication
  - Env var: `LOCALIS_HA_TOKEN`
  - HTTP header: `Authorization: Bearer {token}`
  - Validation: HA rejects invalid tokens with 401/403 responses

**Voice Security:**
- Localhost-only by default (browser-same-origin WebSocket)
- LAN access: Optional via `LOCALIS_VOICE_KEY` (not yet exposed in current code)

## Monitoring & Observability

**Error Tracking:**
- None (built-in Python logging only)
- Log output: `~/.local/share/localis/logs/localis.log` (if logging configured)
- Console logging: All modules use `logging.getLogger(__name__)` with `[MODULE]` prefixes

**Logs:**
- Approach: Standard Python logging via `logging` module
  - Format: Info/Warning/Error messages with module prefixes (`[Voice]`, `[Memory]`, `[Tools]`, etc.)
  - Debug mode: Enabled via `LOCALIS_DEBUG=1` environment variable
  - No structured logging (flat text logs)

**Metrics:**
- System monitoring endpoint: `GET /api/system-stats`
  - Collects: CPU%, memory usage, VRAM per GPU (via pynvml), disk space
  - Used by UI right-sidebar to display stats poll
- No persistent metrics store or time-series database

## CI/CD & Deployment

**Hosting:**
- Self-hosted local/LAN deployment (no cloud platform assumed)
- Development: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

**CI Pipeline:**
- None configured (no GitHub Actions, GitLab CI, etc.)
- Updater module: Git-based self-update via `app/updater.py`
  - Mechanism: `git fetch` + `git pull` for main branch updates
  - Git executable: Configurable via `LOCALIS_GIT_EXE` env var
  - Status API: `GET /update/status` returns branch, commits ahead/behind, dirty working tree

**Update/Deployment:**
- Manual git pull + server restart
- Automatic schema migrations on database open (app/database.py)
- No containerization (Docker support not present)

## Webhooks & Callbacks

**Incoming:**
- Voice endpoints (streaming):
  - `WebSocket /voice/wakeword/ws` - Browser streams PCM audio, server runs wakeword detection
  - `POST /voice/transcribe` - Transcribe uploaded WAV (browser PTT)
  - `POST /voice/speak` - Generate TTS audio (Piper subprocess)

- RAG SSE streaming:
  - `GET /rag/ingest_events/{ingest_id}` - Server-sent events for file ingest progress
  - Event payload: JSON with `event_type`, `state`, `phase`, `total_files`, `done_files`, `current_file_name`, `message`, `error`

**Outgoing:**
- Home Assistant service calls:
  - `POST /api/services/light/toggle` - Toggle light via HA API
  - `POST /api/services/light/turn_on` - Set brightness/color via HA API
- Web search requests:
  - Brave: GET to `https://api.search.brave.com/res/v1/web/search`
  - Tavily: POST to `https://api.tavily.com/search`
- Model downloads:
  - HuggingFace CDN HTTP GET for `.gguf` and voice model files

## Environment Configuration

**Required env vars for full features:**
- `LOCALIS_HA_URL` - Home Assistant URL (e.g., `http://192.168.1.100:8123`)
- `LOCALIS_HA_TOKEN` - HA auth token (long alphanumeric string)
- `LOCALIS_LIGHT_ENTITY` - Light entity ID (e.g., `light.rishi_room_light`)
- `BRAVE_API_KEY` or `TAVILY_API_KEY` - At least one web search provider
- `LOCALIS_PIPER_MODEL` - Path to Piper ONNX model (for TTS)

**Optional but recommended:**
- `MODEL_PATH` - Custom GGUF models directory (default: `DATA_DIR/models`)
- `LOCALIS_DATA_DIR` - Custom persistent data directory
- `LOCALIS_WHISPER_DEVICE` - Force STT device: cpu|cuda (default: auto-detect)
- `LOCALIS_WAKEWORD_THRESHOLD` - Adjust sensitivity (default: 0.20, tuned to 0.15 for "Hey Jarvis")
- `LOCALIS_DEBUG` - Enable verbose logging (0|1)

**Secrets location:**
- Primary: `~/.local/share/localis/secret.env`
- Fallback: Project root `./secret.env`
- Load order: Checked at startup before importing modules that use env vars
- Never committed to git (in `.gitignore`)

---

*Integration audit: 2026-03-14*
