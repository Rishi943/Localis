# Coding Conventions

**Analysis Date:** 2026-03-14

## Naming Patterns

**Files:**
- Snake case: `app/main.py`, `memory_core.py`, `rag_processing.py`
- Prefix modules by function: `setup_wizard.py`, `updater.py`, `rag_vector.py`
- Test files: `test_<module>.py` (e.g., `test_assist_router.py`)

**Functions:**
- Snake case: `parse_bool_env()`, `_load_model_internal()`, `_ws_auth()`
- Private functions prefix with underscore: `_connect_db()`, `_resolve_db_path()`, `_feed_frame()`
- Async functions: `async def web_search()`, `async def _execute_tool_call()`

**Variables:**
- Snake case for globals: `MODEL_LOCK`, `MODELS_DIR`, `DATABASE_PATH`
- Module-level private state prefixed with underscore: `_EMBEDDER`, `_identity_cache`, `_assist_model`
- Constants in UPPER_CASE: `TIER_A_KEYS`, `BULLET_LIST_KEYS`, `EMBEDDING_MODEL_NAME`, `MAX_CACHE_SIZE`

**Types:**
- PascalCase for classes: `MemoryItem`, `MemoryProposal`, `TutorialChatRequest`, `ModelLoadRequest`
- Type hints inline: `def func(name: str, count: int = 5) -> Dict[str, Any]:`
- Union types: `Union[str, int]`, `Optional[str]` (from `typing` module)
- Literal types for enums: `Literal["on", "off"]`, `Literal["tier_a", "tier_b"]`

**JavaScript/CSS:**
- camelCase for functions: `debounce()`, `escapeHtml()`, `parseThinking()`
- PascalCase for IIFE module objects: `Logger`, `UX`
- snake_case for HTML IDs and CSS classes: `#chat-input`, `#voice-status-bar`, `.glass-blur`
- CSS variables: `--glass-bg`, `--text-primary`, `--accent-primary`

## Code Style

**Formatting:**
- No auto-formatter detected (no prettier, eslint, black, or ruff config)
- Implicit style: 4-space indentation (Python), 2-space indentation (JS/CSS)
- Line length: No strict limit enforced; code varies 80–120 chars
- Import statements: Always at top of file, grouped (stdlib → third-party → local)

**Linting:**
- No ESLint or Pylint configuration found
- No automated code review gates

**Indentation:**
- Python: 4 spaces per level
- JavaScript: 2 spaces per level (observed in CSS)
- HTML/CSS: 2 spaces per level

## Import Organization

**Python Order:**
1. Standard library (`os`, `sys`, `logging`, `json`, `pathlib`)
2. Third-party (`fastapi`, `pydantic`, `dotenv`, `httpx`, `numpy`)
3. Local modules (`from . import database`, `from .assist import register_assist`)

**Example from `app/main.py`:**
```python
import os
import gc
import json
import re
import time
import shutil
import asyncio
import threading
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Union, List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import sys

import psutil
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# ... env setup ...

from .setup_wizard import register_setup_wizard
from .updater import register_updater
from .rag import register_rag
from .assist import register_assist
from .voice import register_voice
from .wakeword import register_wakeword

from . import database, memory_core, tools, rag_vector

from llama_cpp import Llama
```

**JavaScript:**
- No formal module system (no ES6 imports/exports)
- Global scope pollution minimized via IIFE modules
- External libs loaded via CDN in HTML (`<script>`)

## Error Handling

**Pattern:**
- Try-except blocks for predictable failures
- Specific exception types where meaningful: `FileNotFoundError`, `HTTPException`, `ValueError`
- Generic `Exception` catch for unexpected errors with logging
- HTTPException for API layer errors with status codes

**Example from `app/main.py`:**
```python
try:
    with MODEL_LOCK:
        loaded_name = _load_model_internal(req.model_name, req.n_gpu_layers, req.n_ctx)
    return {"status": "success", "loaded": loaded_name}
except FileNotFoundError:
    raise HTTPException(status_code=404, detail="Model file not found")
except Exception as e:
    logger.error(f"[System] Load failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

**Logging:**
- Use `logger = logging.getLogger(__name__)` in every module
- Log level gates: `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()`
- Prefix logs with module component: `[Database]`, `[Memory]`, `[Tools]`, `[System]`
- Example: `logger.error(f"[Database] Critical: Database schema mismatch detected (legacy version).")`

**Environment-based Debug Logging:**
- Check `LOCALIS_DEBUG` env var: `DEBUG = parse_bool_env("LOCALIS_DEBUG", False)`
- Example from `main.py`:
```python
def parse_bool_env(name: str, default: bool = False) -> bool:
    """Parse boolean environment variable (1/true/yes = True, 0/false/no = False)"""
    val = os.getenv(name, "").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default

DEBUG = parse_bool_env("LOCALIS_DEBUG", False)
```

**Exception Hierarchy:**
- `HTTPException(status_code, detail)` for API errors
- Custom validation errors via Pydantic `@field_validator`
- `ImportError` for missing dependencies with graceful fallback
- `RuntimeError` for critical failures (e.g., HA connection lost)

## Comments

**When to Comment:**
- Complex algorithms or non-obvious control flow
- Module docstrings at top of file explaining purpose
- Section dividers for logical grouping (e.g., `# --- Parsing tests ---`)
- TODO/FIXME comments for known issues (rarely used in this codebase)

**JSDoc/TSDoc:**
- Python: Used sparingly, mostly function docstrings
- Example from `app/memory_core.py`:
```python
def get_embedder():
    """Lazy loader for SentenceTransformer with failure handling and GPU acceleration."""
```

**JS Comments:**
- Descriptive function headers with intent
- Example from `app.js`:
```javascript
// Logger utility with debug toggle and ring buffer
const Logger = (() => {
    // ...
});
```

**Section Comments:**
- Use `// --- CATEGORY ---` or `# --- CATEGORY ---` to mark sections
- Example: `# --- Parsing tests ---`, `# --- Error handling ---`

## Function Design

**Size:**
- Most functions 10-50 lines
- Router functions in FastAPI stay compact (5-15 lines)
- Complex business logic extracted to pure functions

**Parameters:**
- Avoid long parameter lists (max 5-6 params, then use Pydantic BaseModel)
- Use keyword arguments for optional/boolean params
- Type hints required: `def func(name: str, count: int = 5) -> Dict[str, str]:`
- Async functions accept `Request` as dependency injection for FastAPI

**Return Values:**
- Return type explicitly annotated
- Consistent return types (e.g., always `Dict[str, Any]` or `Optional[str]`)
- Functions that may fail return `None` or raise `HTTPException`

**Example from `app/tools.py`:**
```python
async def web_search(
    query: str,
    provider: Optional[str] = None,
    custom_endpoint: Optional[str] = None,
    custom_api_key: Optional[str] = None
) -> str:
    """Performs a real-time web search..."""
    # ...
```

## Module Design

**Exports:**
- Private functions/vars prefixed with `_` (not re-exported)
- Public API explicit in docstring or module header
- No `__all__` lists (imports follow `from .module import specific_func`)

**Barrel Files:**
- Not used; imports are direct (`from .database import init_db`)
- Main app aggregates all routers via `register_*()` pattern

**Module Scope:**
- Initialization logic at module level only for critical setup
- Example: `logger = logging.getLogger(__name__)` always first
- Environment variables loaded at import time via `_load_secrets()` or dotenv

**Router Pattern:**
- Every feature module exports `register_<feature>(app, config_param)` function
- Registration function sets up module-level state on `app.state`
- Example from `app/assist.py`:
```python
def register_assist(app, models_dir, debug: bool = False):
    """Called from main.py during app construction."""
    global _models_dir, _ha_url, _ha_token, _light_entity, _debug, _assist_model_file
    _models_dir = str(models_dir)
    # ... more setup ...
    app.include_router(router)
```

## Data Structures

**Pydantic Models (FastAPI):**
- Used for all request/response payloads
- Field validation with `@field_validator` decorators
- Examples:
```python
class ModelLoadRequest(BaseModel):
    model_name: str
    n_gpu_layers: int = 35
    n_ctx: int = 4096

class _BrightnessReq(BaseModel):
    value: int = Field(..., ge=0, le=100)
```

**Dataclasses (Python 3.10+):**
- Used for type-safe structures without validation
- Example from `memory_core.py`:
```python
@dataclass
class MemoryItem:
    content: str
    intent: MemoryIntent
    authority: MemoryAuthority
    source: MemorySource
    created_at: datetime
    id: Optional[Union[str, int]] = None
```

**Python Dictionaries:**
- Used for untyped flexible structures (cache, state)
- Prefer `Dict[str, Any]` type hint

**JavaScript Objects:**
- IIFE modules return plain object with methods:
```javascript
const Logger = (() => {
    const buffer = [];
    return {
        debug(category, msg, meta = null) { /* ... */ },
        info(category, msg, meta = null) { /* ... */ },
        getBuffer() { return buffer; }
    };
})();
```

## Global State Management

**Python:**
- Use `threading.Lock()` for shared mutable state: `MODEL_LOCK = threading.Lock()`
- Lazy loading with None check:
```python
_EMBEDDER = None

def get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer(...)
    return _EMBEDDER
```
- Module-level state initialized at import via `register_*()` pattern

**JavaScript:**
- Global `state` object for session/app state
- Global `els` object for cached DOM references
- Feature modules use IIFE to avoid global scope pollution
- Event listeners registered in `startApp()`

## Validation

**Pydantic Field Validation:**
```python
@field_validator("rgb")
@classmethod
def validate_channels(cls, v: list[int]) -> list[int]:
    if not all(0 <= c <= 255 for c in v):
        raise ValueError("Each RGB channel must be in 0-255")
    return v
```

**Custom Validation Functions:**
- Prefix with `_safe_*()` for sanitization (e.g., `_safe_session_id()`)
- Return normalized/safe value or raise exception

**Type Guards (Python):**
- Use `isinstance()` checks before operations
- Optional chaining in JavaScript: `els.ragPanel?.classList.add(...)`

---

*Convention analysis: 2026-03-14*
