#!/usr/bin/env bash
set -euo pipefail
source .venv-voice/bin/activate
exec python app/main.py
