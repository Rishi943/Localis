# Localis

A local AI assistant that runs entirely on your machine. No cloud, no subscriptions — your data stays private.

## Features

- **Local LLM inference** via llama-cpp-python (GGUF models, GPU-accelerated)
- **Agentic tool-calling** — single-model loop with 7 built-in tools
- **Persistent memory** — remembers facts about you across conversations
- **RAG** — upload PDFs, Word docs, and CSVs for in-context retrieval
- **Web search** — Brave or Tavily integration (optional)
- **Notes & Reminders** — voice or chat-triggered, with timed pings
- **Finance Advisor** — upload bank/credit CSVs for spending analysis
- **Home Assistant** — control smart home lights and devices
- **Voice** — wake word ("Hey Jarvis"), Whisper STT, Piper TTS *(optional)*

## Requirements

- Python 3.12
- A GGUF model file (e.g. Qwen3.5 from [HuggingFace](https://huggingface.co))
- NVIDIA GPU recommended (CUDA); CPU-only works but is slow

## Installation

```bash
git clone https://github.com/Rishi943/Localis.git
cd Localis

python3.12 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000**. A setup wizard will guide you through downloading a model on first launch.

## Configuration

Create a `secret.env` file in the project root:

```env
MODEL_PATH=/path/to/models/directory

# Web search (optional)
BRAVE_API_KEY=your_key
TAVILY_API_KEY=your_key

# Home Assistant (optional)
LOCALIS_HA_URL=http://homeassistant.local:8123
LOCALIS_HA_TOKEN=your_long_lived_token
LOCALIS_LIGHT_ENTITY=light.your_light
```

## Voice Support (Optional)

Voice requires Python 3.11 due to `tflite-runtime` compatibility.

```bash
bash scripts/setup_voice_venv.sh
```

You also need the [Piper TTS binary](https://github.com/rhasspy/piper/releases) in your PATH and a voice model configured via `LOCALIS_PIPER_MODEL` in `secret.env`.

## Data

All persistent data is stored at `~/.local/share/localis/` — database, models, and uploaded files.
