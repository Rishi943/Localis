"""
Fast-path regex router for voice-sourced Home Assistant light commands.

Intercepts well-known patterns from voice input (wakeword / push-to-talk) and
returns a ready-to-fire HA payload directly, bypassing the LLM entirely.

Caller contract:
    if source == "voice":
        fast = try_fast_path(transcript)
        if fast:
            # POST fast["endpoint"] with fast["payload"] to HA
            return
    # fall through to LLM

Text chat input must NEVER call try_fast_path.
"""

import re

LIGHT_ENTITY = "light.rishi_room_light"

ALLOWED_COLORS = [
    "red", "blue", "green", "yellow", "white",
    "warm white", "cool white", "purple", "pink", "orange",
]

HA_BASE = "/api/services/light"

_ROOM_PREFIX = r"(?:(?:the\s+)?(?:bedroom\s+)?)"

# Toggle patterns
_TURN_ON_RE = re.compile(
    r"(?:(?:turn|switch)\s+on\s+" + _ROOM_PREFIX + r"lights?)"
    r"|(?:" + _ROOM_PREFIX + r"lights?\s+on)"
    r"|(?:lights?\s+on)",
    re.IGNORECASE,
)
_TURN_OFF_RE = re.compile(
    r"(?:(?:turn|switch)\s+off\s+" + _ROOM_PREFIX + r"lights?)"
    r"|(?:" + _ROOM_PREFIX + r"lights?\s+off)"
    r"|(?:lights?\s+off)",
    re.IGNORECASE,
)

# Brightness pattern: "set [the] [room] brightness to N percent" / "brightness N%"
_BRIGHTNESS_RE = re.compile(
    r"(?:set\s+" + _ROOM_PREFIX + r"brightness\s+to\s+(\d{1,3})\s*(?:percent|%))"
    r"|(?:brightness\s+(\d{1,3})\s*(?:percent|%))",
    re.IGNORECASE,
)

# Color pattern: "change [the] [room] [light] [color] to COLOR"
#               "set [the] [room] light to COLOR"
_COLOR_RE = re.compile(
    r"(?:change\s+" + _ROOM_PREFIX + r"(?:light\s+)?(?:color\s+)?to\s+(.+))"
    r"|(?:set\s+" + _ROOM_PREFIX + r"light\s+to\s+(.+))",
    re.IGNORECASE,
)


def try_fast_path(text: str) -> dict | None:
    """
    Try to match a voice transcription against known HA light command patterns.

    Returns {"endpoint": str, "payload": dict} on match, or None if no match.
    Only call this for voice-sourced input (wakeword / push-to-talk).
    """
    normalized = text.strip().lower()

    # 1. Toggle on
    if _TURN_ON_RE.search(normalized):
        print("[FastPath] matched: toggle_on")
        return {
            "endpoint": f"{HA_BASE}/turn_on",
            "payload": {"entity_id": LIGHT_ENTITY},
        }

    # 2. Toggle off
    if _TURN_OFF_RE.search(normalized):
        print("[FastPath] matched: toggle_off")
        return {
            "endpoint": f"{HA_BASE}/turn_off",
            "payload": {"entity_id": LIGHT_ENTITY},
        }

    # 3. Brightness
    m = _BRIGHTNESS_RE.search(normalized)
    if m:
        raw = m.group(1) or m.group(2)
        value = int(raw)
        if not (0 <= value <= 100):
            return None
        print(f"[FastPath] matched: brightness={value}")
        return {
            "endpoint": f"{HA_BASE}/turn_on",
            "payload": {"entity_id": LIGHT_ENTITY, "brightness_pct": value},
        }

    # 4. Color
    m = _COLOR_RE.search(normalized)
    if m:
        color_raw = (m.group(1) or m.group(2) or "").strip()
        if color_raw in ALLOWED_COLORS:
            print(f"[FastPath] matched: color={color_raw}")
            return {
                "endpoint": f"{HA_BASE}/turn_on",
                "payload": {"entity_id": LIGHT_ENTITY, "color_name": color_raw},
            }

    return None


if __name__ == "__main__":
    cases = [
        ("turn on the bedroom light",    {"endpoint": f"{HA_BASE}/turn_on",  "payload": {"entity_id": LIGHT_ENTITY}}),
        ("lights off",                   {"endpoint": f"{HA_BASE}/turn_off", "payload": {"entity_id": LIGHT_ENTITY}}),
        ("set brightness to 50 percent", {"endpoint": f"{HA_BASE}/turn_on",  "payload": {"entity_id": LIGHT_ENTITY, "brightness_pct": 50}}),
        ("set the bedroom brightness to 80%", {"endpoint": f"{HA_BASE}/turn_on", "payload": {"entity_id": LIGHT_ENTITY, "brightness_pct": 80}}),
        ("change color to red",          {"endpoint": f"{HA_BASE}/turn_on",  "payload": {"entity_id": LIGHT_ENTITY, "color_name": "red"}}),
        ("activate the disco mode",      None),
    ]

    passed = 0
    for text, expected in cases:
        result = try_fast_path(text)
        assert result == expected, f"FAIL: {text!r}\n  got:      {result}\n  expected: {expected}"
        print(f"  PASS: {text!r}")
        passed += 1

    print(f"\n{passed}/{len(cases)} tests passed.")
