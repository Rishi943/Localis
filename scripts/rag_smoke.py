#!/usr/bin/env python3
"""RAG smoke test - fast regression gate."""
import sys
import json
import argparse
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def make_request(url, method="GET", data=None, files=None):
    """Make HTTP request (no extra dependencies)."""
    if files:
        # Multipart form data for file upload
        import io
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        body = io.BytesIO()

        for key, value in data.items() if data else []:
            body.write(f'--{boundary}\r\n'.encode())
            body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
            body.write(f'{value}\r\n'.encode())

        for key, filepath in files.items():
            with open(filepath, 'rb') as f:
                file_content = f.read()
            body.write(f'--{boundary}\r\n'.encode())
            body.write(f'Content-Disposition: form-data; name="{key}"; filename="{Path(filepath).name}"\r\n'.encode())
            body.write(b'Content-Type: text/plain\r\n\r\n')
            body.write(file_content)
            body.write(b'\r\n')

        body.write(f'--{boundary}--\r\n'.encode())

        req = Request(url, data=body.getvalue(), method=method)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    else:
        if data:
            data = json.dumps(data).encode('utf-8')
        req = Request(url, data=data, method=method)
        if data:
            req.add_header('Content-Type', 'application/json')

    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8')), resp.status
    except Exception as e:
        return None, None

def main():
    parser = argparse.ArgumentParser(description="RAG smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Server base URL")
    parser.add_argument("--session-id", required=True, help="Session ID")
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/')
    session_id = args.session_id
    unique_phrase = "SMOKE_TEST_MARKER_12345"

    try:
        # 1. Create temp file with unique phrase
        content = f"This is a RAG smoke test file.\n{unique_phrase}\nEnd of test content."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_file = f.name

        # 2. Upload file
        resp, status = make_request(
            f"{base_url}/rag/upload",
            method="POST",
            data={"session_id": session_id},
            files={"file": temp_file}
        )
        if status != 200 or not resp or not resp.get("file"):
            raise Exception(f"Upload failed: {resp}")
        file_id = resp["file"]["id"]

        # 3. Process file
        resp, status = make_request(
            f"{base_url}/rag/process/{file_id}?session_id={session_id}",
            method="POST"
        )
        if status != 200:
            raise Exception(f"Process failed: {resp}")

        # 4. Index session (async) and wait
        resp, status = make_request(
            f"{base_url}/rag/index_start?session_id={session_id}",
            method="POST"
        )
        if status != 200:
            raise Exception(f"Index start failed: {resp}")

        # Wait for indexing to complete
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            resp, status = make_request(
                f"{base_url}/rag/index_status?session_id={session_id}",
                method="GET"
            )
            if not resp:
                raise Exception("Index status check failed")

            state = resp.get("state")
            if state == "done":
                break
            elif state in ["cancelled", "error"]:
                raise Exception(f"Indexing {state}: {resp.get('message')}")

            time.sleep(0.5)
        else:
            raise Exception("Indexing timeout")

        # 5. Query for unique phrase
        resp, status = make_request(
            f"{base_url}/rag/query",
            method="POST",
            data={"session_id": session_id, "query": unique_phrase, "top_k": 5}
        )
        if status != 200 or not resp:
            raise Exception(f"Query failed: {resp}")

        results = resp.get("results", [])
        if not results:
            raise Exception("Query returned no results")

        # 6. Assert top result contains phrase
        top_result = results[0]
        if unique_phrase not in top_result.get("text", ""):
            raise Exception(f"Phrase not in top result. Got: {top_result.get('text', '')[:100]}")

        print("PASS rag_smoke")
        return 0

    except Exception as e:
        print(f"FAIL rag_smoke: {str(e)[:80]}")
        return 1
    finally:
        try:
            Path(temp_file).unlink()
        except:
            pass

if __name__ == "__main__":
    sys.exit(main())
