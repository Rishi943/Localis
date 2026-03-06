#!/bin/bash
# Phase 4B: Async indexing with status polling + cancel (token-light)

BASE="http://127.0.0.1:8000"
SESSION="phase4b_test_$$"

echo "=== Phase 4B Async Indexing Test ==="

# 1. Upload test file
RESP=$(curl -s -F "session_id=$SESSION" -F "file=@/tmp/test_rag.txt" "$BASE/rag/upload")
FILE_ID=$(echo "$RESP" | jq -r '.file.id')
echo "✓ Uploaded file: $FILE_ID"

# 2. Process file (extract + chunk)
curl -s -X POST "$BASE/rag/process/$FILE_ID?session_id=$SESSION" > /dev/null
echo "✓ Processed file (chunked)"

# 3. Start async indexing
echo ""
echo "1. POST /rag/index_start"
curl -s -X POST "$BASE/rag/index_start?session_id=$SESSION" | jq '{ok, state, message}'

# 4. Poll status immediately
echo ""
echo "2. GET /rag/index_status (poll 1)"
sleep 1
curl -s "$BASE/rag/index_status?session_id=$SESSION" | jq '{ok, state, total_files, done_files, current_file_name}'

# 5. Poll status again
echo ""
echo "3. GET /rag/index_status (poll 2)"
sleep 1
curl -s "$BASE/rag/index_status?session_id=$SESSION" | jq '{ok, state, total_files, done_files, current_file_name}'

# 6. Cancel indexing
echo ""
echo "4. POST /rag/index_cancel"
curl -s -X POST "$BASE/rag/index_cancel?session_id=$SESSION" | jq '{ok, message}'

# 7. Poll after cancel
echo ""
echo "5. GET /rag/index_status (after cancel)"
sleep 1
curl -s "$BASE/rag/index_status?session_id=$SESSION" | jq '{ok, state, total_files, done_files, message}'

echo ""
echo "✓ Phase 4B test sequence complete"
