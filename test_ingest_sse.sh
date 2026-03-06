#!/bin/bash
# Test script for RAG ingest SSE endpoints

set -e

SESSION_ID="test_ingest_$(date +%s)"
BASE_URL="http://localhost:8000"

echo "=== RAG Ingest SSE Test ==="
echo "Session ID: $SESSION_ID"
echo ""

# Step 1: Upload test files
echo "1. Uploading test files..."
FILE1_RESP=$(curl -s -F "session_id=$SESSION_ID" -F "file=@test_document.md" "$BASE_URL/rag/upload")
FILE1_ID=$(echo "$FILE1_RESP" | jq -r '.file.id')
echo "   Uploaded file 1: $FILE1_ID"

# Upload a second file if test_extraction.txt exists
if [ -f "test_extraction.txt" ]; then
    FILE2_RESP=$(curl -s -F "session_id=$SESSION_ID" -F "file=@test_extraction.txt" "$BASE_URL/rag/upload")
    FILE2_ID=$(echo "$FILE2_RESP" | jq -r '.file.id')
    echo "   Uploaded file 2: $FILE2_ID"
    FILE_IDS="[\"$FILE1_ID\", \"$FILE2_ID\"]"
else
    FILE_IDS="[\"$FILE1_ID\"]"
fi

echo ""

# Step 2: Start ingest job
echo "2. Starting ingest job..."
INGEST_RESP=$(curl -s -X POST "$BASE_URL/rag/ingest_start" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"file_ids\": $FILE_IDS, \"force\": false}")
echo "   Response: $INGEST_RESP"
echo ""

# Step 3: Monitor SSE events (with timeout)
echo "3. Monitoring ingest events (SSE stream)..."
echo "   Press Ctrl+C to stop monitoring"
echo ""

timeout 60s curl -N "$BASE_URL/rag/ingest_events?session_id=$SESSION_ID" 2>/dev/null | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        # Extract JSON from "data: {...}" line
        json_data="${line#data: }"
        echo "   Event: $json_data" | jq '.'

        # Check if done/error/cancelled
        state=$(echo "$json_data" | jq -r '.state')
        if [[ "$state" == "done" ]] || [[ "$state" == "error" ]] || [[ "$state" == "cancelled" ]]; then
            echo ""
            echo "   Stream ended with state: $state"
            break
        fi
    fi
done

echo ""
echo "4. Verifying final file status..."
curl -s "$BASE_URL/rag/list?session_id=$SESSION_ID" | jq '.files[] | {id, original_name, status}'

echo ""
echo "=== Test Complete ==="
