"""Tests for the diagnosis orchestrator service."""

import pytest
from app.services.diagnosis_service import get_diagnosis, get_direct_diagnosis


@pytest.mark.asyncio
async def test_get_diagnosis_with_symptoms(mock_openai):
    result = await get_diagnosis("I have a headache and fever")
    assert "message" in result
    assert result["message"]  # Non-empty


@pytest.mark.asyncio
async def test_get_diagnosis_no_symptoms(mock_openai):
    # Override parser to return empty list
    mock_empty = type(mock_openai["parser"].chat.completions.create.return_value)()
    mock_empty.choices = [type('Choice', (), {
        'message': type('Msg', (), {'content': '[]'})()
    })()]
    mock_openai["parser"].chat.completions.create.return_value = mock_empty

    result = await get_diagnosis("Hello, how are you?")
    assert result["diagnosis_data"] is None
    assert "symptom" in result["message"].lower() or "describe" in result["message"].lower()


@pytest.mark.asyncio
async def test_get_direct_diagnosis(mock_openai):
    result = await get_direct_diagnosis(["headache", "high_fever"])
    assert result["disease"] != "Unknown"
    assert result["confidence"] > 0
    assert result["severity"] in ("mild", "moderate", "severe", "emergency")


@pytest.mark.asyncio
async def test_get_direct_diagnosis_unknown():
    result = await get_direct_diagnosis(["xyz_not_a_symptom"])
    assert result["disease"] == "Unknown"
