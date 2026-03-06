#!/usr/bin/env python3
"""
RAG Phase 1B Smoketest: Extraction + Chunking
Tests: Upload -> Process (extract + chunk) -> Verify
"""
import sys
import json
import subprocess
import tempfile
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "phase1b_smoketest"

# Test file content
TEST_CONTENT = """This is a comprehensive test document for Phase 1B extraction and chunking.

The document contains multiple paragraphs and sentences to properly test the chunking algorithm.
Chunking should split this text into overlapping chunks of 4000 characters with 400 character overlap.

Each chunk should maintain page offset mapping so we can track which pages each chunk spans.
The chunks.jsonl file should have one JSON object per line with the required fields.

This includes chunk_id, file_id, session_id, source_name, page_start, page_end, char_start, char_end, and text.
Multiple chunks should be created from this content when processed through the chunking algorithm.

The page mapping is important for context in retrieval-augmented generation applications.
It helps maintain lineage between chunks and their source material."""

def curl_post_upload(test_file_path):
    """Upload test file using curl."""
    print("[1] Uploading test file...")
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{BASE_URL}/rag/upload",
        "-F", f"session_id={SESSION_ID}",
        "-F", f"file=@{test_file_path}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ✗ Upload failed: {result.stderr}")
        return None

    try:
        data = json.loads(result.stdout)
        if not data.get("ok"):
            print(f"   ✗ Upload returned ok=false")
            return None
        file_id = data["file"]["id"]
        print(f"   ✓ Uploaded: {file_id}")
        return file_id
    except json.JSONDecodeError:
        print(f"   ✗ Invalid JSON response: {result.stdout}")
        return None

def curl_post_process(file_id):
    """Call POST /rag/process using curl."""
    print(f"\n[2] Processing file (extract + chunk)...")
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{BASE_URL}/rag/process/{file_id}?session_id={SESSION_ID}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ✗ Process failed: {result.stderr}")
        return None

    try:
        data = json.loads(result.stdout)
        if not data.get("ok"):
            print(f"   ✗ Process returned ok=false")
            return None
        print(f"   ✓ Status: {data['status']}")
        print(f"   ✓ Pages: {data['page_count']}, Chars: {data['char_count']}, Chunks: {data['chunk_count']}")
        return data
    except json.JSONDecodeError:
        print(f"   ✗ Invalid JSON response: {result.stdout}")
        return None

def verify_chunks_file(chunks_path):
    """Verify chunks.jsonl exists and is valid."""
    print(f"\n[3] Verifying chunks.jsonl...")
    chunks_file = Path(chunks_path)

    if not chunks_file.exists():
        print(f"   ✗ Chunks file not found: {chunks_path}")
        return False

    print(f"   ✓ File exists")

    # Read and validate JSONL
    chunks = []
    try:
        with open(chunks_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                chunk = json.loads(line)
                chunks.append(chunk)

                # Validate required fields
                required = ["chunk_id", "file_id", "session_id", "source_name",
                           "page_start", "page_end", "char_start", "char_end", "text"]
                missing = [k for k in required if k not in chunk]
                if missing:
                    print(f"   ✗ Line {line_num} missing fields: {missing}")
                    return False
    except json.JSONDecodeError as e:
        print(f"   ✗ Invalid JSON in chunks.jsonl: {e}")
        return False

    print(f"   ✓ Valid JSONL: {len(chunks)} chunks")

    # Show first chunk summary
    if chunks:
        c = chunks[0]
        print(f"   ✓ First chunk: {c['chunk_id']} (pages {c['page_start']}-{c['page_end']}, "
              f"chars {c['char_start']}-{c['char_end']}, {len(c['text'])} text chars)")

    return True

def curl_get_list(file_id):
    """Verify GET /rag/list using curl."""
    print(f"\n[4] Verifying GET /rag/list...")
    cmd = [
        "curl", "-s", "-X", "GET",
        f"{BASE_URL}/rag/list?session_id={SESSION_ID}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ✗ List failed: {result.stderr}")
        return False

    try:
        data = json.loads(result.stdout)
        file_record = None
        for f in data.get("files", []):
            if f["id"] == file_id:
                file_record = f
                break

        if not file_record:
            print(f"   ✗ File not found in list")
            return False

        print(f"   ✓ Found in list")
        print(f"   ✓ Status: {file_record['status']}")
        print(f"   ✓ Page count: {file_record['page_count']}")
        print(f"   ✓ Char count: {file_record['char_count']}")
        print(f"   ✓ Chunk count: {file_record['chunk_count']}")

        # Verify status
        if file_record["status"] != "chunked":
            print(f"   ✗ Status is '{file_record['status']}', expected 'chunked'")
            return False

        if file_record["chunk_count"] is None or file_record["chunk_count"] == 0:
            print(f"   ✗ Chunk count is {file_record['chunk_count']}, expected > 0")
            return False

        return True
    except json.JSONDecodeError:
        print(f"   ✗ Invalid JSON response: {result.stdout}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("RAG Phase 1B Smoketest")
    print("=" * 60)

    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(TEST_CONTENT)
        test_file = f.name

    try:
        # Test 1: Upload
        file_id = curl_post_upload(test_file)
        if not file_id:
            print("\n✗ FAILED at upload stage")
            return 1

        # Test 2: Process
        process_result = curl_post_process(file_id)
        if not process_result:
            print("\n✗ FAILED at process stage")
            return 1

        # Test 3: Chunks file
        chunks_path = process_result.get("chunks_path")
        if not verify_chunks_file(chunks_path):
            print("\n✗ FAILED at chunks file validation")
            return 1

        # Test 4: List API
        if not curl_get_list(file_id):
            print("\n✗ FAILED at list API validation")
            return 1

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0

    finally:
        Path(test_file).unlink(missing_ok=True)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
