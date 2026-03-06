#!/usr/bin/env bash
# scripts/smoke_assist.sh
# Smoke test for Assist Mode endpoints.
#
# Usage:
#   LOCALIS_HA_URL=http://homeassistant.local:8123 \
#   LOCALIS_HA_TOKEN=your_token \
#   LOCALIS_LIGHT_ENTITY=light.bedroom_light \
#   ./scripts/smoke_assist.sh [BASE_URL]
#
# BASE_URL defaults to http://localhost:8000
# Set LOCALIS_ASSIST_PHASE=2 to also run Phase 2 tests.

set -euo pipefail

BASE="${1:-http://localhost:8000}"
PHASE="${LOCALIS_ASSIST_PHASE:-1}"
FAILURES=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }

assert_http_ok() {
    local label="$1"
    local http_code="$2"
    local body="$3"
    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        green "  PASS [$http_code] $label"
    else
        red "  FAIL [$http_code] $label"
        echo "  Body: $body"
        FAILURES=$((FAILURES + 1))
    fi
}

assert_json_field() {
    local label="$1"
    local body="$2"
    local field="$3"
    local expected="$4"
    local actual
    actual=$(echo "$body" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    keys = '$field'.split('.')
    v = d
    for k in keys:
        v = v[k]
    print(str(v).lower())
except Exception as e:
    print('__error__: ' + str(e))
" 2>/dev/null)

    if [[ "$actual" == *"$expected"* ]]; then
        green "  PASS $label (got: $actual)"
    else
        red "  FAIL $label (expected: '$expected', got: '$actual')"
        FAILURES=$((FAILURES + 1))
    fi
}

post_assist() {
    local msg="$1"
    local tmpfile
    tmpfile=$(mktemp)
    local code
    code=$(curl -s -o "$tmpfile" -w "%{http_code}" \
        -X POST "${BASE}/assist/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": $(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$msg"), \"session_id\": \"smoke_test\"}")
    cat "$tmpfile"
    echo "|||HTTP_CODE=$code"
    rm -f "$tmpfile"
}

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

bold "=== Assist Mode Smoke Tests ==="
echo "  Base URL : $BASE"
echo "  Phase    : $PHASE"
echo ""

# 1. Status endpoint
bold "1. GET /assist/status"
resp=$(curl -s -o /tmp/smoke_status.json -w "%{http_code}" "${BASE}/assist/status")
body=$(cat /tmp/smoke_status.json)
echo "  Response : $body"
assert_http_ok "GET /assist/status" "$resp" "$body"

# Warn if HA not configured (don't fail — server might be in test mode)
ha_configured=$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d.get('ha_configured',False)).lower())" 2>/dev/null || echo "false")
if [[ "$ha_configured" != "true" ]]; then
    printf '\033[33m  WARN: ha_configured=false — /assist/chat calls will return 503\033[0m\n'
fi
echo ""

# 2. Turn ON
bold "2. POST /assist/chat — turn on the bedroom light"
raw=$(post_assist "turn on the bedroom light")
body=$(echo "$raw" | grep -v "|||HTTP_CODE=" || true)
code=$(echo "$raw" | grep "|||HTTP_CODE=" | sed 's/.*=//')
echo "  Response : $body"
assert_http_ok "POST /assist/chat (turn on)" "$code" "$body"
if [[ "$code" -eq 200 ]]; then
    assert_json_field "tool_call.name == toggle_lights" "$body" "tool_call.name" "toggle_lights"
    assert_json_field "tool_call.arguments contains 'on'" "$body" "tool_call.arguments.state" "on"
fi
echo ""

# 3. Turn OFF
bold "3. POST /assist/chat — turn off the bedroom light"
raw=$(post_assist "turn off the bedroom light")
body=$(echo "$raw" | grep -v "|||HTTP_CODE=" || true)
code=$(echo "$raw" | grep "|||HTTP_CODE=" | sed 's/.*=//')
echo "  Response : $body"
assert_http_ok "POST /assist/chat (turn off)" "$code" "$body"
if [[ "$code" -eq 200 ]]; then
    assert_json_field "tool_call.name == toggle_lights" "$body" "tool_call.name" "toggle_lights"
    assert_json_field "tool_call.arguments contains 'off'" "$body" "tool_call.arguments.state" "off"
fi
echo ""

# 4. Unclear intent
bold "4. POST /assist/chat — unclear intent"
raw=$(post_assist "order me a large pepperoni pizza")
body=$(echo "$raw" | grep -v "|||HTTP_CODE=" || true)
code=$(echo "$raw" | grep "|||HTTP_CODE=" | sed 's/.*=//')
echo "  Response : $body"
assert_http_ok "POST /assist/chat (unclear)" "$code" "$body"
if [[ "$code" -eq 200 ]]; then
    assert_json_field "tool_call.name == intent_unclear" "$body" "tool_call.name" "intent_unclear"
fi
echo ""

# 5. Phase 2: brightness
if [[ "$PHASE" -ge 2 ]]; then
    bold "5. POST /assist/chat — set brightness to 40% [Phase 2]"
    raw=$(post_assist "set the bedroom light brightness to 40%")
    body=$(echo "$raw" | grep -v "|||HTTP_CODE=" || true)
    code=$(echo "$raw" | grep "|||HTTP_CODE=" | sed 's/.*=//')
    echo "  Response : $body"
    assert_http_ok "POST /assist/chat (brightness)" "$code" "$body"
    if [[ "$code" -eq 200 ]]; then
        assert_json_field "tool_call.name == toggle_lights" "$body" "tool_call.name" "toggle_lights"
    fi
    echo ""
fi

# 6. Get state
bold "6. POST /assist/chat — get light state"
raw=$(post_assist "what is the bedroom light status")
body=$(echo "$raw" | grep -v "|||HTTP_CODE=" || true)
code=$(echo "$raw" | grep "|||HTTP_CODE=" | sed 's/.*=//')
echo "  Response : $body"
assert_http_ok "POST /assist/chat (get state)" "$code" "$body"
if [[ "$code" -eq 200 ]]; then
    assert_json_field "tool_call.name == get_light_state" "$body" "tool_call.name" "get_light_state"
fi
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

bold "=== Summary ==="
if [[ "$FAILURES" -eq 0 ]]; then
    green "All tests passed."
    exit 0
else
    red "$FAILURES test(s) failed."
    exit 1
fi
