#!/usr/bin/env python3
"""RAG query determinism test - verify consistent ordering."""
import sys
import json
import tempfile
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "determinism_test"
QUERY_TEXT = "test query for determinism"
NUM_RUNS = 10

client = httpx.Client(timeout=30)

try:
    # 1. Upload and process a test file
    content = b"This is test content for determinism testing. " * 100
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(content)
        temp_file = f.name

    resp = client.post(
        f"{BASE_URL}/rag/upload",
        data={"session_id": SESSION_ID},
        files={"file": open(temp_file, 'rb')}
    )
    if resp.status_code != 200:
        print("✗ FAIL: Upload failed")
        sys.exit(1)

    file_id = resp.json()["file"]["id"]

    # 2. Process file
    resp = client.post(f"{BASE_URL}/rag/process/{file_id}?session_id={SESSION_ID}")
    if resp.status_code != 200:
        print("✗ FAIL: Process failed")
        sys.exit(1)

    # 3. Index file
    resp = client.post(f"{BASE_URL}/rag/index_session?session_id={SESSION_ID}")
    if resp.status_code != 200:
        print("✗ FAIL: Indexing failed")
        sys.exit(1)

    # 4. Run query 10 times and verify identical ordering
    all_results = []
    for i in range(NUM_RUNS):
        resp = client.post(
            f"{BASE_URL}/rag/query",
            json={"session_id": SESSION_ID, "query": QUERY_TEXT, "top_k": 5}
        )
        if resp.status_code != 200:
            print(f"✗ FAIL: Query {i+1} failed")
            sys.exit(1)

        results = resp.json().get("results", [])
        # Extract ordering key: (chunk_id, distance)
        ordering = [(r["chunk_id"], r["distance"]) for r in results]
        all_results.append(ordering)

    # 5. Verify all orderings are identical
    first_ordering = all_results[0]
    for i, ordering in enumerate(all_results[1:], 1):
        if ordering != first_ordering:
            print(f"✗ FAIL: Run {i+1} ordering differs from run 1")
            print(f"  Run 1: {first_ordering[:2]}")
            print(f"  Run {i+1}: {ordering[:2]}")
            sys.exit(1)

    # Clean up
    Path(temp_file).unlink()

    print(f"✓ PASS: Query ordering deterministic across {NUM_RUNS} runs")
    print(f"  Sample ordering (first 3): {first_ordering[:3]}")
    sys.exit(0)

except Exception as e:
    print(f"✗ FAIL: {str(e)[:80]}")
    sys.exit(1)

finally:
    client.close()
