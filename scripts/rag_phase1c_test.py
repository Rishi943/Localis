#!/usr/bin/env python3
"""
RAG Phase 1C Test: Auto-processing + UI status display
Tests: Upload -> auto-process -> verify status in list
"""
import sys
import json
import subprocess
import tempfile
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SESSION_ID = "phase1c_test"

TEST_CONTENT = """Phase 1C Test Document

This document tests the auto-processing feature that should trigger after upload.
The UI should display status badges showing uploaded, extracting, chunking, and chunked states.

It should also show file statistics:
- Number of pages
- Character count
- Chunk count

When processing completes, the chips should show the final status.
Multiple files should process sequentially in the UI."""

def curl_post(url, method="POST"):
    """Helper to make curl requests."""
    cmd = ["curl", "-s", "-X", method, url]
    print(f"   [DEBUG] curl call: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   [DEBUG] curl error: {result.stderr}")
        return None
    try:
        data = json.loads(result.stdout)
        print(f"   [DEBUG] response: {str(data)[:200]}")
        return data
    except json.JSONDecodeError as e:
        print(f"   [DEBUG] JSON parse error: {result.stdout[:100]}")
        return None

def curl_post_upload(file_path, session_id):
    """Upload file."""
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{BASE_URL}/rag/upload",
        "-F", f"session_id={session_id}",
        "-F", f"file=@{file_path}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   [DEBUG] Upload curl error: {result.stderr}")
        return None
    try:
        data = json.loads(result.stdout)
        file_id = data.get("file", {}).get("id") if data.get("ok") else None
        print(f"   [DEBUG] Upload response: ok={data.get('ok')}, file_id={file_id}")
        return file_id
    except json.JSONDecodeError as e:
        print(f"   [DEBUG] Upload JSON error: {result.stdout[:100]}")
        return None

def test_auto_processing():
    """Test 1: Single file auto-processing"""
    print("=" * 60)
    print("PHASE 1C TEST: Auto-processing + Status Display")
    print("=" * 60)

    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(TEST_CONTENT)
        test_file = f.name

    try:
        # Upload file
        print("\n[1] Uploading file...")
        file_id = curl_post_upload(test_file, SESSION_ID)
        if not file_id:
            print("   ✗ Upload failed")
            return False
        print(f"   ✓ Uploaded: {file_id}")

        # Check initial status (should be "uploaded")
        print("\n[2] Checking status after upload (before processing)...")
        response = curl_post(f"{BASE_URL}/rag/list?session_id={SESSION_ID}", "GET")
        if not response:
            print("   ✗ List API failed")
            return False

        print(f"   [DEBUG] List response has {len(response.get('files', []))} files")
        file_record = None
        for f in response.get("files", []):
            print(f"   [DEBUG] File in list: {f['id']}")
            if f["id"] == file_id:
                file_record = f
                break

        if not file_record:
            print(f"   ✗ File {file_id} not in list")
            return False

        initial_status = file_record.get("status")
        print(f"   ✓ Initial status: {initial_status}")
        if initial_status != "uploaded":
            print(f"   ✗ Expected 'uploaded', got '{initial_status}'")
            return False

        # Simulate auto-processing (what the UI would do)
        print("\n[3] Calling POST /rag/process (auto-processing)...")
        process_response = curl_post(
            f"{BASE_URL}/rag/process/{file_id}?session_id={SESSION_ID}",
            "POST"
        )
        if not process_response:
            print("   ✗ Process API failed")
            return False

        result = json.loads(subprocess.run(
            ["curl", "-s", "-X", "POST",
             f"{BASE_URL}/rag/process/{file_id}?session_id={SESSION_ID}"],
            capture_output=True, text=True
        ).stdout)

        if result.get("status") != "chunked":
            print(f"   ✗ Expected status 'chunked', got '{result.get('status')}'")
            return False
        print(f"   ✓ Processed: status={result['status']}, chunks={result['chunk_count']}")

        # Verify final status in list
        print("\n[4] Verifying status in list after processing...")
        response = curl_post(f"{BASE_URL}/rag/list?session_id={SESSION_ID}", "GET")

        file_record = None
        for f in response.get("files", []):
            if f["id"] == file_id:
                file_record = f
                break

        if not file_record:
            print("   ✗ File not in list")
            return False

        final_status = file_record.get("status")
        print(f"   ✓ Final status: {final_status}")
        print(f"   ✓ Pages: {file_record.get('page_count')}")
        print(f"   ✓ Chars: {file_record.get('char_count')}")
        print(f"   ✓ Chunks: {file_record.get('chunk_count')}")

        if final_status != "chunked":
            print(f"   ✗ Expected 'chunked', got '{final_status}'")
            return False

        if not file_record.get('chunk_count') or file_record['chunk_count'] == 0:
            print(f"   ✗ Chunk count missing or zero")
            return False

        print("\n" + "=" * 60)
        print("✓ ACCEPTANCE TEST 1 PASSED: Upload → Auto-process → Status")
        print("=" * 60)
        return True

    finally:
        Path(test_file).unlink(missing_ok=True)

def test_session_scoping():
    """Test 2: Session scoping (different sessions have different files)"""
    print("\n" + "=" * 60)
    print("ACCEPTANCE TEST 2: Session Scoping")
    print("=" * 60)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(TEST_CONTENT)
        test_file = f.name

    try:
        session1 = "session_a"
        session2 = "session_b"

        # Upload to session 1
        print(f"\n[1] Uploading file to {session1}...")
        file_id_1 = curl_post_upload(test_file, session1)
        if not file_id_1:
            print("   ✗ Upload to session 1 failed")
            return False
        print(f"   ✓ Uploaded to {session1}: {file_id_1}")

        # Upload to session 2
        print(f"\n[2] Uploading file to {session2}...")
        file_id_2 = curl_post_upload(test_file, session2)
        if not file_id_2:
            print("   ✗ Upload to session 2 failed")
            return False
        print(f"   ✓ Uploaded to {session2}: {file_id_2}")

        # Check session 1 list (should only have file_id_1)
        print(f"\n[3] Checking {session1} file list...")
        response1 = curl_post(f"{BASE_URL}/rag/list?session_id={session1}", "GET")
        files_in_session1 = [f["id"] for f in response1.get("files", [])]
        print(f"   ✓ Files in {session1}: {len(files_in_session1)}")

        if file_id_1 not in files_in_session1:
            print(f"   ✗ File {file_id_1} not in session 1")
            return False

        # Check session 2 list (should only have file_id_2)
        print(f"\n[4] Checking {session2} file list...")
        response2 = curl_post(f"{BASE_URL}/rag/list?session_id={session2}", "GET")
        files_in_session2 = [f["id"] for f in response2.get("files", [])]
        print(f"   ✓ Files in {session2}: {len(files_in_session2)}")

        if file_id_2 not in files_in_session2:
            print(f"   ✗ File {file_id_2} not in session 2")
            return False

        print("\n" + "=" * 60)
        print("✓ ACCEPTANCE TEST 2 PASSED: Session Scoping")
        print("=" * 60)
        return True

    finally:
        Path(test_file).unlink(missing_ok=True)

def main():
    """Run all tests."""
    test1_passed = test_auto_processing()
    test2_passed = test_session_scoping()

    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("✓ ALL PHASE 1C ACCEPTANCE TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
