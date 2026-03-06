#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv-voice"
MAIN_REQ="$REPO_ROOT/requirements.txt"
VOICE_REQ="$REPO_ROOT/requirements-voice.txt"

# 1. Fail fast if python3.11 is not available
if ! command -v python3.11 &>/dev/null; then
    echo "ERROR: python3.11 not found in PATH."
    echo "Install it with: sudo apt install python3.11 python3.11-venv"
    echo "  or via pyenv: pyenv install 3.11.9"
    exit 1
fi

echo "Using $(python3.11 --version)"

# 2. Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating voice venv at $VENV_DIR ..."
    python3.11 -m venv "$VENV_DIR"
else
    echo "Voice venv already exists at $VENV_DIR — skipping creation."
fi

# 3. Upgrade pip
"$VENV_DIR/bin/pip" install --upgrade pip -q

# 4. Install main server deps first (FastAPI, uvicorn, llama-cpp-python, etc.)
echo "Installing $MAIN_REQ ..."
"$VENV_DIR/bin/pip" install -r "$MAIN_REQ" -q

# 5. Install voice/wakeword deps on top
echo "Installing $VOICE_REQ ..."
"$VENV_DIR/bin/pip" install -r "$VOICE_REQ" -q

# 6. Pre-download hey_jarvis model into openwakeword's resource dir
echo "Pre-downloading hey_jarvis wakeword model ..."
"$VENV_DIR/bin/python" - <<'PYEOF'
import sys
from openwakeword.utils import download_models
try:
    download_models(model_names=["hey_jarvis"])
    print("hey_jarvis model ready.")
except Exception as e:
    print(f"WARNING: model pre-download failed: {e}", file=sys.stderr)
    print("The model will be downloaded on first use.", file=sys.stderr)
PYEOF

# 7. Sanity checks
echo ""
echo "--- Sanity check ---"
"$VENV_DIR/bin/python" --version
"$VENV_DIR/bin/python" -c "import fastapi, uvicorn; print('fastapi/uvicorn OK')"
"$VENV_DIR/bin/python" -c "
import openwakeword, openwakeword.utils as u
print('openwakeword path:', openwakeword.__file__)
print('download_models present:', hasattr(u, 'download_models'))
"
"$VENV_DIR/bin/python" -c "
import tflite_runtime.interpreter
print('tflite_runtime OK')
"

echo ""
echo "Voice venv ready. Activate with:"
echo "  source $VENV_DIR/bin/activate"
