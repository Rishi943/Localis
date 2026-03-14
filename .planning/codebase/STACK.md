# Technology Stack

**Analysis Date:** 2026-03-14

## Languages

**Primary:**
- Python 3.12.12 - Backend API, inference, memory system, voice processing
- JavaScript (ES6+) - Frontend UI, chat interaction, wakeword toggle

**Secondary:**
- HTML5 - UI templates
- CSS3 - Midnight Glass design system

## Runtime

**Environment:**
- Python 3.12.12 (via `.python-version`)
- Node.js - Not used (no package.json)

**Package Manager:**
- pip (Python)
- No lockfile present (requirements.txt is canonical)

**Voice Support (Optional):**
- Separate Python 3.11 venv (`.venv-voice`) for `openwakeword` + `tflite-runtime` compatibility
- Install via: `bash scripts/setup_voice_venv.sh`

## Frameworks

**Core:**
- FastAPI 0.100+ - HTTP API server, routing, WebSocket support
- Uvicorn - ASGI server for FastAPI (started with `--reload` in dev)

**Inference & AI:**
- llama-cpp-python - Local LLM inference with GGUF format, GPU acceleration via CUDA
- sentence-transformers (BAAI/bge-small-en-v1.5) - CPU-based embeddings for memory retrieval and RAG
- faster-whisper - STT (speech-to-text) with CPU/GPU compute type selection
- openwakeword 0.6.0 - Wakeword detection ("Hey Jarvis") via ONNX models

**Data & Storage:**
- SQLite 3 - Persistent database (chat_history.db)
- ChromaDB - Vector store for RAG chunks (persistent in `DATA_DIR/chroma/`)

**Text Processing:**
- pypdf - PDF extraction for RAG
- python-docx - DOCX extraction for RAG
- (CSV extraction via built-in Python)

**Voice/Audio:**
- Piper TTS - Text-to-speech via CLI subprocess (ONNX-based)
- sounddevice - Microphone audio capture for wakeword daemon
- ffmpeg - Audio format conversion (optional, used if available)
- WebAudio API (browser) - Microphone access for PTT and wakeword

**System Monitoring:**
- psutil - CPU/memory/disk stats
- pynvml - NVIDIA GPU monitoring (VRAM, utilization)

## Key Dependencies

**Critical (inference & memory):**
- llama-cpp-python - LLM inference with GPU support
- sentence-transformers - Embeddings for memory and RAG
- faster-whisper - STT model loading and inference
- chromadb - Vector indexing for RAG
- openwakeword==0.6.0 - Pinned version for tflite-runtime compatibility

**Web Framework:**
- fastapi - API routing, validation (Pydantic)
- uvicorn[standard] - ASGI server with all features (HTTP, WebSocket, lifespan)
- pydantic - Request/response validation
- python-multipart - Form data handling for file uploads

**File & Network:**
- httpx - Async HTTP client (web search, HA API calls)
- aiofiles - Async file I/O
- huggingface-hub - Model download (via `huggingface-cli` for setup wizard)

**System & Utilities:**
- python-dotenv - Environment variable loading from `.env` files
- pynvml - GPU metrics collection
- psutil - System metrics

**Development:**
- No formal test framework present (manual testing only)

## Configuration

**Environment:**
- Primary: `secret.env` at project root or `~/.local/share/localis/secret.env`
- Loaded via python-dotenv in `main.py` BEFORE local imports (critical for voice/assist modules)
- Key config env vars:
  - `LOCALIS_DATA_DIR` - Persistent data directory (default: `~/.local/share/localis/`)
  - `MODEL_PATH` - GGUF models directory
  - `LOCALIS_DB_PATH` or `LOCALIS_DB_PATH` - SQLite database location
  - `LOCALIS_WHISPER_MODEL` - STT model size: tiny|base|small|medium|large (default: small)
  - `LOCALIS_WHISPER_DEVICE` - STT compute: auto|cpu|cuda (default: auto)
  - `LOCALIS_PIPER_MODEL` - Path to Piper ONNX voice model
  - `LOCALIS_WAKEWORD_MODEL` - Wakeword model: "hey jarvis"|"alexa"|custom path (default: "hey jarvis")
  - `LOCALIS_WAKEWORD_THRESHOLD` - Detection sensitivity (default: 0.20, tuned to 0.15 as of 2026-03-10)
  - `LOCALIS_ASSIST_PHASE` - Smart home phase gate: 1 (toggle only)|2 (brightness/color) (default: 2)
  - `BRAVE_API_KEY` - Web search provider key
  - `TAVILY_API_KEY` - Web search fallback provider key
  - `LOCALIS_HA_URL` - Home Assistant instance URL
  - `LOCALIS_HA_TOKEN` - Home Assistant auth token
  - `LOCALIS_LIGHT_ENTITY` - HA entity ID (default: light.bedroom_light)
  - `LOCALIS_DEBUG` - Verbose logging (0|1, default: 0)

**Build:**
- No build system (pure Python)
- Startup: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Platform Requirements

**Development:**
- Linux, macOS, or Windows (tested on Linux x86_64)
- Python 3.12.12
- CUDA 11.8+ (for GPU acceleration, optional)
- piper CLI in PATH (for TTS)
- git (for updater module)
- ffmpeg (optional, for audio conversion)

**Production:**
- Linux x86_64 (primary deployment target)
- 8GB+ RAM (LLM + embeddings on CPU: ~6-7GB)
- 2GB+ VRAM (GPU-accelerated inference, optional)
- SQLite (file-based, no separate server)
- Optional: Home Assistant instance reachable via HTTP

**Browser Support:**
- Modern browsers with WebAudio API (Chrome, Firefox, Safari, Edge)
- WebSocket support required (for wakeword streaming)

---

*Stack analysis: 2026-03-14*
