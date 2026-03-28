# Spec: Single-Model LLM-Driven Tool Calling

**Date:** 2026-03-28
**Status:** Approved for planning
**Scope:** Major architectural overhaul — removes FunctionGemma router, collapses all input paths to one Qwen3.5-driven tool-calling pipeline.

---

## 1. Problem Statement

Current architecture has three core issues:

1. **Two models, two locks** — FunctionGemma (router) + Qwen3.5 (generator) run sequentially, both holding `MODEL_LOCK`. Wasted VRAM and latency.
2. **Forced tool execution** — web search fires on every message when "enabled", regardless of relevance. Notes triggered by fragile regex. HA locked behind a separate FunctionGemma path.
3. **Memory framing bug** — `[USER IDENTITY (Tier-A)]` injected into system prompt without clear attribution. Models misread it as their own identity ("I am Rushi").

---

## 2. Goal

Replace the dual-model pipeline with a single Qwen3.5 agentic loop:
- Model receives available tools as permissions
- Model decides which tools to call (zero to many), in one round
- Tools execute in parallel
- Model generates final response with tool results in context
- All input paths (text, voice, wakeword) use this same pipeline

---

## 3. Architecture: Before vs After

### Before
```
User message
    │
    ├─[assist_mode=true]──► FunctionGemma (ASSIST_MODEL_LOCK)
    │                           └─► HA HTTP calls ──► stream response
    │
    └─[normal]──► Regex/Frontend tool selection
                      └─► Execute selected tools (parallel)
                              └─► Qwen3.5 generator (MODEL_LOCK) ──► stream
```

### After
```
User message (text / voice / wakeword)
    │
    └──► Qwen3.5 Pass 1: Tool Decision (MODEL_LOCK, non-streaming)
             │  tools=[web_search, home.set_light, home.get_device_state,
             │          notes.add, notes.retrieve, memory.retrieve, memory.write]
             │
             ├─[finish_reason="tool_calls"]──► Execute tool_calls in parallel (no lock)
             │                                     └─► Inject tool results as `role:tool` messages
             │                                             └─► Qwen3.5 Pass 2 (MODEL_LOCK, streaming)
             │
             └─[finish_reason="stop"]──► Qwen3.5 already answered, stream directly
```

---

## 4. Tool Definitions

All tools use the OpenAI function-calling schema (llama-cpp-python native format).

### 4.1 `web.search`
```json
{
  "name": "web.search",
  "description": "Search the web for real-time information: current events, live scores, prices, news, weather. Do NOT use for things you can answer from knowledge.",
  "parameters": {
    "query": { "type": "string", "description": "Specific, time-anchored search query." }
  }
}
```

### 4.2 `home.set_light`
```json
{
  "name": "home.set_light",
  "description": "Control the bedroom light (entity: light.rishi_room_light). Use when user explicitly asks to control the light.",
  "parameters": {
    "state":      { "type": "string", "enum": ["on", "off"] },
    "brightness": { "type": "integer", "description": "0-255. Omit to keep current.", "minimum": 0, "maximum": 255 },
    "color_name": { "type": "string",  "description": "Color name e.g. 'red', 'blue', 'warm white'. Omit to keep current." }
  },
  "required": ["state"]
}
```
**Note:** Entity ID hardcoded to `light.rishi_room_light` for now. See CLAUDE.md for multi-device expansion plan.

### 4.3 `home.get_device_state`
```json
{
  "name": "home.get_device_state",
  "description": "Get the current state of a home device.",
  "parameters": {
    "entity_id": { "type": "string", "description": "HA entity ID e.g. 'light.rishi_room_light'" }
  },
  "required": ["entity_id"]
}
```

### 4.4 `notes.add`
```json
{
  "name": "notes.add",
  "description": "Save a note or reminder. Use when user says 'remind me', 'add note', 'note this', 'jot down'.",
  "parameters": {
    "content":   { "type": "string" },
    "note_type": { "type": "string", "enum": ["note", "reminder"], "default": "note" },
    "due_at":    { "type": "string", "description": "ISO8601 UTC datetime for reminders. Null for plain notes." }
  },
  "required": ["content"]
}
```

### 4.5 `notes.retrieve`
```json
{
  "name": "notes.retrieve",
  "description": "Retrieve the user's saved notes and reminders. Use when user asks about their notes, tasks, or upcoming reminders.",
  "parameters": {
    "filter": { "type": "string", "enum": ["all", "notes", "reminders", "due_soon"], "default": "all" }
  }
}
```

### 4.6 `memory.retrieve`
```json
{
  "name": "memory.retrieve",
  "description": "Search the user's personal memory for relevant facts, preferences, and history.",
  "parameters": {
    "query": { "type": "string" }
  },
  "required": ["query"]
}
```

### 4.7 `memory.write`
```json
{
  "name": "memory.write",
  "description": "Save a new fact about the user to memory. Only use when user explicitly asks you to remember something.",
  "parameters": {
    "key":   { "type": "string", "description": "Category key e.g. 'preference', 'fact'" },
    "value": { "type": "string" }
  },
  "required": ["key", "value"]
}
```

---

## 5. System Prompt Design

### 5.1 Structure (assembled dynamically in `chat_endpoint`)

```
{datetime_line}

{localis_identity_and_tool_guidance}

{user_memory_block}
```

### 5.2 `datetime_line`
Prepended dynamically every request:
```python
from datetime import datetime
now_str = datetime.now().strftime("%A, %B %d, %Y %H:%M")
datetime_line = f"Current date and time: {now_str}"
```

### 5.3 `PROMPT_DEFAULT` (new)
```
You are Localis, a private AI assistant running entirely on the user's own hardware. You are helpful, concise, and honest.

Tool usage guidelines:
- Use web.search for live/recent information only (news, scores, prices, current events). Do not search for things you already know.
- Use home.set_light or home.get_device_state only when the user explicitly asks to control or check a device.
- Use notes.add when the user asks to save a note, reminder, or task.
- Use notes.retrieve when the user asks about their saved notes or upcoming reminders.
- Use memory.retrieve when a query seems personal and context from past conversations would help.
- Use memory.write only when the user explicitly asks you to remember something.
- If no tool is needed, answer directly.

You do not have internet access unless a web.search tool result is provided. Never fabricate search results.
```

### 5.4 Memory block (fixed framing)
`format_identity_for_prompt()` updated to:
```python
lines = ["[ABOUT THE USER YOU ARE TALKING TO — not about yourself]"]
for key in sorted(identity.keys()):
    label = key.replace("_", " ").lower()
    lines.append(f"* The user's {label} is: {val}")
```

Result injected after the system prompt body, clearly attributing all facts to the user, not the assistant.

---

## 6. Inference Settings

Added to all `create_chat_completion` calls:
```python
presence_penalty=1.5  # Qwen3.5 model card recommendation — prevents repetition loops
```

---

## 7. Think Mode — Qwen3.5 Native Tokens

Replace system-prompt injection with Qwen3.5's native mechanism.

When `think_mode=True`, append `/think` to the user message before Pass 1:
```python
if req.think_mode:
    user_msg_for_model = user_msg + " /think"
else:
    user_msg_for_model = user_msg + " /no_think"
```

The chat template handles the rest. The 200-word hint in the system prompt is removed.

---

## 8. Two-Pass MODEL_LOCK Flow

```python
# Pass 1 — Tool Decision (non-streaming)
with MODEL_LOCK:
    response = current_model.create_chat_completion(
        messages=messages,
        tools=tool_definitions,        # all permitted tools
        tool_choice="auto",
        max_tokens=req.max_tokens,     # full budget — model may answer directly without tools
        temperature=req.temperature,
        presence_penalty=1.5,
        stream=False,
    )

choice = response["choices"][0]

if choice["finish_reason"] == "tool_calls":
    # Execute tools in parallel (no lock held)
    tool_results = await asyncio.gather(*[execute_tool(tc) for tc in choice["message"]["tool_calls"]])

    # Build tool result messages (role: "tool")
    tool_messages = [
        {"role": "tool", "tool_call_id": tc["id"], "content": result}
        for tc, result in zip(choice["message"]["tool_calls"], tool_results)
    ]

    # Append assistant tool-call message + tool results to messages
    messages.append(choice["message"])          # role: assistant, with tool_calls
    messages.extend(tool_messages)

    # Pass 2 — Final Response (streaming)
    with MODEL_LOCK:
        stream = current_model.create_chat_completion(
            messages=messages,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            presence_penalty=1.5,
            stream=True,
        )
        # ... stream tokens to client

else:
    # Model answered directly in Pass 1 — emit content as synthetic SSE stream.
    # No second model call. Chunk the content into ~4-char pieces to preserve
    # streaming UX, then emit the stop event.
    content = choice["message"]["content"] or ""
    for chunk in [content[i:i+4] for i in range(0, len(content), 4)]:
        yield f"data: {json.dumps({'content': chunk, 'stop': False})}\n\n"
    yield f"data: {json.dumps({'content': '', 'stop': True})}\n\n"
```

**Lock discipline:** MODEL_LOCK released between Pass 1 and Pass 2. Tool execution happens in the gap with no lock held. This is safe — tools are async I/O (HTTP, SQLite), not model calls.

---

## 9. Tool Permission Gating

Which tools are passed to the model depends on user settings:

| Tool | Condition |
|---|---|
| `web.search` | `web_search_mode == "on"` |
| `home.set_light`, `home.get_device_state` | HA URL + token configured in env |
| `notes.add`, `notes.retrieve` | Always available |
| `memory.retrieve`, `memory.write` | Always available |

RAG is **not** a tool — it remains auto-injected into the system context when indexed files exist for the session (unchanged).

---

## 10. Frontend Changes

### 10.1 Web search mode
- Remove "Auto" option
- Toggle becomes: **Off / On**
- When On: `web_search_mode: "on"` sent in request; `web.search` included in tool definitions
- When Off: `web_search_mode: "off"`; `web.search` excluded

### 10.2 Assist mode button
- Removed entirely from UI (HTML, CSS, JS)
- HA tools are always available when configured — no separate mode needed

### 10.3 `tool_actions` field
- Removed from `ChatRequest` — frontend no longer selects tools
- Model decides based on what's permitted via tool definitions

### 10.4 Tool activity pills

New SSE event emitted immediately after Pass 1 resolves tool_calls (before tool execution):
```json
{"event_type": "tool_start", "tool": "web.search"}
{"event_type": "tool_start", "tool": "home.set_light"}
```
One event per tool call. Frontend animates existing tool pills ("Searching web…", "Controlling lights…") on receipt.

Existing `tool_result` event emitted after execution completes (unchanged format):
```json
{"event_type": "tool_result", "tool": "web.search", "results": [...]}
```

Pass 2 streams in → response appears → pill marks complete.

---

## 11. Backend Removals (`assist.py`)

- Remove: FunctionGemma model loading (`_load_assist_model`, `ASSIST_MODEL`)
- Remove: `ASSIST_MODEL_LOCK`
- Remove: `assist_chat()` function
- Remove: `AssistRequest` model
- **Keep:** `_call_ha_service()`, `_get_ha_state()`, `_build_ha_headers()` — these handle the actual HA HTTP calls and are reused by the new `home.set_light` / `home.get_device_state` tool executors
- Remove: assist mode early-return block from `chat_endpoint` (lines ~978-999)
- Remove: `assist_mode` field from `ChatRequest`

---

## 12. Notes / Memory Tool Migration

### Removed
- Regex-based auto-injection for notes (`_note_add_re`, `_note_retrieve_re`)
- `memory_retrieve` from `effective_tool_actions` auto-inject logic
- `ALLOWED_TOOLS` set — replaced by the tool definitions list

### Added
- `notes.add`, `notes.retrieve`, `memory.retrieve`, `memory.write` are now proper tool definitions passed to Pass 1
- Tool executor in `execute_tool()` handles them by tool name (same underlying logic, new dispatch path)

---

## 13. Error Handling

| Scenario | Handling |
|---|---|
| Tool executor raises exception | Inject `"[TOOL ERROR: {tool_name}] {error}"` as tool result message; model gracefully handles |
| HA unreachable | Return error string as tool result; model informs user |
| Web search returns `ERROR_*` | Pass raw error string to model; model says it couldn't search |
| Pass 1 produces malformed tool_calls JSON | Catch parse error, fall back to Pass 2 with no tool results |
| Model calls unknown tool name | Validate tool names against permitted list; reject unknown calls silently |

---

## 14. Files Changed

| File | Change Type |
|---|---|
| `app/main.py` | Major — rewrite `chat_endpoint`, remove router, add two-pass tool loop, new `PROMPT_DEFAULT` |
| `app/memory_core.py` | Minor — fix `format_identity_for_prompt` framing |
| `app/assist.py` | Medium — strip FunctionGemma, keep HA HTTP helpers |
| `app/static/js/app.js` | Medium — remove assist toggle, simplify web search toggle, tool pill SSE handling |
| `app/templates/index.html` | Minor — remove assist mode button |
| `app/static/css/app.css` | Minor — remove assist mode styles if any |

---

## 15. Out of Scope

- Multi-device HA expansion (tracked in CLAUDE.md)
- Multi-round tool calling (revisit when larger Qwen3.5 variants are stable)
- Finance tool as LLM-callable function (existing finance UI unchanged)
- Test suite updates (separate task after implementation)

---

## 16. Post-Implementation Checklist

- [ ] Delete FunctionGemma GGUF from `~/.local/share/localis/models/`
- [ ] Verify `presence_penalty=1.5` in both Pass 1 and Pass 2
- [ ] Confirm `/think` / `/no_think` tokens work with loaded Qwen3.5 chat template
- [ ] Manual test: "who am I?" → model should say "You are Rishi" not "I am Rushi"
- [ ] Manual test: "light banda kar" → `home.set_light` called, light responds
- [ ] Manual test: "what's the next F1 race?" with web search ON → time-anchored query
- [ ] Manual test: web search OFF → no search, model answers from knowledge
- [ ] Voice / wakeword path still works (routes to same chat_endpoint)
