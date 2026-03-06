#!/usr/bin/env python3
"""
scripts/test_wakeword_wav.py

Offline wakeword detection test against a WAV file.

Usage:
    python scripts/test_wakeword_wav.py path/to/test.wav [--threshold 0.5]

Record a test WAV (say "hey Jarvis" during the 5 seconds):
    arecord -r 16000 -c 1 -f S16_LE -d 5 test.wav

Exit code:
    0  — at least one detection found
    1  — no detections
"""

import argparse
import os
import sys
import wave
from pathlib import Path


_VENV_HINT = (
    "Fix: run  bash scripts/setup_voice_venv.sh  to create a Python 3.11 venv\n"
    "     with openwakeword==0.6.0 and tflite-runtime, then re-run this script\n"
    "     using that venv's Python:\n"
    "       .venv-voice/bin/python scripts/test_wakeword_wav.py --wav test.wav\n"
    "     See requirements-voice.txt for pinned dependencies."
)


def wakeword_model_dir() -> Path:
    """Return the directory where hey_jarvis model files are stored.

    Mirrors the DATA_DIR resolution logic in app/main.py so the script and
    the server always use the same on-disk location.

    Override with the LOCALIS_DATA_DIR environment variable.
    """
    localis_data = os.getenv("LOCALIS_DATA_DIR")
    if localis_data:
        base = Path(localis_data)
    elif sys.platform.startswith("win"):
        raw = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
        base = Path(raw) / "Localis"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "Localis"
    else:
        xdg = os.getenv("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        base = Path(xdg) / "localis"
    return base / "wakeword_models"


def _resolve_feature_paths(model_dir: Path) -> dict:
    """
    Glob for melspectrogram and embedding feature model files in model_dir.
    Returns {"melspec": str_or_empty, "embed": str_or_empty}.
    Passing empty string to Model() triggers site-packages fallback (bad),
    so callers should only pass non-empty values.
    """
    melspec = sorted(model_dir.glob("melspectrogram*.tflite"))
    embed   = sorted(model_dir.glob("embedding_model*.tflite"))
    return {
        "melspec": str(melspec[0]) if melspec else "",
        "embed":   str(embed[0])   if embed   else "",
    }


def main():
    parser = argparse.ArgumentParser(description="Offline wakeword WAV test")
    # Accept both positional and --wav for compatibility with voice_verify.sh
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--wav", dest="wav_path", metavar="WAV",
                       help="Path to a 16kHz mono int16 WAV file")
    group.add_argument("wav_path_pos", nargs="?", metavar="wav_path",
                       help=argparse.SUPPRESS)
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Detection threshold (default: 0.5)")
    parser.add_argument("--cooldown", type=float, default=1.0,
                        help="Minimum seconds between counted detections (default: 1.0)")
    args = parser.parse_args()

    wav_path = Path(args.wav_path or args.wav_path_pos)
    if not wav_path.exists():
        print(f"ERROR: File not found: {wav_path}", file=sys.stderr)
        sys.exit(1)

    # ---- Open and validate WAV ----
    try:
        with wave.open(str(wav_path), "rb") as wf:
            n_channels   = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frame_rate   = wf.getframerate()
            n_frames     = wf.getnframes()
            raw_bytes    = wf.readframes(n_frames)
    except Exception as e:
        print(f"ERROR: Could not open WAV: {e}", file=sys.stderr)
        sys.exit(1)

    if n_channels != 1:
        print(f"ERROR: Expected mono (1 channel), got {n_channels}", file=sys.stderr)
        sys.exit(1)
    if sample_width != 2:
        print(f"ERROR: Expected 16-bit PCM (2 bytes/sample), got {sample_width}", file=sys.stderr)
        sys.exit(1)
    if frame_rate != 16000:
        print(f"ERROR: Expected 16000 Hz sample rate, got {frame_rate}", file=sys.stderr)
        sys.exit(1)

    duration_s = n_frames / frame_rate
    print(f"WAV: {wav_path.name} — {duration_s:.2f}s, {n_frames} samples")

    # ---- Resolve model directory (mirrors main.py DATA_DIR logic) ----
    model_dir = wakeword_model_dir()
    model_dir.mkdir(parents=True, exist_ok=True)

    # ---- Load openWakeWord ----
    try:
        from openwakeword.model import Model
        from openwakeword.utils import download_models as _download_models
    except ImportError as e:
        print(
            f"ERROR: openwakeword not importable: {e}\n"
            f"       (tflite-runtime does not build on Python 3.13+)\n"
            f"{_VENV_HINT}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Download to our deterministic directory if no file is present yet.
    # openwakeword 0.6.0 does NOT auto-download in Model(); we must do it explicitly.
    # Using target_directory= ensures we know exactly where the file lands.
    matches = sorted(model_dir.glob("hey_jarvis*.tflite"))
    if not matches:
        print(f"Downloading hey_jarvis model to {model_dir} …")
        try:
            _download_models(model_names=["hey_jarvis"], target_directory=str(model_dir))
        except Exception as e:
            print(f"ERROR: Model download failed: {e}", file=sys.stderr)
            print(f"       Ensure internet access on first run.", file=sys.stderr)
            print(f"{_VENV_HINT}", file=sys.stderr)
            sys.exit(1)
        matches = sorted(model_dir.glob("hey_jarvis*.tflite"))

    if not matches:
        print(
            f"ERROR: hey_jarvis model not found in {model_dir} after download.\n"
            f"       Check internet access or place the .tflite file there manually.\n"
            f"{_VENV_HINT}",
            file=sys.stderr,
        )
        sys.exit(1)

    tflite_path = matches[0]
    print(f"Model: {tflite_path.name} ({tflite_path})")

    # Load by explicit file path so Model() never needs to resolve names via site-packages.
    feature = _resolve_feature_paths(model_dir)
    try:
        model = Model(
            wakeword_models=[str(tflite_path)],
            inference_framework="tflite",
            **({"melspec_model_path": feature["melspec"]} if feature["melspec"] else {}),
            **({"embedding_model_path": feature["embed"]} if feature["embed"] else {}),
        )
    except TypeError as e:
        # API mismatch — wrong openwakeword version (e.g. doesn't accept inference_framework)
        print(
            f"ERROR: openwakeword API mismatch (TypeError: {e})\n"
            f"       Installed version is incompatible — expected openwakeword==0.6.0.\n"
            f"{_VENV_HINT}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        hint = ""
        if "tflite" in str(e).lower() or "flatbuffers" in str(e).lower():
            hint = f"\n       (tflite-runtime missing or incompatible with this Python version)\n{_VENV_HINT}"
        print(f"ERROR: Could not load model {tflite_path.name}: {e}{hint}", file=sys.stderr)
        sys.exit(1)

    # ---- Feed frames ----
    FRAME_SAMPLES = 1280    # 80ms at 16kHz
    FRAME_BYTES   = FRAME_SAMPLES * 2

    detections          = 0
    frame_idx           = 0
    best_score          = 0.0
    best_timestamp      = 0.0
    last_detect_timestamp = float("-inf")
    import numpy as np

    print(f"Threshold: {args.threshold}")
    print(f"Cooldown:  {args.cooldown}s")
    print("Scanning frames...")

    while True:
        start = frame_idx * FRAME_BYTES
        chunk = raw_bytes[start : start + FRAME_BYTES]
        if len(chunk) < FRAME_BYTES:
            break

        audio_np = np.frombuffer(chunk, dtype=np.int16)
        try:
            prediction = model.predict(audio_np)
            score = max(prediction.values()) if prediction else 0.0
        except Exception as e:
            print(f"  [frame {frame_idx}] predict error: {e}", file=sys.stderr)
            frame_idx += 1
            continue

        timestamp_s = (frame_idx * FRAME_SAMPLES) / frame_rate

        if score > best_score:
            best_score     = score
            best_timestamp = timestamp_s

        if score >= args.threshold and (timestamp_s - last_detect_timestamp) >= args.cooldown:
            detections += 1
            last_detect_timestamp = timestamp_s
            print(f"  [{timestamp_s:.2f}s] hey_jarvis score={score:.3f}  *** DETECTED ***")

        frame_idx += 1

    total_frames = frame_idx
    print(f"\nSummary: {detections} detection(s) across {total_frames} frames "
          f"({duration_s:.2f}s audio)")
    print(f"Best score: {best_score:.3f} at {best_timestamp:.2f}s")

    sys.exit(0 if detections >= 1 else 1)


if __name__ == "__main__":
    main()
