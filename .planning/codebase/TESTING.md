# Testing Patterns

**Analysis Date:** 2026-03-14

## Test Framework

**Runner:**
- `unittest` (Python standard library) with `unittest.mock`
- No pytest configuration detected
- Tests runnable via: `python -m unittest tests.<module> -v` or `python -m pytest tests/ -v`

**Assertion Library:**
- `unittest.TestCase` methods: `assertEqual()`, `assertTrue()`, `assertFalse()`, `assertIsNone()`, `assertIn()`, `assertRaises()`
- Plain `assert` statements in pytest-style tests (e.g., `test_voice_stt.py`)

**Run Commands:**
```bash
python -m unittest tests.test_assist_router -v          # Run single test module
python -m unittest discover -s tests -p "test_*.py" -v  # Run all tests
python -m pytest tests/ -v                               # Alternative (if pytest installed)
```

**Coverage:**
- No coverage tool configured
- No coverage requirements enforced

## Test File Organization

**Location:**
- Co-located in `tests/` directory (separate from source)
- Pattern: `tests/test_<module>.py` mirrors `app/<module>.py`
- Examples:
  - `tests/test_assist_router.py` → tests `app/assist.py`
  - `tests/test_wakeword_ws.py` → tests `app/wakeword.py`
  - `tests/test_voice_stt.py` → tests `app/voice.py`

**Naming:**
- Test classes: `Test<Component>` (PascalCase)
- Test methods: `test_<scenario>` (snake_case)
- Example: `TestParseNativeCall`, `test_format_b_toggle_off`

**File Structure:**
```
tests/
├── __init__.py
├── test_assist_router.py      # Assist mode parsing, heuristic fallback, executor
├── test_wakeword_ws.py         # Wakeword detector frame feeding, trigger logic
├── test_voice_stt.py           # Voice transcription env var handling
├── test_wakeword_preload.py    # Wakeword model preloading
├── test_light_state.py         # Light state queries
├── test_system_stats.py        # System stats endpoint
└── test_ha_controls.py         # Home Assistant control endpoints
```

## Test Structure

**Suite Organization:**
```python
class TestParseNativeCall(unittest.TestCase):
    """Tests for _parse_native_call covering all formats."""

    def test_format_b_toggle_off(self):
        content = "<start_function_call>call:toggle_lights{state:<escape>off<escape>}"
        result = _parse_native_call(content)
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "toggle_lights")
        self.assertEqual(result["arguments"]["state"], "off")

    def test_format_b_toggle_on(self):
        content = "<start_function_call>call:toggle_lights{state:<escape>on<escape>}"
        result = _parse_native_call(content)
        self.assertIsNotNone(result)
        self.assertEqual(result["arguments"]["state"], "on")
```

**Patterns:**
- **Setup:** `setUp(self)` method for test initialization
- **Teardown:** `tearDown(self)` method for cleanup (rarely used)
- **Assertion:** Direct method calls on `self`
- **Skip decorators:** `@unittest.skipUnless(PHASE >= 2, "Phase 2 only")`

**Setup Methods:**
```python
def setUp(self):
    # Reset module-level HA config to non-empty so guards pass
    assist._ha_url = "http://homeassistant.local:8123"
    assist._ha_token = "test_token"
    assist._light_entity = "light.bedroom_light"
```

**Environment Patching:**
```python
def setUp(self):
    # Clear env var before each test
    import os
    os.environ.pop("LOCALIS_VOICE_KEY", None)
```

## Mocking

**Framework:**
- `unittest.mock.AsyncMock`, `patch()`, `MagicMock()`
- Heavy dependencies stubbed at module level before import

**Patterns:**

**AsyncMock for async functions:**
```python
def test_toggle_on_calls_ha(self):
    tc = {"name": "toggle_lights", "arguments": {"state": "on"}}
    with patch("app.assist.ha_call_service", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {}
        result = self._run(_execute_tool_call(tc))
    mock_svc.assert_called_once_with("light", "turn_on", {"entity_id": "light.bedroom_light"})
    self.assertIn("ON", result["response"])
```

**Module-level stubbing (before import):**
```python
sys.modules.setdefault("llama_cpp", MagicMock())
sys.modules.setdefault("httpx", __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock())
sys.modules["numpy"] = _NumpyStub("numpy")
```

**Environment patching for constants:**
```python
def _reload_voice(env: dict):
    """Re-import app.voice with a custom environment so module-level constants
    (WAKEWORD_TRANSLATE) are evaluated fresh."""
    for key in list(sys.modules.keys()):
        if key == "app.voice" or key.startswith("app.voice."):
            del sys.modules[key]

    with patch.dict("os.environ", env, clear=False):
        import app.voice as voice_mod
    return voice_mod
```

**Mock return values:**
```python
mock_model = MagicMock()
mock_model.transcribe.return_value = ([_make_segment("turn off the light")], MagicMock())
```

**Side effects for exceptions:**
```python
mock_svc.side_effect = RuntimeError("connection refused")
```

## Fixtures and Factories

**Test Data:**
```python
def _make_mock_model(score: float):
    """Return a minimal model stub that predict() returns score for hey_jarvis."""
    return types.SimpleNamespace(predict=lambda x: {"hey_jarvis": score})

def _make_mock_ws(host: str, query_key: str = ""):
    """Return a minimal websocket stub for _ws_auth tests."""
    ws = types.SimpleNamespace(
        client=types.SimpleNamespace(host=host),
        query_params={"key": query_key} if query_key else {},
    )
    return ws
```

**Helper Functions:**
```python
def run_async(coro):
    """Run a coroutine synchronously (Python 3.7+)."""
    return asyncio.run(coro)

def _make_segment(text: str):
    seg = MagicMock()
    seg.text = text
    return seg
```

**Location:**
- Helpers defined at module level in test file
- Prefix with `_` to indicate they're test utilities, not production code

## Coverage

**Requirements:**
- None enforced by CI/CD
- Manual test coverage via developer review

**View Coverage:**
```bash
# If coverage.py installed:
coverage run -m unittest discover -s tests
coverage report
coverage html  # Generate HTML coverage report
```

## Test Types

**Unit Tests:**
- **Scope:** Individual functions without external dependencies
- **Approach:** Mock external calls (HA, web search, model inference)
- **Examples:**
  - `test_assist_router.py` — parsing logic, no live HA
  - `test_wakeword_ws.py` — frame feeding, detector logic, no audio hardware
  - `test_voice_stt.py` — transcription env vars, no Whisper model

**Integration Tests:**
- **Scope:** Multiple components working together
- **Approach:** Minimal mocking; test real data flow
- **Examples:** (Not extensively used in this codebase)
  - Testing full chat pipeline from user input to database

**E2E Tests:**
- **Framework:** None (manual testing only)
- **Approach:** Start server, open browser, test user flows
- **Known flows:**
  - Demo path: Launch → "Hey Jarvis" → STT → "light banda kar" → HA light off → green "Done" status

## Common Patterns

**Async Testing:**
```python
def _run(self, coro):
    return asyncio.run(coro)

def test_toggle_on_calls_ha(self):
    tc = {"name": "toggle_lights", "arguments": {"state": "on"}}
    with patch("app.assist.ha_call_service", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {}
        result = self._run(_execute_tool_call(tc))
```

**Error Testing:**
```python
def test_ha_connect_error_returns_friendly_message(self):
    # Use RuntimeError (always in the catch list) to simulate unreachable HA
    tc = {"name": "toggle_lights", "arguments": {"state": "on"}}
    with patch("app.assist.ha_call_service", new_callable=AsyncMock) as mock_svc:
        mock_svc.side_effect = RuntimeError("connection refused")
        result = self._run(_execute_tool_call(tc))
    self.assertIn("Could not reach", result["response"])
```

**None/Optional Testing:**
```python
def test_unrecognised_content_returns_none(self):
    content = "I cannot help with that."
    result = _parse_native_call(content)
    self.assertIsNone(result)

def test_never_returns_none(self):
    for msg in ["", "blah blah", "x", "42"]:
        result = _heuristic_fallback(msg)
        self.assertIsNotNone(result, f"Should not return None for: {msg!r}")
```

**Boundary Testing:**
```python
def test_brightness_clamp_upper(self):
    result = _heuristic_fallback("brightness 150%")
    self.assertEqual(result["arguments"]["brightness_pct"], 100)

def test_kelvin_clamp_lower(self):
    result = _heuristic_fallback("1000k")
    self.assertEqual(result["arguments"]["color_temp_kelvin"], 1500)
```

**Conditional Tests (Feature Gates):**
```python
@unittest.skipUnless(ASSIST_PHASE >= 2, "Phase 2 only")
def test_brightness_percent(self):
    result = _heuristic_fallback("set brightness to 40%")
    self.assertEqual(result["name"], "toggle_lights")
    self.assertEqual(result["arguments"]["brightness_pct"], 40)
```

## Test Execution Examples

**Run single test class:**
```bash
python -m unittest tests.test_assist_router.TestParseNativeCall -v
```

**Run single test method:**
```bash
python -m unittest tests.test_assist_router.TestParseNativeCall.test_format_b_toggle_off -v
```

**Run all tests in module:**
```bash
python -m unittest tests.test_assist_router -v
```

**Run all tests:**
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Important Test Patterns

**Import Isolation:**
- Tests stub heavy dependencies (`llama_cpp`, `openwakeword`, `httpx`) before importing modules
- Prevents test failures due to missing optional packages
- Example from `test_wakeword_ws.py`:
```python
for stub in ("sounddevice", "openwakeword", "openwakeword.model",
             "openwakeword.utils", "httpx"):
    if stub not in sys.modules:
        sys.modules[stub] = types.ModuleType(stub)
```

**Environment Variable Isolation:**
- Tests that depend on env vars reload modules after patching
- Ensures module-level constants are re-evaluated with test env
- Example from `test_voice_stt.py`:
```python
def _reload_voice(env: dict):
    """Re-import app.voice with a custom environment..."""
    for key in list(sys.modules.keys()):
        if key == "app.voice" or key.startswith("app.voice."):
            del sys.modules[key]

    with patch.dict("os.environ", env, clear=False):
        import app.voice as voice_mod
    return voice_mod
```

**No Live External Dependencies:**
- Never call real APIs (HA, web search, Whisper model)
- Always mock external calls
- Tests pass offline, without HA instance running

**Assertion Readability:**
- Use descriptive assertion messages
- Example: `self.assertIsNotNone(result, f"Should not return None for: {msg!r}")`

## Testing Quick Reference

| What to Test | How | Example |
|--------------|-----|---------|
| Function parsing | Direct call + assertions | `_parse_native_call()` |
| State transitions | Setup state, call func, verify state changed | Wakeword trigger/cooldown |
| Error handling | Mock exception, verify response | HA unreachable |
| Boundary values | Clamp, overflow cases | Brightness 150% → 100% |
| Optional features | @skipUnless decorator | Phase 2 features only |
| Async functions | asyncio.run() or async test | Tool execution |
| Module initialization | Reload with patched env | WAKEWORD_TRANSLATE flag |

---

*Testing analysis: 2026-03-14*
