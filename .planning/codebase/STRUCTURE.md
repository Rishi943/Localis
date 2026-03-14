# Codebase Structure

**Analysis Date:** 2026-03-14

## Directory Layout

```
/home/rishi/Rishi/AI/Localis/
├── app/                               # Python FastAPI application
│   ├── main.py                        # Entry point, route handlers, inference pipeline (1907 lines)
│   ├── database.py                    # SQLite schema, query builders (961 lines)
│   ├── memory_core.py                 # Two-tier memory system, vector embeddings (792 lines)
│   ├── tools.py                       # Web search integrations (Brave, Tavily, custom)
│   ├── rag.py                         # Document upload, ingest jobs, RAG API
│   ├── rag_processing.py              # Document extraction (PDF, DOCX, TXT, MD, CSV)
│   ├── rag_vector.py                  # Vector embeddings, similarity search for RAG
│   ├── assist.py                      # Home Assistant smart-home control (lights, state)
│   ├── voice.py                       # STT (faster-whisper), TTS (Piper) endpoints
│   ├── wakeword.py                    # Wakeword detection via WebSocket (openwakeword)
│   ├── setup_wizard.py                # First-run model download wizard
│   ├── updater.py                     # Git-based self-update mechanism
│   ├── __init__.py                    # Package init
│   ├── templates/
│   │   └── index.html                 # Single-page app HTML shell (32KB, includes SVG icons)
│   └── static/
│       ├── css/
│       │   └── app.css                # Midnight Glass design system, component styles
│       ├── js/
│       │   ├── app.js                 # Main frontend logic, modules (6346 lines)
│       │   ├── setup_wizard.js        # Tutorial UI state machine
│       │   └── updater_ui.js          # Self-update progress UI
│       └── [static assets]            # wallpaper.bg, icons (symlinked from UIUX/)
├── tests/                             # Unit & integration test files
│   ├── test_assist_router.py          # Home Assistant routing tests
│   ├── test_voice_stt.py              # Voice transcription tests
│   ├── test_wakeword_*.py             # Wakeword detection & preload tests
│   └── test_light_state.py            # HA light state query tests
├── scripts/                           # Utility scripts
│   ├── setup_voice_venv.sh            # Create Python 3.11 venv for voice (openwakeword)
│   └── voice_verify.sh                # Test voice modules
├── docs/
│   └── superpowers/                   # GSD phase plans & specifications
│       ├── specs/
│       └── plans/
├── UIUX/
│   ├── DESIGN.md                      # Canonical design system (Midnight Glass)
│   ├── icons/                         # SVG icon definitions
│   └── [screenshots]                  # Demo screenshots
├── voices/                            # TTS model voices (downloaded at runtime)
├── .env / .env.* / secret.env         # Environment variables (NOT committed, see CLAUDE.md)
├── requirements.txt                   # Python package dependencies (main venv)
├── requirements-voice.txt             # Python voice dependencies (separate .venv-voice)
├── .python-version                    # Python 3.12 (main venv)
├── CLAUDE.md                          # Project instructions, conventions, patterns
├── .gitignore                         # Git exclusions (includes .env, models/, .venv*)
└── chat_history.db                    # SQLite DB (generated at runtime, in DATA_DIR)

# Data Directory Structure (persistent, ~/.local/share/localis/)
DATA_DIR/
├── chat_history.db                    # Main SQLite database
├── models/                            # GGUF model files (user-downloaded)
│   ├── model1.gguf
│   └── model2.gguf
├── static/                            # Persistent static files (synced from app/static/)
│   ├── css/
│   ├── js/
│   ├── wallpaper.bg                   # User-uploaded background image
│   └── .temp_user_name                # Temporary demo name (not persisted between sessions)
├── rag/
│   └── sessions/
│       └── <session-id>/
│           └── uploads/               # Per-session uploaded files
│               ├── <file-id>.pdf
│               ├── <file-id>.txt
│               └── <file-id>.docx
├── wakeword_models/                   # Cached wakeword models
│   └── hey_jarvis_v0.1.onnx           # ONNX format (openwakeword)
├── logs/
│   └── localis.log                    # Rotating log file (10MB max, 3 backups)
└── secret.env                         # Optional local config override (takes precedence over repo root)
```

## Directory Purposes

**app/**
- Purpose: Core Python FastAPI application
- Contains: Route handlers, database layer, memory system, inference pipeline
- Key files: `main.py` (entry point), `database.py` (schema), `memory_core.py` (learning)

**app/templates/**
- Purpose: Server-rendered HTML shell
- Contains: Single `index.html` with SVG icon defs, <head> injection point for voice key
- Key files: `index.html` (32KB)

**app/static/**
- Purpose: Frontend assets (CSS, JavaScript)
- Contains: Styles, module logic, utility functions
- Pattern: Read-only during runtime; `app/main.py` syncs these to DATA_DIR/static/ for persistence
- User-owned files: `wallpaper.bg` (custom upload), `.temp_user_name` (demo override)
- Key files: `app.js` (6346 lines, main logic), `app.css` (Midnight Glass system)

**tests/**
- Purpose: Unit and integration tests
- Contains: Pytest-compatible test modules for voice, assist, wakeword
- Run: `bash scripts/voice_verify.sh` (includes offline WAV test + WS smoke test)

**scripts/**
- Purpose: Development and setup utilities
- Contains: Voice venv creation (`setup_voice_venv.sh`), verification suite (`voice_verify.sh`)
- Usage: Run before first voice test; creates Python 3.11 venv due to tflite-runtime requirement

**docs/superpowers/**
- Purpose: GSD phase plans and specifications
- Contains: Markdown specs for features, implementation checklists
- Pattern: Created by `/gsd:plan-phase`, referenced by `/gsd:execute-phase`

**UIUX/**
- Purpose: Design system and visual assets
- Contains: `DESIGN.md` (canonical, must read before UI changes), SVG icons, screenshots
- Key file: `DESIGN.md` (defines Midnight Glass identity, typography, colors, components)

**voices/**
- Purpose: Text-to-speech model cache
- Contents: Piper voice models (downloaded on first use)
- Location: `~/.local/share/localis/voices/` at runtime

## Key File Locations

**Entry Points:**
- `app/main.py` - FastAPI app initialization, route registration, startup hooks
- `app/templates/index.html` - HTML shell served at `GET /`
- `app/static/js/app.js` - Frontend initialization (runs on page load)

**Configuration:**
- `secret.env` - Environment variables (MODEL_PATH, API keys, HA credentials)
- `.env` - Development environment (optional, git-ignored)
- `requirements.txt` - Python package versions (main venv)
- `requirements-voice.txt` - Voice-specific packages (separate .venv-voice, Python 3.11)
- `.python-version` - Python 3.12 (main development version)

**Core Logic:**
- `app/main.py` - Chat endpoint (lines 893-1488), model loading, session management
- `app/memory_core.py` - Memory retrieval, vector search, Tier-A/B schema
- `app/database.py` - SQLite schema, query builders, health checks
- `app/rag_vector.py` - Embedding generation, RAG search algorithm

**Testing:**
- `tests/test_voice_stt.py` - STT (faster-whisper) unit tests
- `tests/test_wakeword_*.py` - Wakeword detection tests (runs offline + online variants)
- `tests/test_assist_router.py` - Home Assistant integration tests
- `bash scripts/voice_verify.sh` - Complete voice verification suite

**Feature Modules (Router Pattern):**
- `app/setup_wizard.py` - First-run questionnaire, model download
- `app/rag.py` - Upload API, ingest job tracking
- `app/voice.py` - STT/TTS endpoints
- `app/wakeword.py` - WebSocket wakeword stream handler
- `app/assist.py` - Home Assistant light control

## Naming Conventions

**Files:**
- `[feature].py` - Feature module (lowercase, snake_case)
- Example: `app/rag.py`, `app/memory_core.py`, `app/assist.py`
- HTML: `index.html` (single file, required by FastAPI)
- CSS: `app.css` (monolithic, Midnight Glass system)
- JS: `app.js` (monolithic module with IIFE submodules), `setup_wizard.js`, `updater_ui.js`

**Functions:**
- `async def [route_name]_endpoint()` - HTTP route handler
- Example: `async def chat_endpoint()`, `async def list_models()`
- `def _[internal_name]()` - Internal helper (underscore prefix for privacy)
- Example: `def _load_model_internal()`, `def _ensure_db_directory()`
- `def register_[feature]()` - Feature registration function
- Example: `def register_setup_wizard()`, `def register_rag()`

**Variables:**
- `current_model`, `current_model_name` - Global model state
- `MODEL_LOCK` - Global threading lock for model access
- `els` - Element cache in frontend (DOM references)
- `state` - Global app state object in frontend
- `session_id` - UUID string for chat session
- `_[name]` - Module-level private variables
- Example: `_assist_model`, `_ha_url` (module-level state in feature modules)

**Types:**
- `MemoryItem` - Single memory record dataclass
- `MemoryProposal` - Unapproved memory write proposal
- `ChatRequest` - Main chat endpoint request schema
- `TutorialChatRequest` - Stateless tutorial request schema
- `ModelLoadRequest` - Model load endpoint schema

**Database Schema:**
- Tables: `sessions`, `messages`, `user_memory`, `vector_memory`, `memory_events`, `app_settings`, `rag_files`
- Columns: lowercase, snake_case
- Example: `session_id`, `created_at`, `last_updated`, `is_active`

**CSS Classes:**
- `.component-name` - Component base (kebab-case)
- `.component-name.state-modifier` - State variant
- Example: `.lsb` (left sidebar), `.lsb.collapsed`, `.msg-user`, `.msg-assistant`
- Midnight Glass specific: `.glass-bg`, `.glass-border`, `.ui-pulse`, `.typewriter-cursor`

**JavaScript Modules:**
- Uppercase IIFE: `const ModuleName = (() => { ... })();`
- Example: `const FRT = ...` (First Run Tutorial), `const RPG = ...` (RPG questionnaire)
- Methods: camelCase
- Example: `FRT.init()`, `ragUI.uploadFiles()`, `voiceUI.setState()`

## Where to Add New Code

**New Chat Feature (e.g., memory learning):**
- Primary code: `app/main.py` (add logic to `chat_endpoint`, lines 893-1488)
- Database changes: `app/database.py` (add schema + query builders)
- Memory changes: `app/memory_core.py` (add retrieval/write functions if memory-related)
- Tests: `tests/test_[feature].py`
- Frontend: `app/static/js/app.js` (add UI handler if needed)

**New Tool (e.g., third-party API integration):**
- Tool definition: `app/tools.py` (add async function, e.g., `async def tool_my_service()`)
- Tool registration: `app/main.py` line ~1059 (add to `ALLOWED_TOOLS` set)
- Tool execution: `app/main.py` around line 1120 in `execute_tool()` function
- Request handling: Add elif block for tool dispatch
- Tests: `tests/test_[tool]_integration.py`

**New Feature Module (e.g., external service integration):**
- Follow router pattern from `app/setup_wizard.py`, `app/rag.py`, `app/assist.py`
- Create: `app/my_feature.py`
- Export: `def register_my_feature(app, config_param)` function
- Call from: `app/main.py` after line 283 (with other `register_*` calls)
- Routes: Define `router = APIRouter(prefix="/feature", tags=["feature"])` inside module
- State: Store config on `app.state.my_feature_config` within register function
- Tests: `tests/test_my_feature.py`

**New Component/UI Element:**
- HTML: `app/templates/index.html` (add element with clear ID)
- CSS: `app/static/css/app.css` (add styles, follow Midnight Glass variables)
- JavaScript: `app/static/js/app.js`
  - Add element reference to `els` object (line ~400)
  - Create module IIFE: `const myModule = (() => { ... })();`
  - Call `myModule.init()` in `startApp()` function
  - Implement: `init()`, `refresh()`, utility functions as needed

**Shared Utilities:**
- Pure functions: `app/static/js/app.js` (top-level helpers)
  - Example: `escapeHtml()`, `readSSE()`, `parseThinking()`, UX utilities
- Python helpers: `app/database.py` (if DB-related), `app/memory_core.py` (if memory-related)
- CSS utilities: `app/static/css/app.css` (add as `.utility-name` class)

**Settings / Configuration:**
- User settings: `app/main.py` → `POST /api/settings` route (add field to handler + DB)
- Database schema: `app/database.py` → Add row to `app_settings` table if new setting
- Frontend persistence: `app/static/js/app.js` → Add to settings modal form
- App initialization: `app/main.py` startup hook → Load and apply setting

## Special Directories

**models/**
- Purpose: GGUF model files (user-downloaded or setup wizard)
- Generated: Yes (by user or setup wizard)
- Committed: No (in .gitignore, very large files)
- Location: Configured via `MODEL_PATH` env var, defaults to `~/.local/share/localis/models/`
- Expected extensions: `.gguf`

**static/ (persistent copy)**
- Purpose: Persistent, writeable static files (sync'd from app/static on startup)
- Generated: Yes (by `_seed_static_assets()` at startup)
- Committed: No (generated at runtime in DATA_DIR)
- Location: `~/.local/share/localis/static/`
- Preserved: User files (wallpaper.bg, .temp_user_name) retained on overwrite

**.venv / .venv-voice/**
- Purpose: Python virtual environments (development)
- Generated: Yes (manual setup, see CLAUDE.md)
- Committed: No (.gitignore)
- Reason: .venv uses Python 3.12 (main), .venv-voice uses Python 3.11 (openwakeword/tflite)
- Setup: `bash scripts/setup_voice_venv.sh` (creates .venv-voice)

**logs/**
- Purpose: Application logs (rotating file)
- Generated: Yes (by logging handler)
- Committed: No (.gitignore)
- Location: `~/.local/share/localis/logs/localis.log`
- Rotation: 10MB max, 3 backups retained

**rag/sessions/**
- Purpose: Per-session uploaded documents (RAG system)
- Generated: Yes (by RAG upload endpoint)
- Committed: No (user data, transient)
- Location: `~/.local/share/localis/rag/sessions/<session_id>/uploads/`
- Structure: Files named by UUID: `<file_id>.<original_extension>`

**wakeword_models/**
- Purpose: Cached openwakeword model files
- Generated: Yes (auto-downloaded on first wakeword detection)
- Committed: No (large binary files)
- Location: `~/.local/share/localis/wakeword_models/`
- Example: `hey_jarvis_v0.1.onnx` (preloaded from huggingface on startup if VOICE_PRELOAD=1)

**docs/superpowers/**
- Purpose: GSD planning documents and specifications
- Generated: Yes (by `/gsd:plan-phase` and `/gsd:map-codebase` commands)
- Committed: Yes (.gitignore does not exclude)
- Structure: Subdirs: `specs/` (feature specs), `plans/` (implementation plans)

---

*Structure analysis: 2026-03-14*
