# Localis

A local, GPU-accelerated AI assistant that runs entirely on your machine. No cloud, no subscriptions — your data stays private.

## Features

- **Local LLM inference** via llama-cpp-python (GGUF models, GPU-accelerated)
- **Persistent memory** — remembers facts about you across conversations
- **Web search** — Brave or Tavily search integration (optional)
- **RAG** — upload PDFs, text files, and documents for in-context retrieval
- **Voice** — wake word detection, speech-to-text (Whisper), and text-to-speech (Piper) *(optional)*
- **Self-updating** — pulls latest changes from GitHub automatically

## Requirements

- Python 3.12
- A GGUF model file (e.g. from [HuggingFace](https://huggingface.co))
- NVIDIA GPU recommended (CUDA); CPU-only works but is slow

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/Rishi943/localis-app.git
cd localis-app

# 2. Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure (optional but recommended)
#    Create secret.env in the project root:
#    MODEL_PATH=/path/to/your/models
#    BRAVE_API_KEY=your_key      # for web search
#    TAVILY_API_KEY=your_key     # alternative search provider

# 5. Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** in your browser. On first launch, a setup wizard will guide you through downloading a model.

## Voice Support (Optional)

Voice requires Python 3.11 and separate dependencies due to `tflite-runtime` compatibility.

```bash
bash scripts/setup_voice_venv.sh
```

You also need the [Piper TTS binary](https://github.com/rhasspy/piper/releases) installed in your PATH and a voice model (`.onnx`) configured via `LOCALIS_PIPER_MODEL` in `secret.env`.

## Data Directory

All persistent data (database, models, uploaded files) is stored at:

| Platform | Path |
|----------|------|
| Linux | `~/.local/share/localis/` |
| macOS | `~/Library/Application Support/Localis/` |
| Windows | `%LOCALAPPDATA%\Localis\` |

## Configuration (`secret.env`)

```env
MODEL_PATH=/path/to/models/directory
BRAVE_API_KEY=your_brave_key
TAVILY_API_KEY=your_tavily_key
```

Place this file in the project root. It is gitignored and never committed.
