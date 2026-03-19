"""
tests/test_notes.py
Unit tests for Phase 02.1 Notes and Reminders endpoints.

Tests: add note, add reminder, list notes, get due reminders, update note, delete note.
"""
import pytest


# ---------------------------------------------------------------------------
# Test: Add plain note
# ---------------------------------------------------------------------------

def test_add_note(client):
    """POST /notes/add with note_type='note' returns 201 with correct fields."""
    response = client.post("/notes/add", json={
        "content": "Buy milk for test_add_note",
        "note_type": "note"
    })
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["content"] == "Buy milk for test_add_note"
    assert data["note_type"] == "note"
    assert data["color"] == "default"
    assert data["pinned"] == 0
    assert data["dismissed"] == 0
    assert "id" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# Test: Add reminder
# ---------------------------------------------------------------------------

def test_add_reminder(client):
    """POST /notes/add with note_type='reminder' and due_at returns 201."""
    response = client.post("/notes/add", json={
        "content": "Call dentist for test_add_reminder",
        "note_type": "reminder",
        "due_at": "2030-01-01T09:00:00+00:00"
    })
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["note_type"] == "reminder"
    assert data["due_at"] is not None
    assert "2030-01-01" in data["due_at"]


# ---------------------------------------------------------------------------
# Test: List notes
# ---------------------------------------------------------------------------

def test_list_notes(client):
    """GET /notes/list returns all non-dismissed notes."""
    # Create two distinct notes
    client.post("/notes/add", json={"content": "Note Alpha for list test", "note_type": "note"})
    client.post("/notes/add", json={"content": "Note Beta for list test", "note_type": "note"})

    response = client.get("/notes/list")
    assert response.status_code == 200
    notes = response.json()
    assert isinstance(notes, list)
    contents = [n["content"] for n in notes]
    assert "Note Alpha for list test" in contents
    assert "Note Beta for list test" in contents


# ---------------------------------------------------------------------------
# Test: Get due reminders
# ---------------------------------------------------------------------------

def test_get_due_reminders(client):
    """GET /notes/due returns only past-due undismissed reminders."""
    # Past reminder — should appear in /due
    r1 = client.post("/notes/add", json={
        "content": "Overdue reminder for due test",
        "note_type": "reminder",
        "due_at": "2020-01-01T09:00:00+00:00"
    })
    assert r1.status_code == 201

    # Future reminder — must NOT appear in /due
    client.post("/notes/add", json={
        "content": "Future reminder for due test",
        "note_type": "reminder",
        "due_at": "2099-12-31T09:00:00+00:00"
    })

    response = client.get("/notes/due")
    assert response.status_code == 200
    due = response.json()
    assert isinstance(due, list)
    contents = [n["content"] for n in due]
    assert "Overdue reminder for due test" in contents
    assert "Future reminder for due test" not in contents


# ---------------------------------------------------------------------------
# Test: Update note
# ---------------------------------------------------------------------------

def test_update_note(client):
    """PATCH /notes/{id} updates note content."""
    create_resp = client.post("/notes/add", json={
        "content": "Original content for update test",
        "note_type": "note"
    })
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    update_resp = client.patch(f"/notes/{note_id}", json={"content": "Updated content for update test"})
    assert update_resp.status_code == 200, f"Expected 200, got {update_resp.status_code}: {update_resp.text}"
    data = update_resp.json()
    assert data["content"] == "Updated content for update test"
    assert data["id"] == note_id


# ---------------------------------------------------------------------------
# Test: Delete note
# ---------------------------------------------------------------------------

def test_delete_note(client):
    """DELETE /notes/{id} removes the note; it no longer appears in /list."""
    create_resp = client.post("/notes/add", json={
        "content": "Note to delete for delete test",
        "note_type": "note"
    })
    assert create_resp.status_code == 201
    note_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/notes/{note_id}")
    assert delete_resp.status_code == 200
    data = delete_resp.json()
    assert data["deleted"] == note_id

    # Verify note no longer appears in list
    list_resp = client.get("/notes/list")
    assert list_resp.status_code == 200
    ids = [n["id"] for n in list_resp.json()]
    assert note_id not in ids
