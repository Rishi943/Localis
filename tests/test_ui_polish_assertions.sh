#!/usr/bin/env bash
set -e

CSS=/home/rishi/Rishi/AI/Localis/app/static/css/app.css
JS=/home/rishi/Rishi/AI/Localis/app/static/js/app.js
HTML=/home/rishi/Rishi/AI/Localis/app/templates/index.html
PY=/home/rishi/Rishi/AI/Localis/app/main.py

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; exit 1; }

# 1. No legacy CSS variable names in app.css
count=$(grep -cE '\-\-indigo|--glass-bg|--glass-blur|--glass-border|--bg-dark' "$CSS" || true)
[ "$count" -eq 0 ] && pass "no legacy CSS vars" || fail "legacy CSS vars still present ($count lines)"

# 2. No radial-gradient on body/html level
count=$(grep -c 'radial-gradient' "$CSS" || true)
[ "$count" -eq 0 ] && pass "no radial-gradient" || fail "radial-gradient still present ($count lines)"

# 3. clamp() used for sidebar widths
count=$(grep -c 'clamp(' "$CSS" || true)
[ "$count" -gt 0 ] && pass "clamp() present" || fail "clamp() not found in CSS"

# 4. No .voice-status-bar class selectors (only #voice-status-bar ID selectors allowed)
count=$(grep -cE '^\s*\.voice-status-bar' "$CSS" || true)
[ "$count" -eq 0 ] && pass "no .voice-status-bar class selector" || fail ".voice-status-bar class selector present ($count lines)"

# 5. welcome-state present in HTML
count=$(grep -c 'welcome-state' "$HTML" || true)
[ "$count" -gt 0 ] && pass "welcome-state in HTML" || fail "welcome-state missing from HTML"

# 6. addMessageActionChips present in JS
count=$(grep -c 'addMessageActionChips' "$JS" || true)
[ "$count" -gt 0 ] && pass "addMessageActionChips in JS" || fail "addMessageActionChips missing from JS"

# 7. No bare "Jarvis" as assistant name in JS (Hey Jarvis trigger phrase is allowed)
count=$(grep -cE '"Jarvis"' "$JS" | grep -v 'Hey Jarvis\|wakeword\|jarvis_v' || true)
[ "$count" -eq 0 ] && pass "no bare Jarvis name in JS" || fail "bare Jarvis name found in JS ($count lines)"

# 8. GET /api/settings present in main.py
count=$(grep -c 'GET.*api/settings\|@app\.get.*api/settings' "$PY" || true)
[ "$count" -gt 0 ] && pass "GET /api/settings in main.py" || fail "GET /api/settings missing from main.py"

echo ""
echo "ALL ASSERTIONS PASSED"
