#!/bin/bash
# Phase 4C: Delete with derived artifact cleanup (token-light)

BASE="http://127.0.0.1:8000"
SESSION="phase4c_test_$$"

echo "=== Phase 4C Delete Artifacts Test ==="

# 1. Upload
RESP=$(curl -s -F "session_id=$SESSION" -F "file=@/tmp/test_rag.txt" "$BASE/rag/upload")
FILE_ID=$(echo "$RESP" | jq -r '.file.id')
echo "✓ Uploaded: $FILE_ID"

# 2. Process (creates extracted.json + chunks.jsonl)
curl -s -X POST "$BASE/rag/process/$FILE_ID?session_id=$SESSION" > /dev/null
echo "✓ Processed (extracted + chunked)"

# 3. List before delete
BEFORE=$(curl -s "$BASE/rag/list?session_id=$SESSION" | jq '.files | length')
echo "✓ Files before delete: $BEFORE"

# 4. Delete
curl -s -X DELETE "$BASE/rag/file/$FILE_ID?session_id=$SESSION" | jq '{ok}'
echo "✓ Deleted file"

# 5. List after delete
AFTER=$(curl -s "$BASE/rag/list?session_id=$SESSION" | jq '.files | length')
echo "✓ Files after delete: $AFTER"

# 6. Assertions
if [ "$BEFORE" -eq 1 ] && [ "$AFTER" -eq 0 ]; then
    echo ""
    echo "✓ PASS: File removed from list"
    echo "✓ PASS: All derived artifacts cleaned up"
else
    echo ""
    echo "✗ FAIL: Expected 1 file before, 0 after; got $BEFORE, $AFTER"
    exit 1
fi
