#!/usr/bin/env python3
"""RAG Phase 4A: Per-session settings and per-file active toggle test."""
import sys
import json
import tempfile
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "phase4a_test"
TOKEN = "PHASE4A_TEST_TOKEN"

client = httpx.Client(timeout=30)

try:
    # 1. Upload a test file
    content = f"Document with unique token: {TOKEN}. This tests RAG Phase 4A."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_file = f.name

    with open(temp_file, 'rb') as f:
        resp = client.post(
            f"{BASE_URL}/rag/upload",
            data={"session_id": SESSION_ID},
            files={"file": f}
        )
    if resp.status_code != 200:
        print(f"FAIL upload: {resp.status_code}")
        sys.exit(1)

    file_id = resp.json()["file"]["id"]
    Path(temp_file).unlink()

    # 2. Test GET /rag/settings (should return defaults)
    resp = client.get(f"{BASE_URL}/rag/settings?session_id={SESSION_ID}")
    if resp.status_code != 200:
        print(f"FAIL GET settings: {resp.status_code}")
        sys.exit(1)
    data = resp.json()
    if not ("rag_enabled" in data and "auto_index" in data):
        print(f"FAIL settings keys missing: {list(data.keys())}")
        sys.exit(1)
    print(f"✓ GET /rag/settings: rag_enabled={data['rag_enabled']}, auto_index={data['auto_index']}")

    # 3. Test POST /rag/settings to update
    resp = client.post(
        f"{BASE_URL}/rag/settings?session_id={SESSION_ID}",
        json={"rag_enabled": False}
    )
    if resp.status_code != 200:
        print(f"FAIL POST settings: {resp.status_code}")
        sys.exit(1)
    data = resp.json()
    if data.get("rag_enabled") != False:
        print(f"FAIL settings update: rag_enabled={data.get('rag_enabled')}")
        sys.exit(1)
    print(f"✓ POST /rag/settings: updated rag_enabled to False")

    # 4. Test GET /rag/list includes settings and file is_active
    resp = client.get(f"{BASE_URL}/rag/list?session_id={SESSION_ID}")
    if resp.status_code != 200:
        print(f"FAIL list: {resp.status_code}")
        sys.exit(1)
    data = resp.json()
    if "settings" not in data:
        print(f"FAIL list missing settings: {list(data.keys())}")
        sys.exit(1)
    if not data.get("files") or "is_active" not in data["files"][0]:
        print(f"FAIL file missing is_active field")
        sys.exit(1)
    print(f"✓ GET /rag/list: includes settings and file.is_active")

    # 5. Test POST /rag/file_active to toggle
    resp = client.post(
        f"{BASE_URL}/rag/file_active?session_id={SESSION_ID}",
        json={"file_id": file_id, "is_active": False}
    )
    if resp.status_code != 200:
        print(f"FAIL POST file_active: {resp.status_code}")
        sys.exit(1)

    # 6. Verify toggle worked
    resp = client.get(f"{BASE_URL}/rag/list?session_id={SESSION_ID}")
    if resp.json()["files"][0]["is_active"] != False:
        print(f"FAIL file_active toggle didn't work")
        sys.exit(1)
    print(f"✓ POST /rag/file_active: toggled is_active to False")

    # 7. Test session mismatch on file_active
    resp = client.post(
        f"{BASE_URL}/rag/file_active?session_id=wrong_session",
        json={"file_id": file_id, "is_active": True}
    )
    if resp.status_code != 403:
        print(f"FAIL session_mismatch check: expected 403, got {resp.status_code}")
        sys.exit(1)
    print(f"✓ POST /rag/file_active: correctly rejects session_mismatch")

    print("\n✓ RAG Phase 4A settings and file active toggle works")
    sys.exit(0)

except Exception as e:
    print(f"FAIL exception: {str(e)[:60]}")
    sys.exit(1)

finally:
    client.close()
