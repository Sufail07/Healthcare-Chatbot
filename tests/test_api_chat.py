"""Tests for chat API endpoints."""

import pytest


def test_create_conversation(client):
    res = client.post("/api/chat/new")
    assert res.status_code == 200
    data = res.json()
    assert "conversation_id" in data
    assert data["title"] == "New Conversation"


def test_send_message(client, mock_openai):
    # Create conversation first
    conv_res = client.post("/api/chat/new")
    conv_id = conv_res.json()["conversation_id"]

    # Send message
    res = client.post("/api/chat", json={
        "conversation_id": conv_id,
        "message": "I have a headache and fever",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["conversation_id"] == conv_id
    assert data["message"]


def test_send_message_invalid_conversation(client):
    res = client.post("/api/chat", json={
        "conversation_id": "nonexistent-id",
        "message": "test",
    })
    assert res.status_code == 404
