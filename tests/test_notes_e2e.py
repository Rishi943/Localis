"""
tests/test_notes_e2e.py
Integration tests for Phase 02.1 Notes tool execution pipeline.

Tests: notes.add via HTTP endpoint (tool backing), notes.retrieve via list endpoint,
reminder time storage and due-filter correctness.

Note: notes.add / notes.retrieve are not yet wired into the chat tool_actions pipeline
(that is Phase 02.1 Plan 05 work). These tests validate the underlying endpoint
behaviour that the tool calls will delegate to — they constitute the integration
layer tests between the HTTP API and the SQLite persistence layer.
"""
import pytest


# ---------------------------------------------------------------------------
# Test: notes.add tool backing — note persists to DB via endpoint
# ---------------------------------------------------------------------------

def test_tool_notes_add(client):
    """
    POST /notes/add with note_type='note' persists note to DB.
    This tests the endpoint that backs the notes.add tool call — same code path
    the tool dispatcher invokes once notes.add is registered in the chat pipeline.
    """
    response = client.post("/notes/add", json={
        "content": "E2E integration test note via tool",
        "note_type": "note"
    })
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text[:200]}"
    note_id = response.json()["id"]

    # Verify note was persisted to DB (the key integration assertion)
    list_resp = client.get("/notes/list")
    assert list_resp.status_code == 200
    contents = [n["content"] for n in list_resp.json()]
    assert "E2E integration test note via tool" in contents, \
        f"Note not found in list. Notes: {contents[:5]}"

    # Verify by ID as well
    ids = [n["id"] for n in list_resp.json()]
    assert note_id in ids, f"Note ID {note_id} not found in list"


# ---------------------------------------------------------------------------
# Test: notes.retrieve tool backing — list returns notes without crash
# ---------------------------------------------------------------------------

def test_tool_notes_retrieve(client):
    """
    GET /notes/list returns 200 and a list without crashing.
    This tests the endpoint that backs the notes.retrieve tool call.
    The endpoint must handle 0-or-more notes gracefully.
    """
    response = client.get("/notes/list")
    assert response.status_code == 200, \
        f"notes.retrieve endpoint failed: {response.status_code}: {response.text[:200]}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"


# ---------------------------------------------------------------------------
# Test: Reminder time storage (9 AM default pattern check)
# ---------------------------------------------------------------------------

def test_reminder_default_time(client):
    """
    Reminder stored with 9 AM UTC due_at is retrievable and not yet due.
    Verifies the schema stores due_at correctly and GET /due correctly excludes future reminders.
    """
    future_9am = "2030-06-15T09:00:00+00:00"
    response = client.post("/notes/add", json={
        "content": "Reminder default time test",
        "note_type": "reminder",
        "due_at": future_9am
    })
    assert response.status_code == 201
    note_id = response.json()["id"]
    stored_due_at = response.json()["due_at"]
    assert stored_due_at is not None
    assert "09:00" in stored_due_at, f"Expected 09:00 in due_at, got: {stored_due_at}"

    # Must NOT appear in /due (it's in 2030)
    due_resp = client.get("/notes/due")
    assert due_resp.status_code == 200
    due_ids = [n["id"] for n in due_resp.json()]
    assert note_id not in due_ids, "Future reminder incorrectly returned in /due"
