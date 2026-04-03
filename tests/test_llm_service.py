"""Tests for LLM service response parsing and fallback."""

from app.services.llm_service import _parse_llm_response, _fallback_response


def test_parse_llm_response():
    content = (
        "You may have a common cold.\n\n"
        "REMEDIES: Rest | Warm fluids | Honey tea\n"
        "MEDICATIONS: Paracetamol | Ibuprofen\n"
        "SPECIALIST: General Practitioner"
    )
    result = _parse_llm_response(content)
    assert "common cold" in result["message"].lower()
    assert result["remedies"] == ["Rest", "Warm fluids", "Honey tea"]
    assert result["medications"] == ["Paracetamol", "Ibuprofen"]
    assert result["specialist"] == "General Practitioner"


def test_parse_llm_response_no_structured_data():
    content = "I'm not sure about your symptoms. Please see a doctor."
    result = _parse_llm_response(content)
    assert "not sure" in result["message"].lower()
    assert result["remedies"] is None
    assert result["medications"] is None
    assert result["specialist"] is None


def test_fallback_response():
    result = _fallback_response(
        disease="Common Cold",
        confidence=0.85,
        severity={"level": "mild", "recommendation": "Rest at home."},
        symptoms=["headache", "high_fever"],
    )
    assert "Common Cold" in result["message"]
    assert "85%" in result["message"]
    assert result["remedies"] is not None
    assert result["specialist"] == "General Practitioner"
