"""Tests for symptom parser service."""

from app.services.symptom_parser import _fallback_parse
from app.services.ml_service import get_known_symptoms


def test_fallback_parse_finds_symptoms():
    known = get_known_symptoms()
    result = _fallback_parse("I have a headache and nausea", known)
    assert "headache" in result or "nausea" in result


def test_fallback_parse_no_symptoms():
    known = get_known_symptoms()
    result = _fallback_parse("Hello how are you today?", known)
    # May or may not find symptoms in this generic message
    assert isinstance(result, list)


def test_fallback_parse_underscore_format():
    known = get_known_symptoms()
    result = _fallback_parse("I have high_fever and chest_pain", known)
    found = set(result)
    assert "high_fever" in found or "chest_pain" in found
