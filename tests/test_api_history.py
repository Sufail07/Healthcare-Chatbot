"""Tests for history API endpoints."""


def test_list_conversations_empty(client):
    res = client.get("/api/history")
    assert res.status_code == 200
    assert res.json() == []


def test_list_conversations(client):
    # Create two conversations
    client.post("/api/chat/new")
    client.post("/api/chat/new")

    res = client.get("/api/history")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_conversation(client):
    conv = client.post("/api/chat/new").json()
    res = client.get(f"/api/history/{conv['conversation_id']}")
    assert res.status_code == 200
    assert res.json()["id"] == conv["conversation_id"]
    assert res.json()["messages"] == []


def test_get_conversation_not_found(client):
    res = client.get("/api/history/nonexistent")
    assert res.status_code == 404


def test_delete_conversation(client):
    conv = client.post("/api/chat/new").json()
    res = client.delete(f"/api/history/{conv['conversation_id']}")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"

    # Verify it's gone
    res = client.get(f"/api/history/{conv['conversation_id']}")
    assert res.status_code == 404
