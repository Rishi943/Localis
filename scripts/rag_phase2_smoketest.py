#!/usr/bin/env python3
"""
RAG Phase 2 Smoketest: Upload -> Process -> Index -> Query
Minimal output: 3 lines max.
"""
import sys
import tempfile
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "phase2_smoke"
PHRASE = "ZEBRA_CAROUSEL_123"

def main():
    client = httpx.Client(timeout=30)

    try:
        # 1. Upload
        content = f"Test document with phrase: {PHRASE}. This should be indexed and retrievable."
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
            return 1

        file_id = resp.json()["file"]["id"]
        Path(temp_file).unlink()

        # 2. Process
        resp = client.post(
            f"{BASE_URL}/rag/process/{file_id}?session_id={SESSION_ID}"
        )
        if resp.status_code != 200:
            print(f"FAIL process: {resp.status_code}")
            return 1

        print("PASS upload/process")

        # 3. Index
        resp = client.post(
            f"{BASE_URL}/rag/index_session?session_id={SESSION_ID}"
        )
        if resp.status_code != 200:
            print(f"FAIL index: {resp.status_code}")
            return 1

        indexed = resp.json()
        vector_count = indexed.get("total_chunks", 0)
        print(f"PASS indexed vectors={vector_count}")

        # 4. Query
        resp = client.post(
            f"{BASE_URL}/rag/query",
            json={"session_id": SESSION_ID, "query": PHRASE, "top_k": 3}
        )
        if resp.status_code != 200:
            print(f"FAIL query: {resp.status_code}")
            return 1

        results = resp.json().get("results", [])
        if not results:
            print("PASS query top_match_contains_phrase=false")
            return 0

        top_match_text = results[0].get("text", "").upper()
        contains_phrase = PHRASE.upper() in top_match_text or PHRASE in results[0].get("text", "")
        print(f"PASS query top_match_contains_phrase={contains_phrase}")

        return 0 if contains_phrase else 1

    except Exception as e:
        print(f"FAIL exception: {str(e)[:60]}")
        return 1

    finally:
        client.close()

if __name__ == "__main__":
    sys.exit(main())
