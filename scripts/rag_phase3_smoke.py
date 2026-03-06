#!/usr/bin/env python3
"""RAG Phase 3: Injection preview smoketest."""
import sys
import json
import tempfile
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "phase3_smoke"
TOKEN = "PHASE3_INJECTION_TOKEN"

client = httpx.Client(timeout=30)

try:
    # 1. Create test file
    content = f"Document with unique token: {TOKEN}. This tests RAG injection."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_file = f.name

    # 2. Upload
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
    original_name = resp.json()["file"]["original_name"]
    Path(temp_file).unlink()

    # 3. Process
    resp = client.post(f"{BASE_URL}/rag/process/{file_id}?session_id={SESSION_ID}")
    if resp.status_code != 200:
        print(f"FAIL process: {resp.status_code}")
        sys.exit(1)

    # 4. Index
    resp = client.post(f"{BASE_URL}/rag/index_session?session_id={SESSION_ID}")
    if resp.status_code != 200:
        print(f"FAIL index: {resp.status_code}")
        sys.exit(1)

    # 5. Injection preview
    resp = client.post(
        f"{BASE_URL}/rag/injection_preview",
        json={"session_id": SESSION_ID, "query": TOKEN, "top_k": 4}
    )
    if resp.status_code != 200:
        print(f"FAIL preview: {resp.status_code}")
        sys.exit(1)

    data = resp.json()
    hits = data.get("hits", 0)
    sources = data.get("sources", "")
    context_chars = data.get("context_chars", 0)

    # 6. Verify results
    sources_contains_file = original_name in sources if sources else False

    print(f"file_id: {file_id}")
    print(f"hits: {hits}")
    print(f"sources_contains_filename: {sources_contains_file}")
    print(f"context_chars: {context_chars}")

    if hits > 0 and sources_contains_file:
        print("\n✓ RAG injection preview works")
        sys.exit(0)
    else:
        print(f"\n✗ FAIL: hits={hits}, sources_ok={sources_contains_file}")
        sys.exit(1)

except Exception as e:
    print(f"FAIL exception: {str(e)[:60]}")
    sys.exit(1)

finally:
    client.close()
